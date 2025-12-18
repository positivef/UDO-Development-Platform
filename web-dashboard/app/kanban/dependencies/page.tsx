"use client"

/**
 * Kanban Dependency Graph Page
 *
 * Week 6 Day 2: Dependency Graph UI (D3.js force-directed visualization)
 *
 * Features:
 * - Select task to visualize dependency graph
 * - Adjust depth (1-10 levels)
 * - D3.js force-directed graph with drag & click
 * - DAG statistics (performance metrics)
 * - Emergency override for blocked tasks (Q7)
 */

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { DependencyGraph as DependencyGraphComponent } from '@/components/kanban/DependencyGraph'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, AlertCircle, TrendingUp, GitBranch, Clock, CheckCircle } from 'lucide-react'
import { kanbanAPI } from '@/lib/api/kanban'
import { getDependencyGraph, getStatistics, emergencyOverride as apiEmergencyOverride } from '@/lib/api/kanban-dependencies'
import type { KanbanTask } from '@/lib/types/kanban'
import type { DependencyGraph, DAGStatistics } from '@/lib/api/kanban-dependencies'

export default function DependenciesPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [depth, setDepth] = useState<number>(3)
  const [graphData, setGraphData] = useState<DependencyGraph | null>(null)
  const [statsData, setStatsData] = useState<DAGStatistics | null>(null)
  const [isLoadingGraph, setIsLoadingGraph] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch all tasks for selection dropdown
  const { data: tasksResponse, isLoading: isLoadingTasks } = useQuery({
    queryKey: ['kanban-tasks'],
    queryFn: () => kanbanAPI.fetchTasks(),
  })

  const tasks = tasksResponse?.tasks || []

  // Auto-select first task if none selected
  useEffect(() => {
    if (tasks.length > 0 && !selectedTaskId) {
      setSelectedTaskId(tasks[0].id)
    }
  }, [tasks, selectedTaskId])

  // Fetch dependency graph when task or depth changes
  useEffect(() => {
    if (!selectedTaskId) return

    const fetchGraph = async () => {
      setIsLoadingGraph(true)
      setError(null)

      try {
        // Fetch dependency graph
        const graph = await getDependencyGraph(selectedTaskId, depth)
        setGraphData(graph)

        // Fetch statistics for all tasks in graph
        const taskIds = graph.nodes.map(node => node.id)
        if (taskIds.length > 0) {
          const stats = await getStatistics(taskIds)
          setStatsData(stats)
        }
      } catch (err) {
        console.error('Failed to fetch dependency graph:', err)
        setError(err instanceof Error ? err.message : 'Failed to load dependency graph')
      } finally {
        setIsLoadingGraph(false)
      }
    }

    fetchGraph()
  }, [selectedTaskId, depth])

  // Convert API graph data to DependencyGraphComponent format
  const convertedTasks: KanbanTask[] = graphData?.nodes.map(node => ({
    id: node.id,
    title: node.title,
    description: '',
    phase: (node.phase as any) || 'ideation',
    status: node.status as any,
    priority: (node.priority as any) || 'medium',
    tags: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    estimated_hours: 0,
    actual_hours: 0,
    dependencies: [],
    blocked_by: graphData.edges
      .filter(edge => edge.target === node.id)
      .map(edge => edge.source),
    ai_suggested: false,
    context_notes: '',
  })) || []

  // Emergency override handler (Q7)
  const handleEmergencyOverride = async (taskId: string, dependencyId: string) => {
    const reason = prompt('Enter reason for emergency override (min 10 chars):')
    if (!reason || reason.length < 10) {
      alert('Reason must be at least 10 characters')
      return
    }

    try {
      await apiEmergencyOverride(dependencyId, reason)
      alert('Dependency overridden successfully')

      // Refresh graph
      if (selectedTaskId) {
        const graph = await getDependencyGraph(selectedTaskId, depth)
        setGraphData(graph)
      }
    } catch (err) {
      console.error('Emergency override failed:', err)
      alert(err instanceof Error ? err.message : 'Failed to override dependency')
    }
  }

  if (isLoadingTasks) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2">Loading tasks...</span>
      </div>
    )
  }

  if (tasks.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No tasks found. Create tasks in the Kanban board to visualize dependencies.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dependency Graph</h1>
        <p className="text-muted-foreground">
          Visualize task dependencies with D3.js force-directed graph
        </p>
      </div>

      {/* Controls */}
      <div className="flex gap-4 items-end">
        {/* Task Selection */}
        <div className="flex-1">
          <Label htmlFor="task-select">Select Task</Label>
          <Select value={selectedTaskId || undefined} onValueChange={setSelectedTaskId}>
            <SelectTrigger id="task-select">
              <SelectValue placeholder="Select a task..." />
            </SelectTrigger>
            <SelectContent>
              {tasks.map((task) => (
                <SelectItem key={task.id} value={task.id}>
                  {task.title} ({task.phase})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Depth Selection */}
        <div className="w-32">
          <Label htmlFor="depth-select">Depth</Label>
          <Select value={depth.toString()} onValueChange={(v) => setDepth(Number(v))}>
            <SelectTrigger id="depth-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((d) => (
                <SelectItem key={d} value={d.toString()}>
                  {d} level{d > 1 ? 's' : ''}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Refresh Button */}
        <Button
          onClick={() => {
            if (selectedTaskId) {
              getDependencyGraph(selectedTaskId, depth).then(setGraphData)
            }
          }}
          disabled={!selectedTaskId || isLoadingGraph}
        >
          {isLoadingGraph ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Loading...
            </>
          ) : (
            'Refresh'
          )}
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Statistics */}
      {statsData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
              <GitBranch className="h-4 w-4" />
              Total Tasks
            </div>
            <div className="text-2xl font-bold">{statsData.total_tasks}</div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
              <TrendingUp className="h-4 w-4" />
              Dependencies
            </div>
            <div className="text-2xl font-bold">{statsData.total_dependencies}</div>
            <div className="text-xs text-muted-foreground">
              Avg: {statsData.avg_dependencies_per_task.toFixed(1)} per task
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
              <TrendingUp className="h-4 w-4" />
              Max Depth
            </div>
            <div className="text-2xl font-bold">{statsData.max_depth}</div>
            <div className="text-xs text-muted-foreground">
              Longest chain
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
              <Clock className="h-4 w-4" />
              Performance
            </div>
            <div className="text-2xl font-bold">
              {statsData.topological_sort_time_ms.toFixed(1)}ms
            </div>
            <div className="text-xs flex items-center gap-1">
              {statsData.meets_performance_target ? (
                <>
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  <span className="text-green-600">Under 50ms target</span>
                </>
              ) : (
                <>
                  <AlertCircle className="h-3 w-3 text-yellow-500" />
                  <span className="text-yellow-600">Above 50ms target</span>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Dependency Graph */}
      {isLoadingGraph ? (
        <div className="flex items-center justify-center h-96 bg-white dark:bg-gray-900 rounded-lg border">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2">Loading dependency graph...</span>
        </div>
      ) : convertedTasks.length > 0 ? (
        <DependencyGraphComponent
          tasks={convertedTasks}
          currentTaskId={selectedTaskId || undefined}
          onTaskClick={(taskId) => setSelectedTaskId(taskId)}
          onEmergencyOverride={handleEmergencyOverride}
        />
      ) : (
        <div className="flex items-center justify-center h-96 bg-white dark:bg-gray-900 rounded-lg border">
          <p className="text-muted-foreground">No dependency data available</p>
        </div>
      )}

      {/* Cycle Warning - TODO: Backend API doesn't return has_cycles/cycles yet */}
      {/* Will be implemented when backend adds these fields to DependencyGraph response */}
    </div>
  )
}
