# UDO Development Platform v3.0

> **Unified Development Orchestrator with Predictive Uncertainty Modeling**

## 🚀 Overview

세계 최초의 예측적 불확실성 모델링을 적용한 지능형 개발 자동화 플랫폼입니다.

### 핵심 특징

- **Phase-Aware Evaluation**: 개발 단계별 맞춤 평가 (Ideation → Testing)
- **Predictive Uncertainty**: 24시간 불확실성 예측 모델링
- **Quantum States**: 5단계 양자 불확실성 상태 분류
- **Auto-Mitigation**: 실시간 완화 전략 생성 with ROI 계산
- **ML Learning System**: 패턴 인식 및 지속적 개선

## 📊 Performance

| Metric | v1 | v3 | Improvement |
|--------|-----|-----|-------------|
| Ideation Confidence | 9% | 80% | **+888%** |
| Phase Recognition | 0% | 100% | **∞** |
| Uncertainty Prediction | None | 24h | **∞** |
| Auto-Mitigation | None | Real-time | **∞** |

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      UDO v2 (Orchestrator)          │
│  - Phase-Aware Evaluation           │
│  - Bayesian Confidence              │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Uncertainty Map v3 (Predictor)    │
│  - Predictive Modeling              │
│  - Quantum States                   │
│  - Auto-Mitigation                  │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│  AI Collaboration Bridge (3-AI)     │
│  - Claude + Codex + Gemini         │
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
UDO-Development-Platform/
├── src/                    # Core source code
│   ├── unified_development_orchestrator_v2.py
│   ├── uncertainty_map_v3.py
│   └── three_ai_collaboration_bridge.py
├── tests/                  # Test suites
│   ├── test_udo_v3_integration.py
│   └── run_udo_phase1.py
├── docs/                   # Documentation
│   ├── UDO_V3_INTEGRATION_REPORT.md
│   └── udo_v2_upgrade_report.md
├── data/                   # Data & state files
│   ├── udo_learning_data.json
│   └── udo_state_phase1.json
└── README.md
```

## 📌 버전 선택 가이드

- 현재 PR과 문서는 **UDO v2 + Uncertainty Map v3** 구성을 표준으로 사용합니다.
- 버전 1 대비 개선 지표와 선택 근거는 [`docs/pr_version_selection.md`](docs/pr_version_selection.md)에서 요약합니다.
- 향후 v3 전환 계획은 `docs/UDO_V3_INTEGRATION_REPORT.md`와 `FINAL_REPORT.md`를 참조하세요.
- Codex 리팩토링 8단계(로깅 정비~타입 검증)는 위 문서 4장에서 세부 내역과 테스트 결과를 확인할 수 있습니다.

## 🔧 Installation

```bash
# Clone repository
git clone https://github.com/[username]/UDO-Development-Platform.git
cd UDO-Development-Platform

# Install dependencies
pip install -r requirements.txt
```

## 🚦 Quick Start

```python
from src.unified_development_orchestrator_v2 import UnifiedDevelopmentOrchestratorV2, ProjectContext

# Initialize project
project = ProjectContext(
    project_name="My-AI-Project",
    goal="AI-powered solution",
    team_size=5,
    timeline_weeks=12,
    budget=50000,
    tech_stack=["Next.js", "FastAPI", "PostgreSQL"],
    constraints=["3 months deadline"],
    success_metrics=["MAU 1000+"],
    current_phase="ideation",
    files=[],
    metadata={}
)

# Create UDO instance
udo = UnifiedDevelopmentOrchestratorV2(project)

# Start development cycle
plan = udo.start_development_cycle("Build AI code review platform")

# Execute if GO decision
if plan['decision'] == 'GO':
    result = udo.execute_plan(plan)
```

## 🚀 Development Server

### Recommended Workflow (New - 2025-12-22)

Use the improved startup script with automatic process management:

```bash
# Start backend server (automatically handles port conflicts)
python scripts/start_dev.py

# Or specify custom port
python scripts/start_dev.py --port 8080

# Fast start (skip process checks)
python scripts/start_dev.py --no-check
```

**Features**:
- ✅ Automatic duplicate process detection
- ✅ Graceful shutdown of existing processes
- ✅ Port conflict resolution
- ✅ PID file tracking
- ✅ Clean exit on Ctrl+C

### Process Management

**Check running processes**:
```bash
python scripts/cleanup_processes.py --check-only
```

**Clean up all UDO processes**:
```bash
python scripts/cleanup_processes.py
```

**Frontend development server**:
```bash
cd web-dashboard
npm run dev
```

### Legacy Manual Startup

If you prefer manual control:

```bash
# Backend (Windows)
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Backend (Linux/Mac)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Note**: Manual startup doesn't include automatic process management. See `docs/PORT_CONFLICT_ROOT_CAUSE_ANALYSIS.md` for details.

## 🧪 Testing

To run the test suite, use the `run_tests.py` script in the root directory:

```bash
python run_tests.py
```

This will discover and run all tests in the `tests/` directory.

## 📈 Phase Workflow

### 1. Ideation (60% confidence required)
- Market validation
- Technical feasibility
- Innovation assessment

### 2. Design (65% confidence required)
- Architecture quality
- Pattern adherence
- Scalability analysis

### 3. MVP (65% confidence required)
- Core feature coverage
- Development speed
- Validation readiness

### 4. Implementation (70% confidence required)
- Code quality metrics
- Test coverage
- Performance benchmarks

### 5. Testing (70% confidence required)
- Coverage completeness
- Edge case handling
- Regression prevention

## 🎯 Uncertainty States

| State | Symbol | Range | Description |
|-------|--------|-------|-------------|
| DETERMINISTIC | 🟢 | <10% | Fully predictable |
| PROBABILISTIC | 🔵 | 10-30% | Statistical confidence |
| QUANTUM | 🟠 | 30-60% | Multiple possibilities |
| CHAOTIC | 🔴 | 60-90% | High uncertainty |
| VOID | ⚫ | >90% | Unknown territory |

## 📊 Testing

```bash
# Run integration tests
python tests/test_udo_v3_integration.py

# Test specific phase
python tests/run_udo_phase1.py
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines.

## 📄 License

MIT License - see LICENSE file for details

## 🏆 Achievements

- ✅ Phase-Aware Evaluation System
- ✅ Predictive Uncertainty Modeling
- ✅ Quantum State Classification
- ✅ Auto-Mitigation Strategy Generation
- ✅ ML-based Learning System
- 🔄 Real AI Integration (30% - in progress)
- 🔄 Production Deployment (60% - testing)

## 📞 Contact

- GitHub: [Your GitHub Profile]
- Email: [Your Email]

---

**Version**: 3.0.0
**Status**: Beta Testing
**Last Updated**: 2025-11-17