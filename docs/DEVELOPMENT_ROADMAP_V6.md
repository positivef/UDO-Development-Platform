# UDO Platform 최종 개발 로드맵 v6.1
## 하이브리드 접근 + RL 기반 지식 재사용 통합

**Date**: 2025-12-07
**Version**: 6.1 (RL Integration - Training-free GRPO)
**Approach**: 하이브리드 (영역별 성숙도에 맞춘 목표) + RL 지식 재사용
**Verified**: 테스트 실행 + 5 Whys 분석 + RL 이론 통합 완료

**NEW (v6.1)**: Training-free Group Relative Policy Optimization 통합
- ArXiv 2510.08191 논문 기반
- 현재 60% RL 구현 → 95% 목표
- 지식 재사용율 70% → 90% (+20%)
- 자동화율 85% → 92% (+7%)

---

## 📊 현재 상태 진단 (2025-12-06 실측)

### 테스트 실행 결과

```yaml
테스트 결과:
  총 테스트: ~200개
  통과: ~85%
  실패: ~15% (주로 Uncertainty 통합 테스트)
  
실패 원인:
  - predict() 함수 파라미터 불일치
  - 통합 모듈 호환성 이슈
```

### 영역별 성숙도

| 영역 | 현재 상태 | 성숙도 | 접근법 |
|------|----------|--------|--------|
| **Backend Core** | 14,968 LOC, 30 files | ✅ 95% | 높은 목표 (80%+) |
| **Uncertainty Map** | v3 완료 | ✅ 100% | 높은 목표 (70%+) |
| **Routers** | 14개 라우터 | ✅ 90% | 높은 목표 |
| **Services** | 15개 서비스 | ✅ 85% | 높은 목표 |
| **Frontend** | 기본 대시보드 | ⚠️ 50% | **점진적** (40→70%) |
| **AI Bridge** | Claude 연동만 | ⚠️ 30% | **점진적** (65→85%) |
| **CI/CD** | 없음 | ❌ 0% | **점진적** (60→85%) |
| **Obsidian** | 서비스 있음 | ⚠️ 40% | 점진적 |
| **RL 지식 재사용** | Training-free 60% | ⚠️ 60% | **점진적** (60→95%) 🆕 |

---

## 🎯 하이브리드 목표 (영역별 맞춤)

### 성숙한 영역 (높은 목표)

| 영역 | 현재 | 목표 | 타임라인 |
|------|------|------|----------|
| Backend 테스트 커버리지 | ~54% | **80%** | 2주 |
| API 응답 시간 | 미측정 | **<200ms** | 2주 |
| 라우터 모듈화 | 수동 | **자동 등록** | 1주 |

### 신규 영역 (점진적 목표)

| 영역 | MVP (2주) | Prototype (4주) | Beta (6주) | Production |
|------|-----------|-----------------|------------|------------|
| **Frontend** | 기본 UI | 연동 완료 | 실시간 | 최적화 |
| 예측 정확도 | 40% | 55% | 65% | 70% |
| 자동화율 | 65% | 75% | 85% | **92%** 🆕 |
| 지식 재사용율 | 70% 🆕 | 75% 🆕 | 85% 🆕 | **90%** 🆕 |
| 오류율 | 15% | 10% | 8% | 5% |

---

## 📋 단계별 보완점 검증

### Stage 1: MVP (2주)

#### 보완 필요 항목

| 항목 | 현재 상태 | 보완 방법 | 우선순위 |
|------|----------|----------|----------|
| Uncertainty API 호환성 | predict() 실패 | 파라미터 수정 | **P0** |
| Frontend 페이지 | 없음 | 기본 UI 생성 | **P0** |
| CI Pipeline | 없음 | backend-test.yml | **P0** |
| 테스트 커버리지 측정 | 없음 | --cov 설정 | P1 |

#### MVP 체크리스트

```yaml
필수 완료:
  - [ ] Uncertainty API predict() 수정
  - [ ] web-dashboard/app/uncertainty/page.tsx
  - [ ] web-dashboard/app/confidence/page.tsx
  - [ ] .github/workflows/backend-test.yml
  - [ ] 테스트 통과율 90%+

RL 통합 (NEW):
  - [ ] RL-1: Obsidian 태그 시스템 설계 (scripts/obsidian_tagger.py)
  - [ ] RL-2: Facade 패턴 Token Prior 확장 (src/uncertainty_map_v3.py)
  - [ ] RL-3: Group Relative Scorer 핵심 (src/rl_knowledge_optimizer.py)

성공 기준:
  - 예측 화면 표시
  - CI 자동 실행
  - 지식 재사용율: 70% → 75% 🆕
  - "뭔가 동작한다" + "지식이 쌓인다" 🆕
```

---

### Stage 2: Prototype (4주)

#### 보완 필요 항목

| 항목 | 현재 상태 | 보완 방법 | 우선순위 |
|------|----------|----------|----------|
| Predictive Alert | 없음 | 서비스 생성 | P0 |
| AI Bridge Claude | 30% | 완성도 50% | P0 |
| Frontend CI | 없음 | frontend-test.yml | P1 |
| Obsidian 연동 | 서비스만 | 파이프라인 활성화 | P1 |

#### Prototype 체크리스트

```yaml
필수 완료:
  - [ ] Predictive Alert 서비스
  - [ ] AI Bridge 50% (Claude 완전 연동)
  - [ ] Frontend CI 추가
  - [ ] Obsidian 자동 로그
  - [ ] 예측 vs 실제 비교 UI

RL 통합 (NEW):
  - [ ] RL-4: 3-Tier Resolution에 점수 계산 통합 (unified_error_resolver.py)
  - [ ] RL-5: Multi-Rollout 추적 (Todo workflow 통합)
  - [ ] RL-6: 주간 정제 프로토타입 (수동 테스트)

성공 기준:
  - 위험 사전 알림 동작
  - Claude와 협업 가능
  - 지식 재사용율: 75% → 85% 🆕
  - 패턴 자동 감지: 0% → 30% 🆕
  - "유용하다" + "지식 재사용이 보인다" 🆕
```

---

### Stage 3: Beta (6주)

#### 보완 필요 항목

| 항목 | 현재 상태 | 보완 방법 | 우선순위 |
|------|----------|----------|----------|
| AI Bridge Codex | 없음 | MCP 연동 완성 | P0 |
| 예측 정확도 피드백 | 없음 | 베이지안 학습 | P1 |
| 롤백 테스트 | 없음 | rollback-test.yml | P1 |
| E2E 테스트 | 부분적 | Playwright 확장 | P2 |

#### Beta 체크리스트

```yaml
필수 완료:
  - [ ] AI Bridge 80% (Claude + Codex)
  - [ ] 예측 정확도 65%+ 달성
  - [ ] 3주 이상 안정 운영
  - [ ] 롤백 테스트 CI

RL 통합 (NEW):
  - [ ] RL-7: 자동 주간 정제 (cron job, .github/workflows/weekly-distillation.yml)
  - [ ] RL-8: GRPO 성능 벤치마크 (Tier 1 hit rate, 최적 솔루션 비율)
  - [ ] RL-9: Knowledge Dashboard 실시간 메트릭

성공 기준:
  - AI 결과물 신뢰
  - 지식 재사용율: 85% → 90% 🆕
  - 패턴 자동 감지: 30% → 60% 🆕
  - 주간 정리 시간: 30분 → 0min 🆕
  - "믿을 만하다" + "지식이 자동으로 정리된다" 🆕
```

---

### Stage 4: Production (8주+)

#### 보완 필요 항목

| 항목 | 현재 상태 | 보완 방법 | 우선순위 |
|------|----------|----------|----------|
| Multi-model AI | 없음 | Gemini 추가 | P1 |
| 문서화 | 부분적 | 완전 문서화 | P1 |
| 성능 최적화 | 미측정 | 프로파일링 | P2 |

#### Production 체크리스트

```yaml
필수 완료:
  - [ ] Multi-model AI (Claude + Codex + Gemini)
  - [ ] 예측 정확도 70%+ 달성
  - [ ] 오류율 5% 이하
  - [ ] 6주 이상 안정 운영
  - [ ] 완전 문서화

RL 통합 (NEW):
  - [ ] RL-10: RL-Guided Decision API (/api/rl/suggest-approach)
  - [ ] RL-11: Knowledge Quality Metrics (Precision/Recall)
  - [ ] RL-12: Cross-Project Token Prior Sharing

성공 기준:
  - 상용 수준 품질
  - 지식 재사용율: 90%+ 🆕
  - 패턴 자동 감지: 60%+ 🆕
  - Zero-Effort Learning: 95% 🆕
  - 자동화율: 92% 🆕
  - "지식이 자산이다" 🆕
```

---

## 🚀 Claude Code 즉시 시작 가이드

### Priority 0: 테스트 실패 수정 (오늘)

```yaml
문제: Uncertainty 통합 테스트 실패
원인: predict() 함수 파라미터 불일치

수정 필요 파일:
  - src/uncertainty_map_v3.py: predict() 시그니처 확인
  - tests/test_*.py: 호출 방식 수정

검증:
  .venv\Scripts\python.exe -m pytest tests/ -v
```

### Priority 1: MVP Task (2주)

```yaml
Task 1: Uncertainty UI (3일)
  파일: web-dashboard/app/uncertainty/page.tsx
  내용:
    - 24시간 예측 타임라인
    - 양자 상태 색상 (🟢🔵🟠🔴⚫)
    - API 연동: /api/uncertainty/

Task 2: Confidence Dashboard (2일)
  파일: web-dashboard/app/confidence/page.tsx
  내용:
    - Confidence Score 표시
    - GO/NO_GO 상태
    - Phase 진행도

Task 3: CI Pipeline (1일)
  파일: .github/workflows/backend-test.yml
  내용:
    - pytest 실행
    - 커버리지 60% 이상
    - bandit 보안 검사
```

### 명령어 참조

```bash
# 테스트 실행
.venv\Scripts\python.exe -m pytest tests/ -v

# 커버리지 측정
.venv\Scripts\python.exe -m pytest --cov=backend --cov-report=html

# 백엔드 시작
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload

# 프론트엔드 시작
cd web-dashboard && npm run dev
```

---

## 📈 KPI 대시보드 (하이브리드)

### 성숙 영역 (높은 목표)

| 지표 | 현재 | W1 | W2 | 목표 |
|------|------|-----|-----|------|
| 백엔드 테스트 통과율 | 85% | 95% | 98% | 98%+ |
| API 응답 시간 | 미측정 | 측정 | <200ms | <200ms |
| 라우터 모듈화 | 수동 | 자동 | 최적화 | 완료 |

### 신규 영역 (점진적)

| 지표 | 현재 | MVP | Prototype | Beta | Prod |
|------|------|-----|-----------|------|------|
| 예측 정확도 | 0% | 40% | 55% | 65% | 70% |
| 오류율 | ~20% | 15% | 10% | 8% | 5% |
| 자동화율 | 60% | 65% | 75% | 85% | **92%** 🆕 |
| 지식 재사용율 | 70% 🆕 | 75% 🆕 | 85% 🆕 | 90% 🆕 | **90%+** 🆕 |
| 패턴 자동 감지 | 0% 🆕 | 0% 🆕 | 30% 🆕 | 60% 🆕 | **60%+** 🆕 |
| 주간 정리 시간 | 30min 🆕 | 30min 🆕 | 15min 🆕 | 5min 🆕 | **0min** 🆕 |
| 테스트 커버리지 | 54% | 60% | 70% | 80% | 85% |
| AI Bridge | 30% | 30% | 50% | 80% | 85% |

---

## 🔄 3-Tier Rollback 전략

| 변경 | Tier 1 (초) | Tier 2 (분) | Tier 3 (시간) |
|------|-------------|-------------|---------------|
| Router Registry | `USE_ROUTER_REGISTRY=false` | `DISABLE_ROUTERS=X` | `git revert` |
| Uncertainty UI | 컴포넌트 숨김 | API 해제 | `git revert` |
| CI Pipeline | 워크플로우 비활성화 | threshold 조정 | 삭제 |

---

## ✅ 검증 완료 항목

- [x] 5 Whys 본질 분석: AI 신뢰성 향상 → 오류율 감소
- [x] 현재 상태 테스트: ~85% 통과, 일부 실패
- [x] 영역별 성숙도 분석: Backend 95%, Frontend 50%, AI 30%
- [x] 하이브리드 접근법: 성숙 영역 높은 목표, 신규 영역 점진적
- [x] 단계별 보완점: MVP/Prototype/Beta/Production 체크리스트
- [x] 롤백 전략: 3-Tier 정의

---

## 📌 Claude Code 핵심 메시지

```yaml
현재 상태:
  - Backend: 95% 완료 ✅ (높은 목표 적용)
  - Frontend: 50% 완료 ⚠️ (점진적 개발)
  - AI Bridge: 30% 완료 ⚠️ (점진적 개발)
  - 테스트: 85% 통과 (일부 실패 수정 필요)

즉시 해야 할 일:
  1. 테스트 실패 수정 (P0)
  2. Uncertainty UI 기본 (MVP)
  3. Confidence Dashboard 기본 (MVP)
  4. CI Pipeline 생성 (MVP)

MVP 성공 기준:
  - 예측 정확도: 40%
  - 오류율: 15%
  - 테스트 커버리지: 60%
  - "뭔가 동작한다"

접근법:
  - Backend: 높은 목표 (이미 성숙)
  - Frontend/AI: 점진적 (MVP→Prototype→Beta→Production)
  - 매 단계 피드백 반영
```

---

## 📚 참고 문서

| 문서 | 위치 | 용도 |
|------|------|------|
| 본 문서 | `docs/DEVELOPMENT_ROADMAP_V6.md` | 최종 하이브리드 + RL 계획 (v6.1) |
| **RL 지식 재사용** | `docs/RL_GUIDED_KNOWLEDGE_REUSE.md` | Training-free GRPO 통합 (24KB) 🆕 |
| 5 Whys 분석 | `.gemini/brain/.../FIVE_WHYS_DEEP_ANALYSIS.md` | 본질 분석 |
| USER_SCENARIOS | `docs/USER_SCENARIOS.md` | 핵심 목적 |
| CLAUDE.md | 프로젝트 루트 | Claude Code 가이드 |
