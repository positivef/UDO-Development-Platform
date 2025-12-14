-- Migration 004: Kanban-UDO Integration Database Schema
-- Date: 2025-12-04
-- Purpose: Create Kanban task management system integrated with UDO Platform
-- Dependencies: 001_initial_schema.sql, 002_time_tracking_schema.sql, 003_phase_transitions.sql

-- ==================================================================
-- 1. Create Kanban Schema
-- ==================================================================

CREATE SCHEMA IF NOT EXISTS kanban;

COMMENT ON SCHEMA kanban IS 'Kanban task management system integrated with UDO Platform v3.0';

-- ==================================================================
-- 2. Core Tables
-- ==================================================================

-- 2.1 Tasks Table
-- Purpose: Core task management with phase relationship (Q1: Task within Phase)
CREATE TABLE kanban.tasks (
    -- Primary Key
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic Info
    title VARCHAR(255) NOT NULL,
    description TEXT,

    -- Phase Relationship (Q1: Task within Phase)
    phase_id UUID NOT NULL,
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
    approved_by VARCHAR(100),
    approval_timestamp TIMESTAMP,

    -- Quality Gate (Q3: Hybrid completion)
    quality_gate_passed BOOLEAN NOT NULL DEFAULT FALSE,
    quality_score INTEGER CHECK (quality_score >= 0 AND quality_score <= 100),
    constitutional_compliant BOOLEAN NOT NULL DEFAULT TRUE,
    violated_articles TEXT[],

    -- User Confirmation (Q3)
    user_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    confirmed_by VARCHAR(100),
    confirmed_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    archived_at TIMESTAMP
);

COMMENT ON TABLE kanban.tasks IS 'Core Kanban tasks with phase integration and quality gates';
COMMENT ON COLUMN kanban.tasks.ai_suggested IS 'Q2: Task created by AI suggestion (requires user approval)';
COMMENT ON COLUMN kanban.tasks.quality_gate_passed IS 'Q3: Automated quality checks passed';
COMMENT ON COLUMN kanban.tasks.user_confirmed IS 'Q3: User manually confirmed task completion';

-- Indexes for performance (<50ms queries for 1,000 tasks)
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

-- 2.2 Dependencies Table
-- Purpose: DAG structure for task dependencies (Q7: Hard Block dependencies)
CREATE TABLE kanban.dependencies (
    dependency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task References
    source_task_id UUID NOT NULL REFERENCES kanban.tasks(task_id) ON DELETE CASCADE,
    target_task_id UUID NOT NULL REFERENCES kanban.tasks(task_id) ON DELETE CASCADE,

    -- Dependency Type (4 types: FS/SS/FF/SF)
    dependency_type VARCHAR(20) NOT NULL DEFAULT 'finish_to_start' CHECK (dependency_type IN (
        'finish_to_start',  -- FS: Most common
        'start_to_start',   -- SS: Parallel tasks
        'finish_to_finish', -- FF: Synchronized completion
        'start_to_finish'   -- SF: Rare, legacy handoff
    )),

    -- Lag (in hours, can be negative for lead time)
    lag_hours DECIMAL(10, 2) NOT NULL DEFAULT 0,

    -- Emergency Override (Q7: Emergency bypass with logging)
    emergency_override BOOLEAN NOT NULL DEFAULT FALSE,
    override_reason TEXT,
    override_by VARCHAR(100),
    override_timestamp TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT no_self_dependency CHECK (source_task_id != target_task_id),
    CONSTRAINT unique_dependency UNIQUE (source_task_id, target_task_id, dependency_type)
);

COMMENT ON TABLE kanban.dependencies IS 'DAG structure for task dependencies with cycle prevention';
COMMENT ON COLUMN kanban.dependencies.dependency_type IS 'FS/SS/FF/SF dependency types';
COMMENT ON COLUMN kanban.dependencies.emergency_override IS 'Q7: Emergency bypass of hard block (requires reason)';

-- Indexes for DAG operations
CREATE INDEX idx_dependencies_source ON kanban.dependencies(source_task_id);
CREATE INDEX idx_dependencies_target ON kanban.dependencies(target_task_id);
CREATE INDEX idx_dependencies_type ON kanban.dependencies(dependency_type);
CREATE INDEX idx_dependencies_override ON kanban.dependencies(emergency_override) WHERE emergency_override = TRUE;

-- 2.3 Task Contexts Table
-- Purpose: ZIP-based context storage (Q4: Context loading tracking)
CREATE TABLE kanban.task_contexts (
    context_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES kanban.tasks(task_id) ON DELETE CASCADE,

    -- Context Storage
    context_zip BYTEA, -- ZIP file content (max 50MB enforced by trigger)
    context_metadata JSONB, -- {files: [...], total_size: N, compression_ratio: X}

    -- Q4: Context Loading Tracking
    double_click_loads INTEGER NOT NULL DEFAULT 0, -- Auto-load count
    manual_loads INTEGER NOT NULL DEFAULT 0, -- Popup download count
    last_loaded_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT one_context_per_task UNIQUE (task_id)
);

COMMENT ON TABLE kanban.task_contexts IS 'ZIP-based context storage with 50MB limit';
COMMENT ON COLUMN kanban.task_contexts.double_click_loads IS 'Q4: Auto-load count (double-click behavior)';
COMMENT ON COLUMN kanban.task_contexts.manual_loads IS 'Q4: Manual download count (single-click popup)';

-- Index for context queries
CREATE INDEX idx_task_contexts_task ON kanban.task_contexts(task_id);

-- 2.4 Task Projects Table
-- Purpose: Multi-project mapping (Q5: 1 Primary + max 3 Related)
CREATE TABLE kanban.task_projects (
    task_project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES kanban.tasks(task_id) ON DELETE CASCADE,
    project_id UUID NOT NULL, -- References public.projects(id)

    -- Project Role (Q5: Primary vs Related)
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,

    -- Isolation (Q5: Default isolated, explicit sharing required)
    shared_with_team BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_task_project UNIQUE (task_id, project_id)
);

COMMENT ON TABLE kanban.task_projects IS 'Multi-project mapping: 1 Primary + max 3 Related projects';
COMMENT ON COLUMN kanban.task_projects.is_primary IS 'Q5: Exactly one primary project per task';
COMMENT ON COLUMN kanban.task_projects.shared_with_team IS 'Q5: Default isolated, explicit sharing';

-- Indexes for project queries
CREATE INDEX idx_task_projects_task ON kanban.task_projects(task_id);
CREATE INDEX idx_task_projects_project ON kanban.task_projects(project_id);
CREATE INDEX idx_task_projects_primary ON kanban.task_projects(task_id, is_primary) WHERE is_primary = TRUE;

-- Unique constraint: Exactly 1 primary project per task
CREATE UNIQUE INDEX idx_task_projects_one_primary ON kanban.task_projects(task_id) WHERE is_primary = TRUE;

-- 2.5 Task Archive Table
-- Purpose: Done-End archiving with AI summaries (Q6)
CREATE TABLE kanban.task_archive (
    archive_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL UNIQUE, -- Original task_id (immutable)

    -- Original Task Data (snapshot)
    title VARCHAR(255) NOT NULL,
    description TEXT,
    phase_name VARCHAR(50) NOT NULL,
    estimated_hours DECIMAL(10, 2),
    actual_hours DECIMAL(10, 2),
    quality_score INTEGER,

    -- AI Summary (Q6: Automatic knowledge extraction)
    ai_summary TEXT, -- GPT-4o generated summary
    ai_summary_confidence DECIMAL(3, 2),
    lessons_learned TEXT[], -- Extracted key learnings
    obsidian_synced BOOLEAN NOT NULL DEFAULT FALSE,
    obsidian_note_path TEXT, -- Path to synced Obsidian note

    -- ROI Metrics (Q6: Knowledge asset tracking)
    time_saved_hours DECIMAL(10, 2), -- vs initial estimate
    roi_multiplier DECIMAL(5, 2), -- (time_saved / actual_hours)

    -- Timestamps
    archived_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NOT NULL, -- Original completion time

    -- Partitioning key (for year-based partitioning)
    archive_year INTEGER NOT NULL GENERATED ALWAYS AS (EXTRACT(YEAR FROM archived_at)) STORED
);

COMMENT ON TABLE kanban.task_archive IS 'Immutable Done-End archive with AI summaries and Obsidian sync';
COMMENT ON COLUMN kanban.task_archive.ai_summary IS 'Q6: GPT-4o generated knowledge extraction';
COMMENT ON COLUMN kanban.task_archive.obsidian_synced IS 'Q6: Synced to Obsidian knowledge base';

-- Indexes for archive queries
CREATE INDEX idx_task_archive_year ON kanban.task_archive(archive_year);
CREATE INDEX idx_task_archive_phase ON kanban.task_archive(phase_name);
CREATE INDEX idx_task_archive_archived_at ON kanban.task_archive(archived_at DESC);
CREATE INDEX idx_task_archive_obsidian ON kanban.task_archive(obsidian_synced) WHERE obsidian_synced = FALSE;

-- GIN index for full-text search on summaries
CREATE INDEX idx_task_archive_summary_search ON kanban.task_archive USING GIN(to_tsvector('english', ai_summary));
CREATE INDEX idx_task_archive_lessons_search ON kanban.task_archive USING GIN(lessons_learned);

-- 2.6 Quality Gates Table
-- Purpose: Constitutional compliance tracking (P1-P17)
CREATE TABLE kanban.quality_gates (
    gate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES kanban.tasks(task_id) ON DELETE CASCADE,

    -- Gate Type
    gate_type VARCHAR(50) NOT NULL CHECK (gate_type IN (
        'code_quality',      -- Pylint/ESLint
        'test_coverage',     -- pytest-cov
        'constitutional',    -- P1-P17 compliance
        'code_review',       -- PR approval
        'performance',       -- Benchmarks
        'security'           -- Security scan
    )),

    -- Gate Status
    passed BOOLEAN NOT NULL DEFAULT FALSE,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    violations TEXT[], -- e.g., ['P1: Design Review First', 'P5: ...']

    -- Evidence
    evidence_url TEXT, -- Link to test report, PR, etc.

    -- Timestamps
    checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_task_gate_type UNIQUE (task_id, gate_type)
);

COMMENT ON TABLE kanban.quality_gates IS 'Quality gate tracking for constitutional compliance';
COMMENT ON COLUMN kanban.quality_gates.violations IS 'Constitutional articles violated (P1-P17)';

-- Indexes for quality gate queries
CREATE INDEX idx_quality_gates_task ON kanban.quality_gates(task_id);
CREATE INDEX idx_quality_gates_type ON kanban.quality_gates(gate_type);
CREATE INDEX idx_quality_gates_passed ON kanban.quality_gates(passed);

-- 2.7 Dependency Audit Table
-- Purpose: Emergency override logging (Q7: Accountability)
CREATE TABLE kanban.dependency_audit (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dependency_id UUID NOT NULL REFERENCES kanban.dependencies(dependency_id) ON DELETE CASCADE,

    -- Override Details
    override_by VARCHAR(100) NOT NULL,
    override_reason TEXT NOT NULL,
    emergency_justification TEXT, -- Required for emergency overrides

    -- Impact Assessment
    affected_tasks UUID[], -- Tasks impacted by override
    estimated_delay_hours DECIMAL(10, 2),

    -- Approval (for high-impact overrides)
    approved_by VARCHAR(100),
    approval_timestamp TIMESTAMP,

    -- Timestamps
    override_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE kanban.dependency_audit IS 'Audit log for dependency emergency overrides';
COMMENT ON COLUMN kanban.dependency_audit.emergency_justification IS 'Q7: Required justification for emergency bypass';

-- Index for audit queries
CREATE INDEX idx_dependency_audit_timestamp ON kanban.dependency_audit(override_timestamp DESC);
CREATE INDEX idx_dependency_audit_user ON kanban.dependency_audit(override_by);

-- ==================================================================
-- 3. Triggers & Functions
-- ==================================================================

-- 3.1 Auto-update timestamp trigger function
CREATE OR REPLACE FUNCTION kanban.update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tasks table
CREATE TRIGGER update_tasks_modtime
    BEFORE UPDATE ON kanban.tasks
    FOR EACH ROW
    EXECUTE FUNCTION kanban.update_modified_column();

-- Apply to task_contexts table
CREATE TRIGGER update_task_contexts_modtime
    BEFORE UPDATE ON kanban.task_contexts
    FOR EACH ROW
    EXECUTE FUNCTION kanban.update_modified_column();

-- 3.2 Validate DAG (prevent circular dependencies)
CREATE OR REPLACE FUNCTION kanban.validate_dag()
RETURNS TRIGGER AS $$
DECLARE
    has_cycle BOOLEAN;
BEGIN
    -- Check for cycles using recursive CTE
    WITH RECURSIVE dependency_path AS (
        -- Start from the new dependency
        SELECT NEW.source_task_id AS current_task, NEW.target_task_id AS visited_task, 1 AS depth
        UNION ALL
        -- Follow the chain
        SELECT dp.current_task, d.target_task_id, dp.depth + 1
        FROM dependency_path dp
        JOIN kanban.dependencies d ON d.source_task_id = dp.visited_task
        WHERE dp.depth < 100 -- Prevent infinite loops
    )
    SELECT EXISTS(
        SELECT 1 FROM dependency_path
        WHERE current_task = visited_task
    ) INTO has_cycle;

    IF has_cycle THEN
        RAISE EXCEPTION 'Circular dependency detected: Task % → Task %', NEW.source_task_id, NEW.target_task_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_dependency_dag
    BEFORE INSERT OR UPDATE ON kanban.dependencies
    FOR EACH ROW
    EXECUTE FUNCTION kanban.validate_dag();

-- 3.3 Enforce max 3 related projects (Q5)
CREATE OR REPLACE FUNCTION kanban.enforce_max_related_projects()
RETURNS TRIGGER AS $$
DECLARE
    related_count INTEGER;
BEGIN
    IF NEW.is_primary = FALSE THEN
        SELECT COUNT(*) INTO related_count
        FROM kanban.task_projects
        WHERE task_id = NEW.task_id AND is_primary = FALSE;

        IF related_count >= 3 THEN
            RAISE EXCEPTION 'Task can have maximum 3 related projects (Q5 decision)';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_related_projects_limit
    BEFORE INSERT ON kanban.task_projects
    FOR EACH ROW
    EXECUTE FUNCTION kanban.enforce_max_related_projects();

-- 3.4 Enforce 50MB context size limit
CREATE OR REPLACE FUNCTION kanban.enforce_context_size_limit()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.context_zip IS NOT NULL AND octet_length(NEW.context_zip) > 52428800 THEN -- 50MB
        RAISE EXCEPTION 'Context ZIP size exceeds 50MB limit';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_context_size
    BEFORE INSERT OR UPDATE ON kanban.task_contexts
    FOR EACH ROW
    EXECUTE FUNCTION kanban.enforce_context_size_limit();

-- ==================================================================
-- 4. Initial Data & Configuration
-- ==================================================================

-- Create default quality gate types
INSERT INTO kanban.quality_gates (task_id, gate_type, passed, score)
SELECT gen_random_uuid(), gen_random_uuid(), FALSE, 0
FROM generate_series(1, 0); -- No initial data, just schema

-- ==================================================================
-- Migration Complete
-- ==================================================================

-- Verify tables created
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'kanban';

    RAISE NOTICE 'Kanban schema migration complete: % tables created', table_count;
END $$;
