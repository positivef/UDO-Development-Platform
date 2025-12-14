-- Time Tracking Schema Rollback
-- Removes all time tracking tables, views, and related objects

-- Drop views first (they depend on tables)
DROP VIEW IF EXISTS phase_performance CASCADE;
DROP VIEW IF EXISTS ai_model_performance CASCADE;
DROP VIEW IF EXISTS task_type_performance CASCADE;
DROP VIEW IF EXISTS daily_summary CASCADE;
DROP VIEW IF EXISTS active_sessions CASCADE;

-- Drop tables (this will also drop their indexes and triggers)
DROP TABLE IF EXISTS time_metrics CASCADE;
DROP TABLE IF EXISTS task_sessions CASCADE;

-- Drop trigger function
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Note: If you only want to disable time tracking temporarily,
-- consider keeping the tables and just removing the API endpoints instead.
