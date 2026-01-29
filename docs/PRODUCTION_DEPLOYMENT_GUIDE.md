# Production Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- Domain name with DNS configured
- SSL certificate (Let's Encrypt or commercial)
- Server with 4GB+ RAM, 2+ CPU cores

## 10-Step Deployment

### Step 1: Clone and Configure

```bash
git clone https://github.com/positivef/UDO-Development-Platform.git
cd UDO-Development-Platform
cp .env.production.example .env
```

Edit `.env` with actual values:
- Generate `JWT_SECRET`: `openssl rand -hex 32`
- Set strong `DB_PASSWORD` and `REDIS_PASSWORD`
- Configure `CORS_ORIGINS` with your domain
- Set `NEXT_PUBLIC_API_URL` to your API domain

### Step 2: Build Docker Images

```bash
docker-compose -f docker-compose.prod.yml build
```

### Step 3: Start Database and Redis First

```bash
docker-compose -f docker-compose.prod.yml up -d db redis
```

Wait for health checks:
```bash
docker-compose -f docker-compose.prod.yml ps
# Both should show "healthy"
```

### Step 4: Run Database Migrations

```bash
docker exec udo_backend_prod python -m backend.migrations.run_migration \
  --database $DB_NAME --user $DB_USER --password $DB_PASSWORD
```

### Step 5: Start Backend

```bash
docker-compose -f docker-compose.prod.yml up -d backend
```

Verify:
```bash
curl http://localhost:8000/api/health
# Expected: {"status": "ok"}
```

### Step 6: Start Frontend

```bash
docker-compose -f docker-compose.prod.yml up -d frontend
```

Verify:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# Expected: 200
```

### Step 7: Start Monitoring (Optional)

```bash
docker-compose -f docker-compose.prod.yml up -d prometheus grafana
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin / your password)

### Step 8: Enable Nginx Reverse Proxy (Optional)

```bash
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d nginx
```

### Step 9: Enable Automated Backups (Optional)

```bash
docker-compose -f docker-compose.prod.yml --profile with-backup up -d backup
```

### Step 10: Verify All Services

```bash
docker-compose -f docker-compose.prod.yml ps
```

All services should show `Up (healthy)`.

**Smoke test endpoints:**

| Endpoint | Expected |
|----------|----------|
| `GET /api/health` | `{"status": "ok"}` |
| `GET /api/kanban/tasks` | Task list JSON |
| `GET /docs` | Swagger UI |
| `GET /` (frontend) | Dashboard HTML |

## Post-Deployment

### Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Manual Backup
```bash
docker exec udo_postgres_prod pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d).sql
```

### Restart Service
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### Full Shutdown
```bash
docker-compose -f docker-compose.prod.yml down
```

### Update Deployment
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## Deployment Blockers Checklist

Before deploying, verify all items:

- [ ] `.env` configured with real secrets (no defaults)
- [ ] `JWT_SECRET` is random 256-bit value
- [ ] `DB_PASSWORD` is strong (20+ chars)
- [ ] `CORS_ORIGINS` set to actual domain
- [ ] SSL certificate installed
- [ ] Firewall rules configured (only 80/443 exposed)
- [ ] Backup schedule verified
- [ ] Monitoring alerts configured
- [ ] All backend tests passing (707/707)
- [ ] User testing passed (4.3/5.0)
