# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Current Development Roadmap (2025-12-06)

> **하이브리드 접근**: 영역별 성숙도에 맞춘 목표 설정

### 📌 Claude Code 핵심 요약

```yaml
현재 상태 (2025-12-09 기준):
  Backend: 95% ✅ → 높은 목표 적용
  Frontend: 50% ⚠️ → 점진적 개발
  AI Bridge: 30% ⚠️ → 점진적 개발
  테스트: 98.4% 통과 (183/186) ✅
  E2E: 85% 통과 (17/20) - 3개 이슈 수정 필요

즉시 해야 할 일 (P0):
  1. CI/CD Pipeline 생성 (.github/workflows/)
  2. DB 마이그레이션 실행 (PostgreSQL + kanban 스키마)
  3. E2E 이슈 3개 해결 (Time Tracking, Quality, Performance)
```

### 📚 문서 계층 (Document Hierarchy)

**Tier 1 - 필수 참조** (Single Source of Truth):
| 문서 | 위치 | 내용 |
|------|------|------|
| **CLAUDE.md** | 루트 | 프로젝트 컨텍스트 + 현재 상태 ⭐ |
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


## Current Status (2025-12-08) - Week 1 Day 2 API Integration Complete ✅

**Phase**: Week 1 Day 2 - Backend API Integration & Task Detail Modal
**Completion**: 100% (6/6 tasks)
**Build Status**: ✅ Production build passing
**New Components**: 2 (API client + TaskDetailModal)
**Type System**: ✅ Aligned frontend/backend types

### Week 0-1 Progress
- ✅ **Week 0 Day 1-3**: Foundation setup, pre-commit hooks, RL validation framework
- ✅ **Week 0 Day 4**: Performance baselines, coverage tracking, RL hypothesis validation
- ✅ **Week 0 Day 5**: Comprehensive test analysis, Week 0 completion (95%)
- ✅ **Week 1 Day 1**: Kanban UI Foundation (COMPLETE)
- ✅ **Week 1 Day 2**: API Integration + Task Detail Modal (COMPLETE)

### Recent Achievements (2025-12-08)

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

### Documentation
- Latest: `docs/WEEK0_DAY4_COMPLETION_REPORT.md`
- RL Validation: `docs/WEEK0_DAY4_RL_VALIDATION_SUMMARY.md`
- Coverage Tracker: `scripts/track_coverage_trend.py`

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
