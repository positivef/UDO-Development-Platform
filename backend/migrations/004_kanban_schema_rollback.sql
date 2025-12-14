-- Rollback Migration 004: Kanban-UDO Integration Database Schema
-- Date: 2025-12-04
-- Purpose: Safely rollback Kanban schema migration
-- Rollback Strategy: Tier 1 (immediate) - DROP SCHEMA kanban CASCADE

-- ==================================================================
-- SAFETY CHECKS BEFORE ROLLBACK
-- ==================================================================

DO $$
DECLARE
    task_count INTEGER;
    archive_count INTEGER;
BEGIN
    -- Check if schema exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'kanban') THEN
        RAISE NOTICE 'Kanban schema does not exist. Nothing to rollback.';
        RETURN;
    END IF;

    -- Count existing tasks
    SELECT COUNT(*) INTO task_count FROM kanban.tasks;

    -- Count archived tasks
    SELECT COUNT(*) INTO archive_count FROM kanban.task_archive;

    -- Warn if data exists
    IF task_count > 0 OR archive_count > 0 THEN
        RAISE WARNING 'Rollback will delete % active tasks and % archived tasks', task_count, archive_count;
        RAISE NOTICE 'Consider backing up data before proceeding';
    END IF;

    RAISE NOTICE 'Proceeding with Kanban schema rollback...';
END $$;

-- ==================================================================
-- BACKUP CRITICAL DATA (Optional - commented out by default)
-- ==================================================================

/*
-- Uncomment to backup task data before rollback
CREATE TABLE IF NOT EXISTS public.kanban_tasks_backup_20251204 AS
SELECT * FROM kanban.tasks;

CREATE TABLE IF NOT EXISTS public.kanban_archive_backup_20251204 AS
SELECT * FROM kanban.task_archive;

RAISE NOTICE 'Backup created: kanban_tasks_backup_20251204, kanban_archive_backup_20251204';
*/

-- ==================================================================
-- DROP TRIGGERS
-- ==================================================================

-- Drop all triggers
DROP TRIGGER IF EXISTS update_tasks_modtime ON kanban.tasks;
DROP TRIGGER IF EXISTS update_task_contexts_modtime ON kanban.task_contexts;
DROP TRIGGER IF EXISTS validate_dependency_dag ON kanban.dependencies;
DROP TRIGGER IF EXISTS enforce_related_projects_limit ON kanban.task_projects;
DROP TRIGGER IF EXISTS enforce_context_size ON kanban.task_contexts;

-- ==================================================================
-- DROP FUNCTIONS
-- ==================================================================

-- Drop trigger functions
DROP FUNCTION IF EXISTS kanban.update_modified_column();
DROP FUNCTION IF EXISTS kanban.validate_dag();
DROP FUNCTION IF EXISTS kanban.enforce_max_related_projects();
DROP FUNCTION IF EXISTS kanban.enforce_context_size_limit();

-- ==================================================================
-- DROP INDEXES (CASCADE will handle most, but explicit for clarity)
-- ==================================================================

-- Tasks indexes
DROP INDEX IF EXISTS kanban.idx_tasks_phase;
DROP INDEX IF EXISTS kanban.idx_tasks_status;
DROP INDEX IF EXISTS kanban.idx_tasks_priority;
DROP INDEX IF EXISTS kanban.idx_tasks_created_at;
DROP INDEX IF EXISTS kanban.idx_tasks_completeness;
DROP INDEX IF EXISTS kanban.idx_tasks_quality_gate;
DROP INDEX IF EXISTS kanban.idx_tasks_kanban_board;
DROP INDEX IF EXISTS kanban.idx_tasks_violations;

-- Dependencies indexes
DROP INDEX IF EXISTS kanban.idx_dependencies_source;
DROP INDEX IF EXISTS kanban.idx_dependencies_target;
DROP INDEX IF EXISTS kanban.idx_dependencies_type;
DROP INDEX IF EXISTS kanban.idx_dependencies_override;

-- Task contexts indexes
DROP INDEX IF EXISTS kanban.idx_task_contexts_task;

-- Task projects indexes
DROP INDEX IF EXISTS kanban.idx_task_projects_task;
DROP INDEX IF EXISTS kanban.idx_task_projects_project;
DROP INDEX IF EXISTS kanban.idx_task_projects_primary;
DROP INDEX IF EXISTS kanban.idx_task_projects_one_primary;

-- Task archive indexes
DROP INDEX IF EXISTS kanban.idx_task_archive_year;
DROP INDEX IF EXISTS kanban.idx_task_archive_phase;
DROP INDEX IF EXISTS kanban.idx_task_archive_archived_at;
DROP INDEX IF EXISTS kanban.idx_task_archive_obsidian;
DROP INDEX IF EXISTS kanban.idx_task_archive_summary_search;
DROP INDEX IF EXISTS kanban.idx_task_archive_lessons_search;

-- Quality gates indexes
DROP INDEX IF EXISTS kanban.idx_quality_gates_task;
DROP INDEX IF EXISTS kanban.idx_quality_gates_type;
DROP INDEX IF EXISTS kanban.idx_quality_gates_passed;

-- Dependency audit indexes
DROP INDEX IF EXISTS kanban.idx_dependency_audit_timestamp;
DROP INDEX IF EXISTS kanban.idx_dependency_audit_user;

-- ==================================================================
-- DROP TABLES (in reverse dependency order)
-- ==================================================================

-- Drop tables with foreign key dependencies first
DROP TABLE IF EXISTS kanban.dependency_audit CASCADE;
DROP TABLE IF EXISTS kanban.quality_gates CASCADE;
DROP TABLE IF EXISTS kanban.task_archive CASCADE;
DROP TABLE IF EXISTS kanban.task_projects CASCADE;
DROP TABLE IF EXISTS kanban.task_contexts CASCADE;
DROP TABLE IF EXISTS kanban.dependencies CASCADE;
DROP TABLE IF EXISTS kanban.tasks CASCADE;

-- ==================================================================
-- DROP SCHEMA
-- ==================================================================

-- Drop the entire schema (will cascade delete everything)
DROP SCHEMA IF EXISTS kanban CASCADE;

-- ==================================================================
-- VERIFY ROLLBACK
-- ==================================================================

DO $$
BEGIN
    -- Verify schema is gone
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'kanban') THEN
        RAISE NOTICE '✅ Kanban schema successfully rolled back';
        RAISE NOTICE '✅ All tables, indexes, triggers, and functions removed';
    ELSE
        RAISE WARNING '⚠️  Kanban schema still exists after rollback';
    END IF;
END $$;

-- ==================================================================
-- ROLLBACK COMPLETE
-- ==================================================================

-- Usage Instructions:
--
-- To execute this rollback:
--   psql -U postgres -d udo_platform -f 004_kanban_schema_rollback.sql
--
-- Or using Python migration runner:
--   python backend/migrations/run_migration.py --rollback 004
--
-- Rollback Strategy:
--   Tier 1: Immediate (DROP SCHEMA) - Complete in <1 minute
--   Tier 2: N/A (no intermediate steps needed)
--   Tier 3: Database restore from backup - If Tier 1 fails (5 minutes)
