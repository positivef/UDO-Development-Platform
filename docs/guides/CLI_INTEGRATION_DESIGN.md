# CLI 통합 기능 설계

> **기능**: 웹 대시보드에서 작업 카드 클릭 → CLI로 개발 이어서 진행
> **작성일**: 2025-11-17
> **우선순위**: 모든 Phase에 적용 가능한 Universal 기능

---

## 🎯 기능 개요

### 사용자 시나리오

```
1. 웹 대시보드에서 Kanban 카드 확인
2. 카드를 더블클릭 또는 "Continue in CLI" 버튼 클릭
3. 터미널이 자동으로 열림
4. Claude Code CLI가 해당 작업의 컨텍스트를 자동 로드
5. "이 작업을 이어서 진행할까요?" 프롬프트 표시
6. 개발자가 즉시 작업 시작
```

### 핵심 가치

- ⭐⭐⭐⭐⭐ **원클릭 작업 재개**: 컨텍스트 스위칭 시간 제로
- ⭐⭐⭐⭐⭐ **컨텍스트 자동 로드**: 파일, 히스토리, 상태 자동 복원
- ⭐⭐⭐⭐ **CLI 파워 유저 지원**: GUI + CLI 최고의 조합

---

## 🏗️ 기술 아키텍처

### 시스템 구조

```
Web Dashboard (React)
    ↓ (1) User clicks "Continue in CLI"
    ↓
Backend API (FastAPI)
    ↓ (2) Generate CLI command with context
    ↓
    ├─→ (3a) Deep Link: claude-code://continue?task=123
    │         (브라우저가 Claude Code CLI 실행)
    │
    └─→ (3b) WebSocket: Send command to open terminal
              (VS Code Terminal API 사용)

Claude Code CLI
    ↓ (4) Load context from task ID
    ↓
UDO System
    ↓ (5) Resume task with full context
```

---

## 🔧 구현 방안

### 방안 1: Deep Link Protocol (권장) ⭐⭐⭐⭐⭐

**개념**: 웹에서 `claude-code://` 프로토콜로 CLI 실행

**장점**:
- ✅ 가장 직관적인 UX
- ✅ 브라우저 기본 기능 활용
- ✅ 추가 서버 불필요

**구현**:

```typescript
// Frontend: 버튼 클릭 핸들러
async function handleContinueInCLI(card: KanbanCard) {
  // 1. 작업 컨텍스트 준비
  const context = await prepareTaskContext(card)

  // 2. Deep link 생성
  const deepLink = generateDeepLink(card.id, context)

  // 3. Deep link 실행
  window.location.href = deepLink
  // 예: claude-code://continue?task=123&project=udo&phase=implementation
}

function generateDeepLink(taskId: string, context: TaskContext): string {
  const params = new URLSearchParams({
    task: taskId,
    project: context.project,
    phase: context.phase,
    files: context.files.join(','),
    description: context.description
  })

  return `claude-code://continue?${params.toString()}`
}
```

```python
# Backend: Deep link 등록 (설치 시 한 번만)
# Windows
def register_deep_link_windows():
    """Windows 레지스트리에 claude-code:// 프로토콜 등록"""

    import winreg

    protocol_key = r"Software\Classes\claude-code"

    # 프로토콜 등록
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, protocol_key) as key:
        winreg.SetValue(key, "", winreg.REG_SZ, "URL:Claude Code Protocol")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

    # 실행 명령 등록
    command_key = f"{protocol_key}\\shell\\open\\command"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key) as key:
        cli_path = get_claude_code_cli_path()
        winreg.SetValue(key, "", winreg.REG_SZ, f'"{cli_path}" --continue "%1"')

# macOS/Linux
def register_deep_link_unix():
    """Unix 시스템에 claude-code:// 프로토콜 등록"""

    # macOS: .app 번들 생성
    # Linux: .desktop 파일 생성
    pass
```

```python
# CLI: Deep link 핸들러
# claude_code/cli/main.py

import sys
from urllib.parse import urlparse, parse_qs

def handle_deep_link(url: str):
    """Deep link에서 컨텍스트 추출 및 작업 재개"""

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    task_id = params.get('task', [None])[0]
    project = params.get('project', [None])[0]
    phase = params.get('phase', [None])[0]

    if not task_id:
        print("Error: No task ID provided")
        return

    # 1. 백엔드에서 전체 컨텍스트 로드
    context = fetch_task_context(task_id)

    # 2. UDO 시스템 초기화
    udo = initialize_udo_with_context(context)

    # 3. 작업 재개 프롬프트
    print(f"\n{'='*60}")
    print(f"📋 Task: {context['title']}")
    print(f"📂 Project: {project}")
    print(f"🎯 Phase: {phase}")
    print(f"📝 Description:\n{context['description']}")
    print(f"{'='*60}\n")

    user_input = input("Continue this task? (Y/n): ")

    if user_input.lower() != 'n':
        # 4. 작업 이어서 진행
        resume_task(context, udo)

def fetch_task_context(task_id: str) -> dict:
    """백엔드 API에서 작업 컨텍스트 가져오기"""

    import requests

    response = requests.get(f"http://localhost:8000/api/tasks/{task_id}/context")

    return response.json()

def resume_task(context: dict, udo):
    """작업 재개"""

    # 1. 프로젝트 디렉토리로 이동
    os.chdir(context['project_path'])

    # 2. Git 브랜치 체크아웃 (필요 시)
    if context.get('git_branch'):
        subprocess.run(['git', 'checkout', context['git_branch']])

    # 3. 관련 파일 열기 (VS Code 통합)
    if context.get('files'):
        open_files_in_editor(context['files'])

    # 4. UDO 실행
    print("\n🤖 Starting UDO development cycle...\n")

    result = udo.execute_development_cycle(
        task=context['description'],
        phase=context['phase']
    )

    # 5. 결과 백엔드에 전송
    update_task_progress(context['task_id'], result)

    print(f"\n✅ Task completed with decision: {result.decision}")
    print(f"Confidence: {result.confidence:.2%}")

if __name__ == "__main__":
    # Deep link로 실행된 경우
    if len(sys.argv) > 1 and sys.argv[1].startswith('claude-code://'):
        handle_deep_link(sys.argv[1])
    # 일반 CLI로 실행된 경우
    else:
        normal_cli_mode()
```

---

### 방안 2: Copy Command (간단한 대안) ⭐⭐⭐⭐

**개념**: 카드 클릭 시 CLI 명령어를 클립보드에 복사

**장점**:
- ✅ 구현 매우 간단
- ✅ 플랫폼 독립적
- ✅ 추가 설정 불필요

**구현**:

```typescript
// Frontend: 클립보드 복사
async function handleCopyCommand(card: KanbanCard) {
  // CLI 명령어 생성
  const command = generateCLICommand(card)

  // 클립보드에 복사
  await navigator.clipboard.writeText(command)

  // 토스트 알림
  toast.success(`Command copied! Paste in terminal:\n${command}`)
}

function generateCLICommand(card: KanbanCard): string {
  return `claude-code continue --task ${card.id} --project ${card.project} --phase ${card.phase}`
}
```

**UX**:
```
1. 카드 클릭 → "Command copied to clipboard!"
2. 터미널 열기
3. Ctrl+V (붙여넣기)
4. Enter
```

---

### 방안 3: VS Code Extension Integration ⭐⭐⭐⭐⭐ (고급)

**개념**: VS Code Extension을 통해 터미널 자동 열기

**장점**:
- ✅ 가장 강력한 통합
- ✅ 터미널 자동 실행
- ✅ VS Code 컨텍스트 활용

**구현**:

```typescript
// VS Code Extension
import * as vscode from 'vscode'

export function activate(context: vscode.ExtensionContext) {
  // 명령어 등록
  let disposable = vscode.commands.registerCommand(
    'udo.continueTask',
    async (taskId: string) => {
      // 1. 터미널 생성
      const terminal = vscode.window.createTerminal({
        name: `UDO Task ${taskId}`,
        cwd: vscode.workspace.rootPath
      })

      // 2. 터미널 표시
      terminal.show()

      // 3. CLI 명령어 실행
      terminal.sendText(`claude-code continue --task ${taskId}`)
    }
  )

  context.subscriptions.push(disposable)
}
```

```typescript
// Frontend: VS Code Extension 호출
async function handleContinueInVSCode(card: KanbanCard) {
  // vscode:// 프로토콜 사용
  const vscodeUri = `vscode://udo-extension/continue?task=${card.id}`

  window.location.href = vscodeUri
}
```

---

## 📦 작업 컨텍스트 구조

### TaskContext 데이터 모델

```typescript
interface TaskContext {
  // 기본 정보
  task_id: string
  title: string
  description: string

  // 프로젝트 정보
  project: string
  project_path: string

  // 개발 상태
  phase: string
  status: "todo" | "in_progress" | "review" | "testing" | "done"

  // Git 정보
  git_branch?: string
  git_commit?: string

  // 파일 정보
  files: string[]  // 관련 파일 경로
  current_file?: string  // 현재 작업 중인 파일

  // 히스토리
  previous_prompts?: string[]  // 이전 프롬프트
  code_changes?: {
    files_modified: string[]
    last_commit: string
  }

  // UDO 상태
  udo_state?: {
    last_decision: "GO" | "NO_GO" | "GO_WITH_CHECKPOINTS"
    confidence: number
    quantum_state: string
  }

  // 메타데이터
  created_at: string
  updated_at: string
  assignee?: string
  priority: "high" | "medium" | "low"

  // 체크포인트 (중단/재개)
  checkpoint?: {
    step: string  // 어디까지 진행했는지
    next_action: string  // 다음에 할 일
    blockers?: string[]  // 막힌 부분
  }
}
```

### API 엔드포인트

```python
# Backend API
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/tasks")

@router.get("/{task_id}/context")
async def get_task_context(task_id: str) -> TaskContext:
    """작업 컨텍스트 조회 (CLI에서 호출)"""

    task = await db.get_task(task_id)

    if not task:
        raise HTTPException(404, "Task not found")

    # 1. 기본 컨텍스트
    context = TaskContext(
        task_id=task.id,
        title=task.title,
        description=task.description,
        project=task.project,
        project_path=get_project_path(task.project),
        phase=task.phase,
        status=task.status
    )

    # 2. Git 정보 추가
    if task.git_branch:
        context.git_branch = task.git_branch
        context.git_commit = get_latest_commit(task.git_branch)

    # 3. 관련 파일 추출
    context.files = await extract_related_files(task)

    # 4. 히스토리 추가
    context.previous_prompts = await get_task_history(task.id)

    # 5. 체크포인트 복원
    context.checkpoint = task.checkpoint

    return context

@router.post("/{task_id}/progress")
async def update_task_progress(
    task_id: str,
    progress: dict
) -> dict:
    """작업 진행 상황 업데이트 (CLI에서 호출)"""

    await db.update_task(task_id, {
        "status": progress.get("status"),
        "checkpoint": progress.get("checkpoint"),
        "udo_state": progress.get("udo_result")
    })

    # WebSocket으로 대시보드에 실시간 업데이트
    await broadcast_task_update(task_id, progress)

    return {"status": "success"}
```

---

## 🎨 UI/UX 디자인

### Kanban 카드 컴포넌트

```tsx
interface KanbanCardProps {
  card: KanbanCard
  onUpdate: (card: KanbanCard) => void
}

export function KanbanCard({ card, onUpdate }: KanbanCardProps) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <motion.div
      className="kanban-card"
      onDoubleClick={() => handleContinueInCLI(card)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 카드 헤더 */}
      <div className="card-header">
        <h3>{card.title}</h3>
        <PriorityBadge priority={card.priority} />
      </div>

      {/* 카드 본문 */}
      <div className="card-body">
        <p>{card.description}</p>

        {/* UDO 상태 표시 */}
        {card.udo_task && (
          <UDOStatusBadge
            decision={card.udo_task.decision}
            confidence={card.udo_task.confidence}
          />
        )}
      </div>

      {/* 카드 하단 (호버 시 표시) */}
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="card-actions"
          >
            {/* Continue in CLI 버튼 */}
            <Button
              variant="primary"
              onClick={() => handleContinueInCLI(card)}
              icon={<Terminal />}
            >
              Continue in CLI
            </Button>

            {/* Copy Command 버튼 */}
            <Button
              variant="ghost"
              onClick={() => handleCopyCommand(card)}
              icon={<Copy />}
            >
              Copy Command
            </Button>

            {/* Edit 버튼 */}
            <Button
              variant="ghost"
              onClick={() => handleEdit(card)}
              icon={<Edit />}
            >
              Edit
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// CLI 실행 핸들러
async function handleContinueInCLI(card: KanbanCard) {
  try {
    // 방안 1: Deep Link
    if (isDeepLinkSupported()) {
      const deepLink = generateDeepLink(card.id, card)
      window.location.href = deepLink
    }
    // 방안 2: VS Code Extension
    else if (isVSCodeExtensionInstalled()) {
      const vscodeUri = `vscode://udo-extension/continue?task=${card.id}`
      window.location.href = vscodeUri
    }
    // 방안 3: Copy Command (fallback)
    else {
      await handleCopyCommand(card)
    }
  } catch (error) {
    console.error("Failed to continue in CLI:", error)
    toast.error("Failed to open CLI. Command copied to clipboard.")
    await handleCopyCommand(card)
  }
}
```

---

## 🔄 실시간 동기화

### CLI ↔ Web 양방향 동기화

```python
# CLI에서 WebSocket으로 상태 업데이트
class CLIProgressReporter:
    """CLI 진행 상황을 웹 대시보드에 실시간 전송"""

    def __init__(self, task_id: str, websocket_url: str):
        self.task_id = task_id
        self.ws = websocket.create_connection(websocket_url)

    def report_progress(self, status: str, message: str):
        """진행 상황 보고"""

        self.ws.send(json.dumps({
            "type": "task_progress",
            "task_id": self.task_id,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }))

    def report_step(self, step: str, result: dict):
        """단계 완료 보고"""

        self.ws.send(json.dumps({
            "type": "task_step_completed",
            "task_id": self.task_id,
            "step": step,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }))

    def report_completion(self, result: dict):
        """작업 완료 보고"""

        self.ws.send(json.dumps({
            "type": "task_completed",
            "task_id": self.task_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }))

        self.ws.close()

# 사용 예시
async def resume_task_with_reporting(context: dict, udo):
    """작업 재개 (실시간 보고 포함)"""

    reporter = CLIProgressReporter(
        task_id=context['task_id'],
        websocket_url="ws://localhost:8000/ws"
    )

    try:
        # 1. 시작 보고
        reporter.report_progress("started", "Task resumed from CLI")

        # 2. UDO 실행
        reporter.report_progress("running", "Executing UDO development cycle...")

        result = udo.execute_development_cycle(
            task=context['description'],
            phase=context['phase']
        )

        # 3. 단계별 보고
        reporter.report_step("analysis", {
            "decision": result.decision,
            "confidence": result.confidence
        })

        # 4. 완료 보고
        reporter.report_completion({
            "decision": result.decision,
            "confidence": result.confidence,
            "quantum_state": result.quantum_state
        })

    except Exception as e:
        reporter.report_progress("failed", str(e))
        raise
```

```tsx
// Frontend: WebSocket으로 실시간 업데이트 수신
export function KanbanBoard({ project }: { project: string }) {
  const [cards, setCards] = useState<KanbanCard[]>([])

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)

      if (message.type === 'task_progress') {
        // 카드 상태 업데이트
        updateCardStatus(message.task_id, message.status, message.message)

        // 토스트 알림
        toast.info(`Task ${message.task_id}: ${message.message}`)
      }

      if (message.type === 'task_completed') {
        // 카드를 "Done" 컬럼으로 이동
        moveCardToColumn(message.task_id, 'done')

        // 성공 알림
        toast.success(`Task ${message.task_id} completed!`)
      }
    }

    return () => ws.close()
  }, [])

  return <div>...</div>
}
```

---

## ✅ 구현 체크리스트

### Phase 1: 기본 CLI 통합 (Week 1)

- [ ] Deep link 프로토콜 등록 (Windows/macOS/Linux)
- [ ] CLI `--continue` 플래그 구현
- [ ] 백엔드 `/api/tasks/{id}/context` 엔드포인트
- [ ] TaskContext 데이터 모델
- [ ] 기본 UX (버튼 1개)

### Phase 2: 고급 기능 (Week 2)

- [ ] Copy Command 기능
- [ ] VS Code Extension (선택적)
- [ ] CLI ↔ Web 실시간 동기화
- [ ] 진행 상황 보고
- [ ] 체크포인트 저장/복원

### Phase 3: UX 개선 (Week 3)

- [ ] 더블클릭 지원
- [ ] 호버 UI
- [ ] 키보드 단축키
- [ ] 토스트 알림
- [ ] 에러 핸들링

---

## 🎯 사용자 경험 플로우

### 최종 워크플로우

```
1. 웹 대시보드에서 작업 확인
   ↓
2. 카드 더블클릭 또는 "Continue in CLI" 버튼
   ↓
3. [자동] 터미널 열림 + 프로젝트 디렉토리로 이동
   ↓
4. [자동] Git 브랜치 체크아웃 (필요 시)
   ↓
5. [자동] 관련 파일 VS Code에서 열기
   ↓
6. [자동] UDO 컨텍스트 로드
   ↓
7. "Continue this task? (Y/n):" 프롬프트
   ↓
8. 개발자가 Enter 또는 추가 지시
   ↓
9. [자동] UDO 실행 + 실시간 진행 상황 웹에 표시
   ↓
10. [자동] 완료 시 카드 상태 업데이트 + 알림
```

**결과**: 클릭 1번으로 모든 컨텍스트가 자동 로드되어 즉시 개발 시작!

---

## 📄 다음 단계

1. ✅ 이 설계 검토 및 승인
2. Phase 1 구현 시작
3. 프로토타입 테스트
4. Phase 2-3 점진적 확장
