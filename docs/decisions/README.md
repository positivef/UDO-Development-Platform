# Architecture Decision Records (ADRs)

**Purpose**: 프로젝트의 주요 아키텍처 결정을 불변 기록으로 보존
**Methodology**: Michael Nygard's ADR (Lightweight version)
**Template**: [adr-template.md](../templates/adr-template.md)

---

## Quick Reference

| ADR # | Title | Status | Date |
|-------|-------|--------|------|
| [0001](0001-record-architecture-decisions.md) | Record Architecture Decisions | accepted | 2025-12-13 |

---

## ADR Lifecycle

```
proposed → accepted → deprecated → superseded
              ↘
               rejected
```

**Status Definitions**:
- `proposed`: 검토 대기 중
- `accepted`: 승인됨, 구현 진행
- `deprecated`: 더 이상 유효하지 않음
- `superseded`: 새 ADR로 대체됨
- `rejected`: 거부됨 (드묾)

---

## Creating a New ADR

### 1. Copy Template
```bash
cp docs/templates/adr-template.md docs/decisions/XXXX-title.md
```

### 2. Fill Required Sections
- **Status**: Start with `proposed`
- **Date**: Today's date
- **Problem**: What problem are we solving?
- **Decision**: What did we decide?
- **Rationale**: Why this decision?
- **Consequences**: Positive, Negative, Uncertainty

### 3. Submit for Review
- Create PR with ADR
- Get minimum 1 reviewer approval
- Merge when `accepted`

---

## ADR Numbering

- 4-digit sequential: 0001, 0002, 0003...
- Never reuse numbers
- Deprecated ADRs keep their number

---

## When to Write an ADR

**Required**:
- Architecture changes affecting >3 files
- Technology choices (database, framework)
- Design patterns adoption
- Integration decisions

**Optional**:
- Minor refactoring
- Bug fixes
- Documentation updates

---

## Planned ADRs

| # | Title | Related | Priority |
|---|-------|---------|----------|
| 0010 | Task-Phase Relationship | Q1 | P0 |
| 0011 | Task Creation AI Hybrid | Q2 | P1 |
| 0012 | Multi-project Primary Selection | Q5 | P0 |
| 0013 | Dependency Hard Block | Q7 | P1 |

---

## Related Documents

- [SSOT Registry](../SSOT_REGISTRY.md) - Document hierarchy
- [Glossary](../glossary.md) - Term definitions
- [ADR Template](../templates/adr-template.md) - Template file
