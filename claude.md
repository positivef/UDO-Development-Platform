Last Updated: 2026-01-29 19:10
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current Development Roadmap (2025-12-25)

> **하이브리드 접근**: 영역별 성숙도에 맞춘 목표 설정

### Claude Code 핵심 요약

```yaml
현재 상태 (2026-01-29 기준):
  Backend: 100% -> 713/713 tests passing
  Frontend: 95% -> Kanban UI + Governance UI + Uncertainty/Confidence WebSocket + E2E tests
  CI/CD: 100% -> GitHub Actions workflows deployed (3 workflows)
  Feature Flags: 100% -> Tier 1 rollback ready (<10s)
  Database: 100% -> Kanban schema (7 tables) migrated + Service DI fixed
  Production: 100% -> Deployment infrastructure complete (10 files)
  Governance: 100% -> 4-Tier System + Phase 5 Enhancement complete

완료 상황:
  Week 8: CI/CD + Performance + Production Deployment Prep
  2025-12-24~25: 4-Tier Governance System Implementation
    - Tier 규칙 시스템 (tiers.yaml)
    - Backend API (/tier/status, /tier/upgrade)
    - Frontend UI (ProjectTierStatus 컴포넌트)
    - CLI Tool (udo.bat + cli/udo.py)
    - E2E 검증 완료 (Tier 1 -> Tier 2 업그레이드)
  2026-01-01: Uncertainty/Confidence WebSocket Implementation
    - /ws/uncertainty 실시간 엔드포인트
    - /ws/confidence/{phase} Phase별 실시간 엔드포인트
    - UncertaintyConnectionManager, ConfidenceConnectionManager
    - Frontend WebSocket 활성화 (wsEnabled: true)
  2025-12-25: Phase 5 - Governance Dashboard Enhancement
    - 7 API endpoints (/rules, /validate, /templates, /apply, /config, /auto-fix, /timeline)
    - Interactive UI (template apply buttons, rule detail modals, auto-fix button)
    - 2 new components (GovernanceStatusCard, TimelineTracker)
    - Path fixes (get_project_root: 2->3 levels, validate_system_rules.py location)
    - Error handling + loading states + success/error toast notifications
    - Dynamic port allocation (start-backend.bat + port_finder.py)
  2026-01-29: User Testing + Production Deployment Prep
    - AI-simulated user testing: 4.3/5.0 (target 4.0 PASS)
    - 5 scenarios: Kanban (5.0), Navigation (4.0), Uncertainty (5.0), Confidence (5.0), Governance (2.5)
    - Production infrastructure: Dockerfile, nginx, Prometheus, Grafana
    - 3 deployment docs: Deployment Guide, Security Audit (103 items), Rollback Procedures
  Test Status: 713/713 backend

다음 단계:
  1. Governance Dashboard Enhancement (완료 - 2025-12-25)
  2. User Testing Sessions (완료 - 2026-01-29, 4.3/5.0 PASS)
  3. Production Deployment Prep (완료 - 2026-01-29)
  4. Production Deployment (ready - follow docs/PRODUCTION_DEPLOYMENT_GUIDE.md)
```

### Session Start Protocol (MANDATORY)

**CRITICAL**: Run this at the START of EVERY new session to check for scheduled tasks:

```bash
python scripts/session_start.py
```

### 세션 문서 (AI Generated - claudedocs/)

> AI 세션 간 컨텍스트는 아래 파일을 참조하세요.

| 문서 | 설명 |
|------|------|
| **`claudedocs/HANDOFF.md`** | 세션 간 인계 문서 (단일 진입점) |

### 문서 계층 (Document Hierarchy)

**Tier 1 - 필수 참조** (Single Source of Truth):
| 문서 | 위치 | 내용 |
|------|------|------|
| **CLAUDE.md** | 루트 | 프로젝트 컨텍스트 + 현재 상태 |
| **AGENTS.md** | 루트 | 코딩 스타일 + Git 규칙 + 테스트 가이드 |
| **개발 로드맵 v6.1** | `docs/DEVELOPMENT_ROADMAP_V6.md` | 하이브리드 접근 + RL 통합 |

**Tier 2 - 실행 가이드**:
| 문서 | 위치 | 내용 |
|------|------|------|
| **Kanban 구현 요약** | `docs/KANBAN_IMPLEMENTATION_SUMMARY.md` | Q1-Q8 결정 + 4주 로드맵 |
| **기술 인계 가이드** | `docs/HANDOFF_TO_CLAUDE.md` | Facade 패턴 + 실행 가이드 |

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

1. **UDO v2 (Orchestrator)** - `src/unified_development_orchestrator_v2.py`
   - Phase-aware evaluation (Ideation -> Design -> MVP -> Implementation -> Testing)
   - Bayesian confidence scoring per phase
   - Decision logic (GO/GO_WITH_CHECKPOINTS/NO_GO)

2. **Uncertainty Map v3 (Predictor)** - `src/uncertainty_map_v3.py`
   - 24-hour predictive uncertainty modeling
   - Quantum state classification (5 states)
   - Auto-mitigation strategy generation with ROI calculation

3. **AI Collaboration Bridge** - `src/three_ai_collaboration_bridge.py`
   - Multi-AI orchestration (Claude, Codex, Gemini)
   - MCP server integration

### Backend API (FastAPI)

**Location**: `backend/main.py`

**Key Routers** (`backend/app/routers/`):
- `quality_metrics_router` - Code quality analysis (Pylint, ESLint, pytest coverage)
- `constitutional_router` - AI governance enforcement (17-article constitution)
- `time_tracking_router` - ROI measurement and productivity tracking
- `uncertainty_router` - Uncertainty analysis and predictions
- `kanban_tasks` - Kanban task management
- `kanban_dependencies` - Task dependencies (DAG)
- `kanban_archive` - Task archiving with AI summarization
- `websocket_handler` - Real-time updates to frontend

**Critical Services** (`backend/app/services/`):
- `quality_service.py` - Unified subprocess execution
- `project_context_service.py` - Project state management with mock service fallback
- `kanban_task_service.py` - Kanban task CRUD operations
- `kanban_archive_service.py` - Archive service with GPT-4o integration

### Frontend Dashboard (Next.js)

**Location**: `web-dashboard/`

**Stack**: Next.js 16.0.3, React 19.2.0, Tailwind CSS v4, Zustand, Tanstack Query, Recharts

**Key Pages**:
- `/` - Main dashboard with real-time metrics
- `/kanban` - Kanban board with drag & drop
- `/uncertainty` - Uncertainty map with WebSocket
- `/confidence` - Confidence dashboard with WebSocket
- `/quality` - Quality metrics visualization
- `/time-tracking` - ROI and productivity dashboard
- `/governance` - Governance dashboard (interactive)
- `/archive` - Archive view with ROI dashboard

## Development Commands

### Environment Setup

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Install frontend dependencies
cd web-dashboard && npm install
```

### Running Tests

```bash
# All backend tests
.venv\Scripts\python.exe -m pytest backend/tests/ -v

# Specific test file
.venv\Scripts\python.exe -m pytest backend/tests/test_kanban_tasks.py -v

# E2E tests
cd web-dashboard && npx playwright test

# Frontend build
cd web-dashboard && npm run build
```

### Running Development Servers

```bash
# Backend
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd web-dashboard && npm run dev
```

### Production Deployment

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# With monitoring + backup
docker-compose -f docker-compose.prod.yml --profile with-nginx --profile with-backup up -d
```

## Key Configuration

### Phase-Specific Confidence Thresholds
- **Ideation**: 60% | **Design**: 65% | **MVP**: 65% | **Implementation**: 70% | **Testing**: 70%

### Uncertainty States
- DETERMINISTIC (<10%) | PROBABILISTIC (10-30%) | QUANTUM (30-60%) | CHAOTIC (60-90%) | VOID (>90%)

### Backend Configuration
- `backend/config/UDO_CONSTITUTION.yaml` - AI governance rules (17 articles)
- `backend/config/baseline_times.yaml` - Performance baselines
- `backend/.env` - Environment variables

## Critical Implementation Details

### Mock Service Pattern

Project context service uses mock fallback when database is unavailable:

```python
# In backend/main.py
from app.services.project_context_service import enable_mock_service
enable_mock_service()  # CRITICAL: Before router imports
```

### Constitutional Guard Pre-commit

**P1: Design Review First** - Blocks commits affecting >3 files without design doc.

## Project Structure

```
UDO-Development-Platform/
+-- src/                           # Core Python modules
+-- backend/                       # FastAPI backend
|   +-- app/routers/              # API route handlers
|   +-- app/services/             # Business logic
|   +-- app/models/               # Pydantic models
|   +-- app/core/                 # Security, monitoring
|   +-- tests/                    # Backend tests (713)
+-- web-dashboard/                 # Next.js frontend
|   +-- app/                      # Next.js app directory
|   +-- components/               # React components
|   +-- tests/e2e/                # Playwright E2E tests
+-- tests/                        # Integration tests
+-- docs/                         # Documentation
+-- scripts/                      # Utility scripts
+-- nginx/                        # Nginx reverse proxy config
+-- monitoring/                   # Prometheus + Grafana
+-- docker-compose.yml            # Dev environment
+-- docker-compose.prod.yml       # Production environment (9 services)
+-- docker-compose.secure.yml     # Security-hardened
```

## Important Context

### Current Environment
- **Python**: 3.13.0 with pip 25.3 (pyenv-win)
- **Environment**: Windows shell ONLY (WSL blocked)
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000

### Known Issues
1. **WSL Environment**: Do NOT run tests from WSL. Always use Windows PowerShell/cmd.
2. **Cross-Shell Invocation**: Never call Windows venv from WSL.

---

## Kanban-UDO Integration

### Q1-Q8 Decisions (MUST preserve)

| Question | Decision |
|----------|----------|
| Q1: Task-Phase Relationship | Task within Phase (1:N) |
| Q2: Task Creation | AI Hybrid (suggest + approve) |
| Q3: Completion Criteria | Hybrid (Quality gate + user) |
| Q4: Context Loading | Double-click auto, single popup |
| Q5: Multi-Project | 1 Primary + max 3 Related |
| Q6: Archiving | Done-End + AI -> Obsidian |
| Q7: Dependencies | Hard Block + Emergency override |
| Q8: Accuracy vs Speed | Accuracy first + Adaptive |

### Key Performance Targets
- Database queries: <50ms (1,000 tasks)
- API endpoints: p95 <500ms
- UI initial load: TTI <3s, FCP <1s, LCP <2.5s
- WebSocket latency: <50ms
- AI suggestion: <3s

### Rollback Strategy
- **Tier 1**: Feature flag disable (immediate)
- **Tier 2**: Git revert + redeploy (1 minute)
- **Tier 3**: Database restore from backup (5 minutes)

---

## Current Status (2026-01-29)

**Phase**: Production Ready
**Backend Tests**: 713/713 passing (100%)
**User Testing**: 4.3/5.0 (target 4.0 PASS)
**Production Infrastructure**: Complete (10 files)

### Production Documents
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md` - 10-step deployment
- `docs/SECURITY_AUDIT_CHECKLIST.md` - 103 items, 10 categories
- `docs/ROLLBACK_PROCEDURES.md` - 3-tier rollback strategy

### Next Steps
1. Production Deployment (follow PRODUCTION_DEPLOYMENT_GUIDE.md)
2. Mobile responsive design (Week 9+)
3. i18n multi-language support (Week 9+)
4. Offline mode with Service Worker (Week 9+)
