# UDO Project Glossary (Single Source of Truth)

**Last Updated**: 2025-12-20
**Purpose**: 프로젝트 전체에서 사용하는 용어의 단일 정의 소스
**Maintainer**: @claude-code
**Related**: [SSOT_REGISTRY.md](SSOT_REGISTRY.md)

---

## Quick Reference

| Category | Terms Count | Last Updated |
|----------|-------------|--------------|
| [Completion Status](#completion-status) | 4 | 2025-12-13 |
| [Development Phases](#development-phases) | 4 | 2025-12-13 |
| [Time Units](#time-units) | 3 | 2025-12-13 |
| [Architecture Terms](#architecture-terms) | 6 | 2025-12-13 |
| [AI Collaboration](#ai-collaboration) | 4 | 2025-12-13 |
| [Quality Metrics](#quality-metrics) | 5 | 2025-12-13 |

---

## Completion Status

프로젝트 완료 상태를 나타내는 용어들. **순서대로 진행**됨.

| Term | Definition | Criteria | Example |
|------|------------|----------|---------|
| **Code Complete** | 기능 코드 작성 완료 | 컴파일/실행 가능 | "obsidian_service.py Code Complete" |
| **Test Verified** | 테스트 검증 완료 | 커버리지 60%+ | "Test Verified (coverage: 65%)" |
| **Integration Ready** | 연동 테스트 완료 | 실제 시스템 연동 성공 | "Obsidian MCP Integration Ready" |
| **Production Ready** | 프로덕션 준비 완료 | 6주+ 안정 운영 | "Kanban UI Production Ready" |

**Usage Rules**:
- "완료"라고만 표기하지 말 것 → 반드시 위 4가지 중 하나 명시
- ADR Status에서 사용: `Status: accepted (Code Complete)`
- RFC에서 사용: `Success Criteria: [x] Test Verified`

**Anti-patterns** (사용 금지):
- ❌ "완료", "Done", "Finished" (모호함)
- ❌ "100% 완료" (기준 불명확)
- ❌ "Ready" (어떤 Ready인지 불명확)

---

## Development Phases

프로젝트 진행 단계. **MVP → Prototype → Beta → Production** 순서.

| Term | Definition | Duration | Success Criteria |
|------|------------|----------|------------------|
| **MVP** | Minimum Viable Product | 2 weeks | 기본 UI 표시, 핵심 기능 동작 |
| **Prototype** | Feature Complete | 4 weeks | 모든 기능 구현, 통합 테스트 통과 |
| **Beta** | Production-like | 6 weeks | 실사용자 테스트, 성능 최적화 |
| **Production** | Stable Release | 8 weeks+ | 6주 이상 안정 운영, 장애 0건 |

**Usage Rules**:
- 문서에서 "MVP"라고 표기 시 위 정의 기준 적용
- 각 Phase 전환 시 RFC 작성 권장

**Anti-patterns**:
- ❌ "Alpha", "Pre-release" (정의되지 않은 용어)
- ❌ "거의 완성" (모호함)

---

## Time Units

시간/진행 단위를 나타내는 용어들. **Week vs Phase vs Stage 구분 주의**.

| Term | Definition | Example | Notes |
|------|------------|---------|-------|
| **Week N** | 프로젝트 주차 (0-indexed) | Week 0 = 첫 주 | 시간 단위 |
| **Day N** | 주 내 일차 (1-indexed) | Day 1 = 월요일 | 시간 단위 |
| **Phase A/B/C** | 프로젝트 프로세스 단계 | Phase A = Design | 프로세스 단위 |
| **Stage** | 제품 성숙도 단계 | Stage: MVP | **= Development Phases** |

**Stage vs Phase 구분** (2025-12-20 추가):
- **Phase**: 프로젝트 **프로세스** 단계 (Design → Implementation → Testing)
- **Stage**: 제품 **성숙도** 수준 (MVP → Prototype → Beta → Production)
- Stage는 [Development Phases](#development-phases)와 동의어로 사용

**Usage Rules**:
- 문서 파일명: `WEEK{N}_DAY{N}_*.md` (예: WEEK1_DAY2_API.md)
- Phase는 **프로세스 단계**를 의미 (A/B/C)
- Stage는 **제품 성숙도**를 의미 (MVP/Prototype/Beta/Production)
- Week과 Phase를 혼용하지 말 것

**Phase-Week Mapping** (현재 프로젝트):
```
Phase A (Design): 2025-11-17 ~ 11-20
Phase B (Implementation): 2025-12-06 ~ 현재
  └── Week 0: Baseline (12-06 ~ 12-07)
  └── Week 1: Foundation (12-08 ~ 12-14)
  └── Week 2-4: Kanban Core
  └── Week 5-6: Database & Testing (현재: Stage MVP)
```

**Anti-patterns**:
- ❌ "WEEK_0" (언더스코어 금지, WEEK0 사용)
- ❌ "Phase Week 0" (Phase와 Week 혼용)
- ❌ Phase와 Stage 혼용 (각각 다른 의미)

---

## Architecture Terms

시스템 아키텍처 구성요소를 나타내는 용어들.

| Term | Definition | Location | Example |
|------|------------|----------|---------|
| **Service** | 비즈니스 로직 계층 | `backend/app/services/` | `quality_service.py` |
| **Router** | API 엔드포인트 정의 | `backend/app/routers/` | `quality_metrics_router.py` |
| **Model** | Pydantic 데이터 모델 | `backend/app/models/` | `KanbanTask` |
| **Component** | React UI 컴포넌트 | `web-dashboard/components/` | `TaskCard.tsx` |
| **Hook** | React Custom Hook | `web-dashboard/hooks/` | `useKanbanStore.ts` |
| **Store** | Zustand 상태 저장소 | `web-dashboard/lib/stores/` | `kanban-store.ts` |

**Usage Rules**:
- 파일명은 해당 계층 규칙을 따름
- Service는 `*_service.py`, Router는 `*_router.py`
- Component는 PascalCase (`TaskCard.tsx`)

**Anti-patterns**:
- ❌ "Module" (Service 또는 Component로 명확히)
- ❌ "Endpoint" (Router로 통일)
- ❌ "Controller" (FastAPI에서 Router 사용)

---

## AI Collaboration

AI 협업 관련 용어들.

| Term | Definition | Usage |
|------|------------|-------|
| **Session** | AI와의 단일 대화 세션 | "Session 3에서 결정됨" |
| **Handoff** | 세션 간 컨텍스트 전달 | "Session Handoff 문서 작성" |
| **ADR** | Architecture Decision Record | "ADR-0012 참조" |
| **RFC** | Request for Comments | "RFC-0003 승인됨" |

**Session Lifecycle**:
```
Session Start → Work → Checkpoint (30min) → Handoff → Session End
```

**Handoff Protocol**:
- 세션 종료 시 `docs/sessions/` 에 핸드오프 문서 생성
- 다음 세션 시작 시 이전 핸드오프 문서 참조

---

## Quality Metrics

품질 측정 관련 용어들.

| Term | Definition | Target | Measurement |
|------|------------|--------|-------------|
| **Coverage** | 테스트 커버리지 | 60%+ | `pytest --cov` |
| **Pass Rate** | 테스트 통과율 | 95%+ | `passed / total` |
| **Uncertainty** | 불확실성 수준 | <30% | Uncertainty Map v3 |
| **Confidence** | 신뢰도 수준 | >70% | Bayesian scoring |
| **TTI** | Time to Interactive | <3s | Lighthouse |

**Uncertainty Emoji Guide**:
- 🟢 DETERMINISTIC (<10%): 완전 예측 가능
- 🔵 PROBABILISTIC (10-30%): 통계적 신뢰 가능
- 🟡 QUANTUM (30-60%): 복수 가능성 존재
- 🔴 CHAOTIC (60-90%): 높은 불확실성
- ⚫ VOID (>90%): 미지 영역

---

## Maintenance

### Adding New Terms

1. 해당 카테고리 섹션에 추가
2. Definition, Criteria/Example 명확히 작성
3. Anti-patterns 추가 (있는 경우)
4. `Last Updated` 날짜 업데이트

### Term Conflict Resolution

1. 기존 용어와 충돌 시 → 기존 용어 우선
2. 새 용어 필요 시 → ADR 작성 후 추가
3. 용어 폐기 시 → `[DEPRECATED]` 표시, 대체 용어 안내

### CI/CD Validation

```yaml
# .github/workflows/glossary-check.yml
- name: Check Term Consistency
  run: python scripts/check_glossary.py
  # Scans all docs/*.md for term mismatches
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2025-12-20 | Added Stage definition, clarified Stage vs Phase distinction |
| 1.0 | 2025-12-13 | Initial glossary creation |

---

**Document Status**: Active (SSOT)
**Update Frequency**: As needed (term changes)
**Owner**: @claude-code
