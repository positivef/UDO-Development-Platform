-- Migration: Add project_states table for UDO state management
-- Keeps existing project_contexts for RAG purposes

-- Project states table for UDO system state persistence
CREATE TABLE IF NOT EXISTS project_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,

    -- UDO system state
    udo_state JSONB DEFAULT '{}',

    -- ML models state
    ml_models JSONB DEFAULT '{}',

    -- Recent executions (FIFO, max 10)
    recent_executions JSONB DEFAULT '[]',

    -- AI preferences
    ai_preferences JSONB DEFAULT '{}',

    -- Editor state
    editor_state JSONB DEFAULT '{}',

    -- Timestamps
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    loaded_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient lookups
CREATE INDEX idx_project_states_project ON project_states(project_id);
CREATE INDEX idx_project_states_saved_at ON project_states(saved_at DESC);

-- Trigger for updated_at
CREATE TRIGGER update_project_states_updated_at
BEFORE UPDATE ON project_states
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Grant permissions
GRANT ALL PRIVILEGES ON project_states TO udo_dev;

-- Insert default state for existing project
INSERT INTO project_states (project_id, udo_state)
SELECT id, '{}'::jsonb
FROM projects
WHERE id = '22222222-2222-2222-2222-222222222222'
ON CONFLICT (project_id) DO NOTHING;

-- Migration tracking
INSERT INTO migration_status (
    component,
    source_system,
    target_system,
    status,
    started_at,
    completed_at
) VALUES (
    'project_states',
    'mock',
    'postgres',
    'completed',
    NOW(),
    NOW()
);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 001: project_states table created successfully';
    RAISE NOTICE '✅ Separate tables: project_contexts (RAG) + project_states (UDO state)';
END $$;
