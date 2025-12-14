# Week 2: Core Implementation - 개선된 계획 (상용화 품질)

**Date**: 2025-12-04
**Status**: 🎯 Ready to Start (불확실성 해소 완료)
**Quality Target**: 프로덕션 배포 가능 수준

---

## 개선 배경

### 원래 계획의 문제점

| 문제 | 위험도 | 영향 |
|------|--------|------|
| 인증/권한 전략 없음 | 🔴 HIGH | 보안 취약, 프로덕션 불가 |
| 실시간 동기화 불명확 | 🔴 HIGH | 멀티유저 충돌, UX 저하 |
| 충돌 해결 전략 없음 | 🔴 HIGH | 데이터 손실 가능성 |
| 성능 최적화 불명확 | 🟡 MEDIUM | 1,000 태스크 시 느림 |
| 테스트 전략 없음 | 🟡 MEDIUM | 버그 발견 늦음 |

### 개선된 접근 방식

**2025 AI 코드 리뷰 모범 사례 반영**:
- 구현 전 설계 검토 및 불확실성 해소 ✅
- 보안-퍼스트 접근 (JWT + RBAC) ✅
- 데이터 안전성 우선 (Optimistic locking) ✅
- 성능 메트릭 기반 최적화 (Pagination) ✅
- 자동화된 테스트 (E2E + 통합) ✅

**참고 자료**:
- [AI Code Review Best Practices 2025](https://www.qodo.ai/blog/ai-code-review/)
- [Automated Code Review Tools](https://www.digitalocean.com/resources/articles/ai-code-review-tools)
- [Code Quality Metrics 2025](https://www.qodo.ai/blog/code-quality/)

---

## Week 2 일정 (7일)

### Day 1-2: JWT 인증 + RBAC 권한 시스템

**목표**: 프로덕션 레벨 인증/권한 시스템 구축

#### 구현 사항

**1.1 JWT 토큰 시스템**
```python
# backend/app/core/auth.py
class JWTAuthService:
    - generate_access_token(user_id, roles) → JWT (15분 유효)
    - generate_refresh_token(user_id) → JWT (7일 유효)
    - verify_token(token) → user_id, roles
    - revoke_token(token) → blacklist에 추가
```

**1.2 RBAC (Role-Based Access Control)**

| Role | Permissions | Use Case |
|------|-------------|----------|
| `admin` | Full access (모든 작업) | 시스템 관리자 |
| `project_owner` | 프로젝트 생성/삭제, 팀 관리 | 프로젝트 책임자 |
| `developer` | 태스크 CRUD, 자신의 태스크 수정 | 일반 개발자 |
| `viewer` | 읽기 전용 | 외부 관계자 |

**1.3 API 엔드포인트**
```
POST /api/auth/register       # 회원가입
POST /api/auth/login          # 로그인 (access + refresh 토큰 발급)
POST /api/auth/refresh        # 토큰 갱신
POST /api/auth/logout         # 로그아웃 (토큰 무효화)
GET  /api/auth/me             # 현재 사용자 정보
```

**1.4 미들웨어**
```python
@router.get("/tasks", dependencies=[Depends(require_role("developer"))])
async def get_tasks():
    # Only accessible by developers or higher roles
```

**1.5 테스트**
- 토큰 발급/검증 테스트 (10개)
- RBAC 권한 테스트 (각 role별 5개)
- 토큰 만료/갱신 테스트 (5개)
- **Total**: 20 tests

#### 성공 기준
- ✅ 모든 API가 JWT로 보호됨
- ✅ Role-based 권한 검증 작동
- ✅ 토큰 갱신 플로우 정상 작동
- ✅ 20/20 테스트 통과

---

### Day 3-4: Core API (Tasks CRUD + Dependencies)

**목표**: Kanban 핵심 API 25개 엔드포인트 구현

#### 3.1 Tasks API (12 endpoints)

```
# CRUD
POST   /api/tasks                 # 태스크 생성
GET    /api/tasks                 # 태스크 목록 (필터, 정렬, 페이지네이션)
GET    /api/tasks/{task_id}       # 태스크 상세
PUT    /api/tasks/{task_id}       # 태스크 수정
DELETE /api/tasks/{task_id}       # 태스크 삭제

# Phase 관련
GET    /api/tasks?phase={phase}   # 특정 Phase 태스크
PUT    /api/tasks/{task_id}/phase # Phase 이동

# Status 관련
PUT    /api/tasks/{task_id}/status # Status 변경 (pending/in_progress/completed)

# Priority 관련
PUT    /api/tasks/{task_id}/priority # Priority 변경

# Completeness
PUT    /api/tasks/{task_id}/completeness # 완료율 업데이트 (0-100%)

# Quality Gate (Week 1 구현 활용)
GET    /api/tasks/{task_id}/quality-gates # Quality gate 상태
POST   /api/tasks/{task_id}/quality-gates # Quality gate 실행

# Archive (Q6: Done-End)
POST   /api/tasks/{task_id}/archive # 태스크 아카이브
```

#### 3.2 Dependencies API (8 endpoints)

```
# CRUD
POST   /api/dependencies          # 의존성 생성 (DAG 검증 포함)
GET    /api/dependencies          # 의존성 목록
DELETE /api/dependencies/{dep_id} # 의존성 삭제

# DAG Operations
GET    /api/tasks/{task_id}/dependencies      # 해당 태스크가 의존하는 태스크들
GET    /api/tasks/{task_id}/dependents        # 해당 태스크에 의존하는 태스크들
GET    /api/tasks/{task_id}/dependency-graph  # 전체 의존성 그래프 (D3.js용)

# Emergency Override (Q7)
POST   /api/dependencies/{dep_id}/override    # 긴급 우회
GET    /api/dependencies/audit                # Override 감사 로그
```

#### 3.3 Multi-Project API (5 endpoints)

```
# Q5: 1 Primary + max 3 Related
POST   /api/tasks/{task_id}/projects          # 프로젝트 연결
DELETE /api/tasks/{task_id}/projects/{proj_id} # 프로젝트 연결 해제
PUT    /api/tasks/{task_id}/projects/{proj_id}/primary # Primary 설정
GET    /api/tasks/{task_id}/projects          # 태스크-프로젝트 관계
GET    /api/projects/{proj_id}/tasks          # 프로젝트별 태스크
```

#### 3.4 Pagination 구현

**Query Parameters**:
```
GET /api/tasks?page=1&per_page=50&sort=priority:desc&filter=status:in_progress
```

**Response Format**:
```json
{
  "data": [...],
  "pagination": {
    "total": 1000,
    "page": 1,
    "per_page": 50,
    "total_pages": 20,
    "has_next": true,
    "has_prev": false
  }
}
```

#### 3.5 에러 처리

**표준 에러 응답**:
```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID {task_id} not found",
    "details": {...},
    "timestamp": "2025-12-04T10:30:00Z"
  }
}
```

**에러 코드 정의** (20개):
- `TASK_NOT_FOUND`, `TASK_ALREADY_EXISTS`
- `DEPENDENCY_CYCLE_DETECTED`, `DEPENDENCY_NOT_FOUND`
- `MAX_RELATED_PROJECTS_EXCEEDED`, `NO_PRIMARY_PROJECT`
- `UNAUTHORIZED`, `FORBIDDEN`, `INVALID_TOKEN`
- `VALIDATION_ERROR`, `INTERNAL_SERVER_ERROR`
- ... (나머지 10개)

#### 3.6 테스트
- Tasks API 테스트 (12 endpoints × 5 cases = 60 tests)
- Dependencies API 테스트 (8 endpoints × 5 cases = 40 tests)
- Multi-Project API 테스트 (5 endpoints × 5 cases = 25 tests)
- **Total**: 125 tests

#### 성공 기준
- ✅ 25 API 엔드포인트 모두 작동
- ✅ Pagination 정상 작동 (1,000 태스크)
- ✅ DAG 순환 감지 작동
- ✅ 125/125 테스트 통과
- ✅ p95 응답시간 <500ms

---

### Day 5: WebSocket 실시간 동기화

**목표**: 멀티유저 실시간 협업 지원

#### 5.1 WebSocket 서버

```python
# backend/app/routers/websocket_kanban.py
@router.websocket("/ws/kanban/{project_id}")
async def kanban_websocket(websocket: WebSocket, project_id: UUID):
    # 1. 연결 인증 (JWT via query param)
    # 2. 프로젝트별 채널 구독
    # 3. 실시간 이벤트 브로드캐스트
```

#### 5.2 이벤트 타입

```typescript
// web-dashboard/lib/types/websocket.ts
type KanbanEvent =
  | { type: 'task_created', data: Task }
  | { type: 'task_updated', data: Task }
  | { type: 'task_deleted', data: { task_id: string } }
  | { type: 'task_moved', data: { task_id: string, from: Phase, to: Phase } }
  | { type: 'dependency_added', data: Dependency }
  | { type: 'user_joined', data: { user_id: string, username: string } }
  | { type: 'user_left', data: { user_id: string } }
```

#### 5.3 클라이언트 통합

```typescript
// web-dashboard/lib/hooks/useKanbanWebSocket.ts
export function useKanbanWebSocket(projectId: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState<KanbanEvent | null>(null)

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/kanban/${projectId}?token=${getToken()}`)

    ws.onmessage = (event) => {
      const kanbanEvent: KanbanEvent = JSON.parse(event.data)
      setLastEvent(kanbanEvent)

      // 낙관적 업데이트 롤백 또는 적용
      handleEvent(kanbanEvent)
    }

    return () => ws.close()
  }, [projectId])

  return { isConnected, lastEvent }
}
```

#### 5.4 연결 안정성

- **재연결 로직**: Exponential backoff (1s, 2s, 4s, 8s, 최대 30s)
- **Heartbeat**: 30초마다 ping/pong
- **연결 끊김 감지**: 60초 무응답 시 재연결
- **오프라인 큐**: 연결 끊김 중 발생한 이벤트 저장 → 재연결 시 동기화

#### 5.5 테스트
- 연결/재연결 테스트 (5개)
- 이벤트 브로드캐스트 테스트 (7개)
- 멀티 클라이언트 동기화 테스트 (5개)
- **Total**: 17 tests

#### 성공 기준
- ✅ WebSocket 연결 안정적
- ✅ 이벤트 실시간 브로드캐스트 (<100ms 지연)
- ✅ 재연결 로직 작동
- ✅ 17/17 테스트 통과

---

### Day 6: Optimistic Locking 충돌 해결

**목표**: 데이터 안전성 보장 (2명이 동시 수정 시)

#### 6.1 Optimistic Locking 구현

**데이터베이스 스키마 수정**:
```sql
ALTER TABLE kanban.tasks ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

-- Trigger: 수정 시 version 자동 증가
CREATE OR REPLACE FUNCTION kanban.increment_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_task_version
    BEFORE UPDATE ON kanban.tasks
    FOR EACH ROW
    EXECUTE FUNCTION kanban.increment_version();
```

**API 수정**:
```python
# backend/app/routers/tasks.py
@router.put("/tasks/{task_id}")
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    expected_version: int  # Required header: If-Match
):
    # 1. 현재 버전 조회
    current_task = await db.get_task(task_id)

    # 2. 버전 충돌 감지
    if current_task.version != expected_version:
        raise HTTPException(
            status_code=409,  # Conflict
            detail={
                "code": "VERSION_CONFLICT",
                "message": "Task was modified by another user",
                "current_version": current_task.version,
                "expected_version": expected_version,
                "current_data": current_task.dict()  # 최신 데이터 제공
            }
        )

    # 3. 업데이트 (version 자동 증가)
    updated_task = await db.update_task(task_id, task_update)
    return updated_task
```

#### 6.2 프론트엔드 충돌 해결 UI

```typescript
// web-dashboard/components/ConflictResolutionModal.tsx
export function ConflictResolutionModal({
  localChanges: Task,
  serverChanges: Task,
  onResolve: (resolved: Task) => void
}) {
  return (
    <Modal>
      <h2>충돌 감지</h2>
      <p>다른 사용자가 이 태스크를 수정했습니다.</p>

      <div className="comparison">
        <div>
          <h3>내 변경사항</h3>
          <DiffView data={localChanges} />
        </div>
        <div>
          <h3>서버의 최신 버전</h3>
          <DiffView data={serverChanges} />
        </div>
      </div>

      <div className="actions">
        <Button onClick={() => onResolve(localChanges)}>내 변경사항 유지</Button>
        <Button onClick={() => onResolve(serverChanges)}>서버 버전 수용</Button>
        <Button onClick={() => showMergeEditor()}>수동 병합</Button>
      </div>
    </Modal>
  )
}
```

#### 6.3 낙관적 업데이트 플로우

```typescript
// web-dashboard/lib/hooks/useOptimisticUpdate.ts
export function useOptimisticUpdate() {
  const queryClient = useQueryClient()

  const updateTask = useMutation({
    mutationFn: async ({ taskId, updates, version }) => {
      // 1. 낙관적 업데이트 (즉시 UI 반영)
      queryClient.setQueryData(['task', taskId], (old) => ({
        ...old,
        ...updates,
        version: version + 1
      }))

      // 2. 서버 요청
      return await api.updateTask(taskId, updates, version)
    },

    onError: (error, variables, context) => {
      if (error.code === 'VERSION_CONFLICT') {
        // 3. 충돌 발생 → 롤백 + 충돌 해결 모달 표시
        queryClient.setQueryData(['task', variables.taskId], context.previousData)
        showConflictModal(error.detail.current_data, variables.updates)
      } else {
        // 4. 기타 에러 → 롤백 + 에러 메시지
        queryClient.setQueryData(['task', variables.taskId], context.previousData)
        showErrorToast(error.message)
      }
    },

    onSuccess: () => {
      // 5. 성공 → WebSocket 이벤트로 다른 클라이언트 동기화
      // (WebSocket 서버가 자동 브로드캐스트)
    }
  })

  return { updateTask }
}
```

#### 6.4 테스트
- Optimistic locking 테스트 (10개)
- 충돌 해결 시나리오 테스트 (10개)
- 낙관적 업데이트 롤백 테스트 (5개)
- **Total**: 25 tests

#### 성공 기준
- ✅ 버전 충돌 감지 작동
- ✅ 충돌 해결 UI 정상 작동
- ✅ 낙관적 업데이트 + 롤백 작동
- ✅ 25/25 테스트 통과
- ✅ 데이터 손실 0건

---

### Day 7: UI 컴포넌트 + 드래그-앤-드롭

**목표**: Kanban 보드 UI 완성

#### 7.1 KanbanBoard 컴포넌트

```typescript
// web-dashboard/components/kanban/KanbanBoard.tsx
export function KanbanBoard({ projectId }: { projectId: string }) {
  const { data: tasks, isLoading } = useTasksQuery(projectId)
  const { updateTask } = useOptimisticUpdate()
  const { isConnected, lastEvent } = useKanbanWebSocket(projectId)

  const [currentPage, setCurrentPage] = useState(1)
  const tasksPerPage = 50  // Pagination

  return (
    <div className="kanban-board">
      <ConnectionStatus connected={isConnected} />

      <div className="phases">
        {PHASES.map(phase => (
          <PhaseColumn
            key={phase}
            phase={phase}
            tasks={getTasksByPhase(tasks, phase, currentPage, tasksPerPage)}
            onTaskMove={handleTaskMove}
          />
        ))}
      </div>

      <Pagination
        total={tasks.length}
        perPage={tasksPerPage}
        current={currentPage}
        onChange={setCurrentPage}
      />
    </div>
  )
}
```

#### 7.2 드래그-앤-드롭 (react-beautiful-dnd)

```typescript
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'

function PhaseColumn({ phase, tasks, onTaskMove }) {
  return (
    <Droppable droppableId={phase}>
      {(provided) => (
        <div ref={provided.innerRef} {...provided.droppableProps}>
          {tasks.map((task, index) => (
            <Draggable key={task.id} draggableId={task.id} index={index}>
              {(provided) => (
                <TaskCard
                  ref={provided.innerRef}
                  task={task}
                  {...provided.draggableProps}
                  {...provided.dragHandleProps}
                />
              )}
            </Draggable>
          ))}
          {provided.placeholder}
        </div>
      )}
    </Droppable>
  )
}

function handleTaskMove(result) {
  const { draggableId, source, destination } = result

  if (!destination) return
  if (source.droppableId === destination.droppableId) return  // 같은 Phase

  // 낙관적 업데이트 + Optimistic locking
  updateTask({
    taskId: draggableId,
    updates: { phase_name: destination.droppableId },
    version: tasks.find(t => t.id === draggableId).version
  })
}
```

#### 7.3 TaskCard 컴포넌트

```typescript
// web-dashboard/components/kanban/TaskCard.tsx
export function TaskCard({ task }: { task: Task }) {
  return (
    <div className="task-card">
      <div className="header">
        <span className="title">{task.title}</span>
        <Badge priority={task.priority} />
      </div>

      <div className="body">
        <p className="description">{task.description}</p>
        <ProgressBar value={task.completeness} />
      </div>

      <div className="footer">
        <QualityGateIndicator passed={task.quality_gate_passed} />
        <ProjectTags projects={task.projects} />
        <DependencyCount count={task.dependency_count} />
      </div>
    </div>
  )
}
```

#### 7.4 Pagination 컴포넌트

```typescript
// web-dashboard/components/Pagination.tsx
export function Pagination({ total, perPage, current, onChange }) {
  const totalPages = Math.ceil(total / perPage)

  return (
    <div className="pagination">
      <Button disabled={current === 1} onClick={() => onChange(current - 1)}>
        이전
      </Button>

      <span>{current} / {totalPages} 페이지</span>

      <Button disabled={current === totalPages} onClick={() => onChange(current + 1)}>
        다음
      </Button>

      <select value={perPage} onChange={(e) => onPerPageChange(e.target.value)}>
        <option value="25">25개씩</option>
        <option value="50">50개씩</option>
        <option value="100">100개씩</option>
      </select>
    </div>
  )
}
```

#### 7.5 테스트
- KanbanBoard 렌더링 테스트 (5개)
- 드래그-앤-드롭 테스트 (10개)
- TaskCard 테스트 (5개)
- Pagination 테스트 (5개)
- **Total**: 25 tests

#### 성공 기준
- ✅ Kanban 보드 정상 렌더링
- ✅ 드래그-앤-드롭 작동
- ✅ Pagination 작동 (1,000 태스크)
- ✅ 25/25 테스트 통과
- ✅ TTI <3s, FCP <1s

---

## 통합 테스트 (E2E)

### Playwright E2E 시나리오 (10개)

1. **사용자 인증 플로우**
   - 회원가입 → 로그인 → 토큰 검증

2. **태스크 생성 플로우**
   - 태스크 생성 → Phase 이동 → 상태 변경

3. **의존성 추가 플로우**
   - 2개 태스크 생성 → 의존성 추가 → DAG 그래프 확인

4. **멀티유저 실시간 동기화**
   - 2개 브라우저 창 열기 → 한 쪽에서 태스크 수정 → 다른 쪽 즉시 반영 확인

5. **충돌 해결 플로우**
   - 2개 브라우저 창 → 동시에 같은 태스크 수정 → 충돌 모달 표시 → 해결

6. **드래그-앤-드롭 플로우**
   - 태스크 드래그 → Phase 이동 → 서버 반영 확인

7. **Pagination 플로우**
   - 100개 태스크 생성 → 페이지 이동 → 성능 확인

8. **Quality Gate 플로우**
   - 태스크 생성 → Quality gate 실행 → 결과 확인

9. **Multi-Project 플로우**
   - 태스크에 프로젝트 추가 → Primary 설정 → 제약조건 확인

10. **Archive 플로우**
    - 태스크 완료 → Done-End 아카이브 → AI 요약 생성 확인

---

## 성공 기준 (Week 2)

### 기능 완성도
- ✅ 25 API 엔드포인트 구현
- ✅ JWT + RBAC 인증 시스템
- ✅ WebSocket 실시간 동기화
- ✅ Optimistic locking 충돌 해결
- ✅ Kanban 보드 UI + 드래그-앤-드롭
- ✅ Pagination (1,000 태스크 처리)

### 테스트 커버리지
- **백엔드**: 207 테스트 (인증 20 + API 125 + WebSocket 17 + Locking 25 + 기타 20)
- **프론트엔드**: 25 테스트 (UI 컴포넌트)
- **E2E**: 10 테스트 (Playwright)
- **Total**: 242 테스트 목표

### 성능 목표
- API 응답시간 p95 <500ms
- WebSocket 지연 <100ms
- UI 렌더링 TTI <3s
- 1,000 태스크 페이지네이션 <1s

### 품질 목표
- 테스트 통과율 95% 이상
- 데이터 손실 0건
- 충돌 해결 성공률 100%
- 보안 취약점 0건

---

## 롤백 전략

### Tier 1: Feature Flag (즉시)
```python
# backend/config/feature_flags.yaml
features:
  kanban_api: enabled
  websocket_sync: enabled
  optimistic_locking: enabled
```

### Tier 2: API 버전 롤백 (1분)
```
/api/v1/tasks  # Old version
/api/v2/tasks  # New version (Week 2)
```

### Tier 3: Git Revert (5분)
```bash
git revert <commit-hash-week2>
```

---

## 마일스톤

| Day | Milestone | 완성도 |
|-----|-----------|--------|
| 1-2 | JWT + RBAC | 100% |
| 3-4 | Core API | 100% |
| 5 | WebSocket | 100% |
| 6 | Optimistic Locking | 100% |
| 7 | UI + 드래그-드롭 | 100% |

**Week 2 완료 시**: 상용화 가능한 Kanban 시스템 완성 ✅

---

**Document Version**: 2.0 (개선)
**Last Updated**: 2025-12-04
**Author**: Claude Code + User Feedback
**Review Status**: 불확실성 해소 완료 ✅
