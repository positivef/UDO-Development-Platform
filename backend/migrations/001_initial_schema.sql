-- ============================================================
-- UDO Development Platform - Initial Database Schema
-- Version: 1.0.0
-- Date: 2025-11-17
-- Description: Complete schema for multi-project support
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search

-- ============================================================
-- 1. PROJECTS TABLE
-- ============================================================
-- Core project information and configuration

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    path VARCHAR(500) NOT NULL,

    -- Git configuration
    git_url VARCHAR(500),
    git_branch VARCHAR(100) DEFAULT 'main',

    -- Development phase tracking
    current_phase VARCHAR(50) DEFAULT 'ideation',
    phase_progress JSONB DEFAULT '{
        "ideation": 0,
        "design": 0,
        "mvp": 0,
        "implementation": 0,
        "testing": 0
    }'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW(),

    -- Project settings (JSON)
    settings JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    is_archived BOOLEAN DEFAULT FALSE,

    CONSTRAINT valid_phase CHECK (current_phase IN
        ('ideation', 'design', 'mvp', 'implementation', 'testing')
    )
);

-- Indexes for projects
CREATE INDEX idx_projects_name ON projects(name);
CREATE INDEX idx_projects_last_active ON projects(last_active_at DESC);
CREATE INDEX idx_projects_phase ON projects(current_phase);
CREATE INDEX idx_projects_archived ON projects(is_archived) WHERE is_archived = FALSE;

-- Full-text search on project name and description
CREATE INDEX idx_projects_search ON projects
    USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- ============================================================
-- 2. PROJECT CONTEXTS TABLE
-- ============================================================
-- Auto-loading project context for seamless switching

CREATE TABLE IF NOT EXISTS project_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- UDO System State
    udo_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Example: {
    --   "last_decision": "GO",
    --   "confidence": 0.85,
    --   "quantum_state": "Deterministic",
    --   "uncertainty_map": {...}
    -- }

    -- ML Models state
    ml_models JSONB DEFAULT '{}'::jsonb,
    -- Example: {
    --   "confidence_predictor": "models/confidence_v1.pkl",
    --   "task_classifier": "models/classifier_v2.pkl"
    -- }

    -- Recent executions cache (last 10)
    recent_executions JSONB DEFAULT '[]'::jsonb,

    -- AI service preferences
    ai_preferences JSONB DEFAULT '{}'::jsonb,
    -- Example: {
    --   "preferred_model": "gpt-4",
    --   "temperature": 0.7,
    --   "max_tokens": 2000
    -- }

    -- Editor state
    editor_state JSONB DEFAULT '{}'::jsonb,
    -- Example: {
    --   "open_files": [...],
    --   "cursor_positions": {...},
    --   "breakpoints": [...]
    -- }

    -- Timestamps
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    loaded_at TIMESTAMPTZ,

    UNIQUE(project_id)
);

-- Indexes for project contexts
CREATE INDEX idx_project_contexts_project ON project_contexts(project_id);
CREATE INDEX idx_project_contexts_saved ON project_contexts(saved_at DESC);

-- ============================================================
-- 3. TASK HISTORY TABLE
-- ============================================================
-- Prompt/Code history management and ML training data

CREATE TABLE IF NOT EXISTS task_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- User input
    user_prompt TEXT NOT NULL,
    context_files TEXT[] DEFAULT '{}',

    -- UDO Decision
    decision VARCHAR(50) NOT NULL,  -- GO, GO_WITH_CHECKPOINTS, NO_GO
    confidence DECIMAL(3, 2),  -- 0.00 to 1.00
    quantum_state VARCHAR(50),  -- Deterministic, Probabilistic, Quantum, Chaotic, Void
    uncertainty_state VARCHAR(50),

    -- Suggestions and execution
    suggestions TEXT[],
    executed_commands TEXT[],

    -- Code changes
    files_modified TEXT[],
    files_added TEXT[],
    files_deleted TEXT[],
    lines_added INTEGER DEFAULT 0,
    lines_deleted INTEGER DEFAULT 0,

    -- Git integration
    git_commit VARCHAR(40),  -- SHA hash
    git_branch VARCHAR(100),

    -- Development phase
    phase VARCHAR(50) NOT NULL,

    -- AI tools used
    ai_tools_used TEXT[],  -- ['claude', 'gpt-4', 'gemini']
    ai_model VARCHAR(100),

    -- Execution metrics
    execution_time_ms INTEGER,
    token_usage INTEGER,

    -- Result
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    output_summary TEXT,

    -- Metadata
    executed_at TIMESTAMPTZ DEFAULT NOW(),
    tags TEXT[],
    category VARCHAR(50),  -- feature, bugfix, refactor, docs, test

    -- User feedback
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT
);

-- Indexes for task history
CREATE INDEX idx_task_history_project ON task_history(project_id);
CREATE INDEX idx_task_history_executed ON task_history(executed_at DESC);
CREATE INDEX idx_task_history_phase ON task_history(phase);
CREATE INDEX idx_task_history_decision ON task_history(decision);
CREATE INDEX idx_task_history_success ON task_history(success);
CREATE INDEX idx_task_history_category ON task_history(category);
CREATE INDEX idx_task_history_git_commit ON task_history(git_commit);

-- Full-text search on prompts
CREATE INDEX idx_task_history_prompt_search ON task_history
    USING gin(to_tsvector('english', user_prompt));

-- Composite index for filtering
CREATE INDEX idx_task_history_composite ON task_history(project_id, phase, executed_at DESC);

-- ============================================================
-- 4. VERSION HISTORY TABLE (Cache)
-- ============================================================
-- Cached Git commit information with quality metrics

CREATE TABLE IF NOT EXISTS version_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Git commit info
    commit_hash VARCHAR(40) NOT NULL,
    short_hash VARCHAR(7) NOT NULL,
    author VARCHAR(255) NOT NULL,
    author_email VARCHAR(255) NOT NULL,
    commit_date TIMESTAMPTZ NOT NULL,
    message TEXT NOT NULL,

    -- File changes
    files_modified TEXT[],
    files_added TEXT[],
    files_deleted TEXT[],
    lines_added INTEGER DEFAULT 0,
    lines_deleted INTEGER DEFAULT 0,

    -- Git metadata
    tags TEXT[],
    branches TEXT[],

    -- UDO integration
    udo_execution_id UUID REFERENCES task_history(id),

    -- Quality metrics snapshot
    quality_metrics JSONB,
    -- Example: {
    --   "code_quality": 8.5,
    --   "test_coverage": 85.2,
    --   "complexity": 12,
    --   "security_score": 9.0
    -- }

    -- Cache metadata
    cached_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(project_id, commit_hash)
);

-- Indexes for version history
CREATE INDEX idx_version_history_project ON version_history(project_id);
CREATE INDEX idx_version_history_commit_hash ON version_history(commit_hash);
CREATE INDEX idx_version_history_commit_date ON version_history(commit_date DESC);
CREATE INDEX idx_version_history_author ON version_history(author_email);
CREATE INDEX idx_version_history_udo_exec ON version_history(udo_execution_id);

-- Full-text search on commit messages
CREATE INDEX idx_version_history_message_search ON version_history
    USING gin(to_tsvector('english', message));

-- ============================================================
-- 5. KANBAN BOARDS TABLE
-- ============================================================
-- Work management boards per project

CREATE TABLE IF NOT EXISTS kanban_boards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Board info
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Column configuration
    columns JSONB NOT NULL DEFAULT '[
        {"id": "todo", "name": "To Do", "order": 0},
        {"id": "in_progress", "name": "In Progress", "order": 1},
        {"id": "review", "name": "Review", "order": 2},
        {"id": "testing", "name": "Testing", "order": 3},
        {"id": "done", "name": "Done", "order": 4}
    ]'::jsonb,

    -- Automation rules
    automation_rules JSONB DEFAULT '[]'::jsonb,
    -- Example: {
    --   "on_commit": "move_to_review",
    --   "on_test_pass": "move_to_done"
    -- }

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,

    UNIQUE(project_id, name)
);

-- Indexes for kanban boards
CREATE INDEX idx_kanban_boards_project ON kanban_boards(project_id);
CREATE INDEX idx_kanban_boards_default ON kanban_boards(is_default) WHERE is_default = TRUE;

-- ============================================================
-- 6. KANBAN CARDS TABLE
-- ============================================================
-- Individual tasks/cards on kanban boards

CREATE TABLE IF NOT EXISTS kanban_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    board_id UUID NOT NULL REFERENCES kanban_boards(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Card content
    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- Card position
    column_id VARCHAR(50) NOT NULL,  -- Maps to columns in board
    position INTEGER NOT NULL,  -- Order within column

    -- Card type
    card_type VARCHAR(50) DEFAULT 'task',  -- task, bug, feature, epic

    -- Status and priority
    status VARCHAR(50) DEFAULT 'todo',
    priority VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, urgent

    -- Effort estimation
    estimated_hours DECIMAL(5, 2),
    actual_hours DECIMAL(5, 2),

    -- Task context for CLI integration
    task_context JSONB,
    -- Example: {
    --   "files": [...],
    --   "git_branch": "feature/auth",
    --   "previous_prompts": [...],
    --   "udo_state": {...}
    -- }

    -- Linked entities
    task_history_id UUID REFERENCES task_history(id),
    version_commit_hash VARCHAR(40),

    -- Assignees and watchers
    assignees TEXT[],
    watchers TEXT[],

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Metadata
    tags TEXT[],
    labels TEXT[],

    -- Checklist
    checklist JSONB DEFAULT '[]'::jsonb,
    -- Example: [
    --   {"id": 1, "text": "Write tests", "done": false},
    --   {"id": 2, "text": "Update docs", "done": true}
    -- ]

    -- Comments count (denormalized for performance)
    comments_count INTEGER DEFAULT 0
);

-- Indexes for kanban cards
CREATE INDEX idx_kanban_cards_board ON kanban_cards(board_id);
CREATE INDEX idx_kanban_cards_project ON kanban_cards(project_id);
CREATE INDEX idx_kanban_cards_column ON kanban_cards(column_id, position);
CREATE INDEX idx_kanban_cards_status ON kanban_cards(status);
CREATE INDEX idx_kanban_cards_priority ON kanban_cards(priority);
CREATE INDEX idx_kanban_cards_type ON kanban_cards(card_type);
CREATE INDEX idx_kanban_cards_task_history ON kanban_cards(task_history_id);
CREATE INDEX idx_kanban_cards_due_date ON kanban_cards(due_date) WHERE due_date IS NOT NULL;

-- Full-text search on card content
CREATE INDEX idx_kanban_cards_search ON kanban_cards
    USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- ============================================================
-- 7. QUALITY METRICS TABLE
-- ============================================================
-- Historical quality metrics tracking

CREATE TABLE IF NOT EXISTS quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Metric categories
    code_quality JSONB,
    -- Example: {
    --   "eslint_score": 9.2,
    --   "pylint_score": 8.5,
    --   "complexity": 12,
    --   "duplications": 2.1
    -- }

    test_metrics JSONB,
    -- Example: {
    --   "coverage": 85.5,
    --   "passed": 150,
    --   "failed": 2,
    --   "skipped": 5
    -- }

    performance_metrics JSONB,
    -- Example: {
    --   "build_time_ms": 5000,
    --   "test_time_ms": 12000,
    --   "bundle_size_kb": 250
    -- }

    security_metrics JSONB,
    -- Example: {
    --   "vulnerabilities": 0,
    --   "security_score": 9.5,
    --   "dependencies_outdated": 3
    -- }

    documentation_metrics JSONB,
    -- Example: {
    --   "coverage": 75.0,
    --   "outdated_docs": 5
    -- }

    git_metrics JSONB,
    -- Example: {
    --   "commits_today": 5,
    --   "commits_week": 23,
    --   "active_branches": 3
    -- }

    -- Overall score (calculated)
    overall_score DECIMAL(3, 1),  -- 0.0 to 10.0

    -- Snapshot info
    commit_hash VARCHAR(40),
    measured_at TIMESTAMPTZ DEFAULT NOW(),

    -- Metadata
    measurement_duration_ms INTEGER,
    tool_versions JSONB
);

-- Indexes for quality metrics
CREATE INDEX idx_quality_metrics_project ON quality_metrics(project_id);
CREATE INDEX idx_quality_metrics_measured ON quality_metrics(measured_at DESC);
CREATE INDEX idx_quality_metrics_commit ON quality_metrics(commit_hash);
CREATE INDEX idx_quality_metrics_overall_score ON quality_metrics(overall_score DESC);

-- Composite index for trends
CREATE INDEX idx_quality_metrics_trends ON quality_metrics(project_id, measured_at DESC);

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kanban_boards_updated_at BEFORE UPDATE ON kanban_boards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kanban_cards_updated_at BEFORE UPDATE ON kanban_cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update last_active_at when project context is accessed
CREATE OR REPLACE FUNCTION update_project_last_active()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE projects
    SET last_active_at = NOW()
    WHERE id = NEW.project_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_last_active_on_context_load AFTER UPDATE ON project_contexts
    FOR EACH ROW WHEN (NEW.loaded_at IS NOT NULL AND NEW.loaded_at <> OLD.loaded_at)
    EXECUTE FUNCTION update_project_last_active();

CREATE TRIGGER update_last_active_on_task_execution AFTER INSERT ON task_history
    FOR EACH ROW EXECUTE FUNCTION update_project_last_active();

-- ============================================================
-- VIEWS
-- ============================================================

-- Active projects view
CREATE OR REPLACE VIEW active_projects AS
SELECT
    p.*,
    COUNT(DISTINCT th.id) as total_tasks,
    COUNT(DISTINCT kc.id) as total_cards,
    MAX(th.executed_at) as last_task_at,
    AVG(qm.overall_score) as avg_quality_score
FROM projects p
LEFT JOIN task_history th ON p.id = th.project_id
LEFT JOIN kanban_cards kc ON p.id = kc.project_id
LEFT JOIN quality_metrics qm ON p.id = qm.project_id
WHERE p.is_archived = FALSE
GROUP BY p.id;

-- Project summary view
CREATE OR REPLACE VIEW project_summary AS
SELECT
    p.id,
    p.name,
    p.current_phase,
    p.last_active_at,
    COUNT(DISTINCT th.id) as total_executions,
    COUNT(DISTINCT vh.id) as total_commits,
    COUNT(DISTINCT kc.id) as total_cards,
    (
        SELECT overall_score
        FROM quality_metrics qm
        WHERE qm.project_id = p.id
        ORDER BY measured_at DESC
        LIMIT 1
    ) as latest_quality_score
FROM projects p
LEFT JOIN task_history th ON p.id = th.project_id
LEFT JOIN version_history vh ON p.id = vh.project_id
LEFT JOIN kanban_cards kc ON p.id = kc.project_id
GROUP BY p.id, p.name, p.current_phase, p.last_active_at;

-- ============================================================
-- INITIAL DATA
-- ============================================================

-- Insert default project (current UDO project)
INSERT INTO projects (name, description, path, current_phase, settings)
VALUES (
    'UDO-Development-Platform',
    'Unified Development Orchestrator - AI-powered development automation platform',
    'C:\Users\user\Documents\GitHub\UDO-Development-Platform',
    'testing',
    '{"auto_commit": false, "ai_model": "claude-sonnet-4.5"}'::jsonb
) ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================

COMMENT ON TABLE projects IS 'Core project information and configuration';
COMMENT ON TABLE project_contexts IS 'Auto-loading project context for seamless switching';
COMMENT ON TABLE task_history IS 'Prompt/Code history management and ML training data';
COMMENT ON TABLE version_history IS 'Cached Git commit information with quality metrics';
COMMENT ON TABLE kanban_boards IS 'Work management boards per project';
COMMENT ON TABLE kanban_cards IS 'Individual tasks/cards on kanban boards';
COMMENT ON TABLE quality_metrics IS 'Historical quality metrics tracking';

-- ============================================================
-- END OF SCHEMA
-- ============================================================
