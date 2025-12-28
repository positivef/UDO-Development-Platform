# UDO Platform - Production Deployment Guide

**Version**: 1.0
**Last Updated**: 2025-12-23
**Status**: Production Ready

---

## 📋 Pre-Deployment Checklist

### Environment Preparation
- [ ] `.env.production.example` copied to `.env` with real values
- [ ] All `<CHANGE_ME_*>` placeholders replaced with actual credentials
- [ ] SSL certificates obtained (Let's Encrypt or commercial CA)
- [ ] Domain DNS configured (A/AAAA records pointing to server)
- [ ] Firewall rules configured (ports 80, 443, 5432 only from trusted IPs)

### Security Validation
- [ ] JWT_SECRET is 64+ characters, cryptographically random
- [ ] Database password is 32+ characters
- [ ] CORS_ORIGINS limited to production domains only
- [ ] DEBUG=False confirmed
- [ ] DISABLE_AUTH_IN_DEV removed or set to false
- [ ] Rate limiting enabled (RATE_LIMIT_ENABLED=true)

### Infrastructure
- [ ] PostgreSQL 16 with pgvector extension available
- [ ] Redis 7+ available
- [ ] Docker Engine 24.0+ installed
- [ ] Docker Compose 2.20+ installed
- [ ] Minimum 4 CPU cores, 8GB RAM, 50GB disk space
- [ ] Backup storage configured (S3, GCS, or local NAS)

### Monitoring Setup
- [ ] Sentry account created (error tracking)
- [ ] Grafana dashboards configured
- [ ] Prometheus scraping endpoints verified
- [ ] Uptime monitoring configured (Uptime Robot, Pingdom)
- [ ] Alert channels configured (email, Slack, PagerDuty)

---

## 🚀 Deployment Steps

### Step 1: Clone Repository

```bash
# Clone production branch
git clone https://github.com/yourusername/UDO-Development-Platform.git
cd UDO-Development-Platform

# Checkout production tag or main branch
git checkout tags/v1.0.0  # Or: git checkout main
```

---

### Step 2: Configure Environment Variables

```bash
# Copy production example
cp .env.production.example .env

# Edit with production values
nano .env  # or vim .env

# CRITICAL: Replace ALL <CHANGE_ME_*> placeholders
# Verify no placeholders remain:
grep "CHANGE_ME" .env && echo "ERROR: Placeholders found!" || echo "OK"
```

**Minimum Required Variables**:
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `REDIS_HOST`, `REDIS_PASSWORD`
- `JWT_SECRET` (generate: `openssl rand -hex 32`)
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- `CORS_ORIGINS` (e.g., `https://yourdomain.com`)
- `SENTRY_DSN`

---

### Step 3: Build Docker Images

```bash
# Build all production images
docker-compose -f docker-compose.prod.yml build

# Verify images created
docker images | grep udo

# Expected output:
# udo-backend      production    <image-id>    <size>
# udo-frontend     production    <image-id>    <size>
```

**Build Time**: ~5-10 minutes (first build)

---

### Step 4: Database Initialization

```bash
# Start database only
docker-compose -f docker-compose.prod.yml up -d db

# Wait for database to be ready
docker-compose -f docker-compose.prod.yml exec db pg_isready -U udo_prod_user

# Run migrations (if using Alembic)
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Verify database schema
docker-compose -f docker-compose.prod.yml exec db psql -U udo_prod_user -d udo_production -c "\dt"
```

---

### Step 5: Start All Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# With optional backup service
docker-compose -f docker-compose.prod.yml --profile with-backup up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# Expected: All services should be "Up (healthy)"
```

---

### Step 6: Health Checks

```bash
# Backend API
curl -f http://localhost:8000/api/status || echo "FAIL"

# Frontend
curl -f http://localhost:3000 || echo "FAIL"

# Database
docker-compose -f docker-compose.prod.yml exec db pg_isready

# Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli --pass $REDIS_PASSWORD ping
```

**Expected**: All checks return "OK" or "PONG"

---

### Step 7: Nginx Reverse Proxy (Recommended)

```bash
# Start with Nginx profile
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d nginx

# Configure SSL (Let's Encrypt)
docker exec udo_nginx certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Verify HTTPS
curl -I https://yourdomain.com
```

**Nginx Config Location**: `./nginx/nginx.conf`

---

### Step 8: Verify E2E Functionality

```bash
# 1. Create a test task via API
curl -X POST http://localhost:8000/api/kanban/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Production Test Task", "phase": "ideation", "priority": "high"}'

# 2. Verify task appears in frontend
curl http://localhost:3000/kanban

# 3. Test AI suggestions
curl -X POST http://localhost:8000/api/kanban/tasks/ai-suggestions \
  -H "Content-Type: application/json" \
  -d '{"task_id": "test-task-id"}'

# 4. Check logs for errors
docker-compose -f docker-compose.prod.yml logs backend | grep -i error
docker-compose -f docker-compose.prod.yml logs frontend | grep -i error
```

---

### Step 9: Monitoring Setup

```bash
# Access Grafana
# http://your-server:3001
# Login: admin / <GRAFANA_ADMIN_PASSWORD>

# Import dashboards:
# - UDO System Overview
# - Database Performance
# - API Response Times
# - Error Rates

# Access Prometheus
# http://your-server:9090

# Verify targets are up:
# Status > Targets > All should be "UP"
```

---

### Step 10: Backup Validation

```bash
# Trigger manual backup
docker-compose -f docker-compose.prod.yml exec backup /backup.sh

# Verify backup created
ls -lh backups/

# Test restore (on test database)
# docker exec -i udo_postgres_prod psql -U udo_prod_user -d udo_test < backups/latest.sql
```

---

## 🔒 Security Hardening

### Firewall Configuration (UFW)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Database - only from backend IP
sudo ufw allow from 172.29.0.0/16 to any port 5432

# Deny all other traffic
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Enable firewall
sudo ufw enable
```

---

### SSL/TLS Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal cron job (added automatically)
sudo certbot renew --dry-run
```

---

### Rate Limiting (Application Level)

**Already configured** in `.env`:
```
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

**Test**:
```bash
# Should block after 60 requests/minute
for i in {1..65}; do curl http://localhost:8000/api/status; done
```

---

## 📊 Monitoring & Alerts

### Grafana Dashboards

1. **System Overview**:
   - CPU/Memory usage
   - Request rate
   - Error rate
   - Response time (p50, p95, p99)

2. **Database Performance**:
   - Connection pool usage
   - Query latency
   - Slow queries (>1s)
   - Table sizes

3. **AI Services**:
   - API call success rate
   - Token usage
   - Cost tracking

---

### Alert Rules

Configure in Grafana:

| Alert | Threshold | Action |
|-------|-----------|--------|
| High Error Rate | >5% in 5 min | Slack + Email |
| Database Down | Connection fail | PagerDuty (immediate) |
| High Memory | >90% for 10 min | Email |
| Slow Queries | >1000ms p95 | Email |
| Disk Space | <10% free | Email + Slack |

---

## 🔄 Rollback Procedures

See `ROLLBACK_PROCEDURES.md` for detailed instructions.

**Quick Rollback** (within 5 minutes):
```bash
# Stop current version
docker-compose -f docker-compose.prod.yml down

# Checkout previous version
git checkout tags/v0.9.0

# Restart
docker-compose -f docker-compose.prod.yml up -d

# Verify
curl http://localhost:8000/api/status
```

---

## 📝 Post-Deployment Tasks

- [ ] Update DNS TTL back to normal (3600s)
- [ ] Enable automated backups
- [ ] Configure log rotation (logrotate)
- [ ] Set up uptime monitoring (Uptime Robot)
- [ ] Document deployment date and version in changelog
- [ ] Notify team of successful deployment
- [ ] Schedule post-deployment review (1 week)

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs <service-name>

# Common issues:
# 1. Port already in use: netstat -tuln | grep <port>
# 2. Environment variable missing: docker-compose config
# 3. Database not ready: Wait 30s after db start
```

---

### High Memory Usage

```bash
# Check container stats
docker stats

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Increase limits in docker-compose.prod.yml:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

---

### Database Connection Errors

```bash
# Verify database is running
docker-compose -f docker-compose.prod.yml ps db

# Test connection
docker-compose -f docker-compose.prod.yml exec backend python -c "from backend.async_database import async_db; import asyncio; asyncio.run(async_db.initialize())"

# Check connection pool
docker-compose -f docker-compose.prod.yml logs backend | grep "pool initialized"
```

---

## 📞 Support Contacts

- **Technical Lead**: [Your Name] - [email]
- **DevOps**: [DevOps Team] - [email]
- **On-Call**: [PagerDuty rotation]

---

## 🔗 Related Documentation

- `ROLLBACK_PROCEDURES.md` - Rollback strategies
- `SECURITY_AUDIT_CHECKLIST.md` - Security validation
- `.env.production.example` - Environment variables reference
- `docker-compose.prod.yml` - Production services configuration

---

**Deployment completed successfully! 🎉**

**Next Steps**: Monitor for 24 hours, then schedule Day 2 operations review.
