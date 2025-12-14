# PRD 종합 검토 보고서
**UDO Development Platform v3.0**

**날짜**: 2025-11-20
**검토자**: Claude (Requirements Analyst)
**목적**: 5개 PRD 심층 분석 및 보완 방안 제시

---

## Executive Summary

### 전체 현황
- **검토 대상**: PRD 01~05 (총 5개 문서, ~15,000 LOC)
- **전체 완성도**: 78% (우수)
- **주요 강점**: 기술 아키텍처 명확성, 리스크 분석 체계성
- **핵심 약점**: PRD 간 충돌 3건, 측정 가능성 부족 15%, 구현 갭 존재

### 긴급 조치 필요 항목 (Week 1 전 해결)
1. **PRD 02 (GPT Pro)**: 성공 지표 측정 방법 누락 → 정량화 필요
2. **PRD 03 (Magic)**: 기술 스택과 백엔드 API 불일치 → 인터페이스 명세 추가
3. **PRD 04 (Grok)**: RPN 보완 후에도 DB 마이그레이션 60% vs 50% 모순 → 통일 필요
4. **PRD 01 & 05**: pgvector 버전 불일치 (0.5.1 vs 미명시) → 버전 고정

---

## 1. PRD_01: 기술 아키텍처 (Gemini)

### ✅ 강점 (Strengths)
1. **명확한 인프라 설계**
   - Docker-compose 즉시 실행 가능 (Day 1 deployment ready)
   - pgvector 통합으로 별도 벡터 DB 불필요 (관리 포인트 단일화)
   - 비동기 아키텍처로 AI 병목 해결 (50ms 응답 유지 가능)

2. **구체적인 데이터 모델**
   - 4개 핵심 테이블 (projects, project_contexts, uncertainty_logs, uncertainty_feedback)
   - JSONB 활용으로 유연성 확보
   - RLHF 지원 구조 (self-learning 기반 마련)

3. **비용 최적화 전략**
   - Standard mode ($0.01) vs Deep Reasoning ($0.50) 이원화
   - RAG 기반 토큰 절감 (66K LOC → 상위 20 청크만 로드)

### ❌ 약점 (Weaknesses)
1. **데이터베이스 마이그레이션 전략 불명확**
   - 문제: "Day 1 즉시 PostgreSQL 전환"이지만 Grok PRD 04는 "점진적 마이그레이션" 권장
   - 영향: DB 장애 시 전체 시스템 다운 (RPN 90 리스크)
   - 충돌: PRD 05에서는 "Week 1-2 dual-write" 해결했으나, PRD 01은 미반영

2. **API 응답 시간 목표 모호**
   - 문제: "API 서버 < 50ms"라고 했으나, Grok PRD 04는 "170ms + 20ms 경쟁 버퍼"
   - 영향: 성능 테스트 기준 불명확
   - 근거 부족: 50ms 달성 가능성 검증 데이터 없음

3. **pgvector 설정 세부사항 부재**
   - 문제: 인덱스 타입(ivfflat, hnsw), lists 파라미터 미명시
   - 영향: 66K LOC 규모에서 검색 성능 예측 불가
   - PRD 05는 "ivfflat lists=100" 명시했으나 PRD 01 미반영

### 🔍 누락 (Missing)
1. **벡터 임베딩 생성 프로세스**
   - 필요: 초기 66K LOC 임베딩 비용 ($100 추정, PRD 05 참조)
   - 필요: 증분 업데이트 전략 (파일 변경 시 delta 임베딩)
   - 필요: 임베딩 품질 검증 방법 (코사인 유사도 >0.75 임계값)

2. **Circuit Breaker 구체적 설정**
   - 필요: 실패 임계값 (5회? 10회?)
   - 필요: 복구 시간 (60초? 300초?)
   - 필요: Fallback 우선순위 (PRD 05 참조: Claude → GPT-4o → Cached)

3. **데이터 백업 및 복구 전략**
   - 필요: PostgreSQL WAL 백업 주기
   - 필요: 복구 시간 목표 (RTO: <30분? <2시간?)
   - 필요: 데이터 손실 허용 범위 (RPO: 5분? 1시간?)

### 🔧 개선 제안 (Recommendations)

#### 우선순위 1 (Week 1 전 필수)
```yaml
1. DB 마이그레이션 전략 통일:
   - PRD 01 수정: "Day 1 즉시" → "Week 1-2 dual-write (PRD 05 참조)"
   - 추가: SQLite fallback 메커니즘 명시
   - 추가: 일관성 검증 스크립트 (compare.py)

2. pgvector 설정 명시:
   - docker-compose.yml에 추가:
     ```sql
     CREATE INDEX ON project_contexts
     USING ivfflat (embedding vector_cosine_ops)
     WITH (lists = 100);
     ```
   - 추가: 검색 성능 SLA (<500ms for top-20)

3. API 성능 목표 재정의:
   - "< 50ms" → "< 200ms (P95, PRD 04 기준)"
   - 추가: 성능 저하 시 자동 fallback 조건
```

#### 우선순위 2 (Week 2)
```yaml
1. 임베딩 파이프라인 문서화:
   - 초기 비용: $100 (66K LOC × 200-line chunks × $0.10/1M tokens)
   - 증분 업데이트: Git diff 기반 delta 임베딩
   - 품질 검증: Cosine similarity >0.75 for known queries

2. Circuit Breaker 구현 명세:
   - 임계값: 5회 연속 실패
   - 타임아웃: 60초 복구 대기
   - Fallback: Claude → GPT-4o → PostgreSQL cache

3. 백업 전략:
   - WAL continuous archiving (5분 주기)
   - Point-in-time recovery (<30분 RTO)
   - S3 glacier for long-term (7일 이상)
```

---

## 2. PRD_02: Product Strategy (GPT Pro)

### ✅ 강점 (Strengths)
1. **Phase-Aware 전략 독창성**
   - 5단계 개발 단계별 AI 판단 기준 차별화 (Ideation 60% → Deployment 95%)
   - 불확실성 상태(Quantum State)와 연동한 적응형 의사결정
   - 멀티-AI 조율 프레임워크 (Claude + Codex + Gemini 역할 분리)

2. **불확실성 지도 강제**
   - 모든 AI 출력에 "가장 덜 자신있는 부분" 명시 요구
   - "의견을 바꿀 수 있는 질문" 3개로 사용자 주도권 보장
   - RLHF 피드백 루프 설계 (학습 가능 시스템)

3. **명확한 사용자 시나리오**
   - 개발자, PM, QA별 맞춤 use case
   - 실제 워크플로우 시뮬레이션 가능

### ❌ 약점 (Weaknesses)
1. **성공 지표 측정 방법 부재**
   - 문제: "의사결정 소요시간 40% 절감"이지만 측정 도구 미명시
   - 문제: "NPS > 50"이지만 설문 시점/대상/도구 불명확
   - 문제: "프로젝트 오류 발생률 20% 감소"의 baseline 데이터 없음
   - 영향: 성공/실패 판단 불가능 → 프로젝트 리스크

2. **AI 모델 선택 기준 모호**
   - 문제: "Phase별 모델 선택"이지만 비용/정확도 trade-off 분석 없음
   - 문제: GPT Pro가 "조율자"인데 자기 자신을 선택하는 순환 논리
   - 충돌: PRD 01은 "GPT-4o-mini 기본"인데 PRD 02는 "GPT Pro 항상 사용" 암시

3. **충돌 해결 프로토콜 추상적**
   - 문제: "우선순위 규칙"이 3줄 설명으로 끝남
   - 필요: 30% 차이 계산 방법 (코사인 유사도? 문자열 diff?)
   - 필요: 동률 시 처리 (Claude 40% vs Codex 35% + Gemini 25% = 60%인 경우)

### 🔍 누락 (Missing)
1. **성공 지표 측정 인프라**
   - 필요: Grafana 대시보드 (의사결정 시간 추적)
   - 필요: NPS 설문 도구 (Typeform? Google Forms?)
   - 필요: 오류율 계산 로직 (error_count / total_tasks × 100)

2. **Phase 전환 트리거**
   - 필요: "Ideation → Planning" 전환 조건 (사용자 승인? 자동?)
   - 필요: 역행 가능 여부 (Deployment → Testing 롤백?)
   - 필요: Phase 불일치 시 처리 (프로젝트 메타데이터 vs 실제 작업 상태)

3. **GPT Pro Decision Memory 구현**
   - 필요: PostgreSQL 스키마 (decision_history 테이블)
   - 필요: 패턴 인식 알고리즘 (과거 유사 결정 검색)
   - 필요: 학습 곡선 측정 (초기 30분 → 4주 후 2분?)

### 🔧 개선 제안 (Recommendations)

#### 우선순위 1 (Week 1 전 필수)
```yaml
1. 성공 지표 측정 방법 구체화:
   - 의사결정 시간 측정:
     ```python
     @timer_decorator
     def make_decision(context):
         start = time.time()
         result = gpt_pro.decide(context)
         duration = time.time() - start
         log_metric("decision_duration", duration)
         return result
     ```
   - NPS 설문: Week 4 종료 시 Typeform 발송 (대상: 10명 내부 사용자)
   - 오류율:
     ```sql
     SELECT
       (COUNT(*) FILTER (WHERE status='failed') / COUNT(*))::FLOAT * 100 AS error_rate
     FROM tasks
     WHERE created_at >= NOW() - INTERVAL '1 week';
     ```

2. AI 모델 선택 decision tree 명시:
   - 기본 모델: GPT-4o-mini (PRD 01 기준)
   - GPT Pro 역할: 조율자 (Meta-AI, 다른 AI의 출력 판단만)
   - Phase-Aware 룰:
     ```python
     if phase == "Ideation" and uncertainty < 40:
         return "gpt-4o-mini"
     elif phase in ["Development", "Testing"] and task_type == "code":
         return "codex"
     elif uncertainty > 60 or phase == "Deployment":
         return "claude-3-sonnet"
     ```

3. 충돌 해결 알고리즘:
   - 차이 계산: Cosine similarity of embeddings
   - 투표 시스템: Weighted voting (Claude 40%, Codex 35%, Gemini 25%)
   - 동률: 사용자 escalation (> 1분 대기 후 UI 알림)
```

#### 우선순위 2 (Week 2-3)
```yaml
1. Phase 전환 로직:
   - 자동 전환: 사용자가 "배포 준비 완료" 체크박스 클릭 시
   - 역행 허용: Testing → Development (버그 발견 시)
   - Phase 불일치: 프로젝트 메타데이터 우선 (DB current_phase)

2. Decision Memory 스키마:
   ```sql
   CREATE TABLE decision_history (
     id BIGSERIAL PRIMARY KEY,
     project_id UUID REFERENCES projects(id),
     phase VARCHAR(50),
     decision_context JSONB,
     ai_choice VARCHAR(50),
     user_override BOOLEAN DEFAULT false,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   CREATE INDEX ON decision_history (project_id, phase);
   ```

3. 학습 곡선 추적:
   - Baseline: Week 1 평균 의사결정 시간
   - Target: Week 4 40% 절감
   - 시각화: Grafana line chart (daily average)
```

---

## 3. PRD_03: UX Implementation (Magic)

### ✅ 강점 (Strengths)
1. **Production-Ready 코드**
   - 2,500 LOC React/TypeScript 컴포넌트 (즉시 사용 가능)
   - WCAG 2.1 AA 준수 (접근성 최우선)
   - Framer Motion 애니메이션 (사용자 경험 우수)

2. **체계적인 UI 아키텍처**
   - 3개 핵심 컴포넌트 (Task List, CLI Integration, Quality Dashboard)
   - WebSocket 실시간 업데이트 (< 100ms latency)
   - Accessibility checklist (키보드 네비게이션, 스크린 리더)

3. **성능 최적화 전략**
   - Code splitting (lazy load)
   - Virtualization (react-window for >20 items)
   - Memoization (useMemo, memo)

### ❌ 약점 (Weaknesses)
1. **백엔드 API 인터페이스 불일치**
   - 문제: UI는 `/api/tasks/:id/context` 호출하지만 PRD 01/05에 해당 엔드포인트 없음
   - 문제: WebSocket `ws://localhost:8000/ws/tasks`인데 PRD 01은 단순 `/ws` 명시
   - 영향: Week 2 통합 시 404 오류 예상 → 2-3일 지연

2. **기술 스택 충돌**
   - 문제: Next.js 14 사용하지만 PRD 01은 FastAPI만 언급 (Next.js 미명시)
   - 문제: Recharts 차트 라이브러리인데 PRD 01/02에 데이터 API 스키마 없음
   - 충돌: PRD 05는 "Vercel 호스팅"인데 PRD 01은 "Docker-compose 로컬만"

3. **Progressive Enhancement 순서 불명확**
   - 문제: "Week 1: Task List (40%)" → 나머지 60% 언제?
   - 문제: "Defer: Advanced features" → 무엇이 advanced인지 목록 없음
   - 영향: 개발 우선순위 혼란 → 리소스 낭비

### 🔍 누락 (Missing)
1. **API 명세 (OpenAPI Spec)**
   - 필요: `/api/tasks/` 응답 스키마
   ```typescript
   interface TaskListResponse {
     items: Task[]
     total: number
     page: number
     has_next: boolean
   }
   ```
   - 필요: `/api/quality/metrics` 응답 예시
   ```json
   {
     "coverage": 85,
     "type_safety": 72,
     "complexity": "Medium",
     "tech_debt_hours": 12
   }
   ```

2. **에러 처리 전략**
   - 필요: API 실패 시 UI fallback (로컬 캐시? 이전 데이터 유지?)
   - 필요: WebSocket 재연결 로직 (exponential backoff)
   - 필요: 사용자 에러 메시지 문구 (toast 알림 내용)

3. **모바일 반응형 상세**
   - 필요: Breakpoint 정의 (sm: 640px, md: 768px, lg: 1024px)
   - 필요: 모바일 제스처 (swipe to delete task)
   - 필요: PWA manifest.json (오프라인 지원)

### 🔧 개선 제안 (Recommendations)

#### 우선순위 1 (Week 1 전 필수)
```yaml
1. API 인터페이스 명세 작성 (OpenAPI):
   - 파일: docs/api_spec.yaml
   - 도구: Swagger UI (자동 문서화)
   - 필수 엔드포인트:
     * GET /api/tasks/ → TaskListResponse
     * GET /api/tasks/:id → TaskDetail
     * GET /api/tasks/:id/context → CLIContext
     * GET /api/quality/metrics → QualityMetrics
   - WebSocket 이벤트:
     * task_updated: {id, status, completeness}
     * cli_activity: {timestamp, command, type}

2. Next.js + FastAPI 통합 아키텍처 명시:
   - 배포: Vercel (Next.js) + AWS ECS (FastAPI)
   - 통신: Vercel Proxy (/api/* → FastAPI)
   - 환경변수: NEXT_PUBLIC_API_URL=https://api.udo.com
   - 로컬 개발: Next.js (3000) + FastAPI (8000) 병렬 실행

3. Progressive Enhancement 로드맵:
   Week 1 (40%):
   - Task List: 카드 뷰 + 상태 표시 (모달 제외)
   - API: GET /api/tasks/ 만

   Week 2 (70%):
   - Task List: 모달 + TODO 체크리스트
   - CLI Panel: 명령 생성 + 클립보드 복사
   - API: GET /api/tasks/:id, /api/cli/context

   Week 3 (100%):
   - Quality Dashboard 전체
   - API: /api/quality/* 전체
```

#### 우선순위 2 (Week 2-3)
```yaml
1. 에러 처리 컴포넌트:
   ```tsx
   // components/ErrorBoundary.tsx
   export function ErrorBoundary({ children }) {
     return (
       <ErrorBoundaryWrapper
         fallback={<ErrorFallback />}
         onError={(error, info) => {
           logErrorToSentry(error, info)
         }}
       >
         {children}
       </ErrorBoundaryWrapper>
     )
   }
   ```

2. WebSocket 재연결 로직:
   ```typescript
   const connectWebSocket = (retryCount = 0) => {
     const ws = new WebSocket(WS_URL)
     ws.onclose = () => {
       const delay = Math.min(1000 * Math.pow(2, retryCount), 30000)
       setTimeout(() => connectWebSocket(retryCount + 1), delay)
     }
   }
   ```

3. 모바일 최적화:
   - Tailwind breakpoints: sm:, md:, lg:, xl:
   - Touch gestures: react-swipeable 라이브러리
   - PWA: next-pwa 플러그인 설정
```

---

## 4. PRD_04: Risk Analysis (Grok)

### ✅ 강점 (Strengths)
1. **FMEA 방법론 적용**
   - RPN (Risk Priority Number) 체계적 계산
   - 8개 주요 장애 모드 식별 (DB, 타입, 임포트, ML, 보안, UI, API, Git)
   - 완화 전 RPN 평균 150 → 완화 후 75 (50% 감소 목표)

2. **다차원 요인 고려**
   - 팀 역량, 예산 제약, 경쟁 압력 반영
   - 과거 실패 사례 (20% 확률) 포함
   - 가상 시뮬레이션으로 RPN 재조정

3. **기술 부채 정량화**
   - 550 LOC 중복 코드 (uncertainty_map_v3.py 200 LOC, Dict 변환 150 LOC)
   - 7개 mypy 타입 오류 (구체적 예시 포함)
   - 50+ 미커밋 파일 추적

### ❌ 약점 (Weaknesses)
1. **RPN 계산 근거 여전히 추측적**
   - 문제: "보완 후에도" DB 실패 발생률 60% → 50% 근거 불명확
   - 문제: "팀 수준 낮으면 +20%" → 20%의 출처?
   - 문제: "과거 실패 사례 20% 확률" → 어떤 데이터?
   - 영향: RPN 신뢰도 낮음 → 리스크 과소/과대평가 가능

2. **보완 전후 RPN 모순**
   - 문제: DB 실패 RPN 540 → 90 (83% 감소)인데 "가장 높은 리스크"라고 함
   - 문제: 타입 오류 RPN 480 → 120 (75% 감소)인데 "고RPN" 유지
   - 충돌: PRD 05는 "평균 RPN <80"인데 PRD 04는 "120 허용" 암시

3. **완화 전략 실행 가능성 불확실**
   - 문제: "Week 1 JWT 수정"인데 구현 시간 미추정 (2일? 5일?)
   - 문제: "Week 2 캐싱"인데 Redis 설정 누락 (PRD 01에는 있음)
   - 문제: "Week 3 오프로드"인데 GPU 인프라 가정 없음

### 🔍 누락 (Missing)
1. **리스크 발생 시나리오**
   - 필요: DB 실패 → SQLite fallback 전환 시간 (<2분? <30분?)
   - 필요: 타입 오류 → 런타임 크래시 복구 절차
   - 필요: ML 타임아웃 → 사용자에게 보여줄 메시지

2. **리스크 모니터링 도구**
   - 필요: Grafana RPN 대시보드 (실시간 추적)
   - 필요: Slack 알림 (RPN >80 발생 시)
   - 필요: Weekly 리스크 리포트 (자동 생성)

3. **Post-Mortem 프로세스**
   - 필요: 장애 발생 시 분석 템플릿
   - 필요: 교훈 저장소 (PostgreSQL uncertainty_feedback 활용?)
   - 필요: 재발 방지 체크리스트

### 🔧 개선 제안 (Recommendations)

#### 우선순위 1 (Week 1 전 필수)
```yaml
1. RPN 계산 근거 데이터화:
   - 기준 데이터:
     * 팀 수준: 중간 (Netflix/Uber 5년 경력 = baseline 1.0x)
     * 과거 실패: GitHub commit history 분석 (revert 비율 20%)
     * 예산 제약: 월 $500 초과 시 발생률 +10%
   - 보정 공식:
     ```python
     RPN_adjusted = Severity × (Occurrence × team_factor × budget_factor) × (Detection / automation_rate)
     ```
   - 검증: 3명 엔지니어 개별 평가 후 평균

2. RPN 목표 통일:
   - PRD 04 수정: "평균 RPN <80" (PRD 05 기준)
   - 개별 리스크 목표:
     * CRITICAL (Severity 9): RPN <100
     * HIGH (Severity 7-8): RPN <80
     * MEDIUM (Severity 5-6): RPN <60
   - 재계산 결과:
     * DB 실패: 90 → 목표 100 (OK)
     * 타입 오류: 120 → 목표 80 (NOT OK, 추가 완화 필요)

3. 완화 전략 실행 계획:
   Week 1:
   - Day 1-2: JWT 구현 (2명×2일=4인일)
   - Day 3: 키 관리 (AWS Secrets Manager 설정)
   - Day 4-5: 입력 검증 (Pydantic 모델 8개)

   Week 2:
   - Day 1-2: Redis 캐싱 (5개 엔드포인트, 5분 TTL)
   - Day 3-4: mypy 수정 (7개 오류, 1일 1개 목표)

   Week 3:
   - Day 1-3: ML 오프로드 (Celery 큐, GPU 불필요)
   - Day 4-5: UI 최적화 (code splitting, memoization)
```

#### 우선순위 2 (Week 2-4)
```yaml
1. 리스크 모니터링 시스템:
   - Grafana 대시보드:
     * 패널 1: RPN 히트맵 (8개 리스크 × 시간)
     * 패널 2: Top 3 리스크 트렌드 (선 차트)
     * 패널 3: 완화 조치 진행률 (프로그래스 바)
   - Slack 알림:
     ```python
     if current_rpn > 80:
         slack.send(f"⚠️ High RPN: {risk_name} = {current_rpn}")
     ```

2. Post-Mortem 템플릿:
   ```markdown
   # Incident: [제목]
   ## 타임라인
   - T+0: 사용자 리포트
   - T+5: 엔지니어 확인
   - T+30: 임시 조치
   - T+120: 근본 원인 수정

   ## Root Cause
   - 직접 원인: [예: DB 연결 풀 고갈]
   - 근본 원인: [예: 연결 누수]

   ## Action Items
   - [ ] 재발 방지 (예: connection pool monitoring)
   - [ ] 문서 업데이트 (runbook)
   - [ ] RPN 재평가 (발생률 갱신)
   ```

3. RPN 자동 재계산:
   - 트리거: 장애 발생 시 uncertainty_logs에 기록
   - 로직: 발생률 = (최근 30일 장애 건수 / 30) × 10
   - 업데이트: 주간 리뷰 시 Grafana에서 확인
```

---

## 5. PRD_05: Integration (Claude)

### ✅ 강점 (Strengths)
1. **종합 조율 능력**
   - 4개 PRD 충돌 3건 식별 및 해결
   - 47개 교차 참조로 일관성 확보
   - 28개 리스크 통합 관리

2. **실행 가능한 4주 로드맵**
   - Week별 우선순위 명확 (Foundation → Intelligence → Performance → Integration)
   - 질적 게이트 (Quality Gates) 설정 (각 주 종료 시 검증)
   - 구체적 산출물 정의 (1,200+ LOC 문서)

3. **비용 및 리소스 현실적**
   - 총 예산 $31,572 (인프라 $115 + AI $5.65 + 인건비 $26,500)
   - 팀 배치 (Senior 50%, ML 30%, UX 20%)
   - 비상 예비비 20% ($5,262)

### ❌ 약점 (Weaknesses)
1. **지나치게 낙관적인 일정**
   - 문제: Week 1에 "DB 마이그레이션 + 보안 패치 + 타입 수정" 동시 진행
   - 문제: Week 2에 "RAG 파이프라인 + 멀티-AI 브리지 + Task UI" 병렬 작업
   - 리스크: 한 작업 지연 시 전체 연쇄 지연 (크리티컬 패스 미고려)

2. **측정 가능성 일부 추상적**
   - 문제: "Automation Rate 85%"의 분모 정의 불명확 (전체 이슈? AI 적용 가능 이슈?)
   - 문제: "Decision Accuracy 95%"의 측정 방법 불명확 (사용자 피드백? 자동 검증?)
   - 문제: "Error Recovery Time 2분"의 시작점 불명확 (에러 발생 시점? 감지 시점?)

3. **외부 의존성 리스크 과소평가**
   - 문제: OpenAI API 장애 시 대응 방안 부족 (5회 실패 → fallback인데 장애 1시간 지속 시?)
   - 문제: pgvector 버전 업그레이드 시 호환성 (0.5.1 → 0.6.0)
   - 문제: Next.js 14 breaking changes (14.0 → 14.1 마이너 업데이트도 위험)

### 🔍 누락 (Missing)
1. **크리티컬 패스 분석**
   - 필요: PERT 차트 (Program Evaluation Review Technique)
   - 필요: 병목 식별 (예: RAG 파이프라인 완료 전까지 Multi-AI 작업 블록)
   - 필요: 슬랙 타임 계산 (각 작업의 여유 시간)

2. **리스크 관리 계획**
   - 필요: 주간 리스크 리뷰 회의 (매주 금요일 2PM)
   - 필요: 리스크 레지스터 (식별 → 평가 → 완화 → 모니터링)
   - 필요: 조기 경고 지표 (예: Week 1 automation <50% → Week 4 목표 미달 예측)

3. **변경 관리 프로세스**
   - 필요: PRD 변경 승인 절차 (누가 승인? 어떤 기준?)
   - 필요: Scope creep 방지 (기능 추가 요청 시 Week 4 후로 연기)
   - 필요: 우선순위 재조정 기준 (어떤 상황에서 Week 2-3 순서 변경?)

### 🔧 개선 제안 (Recommendations)

#### 우선순위 1 (Week 1 전 필수)
```yaml
1. 크리티컬 패스 재분석:
   - PERT 차트 작성:
     ```
     Week 1: DB 마이그레이션 (CRITICAL PATH)
       └─> Week 2: RAG 파이프라인 (CRITICAL PATH)
           └─> Week 3: Multi-AI 조율
               └─> Week 4: 통합 테스트

     Week 1: 보안 패치 (병렬, 슬랙 2일)
     Week 2: Task UI (병렬, 슬랙 3일)
     ```
   - 병목 완화:
     * DB 마이그레이션 우선 (Day 1-3)
     * 보안 패치 병렬 (Day 1-5, 리소스 분리)
     * 타입 수정은 Week 2로 연기 (비크리티컬)

2. 측정 가능성 구체화:
   - Automation Rate:
     ```python
     total_issues = count(uncertainty_logs WHERE created_at >= week_start)
     auto_resolved = count(... WHERE resolved_by IN ['tier1', 'tier2'])
     automation_rate = (auto_resolved / total_issues) × 100
     ```
   - Decision Accuracy:
     ```python
     correct_decisions = count(uncertainty_feedback WHERE rating = 1)
     total_decisions = count(uncertainty_feedback)
     accuracy = (correct_decisions / total_decisions) × 100
     ```
   - Error Recovery Time:
     ```python
     start = error_log.detected_at  # 시스템 감지 시점
     end = uncertainty_log.created_at  # 해결책 생성 시점
     recovery_time = end - start
     ```

3. 외부 의존성 다중 fallback:
   - OpenAI 장애:
     * Level 1: Retry with exponential backoff (3회, 1s → 2s → 4s)
     * Level 2: Switch to Anthropic Claude (5분 이내)
     * Level 3: Use cached responses (PostgreSQL, 유사도 >0.85)
     * Level 4: Degrade to rule-based system (1시간 이상)
   - pgvector:
     * 버전 고정: 0.5.1 (docker-compose.yml에 명시)
     * 업그레이드 금지: Week 1-4 동안 (안정성 우선)
     * 테스트 환경: Week 4 후 별도 검증
   - Next.js:
     * 버전 고정: 14.0.x (package.json "~14.0.0")
     * Dependabot 비활성화 (수동 업그레이드만)
```

#### 우선순위 2 (Week 2-4)
```yaml
1. 리스크 관리 프로세스:
   - 리스크 레지스터:
     | ID | 리스크 | 확률 | 영향 | 완화 전략 | 담당자 | 상태 |
     |----|--------|------|------|-----------|--------|------|
     | R1 | DB 마이그레이션 실패 | 30% | HIGH | Dual-write | 홍길동 | Open |
     | R2 | OpenAI API 장애 | 10% | MED | Multi-provider | 김철수 | Mitigated |

   - 주간 리뷰:
     * 매주 금요일 2PM (1시간)
     * 참석: Tech Lead, Product Owner, 각 영역 담당자
     * 안건: 리스크 레지스터 업데이트, 조기 경고 지표 확인

2. 변경 관리 절차:
   - PRD 변경 승인:
     * Minor (예: 성능 목표 200ms → 250ms): Tech Lead 승인
     * Major (예: Week 순서 변경): Product Owner + Tech Lead 합의
     * Critical (예: 기능 추가/삭제): Stakeholder 회의

   - Scope creep 방지:
     * "Nice to have" 기능은 Phase 2로 연기 (backlog에 기록)
     * Week 4 목표 달성이 우선 (85% automation)

3. 조기 경고 시스템:
   - Week 1 종료 시:
     * Automation Rate <50% → Week 4 목표 미달 위험 90%
     * Security RPN >150 → Week 3까지 추가 리소스 필요
   - Week 2 종료 시:
     * RAG cost >$0.10 → 예산 초과 위험
     * Multi-AI 충돌 해결 <80% → Decision accuracy 목표 위험
```

---

## 종합 충돌 해결 매트릭스

### 충돌 1: 데이터베이스 마이그레이션 전략
| PRD | 입장 | 근거 |
|-----|------|------|
| PRD 01 (Gemini) | Day 1 즉시 PostgreSQL | "빠른 RAG 구축" |
| PRD 04 (Grok) | 점진적 마이그레이션 (SQLite fallback) | "RPN 90 리스크" |
| PRD 05 (Claude) | Week 1-2 dual-write | "안정성 + 속도 균형" |

**최종 해결책** (PRD 05 채택):
```yaml
Week 1:
- Day 1-2: PostgreSQL + pgvector 설치 및 스키마 생성
- Day 3-4: Dual-write 모드 (SQLite + PostgreSQL 동시 쓰기)
- Day 5: 일관성 검증 (compare.py 스크립트)

Week 2:
- PostgreSQL를 primary로 전환
- SQLite는 fallback으로 유지 (읽기 전용)
- 성능 모니터링 (<100ms 쿼리 시간)

Week 3:
- PostgreSQL 안정성 95% 확인 시 SQLite 제거
- 롤백 불가능 지점 (Point of No Return)

조건:
- PostgreSQL 장애 시 자동 fallback (< 2분)
- 데이터 불일치 시 SQLite 우선 (사용자 데이터 보호)
```

### 충돌 2: API 성능 목표
| PRD | 목표 | 근거 |
|-----|------|------|
| PRD 01 (Gemini) | <50ms | "API 서버 응답성" |
| PRD 04 (Grok) | 170ms (+20ms 경쟁 버퍼) | "현실적 측정치" |
| PRD 05 (Claude) | <200ms (P95) | "산업 표준" |

**최종 해결책** (PRD 05 채택, PRD 01 수정):
```yaml
성능 목표 (P95 기준):
- API 엔드포인트: <200ms
  * /api/tasks/ (단순 조회): <50ms (PRD 01 목표 유지)
  * /api/quality/metrics (계산 필요): <150ms
  * /api/cli/context (RAG 검색 포함): <200ms

측정 방법:
- Prometheus histogram_quantile(0.95, ...)
- Grafana 대시보드 (실시간)
- Weekly 성능 리포트 (자동 생성)

Fallback:
- >200ms 3회 연속: Circuit breaker 발동
- 캐시 응답 반환 (5분 TTL)
- 백그라운드에서 재시도
```

### 충돌 3: UI 기술 스택 및 배포
| PRD | 기술 스택 | 배포 방식 |
|-----|----------|-----------|
| PRD 01 (Gemini) | FastAPI만 명시 | Docker-compose 로컬 |
| PRD 03 (Magic) | Next.js 14 + FastAPI | Vercel + AWS |
| PRD 05 (Claude) | Next.js + FastAPI | Vercel + ECS |

**최종 해결책** (PRD 03 + PRD 05 통합, PRD 01 보완):
```yaml
아키텍처:
- Frontend: Next.js 14 (Vercel 호스팅)
  * SSR for SEO (landing page)
  * CSR for dashboard (dynamic content)
  * API proxy: /api/* → FastAPI backend

- Backend: FastAPI (AWS ECS Fargate)
  * 2 tasks minimum (HA)
  * Auto-scaling (최대 10 tasks)
  * ALB health check (/health)

로컬 개발:
- docker-compose.yml 업데이트:
  ```yaml
  services:
    frontend:
      build: ./frontend
      ports: ["3000:3000"]
      environment:
        - NEXT_PUBLIC_API_URL=http://localhost:8000

    api:
      # (기존 PRD 01 설정 유지)
  ```

배포:
- Week 1-3: 로컬 개발 환경만 (docker-compose)
- Week 4: Vercel + AWS 프로덕션 배포
- CI/CD: GitHub Actions (automated testing + deployment)
```

### 충돌 4: AI 모델 선택 및 비용
| PRD | 기본 모델 | 비용 전략 |
|-----|----------|----------|
| PRD 01 (Gemini) | GPT-4o-mini | Standard $0.01 / Deep $0.50 |
| PRD 02 (GPT Pro) | GPT Pro 항상 사용 (암시적) | 미명시 |
| PRD 05 (Claude) | 적응형 (Phase + Uncertainty) | $0.01 평균 |

**최종 해결책** (PRD 05 명확화, PRD 02 역할 재정의):
```yaml
AI 역할 정의:
- GPT Pro: 조율자(Meta-AI)만
  * 다른 AI의 출력 판단
  * 충돌 해결
  * Phase 전환 승인
  * 비용: $0.03/1K (전체의 5%)

- Claude 3.5 Sonnet: 전략/설계
  * CHAOTIC 상태 (uncertainty >60)
  * Deployment phase (critical)
  * 비용: $0.015/1K (전체의 10%)

- GPT-4o-mini: 기본 작업
  * DETERMINISTIC/PROBABILISTIC (uncertainty <40)
  * 일상 대화, 단순 조회
  * 비용: $0.0005/1K (전체의 70%)

- Codex: 코드 생성
  * Development phase + code 작업
  * 비용: $0.002/1K (전체의 10%)

- Gemini Flash: 분석/메트릭
  * Testing phase
  * 성능 질문
  * 비용: $0.0001/1K (전체의 5%)

예상 분포:
- 총 요청: 1,000/day
- 평균 비용: $0.01/query
- 월 총 비용: $300 (예산 $500 이내)
```

---

## 우선순위별 보완 로드맵

### 🔴 Critical (Week 1 착수 전 필수, 48시간 이내)

1. **API 인터페이스 명세 작성** (6시간)
   - 담당: Tech Lead + UX Engineer
   - 산출물: `docs/api_spec.yaml` (OpenAPI 3.0)
   - 검증: Swagger UI에서 모든 엔드포인트 문서화 확인

2. **성공 지표 측정 인프라 구축** (8시간)
   - 담당: Senior Engineer
   - 산출물:
     * Grafana 대시보드 (automation_rate, decision_accuracy, recovery_time)
     * PostgreSQL 테이블 (metrics_log)
   - 검증: 더미 데이터로 차트 렌더링 확인

3. **크리티컬 패스 분석 및 일정 재조정** (4시간)
   - 담당: Tech Lead + Product Owner
   - 산출물: PERT 차트 + 조정된 Week 1-4 일정
   - 검증: 슬랙 타임 <2일 작업 식별 및 리소스 추가 배정

4. **PRD 버전 통일** (2시간)
   - 담당: Tech Lead
   - 수정:
     * PRD 01: "Day 1 PostgreSQL" → "Week 1-2 dual-write" (section 3.1)
     * PRD 01: "API <50ms" → "API <200ms (P95), 단순 조회 <50ms" (section 2.2)
     * PRD 02: GPT Pro 역할 명확화 "조율자 전용" (section 2.1)
     * PRD 04: "RPN 평균 <80" 목표 추가 (section 7)
   - 검증: 5개 PRD 교차 검증 (충돌 0건)

### 🟡 High (Week 1 중, 1주일 이내)

5. **백엔드 API 구현** (16시간)
   - 담당: Senior Engineer + ML Engineer
   - 산출물:
     * `/api/tasks/` (GET, POST, PATCH, DELETE)
     * `/api/tasks/:id/context` (GET)
     * `/api/quality/*` (GET)
     * WebSocket `/ws/tasks`, `/ws/cli`
   - 검증: Postman 테스트 통과 (100% 엔드포인트)

6. **pgvector 설정 및 성능 테스트** (8시간)
   - 담당: Senior Engineer
   - 작업:
     * ivfflat 인덱스 (lists=100)
     * 검색 성능 SLA (<500ms for top-20)
     * 임베딩 생성 파이프라인 (batch size=50)
   - 검증: 66K LOC → 500K tokens → $100 비용 확인, <500ms 검색

7. **RPN 재계산 및 완화 전략 구체화** (6시간)
   - 담당: Tech Lead + Senior Engineer
   - 작업:
     * RPN 근거 데이터 명시 (팀 수준, 과거 실패율)
     * 타입 오류 RPN 120 → 80 추가 완화 (CI 강제 mypy)
     * Week 1-3 완화 조치 실행 계획 (시간 추정 포함)
   - 검증: 평균 RPN <80 달성 가능성 80% 이상

### 🟢 Medium (Week 2-3, 2주일 이내)

8. **에러 처리 및 Fallback 로직** (12시간)
   - 담당: Senior Engineer
   - 작업:
     * Circuit Breaker (5회 실패, 60초 복구)
     * Multi-provider fallback (OpenAI → Anthropic → Cache)
     * WebSocket 재연결 (exponential backoff)
   - 검증: 장애 시뮬레이션 (API 500 응답) → 2분 내 복구

9. **Progressive Enhancement UI 로드맵** (4시간)
   - 담당: UX Engineer + Product Owner
   - 산출물:
     * Week 1: Task List 40% (카드만, 모달 제외)
     * Week 2: Task List 70% + CLI Panel (기본)
     * Week 3: Quality Dashboard 100%
   - 검증: 각 주 QA 게이트 통과 (WCAG 0 violation)

10. **리스크 모니터링 시스템** (8시간)
    - 담당: Senior Engineer
    - 산출물:
      * Grafana RPN 대시보드
      * Slack 알림 (RPN >80)
      * 주간 리스크 리포트 (자동 생성)
    - 검증: 더미 RPN 데이터 → Slack 알림 발송 확인

### 🔵 Low (Week 4 또는 Phase 2, 1개월 이내)

11. **모바일 최적화** (16시간)
    - 담당: UX Engineer
    - 작업:
      * Breakpoint 정의 (sm, md, lg, xl)
      * Touch 제스처 (swipe)
      * PWA manifest (오프라인 지원)
    - 검증: iPhone 12, Galaxy S21 실기 테스트

12. **Post-Mortem 프로세스** (4시간)
    - 담당: Tech Lead
    - 산출물:
      * 장애 분석 템플릿
      * PostgreSQL incident_log 테이블
      * 재발 방지 체크리스트
    - 검증: 첫 장애 발생 시 템플릿 적용

13. **AI Decision Memory** (20시간)
    - 담당: ML Engineer
    - 작업:
      * decision_history 테이블
      * 패턴 인식 알고리즘 (유사 결정 검색)
      * 학습 곡선 추적 (30분 → 2분)
    - 검증: 동일 질문 2회 → 2번째 응답 시간 <10% (학습 효과)

---

## 측정 가능성 개선 제안

### 현재 문제점
- **추상적 목표**: "의사결정 속도 향상", "품질 개선"
- **측정 방법 부재**: 어떻게 측정? 언제 측정?
- **Baseline 데이터 없음**: 현재 상태 vs 목표 비교 불가

### 해결 방안

#### 1. Automation Rate (85% 목표)
```python
# 정의
automation_rate = (tier1_resolved + tier2_resolved) / total_issues × 100

# 측정 방법
SELECT
  COUNT(*) FILTER (WHERE resolved_by = 'tier1') AS tier1,
  COUNT(*) FILTER (WHERE resolved_by = 'tier2') AS tier2,
  COUNT(*) AS total,
  (COUNT(*) FILTER (WHERE resolved_by IN ('tier1', 'tier2')) / COUNT(*)::FLOAT * 100) AS automation_rate
FROM uncertainty_logs
WHERE created_at >= '2025-11-20' AND created_at < '2025-12-18';

# Baseline (Week 0)
- Tier 1: 30% (기존 Obsidian)
- Tier 2: 15% (Context7)
- Total: 45%

# 목표 (Week 4)
- Tier 1: 40% (+10%, PostgreSQL 학습 효과)
- Tier 2: 45% (+30%, RAG + Multi-AI)
- Total: 85% (+40%)

# 측정 주기
- 일간: Grafana 대시보드 (실시간)
- 주간: 리포트 (월요일 오전, 지난주 평균)
- 월간: 경영진 보고 (트렌드 분석)
```

#### 2. Decision Accuracy (95% 목표)
```python
# 정의
decision_accuracy = correct_decisions / total_decisions × 100

# 측정 방법
SELECT
  COUNT(*) FILTER (WHERE rating = 1) AS correct,
  COUNT(*) AS total,
  (COUNT(*) FILTER (WHERE rating = 1) / COUNT(*)::FLOAT * 100) AS accuracy
FROM uncertainty_feedback
WHERE created_at >= NOW() - INTERVAL '7 days';

# 사용자 피드백 수집
- UI: 각 AI 응답 하단에 👍/👎 버튼
- 저장: uncertainty_feedback 테이블
- 인센티브: 피드백 10회 → 프리미엄 기능 7일 무료

# Baseline (Week 0)
- 단일 모델 (Claude만): 70%
- Phase 무시: 65%

# 목표 (Week 4)
- Phase-Aware: 95%
- Multi-AI 조율: 97% (충돌 해결 효과)

# 측정 주기
- 일간: 피드백 수 모니터링 (최소 10개/일)
- 주간: 정확도 계산 (95% 미달 시 알림)
```

#### 3. Error Recovery Time (2분 목표)
```python
# 정의
recovery_time = resolution_time - detection_time

# 측정 방법
SELECT
  AVG(EXTRACT(EPOCH FROM (ul.created_at - el.detected_at))) / 60 AS avg_recovery_min,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (ul.created_at - el.detected_at))) / 60 AS p95_recovery_min
FROM error_logs el
JOIN uncertainty_logs ul ON el.id = ul.error_log_id
WHERE el.detected_at >= NOW() - INTERVAL '7 days';

# 타임라인
1. Error 발생 (T+0)
2. 시스템 감지 (T+0.1s, error_logs.detected_at)
3. Tier 1 검색 (T+0.2s, Obsidian)
4. Tier 2 검색 (T+1s, RAG + Multi-AI)
5. 해결책 생성 (T+2s, uncertainty_logs.created_at)
6. 사용자 알림 (T+2.5s, WebSocket)

# Baseline (Week 0)
- 평균: 30분 (Tier 3 사용자 개입)
- P95: 2시간 (복잡한 문제)

# 목표 (Week 4)
- 평균: 2분 (Tier 1+2 자동화)
- P95: 5분 (CHAOTIC 상태)

# 측정 주기
- 실시간: Grafana histogram (0-60분 범위)
- 주간: P50, P95, P99 추적
```

#### 4. Context Loading Cost ($0.01 목표)
```python
# 정의
avg_cost = total_ai_cost / total_queries

# 측정 방법
SELECT
  SUM(token_count * unit_cost) AS total_cost,
  COUNT(*) AS total_queries,
  (SUM(token_count * unit_cost) / COUNT(*)) AS avg_cost_per_query
FROM ai_usage_logs
WHERE created_at >= NOW() - INTERVAL '1 day';

# 토큰 비용 (2025년 기준)
- GPT-4o-mini: $0.15/1M input, $0.60/1M output
- Claude Sonnet: $3/1M input, $15/1M output
- Ada-002 (embedding): $0.10/1M

# Baseline (Week 0)
- 전체 컨텍스트 로드: 50K tokens × $3/1M = $0.15
- 항상 Claude Opus: $15/1M output = $0.30
- 총: $0.50/query

# 목표 (Week 4)
- RAG top-20 청크: 5K tokens × $0.15/1M = $0.0008
- GPT-4o-mini 70%: $0.60/1M output × 70% = $0.0042
- Claude Sonnet 10%: $15/1M output × 10% = $0.0015
- 총: $0.01/query (98% 절감)

# 측정 주기
- 실시간: 누적 비용 (일간 예산 $10 알림)
- 주간: 모델별 비용 분포 (파이 차트)
- 월간: ROI 분석 (비용 절감 vs 정확도)
```

#### 5. Technical Debt (<100 LOC 목표)
```python
# 정의
debt_loc = duplicate_code_loc + unused_code_loc + complex_code_loc

# 측정 방법
# 1. 중복 코드 (jscpd)
npx jscpd --min-lines 5 --min-tokens 50 src/

# 2. 사용하지 않는 코드 (vulture)
vulture src/ --min-confidence 80

# 3. 복잡한 코드 (radon)
radon cc src/ -a -nb

# Baseline (Week 0)
- 중복: 550 LOC (uncertainty_map_v3.py 200, Dict 변환 150)
- 미사용: 50 LOC (deprecated functions)
- 복잡도 >10: 100 LOC (난독화된 로직)
- 총: 700 LOC

# 목표 (Week 4)
- 중복: 50 LOC (공통 모듈로 추출)
- 미사용: 0 LOC (제거)
- 복잡도 >10: 50 LOC (리팩토링)
- 총: 100 LOC (85% 절감)

# 측정 주기
- 일간: CI/CD에서 자동 측정 (PR merge 전)
- 주간: 트렌드 분석 (증가 시 리팩토링 주간 할당)
```

---

## 최종 권고사항

### Immediate Actions (24시간 내)
1. ✅ **PRD 버전 통일 회의** (2시간)
   - 참석: Tech Lead, Product Owner, Senior Engineer
   - 안건: 4개 충돌 해결 방안 승인
   - 산출물: 통일된 PRD v2.0 (각 PRD 업데이트)

2. ✅ **API 명세 작성 착수** (4시간)
   - 담당: Tech Lead + UX Engineer
   - OpenAPI 3.0 Spec 초안 완성
   - Swagger UI 배포 (http://localhost:8080/docs)

3. ✅ **크리티컬 패스 분석** (2시간)
   - 담당: Tech Lead
   - PERT 차트 작성 (Mermaid.js or Lucidchart)
   - 병목 식별 및 리소스 재배치

### Week 1 Priorities (재조정)
```yaml
Day 1-2 (CRITICAL PATH):
- PostgreSQL + pgvector 설치
- 스키마 생성 (Alembic migration)
- 성능 테스트 (>500ms 검색 시간 시 인덱스 튜닝)

Day 3-4 (PARALLEL):
- Dual-write 모드 구현 (Senior Engineer)
- API 명세 기반 FastAPI 엔드포인트 구현 (ML Engineer)
- 일관성 검증 스크립트 (compare.py)

Day 5 (INTEGRATION):
- API + DB 통합 테스트
- 보안 패치 시작 (JWT, input validation)
- 주간 리뷰 (금요일 2PM, 진행률 평가)
```

### Success Criteria (4주 후)
```yaml
기술 지표:
- ✅ Automation Rate: ≥85%
- ✅ Decision Accuracy: ≥95%
- ✅ Error Recovery: ≤2분 (평균)
- ✅ Context Cost: ≤$0.01 (평균)
- ✅ Technical Debt: ≤100 LOC

품질 지표:
- ✅ Security RPN: <80 (평균)
- ✅ API Response: <200ms (P95)
- ✅ WCAG Violations: 0
- ✅ Test Coverage: >90%

비즈니스 지표:
- ✅ NPS: >50
- ✅ 의사결정 시간: 40% 절감
- ✅ 프로젝트 오류율: 20% 감소
- ✅ 예산 준수: <$32K
```

### Risk Management
```yaml
Week 1 리스크:
- ⚠️ DB 마이그레이션 지연 (확률 30%, 영향 HIGH)
  → 완화: SQLite fallback 준비, Day 1 착수
- ⚠️ pgvector 성능 이슈 (확률 20%, 영향 MED)
  → 완화: Pinecone 임시 사용 옵션

Week 2-3 리스크:
- ⚠️ Multi-AI 충돌 해결 복잡도 (확률 40%, 영향 MED)
  → 완화: Claude-only fallback, GPT Pro 조율 강화
- ⚠️ UI 접근성 위반 (확률 25%, 영향 LOW)
  → 완화: jest-axe 자동화, NVDA 수동 테스트

Week 4 리스크:
- ⚠️ 통합 테스트 실패 (확률 35%, 영향 HIGH)
  → 완화: Week 3 종료 전 smoke test, 롤백 계획
```

---

## 부록: PRD 개선 체크리스트

각 PRD 작성자는 다음 항목을 Week 1 착수 전까지 검토 및 업데이트하세요.

### PRD 01 (Gemini) ✅
- [ ] DB 마이그레이션 전략 → "Week 1-2 dual-write"로 수정 (section 3.1)
- [ ] API 성능 목표 → "<200ms (P95), 단순 조회 <50ms"로 명확화 (section 2.2)
- [ ] pgvector 설정 → "ivfflat lists=100" 추가 (section 3.2)
- [ ] Circuit Breaker 파라미터 → "5회 실패, 60초 복구" 명시 (section 6.2)
- [ ] Next.js 통합 → docker-compose.yml에 frontend 서비스 추가 (section 6.1)

### PRD 02 (GPT Pro) ✅
- [ ] GPT Pro 역할 재정의 → "조율자(Meta-AI) 전용" (section 2.1)
- [ ] 성공 지표 측정 방법 → SQL 쿼리 예시 추가 (section 9)
- [ ] AI 모델 선택 decision tree → Python 코드 추가 (section 5.2)
- [ ] 충돌 해결 알고리즘 → Cosine similarity + Weighted voting (section 5.3)
- [ ] Phase 전환 트리거 → "사용자 체크박스 클릭 시" 명시 (section 5.1)

### PRD 03 (Magic) ✅
- [ ] API 인터페이스 → `docs/api_spec.yaml` 작성 (section 4.3)
- [ ] WebSocket 이벤트 → task_updated, cli_activity 스키마 정의 (section 2.2)
- [ ] Progressive Enhancement → Week별 40%, 70%, 100% 상세화 (section 8)
- [ ] 에러 처리 → ErrorBoundary + WebSocket 재연결 로직 (section 5.3)
- [ ] Next.js + FastAPI 통합 → Vercel proxy 설정 예시 (section 4.1)

### PRD 04 (Grok) ✅
- [ ] RPN 계산 근거 → 팀 수준, 과거 실패율 데이터 명시 (section 2)
- [ ] RPN 목표 통일 → "평균 <80" 추가 (section 7)
- [ ] 완화 전략 실행 계획 → Week별 작업 시간 추정 (section 6)
- [ ] 리스크 모니터링 → Grafana 대시보드 + Slack 알림 (section 7)
- [ ] Post-Mortem 템플릿 → incident_log 테이블 스키마 (section 8)

### PRD 05 (Claude) ✅
- [ ] 크리티컬 패스 → PERT 차트 추가 (section 2.2)
- [ ] 측정 가능성 → 5개 KPI SQL 쿼리 예시 (section 7.1)
- [ ] 외부 의존성 → Multi-provider fallback 상세화 (section 5.1)
- [ ] 리스크 레지스터 → 주간 리뷰 프로세스 (section 4.2)
- [ ] 변경 관리 → PRD 변경 승인 절차 (section 2.3)

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-11-20
**다음 리뷰**: Week 1 종료 시 (2025-11-26)
**승인 필요**: Tech Lead, Product Owner, 각 PRD 담당자
