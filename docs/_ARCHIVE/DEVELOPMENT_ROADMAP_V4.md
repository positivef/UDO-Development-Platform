# UDO Platform 개발 로드맵 v4.1

**Date**: 2025-12-06 (Updated)
**Framework**: Toyota-Deming Hybrid (Pre-mortem + 5 Whys + Ishikawa + A3 + PDCA)
**Priority**: 안정성 > 완성도 > 토큰 최적화
**Status**: Final - Claude Code 구현 준비 완료

---

## 🎯 프로젝트 핵심 목적 (Project Purpose)

> **UDO (Unified Development Orchestrator) v3.0**은 **예측적 불확실성 모델링**을 통해 프로젝트 위험을 **사전에 예측하고 완화**하는 지능형 개발 자동화 플랫폼입니다.

### Core Innovation

| 핵심 기능 | 역할 | 구현 상태 |
|----------|------|----------|
| **UDO v2 Orchestrator** | The "Brain" - Phase-aware 의사결정 | ✅ 95% 완료 |
| **Uncertainty Map v3** | The "Prophet" - 24시간 예측 | ✅ 100% 완료 |
| **AI Collaboration Bridge** | The "Team" - 3-AI 오케스트레이션 | ⚠️ 30% 완료 |
| **Time Tracking System** | The "Accountant" - ROI 측정 | ✅ 85% 완료 |
| **Web Dashboard** | The "Cockpit" - 실시간 시각화 | ⚠️ 50% 완료 |

### Success Metrics (목표)

```yaml
전체 완성도: 45% → 85% (4주)
AI 자동화율: 60% → 95%
에러 자동 해결: 70% (Tier 1: Obsidian)
설계 품질: 3x 향상 (C-K Theory)
시간 절약: 485h/년 ($24,250)
```

---

## 🔗 개발 목표와 계획 연계 (Alignment)

| 프로젝트 목표 | 로드맵 Task | Phase | 연계 확인 |
|--------------|-------------|-------|-----------|
| **95% 자동화** | CI/CD Pipeline, Pattern Library | 1, 2 | ✅ |
| **예측적 불확실성** | Uncertainty Map v3 (완료) | - | ✅ 이미 완료 |
| **3-AI 오케스트레이션** | ⚠️ **누락** → Phase 3 추가 | 3 | 🔧 추가 |
| **Phase-aware 의사결정** | UDO v2 (완료) | - | ✅ 이미 완료 |
| **ROI 측정** | Time Tracking (완료) | - | ✅ 이미 완료 |
| **실시간 시각화** | Frontend Kanban UI | 3 | ✅ |
| **Constitutional 거버넌스** | P1-P17 (완료) | - | ✅ 이미 완료 |

### 발견된 누락 항목

1. **AI Collaboration Bridge 완성** (30% → 85%) - Phase 3에 추가
2. **Obsidian 통합** (지식 보존) - Phase 2에 추가
3. **다중 모델 지원** (Claude + Codex + Gemini) - Phase 3에 추가

---

## Quick Reference (Claude Code용)

### 현재 상태 요약

| 영역 | 완료 | 진행중 | 미완료 |
|------|------|--------|--------|
| **Backend** | Kanban Archive, Constitutional Guard, Time Tracking | Router Modularization | Service Container |
| **Frontend** | Time Tracking Dashboard | - | Kanban UI, Uncertainty UI |
| **Core Systems** | UDO v2, Uncertainty Map v3 | - | AI Collaboration Bridge |
| **CI/CD** | - | - | GitHub Actions |
| **Integration** | - | - | Obsidian, Multi-Model |

### 핵심 수치

```yaml
main.py: 902줄 → 500줄 목표 (44% 감소)
CLAUDE.md: 572줄 → 300줄 목표 (48% 감소)
테스트 커버리지: 80% 목표
자동화율: 60% → 95% 목표
전체 완성도: 62% → 85% 목표
```

---

## Phase 구조 (5주) - 업데이트

```
Phase 0: Pre-mortem ──────────────────────────────── [1일]
    │   • 위험 사전 분석
    │   • 완화 전략 수립
    │
Phase 1: Stabilization ───────────────────────────── [1주]
    │   ├─ CI/CD Pipeline (P0) - 95% 자동화 기반
    │   ├─ Router Modularization (P0) - 확장성
    │   └─ Central Config (P1) - 유지보수성
    │
Phase 1.5: Gap Closure ───────────────────────────── [3일]
    │   ├─ Frontend CI (G1)
    │   ├─ Rollback Test (G7)
    │   └─ CLAUDE.md Compression (G5)
    │
Phase 2: Optimization ────────────────────────────── [2주]
    │   ├─ Pattern Library - 토큰 효율 +60%
    │   ├─ Obsidian Integration - 지식 보존 ⭐ NEW
    │   └─ Service Container (조건부)
    │
Phase 3: Expansion ───────────────────────────────── [2주]
        ├─ Frontend Kanban UI - 실시간 시각화
        ├─ AI Collaboration Bridge 완성 ⭐ NEW
        ├─ Multi-Model Support ⭐ NEW
        └─ Production Readiness
```

---

## 발견된 Gap (9개) - 업데이트

| ID | 영역 | Uncertainty | 우선순위 | 해결 | 프로젝트 목표 연계 |
|----|------|-------------|----------|------|-------------------|
| **G1** | Frontend CI 누락 | 🟠 40% | P1 | frontend-test.yml | 95% 자동화 |
| **G2** | Import 순서 의존성 | 🔴 70% | P0 | ROUTER_ORDER | 안정성 |
| **G3** | Config 롤백 불가 | 🔴 80% | P0 | USE_CENTRAL_CONFIG | 안정성 |
| **G4** | 순환 의존성 위험 | ⚫ 95% | Deferred | Phase 2 연기 | 안정성 |
| **G5** | 압축 기준 미정의 | 🔵 20% | P2 | 기준 문서화 | 토큰 효율 |
| **G6** | 템플릿 검증 없음 | 🔵 25% | P2 | 3회 실사용 후 승인 | 토큰 효율 |
| **G7** | 롤백 테스트 없음 | 🟠 50% | P1 | rollback-test.yml | 안정성 |
| **G8** | AI Bridge 미완성 | 🟠 45% | P2 | Phase 3 ⭐ NEW | 3-AI 오케스트레이션 |
| **G9** | Obsidian 미연동 | 🔵 30% | P2 | Phase 2 ⭐ NEW | 지식 보존 |

---

## Phase 1: Stabilization 상세

### Task 1: CI/CD Pipeline (Day 1-2)

**목표와 연계**: 95% AI 자동화 달성의 기반

**파일 생성**:
```
.github/workflows/
├── backend-test.yml
├── frontend-test.yml
└── rollback-test.yml
```

**backend-test.yml**:
```yaml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install -r requirements.txt
      - run: pytest --cov=backend --cov-fail-under=80
      - run: bandit -r backend/
```

**frontend-test.yml**:
```yaml
name: Frontend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - working-directory: web-dashboard
        run: |
          npm ci
          npm run lint
          npm run build
```

---

### Task 2: Router Modularization (Day 3-4)

**목표와 연계**: 확장성 확보 (50개 → 100개 라우터)

**파일 생성**: `backend/app/routers/__init__.py`

```python
"""
Router Registry - 롤백 가능한 라우터 등록 시스템

목표 연계: 
  - 확장성: 신규 라우터 추가 5분 이내
  - 안정성: 3-Tier Rollback

Rollback:
  Tier 1: USE_ROUTER_REGISTRY=false (즉시)
  Tier 2: DISABLE_ROUTERS=kanban_tasks (선택적)
  Tier 3: git revert (완전)
"""
import os
import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# G2 해결: Import 순서 명시
ROUTER_ORDER = [
    "auth",
    "uncertainty",       # Core: Uncertainty Map v3
    "quality_metrics",
    "time_tracking",     # Core: ROI Measurement
    "kanban_tasks",
    "kanban_dependencies",
    "kanban_projects",
    "kanban_context",
    "kanban_ai",
    "kanban_archive",
]


class RouterRegistry:
    def __init__(self):
        self.registered = []
        self.failed = []

    def register(self, app: FastAPI):
        if os.getenv("USE_ROUTER_REGISTRY", "true") == "false":
            logger.warning("Router registry disabled")
            return self._legacy_import(app)

        disabled = os.getenv("DISABLE_ROUTERS", "").split(",")

        for name in ROUTER_ORDER:
            if name in disabled:
                logger.info(f"Skipped: {name}")
                continue
            try:
                module = __import__(
                    f"backend.app.routers.{name}", fromlist=["router"]
                )
                app.include_router(getattr(module, "router"))
                self.registered.append(name)
            except Exception as e:
                logger.error(f"Failed {name}: {e}")
                self.failed.append(name)

    def _legacy_import(self, app: FastAPI):
        from backend.app.routers.uncertainty import router
        app.include_router(router)


def register_all_routers(app: FastAPI):
    registry = RouterRegistry()
    registry.register(app)
    return registry
```

---

### Task 3: Central Config (Day 5)

**목표와 연계**: 환경별 설정 분리, 유지보수성 향상

**파일 생성**: `backend/app/config.py`

```python
"""
Central Config Module - 중앙 설정 관리

목표 연계:
  - 12-Factor App 원칙
  - 환경별 설정 분리 (.env)
  - Feature Flag 기반 롤백

Rollback:
  USE_CENTRAL_CONFIG=false → 기존 변수 사용
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # Logging
    log_level: str = "INFO"
    
    # Database
    database_url: str = "sqlite:///./udo.db"
    
    # Feature Flags
    use_router_registry: bool = True
    kanban_enabled: bool = True
    use_central_config: bool = True
    ai_collaboration_enabled: bool = True  # For G8

    class Config:
        env_file = ".env"
        case_sensitive = False


# G3 해결: Feature Flag로 롤백 가능
if os.getenv("USE_CENTRAL_CONFIG", "true") == "true":
    settings = Settings()
    ALLOWED_ORIGINS = settings.allowed_origins
    LOG_LEVEL = settings.log_level
    DATABASE_URL = settings.database_url
else:
    ALLOWED_ORIGINS = ["http://localhost:3000"]
    LOG_LEVEL = "INFO"
    DATABASE_URL = "sqlite:///./udo.db"
```

---

## Phase 2: Optimization 상세 (업데이트)

### Task 4: Pattern Library

**목표와 연계**: 토큰 효율 +60%, 개발 속도 +30%

### Task 5: Obsidian Integration ⭐ NEW

**목표와 연계**: 지식 보존 95%, 에러 자동 해결 70%

```python
# backend/app/services/obsidian_service.py (기존)
# 이미 구현됨 - 연동 활성화 필요

"""
Obsidian Integration - Second Brain

목표:
  - 지식 보존: 95%
  - 에러 자동 해결: 70% (Tier 1)
  - 컨텍스트 유실 방지
"""
```

**활성화 Task**:
- [ ] Obsidian 경로 설정 (.env)
- [ ] 자동 로그 파이프라인 활성화
- [ ] 3-Tier 에러 해결 연동

---

## Phase 3: Expansion 상세 (업데이트)

### Task 6: Frontend Kanban UI

**목표와 연계**: 실시간 시각화 (The "Cockpit")

### Task 7: AI Collaboration Bridge 완성 ⭐ NEW

**목표와 연계**: 3-AI 오케스트레이션 (The "Team")

```python
# src/three_ai_collaboration_bridge.py (기존)
# 현재 30% 완료 - 85%로 확장

"""
AI Collaboration Bridge - The Team

목표:
  - Claude: Creative (설계 대안)
  - Codex: Implementation (코드 생성)
  - Gemini: Validation (검증)
  
현재 구현:
  - ✅ Claude 연동
  - ⚠️ Codex 부분 연동
  - ❌ Gemini 미연동
"""
```

**Task**:
- [ ] Codex MCP 완전 연동
- [ ] Gemini API 연동
- [ ] Multi-model fallback 구현
- [ ] Constitutional voting 메커니즘

### Task 8: Multi-Model Support ⭐ NEW

**목표와 연계**: GitHub Copilot 스타일 다중 모델

```yaml
Multi-Model Strategy:
  Primary: Claude (Creative Thinking)
  Secondary: Codex (Implementation)
  Tertiary: Gemini (Validation)
  Fallback: Single AI Mode
```

---

## 3-Tier Rollback 전략

| 변경 | Tier 1 (초) | Tier 2 (분) | Tier 3 (시간) |
|------|-------------|-------------|---------------|
| Router Registry | `USE_ROUTER_REGISTRY=false` | `DISABLE_ROUTERS=X` | `git revert` |
| Central Config | `USE_CENTRAL_CONFIG=false` | 기존 변수 사용 | `git revert` |
| Service Container | `USE_SERVICE_CONTAINER=false` | `legacy_create()` | `git revert` |
| AI Collaboration | `AI_COLLABORATION_ENABLED=false` | Single AI | `git revert` |
| CI/CD | 워크플로우 삭제 | threshold 조정 | Actions 비활성화 |

---

## 검증 체크리스트 (각 Task 전)

```yaml
Before Implementation:
  - [ ] Why: 왜 필요한가? (프로젝트 목표와 연계)
  - [ ] What: 무엇을 하는가?
  - [ ] Solution: 어떻게 구현하는가?
  - [ ] Side Effects: 부작용 3개 이상 식별
  - [ ] Rollback: 3-Tier 롤백 전략
  - [ ] Uncertainty: 양자 상태 분류
  - [ ] Goal Alignment: 프로젝트 핵심 목표와 일치 여부 ⭐ NEW

After Implementation:
  - [ ] Tests: 단위 테스트 추가
  - [ ] Coverage: 80% 이상
  - [ ] Rollback Test: 환경변수로 롤백 테스트
  - [ ] PDCA Check: 목표 대비 달성도
```

---

## KPI 대시보드

| 지표 | 현재 | W1 | W2 | W3 | W5 | 목표 |
|------|------|-----|-----|-----|-----|------|
| 전체 완성도 | 62% | 68% | 75% | 80% | 85% | 85% |
| 자동화율 | 60% | 75% | 80% | 85% | 95% | 95% |
| 토큰 효율 | 100% | 120% | 140% | 150% | 160% | 160% |
| CI/CD Score | 3/10 | 7/10 | 8/10 | 9/10 | 10/10 | 10/10 |
| Gap 해결 | 0/9 | 4/9 | 6/9 | 8/9 | 9/9 | 9/9 |
| AI Bridge | 30% | 30% | 50% | 70% | 85% | 85% |

---

## 프로젝트 핵심 목표 달성 체크리스트

```yaml
95% AI 자동화:
  - [ ] CI/CD Pipeline 완성
  - [ ] Pattern Library 구축
  - [ ] 3-AI Orchestration 활성화

예측적 불확실성:
  - [x] Uncertainty Map v3 완료 ✅
  - [ ] 프론트엔드 연동

3-AI 오케스트레이션:
  - [x] Claude 연동 ✅
  - [ ] Codex MCP 완전 연동
  - [ ] Gemini API 연동

지식 보존:
  - [x] Obsidian Service 구현 ✅
  - [ ] 자동 로그 파이프라인 활성화
  - [ ] 3-Tier 에러 해결 연동

Constitutional 거버넌스:
  - [x] P1-P17 완료 ✅
  - [x] ConstitutionalGuard 완료 ✅
  - [ ] Multi-AI voting 메커니즘
```

---

## Claude Code 즉시 시작 가능 Task

### 오늘 시작 (P0)

1. **CI/CD Pipeline** - 95% 자동화 기반
2. **Router Registry** - 확장성 확보
3. **Central Config** - 유지보수성 향상

### 성공 기준

- [ ] CI 워크플로우 3개 생성
- [ ] 모든 테스트 통과
- [ ] main.py 500줄 이하
- [ ] 롤백 테스트 통과
- [ ] 프로젝트 핵심 목표와 일치 확인

---

## 참고 문서

| 문서 | 위치 | 용도 |
|------|------|------|
| CLAUDE.md | 프로젝트 루트 | Claude Code 메인 가이드 |
| USER_SCENARIOS.md | docs/ | 프로젝트 핵심 목적 |
| Uncertainty Map v3 | src/uncertainty_map_v3.py | 예측적 불확실성 |
| 본 문서 | docs/DEVELOPMENT_ROADMAP_V4.md | 개발 로드맵 |

---

## 즉시 실행 명령어 (Claude Code용)

```bash
# 1. 환경 확인
.venv\Scripts\python.exe -m pytest tests/ -v

# 2. 백엔드 시작
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload

# 3. 프론트엔드 시작
cd web-dashboard && npm run dev

# 4. 롤백 테스트
USE_ROUTER_REGISTRY=false pytest tests/
USE_CENTRAL_CONFIG=false pytest tests/
```
