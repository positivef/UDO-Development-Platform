# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Current Development Roadmap (2025-12-06)

> **하이브리드 접근**: 영역별 성숙도에 맞춘 목표 설정

### 📌 Claude Code 핵심 요약

```yaml
현재 상태 (실측):
  Backend: 95% ✅ → 높은 목표 적용
  Frontend: 50% ⚠️ → 점진적 개발
  AI Bridge: 30% ⚠️ → 점진적 개발
  테스트: 85% 통과 (일부 실패 수정 필요)

즉시 해야 할 일 (P0):
  1. 테스트 실패 수정 (Uncertainty predict() 파라미터)
  2. Uncertainty UI 기본 (web-dashboard/app/uncertainty/)
  3. Confidence Dashboard 기본 (web-dashboard/app/confidence/)
  4. CI Pipeline 생성 (.github/workflows/)
```

### 참고 문서

| 문서 | 위치 | 내용 |
|------|------|------|
| **RL 기반 지식 재사용** | `docs/RL_GUIDED_KNOWLEDGE_REUSE.md` | Training-free GRPO 이론 + 실무 통합 (NEW 🆕) |
| **종합 최종 로드맵 v6.0** | `docs/COMPREHENSIVE_ROADMAP_V6.md` | 3개 모델 통합 계획 ⭐ |
| **기술 인계 가이드** | `docs/HANDOFF_TO_CLAUDE.md` | **Facade 패턴 설명 및 실행 가이드** 👈 |
| **Pre-mortem 분석** | `docs/PREMORTEM_ANALYSIS_2025-12-06.md` | 위험 분석 및 단순화 근거 |
| **개발 로드맵 v6.0** | `docs/DEVELOPMENT_ROADMAP_V6.md` | 하이브리드 상세 계획 |

### 하이브리드 목표

**성숙 영역 (Backend) - 높은 목표**:
| 지표 | 현재 | 목표 |
|------|------|------|
| 테스트 통과율 | 85% | **98%** |
| API 응답 시간 | 미측정 | **<200ms** |

**신규 영역 (Frontend/AI) - 점진적 목표**:
| 지표 | MVP (2주) | Prototype | Beta | Production |
|------|-----------|-----------|------|------------|
| 예측 정확도 | 40% | 55% | 65% | 70% |
| 오류율 | 15% | 10% | 8% | 5% |
| 자동화율 | 65% | 75% | 80% | 85% |

### 현재 Stage: MVP (2주)

```yaml
MVP Task (P0):
  1. Uncertainty UI 기본 (3일)
     파일: web-dashboard/app/uncertainty/page.tsx
     
  2. Confidence Dashboard 기본 (2일)
     파일: web-dashboard/app/confidence/page.tsx
     
  3. CI Pipeline (1일)
     파일: .github/workflows/backend-test.yml

MVP 성공 기준:
  - 예측 화면 표시
  - CI 자동 실행
  - 테스트 통과율 95%+
```

### 검증 완료

- [x] 5 Whys 본질 분석 완료
- [x] 현재 상태 테스트 실행 (85% 통과)
- [x] 영역별 성숙도 분석 완료
- [x] 하이브리드 접근법 정의
- [x] 단계별 보완점 체크리스트

### 명령어 참조

```bash
# 테스트 실행
.venv\Scripts\python.exe -m pytest tests/ -v

# 백엔드 시작
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload

# 프론트엔드 시작
cd web-dashboard && npm run dev
```

---

## Project Overview

**UDO Development Platform v3.0** - An intelligent development automation platform using AI collaboration and predictive uncertainty modeling to manage the software development lifecycle.

**Core Innovation**: Phase-aware evaluation system with predictive uncertainty modeling achieving 95% AI automation through multi-model orchestration, constitutional governance, and knowledge retention.

## Architecture

### System Components

The platform consists of three primary systems:

1. **UDO v2 (Orchestrator)** - `src/unified_development_orchestrator_v2.py`
   - Phase-aware evaluation (Ideation → Design → MVP → Implementation → Testing)
   - Bayesian confidence scoring per phase
   - Decision logic (GO/GO_WITH_CHECKPOINTS/NO_GO)

2. **Uncertainty Map v3 (Predictor)** - `src/uncertainty_map_v3.py`
   - 24-hour predictive uncertainty modeling
   - Quantum state classification (5 states: Deterministic, Probabilistic, Quantum, Chaotic, Void)
   - Auto-mitigation strategy generation with ROI calculation

3. **AI Collaboration Bridge** - `src/three_ai_collaboration_bridge.py`
   - Multi-AI orchestration (Claude, Codex, Gemini)
   - MCP server integration (Context7, Sequential, Magic, Morphllm, Serena, Playwright)
   - Codex MCP integration for code analysis and refactoring

### Backend API (FastAPI)

**Location**: `backend/main.py`

**Key Routers** (`backend/app/routers/`):
- `quality_metrics_router` - Code quality analysis (Pylint, ESLint, pytest coverage)
- `constitutional_router` - AI governance enforcement (17-article constitution)
- `time_tracking_router` - ROI measurement and productivity tracking
- `version_history_router` - Code evolution tracking
- `obsidian_router` - Knowledge base synchronization
- `uncertainty_router` - Uncertainty analysis and predictions
- `websocket_handler` - Real-time updates to frontend

**Critical Services** (`backend/app/services/`):
- `quality_service.py` - Unified subprocess execution with Windows/Linux compatibility
- `project_context_service.py` - Project state management with mock service fallback
- `session_manager_v2.py` - Multi-session orchestration
- `obsidian_service.py` - Automatic knowledge syncing (<3 seconds)

### Frontend Dashboard (Next.js)

**Location**: `web-dashboard/`

**Stack**: Next.js 16.0.3, React 19.2.0, Tailwind CSS v4, Zustand, Tanstack Query, Recharts

**Key Pages**:
- `/` - Main dashboard with real-time metrics
- `/quality` - Quality metrics visualization
- `/time-tracking` - ROI and productivity dashboard
- `/ck-theory` - C-K Theory design analysis
- `/gi-formula` - GI Formula calculations

## Development Commands

### Environment Setup

**CRITICAL**: Use Windows shell (PowerShell/cmd) with Python 3.13.0 venv. WSL is currently blocked due to pip issues.

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt
pip install pytest-cov  # For coverage support

# Install frontend dependencies
cd web-dashboard
npm install
```

### Running Tests

**Python Tests**:
```bash
# Run all tests (Windows shell REQUIRED)
.venv\Scripts\python.exe -m pytest tests/ -v

# Run specific test file
.venv\Scripts\python.exe -m pytest tests/test_udo_e2e.py -v

# Run with coverage
.venv\Scripts\python.exe -m pytest tests/ --cov=src --cov-report=html

# Run backend tests
.venv\Scripts\python.exe -m pytest backend/tests/ -v

# Integration test
python tests/run_udo_phase1.py
```

**Frontend Tests**:
```bash
cd web-dashboard
npm run lint  # ESLint check
npm run build # Production build test
```

### Running Development Servers

**Backend API**:
```bash
# From repository root (Windows shell)
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# API documentation available at:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

**Frontend Dashboard**:
```bash
cd web-dashboard
npm run dev  # Starts on http://localhost:3000
```

### Code Quality

```bash
# Python linting
.venv\Scripts\python.exe -m flake8 src/ backend/

# Python formatting (check)
.venv\Scripts\python.exe -m black --check src/ backend/

# Python formatting (apply)
.venv\Scripts\python.exe -m black src/ backend/

# Frontend linting
cd web-dashboard
npm run lint
```

## Key Configuration

### Phase-Specific Confidence Thresholds
Defined in `src/unified_development_orchestrator_v2.py`:
- **Ideation**: 60% confidence required
- **Design**: 65% confidence required
- **MVP**: 65% confidence required
- **Implementation**: 70% confidence required
- **Testing**: 70% confidence required

### Uncertainty States
Defined in `src/uncertainty_map_v3.py`:
- 🟢 **DETERMINISTIC** (<10%): Fully predictable
- 🔵 **PROBABILISTIC** (10-30%): Statistical confidence
- 🟠 **QUANTUM** (30-60%): Multiple possibilities
- 🔴 **CHAOTIC** (60-90%): High uncertainty
- ⚫ **VOID** (>90%): Unknown territory

### Backend Configuration
- `backend/config/UDO_CONSTITUTION.yaml` - AI governance rules (17 articles, P1-P17)
- `backend/config/baseline_times.yaml` - Performance baselines for time tracking
- `backend/.env` - Environment variables (create from `.env.example`)

## Critical Implementation Details

### Quality Service Subprocess Execution

**Location**: `backend/app/services/quality_service.py`

All subprocess calls MUST use the shared `_run_command()` helper with `shell=False` for security. Windows shell is enabled ONLY for ESLint (npx resolution issues).

```python
# CORRECT pattern (used in quality_service.py)
output, error, exit_code = await self._run_command(
    cmd=["pylint", "path/to/file.py"],
    use_shell_on_windows=False  # Default, secure
)

# Windows exception for ESLint only
output, error, exit_code = await self._run_command(
    cmd=["npx", "eslint", "path"],
    use_shell_on_windows=True  # Required for npx on Windows
)
```

### Mock Service Pattern

Project context service uses mock fallback when database is unavailable. Mock service MUST be enabled BEFORE importing routers:

```python
# In backend/main.py (lines 38-44)
from app.services.project_context_service import enable_mock_service
enable_mock_service()  # CRITICAL: Before router imports
logger.info("✅ Mock service enabled (BEFORE router imports)")

# Then import routers
from app.routers import version_history_router, quality_metrics_router, ...
```

### Constitutional Guard Pre-commit

**Location**: `backend/app/core/constitutional_guard.py`

Enforces 17 AI governance principles (P1-P17) at commit time. Key principle:

**P1: Design Review First** - Blocks commits affecting >3 files without design doc
- Must complete 8-Risk Check before implementation
- Design doc required in `docs/[FEATURE]_DESIGN_REVIEW.md`

## Common Development Workflows

### Adding a New API Router

1. Create router file in `backend/app/routers/`
2. Define Pydantic models in `backend/app/models/`
3. Implement service logic in `backend/app/services/`
4. Import and include router in `backend/main.py`
5. Add tests in `backend/tests/`

### Adding Frontend Dashboard Page

1. Create page in `web-dashboard/app/[page-name]/page.tsx`
2. Add navigation link in `web-dashboard/components/Navigation.tsx`
3. Create reusable components in `web-dashboard/components/`
4. Add API integration using Tanstack Query
5. Use Zustand for state management if needed

### Running E2E Integration Tests

```bash
# Full UDO v3 integration test
.venv\Scripts\python.exe -m pytest tests/test_udo_v3_integration.py -v

# E2E workflow tests
.venv\Scripts\python.exe -m pytest tests/test_udo_e2e.py -v

# Collaboration bridge tests
.venv\Scripts\python.exe -m pytest tests/test_three_ai_collaboration_bridge.py -v

# Codex refactoring validation
.venv\Scripts\python.exe -m pytest tests/test_codex_refactors.py -v
```

## Project Structure

```
UDO-Development-Platform/
├── src/                           # Core Python modules
│   ├── unified_development_orchestrator_v2.py
│   ├── uncertainty_map_v3.py
│   ├── three_ai_collaboration_bridge.py
│   └── ai_collaboration_connector.py
├── backend/                       # FastAPI backend
│   ├── main.py                   # Application entry point
│   ├── app/
│   │   ├── routers/              # API route handlers
│   │   ├── services/             # Business logic
│   │   ├── models/               # Pydantic models
│   │   ├── core/                 # Security, monitoring, error handling
│   │   └── db/                   # Database models
│   ├── config/                   # YAML configuration
│   ├── tests/                    # Backend-specific tests
│   └── requirements.txt
├── web-dashboard/                 # Next.js frontend
│   ├── app/                      # Next.js 13+ app directory
│   ├── components/               # React components
│   ├── lib/                      # Utilities
│   └── package.json
├── tests/                        # Integration tests
│   ├── test_udo_e2e.py          # E2E workflows
│   ├── test_udo_v3_integration.py
│   └── run_udo_phase1.py        # Integration runner
├── docs/                         # Documentation
├── data/                         # State and learning data
├── scripts/                      # Utility scripts
├── requirements.txt              # Root Python deps
└── .venv/                        # Python virtual environment
```

## Important Context

### Current Environment
- **Python**: 3.13.0 with pip 25.3 (pyenv-win)
- **Environment**: Windows shell ONLY (WSL blocked until pip available)
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000

### Known Issues
1. **WSL Environment**: Do NOT run tests from WSL - pip is blocked. Always use Windows PowerShell/cmd.
2. **Cross-Shell Invocation**: Never call Windows venv from WSL (`UtilBindVsockAnyPort` error)

### MCP Server Integration

The platform integrates with multiple MCP servers for specialized capabilities:

- **Context7**: Official documentation lookup
- **Sequential**: Multi-step reasoning for complex analysis
- **Magic**: UI component generation from 21st.dev patterns
- **Morphllm**: Bulk code transformations
- **Serena**: Semantic understanding and session persistence
- **Playwright**: Browser automation and E2E testing
- **Codex**: Code analysis, refactoring, and quality checks
- **UDO-MCP-Server** (NEW): Real-time uncertainty analysis and risk prediction.

### 🚀 Trinity Protocol 2.0 Strategy (Multi-Agent)

We are adopting a **Multi-Agent & MCP-driven** workflow to bridge the gap between Backend and Frontend.

**Your Role (Claude Code)**:
- **The Builder**: Focus on **Frontend Integration**.
- **Task**: Connect `web-dashboard` to `UncertaintyMap` using the `/api/uncertainty` endpoints.
- **Guidance**: Use the **UDO-MCP-Server** tools (`get_uncertainty_state`, `predict_risk_impact`) to validate your architectural decisions *before* writing code.

**Antigravity's Role**:
- **The Architect**: Manages the MCP Server and backend infrastructure.
- **The Prophet**: Monitors risk via MCP and provides strategic guidance.

Check `backend/app/services/` for integration implementations.

### Documentation References
- Latest worklog: `docs/CLAUDE_WORKLOG_2025-11-20.md`
- Architecture overview: `docs/ARCHITECTURE_EXECUTIVE_SUMMARY.md`
- Integration design: `docs/INTEGRATION_ARCHITECTURE_V4.md`
- Terminal environment notes: `docs/WSL_VS_WINDOWS_ENV.md`
- Obsidian sync: `docs/OBSIDIAN_SERVICE_README.md`
- Time tracking guide: `docs/TIME_TRACKING_GUIDE.md`

---

## Kanban-UDO Integration (2025-12-05)

**Status**: Week 3 Complete ✅ - Week 4 Testing Preparation

### Quick Reference

**Master Document**: `docs/KANBAN_IMPLEMENTATION_SUMMARY.md` (Concise overview)

**Implementation Documents** (Week 3 Complete):
- `backend/app/models/kanban_archive.py` - Archive models with AI summarization
- `backend/app/services/kanban_archive_service.py` - Archive service (GPT-4o integration)
- `backend/app/routers/kanban_archive.py` - Archive API endpoints
- `backend/tests/test_kanban_archive.py` - 15/15 tests passing (100%)

**Week 4 Testing Documents** (NEW):
- `docs/WEEK4_USER_TESTING_GUIDE.md` - Comprehensive testing scenarios
- `docs/WEEK4_TESTING_CHECKLIST.md` - Quick reference checklist
- `docs/WEEK4_FEEDBACK_TEMPLATE.md` - User feedback collection template
- `docs/WEEK4_ROLLBACK_PROCEDURES.md` - 3-Tier rollback validation

**Detailed Specifications** (for future implementation):
- `docs/KANBAN_UI_COMPONENTS_DESIGN.md` (2,235 lines) - Complete React component specs
- `docs/KANBAN_DATABASE_SCHEMA_DESIGN.md` - Full PostgreSQL schema with migrations
- `docs/KANBAN_API_SPECIFICATION.md` - 25+ REST endpoints with request/response

**Strategic Analysis** (for context):
- `docs/KANBAN_INTEGRATION_STRATEGY.md` (18,000 words) - Full strategic analysis, Q1-Q8 decisions
- `docs/ARCHITECTURE_STABILITY_ANALYSIS.md` - P0 critical issues + solutions
- `docs/CONTEXT_AWARE_KANBAN_RESEARCH.md` - Benchmarking (Linear, ClickUp, Height, Plane.so)

### Q1-Q8 Decisions (MUST preserve in future sessions)

| Question | Decision | File Reference |
|----------|----------|----------------|
| Q1: Task-Phase Relationship | Task within Phase (1:N) | KANBAN_INTEGRATION_STRATEGY.md §6.1 |
| Q2: Task Creation | AI Hybrid (suggest + approve) | KANBAN_INTEGRATION_STRATEGY.md §6.2 |
| Q3: Completion Criteria | Hybrid (Quality gate + user) | KANBAN_INTEGRATION_STRATEGY.md §6.3 |
| Q4: Context Loading | Double-click auto, single popup | KANBAN_INTEGRATION_STRATEGY.md §6.4 |
| Q5: Multi-Project | 1 Primary + max 3 Related | KANBAN_INTEGRATION_STRATEGY.md §6.5 |
| Q6: Archiving | Done-End + AI → Obsidian | KANBAN_INTEGRATION_STRATEGY.md §6.6 |
| Q7: Dependencies | Hard Block + Emergency override | KANBAN_INTEGRATION_STRATEGY.md §6.7 |
| Q8: Accuracy vs Speed | Accuracy first + Adaptive | KANBAN_INTEGRATION_STRATEGY.md §6.8 |

### Implementation Roadmap (4 Weeks)

**Week 1**: Foundation + P0 Fixes
- Database schema creation + migration
- Circuit Breaker recovery (CLOSED/OPEN/HALF_OPEN)
- Cache Manager 50MB limit + LRU eviction
- Multi-project Primary selection algorithm
- DAG real benchmark (confirm <50ms for 1,000 tasks)

**Week 2**: Core Implementation
- UI components (KanbanBoard, TaskCard, Modal)
- Drag-drop + optimistic updates
- Context operations (ZIP upload/download)

**Week 3**: Advanced Features
- Dependency graph (D3.js force-directed)
- AI task suggestion + approval flow
- Archive view + AI summarization (GPT-4o)

**Week 4**: Integration + Testing
- User testing (5 sessions) - Target: 72% → 85% confidence
- Documentation + rollback validation
- Production deployment

### Future Expansion Triggers

**When to read detailed specs**:
1. **Before database migration** → Read `KANBAN_DATABASE_SCHEMA_DESIGN.md`
2. **Before API development** → Read `KANBAN_API_SPECIFICATION.md`
3. **Before UI development** → Read `KANBAN_UI_COMPONENTS_DESIGN.md`
4. **Performance optimization** → Create `KANBAN_PERFORMANCE_DETAILED.md`
5. **Security review** → Create `KANBAN_SECURITY_DETAILED.md`

**Documents to create when needed**:
- `KANBAN_PERFORMANCE_DETAILED.md` - Load testing, benchmarks, k6 scripts, Lighthouse CI
- `KANBAN_SECURITY_DETAILED.md` - STRIDE analysis, penetration testing, OWASP validation
- `KANBAN_INTEGRATION_DETAILED.md` - 14 integration points implementation guides
- `KANBAN_TESTING_STRATEGY.md` - Unit, integration, E2E, accessibility test plans

### Uncertainty Map (低信頼度エリア - 補完が必要)

**Low confidence areas requiring validation** (Week 4 user testing):
- Q5-1 (45%): Multi-project Primary selection logic (needs algorithm benchmark)
- Q6 (50%): AI summary quality (needs GPT-4o prompt optimization)
- Q7 (55%): Emergency override UX (needs user testing for friction)

**Adaptive triggers** (opinion-changing questions):
- If DAG performance <50ms fails → Switch to pagination/filtering
- If AI summary quality <80% satisfaction → Enhance prompt or switch model
- If users override dependencies >10% → Reconsider hard-block default

### Integration Points (14)

**UDO v2**: Phase-Task sync, Confidence thresholds, Execution history
**Uncertainty Map v3**: Priority automation, Predictive blocking, Mitigation tracking
**Quality Service**: Quality gates, Test coverage, Code review
**Time Tracking**: ROI calculation, Bottleneck detection, Productivity metrics
**Obsidian**: Knowledge extraction, Context notes

### Key Performance Targets

- **Database queries**: <50ms (1,000 tasks)
- **API endpoints**: p95 <500ms
- **UI initial load**: TTI <3s, FCP <1s, LCP <2.5s
- **Virtual scrolling**: 10,000 tasks without lag
- **WebSocket latency**: <50ms
- **AI suggestion**: <3s (Claude Sonnet 4.5)

### Rollback Strategy

**Tier 1**: Feature flag disable (immediate)
**Tier 2**: Git revert + redeploy (1 minute)
**Tier 3**: Database restore from backup (5 minutes)

---


## Current Status (2025-12-04) - All Issues Resolved ✅

## Refactoring Validation & Next Steps

### Priority‑ordered Improvements
1. **Backend Router Modularization** – Move all router imports to a lazy registration helper (`app/routers/__init__.py`). Reduces `main.py` clutter and eases future router additions.
2. **Central Configuration Module** – Consolidate CORS, logging, DB URL, and feature flags in `app/config.py`. Enables environment‑specific overrides.
3. **Service Container & Dependency Injection** – Provide services (e.g., `KanbanTaskService`, `TimeTrackingService`) via FastAPI `Depends`. Improves testability.
4. **Typed Pydantic Schemas Alignment** – Ensure API contracts match frontend TypeScript interfaces (`web-dashboard/lib/types`).
5. **Comprehensive Test Suite** – Add integration tests for each new Kanban router (`kanban_dependencies`, `kanban_projects`, `kanban_context`) targeting ≥85 % coverage.
6. **CI/CD Enhancements** – Pre‑commit hooks, GitHub Actions for lint, security (`bandit`), and performance benchmarks.
7. **Documentation Automation** – Generate OpenAPI spec, architecture diagrams, and update `README` with onboarding scripts.
8. **Frontend Kanban Integration** – Introduce typed API client, Zustand store for Kanban state, and lazy‑loaded UI components.
9. **Performance Benchmarking** – Validate DAG processing < 50 ms for 1 000 tasks, DB query latency < 50 ms, and API p95 < 500 ms.
10. **Uncertainty Map Gap Mitigation** – Address low‑confidence areas (Q5‑1, Q6, Q7) with targeted experiments (algorithm benchmark, AI summary quality testing, UX studies).

### Multi‑Agent & MCP‑Driven Strategy
- **Architect (Antigravity)** – Manages backend modularization, config, and service container.
- **Builder (Claude Code)** – Implements frontend Kanban components, API client, and state store.
- **Prophet (MCP‑Sequential)** – Runs risk analysis via the Uncertainty Map, flags low‑confidence decisions.
- **Reviewer (MCP‑Codex)** – Performs static code analysis, suggests refactorings, and ensures style compliance.
- **Tester (MCP‑Playwright)** – Executes end‑to‑end performance and UI tests across browsers.

### Benchmarking & Stability
- **Reference Platforms**: ClickUp, Linear, Height, Plane.so – measured for API latency, DB query patterns, and UI load times.
- **Target Metrics**: DB < 50 ms, API p95 < 500 ms, UI TTI < 3 s, LCP < 2.5 s, WebSocket < 50 ms, AI suggestion < 3 s.
- **Adaptive Triggers**: If any metric exceeds threshold, fallback to pagination, increase cache size, or toggle feature flags.

### Documentation Updates
- Added this section to `CLAUDE.md` for quick reference.
- Summarized the same information in the Obsidian log (see below).


**Previous Issue**: "Application error: a client-side exception has occurred" on `/time-tracking` page.

### All Issues Resolved ✅
1. **API Endpoints**: Fixed incorrect paths in `endpoints.ts` and `useTimeTracking.ts`.
   - `/api/time-tracking/metrics` -> `/api/time-tracking/roi`
   - `/api/time-tracking/weekly` -> `/api/time-tracking/report/weekly`
   - Added `/api/uncertainty/status`
2. **Parameter Mapping**: Mapped `period` parameter (`week` -> `weekly`) to match backend validation.
3. **Data Structure Mismatch**:
   - `useTimeMetrics`: Mapped `period_start/end` -> `date_range`, `manual_time_hours` -> `baseline_hours`.
   - `useWeeklySummary`: Implemented adapter to convert backend `WeeklyReport` to frontend `WeeklySummary`.
4. **Type Conflicts**: Resolved `WeeklySummary` import conflict in `useTimeTracking.ts`.
5. **Hydration Mismatch**: Fixed server/client rendering inconsistency.
   - **Root Cause**: `Date.now()` in mock data + locale-specific date formatting
   - **Fix 1**: Changed mock data to use fixed dates (`'2025-11-18T00:00:00Z'`)
   - **Fix 2**: Added `suppressHydrationWarning` to date display in page.tsx
   - **Files Changed**: `web-dashboard/lib/hooks/useTimeTracking.ts`, `web-dashboard/app/time-tracking/page.tsx`
   - **Documentation**: `docs/HYDRATION_MISMATCH_FIX.md`

### Testing Checklist

### Refactoring Validation Checklist
- [ ] Verify router modularization (`app/routers/__init__.py`) is functional and all routers are included.
- [ ] Confirm central config values are loaded from `app/config.py`.
- [ ] Run integration tests for `kanban_dependencies`, `kanban_projects`, `kanban_context` (≥85 % coverage).
- [ ] Execute performance benchmark script (`scripts/benchmark_kanban.py`) and ensure DAG < 50 ms for 1 000 tasks.
- [ ] Validate low‑confidence uncertainty map items (Q5‑1, Q6, Q7) with targeted experiments.
- [ ] Review generated OpenAPI spec (`docs/openapi.yaml`) for completeness.
- [ ] Ensure CI pipeline passes all lint, security, and test stages.
- [ ] Confirm frontend Kanban UI loads without hydration warnings and meets performance targets.
### Testing Required
- Navigate to `http://localhost:3000/time-tracking` and verify:
  - [ ] Page loads without crash
  - [ ] No "Application error" overlay
  - [ ] Date range displays correctly
  - [ ] Weekly summary card shows data
  - [ ] No hydration mismatch in browser console

---
