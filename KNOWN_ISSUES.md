# Known Issues

## Backend API Router Import Errors (2025-11-20)

**Status**: 🔴 Critical - Blocking frontend functionality

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

**Assignee**: Opus Model (next session)

**Estimated Fix Time**: 30-45 minutes with systematic approach

---

**Test Environment**:
- Python: 3.13.0
- OS: Windows (via pyenv-win)
- Backend: FastAPI + Uvicorn
- Frontend: Next.js 16.0.3 (localhost:3000)
