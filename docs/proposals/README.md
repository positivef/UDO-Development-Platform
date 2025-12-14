# RFC Lite Proposals

**Purpose**: 구조화된 설계 리뷰 프로세스를 통한 품질 확보
**Methodology**: RFC (Request for Comments) - Lightweight version
**Template**: [rfc-lite-template.md](../templates/rfc-lite-template.md)

---

## Quick Reference

| RFC # | Title | Status | Date |
|-------|-------|--------|------|
| - | (No proposals yet) | - | - |

---

## RFC Lifecycle

```
DRAFT → REVIEW → APPROVED → IMPLEMENTED → DEPRECATED
           ↓
        REJECTED (rare)
```

**Status Definitions**:
- `DRAFT`: 작성 중
- `REVIEW`: 리뷰 진행 중 (minimum 2 reviewers)
- `APPROVED`: 승인됨, 구현 가능
- `IMPLEMENTED`: 구현 완료
- `DEPRECATED`: 더 이상 유효하지 않음
- `REJECTED`: 거부됨

---

## When to Write an RFC

**Required**:
- Major feature implementation (>1 week work)
- API contract changes
- Database schema changes
- Cross-system integration

**Not Required** (use ADR instead):
- Architecture decisions
- Technology choices
- Design pattern adoption

---

## RFC vs ADR

| Aspect | ADR | RFC |
|--------|-----|-----|
| **Focus** | What & Why (결정) | How & When (설계) |
| **Timing** | After decision | Before implementation |
| **Length** | 1-2 pages | 3-10 pages |
| **Review** | Optional | Required (min 2) |
| **Change** | Immutable | Draft can be modified |

---

## Creating a New RFC

### 1. Copy Template
```bash
cp docs/templates/rfc-lite-template.md docs/proposals/XXXX-title.md
```

### 2. Fill Sections
- **Status**: Start with `DRAFT`
- **Author**: Your GitHub handle
- **Reviewers**: Minimum 2 (can include AI: @claude-code, @gpt-4o)
- **Summary**: 1 sentence
- **Motivation**: Why this change?
- **Design**: How to implement?
- **Success Criteria**: Measurable outcomes

### 3. Request Review
- Move status to `REVIEW`
- Notify reviewers
- Address feedback in "Review Comments"

### 4. Approval
- Get approval from all reviewers
- Move status to `APPROVED`
- Begin implementation

---

## Planned RFCs

| # | Title | Priority | Target |
|---|-------|----------|--------|
| 0003 | Week 0 Completion Criteria | P0 | 2025-12-14 |
| 0004 | Kanban Integration Strategy | P1 | 2025-12-21 |

---

## Related Documents

- [SSOT Registry](../SSOT_REGISTRY.md) - Document hierarchy
- [Glossary](../glossary.md) - Term definitions
- [RFC Template](../templates/rfc-lite-template.md) - Template file
- [ADR README](../decisions/README.md) - For decision records
