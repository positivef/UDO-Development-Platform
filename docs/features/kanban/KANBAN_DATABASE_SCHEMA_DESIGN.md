# Kanban-UDO Database Schema Design

**Date**: 2025-12-04
**Version**: 1.0.0
**Status**: Design Complete
**Priority**: CRITICAL

---

## Executive Summary

Comprehensive PostgreSQL database schema for Kanban task management integrated with UDO Platform. Based on Q1-Q8 decisions, this schema prioritizes:
- **Performance**: <50ms queries for 10,000 tasks
- **Integrity**: DAG validation, no circular dependencies
- **Scalability**: Partitioning for archive, indexes for fast lookups
- **Integration**: Seamless connection with existing UDO tables

### Key Features
- **Task-Phase Relationship**: Tasks belong to phases (1:N)
- **DAG Dependencies**: 4 types (FS/SS/FF/SF) with cycle prevention
- **Multi-Project Support**: Primary + related projects (max 3)
- **Context Storage**: ZIP-based with 50MB limit
- **Archive System**: Done-End with AI summaries
- **Quality Gates**: Constitutional compliance (P1-P17)

---

## 1. Database Architecture

### 1.1 Schema Overview

```sql
-- New schema for Kanban system
CREATE SCHEMA kanban;

-- Tables:
-- 1. tasks - Core task management
-- 2. dependencies - DAG structure with topological sort support
-- 3. task_contexts - ZIP-based context storage
-- 4. task_projects - Multi-project mapping (Primary + Related)
-- 5. task_archive - Done-End archiving with AI summaries
-- 6. quality_gates - Constitutional compliance tracking
-- 7. dependency_audit - Emergency override logging
```

### 1.2 Integration with Existing UDO Tables

```sql
-- Existing tables used:
-- - public.phases (from UDO v2)
-- - public.uncertainty_predictions (from Uncertainty Map v3)
-- - public.quality_metrics (from quality_service)
-- - public.time_tracking (from time_tracking_service)
-- - public.projects (from project_context_service)
```

---

## 2. Table Definitions

### 2.1 Tasks Table

**Purpose**: Core task management with phase relationship

```sql
CREATE TABLE kanban.tasks (
    -- Primary Key
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic Info
    title VARCHAR(255) NOT NULL,
    description TEXT,

    -- Phase Relationship (Q1: Task within Phase)
    phase_id UUID NOT NULL REFERENCES public.phases(id) ON DELETE CASCADE,
    phase_name VARCHAR(50) NOT NULL CHECK (phase_name IN (
        'ideation', 'design', 'mvp', 'implementation', 'testing'
    )),

    -- Status & Priority
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'in_progress', 'blocked', 'completed', 'done_end'
    )),
    priority VARCHAR(50) NOT NULL DEFAULT 'medium' CHECK (priority IN (
        'critical', 'high', 'medium', 'low'
    )),

    -- Progress Tracking
    completeness INTEGER NOT NULL DEFAULT 0 CHECK (completeness >= 0 AND completeness <= 100),

    -- Time Estimates
    estimated_hours DECIMAL(10, 2) NOT NULL DEFAULT 0,
    actual_hours DECIMAL(10, 2) NOT NULL DEFAULT 0,

    -- AI Creation (Q2: AI Hybrid creation)
    ai_suggested BOOLEAN NOT NULL DEFAULT FALSE,
    ai_confidence DECIMAL(3, 2) CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
    approved_by VARCHAR(100), -- User who approved AI suggestion
    approval_timestamp TIMESTAMP,

    -- Quality Gate (Q3: Hybrid completion)
    quality_gate_passed BOOLEAN NOT NULL DEFAULT FALSE,
    quality_score INTEGER CHECK (quality_score >= 0 AND quality_score <= 100),
    constitutional_compliant BOOLEAN NOT NULL DEFAULT TRUE,
    violated_articles TEXT[], -- e.g., ['P1', 'P5']

    -- User Confirmation (Q3)
    user_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    confirmed_by VARCHAR(100),
    confirmed_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    archived_at TIMESTAMP,

    -- Indexes
    CONSTRAINT tasks_phase_fk FOREIGN KEY (phase_id) REFERENCES public.phases(id) ON DELETE CASCADE
);

-- Indexes for performance (<50ms queries)
CREATE INDEX idx_tasks_phase ON kanban.tasks(phase_id, phase_name);
CREATE INDEX idx_tasks_status ON kanban.tasks(status);
CREATE INDEX idx_tasks_priority ON kanban.tasks(priority DESC);
CREATE INDEX idx_tasks_created_at ON kanban.tasks(created_at DESC);
CREATE INDEX idx_tasks_completeness ON kanban.tasks(completeness);
CREATE INDEX idx_tasks_quality_gate ON kanban.tasks(quality_gate_passed, user_confirmed);

-- Composite index for Kanban board queries (phase + status)
CREATE INDEX idx_tasks_kanban_board ON kanban.tasks(phase_name, status, priority DESC);

-- GIN index for array search (violated_articles)
CREATE INDEX idx_tasks_violations ON kanban.tasks USING GIN(violated_articles);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION kanban.update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tasks_modtime
    BEFORE UPDATE ON kanban.tasks
    FOR EACH ROW
    EXECUTE FUNCTION kanban.update_modified_column();
```

### 2.2 Dependencies Table (DAG Structure)

**Purpose**: Track task dependencies with 4 types (FS/SS/FF/SF) and prevent cycles

```sql
CREATE TABLE kanban.dependencies (
    -- Primary Key
    dependency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task References
    task_id UUID NOT NULL REFERENCES kanban.tasks(task_id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES kanban.tasks(task_id) ON DELETE CASCADE,

    -- Dependency Type (4 types from ClickUp)
    dependency_type VARCHAR(20) NOT NULL CHECK (dependency_type IN (
        'finish_to_start',  -- FS: Most common (default)
        'start_to_start',   -- SS: Both start together
        'finish_to_finish', -- FF: Both finish together
        'start_to_finish'   -- SF: Rare, complex scheduling
    )),

    -- Hard Block (Q7: Hard Block dependencies)
    is_hard_block BOOLEAN NOT NULL DEFAULT TRUE,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'resolved', 'overridden'
    )),

    -- Emergency Override (Q7)
    emergency_override BOOLEAN NOT NULL DEFAULT FALSE,
    overridden_by VARCHAR(100),
    override_reason TEXT,
    override_timestamp TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,

    -- Constraints
    CONSTRAINT no_self_dependency CHECK (task_id != depends_on_task_id),
    CONSTRAINT unique_dependency UNIQUE (task_id, depends_on_task_id, dependency_type)
);

-- Indexes for dependency graph queries
CREATE INDEX idx_dependencies_task ON kanban.dependencies(task_id);
CREATE INDEX idx_dependencies_depends_on ON kanban.dependencies(depends_on_task_id);
CREATE INDEX idx_dependencies_status ON kanban.dependencies(status);
CREATE INDEX idx_dependencies_hard_block ON kanban.dependencies(is_hard_block, status);

-- Composite index for topological sort (Kahn's Algorithm)
CREATE INDEX idx_dependencies_topological ON kanban.dependencies(task_id, depends_on_task_id, status);

-- DAG Validation Function (prevents cycles)
CREATE OR REPLACE FUNCTION kanban.check_no_cycles()
RETURNS TRIGGER AS $$
DECLARE
    has_cycle BOOLEAN;
BEGIN
    -- Check if adding this dependency would create a cycle
    WITH RECURSIVE dependency_chain AS (
        -- Base case: New dependency
        SELECT NEW.task_id AS start_task, NEW.depends_on_task_id AS current_task, 1 AS depth

        UNION ALL

        -- Recursive case: Follow existing dependencies
        SELECT dc.start_task, d.depends_on_task_id, dc.depth + 1
        FROM dependency_chain dc
        JOIN kanban.dependencies d ON dc.current_task = d.task_id
        WHERE d.status = 'pending'
          AND dc.depth < 100 -- Prevent infinite recursion
    )
    SELECT EXISTS (
        SELECT 1 FROM dependency_chain
        WHERE current_task = start_task -- Cycle detected
    ) INTO has_cycle;

    IF has_cycle THEN
        RAISE EXCEPTION 'Circular dependency detected: task % → task %',
            NEW.task_id, NEW.depends_on_task_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_circular_dependencies
    BEFORE INSERT ON kanban.dependencies
    FOR EACH ROW
    EXECUTE FUNCTION kanban.check_no_cycles();
```

### 2.3 Task Contexts Table (ZIP Storage)

**Purpose**: Store JetBrains-style context (files + Git + breakpoints + Obsidian)

```sql
CREATE TABLE kanban.task_contexts (
    -- Primary Key
    context_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task Reference
    task_id UUID NOT NULL UNIQUE REFERENCES kanban.tasks(task_id) ON DELETE CASCADE,

    -- Context Files
    files JSONB NOT NULL DEFAULT '[]', -- Array of file paths
    file_count INTEGER NOT NULL DEFAULT 0,

    -- Git Info
    git_branch VARCHAR(255),
    last_commit_hash VARCHAR(40),
    last_commit_message TEXT,

    -- ZIP Storage (Q4: Context loading)
    zip_url TEXT, -- S3/storage URL
    zip_size_bytes BIGINT CHECK (zip_size_bytes <= 52428800), -- 50MB limit
    zip_checksum VARCHAR(64), -- SHA-256

    -- Obsidian Notes
    obsidian_notes JSONB DEFAULT '[]', -- Array of note paths

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_loaded_at TIMESTAMP,

    -- Double-click tracking (Q4)
    load_count INTEGER NOT NULL DEFAULT 0,
    avg_load_time_ms INTEGER -- Performance tracking
);

-- Indexes
CREATE INDEX idx_contexts_task ON kanban.task_contexts(task_id);
CREATE INDEX idx_contexts_branch ON kanban.task_contexts(git_branch);
CREATE INDEX idx_contexts_size ON kanban.task_contexts(zip_size_bytes);

-- GIN index for files array search
CREATE INDEX idx_contexts_files ON kanban.task_contexts USING GIN(files jsonb_path_ops);

-- Auto-update timestamp
CREATE TRIGGER update_contexts_modtime
    BEFORE UPDATE ON kanban.task_contexts
    FOR EACH ROW
    EXECUTE FUNCTION kanban.update_modified_column();
```

### 2.4 Task Projects Table (Multi-Project Mapping)

**Purpose**: Track Primary + Related projects (Q5)

```sql
CREATE TABLE kanban.task_projects (
    -- Primary Key
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task Reference
    task_id UUID NOT NULL REFERENCES kanban.tasks(task_id) ON DELETE CASCADE,

    -- Project Reference
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,

    -- Project Role (Q5: Primary + Related)
    is_primary BOOLEAN NOT NULL,

    -- Isolation (Q5-3: Isolated by default)
    is_shared BOOLEAN NOT NULL DEFAULT FALSE, -- Explicit sharing required
    shared_at TIMESTAMP,
    shared_by VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_task_project UNIQUE (task_id, project_id)
);

-- Enforce exactly 1 primary project per task
CREATE UNIQUE INDEX idx_task_projects_primary
    ON kanban.task_projects(task_id)
    WHERE is_primary = TRUE;

-- Limit to 3 related projects (enforced by trigger)
CREATE OR REPLACE FUNCTION kanban.check_related_project_limit()
RETURNS TRIGGER AS $$
DECLARE
    related_count INTEGER;
BEGIN
    IF NEW.is_primary = FALSE THEN
        SELECT COUNT(*) INTO related_count
        FROM kanban.task_projects
        WHERE task_id = NEW.task_id AND is_primary = FALSE;

        IF related_count >= 3 THEN
            RAISE EXCEPTION 'Maximum 3 related projects allowed per task';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_related_project_limit
    BEFORE INSERT ON kanban.task_projects
    FOR EACH ROW
    EXECUTE FUNCTION kanban.check_related_project_limit();

-- Indexes
CREATE INDEX idx_task_projects_task ON kanban.task_projects(task_id);
CREATE INDEX idx_task_projects_project ON kanban.task_projects(project_id);
CREATE INDEX idx_task_projects_primary ON kanban.task_projects(is_primary);
```

### 2.5 Task Archive Table (Done-End State)

**Purpose**: Archiving with AI summaries (Q6)

```sql
CREATE TABLE kanban.task_archive (
    -- Primary Key
    archive_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task Reference (denormalized for performance)
    task_id UUID NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    phase_name VARCHAR(50) NOT NULL,

    -- Completion Info
    quality_score INTEGER NOT NULL,
    constitutional_compliant BOOLEAN NOT NULL,
    violated_articles TEXT[],

    -- Time Tracking
    estimated_hours DECIMAL(10, 2) NOT NULL,
    actual_hours DECIMAL(10, 2) NOT NULL,
    time_variance DECIMAL(10, 2) GENERATED ALWAYS AS (actual_hours - estimated_hours) STORED,

    -- AI Summary (Q6: Obsidian summarization)
    ai_summary JSONB NOT NULL, -- Structure from UI Components Design
    /*
    {
        "generated_at": "2025-12-04T10:30:00Z",
        "summary": "2-3 sentence overview",
        "key_achievements": ["achievement 1", "achievement 2"],
        "lessons_learned": ["lesson 1", "lesson 2"],
        "quality_highlights": "98% test coverage, zero regressions",
        "roi_statement": "Saved 12.5 hours vs estimate"
    }
    */

    -- Obsidian Integration
    obsidian_note_path TEXT, -- Link to Obsidian summary
    knowledge_extracted BOOLEAN NOT NULL DEFAULT FALSE,
    extraction_timestamp TIMESTAMP,

    -- Original Context
    context_zip_url TEXT,

    -- Immutability
    archived_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archived_by VARCHAR(100) NOT NULL,

    -- Search (Full-Text)
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, ''))
    ) STORED
);

-- Partitioning by archive date (performance for large archives)
CREATE TABLE kanban.task_archive_2025 PARTITION OF kanban.task_archive
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Future partitions (auto-create via cron or trigger)
-- CREATE TABLE kanban.task_archive_2026 PARTITION OF kanban.task_archive
--     FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- Indexes
CREATE INDEX idx_archive_task ON kanban.task_archive(task_id);
CREATE INDEX idx_archive_phase ON kanban.task_archive(phase_name);
CREATE INDEX idx_archive_date ON kanban.task_archive(archived_at DESC);
CREATE INDEX idx_archive_roi ON kanban.task_archive(time_variance);
CREATE INDEX idx_archive_quality ON kanban.task_archive(quality_score DESC);

-- Full-text search index
CREATE INDEX idx_archive_search ON kanban.task_archive USING GIN(search_vector);

-- GIN index for AI summary JSON search
CREATE INDEX idx_archive_summary ON kanban.task_archive USING GIN(ai_summary jsonb_path_ops);

-- Prevent updates (immutability)
CREATE OR REPLACE FUNCTION kanban.prevent_archive_updates()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Archive records are immutable';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_archive_modifications
    BEFORE UPDATE ON kanban.task_archive
    FOR EACH ROW
    EXECUTE FUNCTION kanban.prevent_archive_updates();
```

### 2.6 Quality Gates Table (Constitutional Compliance)

**Purpose**: Track P1-P17 compliance per task

```sql
CREATE TABLE kanban.quality_gates (
    -- Primary Key
    gate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task Reference
    task_id UUID NOT NULL REFERENCES kanban.tasks(task_id) ON DELETE CASCADE,

    -- Article Compliance (P1-P17)
    article_id VARCHAR(10) NOT NULL, -- e.g., 'P1', 'P5'
    article_title VARCHAR(255) NOT NULL,
    article_category VARCHAR(50) NOT NULL CHECK (article_category IN (
        'design', 'quality', 'security', 'process'
    )),

    -- Compliance Status
    is_compliant BOOLEAN NOT NULL,
    violation_details TEXT, -- Explanation if violated
    fix_suggestions TEXT[], -- AI-generated suggestions

    -- Verification
    checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checked_by VARCHAR(100) NOT NULL, -- 'ai' or user

    -- Constraints
    CONSTRAINT unique_task_article UNIQUE (task_id, article_id)
);

-- Indexes
CREATE INDEX idx_quality_gates_task ON kanban.quality_gates(task_id);
CREATE INDEX idx_quality_gates_article ON kanban.quality_gates(article_id);
CREATE INDEX idx_quality_gates_compliance ON kanban.quality_gates(is_compliant);
CREATE INDEX idx_quality_gates_category ON kanban.quality_gates(article_category);

-- Composite index for task compliance summary
CREATE INDEX idx_quality_gates_summary ON kanban.quality_gates(task_id, is_compliant);
```

### 2.7 Dependency Audit Table (Emergency Override Logging)

**Purpose**: Audit trail for emergency overrides (Q7)

```sql
CREATE TABLE kanban.dependency_audit (
    -- Primary Key
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Dependency Reference
    dependency_id UUID NOT NULL REFERENCES kanban.dependencies(dependency_id) ON DELETE CASCADE,

    -- Task Info
    task_id UUID NOT NULL,
    depends_on_task_id UUID NOT NULL,

    -- Override Info
    action VARCHAR(50) NOT NULL CHECK (action IN (
        'emergency_override', 'override_revoked', 'dependency_activated', 'dependency_deactivated'
    )),

    -- Authorization
    performed_by VARCHAR(100) NOT NULL,
    reason TEXT NOT NULL,
    authorized_by VARCHAR(100), -- Manager/lead approval
    authorization_timestamp TIMESTAMP,

    -- Timestamps
    performed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Impact Analysis
    downstream_affected_tasks INTEGER, -- How many tasks affected
    estimated_delay_hours DECIMAL(10, 2) -- Schedule impact
);

-- Indexes
CREATE INDEX idx_audit_dependency ON kanban.dependency_audit(dependency_id);
CREATE INDEX idx_audit_task ON kanban.dependency_audit(task_id);
CREATE INDEX idx_audit_action ON kanban.dependency_audit(action);
CREATE INDEX idx_audit_timestamp ON kanban.dependency_audit(performed_at DESC);
```

---

## 3. Integration Views

### 3.1 Complete Task View

**Purpose**: Join all task data for frontend (single query)

```sql
CREATE VIEW kanban.v_complete_tasks AS
SELECT
    t.task_id,
    t.title,
    t.description,
    t.phase_id,
    t.phase_name,
    t.status,
    t.priority,
    t.completeness,
    t.estimated_hours,
    t.actual_hours,
    t.quality_score,
    t.constitutional_compliant,
    t.violated_articles,
    t.created_at,
    t.updated_at,

    -- Primary project
    (
        SELECT jsonb_build_object(
            'project_id', p.id,
            'project_name', p.name,
            'is_primary', TRUE
        )
        FROM kanban.task_projects tp
        JOIN public.projects p ON tp.project_id = p.id
        WHERE tp.task_id = t.task_id AND tp.is_primary = TRUE
    ) AS primary_project,

    -- Related projects
    (
        SELECT jsonb_agg(
            jsonb_build_object(
                'project_id', p.id,
                'project_name', p.name,
                'is_shared', tp.is_shared
            )
        )
        FROM kanban.task_projects tp
        JOIN public.projects p ON tp.project_id = p.id
        WHERE tp.task_id = t.task_id AND tp.is_primary = FALSE
    ) AS related_projects,

    -- Dependencies
    (
        SELECT jsonb_agg(
            jsonb_build_object(
                'dependency_id', d.dependency_id,
                'depends_on_task_id', d.depends_on_task_id,
                'dependency_type', d.dependency_type,
                'is_hard_block', d.is_hard_block,
                'status', d.status
            )
        )
        FROM kanban.dependencies d
        WHERE d.task_id = t.task_id
    ) AS dependencies,

    -- Context preview
    (
        SELECT jsonb_build_object(
            'file_count', tc.file_count,
            'git_branch', tc.git_branch,
            'zip_size_bytes', tc.zip_size_bytes,
            'last_loaded_at', tc.last_loaded_at
        )
        FROM kanban.task_contexts tc
        WHERE tc.task_id = t.task_id
    ) AS context_preview,

    -- Quality gate summary
    (
        SELECT jsonb_build_object(
            'total_articles', COUNT(*),
            'compliant', COUNT(*) FILTER (WHERE is_compliant = TRUE),
            'violations', COUNT(*) FILTER (WHERE is_compliant = FALSE)
        )
        FROM kanban.quality_gates qg
        WHERE qg.task_id = t.task_id
    ) AS quality_gate_summary

FROM kanban.tasks t
WHERE t.status != 'done_end'; -- Exclude archived tasks
```

### 3.2 Dependency Graph View

**Purpose**: Fast dependency graph queries for D3.js visualization

```sql
CREATE VIEW kanban.v_dependency_graph AS
SELECT
    d.dependency_id,
    d.task_id,
    t1.title AS task_title,
    t1.status AS task_status,
    t1.priority AS task_priority,
    d.depends_on_task_id,
    t2.title AS depends_on_title,
    t2.status AS depends_on_status,
    t2.priority AS depends_on_priority,
    d.dependency_type,
    d.is_hard_block,
    d.status AS dependency_status,
    d.emergency_override,
    CASE
        WHEN d.is_hard_block = TRUE AND d.status = 'pending' THEN TRUE
        ELSE FALSE
    END AS is_blocking
FROM kanban.dependencies d
JOIN kanban.tasks t1 ON d.task_id = t1.task_id
JOIN kanban.tasks t2 ON d.depends_on_task_id = t2.task_id
WHERE t1.status != 'done_end' AND t2.status != 'done_end';
```

### 3.3 Archive Statistics View

**Purpose**: ROI metrics for archive view

```sql
CREATE VIEW kanban.v_archive_stats AS
SELECT
    phase_name,
    COUNT(*) AS total_tasks,
    AVG(quality_score) AS avg_quality_score,
    AVG(time_variance) AS avg_time_variance,
    SUM(CASE WHEN time_variance < 0 THEN ABS(time_variance) ELSE 0 END) AS total_time_saved,
    SUM(CASE WHEN constitutional_compliant = TRUE THEN 1 ELSE 0 END) AS compliant_count,
    jsonb_agg(
        jsonb_build_object(
            'task_id', task_id,
            'title', title,
            'roi', time_variance
        )
        ORDER BY time_variance DESC
        LIMIT 5
    ) AS top_5_roi_tasks
FROM kanban.task_archive
GROUP BY phase_name;
```

---

## 4. Performance Optimizations

### 4.1 Query Performance Targets

| Query Type | Target | Index Strategy |
|------------|--------|----------------|
| **List tasks by phase** | <50ms | idx_tasks_kanban_board (composite) |
| **Get task detail** | <100ms | Primary key + view (denormalized) |
| **Dependency graph** | <50ms | idx_dependencies_topological |
| **Search archive** | <300ms | GIN full-text search |
| **Context load** | <1s | idx_contexts_task |

### 4.2 Index Maintenance

```sql
-- Periodic index rebuild (weekly cron)
REINDEX TABLE CONCURRENTLY kanban.tasks;
REINDEX TABLE CONCURRENTLY kanban.dependencies;

-- Vacuum analyze (daily)
VACUUM ANALYZE kanban.tasks;
VACUUM ANALYZE kanban.dependencies;

-- Statistics refresh
ANALYZE kanban.tasks;
ANALYZE kanban.dependencies;
```

### 4.3 Connection Pooling

```python
# backend/app/db/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Connection pool configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Max 20 concurrent connections
    max_overflow=10,       # Allow 10 overflow
    pool_timeout=30,       # 30s wait for connection
    pool_recycle=3600,     # Recycle connections after 1 hour
    echo=False,            # Disable SQL logging in production
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

---

## 5. Migration Strategy

### 5.1 Migration Plan

**Phase 1: Schema Creation** (Week 1 Day 1)
```sql
-- 1. Create kanban schema
CREATE SCHEMA IF NOT EXISTS kanban;

-- 2. Create tables (in dependency order)
-- tasks → dependencies → task_contexts → task_projects → quality_gates
-- → task_archive → dependency_audit

-- 3. Create indexes (parallel)
CREATE INDEX CONCURRENTLY ...;

-- 4. Create views
CREATE VIEW kanban.v_complete_tasks ...;
```

**Phase 2: Data Migration** (Week 1 Day 2)
```sql
-- Migrate existing tasks from public.tasks (if any)
INSERT INTO kanban.tasks (task_id, title, description, phase_id, phase_name, ...)
SELECT id, name, description, phase_id, 'ideation', ...
FROM public.tasks
WHERE created_at > '2025-01-01';

-- Validate migration
SELECT COUNT(*) FROM kanban.tasks;
SELECT COUNT(*) FROM public.tasks;
```

**Phase 3: Application Update** (Week 1 Day 3-4)
```python
# Update all API endpoints to use kanban.tasks
# backend/app/routers/kanban_router.py

from app.models.kanban import Task, Dependency, TaskContext

@router.get("/api/tasks")
async def list_tasks(
    phase: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Task)
    if phase:
        query = query.filter(Task.phase_name == phase)
    if status:
        query = query.filter(Task.status == status)

    result = await db.execute(query)
    return result.scalars().all()
```

**Phase 4: Rollback Strategy** (if needed)
```sql
-- Rollback: Drop kanban schema
DROP SCHEMA kanban CASCADE;

-- Restore from backup
pg_restore -d udo_platform kanban_backup_2025-12-04.dump
```

### 5.2 Database Versioning

```sql
-- Version tracking table
CREATE TABLE public.schema_versions (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100) NOT NULL
);

-- Record this migration
INSERT INTO public.schema_versions (version, description, applied_by)
VALUES ('kanban_v1.0.0', 'Kanban-UDO integration schema', 'system');
```

---

## 6. Backup & Recovery

### 6.1 Backup Strategy

```bash
# Daily backup (cron: 0 2 * * *)
pg_dump -h localhost -U postgres -d udo_platform \
    --schema=kanban \
    --format=custom \
    --file=/backups/kanban_$(date +%Y%m%d).dump

# Weekly full backup (cron: 0 3 * * 0)
pg_dump -h localhost -U postgres -d udo_platform \
    --format=custom \
    --file=/backups/full_backup_$(date +%Y%m%d).dump

# Archive context ZIPs (S3 or object storage)
aws s3 sync /var/kanban/contexts s3://udo-kanban-contexts/$(date +%Y%m%d)/
```

### 6.2 Recovery Procedures

```bash
# Restore kanban schema only
pg_restore -h localhost -U postgres -d udo_platform \
    --schema=kanban \
    --clean \
    kanban_20251204.dump

# Restore specific table
pg_restore -h localhost -U postgres -d udo_platform \
    --table=tasks \
    --schema=kanban \
    kanban_20251204.dump

# Point-in-time recovery (requires WAL archiving)
pg_basebackup + WAL replay to 2025-12-04 10:30:00
```

---

## 7. Monitoring Queries

### 7.1 Health Checks

```sql
-- Check for circular dependencies (should return 0)
WITH RECURSIVE dependency_chain AS (
    SELECT task_id, depends_on_task_id, 1 AS depth
    FROM kanban.dependencies
    WHERE status = 'pending'

    UNION ALL

    SELECT dc.task_id, d.depends_on_task_id, dc.depth + 1
    FROM dependency_chain dc
    JOIN kanban.dependencies d ON dc.depends_on_task_id = d.task_id
    WHERE d.status = 'pending' AND dc.depth < 100
)
SELECT COUNT(*)
FROM dependency_chain
WHERE task_id = depends_on_task_id;

-- Check for orphaned dependencies
SELECT COUNT(*)
FROM kanban.dependencies d
WHERE NOT EXISTS (
    SELECT 1 FROM kanban.tasks t WHERE t.task_id = d.task_id
);

-- Check for tasks exceeding related project limit
SELECT task_id, COUNT(*) AS related_count
FROM kanban.task_projects
WHERE is_primary = FALSE
GROUP BY task_id
HAVING COUNT(*) > 3;
```

### 7.2 Performance Metrics

```sql
-- Query execution time monitoring
SELECT
    query,
    calls,
    total_exec_time / 1000 AS total_time_sec,
    mean_exec_time / 1000 AS avg_time_sec,
    max_exec_time / 1000 AS max_time_sec
FROM pg_stat_statements
WHERE query LIKE '%kanban%'
ORDER BY total_exec_time DESC
LIMIT 10;

-- Index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'kanban'
ORDER BY idx_scan DESC;

-- Table bloat check
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_tup_ins AS inserts,
    n_tup_upd AS updates,
    n_tup_del AS deletes,
    n_live_tup AS live_rows,
    n_dead_tup AS dead_rows
FROM pg_stat_user_tables
WHERE schemaname = 'kanban'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 8. Security Considerations

### 8.1 Row-Level Security (RLS)

```sql
-- Enable RLS on sensitive tables
ALTER TABLE kanban.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE kanban.task_contexts ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see tasks from their projects
CREATE POLICY task_access_policy ON kanban.tasks
FOR SELECT
USING (
    task_id IN (
        SELECT tp.task_id
        FROM kanban.task_projects tp
        JOIN public.project_users pu ON tp.project_id = pu.project_id
        WHERE pu.user_id = current_user_id() -- Custom function
    )
);

-- Policy: Users can only load context from authorized tasks
CREATE POLICY context_access_policy ON kanban.task_contexts
FOR SELECT
USING (
    task_id IN (
        SELECT task_id FROM kanban.tasks
        WHERE -- Uses task_access_policy
    )
);
```

### 8.2 Audit Logging

```sql
-- Audit trail for sensitive operations
CREATE TABLE kanban.audit_log (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    performed_by VARCHAR(100) NOT NULL,
    performed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Trigger function for audit logging
CREATE OR REPLACE FUNCTION kanban.audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO kanban.audit_log (table_name, record_id, operation, old_values, performed_by)
        VALUES (TG_TABLE_NAME, OLD.task_id, 'DELETE', row_to_json(OLD), current_user);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO kanban.audit_log (table_name, record_id, operation, old_values, new_values, performed_by)
        VALUES (TG_TABLE_NAME, NEW.task_id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO kanban.audit_log (table_name, record_id, operation, new_values, performed_by)
        VALUES (TG_TABLE_NAME, NEW.task_id, 'INSERT', row_to_json(NEW), current_user);
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to critical tables
CREATE TRIGGER tasks_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON kanban.tasks
    FOR EACH ROW EXECUTE FUNCTION kanban.audit_trigger_func();

CREATE TRIGGER dependencies_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON kanban.dependencies
    FOR EACH ROW EXECUTE FUNCTION kanban.audit_trigger_func();
```

---

## 9. Testing & Validation

### 9.1 Unit Tests (SQL)

```sql
-- Test 1: Task creation with defaults
DO $$
DECLARE
    v_task_id UUID;
BEGIN
    INSERT INTO kanban.tasks (title, phase_id, phase_name, description)
    VALUES ('Test Task', '00000000-0000-0000-0000-000000000001', 'ideation', 'Test')
    RETURNING task_id INTO v_task_id;

    ASSERT (SELECT status FROM kanban.tasks WHERE task_id = v_task_id) = 'pending';
    ASSERT (SELECT completeness FROM kanban.tasks WHERE task_id = v_task_id) = 0;

    -- Cleanup
    DELETE FROM kanban.tasks WHERE task_id = v_task_id;

    RAISE NOTICE 'Test 1: PASSED';
END $$;

-- Test 2: Circular dependency prevention
DO $$
DECLARE
    v_task1 UUID := gen_random_uuid();
    v_task2 UUID := gen_random_uuid();
    v_raised BOOLEAN := FALSE;
BEGIN
    -- Create two tasks
    INSERT INTO kanban.tasks (task_id, title, phase_id, phase_name)
    VALUES (v_task1, 'Task 1', '00000000-0000-0000-0000-000000000001', 'ideation'),
           (v_task2, 'Task 2', '00000000-0000-0000-0000-000000000001', 'ideation');

    -- Create dependency: task1 → task2
    INSERT INTO kanban.dependencies (task_id, depends_on_task_id, dependency_type)
    VALUES (v_task1, v_task2, 'finish_to_start');

    -- Try to create circular dependency: task2 → task1 (should fail)
    BEGIN
        INSERT INTO kanban.dependencies (task_id, depends_on_task_id, dependency_type)
        VALUES (v_task2, v_task1, 'finish_to_start');
    EXCEPTION
        WHEN OTHERS THEN
            v_raised := TRUE;
    END;

    ASSERT v_raised = TRUE;

    -- Cleanup
    DELETE FROM kanban.tasks WHERE task_id IN (v_task1, v_task2);

    RAISE NOTICE 'Test 2: PASSED';
END $$;

-- Test 3: Related project limit (max 3)
DO $$
DECLARE
    v_task_id UUID := gen_random_uuid();
    v_project1 UUID := '00000000-0000-0000-0000-000000000001';
    v_project2 UUID := '00000000-0000-0000-0000-000000000002';
    v_project3 UUID := '00000000-0000-0000-0000-000000000003';
    v_project4 UUID := '00000000-0000-0000-0000-000000000004';
    v_raised BOOLEAN := FALSE;
BEGIN
    -- Create task
    INSERT INTO kanban.tasks (task_id, title, phase_id, phase_name)
    VALUES (v_task_id, 'Test', '00000000-0000-0000-0000-000000000001', 'ideation');

    -- Create projects (assuming they exist)
    -- Add primary project
    INSERT INTO kanban.task_projects (task_id, project_id, is_primary)
    VALUES (v_task_id, v_project1, TRUE);

    -- Add 3 related projects
    INSERT INTO kanban.task_projects (task_id, project_id, is_primary)
    VALUES (v_task_id, v_project2, FALSE),
           (v_task_id, v_project3, FALSE),
           (v_task_id, v_project4, FALSE);

    -- Try to add 4th related (should fail)
    BEGIN
        INSERT INTO kanban.task_projects (task_id, project_id, is_primary)
        VALUES (v_task_id, '00000000-0000-0000-0000-000000000005', FALSE);
    EXCEPTION
        WHEN OTHERS THEN
            v_raised := TRUE;
    END;

    ASSERT v_raised = TRUE;

    -- Cleanup
    DELETE FROM kanban.tasks WHERE task_id = v_task_id;

    RAISE NOTICE 'Test 3: PASSED';
END $$;
```

---

## Appendix: ERD Diagram

```
┌─────────────────────┐
│   public.phases     │
│  (existing UDO v2)  │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────┴──────────────────────────────────────────────┐
│                  kanban.tasks                           │
│ ─────────────────────────────────────────────────────── │
│ PK: task_id (UUID)                                      │
│ FK: phase_id → public.phases(id)                        │
│ ─────────────────────────────────────────────────────── │
│ title, description, phase_name                          │
│ status, priority, completeness                          │
│ estimated_hours, actual_hours                           │
│ quality_score, constitutional_compliant                 │
│ ai_suggested, ai_confidence                             │
│ quality_gate_passed, user_confirmed                     │
└────┬──────────────┬──────────────┬──────────────┬───────┘
     │              │              │              │
     │ 1            │ 1            │ N            │ 1
     │              │              │              │
     │ N            │ 1            │ 1            │ 1
┌────┴────┐   ┌─────┴────┐   ┌────┴─────┐  ┌────┴─────┐
│kanban.  │   │ kanban.  │   │ kanban.  │  │ kanban.  │
│depend-  │   │ task_    │   │ task_    │  │ quality_ │
│encies   │   │ contexts │   │ projects │  │ gates    │
└─────────┘   └──────────┘   └──────────┘  └──────────┘
     │                              │
     │                              │ FK
     │                              ▼
     │                       ┌─────────────┐
     │                       │  public.    │
     │                       │  projects   │
     │                       │ (existing)  │
     │                       └─────────────┘
     │
     │ (archived tasks)
     ▼
┌──────────────────┐
│ kanban.task_     │
│ archive          │
│ (partitioned)    │
└──────────────────┘
```

---

**Document Status**: COMPLETE - READY FOR IMPLEMENTATION
**Last Updated**: 2025-12-04
**Author**: System Architect (Claude Code)
**Approval Required**: CTO, Database Administrator, Backend Lead

---

**END OF KANBAN DATABASE SCHEMA DESIGN**
