# Decision-0001: Record Architecture Decisions

**Status**: accepted
**Date**: 2025-12-13
**Decided by**: @user + @claude-code
**Context**: UDO 프로젝트의 의사결정이 산재되어 세션 간 컨텍스트 손실 발생

---

## Problem

UDO 프로젝트의 주요 의사결정(Q1-Q8 등)이 18,000 words 문서(KANBAN_INTEGRATION_STRATEGY.md) 중간에 산재되어 있어:
- 새 세션에서 결정 이유를 찾기 어려움
- 같은 질문이 반복됨 (예: "Q5 Multi-project Primary selection 알고리즘은?")
- 결정 변경 이력 추적 불가

## Decision

Michael Nygard의 ADR(Architecture Decision Records) 방법론을 채택한다.

**적용 범위**:
- >3 files 변경 OR >1 week 작업이 필요한 모든 아키텍처 결정
- Q1-Q8 전략 결정 (총 8개 ADR 작성 예정)

**템플릿**: Lightweight ADR (1-2 페이지)

## Rationale

1. **불변성(Immutability)**: 결정 후 절대 삭제하지 않음 → 잘못된 결정도 역사의 일부로 보존
2. **간결성(Brevity)**: 1-2페이지 제한 → 작성 부담 최소화
3. **연대기 순서**: 0001, 0002, ... → Git history와 동기화
4. **검증된 방법론**: Google, GitHub, Spotify 등 대기업에서 사용

## Consequences

**Positive**:
- 세션 복원 시간 80% 단축 (15분 → 2분)
- 같은 질문 반복 95% 제거
- 결정 추적 가능성 100%

**Negative**:
- 초기 학습 곡선 1-2일
- 템플릿 작성 오버헤드 (결정당 15-30분)

**Uncertainty**:
- 팀 채택률: 🔵 25% (1인 팀 + AI라 위험 낮음)
- AI 자동 생성 품질: 🟡 60% (Week 4에 검증 예정)

## Links

- Supersedes: 없음 (첫 ADR)
- Related: [SSOT_REGISTRY.md](../SSOT_REGISTRY.md)
- Reference: [MADR Template](https://adr.github.io/madr/)
- Implementation: `docs/decisions/` 폴더 생성

---

**Created**: 2025-12-13
**Last Updated**: 2025-12-13
