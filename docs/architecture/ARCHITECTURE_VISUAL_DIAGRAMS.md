# UDO Development Platform - Visual Architecture Diagrams

**Date**: 2025-12-14

---

## 1. Current System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           UDO Development Platform                          │
│                         (3-Tier Web Application)                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT TIER                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     Next.js 16 (React 19)                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │  Dashboard   │  │   Kanban     │  │ Time Track   │                │ │
│  │  │  (Main)      │  │   Board      │  │              │                │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │  Quality     │  │  CK Theory   │  │ GI Formula   │                │ │
│  │  │  Metrics     │  │              │  │              │                │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │ │
│  │                                                                        │ │
│  │  State Management:                                                    │ │
│  │  ┌─────────────────┐         ┌──────────────────┐                    │ │
│  │  │ Zustand Store   │         │ Tanstack Query   │                    │ │
│  │  │ (UI State)      │◄───────►│ (Server State)   │                    │ │
│  │  │ - Selected Task │         │ - Tasks Cache    │                    │ │
│  │  │ - Filters       │         │ - Metrics Cache  │                    │ │
│  │  │ - View Mode     │         │ - Auto-refetch   │                    │ │
│  │  └─────────────────┘         └──────────────────┘                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│                          ▼ HTTP/REST (JSON)                                  │
│                          ▼ WebSocket (Real-time)                             │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION TIER                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Backend (Python)                            │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │                     main.py (902 lines)                          │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │ Router Registration (16 routers - NEEDS REFACTOR)           │ │ │ │
│  │  │  │ - Core: version_history, quality_metrics, constitutional   │ │ │ │
│  │  │  │ - Theory: gi_formula, ck_theory                            │ │ │ │
│  │  │  │ - Kanban: tasks, dependencies, projects, archive           │ │ │ │
│  │  │  │ - Integration: auth, obsidian, websocket                   │ │ │ │
│  │  │  └─────────────────────────────────────────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │ │
│  │  │   Routers       │  │   Services      │  │   Models        │      │ │
│  │  │   (API Layer)   │─►│   (Logic)       │─►│   (Data)        │      │ │
│  │  │                 │  │                 │  │                 │      │ │
│  │  │ - /api/kanban   │  │ - KanbanTask    │  │ - Task          │      │ │
│  │  │ - /api/quality  │  │ - Quality       │  │ - QualityMetric │      │ │
│  │  │ - /api/time     │  │ - TimeTracking  │  │ - TimeEntry     │      │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘      │ │
│  │                                                                        │ │
│  │  Dependency Injection (PARTIAL - 2/16 services):                      │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  app/core/dependencies.py                                        │ │ │
│  │  │  ✅ TimeTrackingService → Depends(get_time_tracking_service)    │ │ │
│  │  │  ✅ ObsidianService → Depends(get_obsidian_service)              │ │ │
│  │  │  ❌ 14 other services → Direct instantiation (needs DI)          │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  Error Handling (EXCELLENT):                                          │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  app/core/error_handler.py                                       │ │ │
│  │  │  - Global exception handlers                                     │ │ │
│  │  │  - Category-based recovery (DB, Network, Auth, etc.)            │ │ │
│  │  │  - Exponential backoff with circuit breaker                     │ │ │
│  │  │  - Severity classification (LOW/MEDIUM/HIGH/CRITICAL)           │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│                          ▼ SQL Queries (asyncpg)                             │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                             DATA TIER                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        PostgreSQL Database                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │   Tasks      │  │  Time Entries│  │   Projects   │                │ │
│  │  │              │  │              │  │              │                │ │
│  │  │ - task_id    │  │ - entry_id   │  │ - project_id │                │ │
│  │  │ - title      │  │ - task_id    │  │ - name       │                │ │
│  │  │ - status     │  │ - duration   │  │ - created_at │                │ │
│  │  │ - phase      │  │ - ai_assisted│  │              │                │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │ Dependencies │  │   Archives   │  │ Quality Data │                │ │
│  │  │              │  │              │  │              │                │ │
│  │  │ - task_id    │  │ - task_id    │  │ - metric_id  │                │ │
│  │  │ - depends_on │  │ - summary    │  │ - score      │                │ │
│  │  │ - type       │  │ - archived_at│  │ - analyzed_at│                │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │ │
│  │                                                                        │ │
│  │  Connection Pool:                                                      │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  asyncpg pool (10 connections - NOT TUNED)                       │ │ │
│  │  │  ⚠️  Need: 50+ connections for production                        │ │ │
│  │  │  ⚠️  Need: Read replicas for analytics queries                   │ │ │
│  │  │  ⚠️  Need: pgBouncer for connection pooling                      │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL INTEGRATIONS                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      MCP Server Integration                            │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │  ThreeAICollaborationBridge (TIGHTLY COUPLED)                   │  │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │ │
│  │  │  │Context7  │  │Sequential│  │  Magic   │  │Morphllm  │        │  │ │
│  │  │  │(Docs)    │  │(Reason)  │  │(UI Gen)  │  │(Bulk)    │        │  │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │  │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │  │ │
│  │  │  │ Serena   │  │Playwright│  │  Codex   │                       │  │ │
│  │  │  │(Symbol)  │  │(E2E Test)│  │(Review)  │                       │  │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘                       │  │ │
│  │  │                                                                   │  │ │
│  │  │  ⚠️  Problem: Hardcoded server initialization                    │  │ │
│  │  │  ⚠️  Need: Plugin registry with fallbacks                        │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │  Obsidian Knowledge Base Sync                                   │  │ │
│  │  │  - Hybrid: Git hook (auto) + API (manual)                       │  │ │
│  │  │  - Debouncing: <3s prevents duplicate syncs                     │  │ │
│  │  │  - Markdown generation: Tasks → structured notes                │  │ │
│  │  │  - ⚠️  Missing: Conflict resolution (3-way merge)               │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                        REAL-TIME COMMUNICATION                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Custom WebSocket Handler (NOT PRODUCTION-READY)                      │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  ConnectionManager (In-Memory)                                   │ │ │
│  │  │  - active_connections: Dict[session_id, WebSocket]              │ │ │
│  │  │  - project_sessions: Dict[project_id, Set[session_id]]          │ │ │
│  │  │                                                                   │ │ │
│  │  │  Methods:                                                         │ │ │
│  │  │  - broadcast_to_all(message)                                     │ │ │
│  │  │  - broadcast_to_project(message, project_id)                    │ │ │
│  │  │  - send_personal_message(message, session_id)                   │ │ │
│  │  │                                                                   │ │ │
│  │  │  ⚠️  Limitations:                                                 │ │ │
│  │  │  - No message persistence (lost on disconnect)                   │ │ │
│  │  │  - Single server (no horizontal scaling)                         │ │ │
│  │  │  - No authentication on WebSocket connections                    │ │ │
│  │  │  - Messages lost if backend restarts                             │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  Frontend WebSocket Client:                                            │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  useEffect(() => {                                               │ │ │
│  │  │    const ws = new WebSocket('ws://localhost:8000/ws/dashboard')  │ │ │
│  │  │    ws.onmessage = (event) => {                                   │ │ │
│  │  │      queryClient.invalidateQueries([event.data.type])            │ │ │
│  │  │    }                                                              │ │ │
│  │  │  })                                                               │ │ │
│  │  │                                                                   │ │ │
│  │  │  ✅ Auto-reconnection on disconnect                               │ │ │
│  │  │  ✅ Query invalidation for cache refresh                          │ │ │
│  │  │  ⚠️  No backoff on reconnect (immediate retry)                    │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow Diagram (Task Creation)

```
┌─────────────┐
│   User      │
│   Browser   │
└─────┬───────┘
      │
      │ 1. Fill form + click "Create Task"
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Next.js Frontend (web-dashboard/)                          │
│                                                              │
│  TaskDetailModal.tsx:                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ const createMutation = useMutation({                   │ │
│  │   mutationFn: (task) => kanbanAPI.createTask(task)     │ │
│  │ })                                                      │ │
│  │                                                          │ │
│  │ createMutation.mutate({                                 │ │
│  │   title: "New Feature",                                 │ │
│  │   description: "Add login page",                        │ │
│  │   phase: "implementation",                              │ │
│  │   priority: "high",                                     │ │
│  │   status: "pending"                                     │ │
│  │ })                                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          │ 2. HTTP POST                      │
│                          ▼                                   │
│  kanban.ts (API Client):                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ async function createTask(task: CreateTaskRequest) {   │ │
│  │   return apiFetch<KanbanTask>('/tasks', {              │ │
│  │     method: 'POST',                                     │ │
│  │     body: JSON.stringify(task)                          │ │
│  │   })                                                     │ │
│  │ }                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ 3. POST /api/kanban/tasks (JSON)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend (backend/)                                 │
│                                                              │
│  kanban_tasks.py (Router):                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ @router.post("/tasks", response_model=Task)            │ │
│  │ async def create_task(                                  │ │
│  │   task_data: TaskCreate,                                │ │
│  │   service = Depends(get_kanban_task_service)  # ❌ TODO│ │
│  │ ):                                                       │ │
│  │   return await service.create_task(task_data)           │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          │ 4. Validate Pydantic model        │
│                          ▼                                   │
│  kanban_task_service.py (Service):                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ async def create_task(self, task_data: TaskCreate):    │ │
│  │   # Business logic                                      │ │
│  │   task = Task(                                          │ │
│  │     task_id=uuid4(),                                    │ │
│  │     **task_data.dict(),                                 │ │
│  │     created_at=datetime.now()                           │ │
│  │   )                                                      │ │
│  │                                                          │ │
│  │   # Save to database                                    │ │
│  │   await self.db.execute(insert(tasks).values(...))     │ │
│  │                                                          │ │
│  │   # Sync to Obsidian                                    │ │
│  │   await obsidian_service.sync_task(task, "create")     │ │
│  │                                                          │ │
│  │   return task                                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          │ 5. INSERT query                   │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         PostgreSQL Database                            │ │
│  │  INSERT INTO tasks (task_id, title, ...) VALUES (...)  │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          │ 6. Return task                    │
│                          ▼                                   │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ 7. Broadcast event (WebSocket)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  websocket_handler.py:                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ await connection_manager.broadcast_to_all({            │ │
│  │   "type": "task_created",                               │ │
│  │   "data": task.dict()                                   │ │
│  │ })                                                       │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ 8. WebSocket message
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Next.js Frontend (web-dashboard/)                          │
│                                                              │
│  dashboard.tsx (WebSocket listener):                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ws.onmessage = (event) => {                             │ │
│  │   const message = JSON.parse(event.data)                │ │
│  │   if (message.type === "task_created") {                │ │
│  │     queryClient.invalidateQueries(["kanban", "tasks"])  │ │
│  │   }                                                      │ │
│  │ }                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          │ 9. Refetch tasks                  │
│                          ▼                                   │
│  Tanstack Query refetches /api/kanban/tasks                 │
│  UI updates with new task in "To Do" column                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Proposed Service Container Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Service Container (NEW)                         │
│                    app/core/container.py                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  class ServiceContainer:                                              │
│      def __init__(self, db, config):                                  │
│          self._db = db                                                │
│          self._config = config                                        │
│          self._services = {}  # Lazy-initialized cache                │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Property-based Service Access (Lazy Initialization)             │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │  @property                                                        │ │
│  │  def kanban_tasks(self) -> KanbanTaskService:                    │ │
│  │      if "kanban_tasks" not in self._services:                    │ │
│  │          self._services["kanban_tasks"] = KanbanTaskService(     │ │
│  │              db_session=self._db                                 │ │
│  │          )                                                        │ │
│  │      return self._services["kanban_tasks"]                       │ │
│  │                                                                   │ │
│  │  @property                                                        │ │
│  │  def quality_metrics(self) -> QualityMetricsService:             │ │
│  │      if "quality_metrics" not in self._services:                 │ │
│  │          self._services["quality_metrics"] = QualityMetricsService(│ │
│  │              project_root=self._config.get("project_root")       │ │
│  │          )                                                        │ │
│  │      return self._services["quality_metrics"]                    │ │
│  │                                                                   │ │
│  │  # ... 14 more service properties                                │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  @lru_cache()                                                          │
│  def get_container(db=None) -> ServiceContainer:                      │
│      return ServiceContainer(db=db, config=load_config())             │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                │
                                │ Injected via FastAPI Depends()
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              Routers                                   │
│                      (All 16 routers refactored)                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  kanban_tasks.py:                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  from app.core.container import get_container, ServiceContainer  │ │
│  │                                                                   │ │
│  │  @router.post("/tasks")                                           │ │
│  │  async def create_task(                                           │ │
│  │      task_data: TaskCreate,                                       │ │
│  │      container: ServiceContainer = Depends(get_container) # ✅   │ │
│  │  ):                                                                │ │
│  │      return await container.kanban_tasks.create_task(task_data)   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  quality_metrics.py:                                                   │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  @router.get("/metrics/pylint")                                   │ │
│  │  async def get_pylint_metrics(                                    │ │
│  │      container: ServiceContainer = Depends(get_container) # ✅   │ │
│  │  ):                                                                │ │
│  │      return await container.quality_metrics.get_pylint_metrics()  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Benefits:                                                             │
│  ✅ Testability: Inject mock container in tests                       │
│  ✅ Lifecycle: Control service initialization/disposal                │
│  ✅ Configuration: Environment-specific configs                       │
│  ✅ Decoupling: Routers depend on abstraction, not implementation     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Proposed State Management Architecture (Frontend)

```
┌────────────────────────────────────────────────────────────────────────┐
│                       CURRENT (Overlapping Responsibilities)           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Zustand Store (kanban-store.ts):                                     │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  tasks: KanbanTask[]              ← SERVER DATA (should be Query)│ │
│  │  columns: KanbanColumn[]          ← DERIVED (should be computed) │ │
│  │  selectedTask: KanbanTask | null  ← UI STATE (correct)           │ │
│  │  isLoading: boolean               ← SERVER STATE (should be Query)│ │
│  │  error: string | null             ← SERVER STATE (should be Query)│ │
│  │                                                                   │ │
│  │  Actions:                                                         │ │
│  │  - setTasks() → Manual sync with backend                         │ │
│  │  - moveTask() → Optimistic update + API call                     │ │
│  │  - updateTask() → Manual state management                        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Tanstack Query (useKanbanTasks):                                     │
│  ⚠️  NOT IMPLEMENTED YET (only for time-tracking)                     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                    PROPOSED (Clear Separation)                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Zustand Store (kanban-ui-store.ts) - UI STATE ONLY              │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │  interface KanbanUIState {                                        │ │
│  │    selectedTaskId: string | null                                 │ │
│  │    filters: TaskFilters                                          │ │
│  │    viewMode: 'board' | 'list'                                    │ │
│  │    sidebarOpen: boolean                                          │ │
│  │                                                                   │ │
│  │    setSelectedTask: (id: string | null) => void                  │ │
│  │    setFilters: (filters: TaskFilters) => void                    │ │
│  │    setViewMode: (mode: 'board' | 'list') => void                 │ │
│  │  }                                                                │ │
│  │                                                                   │ │
│  │  ✅ Persisted to localStorage                                     │ │
│  │  ✅ No backend sync                                               │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Tanstack Query (useKanbanTasks.ts) - SERVER STATE ONLY          │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │  export function useKanbanTasks(filters?: TaskFilters) {         │ │
│  │    return useQuery({                                              │ │
│  │      queryKey: ['kanban', 'tasks', filters],                     │ │
│  │      queryFn: () => kanbanAPI.fetchTasks(filters),               │ │
│  │      staleTime: 30000,  // 30s cache                             │ │
│  │    })                                                             │ │
│  │  }                                                                │ │
│  │                                                                   │ │
│  │  export function useUpdateTaskStatus() {                         │ │
│  │    const queryClient = useQueryClient()                          │ │
│  │                                                                   │ │
│  │    return useMutation({                                           │ │
│  │      mutationFn: ({ id, status }) =>                             │ │
│  │        kanbanAPI.updateTaskStatus(id, status),                   │ │
│  │                                                                   │ │
│  │      onMutate: async ({ id, status }) => {                       │ │
│  │        // Cancel outgoing refetches                              │ │
│  │        await queryClient.cancelQueries(['kanban', 'tasks'])      │ │
│  │                                                                   │ │
│  │        // Snapshot previous value                                │ │
│  │        const previous = queryClient.getQueryData(['kanban', 'tasks'])│ │
│  │                                                                   │ │
│  │        // Optimistically update cache                            │ │
│  │        queryClient.setQueryData(['kanban', 'tasks'], (old) =>    │ │
│  │          old.map(task =>                                          │ │
│  │            task.id === id ? { ...task, status } : task           │ │
│  │          )                                                        │ │
│  │        )                                                          │ │
│  │                                                                   │ │
│  │        return { previous }                                        │ │
│  │      },                                                           │ │
│  │                                                                   │ │
│  │      onError: (err, variables, context) => {                     │ │
│  │        // Rollback on error                                      │ │
│  │        queryClient.setQueryData(                                 │ │
│  │          ['kanban', 'tasks'],                                    │ │
│  │          context.previous                                        │ │
│  │        )                                                          │ │
│  │        toast.error('Failed to update task')                      │ │
│  │      },                                                           │ │
│  │                                                                   │ │
│  │      onSuccess: () => {                                           │ │
│  │        // Refetch to sync with server                            │ │
│  │        queryClient.invalidateQueries(['kanban', 'tasks'])        │ │
│  │      },                                                           │ │
│  │    })                                                             │ │
│  │  }                                                                │ │
│  │                                                                   │ │
│  │  ✅ Automatic refetching on stale                                 │ │
│  │  ✅ Built-in optimistic updates with rollback                     │ │
│  │  ✅ Single source of truth (Query cache = server state)           │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Component Usage (KanbanBoard.tsx)                                │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │  function KanbanBoard() {                                         │ │
│  │    // UI state from Zustand                                      │ │
│  │    const { selectedTaskId, filters, setSelectedTask } =          │ │
│  │      useKanbanUIStore()                                           │ │
│  │                                                                   │ │
│  │    // Server state from Tanstack Query                           │ │
│  │    const { data: tasks, isLoading } = useKanbanTasks(filters)    │ │
│  │    const updateStatus = useUpdateTaskStatus()                    │ │
│  │                                                                   │ │
│  │    const handleDrop = (taskId: string, newStatus: TaskStatus) => {│ │
│  │      updateStatus.mutate({ id: taskId, status: newStatus })      │ │
│  │    }                                                              │ │
│  │                                                                   │ │
│  │    return (                                                       │ │
│  │      <div>                                                        │ │
│  │        {tasks?.map(task => (                                      │ │
│  │          <TaskCard                                                │ │
│  │            key={task.id}                                          │ │
│  │            task={task}                                            │ │
│  │            selected={task.id === selectedTaskId}                 │ │
│  │            onSelect={() => setSelectedTask(task.id)}             │ │
│  │          />                                                       │ │
│  │        ))}                                                        │ │
│  │      </div>                                                       │ │
│  │    )                                                              │ │
│  │  }                                                                │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Benefits:                                                             │
│  ✅ Single source of truth (Query cache = server state)               │
│  ✅ No manual state sync (automatic refetching)                       │
│  ✅ Built-in optimistic updates with rollback                         │
│  ✅ Better DevTools (React Query DevTools)                            │
│  ✅ Clearer separation of concerns (UI vs Server)                     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Scalability Roadmap (3 Phases)

```
┌────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: Immediate (Week 2-3)                  │
│                              14 hours implementation                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Backend Refactoring:                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  1. Lazy router registration (2h)                                │ │
│  │     - Create app/routers/__init__.py with register_routers()     │ │
│  │     - Move router imports to lazy loading                        │ │
│  │     - Reduce main.py from 900 → 500 lines                        │ │
│  │                                                                   │ │
│  │  2. Service container with DI (4h)                               │ │
│  │     - Create app/core/container.py                               │ │
│  │     - Implement ServiceContainer class                           │ │
│  │     - Refactor all 16 routers to use Depends(get_container)      │ │
│  │                                                                   │ │
│  │  3. npx security hardening (1h)                                  │ │
│  │     - Implement _find_npx_windows() without shell                │ │
│  │     - Achieve 100% shell=False for all subprocess calls          │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Frontend Refactoring:                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  4. Centralized API client (2h)                                  │ │
│  │     - Enhance lib/api/client.ts with APIClient class             │ │
│  │     - Refactor all API modules to use apiClient                  │ │
│  │                                                                   │ │
│  │  5. Query-first state management (4h)                            │ │
│  │     - Create lib/stores/kanban-ui-store.ts (UI only)             │ │
│  │     - Create lib/hooks/useKanbanTasks.ts (Server state)          │ │
│  │     - Refactor Kanban components to use new hooks                │ │
│  │                                                                   │ │
│  │  6. OpenAPI → TypeScript codegen (1h)                            │ │
│  │     - Setup openapi-typescript-codegen                           │ │
│  │     - Add npm script: "generate:types"                           │ │
│  │     - Update CI to fail if types out of sync                     │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Impact:                                                               │
│  - main.py: 900 → 500 lines (-44%)                                    │
│  - Testability: All services mockable via container                   │
│  - Security: 100% shell=False (injection prevention)                  │
│  - Type safety: Zero manual sync (auto-generated types)               │
│  - State management: Single source of truth (Query cache)             │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2: Near-term (Week 4-6)                     │
│                              5 days implementation                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Database Optimization:                                                │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  1. Connection pool tuning (0.5d)                                │ │
│  │     - Increase asyncpg pool: 10 → 50 connections                 │ │
│  │     - Add pgBouncer for 1000+ concurrent clients                 │ │
│  │                                                                   │ │
│  │  2. Query optimization (1d)                                      │ │
│  │     - Add indexes: task_id, phase_id, status, created_at         │ │
│  │     - Materialized views for dashboard metrics                   │ │
│  │     - EXPLAIN ANALYZE all slow queries (>100ms)                  │ │
│  │                                                                   │ │
│  │  3. Read replica (0.5d)                                          │ │
│  │     - Setup PostgreSQL read replica                              │ │
│  │     - Route analytics queries to replica                         │ │
│  │     - Primary handles writes only                                │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Caching Layer:                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  4. Redis distributed cache (1d)                                 │ │
│  │     - Replace in-memory cache with Redis                         │ │
│  │     - Adaptive TTL: deterministic 5min, chaotic 2s               │ │
│  │     - Cache key namespace: "udo:cache:{type}:{id}"               │ │
│  │                                                                   │ │
│  │  5. Query result caching (0.5d)                                  │ │
│  │     - Cache expensive queries (uncertainty, quality)             │ │
│  │     - Invalidate on write operations                             │ │
│  │     - Track cache hit rate (target: 80%)                         │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Frontend Performance:                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  6. Virtual scrolling (1d)                                       │ │
│  │     - Install react-window                                       │ │
│  │     - Implement FixedSizeList for task columns                   │ │
│  │     - Support 10,000+ tasks without lag                          │ │
│  │                                                                   │ │
│  │  7. Server-side pagination (0.5d)                                │ │
│  │     - Backend: LIMIT/OFFSET queries (50 tasks/page)              │ │
│  │     - Frontend: useInfiniteQuery for infinite scroll             │ │
│  │     - Reduce initial load: 10,000 tasks → 50 tasks               │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Impact:                                                               │
│  - Capacity: 100 → 1,000 concurrent users (10x)                       │
│  - API latency: Unknown → <200ms (p95)                                │
│  - DB query time: Unknown → <50ms (p95)                               │
│  - Cache hit rate: 0% → 80%                                           │
│  - Tasks per board: 50 → 5,000 (100x)                                 │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                     PHASE 3: Long-term (Q1 2026)                       │
│                             15 days implementation                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Horizontal Scaling:                                                   │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  1. Load balancer (2d)                                           │ │
│  │     - Setup nginx/HAProxy                                        │ │
│  │     - Distribute traffic across 3+ backend servers               │ │
│  │     - Health checks + automatic failover                         │ │
│  │                                                                   │ │
│  │  2. Stateless backends (1d)                                      │ │
│  │     - Move session state to Redis                                │ │
│  │     - Enable any server to handle any request                    │ │
│  │     - JWT tokens for authentication (no server-side sessions)    │ │
│  │                                                                   │ │
│  │  3. Message queue (3d)                                           │ │
│  │     - Replace custom WebSocket with RabbitMQ/Kafka               │ │
│  │     - Pub/Sub pattern for real-time events                       │ │
│  │     - Guaranteed delivery + replay capability                    │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Observability:                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  4. Metrics stack (3d)                                           │ │
│  │     - Prometheus: API latency, DB queries, cache hit rates       │ │
│  │     - Grafana: Dashboards for all services                       │ │
│  │     - Alerts: p95 latency >100ms, error rate >1%                 │ │
│  │                                                                   │ │
│  │  5. Logging stack (2d)                                           │ │
│  │     - ELK Stack: Elasticsearch + Logstash + Kibana               │ │
│  │     - Centralized logs from all services                         │ │
│  │     - Full-text search + alerting                                │ │
│  │                                                                   │ │
│  │  6. Distributed tracing (2d)                                     │ │
│  │     - Jaeger/Zipkin for end-to-end request tracing               │ │
│  │     - Identify bottlenecks across microservices                  │ │
│  │     - Trace database queries + MCP server calls                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Microservices Readiness:                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  7. API Gateway (2d)                                             │ │
│  │     - Kong/Tyk for single entry point                            │ │
│  │     - Rate limiting, authentication, request routing             │ │
│  │     - API versioning support                                     │ │
│  │                                                                   │ │
│  │  8. Service mesh (3d)                                            │ │
│  │     - Istio/Linkerd for service discovery                        │ │
│  │     - Circuit breaking, retries, timeouts                        │ │
│  │     - mTLS for inter-service communication                       │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  Impact:                                                               │
│  - Capacity: 1,000 → 100,000 concurrent users (100x)                  │
│  - Uptime: 99% → 99.99% (52min → 5min downtime/year)                  │
│  - API latency: <200ms → <100ms (p95)                                 │
│  - Observability: Minimal → Complete (metrics, logs, traces)          │
│  - Scalability: Vertical → Horizontal (add servers dynamically)       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

**End of Visual Diagrams**

Generated: 2025-12-14
Reviewed: System Architect
