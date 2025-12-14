# Single Source of Truth (SSOT) Registry

**Last Updated**: 2025-12-13
**Purpose**: Define authoritative documents for each topic area
**Rule**: When documents conflict, higher tier wins
**Structure Version**: 2.0 (Post-restructure)

---

## Document Structure Overview

```
docs/
├── README.md              # AI Entry Point
├── CURRENT.md             # Current Status
├── SSOT_REGISTRY.md       # This file
├── glossary.md            # Term Definitions
│
├── architecture/          # System Architecture (10+ docs)
├── features/              # Feature Documentation
│   ├── kanban/           # Kanban Integration
│   ├── time-tracking/    # Time Tracking
│   ├── uncertainty/      # Uncertainty Map
│   ├── gi-ck/            # GI/CK Theory
│   ├── obsidian/         # Obsidian Sync
│   ├── ai-collaboration/ # AI Bridge
│   └── udo/              # Core UDO
├── guides/                # User & Developer Guides
│   └── development/      # Development workflows
├── analysis/              # Analysis & Review docs
├── decisions/             # ADRs
├── proposals/             # RFCs
├── sessions/              # Session Handoffs
│   ├── progress/         # Phase completion records
│   └── worklogs/         # Daily worklogs
├── templates/             # Document Templates
├── PRDs/                  # Product Requirements
└── Obsidian/              # Vault sync
```

---

## Tier 1: Primary Reference (Authoritative)

These documents are the **single source of truth**. In case of conflict with other documents, Tier 1 content takes precedence.

| Document | Location | Topic | Update Frequency |
|----------|----------|-------|------------------|
| `CLAUDE.md` | `../CLAUDE.md` | AI context, commands | Every session |
| `README.md` | `./README.md` | Entry point, navigation | On structure changes |
| `CURRENT.md` | `./CURRENT.md` | Current status | Every session |
| `SSOT_REGISTRY.md` | `./SSOT_REGISTRY.md` | Document hierarchy | As needed |
| `glossary.md` | `./glossary.md` | Term definitions | As needed |
| `DEVELOPMENT_ROADMAP_V6.md` | `guides/development/` | Master roadmap | Weekly |

### Tier 1 Update Protocol

1. **Before modifying Tier 1**: Check for dependent Tier 2/3 documents
2. **After modifying Tier 1**: Update related documents within same session
3. **Conflict resolution**: Tier 1 always wins; update lower tiers to match

---

## Tier 2: Phase Records (Immutable)

Immutable records of completed phases. Do not modify after completion.

| Document | Location | Phase | Completion Date |
|----------|----------|-------|-----------------|
| `DESIGN_PHASE_COMPLETION_2025-11-17.md` | `sessions/progress/` | Phase A Design | 2025-11-17 |
| `FOUNDATION_PHASE_COMPLETE_2025-11-20.md` | `sessions/progress/` | Phase A Foundation | 2025-11-20 |
| `WEEK0_COMPLETION_SUMMARY.md` | `sessions/progress/` | Phase B Baseline | 2025-12-07 |
| `WEEK1_*.md` | `sessions/progress/` | Phase B Week 1 | 2025-12-08 |

### Tier 2 Rules

- **Immutable**: Once phase is complete, document is frozen
- **Append-only**: Add follow-up documents, don't modify original
- **Reference**: Link to Tier 2 when citing historical decisions

---

## Tier 3: Active Implementation

Working documents that may change frequently.

### Architecture & Design
| Document | Location | SSOT For |
|----------|----------|----------|
| `EXECUTIVE_SUMMARY.md` | `architecture/` | System overview |
| `INTEGRATION_ARCHITECTURE_V4.md` | `architecture/` | Integration design |
| `MULTI_SESSION_ARCHITECTURE.md` | `architecture/` | Multi-session handling |
| `backend/ANALYSIS.yaml` | `architecture/backend/` | Backend structure |
| `frontend/SUMMARY.md` | `architecture/frontend/` | Frontend structure |

### Feature: Kanban
| Document | Location | SSOT For |
|----------|----------|----------|
| `IMPLEMENTATION_SUMMARY.md` | `features/kanban/` | Kanban master guide |
| `INTEGRATION_STRATEGY.md` | `features/kanban/` | Q1-Q8 decisions |
| `DATABASE_SCHEMA.md` | `features/kanban/` | DB structure |
| `API_SPECIFICATION.md` | `features/kanban/` | REST endpoints |
| `UI_COMPONENTS.md` | `features/kanban/` | UI specs |

### Feature: Time Tracking
| Document | Location | SSOT For |
|----------|----------|----------|
| `IMPLEMENTATION.md` | `features/time-tracking/` | ROI calculation |
| `GUIDE.md` | `features/time-tracking/` | User guide |
| `PHASE_INTEGRATION.md` | `features/time-tracking/` | Phase integration |

### Feature: Obsidian
| Document | Location | SSOT For |
|----------|----------|----------|
| `SERVICE_README.md` | `features/obsidian/` | Obsidian service |
| `QUICK_REFERENCE.md` | `features/obsidian/` | Quick start |

### Feature: GI-CK Theory
| Document | Location | SSOT For |
|----------|----------|----------|
| `ARCHITECTURE_DESIGN.md` | `features/gi-ck/` | GI/CK theory |
| `API_GUIDE.md` | `features/gi-ck/` | API reference |

### Feature: UDO Core
| Document | Location | SSOT For |
|----------|----------|----------|
| `UDO_CONSTITUTION.md` | `features/udo/` | AI governance rules |
| `VERSION_HISTORY_FEATURE.md` | `features/udo/` | Version tracking |

---

## Tier 4: Reference (Read-only)

Stable reference documentation. Rarely changes.

| Document | Location | Topic |
|----------|----------|-------|
| `USER_GUIDE.md` | `guides/` | End-user docs |
| `USER_SCENARIOS.md` | `guides/` | User workflows |
| `CLI_INTEGRATION.md` | `guides/` | CLI setup |
| `WSL_VS_WINDOWS_ENV.md` | `guides/` | Environment setup |
| `adr-template.md` | `templates/` | ADR template |
| `rfc-lite-template.md` | `templates/` | RFC template |
| `session-handoff-template.md` | `templates/` | Handoff template |

---

## Folder Reference

| Folder | Purpose | When to Use |
|--------|---------|-------------|
| `architecture/` | System design docs | Architecture changes |
| `features/{name}/` | Feature-specific docs | Feature work |
| `guides/` | How-to guides | User-facing docs |
| `guides/development/` | Dev workflows | Development process |
| `analysis/` | Analysis & reviews | Assessments, audits |
| `decisions/` | ADRs | Architecture decisions |
| `proposals/` | RFCs | Feature proposals |
| `sessions/` | Session handoffs | AI handoff context |
| `sessions/progress/` | Phase records | Completion summaries |
| `sessions/worklogs/` | Daily logs | Work tracking |
| `templates/` | Document templates | Creating new docs |
| `PRDs/` | Product requirements | Requirements |

---

## Naming Conventions

### By Folder Type

**architecture/**
```
[TOPIC]_[TYPE].md
Example: EXECUTIVE_SUMMARY.md, VISUAL_DIAGRAMS.md
```

**features/{name}/**
```
[TYPE].md or [TOPIC]_[TYPE].md
Example: IMPLEMENTATION.md, API_SPECIFICATION.md
```

**sessions/progress/**
```
WEEK[N]_[TYPE].md or PHASE_[TOPIC].md
Example: WEEK0_COMPLETION_SUMMARY.md
```

**analysis/**
```
[TOPIC]_ANALYSIS.md or [TOPIC]_REVIEW.md
Example: GAP_ANALYSIS_2025-12-13.md
```

**decisions/**
```
[NNNN]-[title].md (ADR format)
Example: 0001-record-architecture-decisions.md
```

---

## Conflict Resolution Protocol

```
Step 1: Identify tier of each document
  Tier 1 > Tier 2 > Tier 3 > Tier 4

Step 2: If same tier, check dates
  More recent = more authoritative (unless Tier 2 which is immutable)

Step 3: If still unclear, check CURRENT.md
  Current status reflects ground truth

Step 4: If contradicts code
  Code is truth; update document to match code
```

---

## Migration Summary (2025-12-13)

### Before
- 129 .md files in docs/ root
- No clear organization
- Difficult navigation

### After
- 5 files in docs/ root (essential only)
- 15 organized subfolders
- Clear entry points (README.md, CURRENT.md)
- Industry-aligned structure (Kubernetes, Next.js patterns)

### Validation
- Technical Writer: Industry pattern alignment ✓
- DevOps Architect: CI/CD integration ready ✓
- System Architect: AI context optimization ✓

---

## Maintenance Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| CURRENT.md update | Every session | Active Claude |
| SSOT Registry review | Monthly | Project lead |
| Document health audit | Bi-weekly | Active Claude |
| Archive cleanup | Monthly | Project lead |

---

**Document Version**: 2.0
**Created**: 2025-12-13
**Updated**: 2025-12-13 (Post-restructure)
**Author**: Claude Code (AI Assistant)
