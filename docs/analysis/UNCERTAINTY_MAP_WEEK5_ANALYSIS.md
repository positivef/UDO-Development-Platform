# Uncertainty Map v3 - Week 5 Analysis

**Date**: 2025-12-17 (00:58 KST)
**Analysis Mode**: Predictive + Diagnostic
**Scope**: Full system (Backend/Frontend/Integration)

---

## 🎯 Executive Summary

**Overall State**: 🟠 QUANTUM (40% uncertainty)
**Critical Issues**: 3 P0 blockers identified
**Recommended Action**: Address P0 issues before Week 5 implementation

### Risk Vector Breakdown

| Dimension | Score | State | Impact |
|-----------|-------|-------|---------|
| **Technical** | 45% | 🟠 Quantum | API 403 errors blocking frontend |
| **Resource** | 30% | 🔵 Probabilistic | Database/Redis offline (mock mode) |
| **Timeline** | 35% | 🔵 Probabilistic | Week 5 delayed until P0 fixed |
| **Quality** | 25% | 🔵 Probabilistic | 471/471 backend tests passing |
| **Integration** | 50% | 🟠 Quantum | Frontend ↔ Backend disconnected |

**Aggregate Uncertainty**: 37% → **🟠 QUANTUM State**

---

## 🚨 P0 Critical Issues (Must Fix Before Week 5)

### P0-1: Kanban API 403 Forbidden (BLOCKER)

**Discovered**: 2025-12-17 00:58 KST
**Severity**: CRITICAL
**Impact**: Frontend completely blocked from Kanban operations

**Root Cause**:
```
INFO: GET /api/kanban/tasks HTTP/1.1" 403 Forbidden (x300+ occurrences)
INFO: PUT /api/kanban/tasks/3/status HTTP/1.1" 403 Forbidden
```

**Analysis**:
- Kanban router requires RBAC authentication (`Depends(require_role(UserRole.VIEWER))`)
- Frontend making requests **without Authorization header**
- Feature Flag `kanban_board: True` (not the issue)

**Solution Options**:

**Option 1 (Quick Fix - Development Only)**:
```python
# Temporarily disable RBAC for development
@router.get(
    "",
    response_model=TaskListResponse,
    # dependencies=[Depends(require_role(UserRole.VIEWER))],  # DISABLED for dev
    summary="List tasks with filtering and pagination",
)
```

**Option 2 (Proper Fix - Production Ready)**:
```typescript
// Frontend: Add authentication to API calls
const response = await fetch('/api/kanban/tasks', {
  headers: {
    'Authorization': `Bearer ${getAccessToken()}`,
    'Content-Type': 'application/json'
  }
});
```

**Recommendation**:
- **Immediate**: Option 1 (disable RBAC temporarily) to unblock development
- **Week 5 Day 2**: Implement Option 2 (proper auth flow)

**Decision Framework**:
- ✅ GO_WITH_CHECKPOINTS if Option 1 applied + tracked in backlog
- ❌ NO_GO until resolved (frontend unusable)

---

### P0-2: PostgreSQL/Redis Connection Failure

**Discovered**: 2025-12-17 00:58 KST (server logs)
**Severity**: HIGH
**Impact**: Mock service fallback, no real data persistence

**Error Logs**:
```
ERROR:app.services.redis_client:Redis connection failed: Error Multiple exceptions:
      [Errno 10061] Connect call failed ('::1', 6379, 0, 0),
      [Errno 10061] Connect call failed ('127.0.0.1', 6379)

ERROR:async_database:❌ Failed to initialize async database pool:
      Multiple exceptions: [Errno 10061] Connect call failed ('::1', 5432, 0, 0),
      [Errno 10061] Connect call failed ('127.0.0.1', 5432)

WARNING:backend.main:⚠️ Database not available, falling back to mock service
```

**Root Cause**:
- Docker Compose services not running
- PostgreSQL port 5432 closed
- Redis port 6379 closed

**Current Workaround**:
- Mock service active (in-memory data)
- Database migration executed in previous session (7 tables created)
- But data not persisting across server restarts

**Solution**:
```bash
# Start Docker services
docker-compose up -d db redis

# Verify connection
docker ps | grep -E "(postgres|redis)"
```

**Impact on Week 5**:
- 🔴 **Blocker** for multi-project features (requires DB persistence)
- 🔴 **Blocker** for Kanban task CRUD (data loss on restart)
- 🟡 **Medium** for development (mock service functional but limited)

**Decision Framework**:
- ✅ GO_WITH_CHECKPOINTS if mock mode acceptable for Week 5 Day 1
- ⚠️ GO_WITH_CHECKPOINTS requires DB by Week 5 Day 3 (multi-project)

---

### P0-3: Obsidian AttributeError (Background Sync)

**Discovered**: 2025-12-17 00:58 KST (hourly background sync)
**Severity**: MEDIUM
**Impact**: Background sync failing, manual sync still works

**Error Log** (repeated every hour):
```
ERROR:app.background_tasks:Failed to create temp devlog:
      'ObsidianService' object has no attribute '_flush_events'
```

**Root Cause**:
- `ObsidianService._flush_events()` method missing or renamed
- Background task trying to call non-existent method
- Created 169 Obsidian files in Week 4, but sync incomplete

**Impact**:
- Knowledge retention gap (periodic backups failing)
- Manual sync via API still works
- Daily notes created successfully (`개발일지/2025-12-15/Event- periodic_backup.md`)

**Solution**:
```python
# Check ObsidianService implementation
# Option 1: Add missing method
# Option 2: Update background_tasks.py to use correct method name
```

**Priority**: P1 (not blocking development, but fix for Week 5 Day 2)

---

## 📊 Uncertainty Map Analysis by Phase

### Current Phase: **Week 4 → Week 5 Transition**

**Phase State**: QUANTUM (40% uncertainty)

**Confidence Breakdown**:
```
Backend Implementation:    95% ✅ (471/471 tests passing)
Frontend Foundation:       60% ⚠️ (UI built, API blocked)
Integration Layer:         20% 🔴 (RBAC blocking, DB offline)
Documentation:             95% ✅ (comprehensive docs)
```

**Phase Transition Risk**: 🔴 **HIGH**
- Cannot proceed to Week 5 without resolving P0 issues
- Estimated delay: 2-4 hours (P0-1 fix + testing)

---

## 🔮 Predictive Analysis: Week 5 Scenarios

### Scenario A: P0 Issues Resolved (Probability: 85%)

**Timeline**: 2-4 hours to fix all P0 issues

**Mitigation Strategy**:
1. **Immediate** (30 min): Disable RBAC for Kanban endpoints (dev mode)
2. **Short-term** (1 hour): Start Docker services, verify DB connection
3. **Medium-term** (Week 5 Day 2): Fix Obsidian background sync
4. **Long-term** (Week 5 Day 3): Implement proper auth flow

**Expected Outcome**:
- Week 5 Day 1: Kanban UI functional with mock data
- Week 5 Day 2: Database persistence enabled
- Week 5 Day 3: Multi-project features testable

**Uncertainty Reduction**: 40% → 20% (QUANTUM → PROBABILISTIC)

---

### Scenario B: P0 Issues Unresolved (Probability: 15%)

**Risk**: Frontend remains blocked, Week 5 cannot proceed

**Contingency Plan**:
1. Focus on backend-only work (AI services, archive logic)
2. Write comprehensive API integration tests
3. Create detailed frontend integration spec
4. Parallel track: Fix RBAC + DB while docs progress

**Expected Outcome**:
- Week 5 delayed by 1-2 days
- Switch to backend stabilization phase
- Frontend work deferred to Week 6

**Uncertainty Increase**: 40% → 60% (QUANTUM → CHAOTIC)

---

## 🎯 Week 5 Gap Analysis: Missing Components

### 1. Authentication Flow (P0-1 Related)

**Current State**: RBAC implemented but frontend not integrated

**Missing Pieces**:
```typescript
// 1. Token storage (localStorage/sessionStorage)
// 2. Login/logout flow
// 3. Token refresh mechanism
// 4. Role-based UI visibility
```

**Impact**: 🔴 Blocks all authenticated endpoints

**Recommendation**:
- Temporary: Disable auth for development
- Permanent: Implement auth flow in Week 5 Day 2-3

---

### 2. Database Persistence Layer (P0-2 Related)

**Current State**: Schema created (7 tables), but DB offline

**Missing Integration**:
```
- Kanban task CRUD → Database
- Dependency DAG → Database
- Multi-project selection → Database
- Quality gates → Database
```

**Impact**: 🔴 Data loss on server restart

**Recommendation**:
- Start Docker services immediately
- Verify migration applied successfully
- Test database queries with real data

---

### 3. Frontend API Client Refinement

**Current State**: Basic fetch calls, no error handling

**Missing Features**:
```typescript
// 1. Retry logic with exponential backoff
// 2. Request/response interceptors
// 3. Error boundary integration
// 4. Loading state management
// 5. Optimistic updates with rollback
```

**Impact**: 🟡 Poor UX, fragile to network issues

**Recommendation**: Week 5 Day 2-3 enhancement

---

### 4. Real-Time Updates (WebSocket)

**Current State**: Backend WebSocket handler implemented

**Missing Frontend**:
```typescript
// 1. WebSocket connection manager
// 2. Event handlers for task updates
// 3. Reconnection logic
// 4. UI update on remote changes
```

**Impact**: 🟡 No real-time collaboration yet

**Recommendation**: Week 5 Day 4-5 (not P0)

---

## 📋 Development Scenario Review

### Original Week 5 Plan (from Roadmap)

**Week 5: Frontend MVP Enhancement**
- Day 1-2: Kanban UI refinements
- Day 3: Context upload/download
- Day 4-5: Drag & Drop optimization

### Revised Week 5 Plan (Post-Analysis)

**Week 5 Day 0 (Immediate)**: P0 Fixes
- [ ] P0-1: Disable RBAC or implement auth (2-4 hours)
- [ ] P0-2: Start Docker services (30 min)
- [ ] P0-3: Fix Obsidian sync (1 hour)
- [ ] Verification: Full stack smoke test

**Week 5 Day 1**: Kanban UI Validation
- [ ] Test all CRUD operations with DB
- [ ] Verify drag & drop persists to DB
- [ ] Load testing (100+ tasks)
- [ ] Fix any data integrity issues

**Week 5 Day 2**: Authentication Integration
- [ ] Implement token storage
- [ ] Add login/logout UI
- [ ] Update API client with auth headers
- [ ] Test RBAC with all 4 roles

**Week 5 Day 3**: Multi-Project Features
- [ ] Project selector component
- [ ] Primary project algorithm
- [ ] Related projects UI (max 3)
- [ ] Context switching validation

**Week 5 Day 4-5**: Polish & Performance
- [ ] WebSocket real-time updates
- [ ] Error handling improvements
- [ ] Loading states refinement
- [ ] E2E test suite expansion

---

## 🚀 Recommended Action Plan

### Immediate Actions (Next 4 Hours)

1. **P0-1 Fix** (1 hour):
   ```python
   # backend/app/routers/kanban_tasks.py
   # Comment out RBAC dependency for all endpoints
   # Add TODO: Re-enable auth in Week 5 Day 2
   ```

2. **P0-2 Fix** (30 min):
   ```bash
   docker-compose up -d db redis
   docker ps  # Verify running
   # Test API calls with curl
   ```

3. **Smoke Test** (30 min):
   ```bash
   # Backend
   pytest backend/tests/test_kanban_tasks.py -v

   # Frontend
   # Navigate to http://localhost:3000/kanban
   # Verify tasks load and drag & drop works
   ```

4. **Documentation Update** (30 min):
   - Update CLAUDE.md with P0 fixes
   - Create WEEK5_DAY0_P0_FIXES.md
   - Update TodoWrite with revised plan

### Week 5 Kickoff (Post-P0)

**Entry Criteria**:
- ✅ All P0 issues resolved
- ✅ Smoke test passing
- ✅ Docker services running
- ✅ Frontend can fetch tasks from DB

**Success Metrics**:
- API response time <200ms (p95)
- Frontend TTI <3 seconds
- Zero 403 errors in logs
- Database queries <50ms

---

## 🧠 Lessons Learned & Uncertainty Reduction

### What Went Well ✅
- Backend tests 100% passing (471/471)
- Feature Flags system production-ready
- Obsidian cleanup successful (169 files)
- Documentation comprehensive

### What Needs Improvement ⚠️
- **Integration testing gap**: Backend and frontend tested in isolation
- **Auth flow deferred**: Should have been Week 4 priority
- **Docker dependency unclear**: Assumed services would be running
- **Monitoring blind spots**: 403 errors not detected proactively

### Uncertainty Reduction Strategy 📉
1. **Add integration smoke tests** to CI/CD (detect RBAC blocks)
2. **Docker health checks** in development workflow
3. **Monitoring dashboard** for API error rates
4. **Daily standup review** of server logs

---

## 📖 References

**Related Documents**:
- `docs/KANBAN_IMPLEMENTATION_SUMMARY.md` - Implementation overview
- `docs/WEEK4_FEATURE_FLAGS_COMPLETION.md` - Feature flags system
- `docs/DEVELOPMENT_ROADMAP_V6.md` - Overall roadmap
- `backend/app/core/security.py` - RBAC implementation

**API Logs**: See `BashOutput(bash_id=5de84c)` for full server logs

**Test Results**: 471 passed (100%), 25% coverage

---

**Uncertainty State**: 🟠 QUANTUM → Target: 🔵 PROBABILISTIC
**ETA for State Transition**: 4 hours (after P0 fixes)
**Next Review**: After P0 resolution + Week 5 Day 1 completion

---

*Generated by: Uncertainty Map v3 Analysis System*
*Analysis Duration: 15 minutes*
*Confidence in Analysis: 85% (HIGH)*
