/**
 * useKanban - React Query hooks for Kanban Board
 *
 * Provides data fetching, caching, and optimistic updates for Kanban operations.
 * Integrates with Zustand store for local state management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { kanbanAPI, FetchTasksParams } from '@/lib/api/kanban'
import { useKanbanStore } from '@/lib/stores/kanban-store'
import type { KanbanTask, TaskStatus } from '@/lib/types/kanban'

// Query keys
export const kanbanKeys = {
  all: ['kanban'] as const,
  tasks: () => [...kanbanKeys.all, 'tasks'] as const,
  tasksFiltered: (params: FetchTasksParams) => [...kanbanKeys.tasks(), params] as const,
  task: (id: string) => [...kanbanKeys.all, 'task', id] as const,
}

/**
 * Hook to fetch all tasks
 * Syncs with Zustand store for local operations
 */
export function useKanbanTasks(params?: FetchTasksParams) {
  const { setTasks, setLoading, setError } = useKanbanStore()

  return useQuery({
    queryKey: params ? kanbanKeys.tasksFiltered(params) : kanbanKeys.tasks(),
    queryFn: async () => {
      setLoading(true)
      try {
        const response = await kanbanAPI.fetchTasks(params)
        setTasks(response.tasks)
        return response
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch tasks'
        setError(message)
        throw error
      } finally {
        setLoading(false)
      }
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  })
}

/**
 * Hook to fetch a single task
 */
export function useKanbanTask(id: string | null) {
  return useQuery({
    queryKey: kanbanKeys.task(id || ''),
    queryFn: () => kanbanAPI.fetchTaskById(id!),
    enabled: !!id,
  })
}

/**
 * Hook for task status update with optimistic updates
 * Used for drag & drop operations
 */
export function useUpdateTaskStatus() {
  const queryClient = useQueryClient()
  const { moveTask, updateTask } = useKanbanStore()

  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatus }) =>
      kanbanAPI.updateTaskStatus(id, status),

    // Optimistic update - update UI immediately
    onMutate: async ({ id, status }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: kanbanKeys.tasks() })

      // Snapshot current state for rollback
      const previousTasks = queryClient.getQueryData(kanbanKeys.tasks())

      // Optimistically update local store
      moveTask(id, status)

      return { previousTasks }
    },

    // On success - sync with server response
    onSuccess: (serverTask) => {
      // Update with server data (timestamps, etc.)
      updateTask(serverTask.id, serverTask)
    },

    // On error - rollback to previous state
    onError: (error, variables, context) => {
      console.error('Failed to update task status:', error)

      // Rollback optimistic update
      if (context?.previousTasks) {
        queryClient.setQueryData(kanbanKeys.tasks(), context.previousTasks)
        // Also rollback store
        const store = useKanbanStore.getState()
        store.setTasks((context.previousTasks as { tasks: KanbanTask[] })?.tasks || [])
      }
    },

    // Always refetch after mutation settles
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: kanbanKeys.tasks() })
    },
  })
}

/**
 * Hook for creating a new task
 */
export function useCreateTask() {
  const queryClient = useQueryClient()
  const { addTask } = useKanbanStore()

  return useMutation({
    mutationFn: kanbanAPI.createTask,

    onSuccess: (newTask) => {
      // Add to local store
      addTask(newTask)
      // Invalidate queries to refetch
      queryClient.invalidateQueries({ queryKey: kanbanKeys.tasks() })
    },

    onError: (error) => {
      console.error('Failed to create task:', error)
    },
  })
}

/**
 * Hook for updating a task
 */
export function useUpdateTask() {
  const queryClient = useQueryClient()
  const { updateTask } = useKanbanStore()

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Parameters<typeof kanbanAPI.updateTask>[1] }) =>
      kanbanAPI.updateTask(id, updates),

    onMutate: async ({ id, updates }) => {
      await queryClient.cancelQueries({ queryKey: kanbanKeys.task(id) })

      const previousTask = queryClient.getQueryData(kanbanKeys.task(id))

      // Optimistic update
      updateTask(id, updates)

      return { previousTask }
    },

    onSuccess: (serverTask) => {
      updateTask(serverTask.id, serverTask)
      queryClient.setQueryData(kanbanKeys.task(serverTask.id), serverTask)
    },

    onError: (error, { id }, context) => {
      console.error('Failed to update task:', error)
      if (context?.previousTask) {
        updateTask(id, context.previousTask as KanbanTask)
      }
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: kanbanKeys.task(id) })
      queryClient.invalidateQueries({ queryKey: kanbanKeys.tasks() })
    },
  })
}

/**
 * Hook for deleting a task
 */
export function useDeleteTask() {
  const queryClient = useQueryClient()
  const { deleteTask } = useKanbanStore()

  return useMutation({
    mutationFn: (id: string) => kanbanAPI.deleteTask(id),

    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: kanbanKeys.tasks() })

      const previousTasks = queryClient.getQueryData(kanbanKeys.tasks())

      // Optimistic delete
      deleteTask(id)

      return { previousTasks }
    },

    onError: (error, _, context) => {
      console.error('Failed to delete task:', error)
      if (context?.previousTasks) {
        const store = useKanbanStore.getState()
        store.setTasks((context.previousTasks as { tasks: KanbanTask[] })?.tasks || [])
      }
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: kanbanKeys.tasks() })
    },
  })
}

/**
 * Combined hook for common Kanban operations
 */
export function useKanban(params?: FetchTasksParams) {
  const tasksQuery = useKanbanTasks(params)
  const updateStatusMutation = useUpdateTaskStatus()
  const createTaskMutation = useCreateTask()
  const updateTaskMutation = useUpdateTask()
  const deleteTaskMutation = useDeleteTask()

  const handleMoveTask = useCallback(
    (taskId: string, newStatus: TaskStatus) => {
      updateStatusMutation.mutate({ id: taskId, status: newStatus })
    },
    [updateStatusMutation]
  )

  return {
    // Query state
    tasks: tasksQuery.data?.tasks || [],
    total: tasksQuery.data?.total || 0,
    isLoading: tasksQuery.isLoading,
    isError: tasksQuery.isError,
    error: tasksQuery.error,
    refetch: tasksQuery.refetch,

    // Mutations
    moveTask: handleMoveTask,
    isMoving: updateStatusMutation.isPending,
    createTask: createTaskMutation.mutate,
    isCreating: createTaskMutation.isPending,
    updateTask: updateTaskMutation.mutate,
    isUpdating: updateTaskMutation.isPending,
    deleteTask: deleteTaskMutation.mutate,
    isDeleting: deleteTaskMutation.isPending,
  }
}
