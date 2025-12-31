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
import { useTranslations } from 'next-intl'
import dynamic from 'next/dynamic'
import { KanbanBoard } from '@/components/kanban/KanbanBoard'
import { TaskCreateModal } from '@/components/kanban/TaskCreateModal'
import { AISuggestionModal } from '@/components/kanban/AISuggestionModal'
import { DependencyGraph } from '@/components/DependencyGraph'
import { useFilterState } from '@/components/kanban/FilterPanel'
import { useKanbanStore, getMockTasks } from '@/lib/stores/kanban-store'
import { useKanbanTasks } from '@/hooks/useKanban'
import { useKanbanWebSocket } from '@/hooks/useKanbanWebSocket'
import type { ConnectionStatus } from '@/lib/websocket/kanban-client'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Plus, Download, Upload, RefreshCw, AlertCircle, Wifi, WifiOff, Sparkles, Radio, LayoutGrid, GitBranch } from 'lucide-react'
import type { KanbanTask } from '@/lib/types/kanban'

// Dynamic import to prevent SSR issues with lucide-react icons
const FilterPanel = dynamic(
  () => import('@/components/kanban/FilterPanel').then(mod => ({ default: mod.FilterPanel })),
  { ssr: false }
)

// Use complete mock data from kanban-store (includes Week 6 Day 4 features: due_date, comments, dependencies)
const mockTasks = getMockTasks()

export default function KanbanPage() {
  const t = useTranslations('kanban')
  const { setTasks, tasks: storeTasks, isLoading: storeLoading, error: storeError, clearError } = useKanbanStore()
  const [useMockData, setUseMockData] = useState(false)
  const [isOnline, setIsOnline] = useState(true)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isAISuggestionOpen, setIsAISuggestionOpen] = useState(false)
  const [wsStatus, setWsStatus] = useState<ConnectionStatus>('disconnected')
  const [activeClients, setActiveClients] = useState(1)
  const { filters, setFilters, hasActiveFilters } = useFilterState()

  // Week 6 Day 2: View toggle (Board / Graph)
  const [currentView, setCurrentView] = useState<'board' | 'graph'>('board')
  const [selectedTaskForGraph, setSelectedTaskForGraph] = useState<KanbanTask | null>(null)

  // WebSocket for real-time updates (Week 7+)
  const {
    broadcastTaskCreated,
    broadcastTaskUpdated,
    broadcastTaskMoved,
    broadcastTaskDeleted,
    broadcastTaskArchived,
  } = useKanbanWebSocket({
    projectId: 'default', // TODO: Get from project selector
    enabled: true,
    onStatusChange: (status) => {
      setWsStatus(status)
      console.log('[KanbanPage] WebSocket status:', status)
    },
    onMessage: (message) => {
      // Track active clients
      if (message.type === 'client_joined' || message.type === 'client_left') {
        setActiveClients(message.active_clients)
      }
    },
    onTaskCreated: (task) => {
      console.log('[KanbanPage] Task created by another user:', task)
      // Refetch to get the latest data
      refetch()
    },
    onTaskUpdated: ({ task_id, updates }) => {
      console.log('[KanbanPage] Task updated by another user:', task_id, updates)
      // Refetch to get the latest data
      refetch()
    },
    onTaskDeleted: (task_id) => {
      console.log('[KanbanPage] Task deleted by another user:', task_id)
      // Refetch to get the latest data
      refetch()
    },
    onTaskArchived: ({ task_id }) => {
      console.log('[KanbanPage] Task archived by another user:', task_id)
      // Refetch to get the latest data
      refetch()
    },
  })

  // Ensure tasks is always an array (fix undefined error)
  const tasks = storeTasks || []

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

  // Initialize with mock data immediately, then update if API succeeds
  useEffect(() => {
    // Always start with mock data to avoid loading spinner blocking UI
    if (tasks.length === 0) {
      setTasks(mockTasks)
      setUseMockData(true)
    }
  }, []) // Run once on mount

  // Handle API response - update to real data if available
  useEffect(() => {
    if (apiData?.tasks && apiData.tasks.length > 0) {
      // Use API data
      setTasks(apiData.tasks)
      setUseMockData(false)
    } else if (apiError || !isOnline) {
      // Keep using mock data on API error
      setUseMockData(true)
    }
  }, [apiData, apiError, isOnline, setTasks])

  // Only show loading spinner if we have no tasks yet (initial load)
  const isLoading = (apiLoading || storeLoading) && tasks.length === 0

  const handleAddTask = () => {
    setIsCreateModalOpen(true)
  }

  const handleCreateSuccess = () => {
    // Refetch tasks after successful creation
    refetch()
  }

  const handleAITaskCreated = () => {
    // Refetch tasks after AI-suggested task creation
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
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold">{t('title')}</h1>
            <p className="text-muted-foreground">
              {t('description')}
            </p>
          </div>

          {/* WebSocket Connection Status */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-muted">
            {wsStatus === 'connected' && (
              <>
                <Radio className="h-4 w-4 text-green-500 animate-pulse" />
                <span className="text-sm font-medium">{t('wsStatus.live')}</span>
                {activeClients > 1 && (
                  <Badge variant="outline" className="text-xs">
                    {activeClients} {t('wsStatus.users')}
                  </Badge>
                )}
              </>
            )}
            {wsStatus === 'connecting' && (
              <>
                <Wifi className="h-4 w-4 text-yellow-500 animate-spin" />
                <span className="text-sm text-muted-foreground">{t('wsStatus.connecting')}</span>
              </>
            )}
            {wsStatus === 'disconnected' && (
              <>
                <WifiOff className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">{t('wsStatus.offline')}</span>
              </>
            )}
            {wsStatus === 'error' && (
              <>
                <AlertCircle className="h-4 w-4 text-red-500" />
                <span className="text-sm text-red-500">{t('wsStatus.error')}</span>
              </>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {/* Week 6 Day 2: View Toggle */}
          <div className="flex items-center gap-1 p-1 bg-muted rounded-lg">
            <Button
              variant={currentView === 'board' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setCurrentView('board')}
              className="h-8"
            >
              <LayoutGrid className="h-4 w-4 mr-2" />
              {t('viewBoard')}
            </Button>
            <Button
              variant={currentView === 'graph' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setCurrentView('graph')}
              className="h-8"
            >
              <GitBranch className="h-4 w-4 mr-2" />
              {t('viewGraph')}
            </Button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            {t('refresh')}
          </Button>
          <FilterPanel filters={filters} onFiltersChange={setFilters} />
          <Button variant="outline" size="sm" onClick={handleImport}>
            <Upload className="h-4 w-4 mr-2" />
            {t('import')}
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            {t('export')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsAISuggestionOpen(true)}
            className="bg-purple-500/10 hover:bg-purple-500/20 text-purple-600 border-purple-500/20"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            {t('aiSuggest')}
          </Button>
          <Button size="sm" onClick={handleAddTask}>
            <Plus className="h-4 w-4 mr-2" />
            {t('createTask')}
          </Button>
        </div>
      </div>

      {/* WebSocket Status Banner */}
      {wsStatus === 'connected' && activeClients > 1 && (
        <div className="mb-4 p-3 rounded-lg bg-blue-100 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 flex items-center gap-2">
          <Radio className="h-4 w-4 text-blue-600 animate-pulse" />
          <span className="text-sm text-blue-700 dark:text-blue-300">
            {t('realTimeSync')} • {activeClients} {t('wsStatus.users')}
          </span>
        </div>
      )}

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
                  {t('offlineMessage')}
                </span>
              </>
            ) : (
              <>
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <span className="text-sm text-yellow-700 dark:text-yellow-300">
                  {t('demoMessage')}
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
              {t('retryConnection')}
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
            {t('dismiss')}
          </Button>
        </div>
      )}

      {/* Main Content Area - Board or Graph View */}
      <div className="flex-1 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-2">
              <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
              <p className="text-muted-foreground">{t('loadingTasks')}</p>
            </div>
          </div>
        ) : currentView === 'board' ? (
          <KanbanBoard
            tasks={hasActiveFilters ? filteredTasks : tasks}
            onBroadcastTaskMoved={broadcastTaskMoved}
            onBroadcastTaskUpdated={broadcastTaskUpdated}
            onBroadcastTaskDeleted={broadcastTaskDeleted}
            onBroadcastTaskArchived={broadcastTaskArchived}
          />
        ) : (
          /* Week 6 Day 2: Dependency Graph View */
          <div className="h-full flex flex-col gap-4">
            {/* Task Selector for Graph View */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <label className="text-sm font-medium mb-2 block">
                {t('graph.selectTask')}
              </label>
              <div className="flex gap-2 flex-wrap">
                {(hasActiveFilters ? filteredTasks : tasks).map((task) => (
                  <Button
                    key={task.id}
                    variant={selectedTaskForGraph?.id === task.id ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedTaskForGraph(task)}
                    className="flex items-center gap-2"
                  >
                    <span className="truncate max-w-[200px]">{task.title}</span>
                    <Badge variant="secondary" className="text-xs">
                      {task.phase}
                    </Badge>
                  </Button>
                ))}
              </div>
            </div>

            {/* Dependency Graph Display */}
            {selectedTaskForGraph ? (
              <div className="flex-1 overflow-auto">
                <DependencyGraph
                  taskId={selectedTaskForGraph.id}
                  depth={3}
                  onNodeClick={(nodeId) => {
                    // Find task and update selection
                    const task = tasks.find((t) => t.id === nodeId)
                    if (task) {
                      setSelectedTaskForGraph(task)
                    }
                  }}
                  height={600}
                  width={1200}
                />
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <GitBranch className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">{t('graph.noSelection')}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Stats Footer */}
      <div className="mt-4 p-4 bg-muted/50 rounded-lg">
        <div className="flex gap-6 text-sm">
          <div>
            <span className="text-muted-foreground">
              {hasActiveFilters ? `${t('stats.showing')}: ` : `${t('stats.totalTasks')}: `}
            </span>
            <span className="font-semibold">
              {hasActiveFilters ? `${filteredTasks.length} / ${tasks.length}` : tasks.length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">{t('stats.inProgress')}: </span>
            <span className="font-semibold text-yellow-600">
              {filteredTasks.filter((task) => task.status === 'in_progress').length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">{t('stats.blocked')}: </span>
            <span className="font-semibold text-red-600">
              {filteredTasks.filter((task) => task.status === 'blocked').length}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">{t('stats.completed')}: </span>
            <span className="font-semibold text-green-600">
              {filteredTasks.filter((task) => task.status === 'completed').length}
            </span>
          </div>
          <div className="ml-auto flex gap-2">
            {hasActiveFilters && (
              <span className="text-xs text-blue-600 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 rounded">
                {t('stats.filtered')}
              </span>
            )}
            {useMockData && (
              <span className="text-xs text-muted-foreground px-2 py-1 bg-muted rounded">
                {t('stats.demoMode')}
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
        availableTasks={tasks}  // Q7: Pass tasks for dependency selection
        onBroadcastTaskCreated={broadcastTaskCreated}  // Week 7: Real-time sync
      />

      {/* AI Suggestion Modal (Q2: AI Hybrid) */}
      <AISuggestionModal
        open={isAISuggestionOpen}
        onClose={() => setIsAISuggestionOpen(false)}
        onTaskCreated={handleAITaskCreated}
      />
    </div>
  )
}
