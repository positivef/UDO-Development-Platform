"use client"

/**
 * Kanban Page - Main Kanban Board view
 *
 * Features:
 * - Full Kanban board with drag & drop
 * - Task management (create, update, delete)
 * - Integration with UDO v2 Phase system
 * - Real-time updates via WebSocket
 */

import { useEffect } from 'react'
import { KanbanBoard } from '@/components/kanban/KanbanBoard'
import { useKanbanStore } from '@/lib/stores/kanban-store'
import { Button } from '@/components/ui/button'
import { Plus, Filter, Download, Upload } from 'lucide-react'

// Sample mock data for testing
const mockTasks = [
  {
    id: '1',
    title: 'Implement authentication system',
    description: 'Add JWT-based authentication with role-based access control',
    status: 'in_progress' as const,
    phase: 'implementation' as const,
    priority: 'high' as const,
    tags: ['auth', 'security', 'backend'],
    created_at: '2025-12-07T10:00:00Z',
    updated_at: '2025-12-07T14:30:00Z',
    estimated_hours: 8,
    actual_hours: 5,
  },
  {
    id: '2',
    title: 'Design API endpoints',
    description: 'Create RESTful API design for Kanban integration',
    status: 'completed' as const,
    phase: 'design' as const,
    priority: 'medium' as const,
    tags: ['api', 'design', 'documentation'],
    created_at: '2025-12-06T09:00:00Z',
    updated_at: '2025-12-06T17:00:00Z',
    estimated_hours: 4,
    actual_hours: 3,
  },
  {
    id: '3',
    title: 'Set up CI/CD pipeline',
    description: 'Configure automated testing and deployment with GitHub Actions',
    status: 'pending' as const,
    phase: 'testing' as const,
    priority: 'medium' as const,
    tags: ['devops', 'ci/cd', 'testing'],
    created_at: '2025-12-07T08:00:00Z',
    updated_at: '2025-12-07T08:00:00Z',
    estimated_hours: 6,
  },
  {
    id: '4',
    title: 'Fix database connection pooling',
    description: 'Resolve connection timeout issues in production',
    status: 'blocked' as const,
    phase: 'implementation' as const,
    priority: 'critical' as const,
    tags: ['database', 'bug', 'production'],
    created_at: '2025-12-07T11:00:00Z',
    updated_at: '2025-12-07T15:00:00Z',
    estimated_hours: 4,
    blocked_by: ['db-migration'],
  },
  {
    id: '5',
    title: 'Research AI task suggestion patterns',
    description: 'Analyze Claude Sonnet 4.5 prompting strategies for task generation',
    status: 'pending' as const,
    phase: 'ideation' as const,
    priority: 'low' as const,
    tags: ['research', 'ai', 'prompting'],
    created_at: '2025-12-07T12:00:00Z',
    updated_at: '2025-12-07T12:00:00Z',
    estimated_hours: 2,
    ai_suggested: true,
    ai_confidence: 0.85,
  },
]

export default function KanbanPage() {
  const { setTasks, tasks, isLoading } = useKanbanStore()

  useEffect(() => {
    // Initialize with mock data if empty
    if (tasks.length === 0) {
      setTasks(mockTasks)
    }
  }, [setTasks, tasks.length])

  const handleAddTask = () => {
    // TODO: Open task creation modal
    console.log('Add task clicked')
  }

  const handleFilter = () => {
    // TODO: Open filter modal
    console.log('Filter clicked')
  }

  const handleExport = () => {
    // TODO: Export tasks to JSON/CSV
    console.log('Export clicked')
  }

  const handleImport = () => {
    // TODO: Import tasks from file
    console.log('Import clicked')
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Kanban Board</h1>
          <p className="text-muted-foreground">
            Manage tasks across UDO v2 development phases
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleFilter}>
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </Button>
          <Button variant="outline" size="sm" onClick={handleImport}>
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button size="sm" onClick={handleAddTask}>
            <Plus className="h-4 w-4 mr-2" />
            Add Task
          </Button>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="flex-1 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">Loading tasks...</p>
          </div>
        ) : (
          <KanbanBoard />
        )}
      </div>

      {/* Stats Footer */}
      <div className="mt-4 p-4 bg-muted/50 rounded-lg">
        <div className="flex gap-6 text-sm">
          <div>
            <span className="text-muted-foreground">Total Tasks: </span>
            <span className="font-semibold">{tasks.length}</span>
          </div>
          <div>
            <span className="text-muted-foreground">In Progress: </span>
            <span className="font-semibold text-yellow-600">
              {tasks.filter((t) => t.status === 'in_progress').length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Blocked: </span>
            <span className="font-semibold text-red-600">
              {tasks.filter((t) => t.status === 'blocked').length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Completed: </span>
            <span className="font-semibold text-green-600">
              {tasks.filter((t) => t.status === 'completed').length}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
