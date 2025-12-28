# UDO Platform - Rollback Procedures

**Version**: 1.0
**Last Updated**: 2025-12-23
**Status**: Production Critical

---

## 🚨 Rollback Decision Matrix

| Severity | Issue Type | Decision | Rollback Tier |
|----------|------------|----------|---------------|
| **P0** | Data loss, security breach | IMMEDIATE rollback | Tier 1 (<5min) |
| **P0** | Complete service outage | IMMEDIATE rollback | Tier 1 (<5min) |
| **P1** | Major feature broken | Rollback within 30min | Tier 2 |
| **P1** | High error rate (>10%) | Rollback within 30min | Tier 2 |
| **P2** | Minor bugs, UI issues | Fix forward preferred | Tier 3 (optional) |
| **P2** | Performance degradation <20% | Monitor, fix in next release | No rollback |

---

## ⚡ Tier 1: Emergency Rollback (<5 minutes)

**When**: P0 incidents (data loss, security breach, complete outage)

**Prerequisites**:
- Database backup from before deployment
- Git tag of previous stable version

### Quick Rollback Commands

```bash
# 1. Stop current services (30 seconds)
docker-compose -f docker-compose.prod.yml down

# 2. Checkout previous version (30 seconds)
git fetch --tags
git checkout tags/v<previous-version>  # e.g., v0.9.0

# 3. Restore environment if needed (60 seconds)
git checkout v<previous-version> -- .env

# 4. Start services (120 seconds)
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify health (60 seconds)
curl -f http://localhost:8000/api/status
curl -f http://localhost:3000

# Total: ~5 minutes
```

**Verification**:
```bash
# Check all services healthy
docker-compose -f docker-compose.prod.yml ps

# Expected: All services "Up (healthy)"
```

---

## 🔄 Tier 2: Standard Rollback (<30 minutes)

**When**: P1 incidents (major feature broken, high error rate)

**Includes**: Database restoration, full service rollback

### Step-by-Step Rollback

#### Step 1: Assessment (2 minutes)
```bash
# Identify issue
docker-compose -f docker-compose.prod.yml logs backend | tail -100
docker-compose -f docker-compose.prod.yml logs frontend | tail -100

# Check error metrics in Grafana
# http://your-server:3001

# Decision: Rollback vs Fix Forward
# - Rollback if: Can't fix in <1 hour
# - Fix Forward if: Simple bug, hotfix possible
```

---

#### Step 2: Database Backup (5 minutes)
```bash
# Create current database snapshot (before rollback)
docker exec udo_postgres_prod pg_dump \
  -U udo_prod_user \
  -d udo_production \
  -F c \
  -f /backups/pre-rollback-$(date +%Y%m%d-%H%M%S).dump

# Verify backup created
docker exec udo_postgres_prod ls -lh /backups/
```

---

#### Step 3: Stop Services (2 minutes)
```bash
# Graceful shutdown (30s timeout)
docker-compose -f docker-compose.prod.yml stop

# Force stop if needed
docker-compose -f docker-compose.prod.yml down
```

---

#### Step 4: Restore Database (10 minutes)
```bash
# List available backups
ls -lht backups/ | head -10

# Identify last good backup (before deployment)
BACKUP_FILE="backups/udo_production-2025-12-22-010000.dump"

# Restore database
docker exec -i udo_postgres_prod pg_restore \
  -U udo_prod_user \
  -d udo_production \
  --clean \
  --if-exists \
  < $BACKUP_FILE

# Verify restoration
docker exec udo_postgres_prod psql \
  -U udo_prod_user \
  -d udo_production \
  -c "SELECT COUNT(*) FROM kanban.tasks;"
```

---

#### Step 5: Application Rollback (5 minutes)
```bash
# Checkout previous version
git checkout tags/v<previous-version>

# Rebuild images (if schema changed)
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Wait for health checks
sleep 60
```

---

#### Step 6: Verification (5 minutes)
```bash
# Backend health
curl -f http://localhost:8000/api/status

# Frontend health
curl -f http://localhost:3000

# Database connectivity
docker-compose -f docker-compose.prod.yml exec backend python -c \
  "from backend.async_database import async_db; import asyncio; asyncio.run(async_db.initialize()); print('OK')"

# E2E test
curl -X GET http://localhost:8000/api/kanban/tasks | jq '.[0]'
```

---

#### Step 7: Monitoring (Continuous)
```bash
# Watch error logs
docker-compose -f docker-compose.prod.yml logs -f backend | grep -i error

# Check Grafana dashboards
# - Error rate should drop to <1%
# - Response time should normalize
```

---

## 🧩 Tier 3: Partial Rollback (Optional)

**When**: P2 incidents (minor bugs, specific feature broken)

**Strategy**: Rollback single component while keeping others running

### Feature Flag Rollback

```bash
# Disable specific feature via environment variable
docker-compose -f docker-compose.prod.yml exec backend bash

# Inside container:
export ENABLE_AI_SUGGESTIONS=false

# Restart backend only
docker-compose -f docker-compose.prod.yml restart backend

# Verify
curl http://localhost:8000/api/status | jq '.features.ai_suggestions'
# Expected: false
```

---

### Component-Specific Rollback

```bash
# Rollback backend only (keep frontend, database)
docker-compose -f docker-compose.prod.yml stop backend
git checkout tags/v<previous-version> -- backend/
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend

# Rollback frontend only
docker-compose -f docker-compose.prod.yml stop frontend
git checkout tags/v<previous-version> -- web-dashboard/
docker-compose -f docker-compose.prod.yml build frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

---

## 📊 Rollback Validation Checklist

After rollback, verify ALL items:

### Functional Checks
- [ ] API responds to /api/status (200 OK)
- [ ] Frontend loads without errors
- [ ] Database queries return expected data
- [ ] User login works
- [ ] Kanban board displays tasks
- [ ] Task CRUD operations work

### Performance Checks
- [ ] API response time <500ms (p95)
- [ ] Frontend load time <3s
- [ ] Database query latency <50ms
- [ ] Error rate <1%

### Monitoring
- [ ] Grafana dashboards show healthy metrics
- [ ] Sentry error count decreasing
- [ ] Prometheus targets all "UP"
- [ ] No critical alerts firing

---

## 🔍 Post-Rollback Analysis

### Incident Report Template

```markdown
# Incident Report: [Date] - [Brief Description]

## Timeline
- [HH:MM] Deployment started
- [HH:MM] Issue detected (describe symptoms)
- [HH:MM] Rollback decision made
- [HH:MM] Rollback completed
- [HH:MM] Service restored

## Root Cause
- Technical cause: [What broke?]
- Human cause: [Process gap?]

## Impact
- Duration: [minutes]
- Affected users: [number or percentage]
- Data loss: [Yes/No, details]
- Financial impact: [$amount if applicable]

## Rollback Method Used
- [ ] Tier 1 (Emergency)
- [ ] Tier 2 (Standard)
- [ ] Tier 3 (Partial)

## Lessons Learned
1. What went well?
2. What could be improved?
3. Action items to prevent recurrence?

## Action Items
- [ ] Update deployment checklist with new checks
- [ ] Add monitoring for detected symptom
- [ ] Improve test coverage for broken area
- [ ] Document new edge case
```

---

## 🛡️ Rollback Prevention

### Pre-Deployment Validation

```bash
# 1. Run full test suite
docker-compose -f docker-compose.prod.yml run --rm backend pytest
cd web-dashboard && npm run test:e2e

# 2. Build production images
docker-compose -f docker-compose.prod.yml build

# 3. Smoke test in staging
ENVIRONMENT=staging docker-compose -f docker-compose.prod.yml up -d
# Run manual smoke tests

# 4. Database migration dry-run
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head --sql

# 5. Security audit
docker scan udo-backend:production
docker scan udo-frontend:production
```

---

### Deployment Gates

**Must Pass ALL Gates**:
1. ✅ All unit tests pass (496/496)
2. ✅ All E2E tests pass (18/18)
3. ✅ Security audit (0 high/critical vulnerabilities)
4. ✅ Performance benchmarks (DAG <50ms, API p95 <500ms)
5. ✅ Staging smoke tests pass
6. ✅ Database migration validated
7. ✅ Rollback plan documented

**Fail ANY Gate** → DO NOT deploy

---

## 🔄 Testing Rollback Procedures

### Monthly Rollback Drill

```bash
# Schedule: Last Friday of each month

# 1. Deploy to staging
git checkout main
docker-compose -f docker-compose.prod.yml up -d

# 2. Simulate issue
docker-compose -f docker-compose.prod.yml exec backend bash
# Kill process or inject error

# 3. Execute Tier 2 rollback
[Follow Tier 2 procedures above]

# 4. Measure time
# Goal: <30 minutes

# 5. Document issues found
# Update procedures based on findings
```

---

## 📞 Escalation Contacts

| Role | Contact | Escalation Time |
|------|---------|-----------------|
| On-Call Engineer | [PagerDuty] | Immediate |
| Tech Lead | [Email/Phone] | 15 minutes |
| VP Engineering | [Email/Phone] | 30 minutes |
| CEO | [Email/Phone] | 1 hour (P0 only) |

---

## 🔗 Related Documentation

- `PRODUCTION_DEPLOYMENT_GUIDE.md` - Deployment procedures
- `SECURITY_AUDIT_CHECKLIST.md` - Security validation
- `docs/3_TIER_ROLLBACK_STRATEGY.md` - Rollback strategy theory
- `.env.production.example` - Environment configuration

---

**Remember**:
- Rollback is NOT a failure - it's a safety mechanism
- Better to rollback quickly than fix forward slowly
- Document EVERY rollback for process improvement
- Test rollback procedures regularly

**Rollback Confidence Level**: 95% (tested in staging monthly)
