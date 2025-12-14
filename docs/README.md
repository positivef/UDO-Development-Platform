# UDO Documentation Hub

**Purpose**: AI & Human Entry Point for Project Documentation
**Last Updated**: 2025-12-13
**Quick Status**: [CURRENT.md](CURRENT.md)

---

## Quick Navigation

### For AI Agents

```yaml
Start Here:
  1. CURRENT.md          # What's happening now
  2. SSOT_REGISTRY.md    # Document authority hierarchy
  3. glossary.md         # Term definitions

Active Work:
  - features/kanban/     # Kanban-UDO Integration (Week 4)
  - sessions/            # Session handoffs

Reference:
  - architecture/        # System design
  - decisions/           # ADRs (Architecture Decision Records)
  - proposals/           # RFCs (Request for Comments)
```

### For Developers

| Need | Go To |
|------|-------|
| **Get Started** | [guides/USER_GUIDE.md](guides/USER_GUIDE.md) |
| **Architecture Overview** | [architecture/ARCHITECTURE_EXECUTIVE_SUMMARY.md](architecture/ARCHITECTURE_EXECUTIVE_SUMMARY.md) |
| **API Reference** | [features/kanban/KANBAN_API_SPECIFICATION.md](features/kanban/KANBAN_API_SPECIFICATION.md) |
| **Database Schema** | [features/kanban/KANBAN_DATABASE_SCHEMA_DESIGN.md](features/kanban/KANBAN_DATABASE_SCHEMA_DESIGN.md) |
| **Decision History** | [decisions/README.md](decisions/README.md) |

---

## Document Hierarchy

```
docs/
├── README.md              # You are here
├── CURRENT.md             # Current status & active work
├── SSOT_REGISTRY.md       # Single Source of Truth registry
├── glossary.md            # Term definitions
│
├── architecture/          # System Architecture (8 docs)
├── features/              # Feature Documentation (25+ docs)
│   ├── kanban/           # Kanban Integration
│   ├── time-tracking/    # Time Tracking
│   ├── uncertainty/      # Uncertainty Map
│   ├── quality/          # Quality Metrics
│   ├── obsidian/         # Obsidian Sync
│   └── ai-collaboration/ # AI Bridge
│
├── guides/                # User & Developer Guides (8 docs)
├── decisions/             # ADRs (Architecture Decisions)
├── proposals/             # RFCs (Feature Proposals)
├── sessions/              # Session Handoffs
├── templates/             # Document Templates
├── PRDs/                  # Product Requirements
└── Obsidian/              # Obsidian Vault Sync
```

---

## Key Documents by Role

### AI Agent (Claude, GPT, Codex)
1. **Context Loading**: `CURRENT.md` → `sessions/HANDOFF_TO_CLAUDE.md`
2. **Architecture**: `architecture/EXECUTIVE_SUMMARY.md`
3. **Active Feature**: `features/kanban/KANBAN_IMPLEMENTATION_SUMMARY.md`
4. **Terminology**: `glossary.md`

### Backend Developer
1. **API Design**: `features/kanban/API_SPECIFICATION.md`
2. **Database**: `features/kanban/DATABASE_SCHEMA.md`
3. **Architecture**: `architecture/backend/ANALYSIS.yaml`

### Frontend Developer
1. **UI Components**: `features/kanban/UI_COMPONENTS.md`
2. **Architecture**: `architecture/frontend/SUMMARY.md`
3. **Integration**: `features/kanban/INTEGRATION_STRATEGY.md`

### Tech Lead / Architect
1. **Decisions**: `decisions/README.md`
2. **Proposals**: `proposals/README.md`
3. **Stability**: `architecture/STABILITY_ANALYSIS.md`

---

## Document Types

| Type | Prefix | Location | Example |
|------|--------|----------|---------|
| **ADR** | `0001-` | `decisions/` | `0001-record-architecture-decisions.md` |
| **RFC** | `PROPOSAL-` | `proposals/` | `PROPOSAL-0003-week0-criteria.md` |
| **Feature** | Feature name | `features/{name}/` | `features/kanban/IMPLEMENTATION_SUMMARY.md` |
| **Guide** | Topic | `guides/` | `guides/USER_GUIDE.md` |
| **Session** | Date | `sessions/` | `sessions/2025-12-13_handoff.md` |

---

## Search Tips

### By Topic
```bash
# Find Kanban-related docs
grep -r "kanban" docs/ --include="*.md"

# Find architecture decisions
ls docs/decisions/

# Find active features
ls docs/features/
```

### By Status
- **Active**: Check `CURRENT.md`
- **Deprecated**: Look for `[DEPRECATED]` or `[LEGACY]` prefix
- **Draft**: Check `proposals/` with status `DRAFT`

---

## Contributing

### Adding New Documentation

1. **Feature docs** → `features/{feature-name}/`
2. **Architecture decisions** → Create ADR in `decisions/`
3. **New proposals** → Create RFC in `proposals/`
4. **Session handoffs** → Use template from `templates/session-handoff-template.md`

### Document Standards

- Use templates from `templates/`
- Follow glossary terms from `glossary.md`
- Update `SSOT_REGISTRY.md` for authority changes
- Add to this README if creating new category

---

## Related Files

- **Project Root**: `../CLAUDE.md` (Claude Code instructions)
- **Backend Config**: `../backend/config/UDO_CONSTITUTION.yaml`
- **Frontend**: `../web-dashboard/` (Next.js dashboard)

---

**Maintainer**: @claude-code
**Update Frequency**: On structure changes
