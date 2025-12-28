# UDO Documentation Rules System v1.0

**Created**: 2025-12-15
**Status**: Draft for Review
**Based on**: React.dev, Next.js, Django/Python (Diataxis) benchmarking

---

## Executive Summary

### Problem Statement
Current documentation has:
- **171 files** in `docs/` with inconsistent organization
- **6 files** in `claudedocs/` (severely underutilized)
- **95.9% violation rate** of RULES.md guidelines
- No distinction between AI-generated vs human-written content
- No frontmatter metadata system
- No ordering/priority system

### Solution Overview
Adopt a **hybrid Diataxis + Author-Based** documentation system:
1. **Diataxis Framework**: 4-part content type separation
2. **Author Distinction**: Clear AI vs Human content paths
3. **Maturity Stages**: Draft → Review → Stable → Archive
4. **Frontmatter Standard**: Mandatory metadata for all documents

---

## 1. Top-Level Folder Structure

```
UDO-Development-Platform/
├── README.md                    # Project entry point (human-maintained)
├── CLAUDE.md                    # AI context file (hybrid)
│
├── docs/                        # Human-facing documentation (persistent)
│   ├── 0-getting-started/       # Tutorials (Diataxis: Learning)
│   ├── 1-guides/                # How-To Guides (Diataxis: Goals)
│   ├── 2-reference/             # API Reference (Diataxis: Information)
│   ├── 3-explanation/           # Conceptual (Diataxis: Understanding)
│   ├── 4-releases/              # Version history & changelogs
│   ├── PRDs/                    # Product Requirements (special)
│   └── _archive/                # Deprecated docs (timestamped)
│
├── claudedocs/                  # AI-generated documentation (session-based)
│   ├── analysis/                # Code/architecture analysis reports
│   ├── completion/              # Task/stage completion summaries
│   ├── decisions/               # Decision records & rationale
│   ├── worklog/                 # Daily/weekly work logs
│   └── whiteboard/              # Draft thinking & explorations
│
└── .claude/                     # System-level AI rules (global)
    ├── RULES.md
    ├── DOCUMENTATION_RULES.md   # This document's rules
    └── ...
```

---

## 2. Decision Tree: Where Does This Document Go?

```
┌─────────────────────────────────────────────────────────────────┐
│                    New Document Created                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  Who is the primary author?   │
              └───────────────────────────────┘
                     /              \
                    /                \
                   ▼                  ▼
          ┌─────────────┐      ┌─────────────┐
          │    Human    │      │  AI (Claude)│
          └─────────────┘      └─────────────┘
                 │                     │
                 ▼                     ▼
    ┌────────────────────┐   ┌────────────────────┐
    │ Will this document │   │ Is this for human  │
    │ be maintained by   │   │ consumption after  │
    │ humans long-term?  │   │ this session?      │
    └────────────────────┘   └────────────────────┘
           /    \                   /    \
          /      \                 /      \
        YES      NO              YES      NO
         │        │               │        │
         ▼        ▼               ▼        ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │  docs/  │ │claudedocs│ │  docs/  │ │claudedocs│
    │         │ │/whiteboard│ │(+ review)│ │         │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### Quick Reference Table

| Document Type | Primary Author | Location | Subfolder |
|---------------|----------------|----------|-----------|
| User guide, tutorial | Human | `docs/` | `0-getting-started/` |
| API documentation | Human | `docs/` | `2-reference/` |
| Architecture explanation | Human | `docs/` | `3-explanation/` |
| How-to guide | Human | `docs/` | `1-guides/` |
| Product requirements | Human | `docs/` | `PRDs/` |
| Release notes | Human | `docs/` | `4-releases/` |
| Code analysis report | AI | `claudedocs/` | `analysis/` |
| Stage completion summary | AI | `claudedocs/` | `completion/` |
| Decision record | AI | `claudedocs/` | `decisions/` |
| Daily work log | AI | `claudedocs/` | `worklog/` |
| Draft/thinking | AI | `claudedocs/` | `whiteboard/` |

---

## 3. Folder Definitions

### 3.1 `docs/` - Human-Facing Documentation

**Purpose**: Persistent, user-facing documentation that humans will read and maintain.

**Characteristics**:
- Stable content that outlives individual sessions
- Reviewed and approved before publishing
- Follows Diataxis framework
- May be AI-assisted but human-approved

#### Subfolders

| Folder | Diataxis Type | Purpose | Example Files |
|--------|---------------|---------|---------------|
| `0-getting-started/` | Tutorial | Step-by-step learning path | `01-installation.md`, `02-first-project.md` |
| `1-guides/` | How-To | Problem-solving recipes | `configure-uncertainty.md`, `deploy-production.md` |
| `2-reference/` | Reference | API specs, configs | `api/uncertainty-endpoints.md`, `config-options.md` |
| `3-explanation/` | Explanation | Conceptual deep-dives | `architecture-overview.md`, `bayesian-confidence.md` |
| `4-releases/` | - | Version history | `v1.0.0.md`, `changelog.md` |
| `PRDs/` | - | Product requirements | `PRD-kanban-integration.md` |
| `_archive/` | - | Deprecated docs | `2025-01-deprecated-v1-api.md` |

### 3.2 `claudedocs/` - AI-Generated Documentation

**Purpose**: Session-based documentation generated by AI for tracking, analysis, and knowledge capture.

**Characteristics**:
- Generated during AI sessions
- May be ephemeral or promoted to `docs/`
- Organized by content type, not by date
- Includes metadata for traceability

#### Subfolders

| Folder | Purpose | Retention | Example Files |
|--------|---------|-----------|---------------|
| `analysis/` | Code/architecture analysis | 90 days | `ARCHITECTURE_ANALYSIS_2025-12.md` |
| `completion/` | Task/stage summaries | Permanent | `WEEK1_DAY2_COMPLETE.md`, `OPTION_A_STAGE1_COMPLETE.md` |
| `decisions/` | Decision records | Permanent | `ADR-001-kanban-architecture.md` |
| `worklog/` | Daily/weekly logs | 30 days | `2025-12-15-worklog.md` |
| `whiteboard/` | Draft thinking | 7 days | `draft-uncertainty-improvements.md` |

---

## 4. Frontmatter Standard (Mandatory)

All documents MUST include YAML frontmatter:

### 4.1 Minimum Required Fields

```yaml
---
title: "Document Title"
created: "2025-12-15"
author: "human" | "claude" | "hybrid"
status: "draft" | "review" | "stable" | "deprecated"
---
```

### 4.2 Full Frontmatter Schema

```yaml
---
# Required
title: "Uncertainty Map API Reference"
created: "2025-12-15"
author: "claude"                    # human | claude | hybrid
status: "stable"                    # draft | review | stable | deprecated

# Recommended
updated: "2025-12-15"
category: "reference"               # tutorial | guide | reference | explanation | analysis | completion | decision | worklog
tags:
  - uncertainty
  - api
  - backend

# For AI-generated content
ai_model: "claude-opus-4.5"
session_id: "abc123"
confidence: 85                      # 0-100, AI's confidence in accuracy
requires_review: true               # Human review needed before promotion

# For versioned content
version: "2.0"
since: "2025-11-20"
deprecated_in: null
migration_guide: null

# For completion/progress docs
phase: "implementation"             # ideation | design | mvp | implementation | testing
milestone: "Week 1 Day 2"
completion_percentage: 100
---
```

### 4.3 Frontmatter Validation

Pre-commit hook should validate:
1. Frontmatter exists
2. Required fields present
3. `author` field is valid
4. `status` field is valid
5. `created` is valid ISO date

---

## 5. File Naming Conventions

### 5.1 General Rules

| Rule | Pattern | Example |
|------|---------|---------|
| Use kebab-case | `word-word-word.md` | `uncertainty-map-api.md` |
| No spaces | Replace with `-` | `getting-started.md` |
| Lowercase | All lowercase | `configuration.md` |
| Descriptive | Clear purpose | `configure-obsidian-sync.md` |

### 5.2 Numbered Prefixes (for docs/)

Use 2-digit prefixes for ordering within folders:

```
0-getting-started/
├── 01-installation.md
├── 02-project-structure.md
├── 03-first-dashboard.md
└── 99-troubleshooting.md
```

### 5.3 Date Prefixes (for claudedocs/)

Use ISO date for session-based documents:

```
worklog/
├── 2025-12-15-worklog.md
├── 2025-12-14-worklog.md
└── 2025-12-13-worklog.md

completion/
├── 2025-12-15-WEEK1-DAY2-COMPLETE.md
├── 2025-12-14-OPTION-A-STAGE1-COMPLETE.md
```

### 5.4 Special Prefixes

| Prefix | Meaning | Example |
|--------|---------|---------|
| `ADR-NNN` | Architecture Decision Record | `ADR-001-kanban-architecture.md` |
| `PRD-` | Product Requirements Document | `PRD-uncertainty-map.md` |
| `RFC-` | Request for Comments | `RFC-documentation-rules.md` |

---

## 6. Content Lifecycle

### 6.1 Status Transitions

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    ▼                                         │
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────┐   │
│  draft  │──▶│ review  │──▶│  stable │──▶│ deprecated  │───┘
└─────────┘   └─────────┘   └─────────┘   └─────────────┘
     │              │              │
     │              │              │
     ▼              ▼              ▼
  claudedocs/   claudedocs/     docs/
  whiteboard/   (pending)    (promoted)
```

### 6.2 Promotion from claudedocs/ to docs/

When AI-generated content should become permanent:

1. **Review**: Human reviews content for accuracy
2. **Edit**: Human edits for clarity and completeness
3. **Update Frontmatter**: Change `author` to `hybrid`, update `status`
4. **Move**: Move file to appropriate `docs/` subfolder
5. **Update Navigation**: Add to relevant index/navigation files

### 6.3 Archival Rules

| Original Location | Archive Location | Trigger |
|-------------------|------------------|---------|
| `docs/` | `docs/_archive/` | Replaced by new version |
| `claudedocs/worklog/` | Delete | 30 days old |
| `claudedocs/whiteboard/` | Delete | 7 days old |
| `claudedocs/analysis/` | `docs/_archive/` or Delete | 90 days old |

---

## 7. AI Decision Rules

### 7.1 When AI Creates Documentation

**ALWAYS use `claudedocs/` for**:
- Analysis reports
- Completion summaries
- Work logs
- Decision records
- Draft explorations

**NEVER directly create in `docs/` unless**:
- Explicitly requested by user
- Content is a pure API reference extracted from code
- Fixing a typo or minor update to existing doc

### 7.2 Folder Selection Logic

```python
def determine_folder(doc_type: str, author: str, for_user_consumption: bool) -> str:
    """
    Decision logic for AI to determine correct folder.
    """
    if author == "human":
        return "docs/"

    if doc_type in ["analysis", "completion", "decision", "worklog", "whiteboard"]:
        return f"claudedocs/{doc_type}/"

    if doc_type in ["tutorial", "guide", "reference", "explanation"]:
        if for_user_consumption and author == "hybrid":
            return f"docs/{DIATAXIS_MAPPING[doc_type]}/"
        else:
            return "claudedocs/whiteboard/"

    return "claudedocs/whiteboard/"
```

### 7.3 Completion Summary Rule

**CRITICAL**: When completing a stage/milestone:
- Create summary in `claudedocs/completion/`
- Filename: `YYYY-MM-DD-MILESTONE-NAME-COMPLETE.md`
- NOT in `docs/sessions/progress/` (deprecated)

---

## 8. Migration Plan

### 8.1 Immediate Actions (Week 1)

1. **Create folder structure** in `claudedocs/`:
   ```
   mkdir -p claudedocs/{analysis,completion,decisions,worklog,whiteboard}
   ```

2. **Move misplaced files**:
   - `docs/WEEK*_COMPLETION*.md` → `claudedocs/completion/`
   - `docs/*_ANALYSIS*.md` → `claudedocs/analysis/`
   - Project root analysis files → `claudedocs/analysis/`

3. **Update RULES.md** with new documentation rules

### 8.2 Gradual Migration (Week 2-4)

1. **Add frontmatter** to existing docs (automated script)
2. **Reorganize `docs/`** into Diataxis folders
3. **Create navigation files** (`navigation.yml`)
4. **Set up pre-commit hooks** for validation

### 8.3 Files to Relocate

| Current Location | New Location | Count |
|------------------|--------------|-------|
| `docs/WEEK*_COMPLETION*.md` | `claudedocs/completion/` | ~8 |
| `docs/*_ANALYSIS*.md` | `claudedocs/analysis/` or `docs/3-explanation/` | ~15 |
| `docs/sessions/progress/*.md` | `claudedocs/completion/` | ~10 |
| Root `*_REPORT.md` | `claudedocs/analysis/` | ~5 |
| Root `*_SUMMARY.md` | `claudedocs/analysis/` | ~3 |

---

## 9. Validation & Enforcement

### 9.1 Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Validate frontmatter exists
for file in $(git diff --cached --name-only -- '*.md'); do
    if ! head -1 "$file" | grep -q "^---$"; then
        echo "ERROR: $file missing frontmatter"
        exit 1
    fi
done

# Validate AI docs go to claudedocs/
for file in $(git diff --cached --name-only -- 'docs/*.md'); do
    author=$(grep "^author:" "$file" | cut -d'"' -f2)
    if [ "$author" = "claude" ]; then
        echo "ERROR: AI-authored doc $file should be in claudedocs/"
        exit 1
    fi
done
```

### 9.2 CI Validation

```yaml
# .github/workflows/docs-validation.yml
name: Documentation Validation
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate frontmatter
        run: python scripts/validate_docs.py
      - name: Check folder placement
        run: python scripts/check_doc_placement.py
```

---

## 10. Quick Reference Card

### For AI (Claude):

```
┌────────────────────────────────────────────────────────────┐
│                  AI DOCUMENTATION QUICK GUIDE              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Creating analysis/report?     → claudedocs/analysis/      │
│  Completing a milestone?       → claudedocs/completion/    │
│  Recording a decision?         → claudedocs/decisions/     │
│  Daily work log?               → claudedocs/worklog/       │
│  Drafting/exploring?           → claudedocs/whiteboard/    │
│                                                            │
│  ⚠️  NEVER create directly in docs/ unless:               │
│      - User explicitly requests it                         │
│      - It's an API reference from code                     │
│      - Minor fix to existing doc                           │
│                                                            │
│  ✅ ALWAYS include frontmatter:                            │
│      ---                                                   │
│      title: "..."                                          │
│      created: "YYYY-MM-DD"                                 │
│      author: "claude"                                      │
│      status: "draft"                                       │
│      ---                                                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### For Humans:

```
┌────────────────────────────────────────────────────────────┐
│               HUMAN DOCUMENTATION QUICK GUIDE              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  docs/0-getting-started/  → Tutorials, learning paths      │
│  docs/1-guides/           → How-to, problem-solving        │
│  docs/2-reference/        → API specs, configuration       │
│  docs/3-explanation/      → Architecture, concepts         │
│  docs/4-releases/         → Release notes, changelog       │
│  docs/PRDs/               → Product requirements           │
│                                                            │
│  📋 To promote AI docs to docs/:                           │
│      1. Review content for accuracy                        │
│      2. Update frontmatter (author: "hybrid")              │
│      3. Move to appropriate docs/ subfolder                │
│      4. Add to navigation index                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 11. Appendix: Diataxis Framework Reference

| Type | User Need | Form | Analogy |
|------|-----------|------|---------|
| **Tutorial** | Learning | Lesson | Teaching a child to cook |
| **How-To Guide** | Goals | Series of steps | Recipe in a cookbook |
| **Reference** | Information | Dry description | Encyclopedia article |
| **Explanation** | Understanding | Discursive explanation | Article on culinary history |

**Source**: https://diataxis.fr/

---

## 12. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-15 | Claude (Opus 4.5) | Initial draft based on React, Next.js, Django benchmarking |

---

**Next Steps**:
1. Review this document with user
2. Create folder structure
3. Migrate existing files
4. Update RULES.md reference
5. Set up validation hooks
