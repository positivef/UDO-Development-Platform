# Kanban Drag-Drop API Error - Troubleshooting Context

**Date**: 2025-12-23
**Priority**: CRITICAL
**Status**: Unresolved

---

## 🚨 Problem Statement

When dragging and dropping a task card on the Kanban board, the frontend displays this error:

```
Failed to update task status: KanbanAPIError: [object Object]
    at apiFetch (kanban.ts:41:13)
    at async KanbanBoard.useCallback[handleDragEnd] (KanbanBoard.tsx:133:27)
```

**Expected Behavior**: Task status should update smoothly when dragged to a different column.

**Actual Behavior**:
- Browser console shows `KanbanAPIError: [object Object]`
- Backend returns `422 Unprocessable Content`
- Task status does NOT change

---

## 🔍 Root Cause Analysis

### Backend Issue

**Backend Log** (critical lines):
```
WARNING: [KANBAN] Database not available, using MockKanbanTaskService:
         Database pool not initialized. Call initialize() first.

INFO: "PUT /api/kanban/tasks/{id}/status HTTP/1.1" 422 Unprocessable Content

ERROR: Failed to initialize async database pool:
       [Errno 10061] Connect call failed ('127.0.0.1', 5432)
```

**Key Findings**:
1. Backend cannot connect to PostgreSQL on port 5432
2. Falling back to MockKanbanTaskService
3. Mock service returns 422 validation error on status update

### Database Connection Test Results

✅ **Docker Container Status**:
```bash
$ docker ps | grep postgres
udo_postgres   pgvector/pgvector:pg16   Up 8 hours (healthy)   0.0.0.0:5432->5432/tcp
```

✅ **Direct Connection Test (SUCCEEDS)**:
```bash
$ docker exec udo_postgres psql -U udo_dev -d udo_v3 -c "SELECT 1;"
 ?column?
----------
        1
(1 row)
```

✅ **Python asyncpg Test (SUCCEEDS)**:
```python
import asyncpg
import asyncio
asyncio.run(asyncpg.connect(
    'postgresql://udo_dev:dev_password_123@127.0.0.1:5432/udo_v3'
))
# No errors - connection successful!
```

❌ **FastAPI Backend Connection (FAILS)**:
```
ERROR: [Errno 10061] Connect call failed ('127.0.0.1', 5432)
```

---

## 🛠️ What We've Tried

### 1. Fixed Backend Code Bugs ✅

**File**: `backend/app/services/kanban_task_service.py`

**Bug 1** (Line 475, 495, 518):
```python
# BEFORE (WRONG):
status_request.new_status.value  # AttributeError: 'str' has no attribute 'value'

# AFTER (FIXED):
status_request.new_status  # Already a string, not an Enum
```

**Bug 2** (Line 496, 519):
```python
# BEFORE (WRONG):
datetime.now(UTC)  # Timezone-aware datetime

# AFTER (FIXED):
datetime.now(UTC).replace(tzinfo=None)  # PostgreSQL expects timezone-naive
```

**Bug 3** (Line 527-529):
```python
# ADDED (FIX):
task_data = dict(row)
if task_data.get('violated_articles') is None:
    task_data['violated_articles'] = []  # Pydantic expects list, not None
task = Task(**task_data)
```

### 2. Restarted Backend Multiple Times ⚠️

**Problem**: Backend always fails to connect to database on startup.

**Evidence**:
```python
# Test script works perfectly:
$ python scripts/test_kanban_api.py
✅ Success! New status: pending → completed

# But browser still gets 422 error
```

**Hypothesis**: The test script somehow uses a different backend instance or connection path.

---

## 📋 Environment Details

### System
- **OS**: Windows 10 (Build 10.0.22631.6199)
- **Shell**: PowerShell + Git Bash (WSL is blocked)
- **Python**: 3.13.0 (pyenv-win, venv)

### Backend
- **Framework**: FastAPI + Uvicorn
- **Database Driver**: asyncpg (async PostgreSQL)
- **Port**: 8000 (multiple processes were running, cleaned up)
- **Current PID**: 100280

### Database
- **PostgreSQL**: 16 (pgvector/pgvector:pg16)
- **Container Name**: udo_postgres
- **Host**: 127.0.0.1
- **Port**: 5432
- **Database**: udo_v3
- **User**: udo_dev
- **Password**: dev_password_123

### Configuration

**File**: `backend/.env`
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=udo_v3
DB_USER=udo_dev
DB_PASSWORD=dev_password_123
DB_POOL_MIN=2
DB_POOL_MAX=10
```

**File**: `backend/async_database.py` (relevant sections)
```python
class AsyncDatabaseConfig:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.database = os.getenv("DB_NAME", "udo_dev")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "postgres")

    def get_dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@async_retry(max_attempts=3, delay=1.0, backoff=2.0)
async def initialize(self):
    self._pool = await asyncpg.create_pool(
        dsn=self.config.get_dsn(),
        min_size=self.config.min_size,
        max_size=self.config.max_size,
        timeout=5.0,
        command_timeout=10.0,
    )
```

**File**: `backend/main.py` (startup event)
```python
@app.on_event("startup")
async def startup_event():
    # ... (Redis initialization)

    # Initialize async database
    try:
        await initialize_async_database()
        logger.info("[OK] Async database initialized")

        # Initialize project context service
        await project_context_service.initialize_default_project()
        logger.info("[OK] Project context service initialized")
    except Exception as e:
        logger.warning(f"[WARN] Database not available: {e}")
        # Falls back to MockProjectService
```

---

## 🎯 Critical Questions

1. **Why does Python asyncpg connection succeed but FastAPI fails?**
   - Same connection string
   - Same environment variables
   - Same host/port

2. **Why is the error `[Errno 10061]` (Connection refused)?**
   - PostgreSQL is running and healthy
   - Port 5432 is exposed (0.0.0.0:5432->5432/tcp)
   - Direct psql and Python connections work

3. **Is there a Windows firewall or network issue?**
   - Only affects FastAPI/uvicorn process
   - Other Python processes can connect fine

4. **Is the .env file being loaded correctly?**
   - Located at: `backend/.env`
   - Loaded in `async_database.py` with `load_dotenv()`

---

## 🔧 Requested Solution

**Please diagnose and fix the database connection issue so that:**

1. ✅ FastAPI backend connects to PostgreSQL on startup
2. ✅ Uses real KanbanTaskService (not Mock)
3. ✅ Browser drag-drop returns HTTP 200 (not 422)
4. ✅ Task status persists in database

---

## 📁 Key Files

**Backend Files**:
- `backend/main.py` (startup event, lines 738-848)
- `backend/async_database.py` (connection pool, lines 71-126)
- `backend/app/services/kanban_task_service.py` (CRUD operations, already fixed)
- `backend/app/routers/kanban_tasks.py` (API endpoints)
- `backend/.env` (database configuration)

**Frontend Files**:
- `web-dashboard/lib/api/kanban.ts` (API client, line 41 throws error)
- `web-dashboard/components/kanban/KanbanBoard.tsx` (drag-drop handler, line 133)

**Test Files**:
- `scripts/test_kanban_api.py` (works perfectly, proves API logic is correct)
- `scripts/restart_backend.py` (automated restart script)

---

## 🧪 How to Reproduce

1. **Start Backend**:
   ```bash
   .venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Check Logs** (watch for database connection error):
   ```
   ERROR: Failed to initialize async database pool:
          [Errno 10061] Connect call failed ('127.0.0.1', 5432)
   ```

3. **Open Browser**: http://localhost:3000/kanban

4. **Drag a Task Card** to another column

5. **See Error** in browser console:
   ```
   Failed to update task status: KanbanAPIError: [object Object]
   ```

6. **Check Backend Response**: HTTP 422 Unprocessable Content

---

## 💡 Possible Debugging Steps

1. **Check if uvicorn process can resolve localhost**:
   ```python
   import socket
   socket.gethostbyname('localhost')  # Should return '127.0.0.1'
   ```

2. **Try connecting with host='127.0.0.1' explicitly** (not 'localhost'):
   ```python
   # In backend/.env
   DB_HOST=127.0.0.1  # Instead of localhost
   ```

3. **Check if asyncpg uses different socket than psycopg2**:
   - asyncpg uses TCP socket
   - Maybe Windows blocks TCP but allows Unix socket?

4. **Enable asyncpg debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   logging.getLogger('asyncpg').setLevel(logging.DEBUG)
   ```

5. **Check if Docker internal network is accessible from host**:
   ```bash
   docker network inspect bridge
   # Check if udo_postgres has correct IP
   ```

---

## 🚀 Expected Outcome

After fixing the database connection:

```bash
# Backend startup log should show:
INFO: [OK] Async database pool initialized: udo_v3
INFO:    Pool size: min=2, max=10

# NOT this:
ERROR: [FAIL] Failed to initialize async database pool
WARNING: [KANBAN] Database not available, using MockKanbanTaskService
```

Then browser drag-drop should work:
```
# Browser console:
✅ Task status updated successfully

# Backend log:
INFO: "PUT /api/kanban/tasks/{id}/status HTTP/1.1" 200 OK
```

---

**Thank you for your help!**
