"use client"

/**
 * Kanban Page - Main Kanban Board view
 *
 * Features:
 * - Full Kanban board with drag & drop
 * - Task management (create, update, delete)
 * - Integration with UDO v2 Phase system
 * - Real-time updates via WebSocket
 * - Backend API integration with fallback to mock data
 */

import { useEffect, useState, useMemo } from 'react'
import dynamic from 'next/dynamic'
import { KanbanBoard } from '@/components/kanban/KanbanBoard'
import { TaskCreateModal } from '@/components/kanban/TaskCreateModal'
import { useFilterState } from '@/components/kanban/FilterPanel'
import { useKanbanStore } from '@/lib/stores/kanban-store'
import { useKanbanTasks } from '@/hooks/useKanban'
import { Button } from '@/components/ui/button'
import { Plus, Download, Upload, RefreshCw, AlertCircle, Wifi, WifiOff } from 'lucide-react'
import type { KanbanTask } from '@/lib/types/kanban'

// Dynamic import to prevent SSR issues with lucide-react icons
const FilterPanel = dynamic(
  () => import('@/components/kanban/FilterPanel').then(mod => ({ default: mod.FilterPanel })),
  { ssr: false }
)

// Sample mock data for fallback when API is unavailable
const mockTasks: KanbanTask[] = [
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
  const { setTasks, tasks, isLoading: storeLoading, error: storeError, clearError } = useKanbanStore()
  const [useMockData, setUseMockData] = useState(false)
  const [isOnline, setIsOnline] = useState(true)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const { filters, setFilters, hasActiveFilters } = useFilterState()

  // Filter tasks based on active filters
  const filteredTasks = useMemo(() => {
    if (!hasActiveFilters) return tasks

    return tasks.filter((task) => {
      // Phase filter
      if (filters.phases.length > 0 && !filters.phases.includes(task.phase)) {
        return false
      }
      // Status filter
      if (filters.statuses.length > 0 && !filters.statuses.includes(task.status)) {
        return false
      }
      // Priority filter
      if (filters.priorities.length > 0 && !filters.priorities.includes(task.priority)) {
        return false
      }
      return true
    })
  }, [tasks, filters, hasActiveFilters])

  // Fetch tasks from API
  const {
    data: apiData,
    isLoading: apiLoading,
    isError: apiError,
    error: apiErrorDetails,
    refetch,
  } = useKanbanTasks()

  // Track online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Handle API response or fallback to mock data
  useEffect(() => {
    if (apiData?.tasks && apiData.tasks.length > 0) {
      // Use API data
      setUseMockData(false)
    } else if (apiError || !isOnline) {
      // Fallback to mock data
      if (tasks.length === 0) {
        setTasks(mockTasks)
        setUseMockData(true)
      }
    } else if (!apiLoading && (!apiData?.tasks || apiData.tasks.length === 0)) {
      // API returned empty, use mock data for demo
      if (tasks.length === 0) {
        setTasks(mockTasks)
        setUseMockData(true)
      }
    }
  }, [apiData, apiError, apiLoading, isOnline, setTasks, tasks.length])

  const isLoading = apiLoading || storeLoading

  const handleAddTask = () => {
    setIsCreateModalOpen(true)
  }

  const handleCreateSuccess = () => {
    // Refetch tasks after successful creation
    refetch()
  }


  const handleExport = () => {
    // TODO: Export tasks to JSON/CSV
    console.log('Export clicked')
  }

  const handleImport = () => {
    // TODO: Import tasks from file
    console.log('Import clicked')
  }

  const handleRefresh = async () => {
    clearError()
    try {
      await refetch()
    } catch (error) {
      console.error('Failed to refresh tasks:', error)
    }
  }

  const handleRetryApi = async () => {
    setUseMockData(false)
    clearError()
    try {
      const result = await refetch()
      if (result.data?.tasks && result.data.tasks.length > 0) {
        setTasks(result.data.tasks)
      }
    } catch (error) {
      console.error('Failed to reconnect to API:', error)
    }
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
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <FilterPanel filters={filters} onFiltersChange={setFilters} />
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

      {/* Connection Status Banner */}
      {(useMockData || !isOnline || apiError) && (
        <div className={`mb-4 p-3 rounded-lg flex items-center justify-between ${
          !isOnline
            ? 'bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
            : 'bg-yellow-100 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
        }`}>
          <div className="flex items-center gap-2">
            {!isOnline ? (
              <>
                <WifiOff className="h-4 w-4 text-red-600" />
                <span className="text-sm text-red-700 dark:text-red-300">
                  Offline - Changes will sync when connection is restored
                </span>
              </>
            ) : (
              <>
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <span className="text-sm text-yellow-700 dark:text-yellow-300">
                  Using demo data - Backend API unavailable
                  {apiErrorDetails && (
                    <span className="ml-1 text-xs opacity-75">
                      ({apiErrorDetails instanceof Error ? apiErrorDetails.message : 'Connection error'})
                    </span>
                  )}
                </span>
              </>
            )}
          </div>
          {isOnline && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRetryApi}
              className="text-yellow-700 border-yellow-300 hover:bg-yellow-200"
            >
              <Wifi className="h-3 w-3 mr-1" />
              Retry Connection
            </Button>
          )}
        </div>
      )}

      {/* Error Banner */}
      {storeError && (
        <div className="mb-4 p-3 rounded-lg bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <span className="text-sm text-red-700 dark:text-red-300">{storeError}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={clearError}
            className="text-red-700 border-red-300 hover:bg-red-200"
          >
            Dismiss
          </Button>
        </div>
      )}

      {/* Kanban Board */}
      <div className="flex-1 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-2">
              <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
              <p className="text-muted-foreground">Loading tasks...</p>
            </div>
          </div>
        ) : (
          <KanbanBoard tasks={hasActiveFilters ? filteredTasks : undefined} />
        )}
      </div>

      {/* Stats Footer */}
      <div className="mt-4 p-4 bg-muted/50 rounded-lg">
        <div className="flex gap-6 text-sm">
          <div>
            <span className="text-muted-foreground">
              {hasActiveFilters ? 'Showing: ' : 'Total Tasks: '}
            </span>
            <span className="font-semibold">
              {hasActiveFilters ? `${filteredTasks.length} / ${tasks.length}` : tasks.length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">In Progress: </span>
            <span className="font-semibold text-yellow-600">
              {filteredTasks.filter((t) => t.status === 'in_progress').length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Blocked: </span>
            <span className="font-semibold text-red-600">
              {filteredTasks.filter((t) => t.status === 'blocked').length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Completed: </span>
            <span className="font-semibold text-green-600">
              {filteredTasks.filter((t) => t.status === 'completed').length}
            </span>
          </div>
          <div className="ml-auto flex gap-2">
            {hasActiveFilters && (
              <span className="text-xs text-blue-600 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 rounded">
                Filtered
              </span>
            )}
            {useMockData && (
              <span className="text-xs text-muted-foreground px-2 py-1 bg-muted rounded">
                Demo Mode
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Task Create Modal */}
      <TaskCreateModal
        open={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleCreateSuccess}
      />
    </div>
  )
}
