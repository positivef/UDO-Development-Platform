# Rollback Procedures

## 3-Tier Rollback Strategy

### Tier 1: Emergency Rollback (<5 minutes)

**When**: Critical bug, service down, data corruption risk

```bash
# 1. Disable feature flags (instant)
curl -X POST http://localhost:8000/api/admin/feature-flags \
  -H "Content-Type: application/json" \
  -d '{"flag": "kanban_enabled", "enabled": false}'

# 2. Rollback to previous image
docker-compose -f docker-compose.prod.yml stop backend
docker tag udo-backend:production udo-backend:broken
docker tag udo-backend:previous udo-backend:production
docker-compose -f docker-compose.prod.yml up -d backend

# 3. Verify health
curl http://localhost:8000/api/health
```

**Recovery time**: <5 minutes

### Tier 2: Standard Rollback (<30 minutes)

**When**: Non-critical bugs, performance degradation, failed deployment

```bash
# 1. Identify last working commit
git log --oneline -10

# 2. Revert to working commit
git revert HEAD
# or
git reset --hard <working-commit-hash>

# 3. Rebuild and redeploy
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify all services
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:8000/api/health
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

**Recovery time**: <30 minutes

### Tier 3: Database Rollback (<60 minutes)

**When**: Schema migration failure, data corruption

```bash
# 1. Stop application
docker-compose -f docker-compose.prod.yml stop backend frontend

# 2. Restore database from backup
docker exec -i udo_postgres_prod psql -U $DB_USER $DB_NAME < backup_YYYYMMDD.sql

# 3. Verify data integrity
docker exec udo_postgres_prod psql -U $DB_USER $DB_NAME \
  -c "SELECT count(*) FROM kanban.tasks;"

# 4. Restart application
docker-compose -f docker-compose.prod.yml up -d backend frontend

# 5. Verify health
curl http://localhost:8000/api/health
```

**Recovery time**: <60 minutes

## Pre-Deployment Checklist

Before every deployment:

- [ ] Database backup taken
- [ ] Current Docker images tagged as `previous`
- [ ] Git commit hash recorded
- [ ] Rollback procedure reviewed
- [ ] Health check endpoints verified

## Tag Current Images Before Deploy

```bash
# Always tag current working images before deploying new ones
docker tag udo-backend:production udo-backend:previous
docker tag udo-frontend:production udo-frontend:previous
```

## Post-Rollback Actions

1. **Notify team** of rollback and reason
2. **Create incident report** in `claudedocs/`
3. **Investigate root cause** before re-deploying
4. **Add regression test** for the issue
5. **Update this document** if procedure needs improvement

## Emergency Contacts

| Role | Responsibility |
|------|---------------|
| On-call Engineer | Execute rollback |
| Team Lead | Approve Tier 3 rollback |
| DBA | Database recovery |
