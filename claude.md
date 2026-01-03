Last Updated: 2026-01-01 18:26
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Current Development Roadmap (2025-12-25)

> **하이브리드 접근**: 영역별 성숙도에 맞춘 목표 설정

### 📌 Claude Code 핵심 요약

```yaml
현재 상태 (2026-01-01 기준):
  Backend: 100% ✅ → 707/707 tests passing
  Frontend: 95% ✅ → Kanban UI + Governance UI + Uncertainty/Confidence WebSocket + E2E tests
  CI/CD: 100% ✅ → GitHub Actions workflows deployed (3 workflows)
  Feature Flags: 100% ✅ → Tier 1 rollback ready (<10s)
  Database: 100% ✅ → Kanban schema (7 tables) migrated + Service DI fixed
  Production: 100% ✅ → Deployment infrastructure complete (7 files)
  Governance: 100% ✅ → 4-Tier System + Phase 5 Enhancement complete

완료 상황:
  ✅ Week 8: CI/CD + Performance + Production Deployment Prep
  ✅ 2025-12-24~25: 4-Tier Governance System Implementation
    - Tier 규칙 시스템 (`tiers.yaml`)
    - Backend API (/tier/status, /tier/upgrade)
    - Frontend UI (ProjectTierStatus 컴포넌트)
    - CLI Tool (udo.bat + cli/udo.py)
    - E2E 검증 완료 (Tier 1 → Tier 2 업그레이드)
  ✅ 2026-01-01: Uncertainty/Confidence WebSocket Implementation
    - /ws/uncertainty 실시간 엔드포인트
    - /ws/confidence/{phase} Phase별 실시간 엔드포인트
    - UncertaintyConnectionManager, ConfidenceConnectionManager
    - Frontend WebSocket 활성화 (wsEnabled: true)
  ✅ 2025-12-25: Phase 5 - Governance Dashboard Enhancement
    - 7 API endpoints (/rules, /validate, /templates, /apply, /config, /auto-fix, /timeline)
    - Interactive UI (template apply buttons, rule detail modals, auto-fix button)
    - 2 new components (GovernanceStatusCard, TimelineTracker)
    - Path fixes (get_project_root: 2→3 levels, validate_system_rules.py location)
    - Error handling + loading states + success/error toast notifications
    - Dynamic port allocation (start-backend.bat + port_finder.py)
  ✅ Test Status: 707/707 backend, 170/198 E2E (85.9% passing)

다음 단계:
  1. ✅ Governance Dashboard Enhancement (완료 - 2025-12-25)
  2. ⏳ Conduct 5 User Testing Sessions
  3. 🚀 Production Deployment (when ready)
```

### 🚀 Session Start Protocol (MANDATORY)

**CRITICAL**: Run this at the START of EVERY new session to check for scheduled tasks:

```bash
python scripts/session_start.py
```

**What it does**:
- ✅ Checks Obsidian vault for scheduled tasks (`_System/Tasks/scheduled.md`)
- ✅ Alerts about overdue tasks (🚨 P0 priority)
- ✅ Shows tasks due this week (📌 P1 priority)
- ✅ Lists upcoming tasks (next 2 weeks)
- ✅ Integrates with 3-Tier Search telemetry

**Exit codes**:
- `0`: No critical tasks or just upcoming tasks
- `1`: Tasks due this week
- `2`: Overdue tasks (urgent action needed)

**Manual check**:
```bash
# Detailed view
python scripts/check_scheduled_tasks.py --verbose

# JSON output
python scripts/check_scheduled_tasks.py --json
```

**Adding new scheduled tasks**:
Edit `C:/Users/user/Documents/Obsidian Vault/_System/Tasks/scheduled.md` following the template format.

### 📚 세션 문서 (AI Generated - claudedocs/)

> **⚠️ 중요**: AI 세션 간 컨텍스트는 아래 파일을 참조하세요.

| 문서 | 설명 |
|------|------|
| **`claudedocs/HANDOFF.md`** | 세션 간 인계 문서 (단일 진입점) ⭐ |

HANDOFF.md에서 최신 작업 로그, 완료 문서, 분석 문서 등을 확인할 수 있습니다.



### 📚 문서 계층 (Document Hierarchy)

**Tier 1 - 필수 참조** (Single Source of Truth):
| 문서 | 위치 | 내용 |
|------|------|------|
| **CLAUDE.md** | 루트 | 프로젝트 컨텍스트 + 현재 상태 ⭐ |
| **AGENTS.md** | 루트 | 코딩 스타일 + Git 규칙 + 테스트 가이드 ⭐ |
| **개발 로드맵 v6.1** | `docs/DEVELOPMENT_ROADMAP_V6.md` | 하이브리드 접근 + RL 통합 |

**Tier 2 - 실행 가이드**:
| 문서 | 위치 | 내용 |
|------|------|------|
| **Kanban 구현 요약** | `docs/KANBAN_IMPLEMENTATION_SUMMARY.md` | Q1-Q8 결정 + 4주 로드맵 |
| **Week 1 완료 보고서** | `docs/WEEK1_DAY1-2_COMPLETION_REPORT.md` | 진행 현황 + 테스트 결과 |
| **기술 인계 가이드** | `docs/HANDOFF_TO_CLAUDE.md` | Facade 패턴 + 실행 가이드 |

**Tier 3 - 상세 참조** (필요시 확장):
| 문서 | 위치 | 내용 |
|------|------|------|
| **Kanban 전략 분석** | `docs/KANBAN_INTEGRATION_STRATEGY.md` | 18,000 words 전체 분석 |
| **Pre-mortem 분석** | `docs/PREMORTEM_ANALYSIS_2025-12-06.md` | 위험 분석 + 완화 전략 |
| **RL 기반 지식 재사용** | `docs/RL_GUIDED_KNOWLEDGE_REUSE.md` | Training-free GRPO 이론 |

### 하이브리드 목표

**성숙 영역 (Backend) - 높은 목표**:
| 지표 | 현재 | 목표 | 상태 |
|------|------|------|------|
| 테스트 통과율 | 98.4% | **98%** | ✅ 달성 |
| API 응답 시간 | 미측정 | **<200ms** | ⏳ 측정 필요 |

**신규 영역 (Frontend/AI) - 점진적 목표**:
| 지표 | MVP (2주) | Prototype | Beta | Production |
|------|-----------|-----------|------|------------|
| 예측 정확도 | 40% | 55% | 65% | 70% |
| 오류율 | 15% | 10% | 8% | 5% |
| 자동화율 | 65% | 75% | 80% | 85% |

### 현재 Stage: MVP (2주)

```yaml
MVP Task (P0) - Status:
  1. ✅ Uncertainty UI 기본 (3일) - COMPLETE (2026-01-01)
     파일: web-dashboard/app/uncertainty/page.tsx
     WebSocket: /ws/uncertainty 엔드포인트 구현 완료

  2. ✅ Confidence Dashboard 기본 (2일) - COMPLETE (2026-01-01)
     파일: web-dashboard/app/confidence/page.tsx
     WebSocket: /ws/confidence/{phase} 엔드포인트 구현 완료

  3. ✅ CI Pipeline (1일) - COMPLETE
     파일: .github/workflows/backend-ci.yml, frontend-ci.yml
     커밋: 3d37e1d (2025-12-16)

MVP 성공 기준:
  - ✅ 예측 화면 표시 (Uncertainty/Confidence WebSocket 실시간 연동)
  - ✅ CI 자동 실행 (GitHub Actions deployed)
  - ✅ 테스트 통과율 95%+ (707/707 = 100%)
```

### 검증 완료

- [x] 5 Whys 본질 분석 완료
- [x] 현재 상태 테스트 실행 (98.4% 통과, 2025-12-09)
- [x] 영역별 성숙도 분석 완료
- [x] 하이브리드 접근법 정의
- [x] 단계별 보완점 체크리스트
- [x] Gap Analysis 및 계획 검토 (2025-12-13)

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
- `/governance` - Governance dashboard (NEW - interactive template apply, auto-fix, timeline)

**Port Configuration**:
- Frontend default: `http://localhost:3000`
- Backend: Dynamic allocation (default 8001, configurable via `.env`)
- Use `start-backend.bat` for automatic port detection and `.env.local` update

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
# Option 1: Using dynamic port script (RECOMMENDED)
start-backend.bat

# Option 2: Manual start with specific port
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001

# Option 3: Using environment variable
set API_PORT=8001
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload

# API documentation available at:
# http://localhost:8001/docs (Swagger UI)
# http://localhost:8001/redoc (ReDoc)
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
- **Obsidian MVP roadmap**: `docs/OBSIDIAN_SYNC_MVP_ROADMAP.md` (NEW - MVP-first approach)
- Time tracking guide: `docs/TIME_TRACKING_GUIDE.md`
- **Error Prevention Guide**: `docs/guides/ERROR_PREVENTION_GUIDE.md` (NEW - Week 7 Day 1, 6 common errors)
- **Quick Checklist**: `docs/guides/QUICK_ERROR_PREVENTION_CHECKLIST.md` (2-minute pre-commit check)
- **Week 7 Day 1 Completion**: `docs/sessions/WEEK7_DAY1_ERROR_PREVENTION_COMPLETE.md` (Session report)

---

<!-- ⚠️ PROTECTED SECTION - DO NOT MODIFY OR DELETE ⚠️
     This section contains critical Obsidian sync strategy decisions.
     Master document: docs/OBSIDIAN_SYNC_MVP_ROADMAP.md
     If CLAUDE.md is regenerated, restore this section from the master document.
     Last updated: 2025-12-16
-->

## Obsidian Sync Strategy (2025-12-16) 🔒

> **⚠️ PROTECTED**: 이 섹션은 사용자 승인된 전략입니다. 수정 시 `docs/OBSIDIAN_SYNC_MVP_ROADMAP.md` 참조.

**Status**: Phase 0 (Maintain Current) - MVP approach adopted

### Current Approach: MVP-First, Data-Driven Expansion

기존 전략 문서(UNIFIED_OBSIDIAN_SYNC_STRATEGY.md, LEARNING_CURRICULUM_AUTOMATION.md)는 현재 단계에서 과도하다고 판단되어 `docs/_ARCHIVE/`로 이동. MVP 우선 접근법 채택.

**Core Principle**: 작동하는 것부터, 측정 기반 확장, 외부 의존성 최소화

### Phase Summary

| Phase | Timeline | Focus | Dependencies |
|-------|----------|-------|--------------|
| 0: Maintain | Now | 기존 개발일지 동기화 유지 | 0 |
| 1: MVP | Week 5-6 | 🌱 단일 카테고리 추출 | 0 |
| 2: Measure | Week 7-8 | 데이터 수집 및 ROI 측정 | 0 |
| 3: Expand | Month 3+ | 카테고리 확장 (데이터 기반) | 0 |
| 4: Advanced | Month 6+ | 고급 기능 (수요 발생 시) | TBD |

### Working Scripts (No Changes)
```
scripts/
├── obsidian_auto_sync.py      # v2.0 - Git commit → 개발일지 (KEEP)
├── obsidian_append.py         # MCP append helper
├── obsidian_3stage_search.py  # 3-tier search
└── obsidian_tag_enforcer.py   # Tag validation
```

### Key Documents
- **MVP Roadmap**: `docs/OBSIDIAN_SYNC_MVP_ROADMAP.md`
- **Critical Review**: `docs/OPUS_CRITICAL_REVIEW_OBSIDIAN_STRATEGY.md`
- **Multi-Angle Analysis**: `docs/MULTI_ANGLE_ANALYSIS_OBSIDIAN_STRATEGY.md`
- **Archived (for future)**: `docs/_ARCHIVE/UNIFIED_OBSIDIAN_SYNC_STRATEGY.md`, `docs/_ARCHIVE/LEARNING_CURRICULUM_AUTOMATION.md`

### Expansion Triggers (Data-Driven)
- Phase 1 → 2: UDO 핵심 기능 완료 후
- Phase 2 → 3: concepts_extracted ≥ 50 AND reuse_rate ≥ 30%
- Phase 3 → 4: 실제 교육/PDF 요청 10건+

---

## Kanban-UDO Integration (2025-12-16)

**Status**: Week 4 Feature Flags Complete ✅ - Ready for User Testing

### Quick Reference

**Master Document**: `docs/KANBAN_IMPLEMENTATION_SUMMARY.md` (Concise overview)

**Week 4 Feature Flags** (2025-12-16 Complete):
- `backend/app/core/feature_flags.py` - Thread-safe feature flag manager (418 lines)
- `backend/app/routers/admin.py` - Admin API for Tier 1 rollback (279 lines)
- `backend/tests/test_feature_flags.py` - 25/25 tests passing (100%)
- `docs/WEEK4_FEATURE_FLAGS_COMPLETION.md` - Complete documentation

**Week 3 Archive Implementation** (Complete):
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


## Current Status (2025-12-23 EOD) - WEEK 8 COMPLETE ✅✅✅✅✅

**Phase**: Week 8 COMPLETE - All AI tasks delivered (100%)
**Completion**: 4/4 AI days complete, 1 user action pending (User Testing sessions)
**Backend Tests**: ✅ 707/707 passing (100%)
**E2E Tests**: ✅ 18/18 passing (100%)
**CI/CD**: ✅ 3 GitHub Actions workflows deployed (pr-tests, frontend-ci, nightly-tests)
**Production Ready**: ✅ 7 files created, 2,870+ lines of documentation
**Code Delivered**: Week 8 complete with production deployment infrastructure

### Week 0-8 Progress (ALL COMPLETE)
- ✅ **Week 0 Day 1-3**: Foundation setup, pre-commit hooks, RL validation framework
- ✅ **Week 0 Day 4**: Performance baselines, coverage tracking, RL hypothesis validation
- ✅ **Week 0 Day 5**: Comprehensive test analysis, Week 0 completion (95%)
- ✅ **Week 1 Day 1**: Kanban UI Foundation (COMPLETE)
- ✅ **Week 1 Day 2**: API Integration + Task Detail Modal (COMPLETE)
- ✅ **Week 2 Day 1**: API Integration + Optimistic Updates (COMPLETE)
- ✅ **Week 2 Day 2**: TaskCreateModal (COMPLETE)
- ✅ **Week 2 Day 3**: Filter Functionality (COMPLETE)
- ✅ **Week 2 Day 4**: Context Operations (COMPLETE)
- ✅ **Week 5 Day 1**: Uncertainty UI Enhancement (COMPLETE)
- ✅ **Week 5 Day 2**: Confidence Dashboard Testing (COMPLETE)
- ✅ **Week 5 Day 3**: E2E Testing Suite + RBAC Restoration (COMPLETE)
- ✅ **Week 6 Day 1**: Database Integration & Kanban Backend (COMPLETE)
- ✅ **Week 6 Day 2**: Dependency Graph UI (D3.js force-directed, 14 E2E tests) (COMPLETE)
- ✅ **Week 6 Day 3**: Context Upload UI (Drag-drop, progress bar, 14 E2E tests) (COMPLETE)
- ✅ **Week 6 Day 4**: AI Task Suggestion Modal (Claude Sonnet 4.5, Q2 hybrid, 11 E2E tests) (COMPLETE)
- ✅ **Week 6 Day 5**: Archive View + ROI Dashboard (18 E2E tests, Recharts visualization) (COMPLETE)
- ✅ **Week 7 Day 1**: Error Prevention & WebSocket 403 Fix (6 error patterns eliminated) (COMPLETE)
- ✅ **Week 7 Day 2**: Performance Optimization (React.memo + Virtual Scrolling) (COMPLETE)
- ✅ **Week 7 Day 3-4**: P0 Critical Fixes (Circuit Breaker, Cache Manager, Multi-Project, DAG) (COMPLETE)
- ✅ **Week 7 Day 5**: E2E Test Recovery (18/18 passing, 60% faster execution) (COMPLETE)
- ✅ **Week 8 Day 1-2**: E2E Tests CI/CD Integration (3 GitHub Actions workflows) (COMPLETE)
- ✅ **Week 8 Day 3**: Performance Optimization Verification (all optimizations in place) (COMPLETE)
- ✅ **Week 8 Day 4**: User Testing Documentation (3 comprehensive guides, 870+ lines) (COMPLETE)
- ✅ **Week 8 Day 5**: Production Deployment Prep (7 files, 2,870+ lines) (COMPLETE)

### Recent Achievements (2025-12-23)

**Week 8 - Production Deployment Prep COMPLETE** 🎉🎉🎉

1. ✅ **Day 1-2: E2E CI/CD Integration** (VERIFIED - Already Implemented)
   - 3 GitHub Actions workflows: pr-tests.yml, frontend-ci.yml, nightly-tests.yml
   - Backend + E2E tests on PR (chromium)
   - Nightly regression (3 browsers: chromium, firefox, webkit)
   - Performance benchmarks (DAG, Circuit Breaker, Cache Manager)

2. ✅ **Day 3: Performance Optimization** (VERIFIED - Already Implemented)
   - Lazy loading: 4 dashboard components (dashboard.tsx:36-39)
   - Virtual scrolling: TaskList with @tanstack/react-virtual (10,000+ tasks)
   - React Query: Proper caching (staleTime: 10s, refetchOnWindowFocus: false)
   - useMemo: 6 expensive computations memoized

3. ✅ **Day 4: User Testing Documentation** (3 Files Created, 870+ lines)
   - `docs/WEEK8_DAY4_USER_TESTING_GUIDE.md` (330 lines)
     - 5 test scenarios (Kanban, Dependencies, Context, AI, Archive/ROI)
     - 30-45 min per user session structure
   - `docs/WEEK8_DAY4_TESTING_CHECKLIST.md` (210 lines)
     - Pre-session setup checklist
     - Quick reference for facilitators
   - `docs/WEEK8_DAY4_FEEDBACK_TEMPLATE.md` (330 lines)
     - 15 survey questions (Likert scale + NPS)
     - Bug reporting templates

4. ✅ **Day 5: Production Deployment Prep** (7 Files Created, 2,870+ lines)
   - `.env.production.example` (90+ lines) - Environment variables
   - `backend/Dockerfile` (70+ lines) - Multi-stage, non-root user
   - `web-dashboard/Dockerfile` (70+ lines) - Next.js standalone
   - `docker-compose.prod.yml` (290+ lines) - 9 services orchestration
   - `docs/PRODUCTION_DEPLOYMENT_GUIDE.md` (550+ lines) - 10-step deployment
   - `docs/ROLLBACK_PROCEDURES.md` (470+ lines) - 3-tier rollback strategy
   - `docs/SECURITY_AUDIT_CHECKLIST.md` (460+ lines) - 103 security items

5. ✅ **Production Readiness Achieved**
   - Security: 103-item audit checklist (10 categories)
   - Rollback: 3-tier strategy (Emergency <5min, Standard <30min, Partial)
   - Monitoring: Prometheus + Grafana + Sentry integration
   - Deployment: Complete infrastructure with health checks
   - Documentation: 2,870+ lines of production guides

**Week 7 Day 5 - E2E Test Recovery** 🎉 (Previous)

1. ✅ **E2E Tests 100% 복구**: 18/18 passing (이전 12/18, 67%)
2. ✅ **Strict Mode Violation 수정**: Role-based selector 사용
   - BEFORE: `locator('text=Context Briefing')` → 2개 요소 매칭
   - AFTER: `getByRole('heading', { name: 'Context Briefing' })` → 정확한 1개 선택
3. ✅ **Playwright 설정 최적화**:
   - Workers: 6 → 3 (리소스 경합 방지)
   - Timeout: 30s → 60s (타임아웃 여유 확보)
4. ✅ **성능 개선**: 실행 시간 59.8s → 23.7s (60% 개선)
5. ✅ **안정성 향상**: 타임아웃 에러 6건 → 0건 (100% 제거)
6. ✅ **문서화 완료**: WEEK7_E2E_TEST_RECOVERY_COMPLETE.md, WEEK7_E2E_TEST_ANALYSIS.md

**Week 7 Day 3-4 - P0 Critical Fixes** 🎉

1. ✅ **Circuit Breaker** (17/17 tests passing)
   - 3가지 상태: CLOSED, OPEN, HALF_OPEN
   - 실패 임계값 기반 자동 차단
   - 복구 타임아웃 후 점진적 복구
2. ✅ **Cache Manager** (20/20 tests passing)
   - 50MB 메모리 제한 (OOM 방지)
   - LRU (Least Recently Used) 자동 퇴출
   - Thread-safe with Lock
3. ✅ **Multi-Project Primary Selection**
   - Q5 결정사항 완벽 구현: 1 Primary + max 3 Related
   - Atomic operation으로 Primary 설정
4. ✅ **DAG Performance Benchmark** (7/7 tests passing)
   - 1,000 tasks 성능 검증
   - 목표 달성: <50ms for 1,000 tasks

**Week 7 Day 1-2 - Error Prevention & Performance** 🎉

1. ✅ **Error Prevention**: 6가지 에러 패턴 완전 제거
   - Dev bypass, Service fallback, WebSocket checking
   - Logging guidelines, Naming conventions, Testing checklist
2. ✅ **WebSocket 403 Fix**: `project_id` 추가로 403 에러 해결
3. ✅ **Performance Optimization**:
   - React.memo 적용 (9개 컴포넌트)
   - Virtual Scrolling 구현 (10,000 tasks 지원)

**Week 6 Day 1 - Database Integration & Kanban Backend** (Previous)

1. ✅ **PostgreSQL 연결 검증**: Docker 컨테이너 `udo_postgres` 정상 작동 (pgvector/pgvector:pg16)
2. ✅ **Kanban 스키마 마이그레이션**: 7개 테이블 생성 완료
   - kanban.tasks (25 컬럼, 9 인덱스, 6 제약조건)
   - kanban.dependencies (DAG 구조, Q7)
   - kanban.dependency_audit (변경 이력)
   - kanban.quality_gates (Q3)
   - kanban.task_archive (Q6)
   - kanban.task_contexts (Q4)
   - kanban.task_projects (Q5)
3. ✅ **Q1-Q8 결정사항 DB 반영**: 모든 전략적 결정 데이터베이스에 완전 반영
4. ✅ **Kanban 테스트 100% 통과**: 155/155 테스트 성공
   - test_kanban_tasks.py: 46/46
   - test_kanban_dependencies.py + projects + contexts: 76/76
   - test_kanban_ai.py + archive: 33/33
5. ✅ **전체 백엔드 테스트 100% 통과**: 707/707 테스트 성공 (165.81초)
6. ✅ **성능 최적화 확인**: 인덱스 전략으로 <50ms 쿼리 목표 달성 준비

**Week 2 Day 4 - Context Operations** (Previous)
1. ✅ **Kanban Context API Client**: Full backend integration (lib/api/kanban-context.ts)
   - 5 API functions: fetchContextMetadata, uploadContext, trackContextLoad, fetchFullContext, downloadContextZip
   - TypeScript interfaces: ContextMetadata, ContextFile, TaskContext
   - Error handling: Custom KanbanContextAPIError class with status codes
   - Size limit validation: 50MB enforcement
   - Browser download: Blob API implementation

2. ✅ **ContextManager Component**: Context management UI (242 lines)
   - Metadata display: File count, size, load stats (count + avg time)
   - Download ZIP: With load time tracking (performance.now())
   - Upload placeholder: Week 3 implementation
   - Error/Success alerts: ShadCN Alert component
   - Q4 info banner: Double-click auto-load guidance

3. ✅ **TaskDetailModal Integration**: Tabs navigation structure
   - Added ShadCN Tabs component
   - Details Tab: All existing task fields (description, tags, time tracking, dependencies, context notes, AI metadata)
   - Context Tab: ContextManager component with taskId prop
   - Clean separation: Tab navigation + footer buttons

4. ✅ **Production Build**: TypeScript compilation passing (10.9s)
   - Zero errors after Tabs + ContextManager integration
   - All routes: 9 pages static-rendered successfully
   - New files: 2 (kanban-context.ts, ContextManager.tsx)

**Week 2 Day 3 - Filter Functionality** 🎉
1. ✅ **FilterPanel Component**: Multi-select filtering (245 lines)
   - Phase, Status, Priority filters with color-coded checkboxes
   - Active filter count badge + clear all button
   - Popover UI with clean organization

2. ✅ **Kanban Page Integration**: Efficient filtering with useMemo
   - Filtered tasks computation: Phase + Status + Priority logic
   - Stats footer: Shows "X / Y" when filtered
   - FilterPanel replaces static Filter button

**Week 2 Day 2 - TaskCreateModal** 🎉
1. ✅ **Task Creation UI**: Full form with validation
   - All task fields: Title, description, phase, priority, tags, time estimates
   - Form validation: Required fields enforcement
   - API integration: Creates task via kanbanAPI.createTask()

**Week 2 Day 1 - Optimistic Updates** 🎉
1. ✅ **Drag & Drop Persistence**: Backend integration
   - Optimistic UI update + API call to updateTaskStatus
   - Rollback on error + network detection
   - Server timestamp sync

**Week 1 Day 2 - API Integration & Task Detail Modal** 🎉
1. ✅ **Kanban API Client**: Complete backend integration (lib/api/kanban.ts)
   - CRUD operations: fetchTasks, createTask, updateTask, deleteTask
   - Status management: updateTaskStatus (for drag & drop persistence)
   - Phase/Priority updates: updateTaskPhase, updateTaskPriority
   - Quality & Archiving: checkQualityGate, archiveTask
   - Batch operations: bulkUpdateStatus
   - Error handling: Custom KanbanAPIError class
   - 12 API endpoints fully integrated

2. ✅ **Type System Alignment**: Frontend/backend type consistency
   - Fixed TaskStatus: `'todo' | 'done'` → `'pending' | 'completed'`
   - Updated files: `kanban.ts`, `kanban-store.ts`, `page.tsx`, `Column.tsx`
   - TypeScript errors: 100% resolved
   - Build verification: ✅ Passing

3. ✅ **Optimistic Updates with Rollback**: Robust error handling
   - Immediate UI feedback on drag & drop
   - Automatic rollback on API failure
   - Network error detection and user notification
   - Prevents concurrent updates with `isUpdating` flag
   - Server response sync for timestamp/metadata updates

4. ✅ **TaskDetailModal Component**: Full task editing capabilities
   - Inline editing: Title, description, tags, context notes
   - Time tracking: Estimated hours, actual hours
   - Metadata display: Priority badges, status indicators, phase info
   - Dependencies: Read-only display of dependencies and blockers
   - AI metadata: Confidence score display for AI-suggested tasks
   - Actions: Edit, Save, Cancel, Delete
   - Integration: Modal triggered from TaskCard click

5. ✅ **ShadCN UI Components**: Added missing form components
   - Components added: `input.tsx`, `textarea.tsx`, `label.tsx`, `select.tsx`
   - Integration: TaskDetailModal uses all new components
   - Consistency: Matches existing UI design system

6. ✅ **Production Build**: Build passing (12.7s compilation)
   - Zero TypeScript errors after type alignment
   - All routes: 7 pages static-rendered successfully
   - Performance: `/kanban` route fully optimized
   - New files: 2 (API client + TaskDetailModal)

**Week 1 Day 1 - Kanban UI Foundation** 🎉
1. ✅ **Kanban Board Component Structure**: Full drag & drop with @dnd-kit
   - Components: `KanbanBoard`, `Column`, `TaskCard`
   - Zustand store: `kanban-store.ts` with localStorage persistence
   - Types: Complete TypeScript interfaces for tasks and columns
   - Files created: 6 new files (types, store, 3 components, page, navigation)

2. ✅ **Drag & Drop Integration**: Modern @dnd-kit library (React 19 compatible)
   - Sensors: Pointer and keyboard for accessibility
   - Optimistic updates: Instant UI feedback
   - Visual feedback: Drag overlay with rotation effect
   - Column states: To Do, In Progress, Blocked, Done

3. ✅ **Production Build**: Next.js build passing (32.6s compilation)
   - TypeScript: Zero errors
   - Routes: `/kanban` added to navigation
   - Static generation: All pages pre-rendered successfully
   - Build size: Optimized for production

4. ✅ **Sample Data**: 5 mock tasks for testing
   - Priority levels: Low, Medium, High, Critical with color coding
   - Phase integration: Ideation, Design, MVP, Implementation, Testing
   - Tags system: Flexible tag display with overflow handling
   - AI indicators: AI-suggested tasks with confidence scores

5. ✅ **E2E Testing with Playwright** (2025-12-07): 13/13 tests passing (100%)
   - Test file: `web-dashboard/tests/e2e/kanban-ui.spec.ts`
   - Coverage: Page load, 4 columns, 5 mock tasks, priority colors, metadata, badges, stats footer, action buttons, navigation
   - Performance: 2083ms load time (< 3000ms target, 30% better than goal)
   - Visual regression: Full page + individual column screenshots captured
   - Console errors: Zero errors detected across all tests
   - Test execution time: 28.8s (13 tests in parallel with 6 workers)

**Week 0 Achievements**
1. ✅ **RL Hypothesis Validated**: 88% conceptual overlap with ArXiv paper 2510.08191
   - User insight confirmed: "Obsidian knowledge reuse = Training-free GRPO"
   - Recommendation: Documentation only (no new code needed)
   - ROI: Focus on existing roadmap (frontend tests 0% → priority)

2. ✅ **Performance Baseline Established**: 5 predictions logged
   - State: DETERMINISTIC (stable, predictable)
   - Window: 24-hour ahead prediction active
   - Location: `C:\Users\user\.udo\predictions_log.jsonl`

3. ✅ **Test Coverage Analysis**: 58% overall
   - High-quality: Kanban (95%+), AI Services (100%), Core (95%+)
   - Needs work: Session Management (25%), Project Context (20%)
   - Pass rate: 92.2% (376/408 tests)

4. ⚠️ **Coverage Trend Tracker**: Script created, encoding issue
   - Workaround: Manual pytest execution available
   - Fix ETA: Week 0 Day 5

### Test Results Summary (2025-12-14)
**Pass Rate**: 100% (440 passed, 0 failed) ✅

**Recent Fixes (2025-12-14)**:
- ✅ Time Tracking Tests (3): Fixed sleep duration for int truncation
- ✅ Uncertainty Tests (4): Fixed import paths and pytest fixture pattern
- ✅ Project Context API (9): Fixed mock service response formats
- ✅ Mock Project Service (2): Aligned with Pydantic model requirements

**Coverage by Category**:
| Category | Coverage | Status |
|----------|----------|--------|
| Backend Tests | 100% | ✅ All passing |
| Kanban Implementation | 95%+ | ✅ Production-ready |
| AI Services | 100% | ✅ Perfect |
| Core Infrastructure | 95%+ | ✅ Excellent |
| Time Tracking | 100% | ✅ All tests pass |
| Uncertainty Integration | 100% | ✅ All tests pass |
| Quality Metrics | 75% | ✅ Good |
| Project Context | 100% | ✅ All tests pass |

### Test Statistics
- **Total Tests**: 440
- **Passed**: 440 (100%)
- **Failed**: 0
- **Warnings**: 402 (deprecation notices, non-critical)

### Documentation (Week 8 Complete)
- **Week 8 Completion Report**: `docs/WEEK8_COMPLETION_REPORT.md` (NEW - comprehensive summary)
- **Week 8 Day 4 User Testing Guide**: `docs/WEEK8_DAY4_USER_TESTING_GUIDE.md`
- **Week 8 Day 4 Testing Checklist**: `docs/WEEK8_DAY4_TESTING_CHECKLIST.md`
- **Week 8 Day 4 Feedback Template**: `docs/WEEK8_DAY4_FEEDBACK_TEMPLATE.md`
- **Production Deployment Guide**: `docs/PRODUCTION_DEPLOYMENT_GUIDE.md` (550+ lines)
- **Rollback Procedures**: `docs/ROLLBACK_PROCEDURES.md` (470+ lines)
- **Security Audit Checklist**: `docs/SECURITY_AUDIT_CHECKLIST.md` (460+ lines)

### Next Steps: Immediate Actions Required
1. **User Testing Sessions** (Week 8 Day 4 - USER ACTION)
   - Conduct 5 user testing sessions (see `docs/WEEK8_DAY4_USER_TESTING_GUIDE.md`)
   - Participants needed: Junior Dev, Senior Dev, PM, DevOps, PO
   - Target: ≥4.0/5.0 satisfaction, 0 critical bugs

2. **Review Production Documentation** (USER ACTION)
   - Read `docs/PRODUCTION_DEPLOYMENT_GUIDE.md` (10-step deployment)
   - Review `docs/SECURITY_AUDIT_CHECKLIST.md` (103 items, 10 categories)
   - Understand `docs/ROLLBACK_PROCEDURES.md` (3-tier strategy)

3. **Production Deployment** (When Ready - After User Testing)
   - Follow 10-step deployment guide
   - Complete security audit (95%+ passing required)
   - Validate all 10 deployment blockers
   - Test 3-tier rollback procedures

### Optional Next Steps (Week 9+)
- Mobile responsive design
- Offline mode (Service Worker)
- Advanced analytics dashboard
- Multi-language support (i18n)
- Increase React Query cache times (staleTime 30-60s, cacheTime 10-15min)
- Performance measurement with Lighthouse CI

**Current Environment**:
- Backend: ✅ Running on port 8000 (707/707 tests passing)
- Frontend: ✅ Next.js dev/build mode ready
- Database: ✅ PostgreSQL with 7 Kanban tables
- CI/CD: ✅ 3 GitHub Actions workflows deployed
- Production Infrastructure: ✅ All files created and documented
- All Week 8 AI tasks: ✅ 100% COMPLETE

---

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
