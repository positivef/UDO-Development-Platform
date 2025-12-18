-- ============================================================================
-- Migration 003 Rollback: Knowledge Reuse System Schema
-- ============================================================================
-- Week 7-8: PostgreSQL Migration Rollback
--
-- This script safely removes all Knowledge Reuse tables and indexes
-- ============================================================================

-- Drop indexes first (cascading)
DROP INDEX IF EXISTS ix_feedback_session_created;
DROP INDEX IF EXISTS ix_feedback_helpful_created;
DROP INDEX IF EXISTS ix_feedback_document_created;
DROP INDEX IF EXISTS ix_feedback_user_id;
DROP INDEX IF EXISTS ix_feedback_created_at;
DROP INDEX IF EXISTS ix_feedback_session_id;
DROP INDEX IF EXISTS ix_feedback_document_id;

DROP INDEX IF EXISTS ix_doc_score_searches;
DROP INDEX IF EXISTS ix_doc_score_updated;
DROP INDEX IF EXISTS ix_doc_score_acceptance;
DROP INDEX IF EXISTS ix_doc_score_usefulness;

DROP INDEX IF EXISTS ix_search_stats_session_created;
DROP INDEX IF EXISTS ix_search_stats_session_id;
DROP INDEX IF EXISTS ix_search_stats_time;
DROP INDEX IF EXISTS ix_search_stats_created;

-- Drop tables (in reverse dependency order)
DROP TABLE IF EXISTS knowledge_search_stats CASCADE;
DROP TABLE IF EXISTS knowledge_document_scores CASCADE;
DROP TABLE IF EXISTS knowledge_feedback CASCADE;

-- ============================================================================
-- Rollback complete
-- ============================================================================
