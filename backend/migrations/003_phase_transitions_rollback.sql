-- Rollback Migration: Remove Phase Transition Tracking
-- Purpose: Revert phase-aware time tracking integration changes
-- Date: 2025-11-21
-- Phase: Week 3, Day 1 - Database Schema Updates

-- ============================================================
-- Safety check: Warn about data loss
-- ============================================================

DO $$
DECLARE
    transition_count INTEGER;
    session_count INTEGER;
BEGIN
    -- Count existing phase transitions
    SELECT COUNT(*) INTO transition_count FROM phase_transitions;

    -- Count sessions with phase transitions
    SELECT COUNT(*) INTO session_count
    FROM task_sessions
    WHERE phase_transition_id IS NOT NULL;

    RAISE WARNING '⚠️  ROLLBACK WARNING';
    RAISE WARNING 'This will delete % phase transitions', transition_count;
    RAISE WARNING 'This will affect % task sessions', session_count;
    RAISE WARNING 'Proceeding with rollback in 5 seconds...';

    -- Give admin a chance to cancel
    PERFORM pg_sleep(5);
END $$;

-- ============================================================
-- 1. Drop indexes (reverse order of creation)
-- ============================================================

DROP INDEX IF EXISTS idx_task_sessions_transition;
DROP INDEX IF EXISTS idx_task_sessions_phase;
DROP INDEX IF EXISTS idx_phase_transitions_phases;
DROP INDEX IF EXISTS idx_phase_transitions_to_phase;
DROP INDEX IF EXISTS idx_phase_transitions_project;
DROP INDEX IF EXISTS idx_phase_transitions_time;

RAISE NOTICE '✅ Indexes dropped';

-- ============================================================
-- 2. Remove columns from task_sessions
-- ============================================================

-- Save data before dropping (optional: for recovery)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'task_sessions'
        AND column_name = 'phase_transition_id'
    ) THEN
        -- Create backup table
        CREATE TABLE IF NOT EXISTS task_sessions_backup_003 AS
        SELECT id, phase_transition_id, previous_phase
        FROM task_sessions
        WHERE phase_transition_id IS NOT NULL OR previous_phase IS NOT NULL;

        RAISE NOTICE '✅ Backed up % affected sessions to task_sessions_backup_003',
            (SELECT COUNT(*) FROM task_sessions_backup_003);
    END IF;
END $$;

-- Drop columns
ALTER TABLE task_sessions
    DROP COLUMN IF EXISTS phase_transition_id CASCADE,
    DROP COLUMN IF EXISTS previous_phase CASCADE;

RAISE NOTICE '✅ task_sessions columns dropped';

-- ============================================================
-- 3. Archive phase_transitions data before dropping
-- ============================================================

-- Create archive table
CREATE TABLE IF NOT EXISTS phase_transitions_archive_003 AS
SELECT *
FROM phase_transitions;

RAISE NOTICE '✅ Archived % transitions to phase_transitions_archive_003',
    (SELECT COUNT(*) FROM phase_transitions_archive_003);

-- ============================================================
-- 4. Drop phase_transitions table
-- ============================================================

DROP TABLE IF EXISTS phase_transitions CASCADE;

RAISE NOTICE '✅ phase_transitions table dropped';

-- ============================================================
-- 5. Remove migration version record
-- ============================================================

DELETE FROM schema_version
WHERE version = '003';

RAISE NOTICE '✅ Migration version record removed';

-- ============================================================
-- Rollback complete
-- ============================================================

RAISE NOTICE '✅ Rollback 003_phase_transitions_rollback.sql completed successfully';
RAISE NOTICE '📦 Data archived in:';
RAISE NOTICE '   - phase_transitions_archive_003';
RAISE NOTICE '   - task_sessions_backup_003';
RAISE NOTICE '💡 To restore data, contact database administrator';
