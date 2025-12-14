-- Time Tracking Schema Migration
-- Creates tables for time tracking, task sessions, and ROI metrics

-- Task Sessions Table
-- Tracks individual task execution sessions with time metrics
CREATE TABLE IF NOT EXISTS task_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN (
        'error_resolution',
        'design_task',
        'implementation',
        'testing',
        'documentation',
        'code_review',
        'refactoring',
        'debugging',
        'phase_transition',
        'other'
    )),
    phase VARCHAR(50) NOT NULL CHECK (phase IN (
        'ideation',
        'design',
        'mvp',
        'implementation',
        'testing'
    )),
    ai_used VARCHAR(50) NOT NULL CHECK (ai_used IN (
        'claude',
        'codex',
        'gemini',
        'multi',
        'none'
    )),

    -- Time tracking
    start_time TIMESTAMP NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP,
    pause_duration_seconds INTEGER NOT NULL DEFAULT 0,

    -- Metrics
    duration_seconds INTEGER,
    baseline_seconds INTEGER NOT NULL,
    time_saved_seconds INTEGER,

    -- Results
    success BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    metadata JSONB,

    -- Relations
    project_id UUID,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    CONSTRAINT positive_pause_duration CHECK (pause_duration_seconds >= 0),
    CONSTRAINT positive_baseline CHECK (baseline_seconds > 0),
    CONSTRAINT end_after_start CHECK (end_time IS NULL OR end_time >= start_time)
);

-- Indexes for task_sessions
CREATE INDEX IF NOT EXISTS idx_task_sessions_task_id ON task_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_sessions_task_type ON task_sessions(task_type);
CREATE INDEX IF NOT EXISTS idx_task_sessions_phase ON task_sessions(phase);
CREATE INDEX IF NOT EXISTS idx_task_sessions_ai_used ON task_sessions(ai_used);
CREATE INDEX IF NOT EXISTS idx_task_sessions_start_time ON task_sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_task_sessions_project_id ON task_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_task_sessions_success ON task_sessions(success);

-- Composite index for period queries
CREATE INDEX IF NOT EXISTS idx_task_sessions_period ON task_sessions(start_time, end_time, success);


-- Time Metrics Table
-- Aggregated metrics for different time periods (daily, weekly, monthly, annual)
CREATE TABLE IF NOT EXISTS time_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly', 'annual')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Aggregated metrics
    total_tasks INTEGER NOT NULL DEFAULT 0,
    total_duration_seconds INTEGER NOT NULL DEFAULT 0,
    total_baseline_seconds INTEGER NOT NULL DEFAULT 0,
    total_saved_seconds INTEGER NOT NULL DEFAULT 0,

    -- Calculated percentages
    roi_percentage DECIMAL(10, 2) NOT NULL DEFAULT 0,
    efficiency_gain DECIMAL(10, 2) NOT NULL DEFAULT 0,

    -- Analysis
    bottlenecks JSONB,
    top_time_savers JSONB,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_period CHECK (period_end >= period_start),
    CONSTRAINT positive_metrics CHECK (
        total_tasks >= 0 AND
        total_duration_seconds >= 0 AND
        total_baseline_seconds >= 0 AND
        total_saved_seconds >= -total_baseline_seconds
    ),

    -- Unique constraint: one record per period
    CONSTRAINT unique_period UNIQUE (period_type, period_start, period_end)
);

-- Indexes for time_metrics
CREATE INDEX IF NOT EXISTS idx_time_metrics_period_type ON time_metrics(period_type);
CREATE INDEX IF NOT EXISTS idx_time_metrics_period_start ON time_metrics(period_start);
CREATE INDEX IF NOT EXISTS idx_time_metrics_period_end ON time_metrics(period_end);

-- Composite index for period range queries
CREATE INDEX IF NOT EXISTS idx_time_metrics_period_range ON time_metrics(period_type, period_start, period_end);


-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_task_sessions_updated_at
    BEFORE UPDATE ON task_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_time_metrics_updated_at
    BEFORE UPDATE ON time_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- Views for common queries

-- Active sessions view
CREATE OR REPLACE VIEW active_sessions AS
SELECT
    id,
    task_id,
    task_type,
    phase,
    ai_used,
    start_time,
    baseline_seconds,
    EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER AS elapsed_seconds,
    metadata
FROM task_sessions
WHERE end_time IS NULL
ORDER BY start_time DESC;

-- Daily summary view
CREATE OR REPLACE VIEW daily_summary AS
SELECT
    DATE(start_time) AS date,
    COUNT(*) AS total_tasks,
    COUNT(*) FILTER (WHERE success = TRUE) AS successful_tasks,
    SUM(duration_seconds) AS total_duration_seconds,
    SUM(baseline_seconds) AS total_baseline_seconds,
    SUM(time_saved_seconds) AS total_saved_seconds,
    ROUND((SUM(time_saved_seconds)::DECIMAL / NULLIF(SUM(duration_seconds), 0) * 100), 2) AS roi_percentage,
    ROUND((SUM(time_saved_seconds)::DECIMAL / NULLIF(SUM(baseline_seconds), 0) * 100), 2) AS efficiency_percentage
FROM task_sessions
WHERE end_time IS NOT NULL
GROUP BY DATE(start_time)
ORDER BY DATE(start_time) DESC;

-- Task type performance view
CREATE OR REPLACE VIEW task_type_performance AS
SELECT
    task_type,
    COUNT(*) AS total_tasks,
    COUNT(*) FILTER (WHERE success = TRUE) AS successful_tasks,
    ROUND((COUNT(*) FILTER (WHERE success = TRUE)::DECIMAL / COUNT(*)) * 100, 2) AS success_rate,
    ROUND(AVG(duration_seconds), 0) AS avg_duration_seconds,
    ROUND(AVG(baseline_seconds), 0) AS avg_baseline_seconds,
    ROUND(AVG(time_saved_seconds), 0) AS avg_saved_seconds,
    ROUND((AVG(time_saved_seconds) / NULLIF(AVG(baseline_seconds), 0) * 100), 2) AS avg_efficiency_percentage
FROM task_sessions
WHERE end_time IS NOT NULL
GROUP BY task_type
ORDER BY avg_saved_seconds DESC;

-- AI model performance view
CREATE OR REPLACE VIEW ai_model_performance AS
SELECT
    ai_used,
    COUNT(*) AS total_tasks,
    COUNT(*) FILTER (WHERE success = TRUE) AS successful_tasks,
    ROUND((COUNT(*) FILTER (WHERE success = TRUE)::DECIMAL / COUNT(*)) * 100, 2) AS success_rate,
    ROUND(AVG(duration_seconds), 0) AS avg_duration_seconds,
    ROUND(AVG(time_saved_seconds), 0) AS avg_saved_seconds,
    ROUND((SUM(time_saved_seconds) / 3600.0), 2) AS total_saved_hours,
    ROUND((AVG(time_saved_seconds) / NULLIF(AVG(baseline_seconds), 0) * 100), 2) AS avg_efficiency_percentage
FROM task_sessions
WHERE end_time IS NOT NULL
GROUP BY ai_used
ORDER BY total_saved_hours DESC;

-- Phase performance view
CREATE OR REPLACE VIEW phase_performance AS
SELECT
    phase,
    COUNT(*) AS total_tasks,
    COUNT(*) FILTER (WHERE success = TRUE) AS successful_tasks,
    ROUND((COUNT(*) FILTER (WHERE success = TRUE)::DECIMAL / COUNT(*)) * 100, 2) AS success_rate,
    ROUND(AVG(duration_seconds), 0) AS avg_duration_seconds,
    ROUND(AVG(baseline_seconds), 0) AS avg_baseline_seconds,
    ROUND(AVG(time_saved_seconds), 0) AS avg_saved_seconds,
    ROUND((SUM(time_saved_seconds) / 3600.0), 2) AS total_saved_hours
FROM task_sessions
WHERE end_time IS NOT NULL
GROUP BY phase
ORDER BY total_saved_hours DESC;


-- Comments for documentation
COMMENT ON TABLE task_sessions IS 'Tracks individual task execution sessions with time metrics and AI usage';
COMMENT ON TABLE time_metrics IS 'Aggregated time metrics for different periods (daily, weekly, monthly, annual)';

COMMENT ON COLUMN task_sessions.task_id IS 'Unique identifier for the task';
COMMENT ON COLUMN task_sessions.task_type IS 'Type of task (error_resolution, design_task, etc.)';
COMMENT ON COLUMN task_sessions.phase IS 'Development phase (ideation, design, mvp, implementation, testing)';
COMMENT ON COLUMN task_sessions.ai_used IS 'AI model used (claude, codex, gemini, multi, none)';
COMMENT ON COLUMN task_sessions.baseline_seconds IS 'Expected manual time in seconds (from baseline_times.yaml)';
COMMENT ON COLUMN task_sessions.duration_seconds IS 'Actual time spent in seconds (excluding pauses)';
COMMENT ON COLUMN task_sessions.time_saved_seconds IS 'Time saved vs baseline (can be negative if over baseline)';
COMMENT ON COLUMN task_sessions.pause_duration_seconds IS 'Total pause duration in seconds';

COMMENT ON VIEW active_sessions IS 'Currently active task sessions';
COMMENT ON VIEW daily_summary IS 'Daily aggregated metrics';
COMMENT ON VIEW task_type_performance IS 'Performance breakdown by task type';
COMMENT ON VIEW ai_model_performance IS 'Performance breakdown by AI model';
COMMENT ON VIEW phase_performance IS 'Performance breakdown by development phase';


-- Insert initial test data (optional, for development)
-- UNCOMMENT FOR TESTING:
/*
INSERT INTO task_sessions (
    task_id, task_type, phase, ai_used,
    start_time, end_time,
    duration_seconds, baseline_seconds, time_saved_seconds,
    success, metadata
) VALUES
    ('test_error_001', 'error_resolution', 'implementation', 'claude',
     NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour 58 minutes',
     120, 1800, 1680,
     TRUE, '{"error_type": "401", "resolution_method": "tier1_obsidian"}'),

    ('test_design_001', 'design_task', 'design', 'multi',
     NOW() - INTERVAL '5 hours', NOW() - INTERVAL '3 hours',
     7200, 7200, 0,
     TRUE, '{"component": "api_design", "complexity": "high"}'),

    ('test_impl_001', 'implementation', 'implementation', 'codex',
     NOW() - INTERVAL '8 hours', NOW() - INTERVAL '6 hours',
     7200, 14400, 7200,
     TRUE, '{"feature": "time_tracking", "lines_added": 500}');
*/
