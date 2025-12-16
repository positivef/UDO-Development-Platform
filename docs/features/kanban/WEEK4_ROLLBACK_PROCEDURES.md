# Week 4 Rollback Procedures

**Date**: 2025-12-16
**Status**: Active
**Purpose**: 3-Tier rollback validation for production safety

---

## Overview

This document defines the rollback strategy for the Kanban-UDO integration. The 3-tier approach ensures rapid recovery with minimal data loss.

### Rollback Tiers Summary

| Tier | Method | Time | Data Impact | Use Case |
|------|--------|------|-------------|----------|
| **Tier 1** | Feature Flag | <10s | None | Minor issues, UX problems |
| **Tier 2** | Git Revert | ~1 min | None | Code bugs, API errors |
| **Tier 3** | DB Restore | ~5 min | Possible | Data corruption, critical failure |

---

## Tier 1: Feature Flag Rollback

### Description
Instant disable of Kanban features without deployment. Uses runtime configuration to toggle features.

### Implementation

#### Feature Flags Configuration
```python
# backend/app/core/feature_flags.py

FEATURE_FLAGS = {
    "kanban_board": True,           # Main Kanban UI
    "kanban_ai_suggest": True,      # AI task suggestion (Q2)
    "kanban_archive": True,         # Archive + AI summary (Q6)
    "kanban_dependencies": True,    # Hard block dependencies (Q7)
    "kanban_multi_project": True,   # Multi-project support (Q5)
    "kanban_obsidian_sync": True,   # Obsidian integration
}

def is_feature_enabled(feature: str) -> bool:
    return FEATURE_FLAGS.get(feature, False)
```

#### API Endpoint for Runtime Toggle
```python
# backend/app/routers/admin.py

@router.post("/api/admin/feature-flag/{flag}")
async def toggle_feature_flag(flag: str, enabled: bool, admin_key: str):
    """Toggle feature flag at runtime (admin only)"""
    if admin_key != os.getenv("ADMIN_KEY"):
        raise HTTPException(403, "Unauthorized")

    if flag not in FEATURE_FLAGS:
        raise HTTPException(404, f"Unknown feature: {flag}")

    FEATURE_FLAGS[flag] = enabled
    logger.warning(f"Feature flag '{flag}' set to {enabled} by admin")
    return {"flag": flag, "enabled": enabled}
```

### Rollback Procedure

1. **Identify Issue**
   ```
   Issue Type: [ ] UX problem [ ] Minor bug [ ] Performance
   Affected Feature: _________________
   ```

2. **Disable Feature**
   ```bash
   # Via API
   curl -X POST "http://localhost:8000/api/admin/feature-flag/kanban_ai_suggest" \
        -H "Content-Type: application/json" \
        -d '{"enabled": false, "admin_key": "$ADMIN_KEY"}'

   # Via environment variable (restart required)
   export KANBAN_AI_SUGGEST=false
   ```

3. **Verify Rollback**
   - [ ] Feature disabled in UI
   - [ ] API returns appropriate error
   - [ ] No new errors in logs

4. **Recovery Time**: <10 seconds

### Feature Flag Matrix

| Flag | Disable Impact | Safe to Disable |
|------|----------------|-----------------|
| `kanban_board` | Full Kanban UI hidden | ⚠️ Major |
| `kanban_ai_suggest` | AI button hidden | ✅ Safe |
| `kanban_archive` | Archive disabled | ✅ Safe |
| `kanban_dependencies` | Dependencies ignored | ⚠️ Careful |
| `kanban_multi_project` | Single project only | ✅ Safe |
| `kanban_obsidian_sync` | Sync disabled | ✅ Safe |

---

## Tier 2: Git Revert Rollback

### Description
Revert to previous working commit and redeploy. Used for code bugs that can't be fixed with feature flags.

### Pre-requisites
- [ ] Known good commit hash recorded
- [ ] CI/CD pipeline configured
- [ ] Deployment automation ready

### Current Good Commits

| Date | Commit Hash | Description | Verified |
|------|-------------|-------------|----------|
| 2025-12-16 | `HEAD` | Week 3 Complete (471/471 tests) | ✅ |
| 2025-12-15 | `HEAD~1` | Week 2 Day 4 Complete | ✅ |
| 2025-12-14 | `HEAD~5` | Week 2 Day 3 Start | ✅ |

### Rollback Procedure

1. **Identify Bad Commit**
   ```bash
   git log --oneline -10
   # Find the problematic commit
   ```

2. **Create Rollback Branch**
   ```bash
   # NEVER force push to main
   git checkout -b rollback/kanban-fix
   git revert HEAD  # Or specific commit
   git push origin rollback/kanban-fix
   ```

3. **Create PR and Deploy**
   ```bash
   gh pr create --title "Rollback: Kanban issue fix" \
                --body "Rolling back due to: [ISSUE DESCRIPTION]"
   ```

4. **Verify Rollback**
   - [ ] All tests pass on rollback branch
   - [ ] Issue no longer reproducible
   - [ ] No new regressions

5. **Recovery Time**: ~1 minute (with CI/CD)

### Git Revert Commands Reference

```bash
# Revert single commit
git revert <commit-hash>

# Revert range of commits
git revert HEAD~3..HEAD

# Revert merge commit
git revert -m 1 <merge-commit-hash>

# Revert without auto-commit (for review)
git revert --no-commit <commit-hash>
```

---

## Tier 3: Database Restore

### Description
Full database restore from backup. Last resort for data corruption or critical failures.

### Pre-requisites
- [ ] Automated backups configured
- [ ] Backup verification tested
- [ ] Restore procedure validated

### Current Backup Status

| Type | Frequency | Retention | Location |
|------|-----------|-----------|----------|
| Full | Daily | 7 days | S3/Local |
| Incremental | Hourly | 24 hours | S3/Local |
| Point-in-time | Continuous | 7 days | WAL archive |

### Mock Service Note
Currently using in-memory mock service. For production:
- Configure PostgreSQL backup
- Enable WAL archiving
- Set up automated restore testing

### Rollback Procedure

1. **Stop Application**
   ```bash
   # Graceful shutdown
   pkill -f "uvicorn backend.main:app"
   # Or Docker
   docker-compose stop backend
   ```

2. **Restore Database**
   ```bash
   # PostgreSQL restore
   pg_restore -d udo_db backup_2025-12-16.dump

   # Or point-in-time recovery
   pg_restore --target-time="2025-12-16 10:00:00" -d udo_db
   ```

3. **Verify Data Integrity**
   ```sql
   -- Check task counts
   SELECT COUNT(*) FROM kanban_tasks;

   -- Check for orphaned records
   SELECT * FROM kanban_tasks WHERE phase_id NOT IN (SELECT id FROM phases);

   -- Verify timestamps
   SELECT * FROM kanban_tasks WHERE updated_at > NOW();
   ```

4. **Restart Application**
   ```bash
   .venv/Scripts/python.exe -m uvicorn backend.main:app --reload
   ```

5. **Recovery Time**: ~5 minutes

### Data Recovery Scripts

```python
# scripts/recover_data.py

async def verify_data_integrity():
    """Check data consistency after restore"""
    issues = []

    # Check task-phase relationships
    orphaned = await db.execute("""
        SELECT task_id FROM kanban_tasks
        WHERE phase_id NOT IN (SELECT id FROM phases)
    """)
    if orphaned:
        issues.append(f"Orphaned tasks: {len(orphaned)}")

    # Check archive references
    invalid_archives = await db.execute("""
        SELECT id FROM task_archives
        WHERE task_id NOT IN (SELECT task_id FROM kanban_tasks)
    """)
    if invalid_archives:
        issues.append(f"Invalid archives: {len(invalid_archives)}")

    return issues
```

---

## Rollback Decision Tree

```
Issue Detected
    │
    ├── Is it a UX/minor issue?
    │   └── YES → Tier 1: Feature Flag (< 10s)
    │
    ├── Is it a code bug?
    │   └── YES → Tier 2: Git Revert (~ 1 min)
    │
    └── Is data corrupted?
        └── YES → Tier 3: DB Restore (~ 5 min)
```

---

## Rollback Validation Checklist

### Pre-Deployment

- [ ] Feature flags implemented and tested
- [ ] Known good commit hash recorded
- [ ] Database backup verified
- [ ] Rollback documentation reviewed by team
- [ ] Emergency contacts identified

### Post-Rollback

- [ ] Issue resolved
- [ ] No new errors in logs
- [ ] User-facing functionality verified
- [ ] Monitoring alerts cleared
- [ ] Incident report created

---

## Emergency Contacts

| Role | Name | Contact | Escalation |
|------|------|---------|------------|
| Primary On-call | TBD | TBD | Immediate |
| Backup On-call | TBD | TBD | 15 min |
| Engineering Lead | TBD | TBD | 30 min |

---

## Incident Response Template

```markdown
## Incident Report: [TITLE]

**Date**: YYYY-MM-DD HH:MM
**Severity**: P0/P1/P2/P3
**Status**: Active/Resolved

### Summary
[Brief description of the issue]

### Timeline
- HH:MM - Issue detected
- HH:MM - Rollback initiated
- HH:MM - Rollback completed
- HH:MM - Issue resolved

### Impact
- Users affected: ___
- Duration: ___ minutes
- Data loss: Yes/No

### Root Cause
[Description of what caused the issue]

### Resolution
- Rollback tier used: 1/2/3
- Specific actions taken:
  1.
  2.
  3.

### Prevention
- [ ] Action item 1
- [ ] Action item 2
```

---

## Testing the Rollback Procedures

### Tier 1 Test
```bash
# 1. Enable feature
curl -X POST "http://localhost:8000/api/admin/feature-flag/kanban_ai_suggest" \
     -d '{"enabled": true, "admin_key": "test"}'

# 2. Verify enabled
curl "http://localhost:8000/api/kanban/ai/suggest" # Should work

# 3. Disable feature
curl -X POST "http://localhost:8000/api/admin/feature-flag/kanban_ai_suggest" \
     -d '{"enabled": false, "admin_key": "test"}'

# 4. Verify disabled
curl "http://localhost:8000/api/kanban/ai/suggest" # Should return 503
```

### Tier 2 Test
```bash
# 1. Create test commit
echo "test" >> test.txt && git add test.txt && git commit -m "Test commit"

# 2. Revert
git revert HEAD --no-edit

# 3. Verify
git log --oneline -3  # Should show revert commit
```

### Tier 3 Test
```bash
# 1. Create backup
pg_dump udo_db > backup_test.dump

# 2. Modify data
psql udo_db -c "DELETE FROM kanban_tasks LIMIT 1"

# 3. Restore
pg_restore -d udo_db backup_test.dump

# 4. Verify
psql udo_db -c "SELECT COUNT(*) FROM kanban_tasks"
```

---

*Document Version*: 1.0
*Last Updated*: 2025-12-16
*Author*: Claude Code
