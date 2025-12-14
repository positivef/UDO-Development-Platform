# Known Issues

## All Issues Resolved (2025-12-04)

**Status**: ✅ ALL ISSUES RESOLVED

---

## Time Tracking Page Hydration Mismatch (2025-12-04)

**Status**: ✅ RESOLVED - Hydration mismatch fixed

**Issue**: `/time-tracking` page crashing with "Application error: a client-side exception has occurred"

**Error Message**:
```
Hydration failed because the server rendered HTML didn't match the client
```

**Impact**:
- ❌ `/time-tracking` - Client-side exception on page load
- ❌ User unable to view Time Tracking Dashboard
- ❌ 100% crash rate on this route

**Root Cause**:
1. **Dynamic Date Generation in Mock Data** (`useTimeTracking.ts:253-254`):
   - `Date.now()` generated different timestamps on server vs client
   - Even after `.toISOString()`, values differed between SSR and CSR

2. **Locale-Specific Date Formatting** (`page.tsx:34`):
   - `date-fns` format with "MMM dd" is timezone/locale dependent
   - Combined with dynamic dates → guaranteed hydration mismatch

**Resolution**:
1. ✅ Changed mock data to use fixed dates instead of `Date.now()`
   - Before: `new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()`
   - After: `'2025-11-18T00:00:00Z'`
2. ✅ Added `suppressHydrationWarning` to date display element
   - Tells React this element intentionally differs between SSR/CSR
   - Safe for presentation-only content like formatted dates

**Resolution Time**: 15 minutes

**Files Changed**:
- `web-dashboard/lib/hooks/useTimeTracking.ts`: Fixed mock data dates
- `web-dashboard/app/time-tracking/page.tsx`: Added suppressHydrationWarning

**Documentation**: `docs/HYDRATION_MISMATCH_FIX.md`

---

## Backend WebSocket Broadcast Function Error (2025-12-02)

**Status**: ✅ RESOLVED - broadcast_update function fixed

**Issue**: `/api/execute` endpoint returning 500 Internal Server Error due to undefined `broadcast_update` function

**Error Message**:
```
WARNING:app.core.error_handler:Medium severity error: 500: name 'broadcast_update' is not defined
```

**Impact**:
- ❌ `/api/execute` - 500 Internal Server Error
- ❌ Phase change WebSocket broadcasting failed

**Root Cause**:
`main.py` was calling undefined `broadcast_update()` function. The correct function is `connection_manager.broadcast_to_all()` from `websocket_handler.py`.

**Resolution**:
1. ✅ Imported `connection_manager` from `app.routers.websocket_handler`
2. ✅ Replaced `broadcast_update()` calls with `connection_manager.broadcast_to_all()`
3. ✅ Added `WEBSOCKET_AVAILABLE` check before broadcasting
4. ✅ Fixed both occurrences (lines 646 and 773)

**Resolution Time**: 10 minutes

**Files Changed**:
- `backend/main.py`: Added `connection_manager` import and fixed 2 broadcast calls

---

## Backend API Router Import Errors (2025-11-20)

**Status**: ✅ RESOLVED - All API routers working

**Issue**: Backend API routers failing to load with import errors

**Error Messages**:
```
WARNING:main:Routers not available: attempted relative import beyond top-level package
WARNING:main:Auth router not available: attempted relative import beyond top-level package
```

**Impact**:
- ❌ `/api/quality-metrics` - 404 Not Found
- ❌ `/api/projects` - 404 Not Found
- ❌ `/api/tasks` - 404 Not Found
- ❌ WebSocket `/ws` - Connection Error

**Root Cause**:
Complex Python import path dependencies in router chain:
```
app/routers/__init__.py → app/routers/*.py → app/models/ → app/core/ → database.py
```

**Attempted Fixes**:
1. ✅ Changed `from backend.app.` → `from app.` in constitutional files
2. ✅ Installed `psycopg2-binary==2.9.11`
3. ✅ Cleared Python `__pycache__`
4. ❌ Still encountering "attempted relative import beyond top-level package"

**Next Steps** (Opus Model Task):
1. Systematic import path analysis across all routers
2. Draw dependency graph to identify circular imports
3. Restructure imports to use absolute paths from backend root
4. Test each router individually
5. Verify all API endpoints respond correctly

**Workaround**:
- Core UDO system works (tests passing 19/19)
- Main API endpoints (`/api/health`, `/api/status`, `/api/metrics`) functional
- Week 2 features (GI Formula, C-K Theory) backend logic complete

**Priority**: HIGH - Affects user-facing dashboard functionality

**Resolution** (Opus Model - 2025-11-20):
1. ✅ Fixed relative import in `backend/app/core/dependencies.py`
   - Changed `from ...async_database` to `from async_database`
2. ✅ Installed missing dependencies:
   - `asyncpg` - for async PostgreSQL operations
   - `pyjwt` - for JWT authentication
   - `prometheus-client` - for monitoring
   - `psycopg2-binary` - for PostgreSQL support
3. ✅ All 13 routers now loading successfully
4. ✅ API endpoints verified working

**Resolution Time**: 10 minutes (27% of estimated time)

---

**Test Environment**:
- Python: 3.13.0
- OS: Windows (via pyenv-win)
- Backend: FastAPI + Uvicorn
- Frontend: Next.js 16.0.3 (localhost:3000)
