# Documentation Inventory
**Last Updated**: 2025-12-13
**Total Active Docs**: ~120 (6 archived)
**Archive Location**: `docs/_ARCHIVE/`

---

## Quick Navigation

### Tier 1: Primary Reference (Single Source of Truth)

| Document | Purpose | Status |
|----------|---------|--------|
| `../CLAUDE.md` | Project context for AI | ✅ Current |
| `DEVELOPMENT_ROADMAP_V6.md` | Master roadmap | ✅ Current (V6.1) |
| `KANBAN_IMPLEMENTATION_SUMMARY.md` | Kanban master guide | ✅ Current |

### Tier 2: Active Implementation Guides

| Category | Document | Description |
|----------|----------|-------------|
| **Week Progress** | `WEEK0_COMPLETION_SUMMARY.md` | Week 0 final summary |
| | `WEEK1_DAY1-2_COMPLETION_REPORT.md` | Week 1 latest progress |
| | `WEEK1_KANBAN_COMPLETION_SUMMARY.md` | Kanban-specific progress |
| **Kanban** | `KANBAN_INTEGRATION_STRATEGY.md` | Strategic analysis (18K words) |
| | `KANBAN_UI_COMPONENTS_DESIGN.md` | UI specifications |
| | `KANBAN_DATABASE_SCHEMA_DESIGN.md` | DB schema |
| | `KANBAN_API_SPECIFICATION.md` | API endpoints |
| **Architecture** | `ARCHITECTURE_EXECUTIVE_SUMMARY.md` | High-level overview |
| | `ARCHITECTURE_STABILITY_ANALYSIS.md` | P0 issues + solutions |
| **Gap Analysis** | `GAP_ANALYSIS_2025-12-13.md` | Latest plan review |
| **Pre-mortem** | `PREMORTEM_ANALYSIS_2025-12-06.md` | Risk mitigation |

### Tier 3: Reference Documentation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **GI/CK Theory** | `GI_CK_ARCHITECTURE_DESIGN.md` | Master spec |
| | `GI_CK_QUICK_REFERENCE.md` | Quick lookup |
| **Time Tracking** | `TIME_TRACKING_IMPLEMENTATION.md` | Master spec |
| | `TIME_TRACKING_QUICK_REFERENCE.md` | Quick lookup |
| **Obsidian** | `OBSIDIAN_SERVICE_README.md` | Integration guide |
| | `Obsidian_Quick_Reference.md` | Quick lookup |
| **Constitution** | `UDO_CONSTITUTION.md` | AI governance rules |
| | `CONSTITUTIONAL_FRAMEWORK_SUMMARY.md` | Framework overview |

---

## Archived Documents (2025-12-13)

The following documents have been moved to `_ARCHIVE/` as they are superseded:

| Archived File | Reason | Action Taken |
|---------------|--------|--------------|
| `DEVELOPMENT_ROADMAP_V4.md` | Superseded version | Content integrated into V6.2 ✅ |
| `DEVELOPMENT_ROADMAP_V5.md` | Superseded version | Content integrated into V6.2 ✅ |

## Restored & Renamed Documents (2025-12-13)

The following documents were initially archived but found to contain unique content:

| Original Name | New Name | Reason |
|---------------|----------|--------|
| `WEEK_0_COMPLETION_SUMMARY.md` | `DESIGN_PHASE_COMPLETION_2025-11-17.md` | Different content (Design 60%→95%, not Baseline) |
| `WEEK1_FOUNDATION_COMPLETE.md` | `FOUNDATION_PHASE_COMPLETE_2025-11-20.md` | Different phase (Obsidian/Constitution, not Kanban) |
| `WEEK1_IMPLEMENTATION_GUIDE.md` | `FOUNDATION_IMPLEMENTATION_GUIDE.md` | Foundation phase guide (Nov 20) |
| `INTEGRATION_ARCHITECTURE_V4_PART2.md` | `INTEGRATION_ARCHITECTURE_V4_SUPPLEMENTARY.md` | Tech stack decisions (unique content) |

---

## Document Categories

### 1. Roadmap & Planning (5 active)
- DEVELOPMENT_ROADMAP_V6.md ⭐
- GAP_ANALYSIS_2025-12-13.md
- PREMORTEM_ANALYSIS_2025-12-06.md
- IMPLEMENTATION_ROADMAP_WITH_UNCERTAINTY.md
- IMPLEMENTATION_WORKFLOW_SYSTEMATIC.md

### 2. Week Progress Reports (10 active)
- WEEK0_*.md (6 files)
- WEEK1_*.md (2 files, after archive)
- WEEK2_*.md (4 files)
- WEEK3-4_*.md (2 files)
- WEEK4_*.md (4 files - testing guides)

### 3. Kanban Integration (6 active)
- KANBAN_IMPLEMENTATION_SUMMARY.md ⭐
- KANBAN_INTEGRATION_STRATEGY.md
- KANBAN_UI_COMPONENTS_DESIGN.md
- KANBAN_DATABASE_SCHEMA_DESIGN.md
- KANBAN_API_SPECIFICATION.md
- KANBAN_PERFORMANCE_VALIDATION.md

### 4. Architecture (9 active)
- ARCHITECTURE_EXECUTIVE_SUMMARY.md
- ARCHITECTURE_VISUAL_DIAGRAMS.md
- ARCHITECTURE_STABILITY_ANALYSIS.md
- BACKEND_ARCHITECTURE_VISUAL_SUMMARY.md
- FRONTEND_ARCHITECTURE_SUMMARY.md
- FRONTEND_ARCHITECTURE_DIAGRAM.md
- INTEGRATION_ARCHITECTURE_V4.md
- INTEGRATION_ARCHITECTURE_V4_SUPPLEMENTARY.md (Tech stack decisions)
- MULTI_SESSION_ARCHITECTURE.md

### 5. GI/CK Theory (7 active)
- GI_CK_ARCHITECTURE_DESIGN.md
- GI_CK_IMPLEMENTATION_SUMMARY.md
- GI_CK_VISUAL_ARCHITECTURE.md
- GI_CK_API_GUIDE.md
- GI_CK_QUICK_REFERENCE.md
- WEEK2_GI_CK_COMPLETION.md
- WEEK2_GI_CK_FRONTEND_COMPLETE.md

### 6. Time Tracking (5 active)
- TIME_TRACKING_IMPLEMENTATION.md
- TIME_TRACKING_GUIDE.md
- TIME_TRACKING_QUICK_REFERENCE.md
- TIME_TRACKING_DEPLOYMENT_VERIFICATION.md
- TIME_TRACKING_PHASE_INTEGRATION_DESIGN.md

### 7. Obsidian Integration (4 active)
- OBSIDIAN_SERVICE_README.md
- Obsidian_Debouncing_Implementation.md
- Obsidian_Debouncing_Diagram.md
- Obsidian_Quick_Reference.md

### 8. PRD Documents (PRDs/ subfolder)
- 01_RAW/ - Raw PRDs from different AI models
- 03_FINAL/ - Unified enhanced PRD
- 04_DRAFT/ - Draft future versions

### 9. Collaboration & Strategy (8 active)
- COLLABORATION_STRATEGY.md
- COLLABORATION_OPTIMIZATION_ANALYSIS.md
- ANTIGRAVITY_COLLABORATION_GUIDE.md
- HYBRID_STRATEGY_ANALYSIS.md
- MODEL_STRATEGY_FEEDBACK.md
- ROLE_BASED_ACTION_PLANS.md
- INTEGRATED_DEVELOPMENT_GUIDE.md
- HANDOFF_TO_CLAUDE.md

### 10. Technical Guides (misc)
- WSL_VS_WINDOWS_ENV.md
- HYDRATION_MISMATCH_FIX.md
- DATABASE_SETUP_STATUS.md
- DATABASE_INTEGRATION_COMPLETE.md
- USER_GUIDE.md
- USER_SCENARIOS.md

---

## Consolidation Opportunities (Future)

These areas have multiple files that could be merged:

| Area | Current Files | Recommendation |
|------|---------------|----------------|
| TIME_TRACKING | 5 files | Merge into 2 (Master + Reference) |
| GI_CK | 7 files | Merge into 3 (Master + Visual + Reference) |
| ARCHITECTURE | 8 files | Review overlap, potentially merge summaries |
| WEEK reports | 20+ files | Consider monthly rollups |

---

## Naming Conventions

**Active Documents**:
- `TOPIC_SUBTOPIC.md` - Standard format
- `WEEK[N]_*.md` - Week progress reports
- No underscores in WEEK number (WEEK0, not WEEK_0)

**Archived Documents**:
- Moved to `_ARCHIVE/` folder
- Original filename preserved

**Version Control**:
- Use `_V[N].md` suffix for versioned docs
- Only keep latest version in active folder

---

## Maintenance Schedule

- **Weekly**: Archive completed week reports
- **Monthly**: Review consolidation opportunities
- **Per Release**: Update inventory with new docs

---

**Document Version**: 1.0
**Created**: 2025-12-13
