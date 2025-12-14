# 작업 계획 확인 워크플로우

> **목적**: 개발 시작 전 계획 불일치 방지
> **접근**: 하이브리드 (웹 + CLI 모두 지원)

---

## 🎯 문제 정의

### 시나리오

```
개발자가 Kanban 카드를 클릭하여 CLI 시작
    ↓
그런데... 카드의 계획이 오래되었거나 불완전함
    ↓
바로 개발 시작하면 → 방향 틀림 → 시간 낭비
    ↓
❌ 문제: 계획 검증 없이 바로 개발 시작
```

### 필요한 것

✅ **개발 시작 전 계획 검증 단계**
✅ **잔존 TODO 리스트 확인**
✅ **개발자의 의도와 일치 여부 확인**

---

## 💡 하이브리드 솔루션

### 옵션 A: 웹 대시보드에서 먼저 확인 (선택적)

**장점**:
- ⭐⭐⭐⭐⭐ 시각적으로 전체 계획 조망
- ⭐⭐⭐⭐⭐ TODO 체크리스트 한눈에 파악
- ⭐⭐⭐⭐ 복잡한 계획도 쉽게 이해

**UX**:
```tsx
// Kanban 카드 확장 뷰
<KanbanCard>
  {/* 기본 정보 */}
  <CardHeader title="Implement auth system" />

  {/* TODO 체크리스트 (클릭 시 확장) */}
  <TodoChecklist>
    <TodoGroup title="1. Planning" status="completed">
      <TodoItem checked>✅ Review requirements</TodoItem>
      <TodoItem checked>✅ Design database schema</TodoItem>
      <TodoItem checked>✅ API endpoint design</TodoItem>
    </TodoGroup>

    <TodoGroup title="2. Implementation" status="in_progress">
      <TodoItem checked>✅ User model</TodoItem>
      <TodoItem>⏳ JWT middleware (← 현재 작업)</TodoItem>
      <TodoItem>📋 Login endpoint</TodoItem>
      <TodoItem>📋 Register endpoint</TodoItem>
    </TodoGroup>

    <TodoGroup title="3. Testing" status="pending">
      <TodoItem>📋 Unit tests</TodoItem>
      <TodoItem>📋 Integration tests</TodoItem>
    </TodoGroup>
  </TodoChecklist>

  {/* Continue in CLI 버튼 */}
  <Button onClick={handleContinueInCLI}>
    Continue "JWT middleware" in CLI
  </Button>
</KanbanCard>
```

**워크플로우**:
```
1. 웹에서 카드 클릭 → 상세 뷰
2. TODO 체크리스트 확인
3. 현재 작업 확인 (⏳ 표시된 항목)
4. "Continue in CLI" 버튼 클릭
5. CLI 자동 실행
```

---

### 옵션 B: CLI에서 계획 확인 + 선택 (필수)

**장점**:
- ⭐⭐⭐⭐⭐ CLI 한 곳에서 모든 작업
- ⭐⭐⭐⭐⭐ 개발 플로우 끊김 없음
- ⭐⭐⭐⭐ 빠른 확인 + 수정 가능

**CLI UX**:
```bash
$ claude-code://continue?task=123

════════════════════════════════════════════════════════════
📋 Task: Implement auth system
📂 Project: MyApp
🎯 Phase: Implementation
📍 Current Step: 2/3 - JWT middleware
════════════════════════════════════════════════════════════

📝 Task Plan:

  ✅ 1. Planning (3/3 completed)
      ✅ Review requirements
      ✅ Design database schema
      ✅ API endpoint design

  ⏳ 2. Implementation (1/4 in progress)
      ✅ User model
      ⏳ JWT middleware           ← YOU ARE HERE
      📋 Login endpoint
      📋 Register endpoint

  📋 3. Testing (0/2 pending)
      📋 Unit tests
      📋 Integration tests

════════════════════════════════════════════════════════════

🤔 What would you like to do?

  1) Continue "JWT middleware" (recommended)
  2) View detailed plan for "JWT middleware"
  3) Skip to next task: "Login endpoint"
  4) Go back to previous task: "User model"
  5) Edit task plan
  6) Cancel

Your choice (1-6): _
```

**선택 시 동작**:

```bash
# 1번 선택 시
Your choice: 1

✅ Loading context for "JWT middleware"...

📂 Related files:
  - src/middleware/auth.ts
  - src/models/User.ts
  - tests/middleware/auth.test.ts

📋 Subtasks for "JWT middleware":
  [ ] Install jsonwebtoken package
  [ ] Create JWT config
  [ ] Implement token generation
  [ ] Implement token verification
  [ ] Add to Express middleware chain

🎯 Starting UDO development cycle...

════════════════════════════════════════════════════════════
```

```bash
# 2번 선택 시 (상세 계획 보기)
Your choice: 2

════════════════════════════════════════════════════════════
📋 Detailed Plan: JWT middleware
════════════════════════════════════════════════════════════

🎯 Goal:
  Implement JWT-based authentication middleware for Express

📝 Description:
  Create middleware to verify JWT tokens in incoming requests.
  Should extract token from Authorization header, verify signature,
  and attach user info to request object.

✅ Acceptance Criteria:
  [ ] Validates JWT token format
  [ ] Verifies token signature with secret
  [ ] Handles expired tokens gracefully
  [ ] Attaches user object to req.user
  [ ] Returns 401 for invalid/missing tokens
  [ ] Has 90%+ test coverage

🔧 Technical Details:
  - Package: jsonwebtoken ^9.0.0
  - Secret: From environment variable JWT_SECRET
  - Token expiry: 24 hours
  - Algorithms: HS256

📂 Files to modify:
  - src/middleware/auth.ts (create)
  - src/types/express.d.ts (extend Request type)
  - package.json (add dependency)

🧪 Test strategy:
  - Unit tests: token validation logic
  - Integration tests: with Express routes
  - E2E tests: full auth flow

⏱️ Estimated time: 2-3 hours

════════════════════════════════════════════════════════════

Press Enter to start, or (c)ancel: _
```

---

### 옵션 C: 스마트 검증 (자동 + 수동)

**개념**: AI가 계획 완성도를 자동 검증 → 불완전하면 경고

```bash
$ claude-code://continue?task=123

🔍 Analyzing task plan...

⚠️  Task Plan Validation Report:

  ✅ Task description: Clear and detailed
  ✅ Acceptance criteria: Well-defined (5 items)
  ⚠️  Subtasks: Missing! (recommended: break into 5-10 subtasks)
  ⚠️  Dependencies: "User model" not fully completed
  ✅ Estimated time: Reasonable (2-3 hours)
  ❌ Test plan: Incomplete (no specific test cases)

Overall completeness: 65% ⚠️

════════════════════════════════════════════════════════════

💡 Recommendations:

  1. Add subtasks to break down implementation
  2. Complete "User model" first (has failing tests)
  3. Define specific test cases for JWT middleware

════════════════════════════════════════════════════════════

Would you like to:

  a) Continue anyway (I know what I'm doing)
  b) Improve plan first (recommended)
  c) Show detailed issues
  d) Cancel

Your choice (a-d): _
```

**선택 b) 시 - AI가 계획 보완**:

```bash
Your choice: b

🤖 Improving task plan...

✨ Generated subtasks for "JWT middleware":

  1. Install jsonwebtoken package
  2. Create JWT configuration module
  3. Implement generateToken() function
  4. Implement verifyToken() middleware
  5. Add error handling for expired/invalid tokens
  6. Extend Express Request type
  7. Write unit tests (5 test cases)
  8. Write integration tests (3 scenarios)
  9. Update API documentation

✨ Generated test cases:

  Unit Tests:
  - should generate valid JWT token with user payload
  - should verify valid token and return decoded data
  - should reject expired token with 401
  - should reject invalid signature with 401
  - should reject malformed token with 400

  Integration Tests:
  - should allow access to protected route with valid token
  - should deny access without token
  - should deny access with expired token

════════════════════════════════════════════════════════════

💾 Save improved plan? (Y/n): _
```

---

## 🎯 최종 권장 워크플로우

### Hybrid Approach (모든 옵션 제공)

```
개발자가 Kanban 카드 클릭
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
옵션 1: 웹에서 먼저 확인 (선택적)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
카드 확장 → TODO 체크리스트 확인
    ↓
현재 작업 확인 (⏳ 표시)
    ↓
"Continue in CLI" 버튼 클릭
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
옵션 2: CLI에서 계획 확인 (필수)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
CLI 자동 실행 + 계획 요약 표시
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
옵션 3: 스마트 검증 (자동)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
AI가 계획 완성도 자동 검증
    ↓
불완전하면 → 경고 + 개선 제안
완전하면 → 바로 진행
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
개발자 선택
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
1) 계획대로 진행
2) 계획 상세히 보기
3) 계획 수정
4) 다른 작업으로 전환
5) 취소
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
개발 시작
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 구현 우선순위

**Phase 1** (필수):
1. ✅ CLI에서 계획 요약 표시 (옵션 B)
2. ✅ 선택 메뉴 (1-6)

**Phase 2** (권장):
3. ✅ 웹에서 TODO 체크리스트 (옵션 A)
4. ✅ 스마트 검증 (옵션 C)

**Phase 3** (고급):
5. ✅ AI 기반 계획 자동 보완
6. ✅ 대화형 계획 수정

---

## 💾 데이터 모델

### TaskPlan 구조

```typescript
interface TaskPlan {
  task_id: string
  title: string
  description: string

  // 계획 완성도
  completeness: {
    score: number  // 0-100
    missing: string[]  // 부족한 부분
    warnings: string[]  // 경고
  }

  // TODO 그룹
  todo_groups: TodoGroup[]

  // 현재 위치
  current_step: {
    group_index: number
    item_index: number
  }

  // 메타데이터
  estimated_time: number  // minutes
  actual_time?: number
  updated_at: string
}

interface TodoGroup {
  id: string
  title: string
  status: "completed" | "in_progress" | "pending"
  order: number
  items: TodoItem[]
}

interface TodoItem {
  id: string
  title: string
  description?: string
  status: "completed" | "in_progress" | "pending"
  order: number

  // 상세 정보
  subtasks?: string[]
  acceptance_criteria?: string[]
  files?: string[]
  dependencies?: string[]  // 다른 TodoItem ID들

  // 시간 추적
  estimated_minutes?: number
  actual_minutes?: number
  started_at?: string
  completed_at?: string
}
```

---

## 📊 계획 완성도 검증 알고리즘

```python
class TaskPlanValidator:
    """작업 계획 완성도 검증"""

    def validate(self, task_plan: TaskPlan) -> ValidationResult:
        """계획 검증"""

        score = 0
        max_score = 100
        missing = []
        warnings = []

        # 1. 기본 정보 (20점)
        if task_plan.description and len(task_plan.description) > 50:
            score += 20
        else:
            missing.append("Detailed description (50+ chars)")

        # 2. TODO 그룹 존재 (20점)
        if task_plan.todo_groups and len(task_plan.todo_groups) >= 2:
            score += 20
        else:
            missing.append("TODO groups (min 2)")

        # 3. Subtasks 세분화 (20점)
        total_items = sum(len(g.items) for g in task_plan.todo_groups)
        if total_items >= 5:
            score += 20
        elif total_items >= 3:
            score += 10
            warnings.append("Consider adding more subtasks (5+ recommended)")
        else:
            missing.append("Subtasks (min 5)")

        # 4. Acceptance criteria (15점)
        items_with_ac = sum(
            1 for g in task_plan.todo_groups
            for item in g.items
            if item.acceptance_criteria
        )
        if items_with_ac >= total_items * 0.5:
            score += 15
        else:
            warnings.append("Add acceptance criteria to more tasks")

        # 5. 시간 추정 (10점)
        if task_plan.estimated_time:
            score += 10
        else:
            warnings.append("No time estimate")

        # 6. 의존성 정의 (10점)
        items_with_deps = sum(
            1 for g in task_plan.todo_groups
            for item in g.items
            if item.dependencies
        )
        if items_with_deps > 0:
            score += 10
        else:
            warnings.append("No dependencies defined (might be OK)")

        # 7. 파일 연결 (5점)
        items_with_files = sum(
            1 for g in task_plan.todo_groups
            for item in g.items
            if item.files
        )
        if items_with_files > 0:
            score += 5

        return ValidationResult(
            score=score,
            grade=self._calculate_grade(score),
            missing=missing,
            warnings=warnings
        )

    def _calculate_grade(self, score: int) -> str:
        if score >= 90:
            return "A"  # Excellent - 바로 시작 가능
        elif score >= 75:
            return "B"  # Good - 약간 보완 권장
        elif score >= 60:
            return "C"  # OK - 보완 필요
        elif score >= 40:
            return "D"  # Poor - 보완 필수
        else:
            return "F"  # Fail - 계획 다시 작성
```

---

## ✅ 최종 권장사항

### 질문 1에 대한 답변

**둘 다 구현합니다!**

1. **웹 대시보드**: TODO 체크리스트 (선택적)
   - 복잡한 계획은 웹에서 먼저 확인
   - 시각적으로 전체 조망

2. **CLI**: 계획 요약 + 검증 (필수)
   - 간단한 계획은 CLI에서 바로 확인
   - 스마트 검증으로 문제 조기 발견

3. **스마트 검증**: AI 자동 체크 (자동)
   - 불완전한 계획 자동 감지
   - 개선 제안

**워크플로우**:
```
빠른 작업: 카드 클릭 → CLI → 계획 확인 → 바로 시작
복잡한 작업: 카드 클릭 → 웹에서 TODO 확인 → CLI → 시작
```

**구현 순서**:
1. Phase 1: CLI 계획 확인 (필수)
2. Phase 2: 웹 TODO 체크리스트 (권장)
3. Phase 3: 스마트 검증 (고급)

