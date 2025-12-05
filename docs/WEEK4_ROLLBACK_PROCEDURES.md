# Week 4 Rollback Validation Procedures

**Date**: 2025-12-05
**Version**: 1.0.0
**Purpose**: 3-Tier rollback strategy for Kanban-UDO Integration
**Target RTO**: 5 minutes (Recovery Time Objective)

---

## 🎯 Rollback Strategy Overview

### 3-Tier Approach

| Tier | Method | RTO | Use Case | Risk Level |
|------|--------|-----|----------|------------|
| **Tier 1** | Feature Flag | Immediate (<10s) | Non-critical bugs, high traffic | Low |
| **Tier 2** | Git Revert | 1 minute | Code bugs, API issues | Medium |
| **Tier 3** | Database Restore | 5 minutes | Data corruption, schema issues | High |

### Decision Tree

```
Is there a critical production issue?
│
├─ YES → Is it a code/API issue?
│   ├─ YES → Can feature flag disable fix it?
│   │   ├─ YES → **Tier 1: Feature Flag** (Immediate)
│   │   └─ NO → **Tier 2: Git Revert** (1 min)
│   └─ NO → Is it a data/database issue?
│       └─ YES → **Tier 3: Database Restore** (5 min)
│
└─ NO → Continue monitoring, no rollback needed
```

---

## 🔴 Tier 1: Feature Flag Rollback (Immediate)

### When to Use
- Non-critical bugs in production
- High traffic periods (don't want to redeploy)
- Need to disable feature temporarily
- Testing in production (canary/A/B test)

### Prerequisites
- Feature flag system in place
- KANBAN_ENABLED environment variable configured
- No database schema changes (use Tier 3 if schema changed)

### Procedure

#### Step 1: Disable Feature Flag (10 seconds)

**Backend** (`backend/.env` or environment config):
```bash
# Disable Kanban feature
KANBAN_ENABLED=false
```

**Alternative (if using config service)**:
```bash
# Via API (if implemented)
curl -X PUT http://localhost:8000/api/config/features \
  -H "Content-Type: application/json" \
  -d '{"kanban_enabled": false}'
```

**Alternative (if using environment variable override)**:
```bash
# Windows (PowerShell)
$env:KANBAN_ENABLED="false"

# Linux/Mac
export KANBAN_ENABLED=false

# Restart backend (if not hot-reloading)
pm2 restart udo-backend
```

#### Step 2: Verify Rollback (10 seconds)

```bash
# Check feature status
curl http://localhost:8000/api/health

# Expected response:
# {
#   "status": "healthy",
#   "features": {
#     "kanban_enabled": false  # ← Should be false
#   }
# }

# Verify Kanban endpoints return 503 Service Unavailable
curl http://localhost:8000/api/kanban/archive
# Expected: 503 Service Unavailable or Feature Disabled message
```

#### Step 3: Monitor (1 minute)

```bash
# Check error logs
tail -f backend/logs/error.log

# Check access logs (should see no Kanban requests)
tail -f backend/logs/access.log | grep "/api/kanban"

# Monitor metrics dashboard
# → Kanban request rate should drop to 0
```

#### Step 4: Communicate

```markdown
**INCIDENT**: Kanban feature temporarily disabled

**Impact**: Users cannot access Kanban board or archive tasks
**Workaround**: Use legacy task management system
**ETA**: Investigating, will re-enable or deploy fix within 1 hour
**Status Page**: https://status.udo-platform.com
```

### Rollback Validation Checklist

- [ ] Feature flag set to `false`
- [ ] Backend restarted (if needed)
- [ ] Health check confirms `kanban_enabled: false`
- [ ] Kanban endpoints return 503 or disabled message
- [ ] Error logs show no new Kanban errors
- [ ] Access logs show zero Kanban requests
- [ ] Stakeholders notified

### Rollforward (Re-enable)

```bash
# When fix is ready or issue resolved
KANBAN_ENABLED=true

# Restart backend
pm2 restart udo-backend

# Verify health check
curl http://localhost:8000/api/health | jq '.features.kanban_enabled'
# Expected: true

# Test Kanban endpoints
curl http://localhost:8000/api/kanban/archive
# Expected: 200 OK (empty list or valid data)
```

---

## 🟡 Tier 2: Git Revert Rollback (1 Minute)

### When to Use
- Code bugs in production
- API issues causing errors
- Feature flag doesn't solve the problem
- Need to revert specific commit(s)

### Prerequisites
- Git access to repository
- CI/CD pipeline configured
- Deployment automation (pm2, Docker, etc.)

### Procedure

#### Step 1: Identify Commit to Revert (20 seconds)

```bash
# Check recent commits
git log --oneline -10

# Example output:
# 0a81468 feat: Week 3 Day 4-5 - Archive View + AI Summarization (Q6)
# 0e8e174 feat: Week 3 Day 3 - AI Task Suggestion
# ...

# Identify the problematic commit hash
COMMIT_HASH="0a81468"  # Example: Week 3 Day 4-5 commit
```

#### Step 2: Create Revert Commit (20 seconds)

```bash
# Revert the commit (creates new commit that undoes changes)
git revert $COMMIT_HASH --no-edit

# Verify revert commit created
git log --oneline -3

# Example output:
# abc1234 Revert "feat: Week 3 Day 4-5 - Archive View + AI Summarization (Q6)"
# 0a81468 feat: Week 3 Day 4-5 - Archive View + AI Summarization (Q6)
# 0e8e174 feat: Week 3 Day 3 - AI Task Suggestion
```

#### Step 3: Push Revert (10 seconds)

```bash
# Push revert to main branch
git push origin main

# Verify push successful
git log origin/main --oneline -3
```

#### Step 4: Trigger Deployment (10 seconds)

**Option A: Automatic CI/CD**
```bash
# If CI/CD is configured, deployment happens automatically
# Monitor CI/CD pipeline
gh run watch  # GitHub Actions
# or
gitlab-ci-runner  # GitLab CI
```

**Option B: Manual Deployment**
```bash
# Pull latest code
git pull origin main

# Restart backend
cd backend
pm2 restart udo-backend

# Or with Docker
docker-compose down
docker-compose up -d --build
```

#### Step 5: Verify Rollback (10 seconds)

```bash
# Check backend version (should show revert commit)
curl http://localhost:8000/api/version

# Expected:
# {
#   "version": "1.0.0",
#   "commit": "abc1234",  # ← Revert commit
#   "timestamp": "2025-12-05T12:30:00Z"
# }

# Test that reverted code is gone
curl http://localhost:8000/api/kanban/archive
# Expected: 404 Not Found (if archive router reverted)

# Check error logs
tail -f backend/logs/error.log
# Expected: No new errors related to Kanban
```

### Rollback Validation Checklist

- [ ] Revert commit created successfully
- [ ] Revert commit pushed to main branch
- [ ] CI/CD pipeline completed successfully
- [ ] Backend restarted with reverted code
- [ ] API version shows revert commit hash
- [ ] Problematic endpoints return 404 or work correctly
- [ ] Error logs show no new issues
- [ ] Stakeholders notified

### Rollforward (Re-deploy Fix)

```bash
# After bug is fixed in new commit
git pull origin main

# Verify fix commit
git log --oneline -3

# Deploy fixed version
pm2 restart udo-backend

# Test endpoints
curl http://localhost:8000/api/kanban/archive
# Expected: 200 OK with correct behavior
```

---

## 🔴 Tier 3: Database Restore Rollback (5 Minutes)

### When to Use
- Data corruption detected
- Schema migration failed
- Critical data integrity issues
- Feature flag + Git revert don't solve the problem

### ⚠️ WARNING
- **CRITICAL OPERATION**: Data loss risk
- **DOWNTIME**: 5-10 minutes service outage
- **APPROVAL**: Requires CTO/Engineering Lead approval
- **COMMUNICATION**: Notify all stakeholders immediately

### Prerequisites
- Database backup exists (automated daily backups)
- Database access credentials
- Backup verification completed weekly
- Maintenance window scheduled (or emergency declared)

### Procedure

#### Step 0: STOP - Confirm This is Necessary (1 minute)

**Critical Questions**:
- [ ] Is there actual data corruption or loss?
- [ ] Can the issue be fixed with Tier 1 or Tier 2?
- [ ] Is there a recent backup (< 24 hours old)?
- [ ] Have you notified CTO/Engineering Lead?
- [ ] Is downtime acceptable right now?

**If ALL answers are YES, proceed. Otherwise, reconsider.**

#### Step 1: Enable Maintenance Mode (30 seconds)

```bash
# Put application in maintenance mode
echo "MAINTENANCE_MODE=true" >> backend/.env

# Restart backend to show maintenance page
pm2 restart udo-backend

# Verify maintenance mode active
curl http://localhost:8000/api/health
# Expected: 503 Service Unavailable (Maintenance Mode)
```

#### Step 2: Stop All Database Connections (30 seconds)

```bash
# Stop backend processes
pm2 stop udo-backend

# Stop all background workers
pm2 stop udo-workers

# Verify no connections to database
psql -U postgres -d udo_platform -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'udo_platform';"
# Expected: 0 (or only your connection)
```

#### Step 3: Backup Current State (30 seconds)

**CRITICAL**: Always backup current state before restoring!

```bash
# Create emergency backup of current database
pg_dump -U postgres udo_platform > /backups/emergency_$(date +%Y%m%d_%H%M%S).sql

# Verify backup created
ls -lh /backups/emergency_*.sql
```

#### Step 4: Identify Restore Point (30 seconds)

```bash
# List available backups
ls -lht /backups/

# Example output:
# -rw-r--r-- 1 postgres postgres 50M Dec  5 12:00 udo_platform_20251205_120000.sql  ← Latest
# -rw-r--r-- 1 postgres postgres 48M Dec  4 12:00 udo_platform_20251204_120000.sql
# -rw-r--r-- 1 postgres postgres 47M Dec  3 12:00 udo_platform_20251203_120000.sql

# Choose backup (usually latest before issue started)
BACKUP_FILE="/backups/udo_platform_20251204_120000.sql"  # Example: Day before issue
```

#### Step 5: Restore Database (2 minutes)

```bash
# Drop Kanban schema only (safer than full restore if possible)
psql -U postgres -d udo_platform -c "DROP SCHEMA IF EXISTS kanban CASCADE;"

# Restore from backup
psql -U postgres udo_platform < $BACKUP_FILE

# Verify restore
psql -U postgres -d udo_platform -c "SELECT COUNT(*) FROM kanban.tasks;"
# Expected: Task count from backup timestamp
```

#### Step 6: Verify Data Integrity (1 minute)

```bash
# Check critical tables exist
psql -U postgres -d udo_platform -c "\dt kanban.*"

# Expected: List of kanban tables (or none if schema didn't exist in backup)

# Check data integrity
psql -U postgres -d udo_platform -c "
  SELECT
    (SELECT COUNT(*) FROM kanban.tasks) as tasks,
    (SELECT COUNT(*) FROM kanban.dependencies) as dependencies,
    (SELECT COUNT(*) FROM kanban.task_archive) as archived;
"

# Verify no corruption
psql -U postgres -d udo_platform -c "SELECT * FROM kanban.tasks LIMIT 5;"
# Expected: Valid task data (or empty if new feature)
```

#### Step 7: Restart Services (30 seconds)

```bash
# Disable maintenance mode
sed -i '/MAINTENANCE_MODE/d' backend/.env
# Or set to false
echo "MAINTENANCE_MODE=false" >> backend/.env

# Restart backend
pm2 restart udo-backend

# Restart workers
pm2 restart udo-workers

# Verify services running
pm2 status
```

#### Step 8: Verify Rollback (30 seconds)

```bash
# Health check
curl http://localhost:8000/api/health
# Expected: 200 OK

# Test database connection
curl http://localhost:8000/api/kanban/archive
# Expected: 200 OK (with data from backup timestamp)

# Check logs for errors
tail -f backend/logs/error.log
# Expected: No critical errors
```

### Rollback Validation Checklist

- [ ] CTO/Engineering Lead approval obtained
- [ ] Maintenance mode enabled
- [ ] All database connections stopped
- [ ] Emergency backup of current state created
- [ ] Backup file identified and verified
- [ ] Database restored successfully
- [ ] Data integrity verified (no corruption)
- [ ] Services restarted successfully
- [ ] Health checks passing
- [ ] Error logs clean
- [ ] Stakeholders notified of completion

### Data Loss Impact

**Expected Data Loss**:
- All changes since backup timestamp
- Example: If backup from 12:00 PM, lose changes from 12:00 PM to now

**Mitigation**:
- Frequent backups (every 1 hour for critical systems)
- Transaction logs for point-in-time recovery
- Inform users of data loss window

---

## 🧪 Rollback Testing (Week 4 Day 3)

### Test Plan

**Objective**: Validate all 3 tiers work correctly in staging

#### Test 1: Feature Flag Rollback

```bash
# In staging environment
# 1. Enable Kanban feature
# 2. Create test task
# 3. Disable feature flag
# 4. Verify task not accessible
# 5. Re-enable feature flag
# 6. Verify task accessible again

# Expected: <10 seconds total, zero errors
```

#### Test 2: Git Revert Rollback

```bash
# In staging environment
# 1. Deploy Week 3 Day 4-5 commit
# 2. Verify archive endpoints work
# 3. Revert commit
# 4. Verify archive endpoints return 404
# 5. Re-deploy fix
# 6. Verify endpoints work again

# Expected: <1 minute deployment, zero downtime
```

#### Test 3: Database Restore Rollback

```bash
# In staging environment
# 1. Create test data in Kanban tables
# 2. Create backup
# 3. Modify/corrupt test data
# 4. Restore from backup
# 5. Verify original test data restored

# Expected: <5 minutes, data integrity maintained
```

### Success Criteria

- [ ] All 3 tiers tested successfully in staging
- [ ] RTO targets met (Immediate, 1 min, 5 min)
- [ ] Zero data loss in Tier 1 & 2
- [ ] Acceptable data loss in Tier 3 (since backup timestamp)
- [ ] Documentation updated with actual timings
- [ ] Team trained on rollback procedures

---

## 📊 Rollback Metrics

### Track Per Incident

| Incident ID | Date | Tier Used | RTO (Actual) | Data Loss | Success | Notes |
|-------------|------|-----------|--------------|-----------|---------|-------|
| INC-001 | 2025-12-05 | Tier 1 | 8s | None | Yes | Feature flag worked |
| INC-002 | 2025-12-06 | Tier 2 | 1m 15s | None | Yes | Git revert successful |
| INC-003 | 2025-12-07 | Tier 3 | 4m 30s | 2 hours | Yes | DB restore from 10 AM backup |

### KPIs

- **Mean Time to Rollback (MTTR)**: Target <5 minutes
- **Rollback Success Rate**: Target >95%
- **Data Loss per Rollback**: Target <4 hours (backup frequency)
- **False Rollback Rate**: Target <5% (rollback wasn't necessary)

---

## 🚨 Emergency Contacts

### Escalation Path

**Level 1**: On-call Engineer
- **Contact**: [Engineer on Pagerduty]
- **Authority**: Execute Tier 1 & Tier 2 rollbacks

**Level 2**: Engineering Lead
- **Contact**: [Engineering Lead]
- **Authority**: Approve Tier 3 rollbacks

**Level 3**: CTO
- **Contact**: [CTO]
- **Authority**: Final approval for data-loss rollbacks

### Communication Channels

- **Slack**: #incidents channel
- **PagerDuty**: Alert all on-call
- **Status Page**: https://status.udo-platform.com
- **Email**: incidents@udo-platform.com

---

## 📚 Reference Documents

- `docs/KANBAN_IMPLEMENTATION_SUMMARY.md` - Overall rollback strategy
- `docs/ARCHITECTURE_STABILITY_ANALYSIS.md` - Risk assessment
- `backend/scripts/backup_database.sh` - Backup script
- `backend/scripts/restore_database.sh` - Restore script

---

**Document Status**: COMPLETE - READY FOR WEEK 4 DAY 3 TESTING
**Last Updated**: 2025-12-05
**Owner**: DevOps Team
**Approval**: Engineering Lead

---

**END OF ROLLBACK PROCEDURES**
