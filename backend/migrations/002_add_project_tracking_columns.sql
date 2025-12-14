-- Migration: Add project tracking columns
-- Add last_active_at and is_archived for project management

-- Add last_active_at column (defaults to created_at)
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add is_archived column (defaults to false)
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;

-- Create index on last_active_at for efficient sorting
CREATE INDEX IF NOT EXISTS idx_projects_last_active ON projects(last_active_at DESC);

-- Create index on is_archived for filtering
CREATE INDEX IF NOT EXISTS idx_projects_archived ON projects(is_archived);

-- Update existing projects to have last_active_at = updated_at
UPDATE projects
SET last_active_at = updated_at
WHERE last_active_at IS NULL;

-- Migration tracking
INSERT INTO migration_status (
    component,
    source_system,
    target_system,
    status,
    started_at,
    completed_at
) VALUES (
    'project_tracking_columns',
    'v1',
    'v2',
    'completed',
    NOW(),
    NOW()
);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 002: Added last_active_at and is_archived columns';
END $$;
