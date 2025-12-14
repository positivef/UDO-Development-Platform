-- Migration: Add Phase Transition Tracking
-- Purpose: Enable automatic phase-aware time tracking integration
-- Date: 2025-11-21
-- Phase: Week 3, Day 1 - Database Schema Updates

-- ============================================================
-- 1. Create phase_transitions table
-- ============================================================

CREATE TABLE IF NOT EXISTS phase_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_phase VARCHAR(50),  -- NULL for initial phase
    to_phase VARCHAR(50) NOT NULL,
    transition_time TIMESTAMP NOT NULL DEFAULT NOW(),
    duration_seconds INTEGER,  -- Duration of previous phase
    automated BOOLEAN DEFAULT true,  -- Whether transition was automatic
    metadata JSONB,  -- Additional transition metadata
    project_id UUID,  -- Optional project association
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE phase_transitions IS 'Tracks development phase transitions for ROI analysis';
COMMENT ON COLUMN phase_transitions.from_phase IS 'Previous phase (NULL if first phase)';
COMMENT ON COLUMN phase_transitions.to_phase IS 'New phase being entered';
COMMENT ON COLUMN phase_transitions.duration_seconds IS 'Time spent in previous phase';
COMMENT ON COLUMN phase_transitions.automated IS 'Whether transition was triggered automatically by UDO';

-- ============================================================
-- 2. Extend task_sessions table
-- ============================================================

-- Add phase_transition_id to link sessions to transitions
ALTER TABLE task_sessions
    ADD COLUMN IF NOT EXISTS phase_transition_id UUID REFERENCES phase_transitions(id);

-- Add previous_phase to track phase changes within sessions
ALTER TABLE task_sessions
    ADD COLUMN IF NOT EXISTS previous_phase VARCHAR(50);

COMMENT ON COLUMN task_sessions.phase_transition_id IS 'Links session to the phase transition that started it';
COMMENT ON COLUMN task_sessions.previous_phase IS 'Previous phase if session spans a transition';

-- ============================================================
-- 3. Create performance indexes
-- ============================================================

-- Index for time-based queries (most common)
CREATE INDEX IF NOT EXISTS idx_phase_transitions_time
    ON phase_transitions(transition_time DESC);

-- Index for project-specific analysis
CREATE INDEX IF NOT EXISTS idx_phase_transitions_project
    ON phase_transitions(project_id)
    WHERE project_id IS NOT NULL;

-- Index for phase-based filtering
CREATE INDEX IF NOT EXISTS idx_phase_transitions_to_phase
    ON phase_transitions(to_phase);

-- Composite index for phase transition analysis
CREATE INDEX IF NOT EXISTS idx_phase_transitions_phases
    ON phase_transitions(from_phase, to_phase);

-- Index for task_sessions phase queries
CREATE INDEX IF NOT EXISTS idx_task_sessions_phase
    ON task_sessions(phase);

-- Index for linking sessions to transitions
CREATE INDEX IF NOT EXISTS idx_task_sessions_transition
    ON task_sessions(phase_transition_id)
    WHERE phase_transition_id IS NOT NULL;

-- ============================================================
-- 4. Verification queries
-- ============================================================

-- Verify table exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'phase_transitions'
    ) THEN
        RAISE NOTICE '✅ phase_transitions table created successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to create phase_transitions table';
    END IF;
END $$;

-- Verify columns added
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'task_sessions'
        AND column_name = 'phase_transition_id'
    ) AND EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'task_sessions'
        AND column_name = 'previous_phase'
    ) THEN
        RAISE NOTICE '✅ task_sessions columns added successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to add columns to task_sessions';
    END IF;
END $$;

-- ============================================================
-- Migration complete
-- ============================================================

-- Log migration success
INSERT INTO schema_version (version, description, applied_at)
VALUES (
    '003',
    'Add phase transition tracking for time tracking integration',
    NOW()
)
ON CONFLICT (version) DO NOTHING;

RAISE NOTICE '✅ Migration 003_phase_transitions.sql completed successfully';
