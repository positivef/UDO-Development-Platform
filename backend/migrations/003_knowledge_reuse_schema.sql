-- ============================================================================
-- Migration 003: Knowledge Reuse System Schema
-- ============================================================================
-- Week 7-8: PostgreSQL Migration for Knowledge Reuse Accuracy Tracking
--
-- Tables:
-- 1. knowledge_feedback: User feedback on search results
-- 2. knowledge_document_scores: Aggregate quality scores per document
-- 3. knowledge_search_stats: Search performance metrics
--
-- Benchmarking:
-- - Notion AI: Explicit feedback tracking
-- - Linear: Confidence-based accuracy (60%+ target)
-- - GitHub Copilot: Acceptance rate (26-40% target)
-- ============================================================================

-- Table 1: knowledge_feedback
-- Tracks explicit and implicit feedback to calculate accuracy metrics
CREATE TABLE IF NOT EXISTS knowledge_feedback (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Document reference
    document_id VARCHAR(500) NOT NULL,

    -- Search context
    search_query TEXT NOT NULL,
    session_id VARCHAR(100),

    -- Feedback signals
    is_helpful BOOLEAN NOT NULL,
    implicit_accept BOOLEAN,
    reason TEXT,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(100)
);

-- Indexes for knowledge_feedback
CREATE INDEX IF NOT EXISTS ix_feedback_document_id
    ON knowledge_feedback(document_id);

CREATE INDEX IF NOT EXISTS ix_feedback_session_id
    ON knowledge_feedback(session_id);

CREATE INDEX IF NOT EXISTS ix_feedback_created_at
    ON knowledge_feedback(created_at);

CREATE INDEX IF NOT EXISTS ix_feedback_user_id
    ON knowledge_feedback(user_id);

CREATE INDEX IF NOT EXISTS ix_feedback_document_created
    ON knowledge_feedback(document_id, created_at);

CREATE INDEX IF NOT EXISTS ix_feedback_helpful_created
    ON knowledge_feedback(is_helpful, created_at);

CREATE INDEX IF NOT EXISTS ix_feedback_session_created
    ON knowledge_feedback(session_id, created_at);

-- Table 2: knowledge_document_scores
-- Maintains running statistics per document for quick metrics retrieval
CREATE TABLE IF NOT EXISTS knowledge_document_scores (
    -- Primary key
    document_id VARCHAR(500) PRIMARY KEY,

    -- Aggregate metrics
    usefulness_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    total_searches INTEGER NOT NULL DEFAULT 0,
    helpful_count INTEGER NOT NULL DEFAULT 0,
    unhelpful_count INTEGER NOT NULL DEFAULT 0,
    acceptance_rate DOUBLE PRECISION NOT NULL DEFAULT 0.0,

    -- Metadata
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    first_search TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT chk_usefulness_score
        CHECK (usefulness_score BETWEEN -5.0 AND 5.0),
    CONSTRAINT chk_total_searches
        CHECK (total_searches >= 0),
    CONSTRAINT chk_helpful_count
        CHECK (helpful_count >= 0),
    CONSTRAINT chk_unhelpful_count
        CHECK (unhelpful_count >= 0),
    CONSTRAINT chk_acceptance_rate
        CHECK (acceptance_rate BETWEEN 0.0 AND 100.0)
);

-- Indexes for knowledge_document_scores
CREATE INDEX IF NOT EXISTS ix_doc_score_usefulness
    ON knowledge_document_scores(usefulness_score);

CREATE INDEX IF NOT EXISTS ix_doc_score_acceptance
    ON knowledge_document_scores(acceptance_rate);

CREATE INDEX IF NOT EXISTS ix_doc_score_updated
    ON knowledge_document_scores(last_updated);

CREATE INDEX IF NOT EXISTS ix_doc_score_searches
    ON knowledge_document_scores(total_searches);

-- Table 3: knowledge_search_stats
-- Tracks search speed and tier hit rates for performance monitoring
CREATE TABLE IF NOT EXISTS knowledge_search_stats (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Search metadata
    search_query TEXT NOT NULL,
    session_id VARCHAR(100),

    -- Performance metrics
    search_time_ms DOUBLE PRECISION NOT NULL,
    tier1_hits INTEGER NOT NULL DEFAULT 0,
    tier2_hits INTEGER NOT NULL DEFAULT 0,
    tier3_hits INTEGER NOT NULL DEFAULT 0,
    total_results INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_search_time
        CHECK (search_time_ms >= 0),
    CONSTRAINT chk_tier1_hits
        CHECK (tier1_hits >= 0),
    CONSTRAINT chk_tier2_hits
        CHECK (tier2_hits >= 0),
    CONSTRAINT chk_tier3_hits
        CHECK (tier3_hits >= 0),
    CONSTRAINT chk_total_results
        CHECK (total_results >= 0)
);

-- Indexes for knowledge_search_stats
CREATE INDEX IF NOT EXISTS ix_search_stats_created
    ON knowledge_search_stats(created_at);

CREATE INDEX IF NOT EXISTS ix_search_stats_time
    ON knowledge_search_stats(search_time_ms);

CREATE INDEX IF NOT EXISTS ix_search_stats_session_id
    ON knowledge_search_stats(session_id);

CREATE INDEX IF NOT EXISTS ix_search_stats_session_created
    ON knowledge_search_stats(session_id, created_at);

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE knowledge_feedback IS
    'User feedback on knowledge search results (Week 6-7)';

COMMENT ON COLUMN knowledge_feedback.document_id IS
    'Obsidian document ID or filename';

COMMENT ON COLUMN knowledge_feedback.is_helpful IS
    'Explicit feedback: helpful or not (boolean)';

COMMENT ON COLUMN knowledge_feedback.implicit_accept IS
    'Implicit signal (copy/dismiss) - GitHub Copilot style';

COMMENT ON TABLE knowledge_document_scores IS
    'Aggregate quality scores for documents';

COMMENT ON COLUMN knowledge_document_scores.usefulness_score IS
    'Weighted score: -5.0 to +5.0 (explicit +1, implicit +0.5, negative -1/-0.3)';

COMMENT ON COLUMN knowledge_document_scores.acceptance_rate IS
    'Percentage: 0-100 (helpful / total searches * 100)';

COMMENT ON TABLE knowledge_search_stats IS
    'Search performance and tier breakdown statistics';

COMMENT ON COLUMN knowledge_search_stats.tier1_hits IS
    'Filename pattern matches (<1ms, 95% accuracy target)';

COMMENT ON COLUMN knowledge_search_stats.tier2_hits IS
    'Frontmatter YAML matches (<50ms, 80% accuracy target)';

COMMENT ON COLUMN knowledge_search_stats.tier3_hits IS
    'Full-text content matches (<500ms, 60% accuracy target)';

-- ============================================================================
-- Migration complete
-- ============================================================================
