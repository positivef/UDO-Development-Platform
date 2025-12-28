-- UDO v3.0 Database Schema
-- Implements schema design from PRD_UNIFIED_ENHANCED Section 3
-- With uncertainty tracking and pgvector for RAG support

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create custom types
CREATE TYPE phase_type AS ENUM (
    'ideation',
    'planning',
    'development',
    'testing',
    'deployment',
    'maintenance'
);

CREATE TYPE uncertainty_state AS ENUM (
    'deterministic',
    'probabilistic',
    'quantum',
    'chaotic',
    'void'
);

-- Users table (simplified for now)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table with phase tracking
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_phase phase_type DEFAULT 'ideation',
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for owner lookup
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_phase ON projects(current_phase);

-- Project contexts for RAG (Retrieval Augmented Generation)
CREATE TABLE IF NOT EXISTS project_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_path VARCHAR(500),
    content_chunk TEXT,
    embedding vector(1536), -- OpenAI Ada-002 embeddings
    metadata JSONB DEFAULT '{}',
    chunk_index INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, file_path, chunk_index)
);

-- Create vector similarity search index (IVFFlat for performance)
CREATE INDEX idx_project_contexts_embedding
ON project_contexts
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create composite index for efficient lookups
CREATE INDEX idx_project_contexts_project_file
ON project_contexts(project_id, file_path);

-- Uncertainty logs for tracking AI decisions
CREATE TABLE IF NOT EXISTS uncertainty_logs (
    id BIGSERIAL PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    component VARCHAR(100) NOT NULL,
    state uncertainty_state NOT NULL,
    score DECIMAL(3,2) CHECK (score >= 0 AND score <= 1),
    decision_metadata JSONB NOT NULL,
    least_confident_area TEXT,
    over_simplifications TEXT[],
    pivot_questions TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Time-series optimization for uncertainty logs
CREATE INDEX idx_uncertainty_logs_time
ON uncertainty_logs(created_at DESC);

CREATE INDEX idx_uncertainty_logs_project_component
ON uncertainty_logs(project_id, component);

-- RLHF (Reinforcement Learning from Human Feedback) table
CREATE TABLE IF NOT EXISTS uncertainty_feedback (
    id BIGSERIAL PRIMARY KEY,
    log_id BIGINT NOT NULL REFERENCES uncertainty_logs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    rating INTEGER CHECK (rating IN (-1, 0, 1)),
    correction TEXT,
    feedback_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for RLHF queries
CREATE INDEX idx_feedback_log ON uncertainty_feedback(log_id);
CREATE INDEX idx_feedback_time ON uncertainty_feedback(created_at DESC);

-- AI model responses cache
CREATE TABLE IF NOT EXISTS ai_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    query_hash VARCHAR(64) NOT NULL, -- SHA256 of query
    model VARCHAR(50) NOT NULL, -- claude, gpt4, gemini, etc.
    response TEXT NOT NULL,
    uncertainty_map JSONB,
    tokens_used INTEGER,
    latency_ms INTEGER,
    cost_cents DECIMAL(10,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Index for cache lookups
CREATE INDEX idx_ai_responses_cache
ON ai_responses(project_id, query_hash, model);

CREATE INDEX idx_ai_responses_expires
ON ai_responses(expires_at);

-- Migration tracking table
CREATE TABLE IF NOT EXISTS migration_status (
    id SERIAL PRIMARY KEY,
    component VARCHAR(100) NOT NULL,
    source_system VARCHAR(50) NOT NULL, -- redis, mock, postgres
    target_system VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    records_migrated INTEGER DEFAULT 0,
    records_total INTEGER,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_details JSONB
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    latency_ms INTEGER NOT NULL,
    status_code INTEGER NOT NULL,
    error_type VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optimize for time-series queries
CREATE INDEX idx_performance_metrics_time
ON performance_metrics(created_at DESC);

-- Create hypertable if TimescaleDB is available (optional)
-- SELECT create_hypertable('performance_metrics', 'created_at',
--   chunk_time_interval => interval '1 day',
--   if_not_exists => TRUE);

-- Session management for context persistence
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    session_data JSONB DEFAULT '{}',
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '7 days',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for session cleanup
CREATE INDEX idx_sessions_expiry ON user_sessions(expires_at);

-- Create materialized view for project statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS project_stats AS
SELECT
    p.id as project_id,
    p.name as project_name,
    p.current_phase,
    COUNT(DISTINCT pc.id) as context_count,
    COUNT(DISTINCT ul.id) as decision_count,
    AVG(ul.score) as avg_uncertainty,
    COUNT(DISTINCT uf.id) as feedback_count,
    MAX(ul.created_at) as last_activity
FROM projects p
LEFT JOIN project_contexts pc ON p.id = pc.project_id
LEFT JOIN uncertainty_logs ul ON p.id = ul.project_id
LEFT JOIN uncertainty_feedback uf ON ul.id = uf.log_id
GROUP BY p.id, p.name, p.current_phase;

-- Create index on materialized view
CREATE UNIQUE INDEX idx_project_stats_id ON project_stats(project_id);

-- Function to refresh project stats
CREATE OR REPLACE FUNCTION refresh_project_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY project_stats;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate system uncertainty
CREATE OR REPLACE FUNCTION calculate_system_uncertainty()
RETURNS TABLE(
    component VARCHAR,
    current_state uncertainty_state,
    average_score DECIMAL,
    sample_size BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ul.component,
        mode() WITHIN GROUP (ORDER BY ul.state) as current_state,
        AVG(ul.score)::DECIMAL as average_score,
        COUNT(*) as sample_size
    FROM uncertainty_logs ul
    WHERE ul.created_at > NOW() - INTERVAL '24 hours'
    GROUP BY ul.component
    ORDER BY average_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables
CREATE TRIGGER update_projects_updated_at
BEFORE UPDATE ON projects
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_project_contexts_updated_at
BEFORE UPDATE ON project_contexts
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Sample data for testing
INSERT INTO users (id, email, name) VALUES
    ('11111111-1111-1111-1111-111111111111', 'test@udo.dev', 'Test User')
ON CONFLICT (email) DO NOTHING;

INSERT INTO projects (id, name, description, owner_id, current_phase) VALUES
    ('22222222-2222-2222-2222-222222222222',
     'UDO Platform Development',
     'Unified Development Orchestrator with AI collaboration',
     '11111111-1111-1111-1111-111111111111',
     'development')
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust for production)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO udo_dev;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO udo_dev;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO udo_dev;

-- Performance optimization settings
-- NOTE: pg_stat_statements settings require restart and shared_preload_libraries
-- Comment out for now, can be configured in postgresql.conf if needed
-- ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
-- ALTER SYSTEM SET pg_stat_statements.track = 'all';
-- ALTER SYSTEM SET pg_stat_statements.max = 10000;

-- Maintenance settings
ALTER SYSTEM SET autovacuum = 'on';
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;

-- Connection pooling optimization
ALTER SYSTEM SET max_connections = 200;

-- Apply settings (requires restart in production)
SELECT pg_reload_conf();

-- Final message
DO $$
BEGIN
    RAISE NOTICE 'UDO v3.0 database schema initialized successfully!';
    RAISE NOTICE 'pgvector extension enabled for RAG support';
    RAISE NOTICE 'Uncertainty tracking tables created';
    RAISE NOTICE 'Sample project created with ID: 22222222-2222-2222-2222-222222222222';
END $$;
