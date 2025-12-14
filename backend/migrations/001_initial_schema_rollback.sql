-- ============================================================
-- UDO Development Platform - Initial Schema Rollback
-- Version: 1.0.0
-- Date: 2025-11-17
-- Description: Rollback script for initial schema migration
-- WARNING: This will delete all data!
-- ============================================================

-- Drop views first
DROP VIEW IF EXISTS project_summary CASCADE;
DROP VIEW IF EXISTS active_projects CASCADE;

-- Drop triggers
DROP TRIGGER IF EXISTS update_last_active_on_task_execution ON task_history;
DROP TRIGGER IF EXISTS update_last_active_on_context_load ON project_contexts;
DROP TRIGGER IF EXISTS update_kanban_cards_updated_at ON kanban_cards;
DROP TRIGGER IF EXISTS update_kanban_boards_updated_at ON kanban_boards;
DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;

-- Drop functions
DROP FUNCTION IF EXISTS update_project_last_active();
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS quality_metrics CASCADE;
DROP TABLE IF EXISTS kanban_cards CASCADE;
DROP TABLE IF EXISTS kanban_boards CASCADE;
DROP TABLE IF EXISTS version_history CASCADE;
DROP TABLE IF EXISTS task_history CASCADE;
DROP TABLE IF EXISTS project_contexts CASCADE;
DROP TABLE IF EXISTS projects CASCADE;

-- Note: Extensions are not dropped as they might be used by other databases
-- DROP EXTENSION IF EXISTS "pg_trgm";
-- DROP EXTENSION IF EXISTS "uuid-ossp";
