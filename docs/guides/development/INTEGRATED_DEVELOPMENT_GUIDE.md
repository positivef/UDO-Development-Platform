# UDO v3.0 통합 개발 가이드 (Integrated Development Guide)

> **생성일**: 2025-11-28
> **통합 분석**: 체계적 워크플로우 + 안티그래비티 계획 + 4개 전문 에이전트 분석
> **전략**: 하이브리드 접근 (인프라 견고성 + UX 우선순위)
> **목표**: 4주 내 62% → 85% 완성 + 프로덕션 준비

---

## 🎯 Executive Summary

### 핵심 통찰

**"The Missing Link"** (안티그래비티) + **"Engineering Discipline"** (체계적 워크플로우) = **"Production-Ready System with Real-World Value"**

### 통합된 접근 방식

| 측면 | 체계적 워크플로우 | 안티그래비티 계획 | **통합 전략** |
|-----|------------------|------------------|--------------|
| **시작점** | Infrastructure-first (PostgreSQL, Monitoring) | UX-first (API-UI Bridge) | **Hybrid**: Minimal DB + API Bridge (Day 1-2) |
| **우선순위** | 기술 KPI (P95 < 200ms, 커버리지 80%) | 사용자 시나리오 완성 | **Both**: 기술 견고성 + 사용자 경험 |
| **AI 통합** | Week 3 Optional (Optimistic Path) | Phase 3 Core Feature | **Week 2 Core + Week 3 Enhancement** |
| **자동화** | CI/CD, 모니터링, 백업 | Time Tracking → Uncertainty 자동 업데이트 | **Full Automation Loop** |
| **초보자 배려** | Docker, k6, Prometheus 필요 | One-Click Start, 친절한 에러 메시지 | **Setup Scripts + Visual Feedback** |

### 4주 통합 로드맵

```
Week 1: Foundation + Immediate Value
├─ Day 1-2: One-Click Start + API-UI Bridge + Minimal DB
├─ Day 3: Monitoring Stack
├─ Day 4: Notification + CI/CD
└─ Day 5: Checkpoint (사용자가 실제 데이터 확인 가능)

Week 2: Core Features + Automation
├─ Sprint 3: Uncertainty System + Time Tracking Automation
├─ Sprint 4: Multi-Project UI + AI Orchestration
└─ Goal: 자동화 루프 완성 (작업 지연 → 불확실성 자동 증가 → 알림)

Week 3: Enhancement + AI Solutions
├─ Mitigation Strategy Generator (LLM 기반)
├─ Mitigation Panel UI (One-Click Apply)
└─ Adaptive Path (속도에 따라 AI Model Switching)

Week 4: Stabilization + Production
├─ Load Testing (1000 VUs) + Security Hardening
├─ Backup/Recovery + Documentation
└─ Handoff (User Guide, Admin Guide, API Reference)
```

---

## 📋 역할별 책임과 우선순위

### 🔧 Backend Developer

**핵심 책임**: API 개발, 데이터베이스, AI 오케스트레이션, 성능 최적화

#### Week 1 우선순위 (24시간)

**Day 1 (Monday)** - 8시간
```yaml
오전 (4시간):
  - mypy_fixes:
      파일: [src/unified_development_orchestrator_v2.py, backend/app/services/quality_service.py]
      목표: 7개 타입 오류 → 0개
      검증: "mypy --strict src/ backend/"

  - minimal_postgresql:
      명령: "docker-compose up -d db"
      설정: "기본 설정만, pgAdmin 나중에"
      검증: "psql -h localhost -U udo_user -d udo_dev"

오후 (4시간):
  - alembic_migration:
      명령: "alembic upgrade head"
      데이터: "기존 SQLite 데이터 마이그레이션"
      검증: "SELECT COUNT(*) FROM projects;"

  - dual_write_setup:
      파일: backend/app/db/dual_write_manager.py
      로직: "PostgreSQL (primary) + SQLite (shadow)"
      검증: "양쪽 DB에 동일 데이터 존재"
```

**Day 2 (Tuesday)** - 8시간
```yaml
오전 (4시간):
  - uncertainty_api:
      파일: backend/app/routers/uncertainty.py
      엔드포인트: "GET /api/uncertainty/status"
      응답:
        uncertainty_vector: [0.3, 0.5, 0.2, 0.4, 0.1]  # 5D vector
        quantum_state: "PROBABILISTIC"  # 🟡
        confidence: 0.72
        mitigation_suggestions: []
      시간: 3시간

  - friendly_errors:
      파일: backend/app/core/error_formatter.py
      로직:
        - DatabaseError → "데이터베이스 연결에 실패했습니다. 잠시 후 다시 시도해주세요."
        - ValidationError → "입력값을 확인해주세요: {field}"
        - AIAPIError → "AI 서비스가 일시적으로 응답하지 않습니다."
      시간: 1시간

오후 (4시간):
  - uncertainty_calculation:
      파일: src/uncertainty_map_v3.py
      검증: "5차원 벡터 계산 로직 테스트"
      테스트: "pytest tests/test_uncertainty_integration.py -v"
      시간: 4시간
```

**Day 3 (Wednesday)** - 8시간
```yaml
전체 (8시간):
  - prometheus_setup:
      파일: backend/app/monitoring.py
      메트릭:
        - api_latency_seconds (histogram)
        - uncertainty_updates_total (counter)
        - ai_api_calls_total (counter, by model)
      검증: "http://localhost:9090/metrics"
      시간: 4시간

  - celery_setup:
      명령: "celery -A backend.app.background_tasks worker"
      작업:
        - AI orchestration (비동기)
        - 대용량 데이터 처리
      검증: "Celery worker 3개 실행 중"
      시간: 4시간
```

**Day 4 (Thursday)** - 8시간
```yaml
오전 (4시간):
  - notification_service:
      파일: backend/app/services/notification_service.py
      채널:
        - email: SendGrid API
        - slack: Webhook URL
      트리거:
        - uncertainty_state >= QUANTUM (🟠)
        - budget > $800/day (80% 임계값)
        - task_overrun > 20%
      rate_limit: "동일 카테고리 15분당 1회"
      시간: 4시간

오후 (4시간):
  - test_coverage:
      현재: 68%
      목표: 80%
      추가:
        - backend/tests/test_uncertainty_api.py
        - backend/tests/test_notification_service.py
        - backend/tests/test_dual_write.py
      검증: "pytest --cov=backend --cov-report=html"
      시간: 4시간
```

#### Week 2 우선순위 (32시간)

**Sprint 3 (Mon-Wed)** - 18시간
```yaml
bayesian_confidence:
  파일: src/adaptive_bayesian_uncertainty.py
  기능:
    - RLHF 피드백 통합
    - 불확실성 학습 (초기 65% → 목표 45%)
    - Confidence score 계산
  시간: 10시간

time_tracking_automation:
  파일: backend/app/services/time_tracking_service.py
  로직: |
    async def on_task_complete(task_id: str):
        task = await get_task(task_id)
        if task.actual_time > task.estimate * 1.2:
            # 20% 초과 시 불확실성 증가
            await uncertainty_service.update(
                technical_risk=+0.1,
                reason=f"Task {task.name} overrun by {overrun_pct}%"
            )
            # WebSocket 브로드캐스트
            await websocket_manager.broadcast({
                "event": "task_overrun",
                "task": task.name,
                "uncertainty_delta": +0.1
            })
  시간: 6시간

websocket_realtime:
  파일: backend/app/routers/websocket_handler.py
  이벤트:
    - uncertainty_update
    - phase_transition
    - mitigation_triggered
    - task_overrun
  시간: 2시간
```

**Sprint 4 (Thu-Fri)** - 14시간
```yaml
ai_orchestration_core:
  파일: src/three_ai_collaboration_bridge.py
  기능:
    - Claude: 분석 및 전략
    - Codex: 코드 리팩토링
    - Gemini: 보안 검토
  fallback:
    - PRIMARY: 3-AI orchestration
    - DEGRADED: Claude only + cache
    - EMERGENCY: Rule-based heuristics
  시간: 10시간

notification_channels:
  이메일: "SendGrid 템플릿 구현"
  슬랙: "Rich message formatting"
  테스트: "모든 트리거 시나리오"
  시간: 4시간
```

#### Week 3-4: 성능 최적화 + 보안 (40시간)

**Week 3** - 24시간
```yaml
mitigation_generator:
  파일: src/uncertainty_map_v3.py (확장)
  로직:
    - DETERMINISTIC: Rule-based (캐싱, 인덱싱)
    - QUANTUM/CHAOTIC: LLM-based (Claude 프롬프팅)
  ROI_계산: "예상 효과 vs 구현 비용"
  시간: 10시간

ai_model_switching:
  조건: "velocity >= 1.0x"
  라우팅:
    - 성능 우선: Codex
    - 품질 우선: Claude
    - 보안 우선: Gemini
  메트릭: "응답 시간, 정확도, 비용"
  시간: 12시간

redis_caching:
  전략:
    - Uncertainty predictions: TTL 300s (5분)
    - AI responses: TTL 3600s (1시간, content-hash 기반)
    - Quality metrics: TTL 1800s (30분)
  무효화: "On project update, on manual trigger"
  시간: 2시간
```

**Week 4** - 16시간
```yaml
security_hardening:
  항목:
    - SQL Injection: Parameterized queries 검증
    - XSS: Output encoding
    - CSRF: Token 검증
    - Rate Limiting: "100 req/min per IP"
  도구: "Snyk, Bandit, Safety"
  시간: 6시간

load_testing:
  시나리오:
    - Baseline: 100 VUs, 1분
    - Stress: 1000 VUs, 5분
    - Endurance: 500 VUs, 30분
  목표: "P95 < 200ms, error rate < 2%"
  도구: "k6"
  시간: 6시간

backup_recovery:
  백업: "PostgreSQL 자동 백업 (매일 2am)"
  복구: "RTO < 1시간, RPO < 4시간"
  테스트: "복구 시나리오 검증"
  시간: 4시간
```

---

### 🎨 Frontend Developer

**핵심 책임**: UI/UX, 실시간 업데이트, 사용자 시나리오 완성

#### Week 1 우선순위 (16시간)

**Day 1 (Monday)** - 4시간
```yaml
one_click_start:
  파일: package.json (web-dashboard)
  스크립트: |
    "dev:full": "concurrently \"cd ../backend && .venv/Scripts/python.exe -m uvicorn main:app --reload\" \"npm run dev\""
  테스트: "npm run dev:full - 한 번에 Backend + Frontend 시작"
  시간: 2시간

scripts_refinement:
  파일: scripts/dev-start.sh (신규)
  내용: |
    #!/bin/bash
    # OS 감지
    if [[ "$OSTYPE" == "win32" || "$OSTYPE" == "msys" ]]; then
        .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
    # Backend + Frontend 동시 시작
    concurrently "cd backend && uvicorn main:app --reload" "cd web-dashboard && npm run dev"
  시간: 2시간
```

**Day 2 (Tuesday)** - 8시간
```yaml
api_integration:
  파일: web-dashboard/app/page.tsx
  코드: |
    "use client"
    import { useQuery } from '@tanstack/react-query'

    export default function Dashboard() {
      const { data, isLoading, error } = useQuery({
        queryKey: ['uncertainty'],
        queryFn: async () => {
          const res = await fetch('http://localhost:8000/api/uncertainty/status')
          if (!res.ok) throw new Error('Failed to fetch')
          return res.json()
        },
        refetchInterval: 5000  // 5초마다 자동 새로고침
      })

      if (isLoading) return <UncertaintyMapSkeleton />
      if (error) return <ErrorFallback error={error} />

      return <UncertaintyMap data={data} />
    }
  시간: 4시간

connection_status:
  파일: web-dashboard/components/ConnectionStatus.tsx
  기능:
    - 로딩: Skeleton UI (shimmer effect)
    - 에러: "데이터를 불러올 수 없습니다. [재시도] 버튼"
    - 빈 상태: "아직 데이터가 없습니다. 첫 작업을 시작해보세요!"
  시간: 3시간

toast_notifications:
  파일: web-dashboard/components/ToastNotifications.tsx
  라이브러리: "react-hot-toast"
  이벤트:
    - uncertainty_spike: "⚠️ 불확실성이 증가했습니다!"
    - task_overrun: "⏱️ 작업이 예상보다 지연되고 있습니다."
    - budget_warning: "💰 AI 비용이 임계값에 도달했습니다."
  시간: 1시간
```

#### Week 2 우선순위 (24시간)

**Sprint 3 (Mon-Wed)** - 16시간
```yaml
uncertainty_visualization:
  파일: web-dashboard/components/dashboard/uncertainty-map.tsx (개선)
  차트:
    - 5D Radar Chart (Recharts)
    - 축: [기술 위험, 일정 위험, 예산 위험, 품질 위험, 팀 위험]
    - 색상: 불확실성 상태별 (🟢🟡🟠🔴⚫)
  시간: 6시간

rlhf_feedback_widget:
  파일: web-dashboard/components/FeedbackWidget.tsx
  UI:
    - 👍/👎 버튼
    - 상세 의견 입력 (optional)
    - "피드백이 AI 학습에 도움이 됩니다" 메시지
  API: "POST /api/uncertainty/feedback"
  시간: 4시간

websocket_integration:
  파일: web-dashboard/lib/websocket.ts
  코드: |
    import { io } from 'socket.io-client'

    const socket = io('http://localhost:8000')

    socket.on('uncertainty_update', (data) => {
      // Zustand store 업데이트
      useUncertaintyStore.getState().setUncertainty(data)
      // Toast 알림
      toast.info(`불확실성 업데이트: ${data.quantum_state}`)
    })
  자동_재연결: "connection error 시 5초 후 재시도"
  시간: 6시간
```

**Sprint 4 (Thu-Fri)** - 8시간
```yaml
project_selector_enhancement:
  파일: web-dashboard/components/dashboard/project-selector.tsx
  기능:
    - 다중 프로젝트 리스트
    - 프로젝트별 상태 아이콘 (🟢🟡🟠)
    - 즐겨찾기 (localStorage)
    - 전환 시 세션 격리
  시간: 6시간

multi_project_testing:
  시나리오:
    1. 프로젝트 A 작업 중
    2. 프로젝트 B로 전환
    3. 데이터 격리 확인
    4. 프로젝트 A로 복귀
    5. 이전 상태 복원 확인
  도구: "Playwright E2E 테스트"
  시간: 2시간
```

#### Week 3 우선순위 (16시간)

```yaml
mitigation_panel:
  파일: web-dashboard/components/dashboard/mitigation-panel.tsx
  레이아웃: |
    ┌─────────────────────────────────────────┐
    │ 🛡️ 제안된 완화 전략                       │
    ├─────────────────────────────────────────┤
    │ ● Redis 캐싱 레이어 도입                  │
    │   예상 효과: 기술 위험 -20%               │
    │   구현 시간: 4시간                        │
    │   ROI: 5배                               │
    │   [Claude 제안] [적용하기] [무시하기]      │
    ├─────────────────────────────────────────┤
    │ ● 테스트 커버리지 80% 달성                │
    │   예상 효과: 품질 위험 -30%               │
    │   구현 시간: 8시간                        │
    │   [Codex 제안] [적용하기] [무시하기]       │
    └─────────────────────────────────────────┘
  시간: 6시간

ai_persona_badges:
  파일: web-dashboard/components/AgentBadge.tsx
  디자인:
    - 🔮 Prophet (Uncertainty Map)
    - 🤖 Claude (전략 및 분석)
    - 🔧 Codex (코드 리팩토링)
    - 🛡️ Gemini (보안 검토)
  위치: "조언/제안 텍스트 앞에 표시"
  시간: 2시간

state_timeline:
  파일: web-dashboard/components/StateTimeline.tsx
  기능:
    - 불확실성 상태 변화 타임라인
    - 🟢 → 🟡 → 🟠 전환 시각화
    - 각 전환 시점의 트리거 표시
  라이브러리: "Recharts LineChart"
  시간: 4시간

vector_table:
  파일: web-dashboard/components/VectorTable.tsx
  표시:
    | 차원 | 현재값 | 추세 | 트리거 |
    |------|--------|------|--------|
    | 기술 위험 | 0.45 | ⬆️ | 작업 지연 |
    | 일정 위험 | 0.30 | ➡️ | - |
    | 예산 위험 | 0.60 | ⬆️ | AI 비용 증가 |
  시간: 4시간
```

---

### ⚙️ DevOps Engineer

**핵심 책임**: 인프라 자동화, CI/CD, 모니터링, 배포

#### Week 1 우선순위 (20시간)

**Day 1** - 4시간
```yaml
docker_compose_refinement:
  파일: docker-compose.yml
  서비스:
    - db: PostgreSQL 15 + pgvector
    - redis: Redis 7 (캐시 + 큐)
    - api: FastAPI (개발용, 나중에 제거)
    - worker: Celery workers (3개)
  네트워크: "udo-network (bridge)"
  볼륨: "db-data, redis-data"
  시간: 2시간

cross_platform_scripts:
  파일: scripts/dev-start.sh, scripts/dev-start.ps1
  테스트:
    - Windows: PowerShell
    - Mac: zsh
    - Linux: bash
  기능: "OS 자동 감지, 환경 변수 설정, 서비스 시작"
  시간: 2시간
```

**Day 3** - 8시간
```yaml
prometheus_grafana:
  prometheus:
    파일: config/prometheus.yml
    설정: |
      scrape_configs:
        - job_name: 'fastapi'
          scrape_interval: 15s
          static_configs:
            - targets: ['localhost:8000']

  grafana:
    대시보드:
      - API Performance (latency, QPS, error rate)
      - Uncertainty Metrics (state distribution, updates/sec)
      - AI Orchestration (calls, costs, latency)
      - Database (connections, query time, cache hit rate)
    알람:
      - P95 > 200ms (warning)
      - Error rate > 2% (critical)
      - Budget > $800/day (warning)

  시간: 8시간
```

**Day 4** - 8시간
```yaml
github_actions:
  파일: .github/workflows/ci.yml
  단계:
    1. Setup (Python 3.13, Node 20)
    2. Install dependencies (pip, npm)
    3. Lint (flake8, black, ESLint)
    4. Type check (mypy)
    5. Unit tests (pytest, coverage report)
    6. E2E tests (Playwright)
    7. Build (npm run build)
    8. Deploy (조건부, main 브랜치만)
  시간: 6시간

pre_commit_hooks:
  파일: .pre-commit-config.yaml
  훅:
    - black (Python formatting)
    - isort (import sorting)
    - flake8 (linting)
    - mypy (type checking)
    - eslint (JavaScript linting)
    - constitutional-guard (P1-P17 검증)
  설치: "pre-commit install"
  시간: 2시간
```

#### Week 2-4: 인프라 최적화 (28시간)

**Week 2** - 12시간
```yaml
celery_redis_production:
  celery:
    workers: 3
    concurrency: 4 (CPU cores)
    max_tasks_per_child: 1000
    task_acks_late: true

  redis:
    maxmemory: 2gb
    maxmemory_policy: "allkeys-lru"
    persistence: "AOF (appendonly yes)"

  모니터링:
    - Flower (Celery 모니터링 UI)
    - Redis Commander (Redis GUI)

  시간: 8시간

production_env:
  환경:
    - .env.development
    - .env.staging
    - .env.production

  변수:
    - DATABASE_URL
    - REDIS_URL
    - AI_API_KEYS (Claude, Codex, Gemini)
    - SENDGRID_API_KEY
    - SLACK_WEBHOOK_URL

  보안: "환경 변수는 절대 커밋하지 않음 (.gitignore)"
  시간: 4시간
```

**Week 4** - 16시간
```yaml
load_testing:
  파일: tests/performance/scenarios.js
  시나리오:
    baseline:
      VUs: 100
      duration: 1m
      target_p95: 200ms

    stress:
      VUs: 1000
      duration: 5m
      target_error_rate: <2%

    endurance:
      VUs: 500
      duration: 30m
      target_degradation: <10%

  보고서: "k6 run --out json=results.json scenarios.js"
  시간: 8시간

backup_recovery:
  백업:
    스크립트: scripts/backup.sh
    스케줄: "cron - 매일 2am"
    저장소: "AWS S3 / Azure Blob"
    보존: "7일 (일별), 4주 (주별), 12개월 (월별)"

  복구:
    RTO: 1시간 (Recovery Time Objective)
    RPO: 4시간 (Recovery Point Objective)
    테스트: "매월 1회 복구 드릴"

  시간: 6시간

documentation:
  admin_guide:
    내용:
      - Deployment (Docker Compose, AWS/Azure)
      - Monitoring (Prometheus, Grafana 설정)
      - Troubleshooting (일반적인 문제 및 해결)
      - Backup/Recovery (절차 및 테스트)
    형식: Markdown
    위치: docs/ADMIN_GUIDE.md

  시간: 2시간
```

---

### 🤖 AI/ML Engineer

**핵심 책임**: 불확실성 알고리즘, AI 오케스트레이션, 학습 시스템

#### Week 2 우선순위 (20시간)

**Sprint 3** - 12시간
```yaml
bayesian_update:
  파일: src/adaptive_bayesian_uncertainty.py
  알고리즘: |
    def update_uncertainty(prior, likelihood, evidence):
        # Bayes' Theorem
        posterior = (likelihood * prior) / evidence
        return posterior

    def calculate_confidence(uncertainty_vector, historical_accuracy):
        # 5D 벡터를 스칼라 신뢰도로 변환
        magnitude = np.linalg.norm(uncertainty_vector)
        confidence = 1 / (1 + magnitude) * historical_accuracy
        return confidence

  검증:
    - 단위 테스트 (pytest)
    - 시뮬레이션 (1000 iterations)
    - 수렴 확인 (불확실성 감소 추세)

  시간: 6시간

rlhf_integration:
  파일: backend/app/services/rlhf_service.py
  로직: |
    async def process_feedback(decision_id, rating, comment):
        # 1. 피드백 저장
        await db.insert_feedback(decision_id, rating, comment)

        # 2. 모델 업데이트
        if rating == 1:  # 긍정
            uncertainty = max(current - 0.1, 0.1)
        else:  # 부정
            uncertainty = min(current + 0.2, 0.9)

        # 3. 재학습 트리거 (100개 피드백마다)
        if feedback_count % 100 == 0:
            await retrain_uncertainty_model()

  목표: "불확실성 65% → 45% (30% 감소)"
  시간: 6시간
```

**Sprint 4** - 8시간
```yaml
ai_orchestration:
  파일: src/three_ai_collaboration_bridge.py
  모델:
    claude:
      용도: "전략 분석, 아키텍처 리뷰"
      모델: "claude-sonnet-4-5"
      비용: "$0.003/1K tokens"

    codex:
      용도: "코드 리팩토링, 자동 수정"
      모델: "gpt-4-turbo"
      비용: "$0.01/1K tokens"

    gemini:
      용도: "보안 검토, 취약점 분석"
      모델: "gemini-2.0-flash"
      비용: "$0.00035/1K tokens"

  라우팅:
    - 성능 우선 → Codex (빠름)
    - 품질 우선 → Claude (정확)
    - 보안 우선 → Gemini (전문)

  시간: 8시간
```

#### Week 3 우선순위 (16시간)

```yaml
mitigation_generator:
  파일: src/uncertainty_map_v3.py (확장)

  rule_based (DETERMINISTIC):
    patterns:
      - high_latency → "Add Redis caching"
      - low_coverage → "Increase test coverage to 80%"
      - high_complexity → "Refactor complex functions"
    ROI: "사전 정의된 효과 값"

  llm_based (QUANTUM/CHAOTIC):
    prompt: |
      You are an expert software architect. Given:
      - Current uncertainty vector: {vector}
      - Quantum state: {state}
      - Recent events: {events}

      Suggest 3 concrete mitigation strategies with:
      1. Action description
      2. Expected impact (% reduction)
      3. Implementation time
      4. ROI calculation

      Format: JSON

    model: "claude-sonnet-4-5"
    temperature: 0.3
    max_tokens: 1000

  시간: 10시간

cost_optimization:
  파일: backend/app/cost_controller.py
  전략:
    tier1_normal:
      budget: "$0-800/day"
      models: [claude, codex, gemini]
      cache_ttl: 3600s

    tier2_degraded:
      budget: "$800-1000/day"
      models: [claude]  # Codex, Gemini 비활성화
      cache_ttl: 7200s  # 2시간

    tier3_emergency:
      budget: ">$1000/day"
      models: []  # 모든 AI 비활성화
      fallback: "Rule-based heuristics"

  모니터링: "실시간 비용 추적, Grafana 대시보드"
  시간: 6시간
```

---

## 🚀 실행 계획 (Week-by-Week)

### Week 1: Foundation + Immediate Value

**목표**: 사용자가 실제 불확실성 데이터를 볼 수 있게 만들기

#### Day 1 체크리스트 ✅

**오전** (모든 역할 병렬 작업):
- [ ] **Backend**: mypy 7개 오류 수정 (4h)
- [ ] **Frontend**: One-Click Start 스크립트 (2h)
- [ ] **DevOps**: docker-compose.yml 정제 (2h)

**오후**:
- [ ] **Backend**: PostgreSQL 마이그레이션 + Dual-write (4h)
- [ ] **Frontend**: package.json에 dev:full 스크립트 추가 (2h)
- [ ] **DevOps**: 크로스 플랫폼 스크립트 테스트 (2h)

**검증**:
```bash
# Terminal 1
npm run dev:full  # Backend + Frontend 동시 시작

# Terminal 2
psql -h localhost -U udo_user -d udo_dev -c '\dt'  # 테이블 확인

# Terminal 3
mypy --strict src/ backend/  # 오류 0개
```

#### Day 2 체크리스트 ✅

**오전**:
- [ ] **Backend**: `GET /api/uncertainty/status` 구현 (4h)
- [ ] **Frontend**: API 통합 + Connection Status UI (4h)

**오후**:
- [ ] **Backend**: Friendly Error Formatter (1h) + 불확실성 계산 검증 (3h)
- [ ] **Frontend**: Toast Notifications (1h) + 테스트 (3h)

**검증**:
```bash
# 브라우저에서 http://localhost:3000 접속
# ✅ 불확실성 맵이 실제 데이터로 렌더링되는지 확인
# ✅ 로딩 스켈레톤이 보이는지 확인
# ✅ 에러 시 "재시도" 버튼이 나타나는지 확인
```

#### Day 3-5: Infrastructure & Checkpoint

**Day 3**: Prometheus + Grafana + Celery/Redis (8h)
**Day 4**: Notification Service + CI/CD + 테스트 커버리지 (8h)
**Day 5**: 문서화 + Week 1 검증 + Week 2 계획 조정 (8h)

**Week 1 성공 기준**:
- ✅ 사용자가 `npm run dev:full` 한 번에 전체 시스템 시작
- ✅ 브라우저에서 실시간 불확실성 데이터 확인 가능
- ✅ PostgreSQL 연결 + Dual-write 작동
- ✅ 모니터링 대시보드 (Prometheus + Grafana) 실행
- ✅ CI/CD 파이프라인 (GitHub Actions) 작동
- ✅ 테스트 커버리지 >= 80%

---

### Week 2: Core Features + Automation

**목표**: 작업 지연 → 불확실성 자동 증가 → 알림 (자동화 루프 완성)

#### Sprint 3 (Mon-Wed): Uncertainty System + Automation

**Monday**:
- [ ] **Backend**: Bayesian Confidence 시스템 (6h)
- [ ] **Frontend**: Uncertainty 5D Radar Chart (6h)
- [ ] **AI/ML**: Bayesian Update 알고리즘 (6h)

**Tuesday**:
- [ ] **Backend**: Time Tracking → Uncertainty 자동 업데이트 (6h)
- [ ] **Frontend**: RLHF Feedback Widget (4h)
- [ ] **Frontend**: WebSocket 통합 (6h)

**Wednesday**:
- [ ] **Backend**: WebSocket 실시간 브로드캐스트 (2h)
- [ ] **Frontend**: 실시간 업데이트 테스트 (4h)
- [ ] **통합 테스트**: 전체 자동화 루프 검증 (4h)

**시나리오 테스트**:
```
1. 작업 시작 (estimate: 4시간)
2. 실제 6시간 소요 (50% 초과)
3. ✅ 불확실성 자동 +0.1 증가
4. ✅ WebSocket으로 프론트엔드 업데이트
5. ✅ Toast 알림: "⏱️ 작업 지연으로 불확실성 증가"
6. ✅ 이메일/슬랙 알림 (threshold 초과 시)
```

#### Sprint 4 (Thu-Fri): Multi-Project + AI Orchestration

**Thursday**:
- [ ] **Backend**: AI Orchestration Core (10h)
- [ ] **Frontend**: Project Selector 개선 (6h)
- [ ] **DevOps**: Celery/Redis Production 설정 (8h)

**Friday**:
- [ ] **Backend**: Notification Channels (Email, Slack) (4h)
- [ ] **Frontend**: Multi-Project E2E 테스트 (2h)
- [ ] **체크포인트**: Week 2 검증 + Week 3 경로 선택 (4h)

**Week 2 성공 기준**:
- ✅ 자동화 루프 완성 (작업 지연 → 불확실성 증가 → 알림)
- ✅ 3-AI Orchestration 작동 (Claude, Codex, Gemini)
- ✅ Multi-Project UI 전환 기능
- ✅ 실시간 알림 (Email + Slack)
- ✅ 불확실성 감소 >= 20% (RLHF 피드백 효과)

---

### Week 3: Enhancement + AI Solutions

**목표**: AI 기반 완화 전략 + One-Click 적용

#### Adaptive Path Selection (Friday 5pm 결정)

**측정**:
```yaml
velocity_calculation:
  week1_actual: ?시간
  week1_planned: 40시간
  week1_velocity: actual / planned

  week2_actual: ?시간
  week2_planned: 32시간
  week2_velocity: actual / planned

  cumulative_velocity: (week1_velocity + week2_velocity) / 2
```

**경로 선택**:
```yaml
IF cumulative_velocity >= 1.2x:
  path: Optimistic
  tasks:
    - AI Model Switching (12h)
    - Vector Search (8h)
    - Advanced Analytics (8h)
  total: 40h

ELSIF cumulative_velocity >= 0.8x:
  path: Realistic
  tasks:
    - Mitigation Generator (10h)
    - Mitigation Panel UI (6h)
    - Bug Fixes (10h)
    - UI Polish (4h)
  total: 30h

ELSE:
  path: Pessimistic
  tasks:
    - P0 Bugs Only (10h)
    - Basic Mitigation (8h)
    - Minimal Docs (2h)
  total: 20h
```

#### 공통 작업 (All Paths)

**Monday-Tuesday**:
- [ ] **AI/ML**: Mitigation Strategy Generator (LLM 기반) (10h)
- [ ] **Frontend**: Mitigation Panel UI (6h)

**Wednesday**: Decision Checkpoint (2pm)
- [ ] 진행률 측정
- [ ] 경로 최종 확정

**Thursday-Friday**: 선택된 경로 작업
- [ ] Optimistic: AI Model Switching
- [ ] Realistic: Bug Fixes + UI Polish
- [ ] Pessimistic: 기술부채 해소

**Week 3 성공 기준**:
- ✅ Mitigation Panel 작동 (제안 표시 + [적용] 버튼)
- ✅ AI Persona 구분 (Prophet, Claude, Codex, Gemini)
- ✅ 선택 경로 작업 >= 90% 완료
- ✅ P0 버그 0개

---

### Week 4: Stabilization + Production

**목표**: 프로덕션 준비 완료 (보안, 성능, 문서화)

#### Day 16-18 (Mon-Wed): Hardening

**Monday**:
- [ ] **DevOps**: Load Testing (8h)
  - Baseline: 100 VUs, 1분
  - Stress: 1000 VUs, 5분
  - Endurance: 500 VUs, 30분
  - 목표: P95 < 200ms, Error < 2%

**Tuesday**:
- [ ] **Backend**: Security Hardening (6h)
  - SQL Injection 방어
  - XSS 방어
  - CSRF 토큰
  - Rate Limiting
- [ ] **DevOps**: Backup/Recovery (4h)

**Wednesday**:
- [ ] **전체**: Performance Tuning (8h)
  - 병목 지점 최적화
  - 캐싱 전략 개선
  - 쿼리 최적화

#### Day 19 (Thursday): Documentation

**모든 역할 협업**:
- [ ] User Guide (Frontend 관점) - 4h
- [ ] Admin Guide (DevOps 관점) - 4h
- [ ] API Reference (Backend 관점) - 2h
- [ ] Technical Documentation (AI/ML 관점) - 2h

#### Day 20 (Friday): Handoff

**오전**:
- [ ] 최종 회귀 테스트 (4h)
- [ ] 모든 체크리스트 검증 (2h)

**오후**:
- [ ] Handoff 미팅 (2h)
  - 프로젝트 데모
  - 문서 전달
  - Q&A
- [ ] Final Report 작성 (2h)

**Week 4 성공 기준**:
- ✅ Load Test 통과 (1000 VUs)
- ✅ Security Scan 통과 (0 Critical/High vulnerabilities)
- ✅ Backup/Recovery 테스트 통과 (RTO < 1h, RPO < 4h)
- ✅ 문서화 100% 완료
- ✅ Handoff 미팅 완료
- ✅ 불확실성 감소 >= 30% (초기 65% → 최종 45%)

---

## 📊 성공 지표 (KPIs) - 통합

### 기술 지표 (Technical KPIs)

| 지표 | Week 1 | Week 2 | Week 3 | Week 4 | 목표 |
|-----|--------|--------|--------|--------|------|
| **완성도** | 70% | 77% | 82% | 85% | 85% |
| **API P95 레이턴시** | 187ms | 195ms | 180ms | 175ms | <200ms |
| **테스트 커버리지** | 82% | 85% | 88% | 90% | >=80% |
| **불확실성 감소** | 10% | 20% | 28% | 32% | >=30% |
| **P0 버그** | 0 | 0 | 0 | 0 | 0 |

### 사용자 경험 지표 (UX KPIs)

| 지표 | 측정 방법 | 목표 | Week 4 |
|-----|-----------|------|--------|
| **초보자 시작 시간** | One-Click Start 실행 → 데이터 확인 | <5분 | ? |
| **시나리오 완성률** | 불확실성 감지 → AI 제안 → 적용 | 100% | ? |
| **에러 메시지 이해도** | 사용자 피드백 (1-5점) | >=4.0 | ? |
| **알림 유용성** | 알림 후 액션 수행률 | >=70% | ? |

### 비즈니스 지표 (Business KPIs)

| 지표 | 측정 방법 | 목표 |
|-----|-----------|------|
| **팀 만족도** | 주간 설문 (1-10점) | >=7.0 |
| **개발 속도** | Velocity (actual / planned) | >=0.8x |
| **AI 비용** | 일일 AI API 사용량 | <$1000/day |
| **시스템 가용성** | Uptime monitoring | >=99.9% |

---

## 🎯 통합 우선순위 매트릭스

### P0 (Critical) - Week 1-2 필수

| 작업 | 역할 | 시간 | Week | 의존성 |
|-----|------|------|------|--------|
| One-Click Start 스크립트 | Frontend + DevOps | 4h | 1 | - |
| PostgreSQL 마이그레이션 | Backend | 8h | 1 | - |
| API-UI Bridge (Uncertainty) | Backend + Frontend | 8h | 1 | PostgreSQL |
| Connection Status UI | Frontend | 3h | 1 | API |
| Time Tracking 자동화 | Backend | 6h | 2 | API |
| Notification Service | Backend | 6h | 2 | - |
| Mitigation Panel | Frontend | 6h | 3 | AI Orchestration |

### P1 (Important) - Week 2-3 권장

| 작업 | 역할 | 시간 | Week | 의존성 |
|-----|------|------|------|--------|
| Prometheus + Grafana | DevOps | 8h | 1 | - |
| CI/CD Pipeline | DevOps | 6h | 1 | - |
| RLHF Feedback | AI/ML + Frontend | 10h | 2 | API |
| AI Orchestration | Backend + AI/ML | 18h | 2 | - |
| Multi-Project UI | Frontend | 8h | 2 | - |
| AI Persona Badges | Frontend | 2h | 3 | - |

### P2 (Nice-to-Have) - Week 3-4 선택

| 작업 | 역할 | 시간 | Week | 조건 |
|-----|------|------|------|------|
| AI Model Switching | AI/ML | 12h | 3 | velocity >= 1.2x |
| Vector Search | Backend | 8h | 3 | velocity >= 1.2x |
| Advanced Analytics | Frontend | 8h | 3 | velocity >= 1.2x |
| State Timeline | Frontend | 4h | 3 | velocity >= 1.0x |

---

## 🚨 위험 관리 - 통합

### 새로운 위험 (통합 과정에서 발견)

**RISK-005: One-Click Start 크로스 플랫폼 실패** (RPN 96)
```yaml
확률: MEDIUM (40%)
영향: HIGH (초보자 온보딩 블로킹)
완화:
  - Day 1에 Windows, Mac, Linux 모두 테스트
  - concurrently, cross-env 사용 (플랫폼 독립적)
  - 실패 시 수동 가이드 제공
복구: 1시간 (스크립트 수정)
```

**RISK-006: Notification Spam** (RPN 72)
```yaml
확률: HIGH (60%)
영향: MEDIUM (사용자 annoying)
완화:
  - Rate Limiting: 동일 카테고리 15분당 1회
  - 알림 설정 UI (사용자가 on/off)
  - Smart Grouping (유사 알림 묶음)
복구: 설정 변경 (즉시)
```

**RISK-007: AI Orchestration Week 2 지연** (RPN 120)
```yaml
확률: MEDIUM (50%)
영향: HIGH (핵심 기능 누락)
완화:
  - Fallback: Rule-based mitigation (Week 2)
  - LLM-based mitigation (Week 3로 이동)
  - 단순화: Claude만 사용, Codex/Gemini는 Week 3
복구: 2일 (Scope 축소)
```

### 기존 위험 업데이트

**RISK-001: Database 마이그레이션 실패** (RPN 90 → 60)
- **이유**: Dual-write 패턴으로 위험 감소
- **새 완화**: 마이그레이션 전 스테이징 테스트

**RISK-004: 팀 속도 변동성** (RPN 135 → 100)
- **이유**: Adaptive Path로 유연성 확보
- **새 완화**: Week 3 경로 선택 (Optimistic/Realistic/Pessimistic)

---

## 📚 참고 문서

### 생성된 문서 (모두 `docs/` 폴더)

1. **IMPLEMENTATION_WORKFLOW_SYSTEMATIC.md** - 원본 체계적 워크플로우 (1,200줄)
2. **BACKEND_ARCHITECTURE_ANALYSIS.yaml** - Backend 아키텍처 분석 (500줄)
3. **FRONTEND_ARCHITECTURE_ANALYSIS.yaml** - Frontend 아키텍처 분석 (400줄)
4. **PERFORMANCE_OPTIMIZATION_STRATEGY.yaml** - 성능 최적화 전략 (750줄)
5. **INTEGRATED_DEVELOPMENT_GUIDE.md** - 이 문서 (통합 가이드)

### 기존 PRD 및 계획

1. **PRD_UNIFIED_ENHANCED.md** - 통합 강화 PRD (518줄)
2. **DEVELOPMENT_PLAN_AND_REVIEW.md** - 안티그래비티 계획 (75줄)

---

## ✅ 최종 체크리스트

### Week 1 완료 기준
- [ ] `npm run dev:full` 한 번에 전체 시스템 시작
- [ ] 브라우저에서 실시간 불확실성 데이터 확인
- [ ] PostgreSQL 연결 + Dual-write 작동
- [ ] Prometheus + Grafana 대시보드 작동
- [ ] CI/CD 파이프라인 작동
- [ ] 테스트 커버리지 >= 80%
- [ ] mypy 오류 0개

### Week 2 완료 기준
- [ ] 작업 지연 → 불확실성 자동 증가
- [ ] WebSocket 실시간 업데이트
- [ ] 이메일 + 슬랙 알림 작동
- [ ] 3-AI Orchestration 작동
- [ ] Multi-Project 전환 기능
- [ ] RLHF 피드백 루프 작동
- [ ] 불확실성 감소 >= 20%

### Week 3 완료 기준
- [ ] Mitigation Panel UI 작동
- [ ] AI Persona 구분 표시
- [ ] One-Click Apply 기능
- [ ] 선택 경로 작업 >= 90% 완료
- [ ] P0 버그 0개
- [ ] 불확실성 감소 >= 28%

### Week 4 완료 기준
- [ ] Load Test 통과 (1000 VUs, P95 < 200ms)
- [ ] Security Scan 통과 (0 Critical/High)
- [ ] Backup/Recovery 테스트 통과
- [ ] 문서화 100% 완료 (User + Admin + API)
- [ ] Handoff 미팅 완료
- [ ] 불확실성 감소 >= 30%

---

## 🎉 성공 시나리오

**"화요일 아침, 리드 개발자가 불확실성 지도를 확인하고 리스크를 예방한다"**

### Before (현재 상태)
```
1. 개발자가 "감"으로 위험 예측
2. 문제 발견 시 이미 늦음
3. 해결책을 찾기 위해 회의 소집
4. 수동으로 완화 전략 실행
```

### After (Week 4 완료 후)
```
1. 월요일 밤: 작업 3개가 예상보다 지연
   ✅ 시스템이 자동으로 기술 위험 +0.3 증가 감지
   ✅ 불확실성 상태 🟡 PROBABILISTIC → 🟠 QUANTUM 전환

2. 화요일 아침 9am: 리드 개발자 출근
   ✅ 슬랙 알림: "⚠️ 기술 위험이 임계값을 초과했습니다"
   ✅ 이메일: "프로젝트 X의 불확실성이 QUANTUM 상태입니다"

3. 대시보드 확인 (3분)
   ✅ 5D Radar Chart: 기술 위험 0.65, 일정 위험 0.40
   ✅ State Timeline: 지난 24시간 동안 🟡 → 🟠 전환
   ✅ Mitigation Panel:
      - 🤖 Claude 제안: "Redis 캐싱 도입 (예상 효과: -20%, 시간: 4h, ROI: 5배)"
      - 🔧 Codex 제안: "복잡도 높은 함수 리팩토링 (예상 효과: -15%, 시간: 6h)"

4. One-Click 적용 (1분)
   ✅ [적용하기] 버튼 클릭
   ✅ Claude가 자동으로 Redis 캐싱 레이어 구현 제안
   ✅ Codex가 Pull Request 생성

5. 결과 확인 (30분 후)
   ✅ 성능 테스트: P95 800ms → 150ms (81% 개선)
   ✅ 불확실성 재계산: 기술 위험 0.65 → 0.45
   ✅ 상태 전환: 🟠 QUANTUM → 🟡 PROBABILISTIC
   ✅ RLHF 피드백: 👍 (시스템 학습 완료)

총 소요 시간: 34분 (vs 이전 4시간)
예방한 지연: 2일 (vs 발견 후 해결)
팀 생산성: +40%
```

---

**생성 정보**:
- **생성일**: 2025-11-28
- **통합 분석**: 4개 전문 에이전트 (Backend, Frontend, Performance, Requirements)
- **활용 도구**: Claude Skills, MCP (Obsidian, Sequential, Context7, Codex), Task (Sub-Agents)
- **전략**: 하이브리드 접근 (체계적 워크플로우 + 안티그래비티 UX)
- **목표**: 4주 내 62% → 85% 완성 + 프로덕션 준비

**마지막 업데이트**: 2025-11-28
**다음 단계**: Week 1 Day 1 시작 (One-Click Start + API-UI Bridge)
