# Documentation Structure Analysis Report

**Date**: 2025-12-13
**Scope**: Industry best practices vs. proposed UDO docs structure
**Method**: Analysis of 5 major open-source projects + current state assessment

---

## Executive Summary

### Key Findings
1. **Industry Pattern**: Feature-based organization dominates (4/5 projects)
2. **Time-based docs**: Only React uses blog-style chronological organization
3. **Numbered prefixes**: Used only for ordered content (tutorials, guides) - not features
4. **Archive strategy**: In-place deprecation warnings preferred over separate folders
5. **Current UDO state**: 129 markdown files in flat structure - immediate refactoring needed

### Recommendation
**Hybrid Feature-Type Organization** with minimal time-based tracking. Avoid numbered prefixes for feature folders. Use in-document frontmatter for versioning and deprecation.

---

## Industry Analysis

### 1. Kubernetes Documentation Structure

**Repository**: kubernetes/website
**Docs Location**: `content/en/docs/`

#### Top-Level Structure
```
docs/
├── concepts/          # Core architecture and theory
│   ├── architecture/
│   ├── cluster-administration/
│   ├── containers/
│   ├── security/
│   └── workloads/
├── tasks/             # How-to guides (goal-oriented)
├── tutorials/         # Learning-oriented walkthroughs
├── reference/         # API reference and CLI docs
│   ├── access-authn-authz/
│   ├── command-line-tools-reference/
│   └── config-api/
├── setup/             # Installation guides
└── contribute/        # Contribution guidelines
```

#### Key Insights
- **Organization**: **Type-based** (concepts/tasks/tutorials/reference)
- **Naming**: Descriptive, lowercase with hyphens
- **Versioning**: Separate branches per K8s version (v1.28, v1.29, etc.)
- **Deprecation**: In-document warnings using frontmatter `feature-state: deprecated`
- **No numbered prefixes** on feature folders
- **No separate archive folder** - deprecated docs remain in place with warnings

#### Strengths
- Clear separation between learning (concepts/tutorials) and doing (tasks)
- Reference material isolated for API consumers
- Version isolation via branches prevents documentation drift

---

### 2. React Documentation Structure

**Repository**: reactjs/react.dev
**Docs Location**: `src/content/`

#### Top-Level Structure
```
content/
├── learn/                    # Learning-oriented guides
│   └── react-compiler/
├── reference/                # API reference
│   ├── react/
│   ├── react-dom/
│   ├── react-compiler/
│   ├── rsc/
│   └── rules/
├── blog/                     # Time-based content
│   ├── 2020/
│   ├── 2021/
│   ├── 2022/
│   ├── 2023/
│   ├── 2024/
│   └── 2025/
├── community/                # Team, conferences, translations
├── errors/                   # Error message reference
└── warnings/                 # Warning message reference
```

#### Key Insights
- **Organization**: **Type-based** (learn/reference) + **time-based blog**
- **Naming**: Lowercase, descriptive
- **Versioning**: No version folders - uses `versions.md` for migration guides
- **Deprecation**: `legacy.md` file within reference section
- **Blog structure**: Year-based folders for announcements
- **No numbered prefixes** except in blog filenames (dates)

#### Strengths
- Clean separation of learning vs reference material
- Time-based content isolated to blog folder only
- Legacy APIs documented in single file with clear warnings
- Error/warning documentation as first-class citizens

---

### 3. Next.js Documentation Structure

**Repository**: vercel/next.js
**Docs Location**: `docs/`

#### Top-Level Structure
```
docs/
├── 01-app/                   # App Router documentation
│   ├── 01-getting-started/
│   ├── 02-guides/
│   └── 03-api-reference/
├── 02-pages/                 # Pages Router (legacy)
│   ├── 01-getting-started/
│   ├── 02-guides/
│   ├── 03-building-your-application/
│   └── 04-api-reference/
├── 03-architecture/          # Architecture documentation
└── 04-community/             # Community resources
```

#### Key Insights
- **Organization**: **Feature-based** with **numbered ordering for navigation**
- **Naming**: Numbered prefixes (01-, 02-) to control display order
- **Versioning**: App vs Pages represents version/paradigm split
- **Deprecation**: Pages router kept alongside App router (dual paradigm support)
- **Numbered prefixes**: Used for **content types** (getting-started, guides, api-reference), not features
- **Purpose**: Ensures consistent ordering in generated navigation

#### Strengths
- Numbered prefixes enforce consistent navigation ordering
- Clear separation between new (App) and legacy (Pages) paradigms
- Parallel structure allows users to choose their path
- Each major section self-contained with getting-started → guides → reference

#### Warning
- **Numbered prefixes are for ordering content types, NOT features**
- Next.js doesn't use `01-routing/`, `02-data-fetching/` - they use descriptive names
- Numbers ensure `01-getting-started` appears before `02-guides` in navigation

---

### 4. FastAPI Documentation Structure

**Repository**: tiangolo/fastapi
**Docs Location**: `docs/en/docs/`

#### Top-Level Structure
```
docs/en/docs/
├── tutorial/                 # Step-by-step learning
│   ├── first-steps.md
│   ├── path-params.md
│   ├── query-params.md
│   ├── body.md
│   ├── dependencies/
│   └── ...
├── advanced/                 # Advanced topics
├── deployment/               # Deployment guides
├── how-to/                   # How-to guides
├── learn/                    # Conceptual learning
├── reference/                # API reference
├── about/                    # Project info
└── resources/                # External resources
```

Additional files in root:
- `async.md`, `benchmarks.md`, `features.md`, `contributing.md`
- `release-notes.md` (597KB changelog!)

#### Key Insights
- **Organization**: **Type-based** (tutorial/advanced/reference/how-to)
- **Naming**: Lowercase with hyphens
- **Versioning**: Branch-based (main, 0.95.x, 0.109.x branches)
- **Deprecation**: Not visible in structure - likely handled in release notes
- **No numbered prefixes** on folders or features
- **Multilingual**: `docs/en/`, `docs/es/`, `docs/fr/`, etc.

#### Strengths
- Tutorial progression from first-steps to advanced topics
- How-to guides separate from tutorial (different learning paths)
- Massive release notes file shows commitment to transparency
- Flat file structure for common topics (async, benchmarks, features)

---

### 5. Stripe Documentation (Note: Private Repository)

**Status**: Repository not publicly accessible on GitHub
**Public Docs**: https://stripe.com/docs

Based on public documentation site observation:

#### Structure (inferred from public site)
```
docs/
├── get-started/              # Quick start guides
├── payments/                 # Payment products
│   ├── payment-intents/
│   ├── payment-methods/
│   └── checkout/
├── billing/                  # Billing products
├── connect/                  # Platform features
├── api/                      # API reference
│   ├── authentication/
│   ├── errors/
│   └── resources/
├── webhooks/                 # Event handling
├── testing/                  # Test mode docs
└── changelog/                # Time-based updates
```

#### Key Insights (from public site)
- **Organization**: **Product/feature-based** with dedicated API section
- **Versioning**: API versioning with upgrade guides
- **Deprecation**: Warnings in API reference with sunset dates
- **Changelog**: Time-based updates separate from main docs
- **Testing**: Dedicated section for sandbox/test mode

---

## Pattern Summary Table

| Project | Primary Org | Numbered Prefixes | Versioning | Deprecation | Archive Folder |
|---------|-------------|-------------------|------------|-------------|----------------|
| **Kubernetes** | Type-based | ❌ None | Branches | In-doc warnings | ❌ No |
| **React** | Type-based | ❌ None | versions.md | legacy.md | ❌ No |
| **Next.js** | Feature-based | ✅ Content types only | Dual paradigm | Parallel docs | ❌ No |
| **FastAPI** | Type-based | ❌ None | Branches | Release notes | ❌ No |
| **Stripe** | Feature-based | ❌ None | API versions | API warnings | ❌ No |

### Common Patterns Across All Projects

1. **No numbered feature folders**: Next.js only uses numbers for content type ordering (getting-started, guides, reference)
2. **No separate archive folders**: 4/5 projects handle deprecation in-place
3. **Branch-based versioning**: Most common strategy (3/5 projects)
4. **Lowercase naming**: Universal standard with hyphens
5. **Time-based content isolated**: React (blog/), Stripe (changelog/) - not mixed with features

---

## Current UDO State Analysis

### Inventory
- **Total markdown files**: 129 in `docs/` root
- **Subdirectories**: 7 (`_ARCHIVE/`, `decisions/`, `Obsidian/`, `PRDs/`, `proposals/`, `sessions/`, `templates/`)
- **Problems**:
  - 129 files in flat structure = severe navigation difficulty
  - Inconsistent naming (UPPERCASE vs lowercase)
  - Unclear categorization (architecture? features? progress?)
  - `_ARCHIVE/` folder exists but unclear when to archive

### Sample Files (categorization unclear)
```
ARCHITECTURE_EXECUTIVE_SUMMARY.md          # Architecture doc
KANBAN_IMPLEMENTATION_SUMMARY.md           # Feature doc
WEEK0_COMPLETION_SUMMARY.md                # Progress/time-based
DEVELOPMENT_ROADMAP_V6.md                  # Planning doc
CLAUDE_WORKLOG_2025-11-20.md              # Session/time-based
PREMORTEM_ANALYSIS_2025-12-06.md          # Analysis/decision doc
```

**Current structure lacks clear organizational principle.**

---

## Proposed Structure Evaluation

### Your Proposed Structure
```
docs/
├── architecture/
├── features/
│   ├── kanban/
│   ├── time-tracking/
│   └── gi-ck-theory/
├── progress/
│   ├── 2025-11-phase-a/
│   └── 2025-12-phase-b/
├── decisions/ (ADR)
├── proposals/ (RFC)
├── reference/
├── analysis/
└── _archive/
```

---

## Strengths of Proposed Structure

### ✅ Feature-Based Organization
- Aligns with Stripe, Next.js patterns
- `features/kanban/`, `features/time-tracking/` → clear product boundaries
- Makes documentation discoverable by product area

### ✅ Dedicated Folders for Decisions/Proposals
- `decisions/` for ADRs (Architecture Decision Records)
- `proposals/` for RFCs (Request for Comments)
- Industry standard for architecture documentation

### ✅ Reference Section
- Follows Kubernetes, React, FastAPI pattern
- Good home for API docs, CLI reference, configuration

### ✅ Analysis Folder
- Unique to UDO, reflects research-driven development
- Good home for performance analysis, architecture studies

---

## Risks and Issues

### ⚠️ Time-Based "Progress" Folder

**Problem**: No industry precedent for project-specific progress tracking in docs

**Comparisons**:
- React: `blog/2025/` is for **public announcements**, not internal progress
- Stripe: `changelog/` is for **API changes**, not project phases
- Kubernetes: No time-based folders - uses Git history for progress

**Risks**:
1. **Stale content**: `2025-11-phase-a/` becomes outdated after phase ends
2. **Search difficulty**: Users searching for "Kanban" won't find completion reports
3. **Duplication**: Progress docs overlap with feature docs (e.g., `KANBAN_IMPLEMENTATION_SUMMARY.md` vs `progress/2025-11-phase-a/kanban-complete.md`)
4. **Unclear archive trigger**: When does `2025-11-phase-a/` move to `_archive/`?

**Industry Alternative**: Use **Git tags** + **feature frontmatter** instead

```yaml
---
title: Kanban Implementation Summary
feature: kanban
phase: implementation
completed: 2025-11-20
status: complete
version: 1.0.0
---
```

Git history + tags provide time-based navigation without folder clutter.

---

### ⚠️ Separate `_archive/` Folder

**Problem**: Industry avoids archive folders in favor of in-place deprecation

**Why industry avoids archive folders**:
1. **Broken links**: External links to archived docs break
2. **Search confusion**: Users find old docs in archive, assume they're current
3. **Maintenance burden**: Two locations to maintain for same feature
4. **Version ambiguity**: "Is this archived because it's old or because feature was removed?"

**Industry Best Practice**: In-document deprecation warnings

```yaml
---
title: Legacy Authentication System
status: deprecated
deprecated_since: 2025-11-01
replacement: /features/kanban/authentication-v2.md
sunset_date: 2026-01-01
---

⚠️ **DEPRECATED**: This feature is deprecated as of 2025-11-01.
Use [Authentication v2](/features/kanban/authentication-v2.md) instead.
Sunset date: 2026-01-01
```

**Advantages**:
- Links remain valid with warning banner
- Search indexes include deprecation status
- Users guided to replacement
- Git history preserves removal date

---

### ⚠️ Unclear Boundaries Between Folders

**Problem**: Where do these files go?

| File | Could Go In... | Ambiguity |
|------|----------------|-----------|
| `KANBAN_PERFORMANCE_ANALYSIS.md` | `features/kanban/` or `analysis/`? | Both valid |
| `ARCHITECTURE_STABILITY_ANALYSIS.md` | `architecture/` or `analysis/`? | Both valid |
| `DEVELOPMENT_ROADMAP_V6.md` | `proposals/` or `progress/`? | Both valid |
| `WEEK0_COMPLETION_SUMMARY.md` | `progress/2025-11-phase-a/` or `decisions/`? | Both valid |

**Recommendation**: Merge `analysis/` into `decisions/` or feature-specific folders

---

### ⚠️ Missing Folders from Industry Patterns

**Not in your structure but common in industry**:

1. **`tutorials/` or `guides/`**: Step-by-step learning (Kubernetes, FastAPI, Next.js)
2. **`api/` or `reference/api/`**: API documentation separate from general reference
3. **`contributing/`**: Contribution guidelines (Kubernetes, FastAPI)
4. **`community/`**: Team info, meetings, code of conduct (React, Next.js)

**UDO Context**:
- `tutorials/` → Low priority (internal tool, not public product)
- `api/` → Should exist under `reference/api/`
- `contributing/` → Relevant if open-sourcing
- `community/` → Not applicable (single developer)

---

## Recommended Structure

### Final Recommended Structure

```
docs/
├── README.md                           # Navigation guide
├── getting-started/                    # Quick start guides
│   ├── installation.md
│   ├── first-project.md
│   └── architecture-overview.md
├── features/                           # Feature documentation
│   ├── kanban/
│   │   ├── README.md                  # Feature overview
│   │   ├── user-guide.md
│   │   ├── api-reference.md
│   │   ├── implementation-notes.md
│   │   └── performance-analysis.md    # ← Move analysis here
│   ├── time-tracking/
│   ├── gi-ck-theory/
│   ├── uncertainty-map/
│   └── quality-metrics/
├── architecture/                       # System architecture
│   ├── overview.md
│   ├── backend-architecture.md
│   ├── frontend-architecture.md
│   ├── data-flow.md
│   └── integration-points.md
├── decisions/                          # ADRs (Architecture Decision Records)
│   ├── README.md                      # ADR index
│   ├── 001-kanban-task-phase-relationship.md
│   ├── 002-multi-project-strategy.md
│   ├── 003-archiving-strategy.md
│   └── template.md
├── proposals/                          # RFCs (Request for Comments)
│   ├── README.md                      # RFC index
│   ├── rfc-001-rl-guided-knowledge-reuse.md
│   ├── rfc-002-trinity-protocol.md
│   └── template.md
├── reference/                          # Technical reference
│   ├── api/                           # API documentation
│   │   ├── rest-api.md
│   │   ├── websocket-api.md
│   │   └── openapi.yaml
│   ├── cli/                           # CLI reference
│   ├── configuration/                 # Config file reference
│   └── glossary.md
├── development/                        # Development guides
│   ├── setup.md                       # Dev environment setup
│   ├── testing.md
│   ├── deployment.md
│   └── contributing.md
├── sessions/                           # AI collaboration logs
│   ├── README.md                      # Session index
│   ├── 2025-11-20-foundation-phase.md
│   └── 2025-12-06-premortem-analysis.md
└── templates/                          # Document templates
    ├── feature-doc-template.md
    ├── adr-template.md
    └── rfc-template.md
```

---

## Key Changes from Your Proposal

### ❌ Removed
1. **`progress/` folder**: Use frontmatter + Git tags instead
2. **`analysis/` folder**: Merged into `features/` or `decisions/`
3. **`_archive/` folder**: Use in-document deprecation warnings

### ✅ Added
1. **`getting-started/`**: Industry standard for onboarding
2. **`development/`**: Developer-focused guides separate from features
3. **`reference/api/`**: API docs as distinct category
4. **`sessions/`**: Renamed from Obsidian-specific, more generic

### ✅ Enhanced
1. **Feature folders**: Include analysis, implementation notes, performance docs
2. **`decisions/` and `proposals/`**: Added README.md for indexing
3. **`reference/`**: Split into api/, cli/, configuration/ subcategories

---

## Implementation Recommendations

### Phase 1: Immediate Migration (Week 1)

**Goal**: Move 129 root files into categories

**Priority mapping**:
```bash
# High-value features (move first)
KANBAN_*.md                  → features/kanban/
TIME_TRACKING_*.md           → features/time-tracking/
GI_CK_*.md                   → features/gi-ck-theory/
UNCERTAINTY_*.md             → features/uncertainty-map/

# Architecture docs
ARCHITECTURE_*.md            → architecture/
BACKEND_ARCHITECTURE_*.md    → architecture/
FRONTEND_ARCHITECTURE_*.md   → architecture/

# Decisions and proposals
*_DECISION_*.md              → decisions/
*_PROPOSAL_*.md              → proposals/
*_RFC_*.md                   → proposals/
PREMORTEM_ANALYSIS_*.md      → decisions/

# Development and process
DEVELOPMENT_ROADMAP_*.md     → development/ or proposals/
CLAUDE_WORKLOG_*.md          → sessions/
WEEK*_*.md                   → sessions/

# Reference material
*_API_*.md                   → reference/api/
*_GUIDE_*.md                 → getting-started/ or features/
glossary.md                  → reference/
```

**Migration script** (bash example):
```bash
#!/bin/bash
# Run from docs/ directory

# Create new structure
mkdir -p getting-started features/{kanban,time-tracking,gi-ck-theory,uncertainty-map}
mkdir -p architecture decisions proposals reference/{api,cli,configuration}
mkdir -p development sessions templates

# Move Kanban docs
mv KANBAN_*.md features/kanban/
mv *kanban*.md features/kanban/

# Move architecture docs
mv ARCHITECTURE_*.md architecture/
mv BACKEND_ARCHITECTURE_*.md architecture/
mv FRONTEND_ARCHITECTURE_*.md architecture/

# Move decisions
mv *DECISION*.md decisions/
mv PREMORTEM_*.md decisions/

# Move session logs
mv CLAUDE_WORKLOG_*.md sessions/
mv WEEK*.md sessions/

# Move glossary
mv glossary.md reference/

echo "Migration complete. Review and adjust as needed."
```

---

### Phase 2: Add Navigation and Frontmatter (Week 2)

**Top-level README.md**:
```markdown
# UDO Development Platform Documentation

## Quick Links
- [Getting Started](./getting-started/installation.md)
- [Feature Documentation](./features/)
- [Architecture Overview](./architecture/overview.md)
- [API Reference](./reference/api/)

## Documentation Structure

### For Users
- **[Getting Started](./getting-started/)**: Installation, first project, architecture overview
- **[Features](./features/)**: Complete documentation for each feature
- **[Reference](./reference/)**: API, CLI, configuration reference

### For Developers
- **[Development Guides](./development/)**: Setup, testing, deployment
- **[Architecture](./architecture/)**: System design and technical architecture
- **[Decisions](./decisions/)**: Architecture Decision Records (ADRs)
- **[Proposals](./proposals/)**: Request for Comments (RFCs)

### For AI Collaborators
- **[Sessions](./sessions/)**: AI collaboration logs and worklogs
- **[Templates](./templates/)**: Document templates for consistency
```

**Feature README template** (`features/kanban/README.md`):
```markdown
# Kanban Feature Documentation

**Status**: Production ✅
**Phase**: Week 3 Complete
**Version**: 1.0.0
**Last Updated**: 2025-12-05

## Overview
Context-aware Kanban board with AI-powered task management and dependency tracking.

## Documentation

### User Documentation
- [User Guide](./user-guide.md) - How to use Kanban features
- [Quick Reference](./quick-reference.md) - Common operations

### Technical Documentation
- [Implementation Summary](./implementation-summary.md) - Technical overview
- [API Reference](./api-reference.md) - REST and WebSocket APIs
- [Database Schema](./database-schema.md) - PostgreSQL schema design
- [UI Components](./ui-components.md) - React component specifications

### Performance and Analysis
- [Performance Analysis](./performance-analysis.md) - Benchmarks and optimization
- [Integration Strategy](./integration-strategy.md) - UDO integration points

## Key Decisions
- [Q1-Q8 Strategic Decisions](../../decisions/001-kanban-strategy.md)
- [Multi-project design](../../decisions/002-multi-project-kanban.md)

## Related Features
- [Time Tracking](../time-tracking/) - ROI measurement
- [Uncertainty Map](../uncertainty-map/) - Risk prediction
```

**Document frontmatter standard**:
```yaml
---
title: Kanban Implementation Summary
feature: kanban
category: implementation
status: complete
version: 1.0.0
created: 2025-12-05
updated: 2025-12-05
tags: [kanban, implementation, week-3]
related:
  - features/time-tracking/integration.md
  - decisions/001-kanban-strategy.md
---
```

---

### Phase 3: Deprecation Strategy (Ongoing)

**Instead of archive folder, use status frontmatter**:

```yaml
---
title: Legacy Authentication System
status: deprecated
deprecated_since: 2025-11-01
deprecated_reason: Replaced by JWT-based authentication
replacement: features/kanban/authentication-v2.md
sunset_date: 2026-01-01
---

⚠️ **DEPRECATED**

This authentication system is deprecated as of **2025-11-01**.

**Reason**: Security improvements and JWT standard adoption
**Replacement**: [Authentication v2](./authentication-v2.md)
**Sunset Date**: 2026-01-01 (removed from codebase)

Please migrate to the new authentication system by the sunset date.
See [Migration Guide](./auth-migration-guide.md) for step-by-step instructions.
```

**Rendering with warning banner** (if using static site generator):
- Docusaurus: Uses `deprecated` frontmatter to render banner
- MkDocs: Custom plugin to detect `status: deprecated`
- VitePress: Custom component for deprecation warnings

**Benefits**:
- Links remain valid (no 404s)
- Search engines index with deprecation context
- Users guided to replacement
- Git history preserves complete timeline

---

## Naming Conventions

### File Naming Standards

**Use lowercase with hyphens** (follows industry standard):

✅ **Good**:
```
features/kanban/implementation-summary.md
features/kanban/user-guide.md
architecture/backend-architecture.md
decisions/001-kanban-task-relationship.md
```

❌ **Avoid**:
```
features/kanban/IMPLEMENTATION_SUMMARY.md     # All caps
features/kanban/UserGuide.md                  # PascalCase
features/kanban/implementation_summary.md     # Snake_case (Python convention, not for docs)
```

**Exception**: `README.md` is universally capitalized

---

### Folder Naming Standards

**No numbered prefixes on feature folders**:

✅ **Good**:
```
features/kanban/
features/time-tracking/
features/gi-ck-theory/
```

❌ **Avoid**:
```
features/01-kanban/              # Next.js uses numbers only for content types
features/02-time-tracking/       # Not for features
features/03-gi-ck-theory/
```

**When to use numbered prefixes**:
- ✅ Tutorial steps: `tutorial/01-getting-started/`, `tutorial/02-first-project/`
- ✅ Content type ordering: `01-getting-started/`, `02-guides/`, `03-api-reference/`
- ❌ Feature folders: Features are not sequential, users jump directly to them

---

### ADR and RFC Numbering

**Architecture Decision Records** (decisions/):
```
001-kanban-task-phase-relationship.md
002-multi-project-strategy.md
003-archiving-strategy.md
```

**Request for Comments** (proposals/):
```
rfc-001-rl-guided-knowledge-reuse.md
rfc-002-trinity-protocol.md
rfc-003-codex-integration.md
```

**Format**: `NNN-descriptive-title.md` where NNN is zero-padded

---

## Versioning Strategy

### Document Versioning (Frontmatter)

**Use frontmatter for version tracking**:

```yaml
---
title: Kanban API Reference
version: 2.0.0
api_version: v2
created: 2025-11-01
updated: 2025-12-05
changelog:
  - version: 2.0.0
    date: 2025-12-05
    changes: Added bulk update endpoints
  - version: 1.1.0
    date: 2025-11-20
    changes: Added WebSocket support
  - version: 1.0.0
    date: 2025-11-15
    changes: Initial release
---
```

**Benefits**:
- Single source of truth
- Version history embedded in document
- No need for separate version folders

---

### Code Versioning (Git Tags)

**Use Git tags for major milestones**:

```bash
git tag -a v1.0.0 -m "Kanban feature complete"
git tag -a v1.1.0 -m "WebSocket support added"
git tag -a v2.0.0 -m "Bulk operations API"
```

**View documentation at specific version**:
```bash
git checkout v1.0.0
cd docs/features/kanban/
```

**Benefits**:
- Time travel to any version
- No folder duplication
- Automated changelog generation

---

### API Versioning (Separate from Docs)

**API versioning in code**, not docs structure:

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── kanban.py
│   │   │   └── time_tracking.py
│   │   └── v2/
│   │       ├── kanban.py
│   │       └── time_tracking.py
```

**Documentation references API version**:

```markdown
# Kanban API Reference

**API Version**: v2
**Endpoint**: `/api/v2/kanban`

## Breaking Changes from v1
- `status` field renamed to `state`
- `priority` now uses numeric scale (1-5) instead of string
```

---

## Documentation Tools and Automation

### Recommended Static Site Generators

#### Option 1: MkDocs (Python ecosystem)
**Why MkDocs**:
- Simple Markdown-based
- Python tooling (matches UDO backend)
- Material theme is excellent
- Search built-in

**Configuration** (`mkdocs.yml`):
```yaml
site_name: UDO Development Platform
theme:
  name: material
  features:
    - navigation.sections
    - navigation.expand
    - search.suggest

nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - First Project: getting-started/first-project.md
  - Features:
    - Kanban: features/kanban/README.md
    - Time Tracking: features/time-tracking/README.md
  - Architecture: architecture/
  - Reference:
    - API: reference/api/
    - CLI: reference/cli/
```

**Install**:
```bash
pip install mkdocs-material
mkdocs serve  # Local preview
mkdocs build  # Generate static site
```

---

#### Option 2: VitePress (JavaScript ecosystem)
**Why VitePress**:
- Vue-based (if frontend is Vue/React)
- Fast and modern
- Excellent TypeScript support
- Great for component documentation

**Configuration** (`.vitepress/config.ts`):
```typescript
export default {
  title: 'UDO Development Platform',
  description: 'AI-powered development automation',
  themeConfig: {
    nav: [
      { text: 'Guide', link: '/getting-started/' },
      { text: 'Features', link: '/features/' },
      { text: 'API', link: '/reference/api/' }
    ],
    sidebar: {
      '/features/': [
        {
          text: 'Features',
          items: [
            { text: 'Kanban', link: '/features/kanban/' },
            { text: 'Time Tracking', link: '/features/time-tracking/' }
          ]
        }
      ]
    }
  }
}
```

---

### Documentation Quality Checks

**Automated validation** (GitHub Actions):

```yaml
# .github/workflows/docs-validation.yml
name: Documentation Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # Check for broken links
      - name: Link Checker
        uses: lycheeverse/lychee-action@v1
        with:
          args: --verbose --no-progress 'docs/**/*.md'

      # Validate frontmatter
      - name: Frontmatter Validation
        run: |
          python scripts/validate_frontmatter.py

      # Check for required sections
      - name: Structure Validation
        run: |
          # Ensure each feature has README.md
          for dir in docs/features/*/; do
            if [ ! -f "$dir/README.md" ]; then
              echo "Missing README.md in $dir"
              exit 1
            fi
          done
```

**Frontmatter validation script** (`scripts/validate_frontmatter.py`):
```python
import yaml
from pathlib import Path

REQUIRED_FIELDS = ['title', 'created', 'updated', 'status']

def validate_frontmatter(file_path):
    content = file_path.read_text()
    if not content.startswith('---'):
        return True  # No frontmatter required for all files

    frontmatter = content.split('---')[1]
    data = yaml.safe_load(frontmatter)

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        print(f"❌ {file_path}: Missing fields: {missing}")
        return False

    return True

# Run validation
docs_dir = Path('docs')
failures = []
for md_file in docs_dir.rglob('*.md'):
    if not validate_frontmatter(md_file):
        failures.append(md_file)

if failures:
    print(f"\n{len(failures)} files failed validation")
    exit(1)
else:
    print("✅ All files passed validation")
```

---

## Migration Checklist

### Pre-Migration

- [ ] **Backup current docs**: `git tag pre-migration && git push --tags`
- [ ] **Inventory all files**: Generate file list and categorization
- [ ] **Identify duplicates**: Find overlapping content to merge
- [ ] **Create folder structure**: Implement recommended structure

### Migration Phase 1 (Week 1)

- [ ] **Move feature docs**: Kanban, Time Tracking, GI/CK Theory, Uncertainty Map
- [ ] **Move architecture docs**: System architecture, backend, frontend
- [ ] **Move decisions**: ADRs and analysis documents
- [ ] **Move proposals**: RFCs and roadmaps
- [ ] **Move sessions**: AI collaboration logs
- [ ] **Update internal links**: Fix all relative links

### Migration Phase 2 (Week 2)

- [ ] **Add frontmatter**: Add YAML frontmatter to all key documents
- [ ] **Create README files**: Add navigation README to each folder
- [ ] **Add templates**: Create document templates
- [ ] **Generate index**: Create top-level documentation index
- [ ] **Validate structure**: Run link checker and structure validation

### Post-Migration

- [ ] **Update CLAUDE.md**: Point to new documentation locations
- [ ] **Update CI/CD**: Adjust documentation build pipelines
- [ ] **Test navigation**: Verify all links work
- [ ] **Archive old structure**: Tag current state before final commit
- [ ] **Document migration**: Add migration notes to changelog

---

## Conclusion

### Final Recommendations Summary

1. **Use hybrid feature-type organization** (not time-based)
2. **No numbered prefixes on feature folders** (only for ordered content types)
3. **No separate archive folder** (use in-document deprecation)
4. **Add missing folders**: `getting-started/`, `development/`, `reference/api/`
5. **Use frontmatter for versioning** (not folder structure)
6. **Implement automated validation** (link checking, frontmatter validation)

### Immediate Next Steps

1. **This week**: Implement Phase 1 migration (move files into categories)
2. **Next week**: Add frontmatter and README files
3. **Week 3**: Set up static site generator (MkDocs or VitePress)
4. **Week 4**: Implement automated validation and CI/CD

### Long-Term Benefits

- **Better navigation**: Users find docs by feature, not by date
- **Reduced maintenance**: No archive folder to manage
- **Future-proof**: Structure scales as features grow
- **Industry alignment**: Familiar structure for external contributors
- **Better search**: Search engines and tools index properly organized content

---

**Document Status**: Complete
**Reviewed By**: Claude Code (Technical Writer)
**Date**: 2025-12-13
