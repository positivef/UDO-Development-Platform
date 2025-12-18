# Kanban 사용자 시나리오 심층 분석

**작성일**: 2025-12-17
**목적**: 실제 사용자 워크플로우 기반 개발 우선순위 재정렬

---

## 📋 핵심 사용자 페르소나

### 페르소나 1: 프로젝트 리드 (김철수, 5년차 개발자)
**목표**: 프로젝트 전체 진행 상황 파악 및 Task 의존성 관리
**Pain Points**:
- Task 간 의존성을 명확히 설정하지 않으면 병목 발생
- 어떤 Task가 다른 Task를 블로킹하는지 한눈에 파악 어려움
- Context 파일(설계 문서, 요구사항)을 Task에 첨부해야 하는데 불편함

### 페르소나 2: 주니어 개발자 (이영희, 1년차)
**목표**: 할당된 Task를 정확히 이해하고 완료
**Pain Points**:
- Task 설명만으로는 부족, Context 파일 필요 (PRD, 설계 문서)
- 이 Task를 시작하기 전에 완료해야 할 다른 Task가 뭔지 모름
- Task 완료 기준이 모호함 (Quality Gate 통과? 리뷰 승인?)

### 페르소나 3: AI Assistant (Claude, UDO 시스템)
**목표**: Task 자동 생성 및 최적 순서 제안
**Pain Points**:
- AI가 제안한 Task를 사용자가 쉽게 승인/거부할 수 있어야 함
- 의존성을 자동으로 추론했을 때 사용자가 수정 가능해야 함

---

## 🎯 사용자 여정 맵핑 (User Journey Mapping)

### 여정 1: 새 프로젝트 시작 (Cold Start)

**단계별 사용자 행동**:

#### 1단계: 프로젝트 Phase 진입
```
사용자 행동: Kanban 보드 접속 → "Implementation" Phase 선택
현재 상태: ✅ Phase Tabs 있음 (Confidence Dashboard에서)
문제점: Kanban 보드에는 Phase 필터가 없음!
개선 필요: Kanban 보드에 Phase 필터 추가 (현재 Status/Priority만 있음)
```

#### 2단계: 첫 Task 생성
```
사용자 행동: "Create Task" 버튼 클릭 → TaskCreateModal 열림
현재 상태: ✅ Title, Description, Phase, Priority, Tags, 시간 추정 입력 가능
문제점 1: 의존성 설정이 없음! ❌
  - "이 Task는 Task A가 완료된 후에만 시작 가능"을 설정할 수 없음
문제점 2: Context 파일 첨부가 없음! ❌
  - PRD, 설계 문서를 Task 생성 시 바로 첨부할 수 없음
개선 필요:
  1. "Depends On" 필드 추가 (다른 Task 선택)
  2. "Attach Files" 버튼 추가 (ZIP 업로드)
```

#### 3단계: 의존성 있는 Task 추가 생성
```
사용자 시나리오:
  Task A: "API 설계" (선행 작업)
  Task B: "API 구현" (Task A에 의존)
  Task C: "프론트엔드 연동" (Task B에 의존)

현재 문제:
  - Task B 생성 시 "Task A 완료 후 시작"을 설정할 수 없음
  - 나중에 TaskDetailModal에서 추가해야 하는데, 그것도 불가능 (Read-only)

사용자가 원하는 것:
  - Task 생성할 때 바로 "Depends On: Task A" 선택
  - Hard Block 옵션 (기본값: true)
  - 또는 "Related to" (참고용, 블로킹 아님)
```

#### 4단계: Context 파일 업로드
```
사용자 행동: Task A 클릭 → Details 탭 → Context 탭 → Upload ZIP

현재 상태:
  ✅ ContextManager 컴포넌트 있음
  ⚠️ Upload 버튼은 placeholder (아직 작동 안 함)
  ✅ Download는 작동함

문제점:
  - ZIP 파일을 드래그앤드롭으로 업로드하고 싶음 (현재 불가)
  - 업로드 진행률을 보고 싶음 (50MB 파일은 시간 걸림)
  - 업로드 후 Context 자동 로드 확인 (Q4: Double-click auto-load)

사용자가 원하는 플로우:
  1. Context 탭 열기
  2. 파일 드래그앤드롭 또는 버튼 클릭
  3. 파일 선택 (ZIP만 허용, 50MB 제한)
  4. 업로드 진행률 표시 (0% → 100%)
  5. 완료 시 "Context loaded successfully" 메시지
  6. 메타데이터 자동 업데이트 (파일 개수, 크기)
```

### 여정 2: 진행 중인 프로젝트 관리 (Ongoing Work)

#### 5단계: 블로킹 Task 확인
```
사용자 시나리오:
  Task B (API 구현)를 시작하려는데, Task A (API 설계)가 아직 "In Progress"

사용자가 원하는 것:
  - Task B 카드에 "🔒 Blocked by Task A" 표시
  - Task B를 클릭하면 Details에서 "Dependencies" 섹션에 Task A 표시
  - Task A를 클릭하면 바로 이동 가능 (링크)

현재 상태:
  ✅ Dependencies 섹션 있음 (Read-only)
  ❌ Blocked 표시 없음
  ❌ Task 링크 클릭 불가

개선 필요:
  1. Blocked Task는 Status가 자동으로 "Blocked"로 변경
  2. Kanban 보드에서 Blocked 컬럼에 표시
  3. Task 카드에 "🔒 Blocked by N tasks" 뱃지
```

#### 6단계: Emergency Override (긴급 상황)
```
사용자 시나리오:
  Task A가 90% 완료되었지만, 급하게 Task B를 시작해야 함

사용자가 원하는 것:
  - Task B Details → Dependencies → Task A 옆에 "Override" 버튼
  - 클릭 시 확인 모달: "Are you sure? This violates the dependency chain."
  - Reason 입력: "Customer demo tomorrow, need to proceed"
  - Override 승인 → Task B Status를 "Blocked" → "Pending"으로 변경

현재 상태:
  ❌ Override 기능 없음
  ✅ DB에는 emergency_override 컬럼 있음

개선 필요:
  - Override UI + 이유 입력 + Audit 로그
```

#### 7단계: Task 완료 및 블로킹 해제
```
사용자 시나리오:
  Task A 완료 → Task B의 블로킹 자동 해제

사용자가 원하는 플로우:
  1. Task A를 "Done" 컬럼으로 드래그
  2. Quality Gate 검사 (자동)
  3. 통과 시 "Task completed! 2 blocked tasks are now unblocked" 알림
  4. Task B, Task C가 자동으로 "Blocked" → "Pending"으로 변경

현재 상태:
  ✅ Drag & drop 작동함
  ⚠️ Quality Gate 체크는 백엔드에만 있음 (프론트엔드 표시 없음)
  ❌ 블로킹 해제 자동화 없음

개선 필요:
  - Task 완료 시 Dependent Task 자동 업데이트
  - 알림 토스트 표시
```

### 여정 3: AI 협업 (AI-Assisted Development)

#### 8단계: AI Task Suggestion 받기
```
사용자 시나리오:
  프로젝트 시작 시 AI에게 "Authentication 기능 구현해줘" 요청

사용자가 원하는 플로우:
  1. Kanban 보드에서 "Ask AI for suggestions" 버튼 클릭
  2. 모달 열림: "What feature do you want to build?"
  3. 입력: "User authentication with JWT"
  4. AI가 5-7개 Task 생성 (예: Setup JWT, Login API, Register API, Middleware, Tests)
  5. 각 Task마다 Confidence Score 표시 (HIGH: 95%, MEDIUM: 75%)
  6. 의존성도 자동 설정 (예: "Login API depends on Setup JWT")
  7. 사용자가 각 Task를 개별 승인/거부
  8. 승인된 Task만 Kanban 보드에 추가

현재 상태:
  ✅ 백엔드 AI Suggestion API 있음 (POST /api/kanban/ai/suggest)
  ✅ Rate Limit 있음 (10/hour)
  ❌ 프론트엔드 UI 없음!

개선 필요:
  - AI Suggestion Modal
  - Task 리스트 + Confidence Score 표시
  - 개별 승인/거부 체크박스
  - 의존성 미리보기
```

### 여정 4: 프로젝트 회고 (Retrospective)

#### 9단계: 완료된 Task Archive
```
사용자 시나리오:
  Sprint 종료 → 완료된 Task를 Archive로 이동 → AI 요약 생성

사용자가 원하는 플로우:
  1. "Done" 컬럼의 Task 선택
  2. "Archive" 버튼 클릭 (또는 자동 Archive after 7 days)
  3. AI가 자동으로 요약 생성:
     - "What was accomplished"
     - "Key learnings"
     - "Technical insights"
  4. ROI 메트릭 계산 (Efficiency, Time saved, Quality score)
  5. Obsidian에 자동 동기화

현재 상태:
  ✅ 백엔드 Archive API 있음 (POST /api/kanban/archive)
  ✅ AI 요약 생성 (GPT-4o, mock mode)
  ❌ 프론트엔드 Archive UI 없음!

개선 필요:
  - Archive 버튼 추가
  - Archive 리스트 페이지
  - AI 요약 + ROI 대시보드
```

#### 10단계: Archive 검색 및 학습
```
사용자 시나리오:
  나중에 "JWT authentication"을 다시 구현할 때 과거 경험 참고

사용자가 원하는 플로우:
  1. Archive 페이지 접속
  2. 검색: "JWT authentication"
  3. 과거 완료된 Task 찾기
  4. AI 요약 읽기: "JWT setup took 3 hours, learned about token refresh"
  5. Context 파일 다운로드 (코드 스니펫, 설계 문서)
  6. 재사용

현재 상태:
  ✅ 백엔드에 Archive List API 있음 (GET /api/kanban/archive)
  ✅ 필터링: Phase, Archiver, AI suggested, Quality score
  ❌ 프론트엔드 페이지 없음!

개선 필요:
  - Archive 페이지 + 검색/필터
  - AI 요약 표시
  - ROI 통계 차트
```

---

## 🔍 현재 구현 Gap Analysis

### 구현 완료 ✅
1. ✅ Kanban 보드 (드래그앤드롭)
2. ✅ Task 생성 (기본 정보)
3. ✅ Task 상세 보기 (Details + Context 탭)
4. ✅ Context 다운로드
5. ✅ 필터링 (Phase, Status, Priority)
6. ✅ 백엔드 API 완성 (Dependencies, AI, Archive)

### 치명적 Gap (사용자 워크플로우 막힘) ❌
1. ❌ **의존성 설정 UI 없음** (Task 생성/편집 시)
   - 영향: Task 간 관계 설정 불가 → 프로젝트 관리 핵심 기능 작동 안 함
   - 우선순위: **P0 (최고)**

2. ❌ **Context 업로드 UI 없음** (placeholder만 있음)
   - 영향: 문서 첨부 불가 → 팀 협업 불가
   - 우선순위: **P0**

3. ❌ **Blocked Task 표시 없음**
   - 영향: 의존성 위반 감지 불가 → 잘못된 Task 실행
   - 우선순위: **P0**

### 중요 Gap (사용성 저하) ⚠️
4. ⚠️ **AI Suggestion Modal 없음**
   - 영향: AI 기능 사용 불가 → Q2 결정사항 미구현
   - 우선순위: **P1**

5. ⚠️ **Archive UI 없음**
   - 영향: 학습 기능 사용 불가 → Q6 결정사항 미구현
   - 우선순위: **P1**

6. ⚠️ **Quality Gate 프론트엔드 표시 없음**
   - 영향: 완료 기준 불명확 → Q3 결정사항 부분 구현
   - 우선순위: **P1**

### Nice-to-Have (추가 가치) 🎨
7. 🎨 **Dependency Graph 시각화**
   - 영향: 시각적 이해 향상 (필수는 아님)
   - 우선순위: **P2**

8. 🎨 **Emergency Override UI**
   - 영향: 긴급 상황 대응 (드물게 사용)
   - 우선순위: **P2**

---

## 📊 우선순위 재정렬 (사용자 영향도 기반)

### Week 6 Day 2 (오늘): P0 치명적 Gap 해결
**목표**: 핵심 워크플로우 작동 가능하게 만들기

#### Task 1: 의존성 관리 UI (4시간 예상)
```
구현 범위:
1. TaskCreateModal에 "Dependencies" 섹션 추가
   - "Depends On" 다중 선택 (다른 Task 검색)
   - "Dependency Type" 선택 (Blocks, Related)
   - "Hard Block" 체크박스 (기본: true)

2. TaskDetailModal에 Dependencies 편집 기능
   - 현재: Read-only 표시만
   - 추가: "Add Dependency" 버튼
   - 추가: 기존 의존성 삭제 버튼
   - 추가: Emergency Override 버튼 (이유 입력 모달)

3. Kanban 보드에 Blocked 표시
   - Task 카드에 "🔒 Blocked" 뱃지
   - Tooltip: "Blocked by Task A, Task B"
   - Blocked 상태면 드래그 비활성화 (또는 경고)

API 연동:
- POST /api/kanban/dependencies (의존성 추가)
- DELETE /api/kanban/dependencies/{id} (의존성 삭제)
- POST /api/kanban/dependencies/{id}/override (Emergency Override)
```

#### Task 2: Context Upload UI (3시간 예상)
```
구현 범위:
1. ContextManager 컴포넌트 완성
   - 파일 드래그앤드롭 영역
   - 파일 선택 버튼 (ZIP만 허용)
   - 50MB 크기 검증 (클라이언트 측)
   - 업로드 진행률 표시 (ProgressBar)
   - 성공/실패 알림

2. 업로드 플로우
   - 파일 선택 → 검증 → FormData 생성
   - POST /api/kanban/context 호출
   - onUploadProgress로 진행률 추적
   - 완료 시 메타데이터 리프레시

3. 에러 처리
   - 50MB 초과: "File too large (max 50MB)"
   - 잘못된 형식: "Only ZIP files allowed"
   - 네트워크 에러: "Upload failed, retry?"
```

#### Task 3: Blocked Task 자동 감지 및 표시 (2시간 예상)
```
구현 범위:
1. useKanban hook 확장
   - Task 리스트 로딩 시 의존성 체크
   - Blocked 상태 계산 (Dependencies에서)
   - Task 객체에 `isBlocked: boolean` 추가

2. TaskCard 컴포넌트 업데이트
   - isBlocked면 "🔒 Blocked" 뱃지 표시
   - opacity 낮춰서 시각적으로 구분
   - Hover 시 블로킹 Task 리스트 표시

3. Drag & Drop 제한
   - Blocked Task는 "In Progress"로 이동 불가
   - 시도 시 경고: "Cannot start blocked task. Complete dependencies first."
```

### Week 6 Day 3: P1 중요 Gap 해결
**목표**: AI 협업 및 Quality 피드백 구현

#### Task 4: AI Task Suggestion Modal (3시간)
- AI 제안 요청 UI
- Task 리스트 + Confidence Score 표시
- 개별 승인/거부
- Rate Limit 표시

#### Task 5: Quality Gate 프론트엔드 표시 (2시간)
- Task 완료 시 Quality Check 실행
- 통과/실패 알림
- 실패 시 완료 방지

### Week 6 Day 4: P1 학습 기능 구현
**목표**: Archive & ROI

#### Task 6: Archive View 페이지 (4시간)
- Archive 리스트 + 필터링
- AI 요약 표시
- ROI 메트릭 차트

### Week 6 Day 5: P2 시각화 및 통합
**목표**: Dependency Graph + E2E Tests

#### Task 7: Dependency Graph (선택적)
- D3.js 시각화
- 순환 의존성 감지

---

## 🎯 의사결정 프레임워크

### 구현 여부 판단 기준
```
if (차단하는_핵심_워크플로우):
    우선순위 = P0  # 즉시 구현
elif (Q1-Q8_결정사항_미구현):
    우선순위 = P1  # 이번 Week 내 구현
elif (사용성_크게_개선):
    우선순위 = P2  # 여유 있으면 구현
else:
    우선순위 = P3  # 다음 버전
```

### 사용자 테스트 시나리오 (Week 6 Day 5)
```
시나리오 1: 의존성 있는 3개 Task 생성
  - Task A, B, C 생성
  - B depends on A, C depends on B
  - A 완료 → B 자동 언블로킹
  - B 완료 → C 자동 언블로킹

시나리오 2: Context 파일 업로드 및 다운로드
  - ZIP 파일 업로드
  - Task에 첨부 확인
  - 다운로드 정상 작동

시나리오 3: AI Task Suggestion
  - "Login feature" 요청
  - 5개 Task 제안받기
  - 3개 승인, 2개 거부
  - Kanban 보드에 추가 확인
```

---

## 📈 예상 사용자 만족도

| 기능 | 구현 전 만족도 | 구현 후 만족도 | 증가폭 |
|------|----------------|----------------|--------|
| Task 생성 | 40% (의존성 설정 불가) | 85% | +45% |
| Task 관리 | 50% (블로킹 확인 불가) | 90% | +40% |
| Context 관리 | 30% (업로드 불가) | 80% | +50% |
| AI 협업 | 0% (UI 없음) | 75% | +75% |
| 학습 재사용 | 0% (Archive 없음) | 70% | +70% |
| **전체 평균** | **24%** | **80%** | **+56%** |

---

**결론**: 사용자 워크플로우 기반 우선순위 재정렬로 실용성 200% 향상 예상
