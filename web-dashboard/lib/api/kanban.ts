/**
 * Kanban API Client - Backend integration for Kanban Board
 *
 * Connects frontend to FastAPI backend endpoints
 * Base URL: http://localhost:8000/api/kanban
 */

import type { KanbanTask, TaskStatus, Priority, Phase } from '@/lib/types/kanban'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const KANBAN_API = `${API_BASE_URL}/api/kanban`

// Error handling helper
class KanbanAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message)
    this.name = 'KanbanAPIError'
  }
}

// Generic fetch wrapper with error handling
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${KANBAN_API}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new KanbanAPIError(
        errorData.detail || `API request failed: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    return response.json()
  } catch (error) {
    if (error instanceof KanbanAPIError) {
      throw error
    }
    throw new KanbanAPIError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

// ============================================================================
// Task CRUD Operations
// ============================================================================

export interface FetchTasksParams {
  status?: TaskStatus
  phase?: Phase
  priority?: Priority
  tags?: string[]
  primary_project?: string
  skip?: number
  limit?: number
}

export interface FetchTasksResponse {
  tasks: KanbanTask[]
  total: number
  skip: number
  limit: number
}

/**
 * Fetch tasks with optional filters and pagination
 * GET /api/kanban/tasks
 */
export async function fetchTasks(
  params?: FetchTasksParams
): Promise<FetchTasksResponse> {
  const queryParams = new URLSearchParams()

  if (params) {
    if (params.status) queryParams.append('status', params.status)
    if (params.phase) queryParams.append('phase', params.phase)
    if (params.priority) queryParams.append('priority', params.priority)
    if (params.tags) params.tags.forEach(tag => queryParams.append('tags', tag))
    if (params.primary_project) queryParams.append('primary_project', params.primary_project)
    if (params.skip !== undefined) queryParams.append('skip', params.skip.toString())
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString())
  }

  const query = queryParams.toString()
  return apiFetch<FetchTasksResponse>(query ? `/tasks?${query}` : '/tasks')
}

/**
 * Get single task by ID
 * GET /api/kanban/tasks/{id}
 */
export async function fetchTaskById(id: string): Promise<KanbanTask> {
  return apiFetch<KanbanTask>(`/tasks/${id}`)
}

export interface CreateTaskRequest {
  title: string
  description: string
  phase: Phase
  priority: Priority
  status?: TaskStatus
  tags?: string[]
  assigned_to?: string
  due_date?: string
  estimated_hours?: number
  primary_project?: string
  related_projects?: string[]
  dependencies?: string[]
  context_notes?: string
}

/**
 * Create new task
 * POST /api/kanban/tasks
 */
export async function createTask(
  task: CreateTaskRequest
): Promise<KanbanTask> {
  return apiFetch<KanbanTask>('/tasks', {
    method: 'POST',
    body: JSON.stringify(task),
  })
}

export interface UpdateTaskRequest {
  title?: string
  description?: string
  phase?: Phase
  priority?: Priority
  tags?: string[]
  assigned_to?: string
  due_date?: string
  estimated_hours?: number
  actual_hours?: number
  primary_project?: string
  related_projects?: string[]
  context_notes?: string
}

/**
 * Update task (partial update)
 * PUT /api/kanban/tasks/{id}
 */
export async function updateTask(
  id: string,
  updates: UpdateTaskRequest
): Promise<KanbanTask> {
  return apiFetch<KanbanTask>(`/tasks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  })
}

/**
 * Delete task
 * DELETE /api/kanban/tasks/{id}
 */
export async function deleteTask(id: string): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`/tasks/${id}`, {
    method: 'DELETE',
  })
}

// ============================================================================
// Task Status/Phase/Priority Operations (for Drag & Drop)
// ============================================================================

/**
 * Update task status (used for drag & drop between columns)
 * PUT /api/kanban/tasks/{id}/status
 */
export async function updateTaskStatus(
  id: string,
  status: TaskStatus
): Promise<KanbanTask> {
  return apiFetch<KanbanTask>(`/tasks/${id}/status`, {
    method: 'PUT',
    body: JSON.stringify({ status }),
  })
}

/**
 * Update task phase
 * PUT /api/kanban/tasks/{id}/phase
 */
export async function updateTaskPhase(
  id: string,
  phase: Phase
): Promise<KanbanTask> {
  return apiFetch<KanbanTask>(`/tasks/${id}/phase`, {
    method: 'PUT',
    body: JSON.stringify({ phase }),
  })
}

/**
 * Update task priority
 * PUT /api/kanban/tasks/{id}/priority
 */
export async function updateTaskPriority(
  id: string,
  priority: Priority
): Promise<KanbanTask> {
  return apiFetch<KanbanTask>(`/tasks/${id}/priority`, {
    method: 'PUT',
    body: JSON.stringify({ priority }),
  })
}

// ============================================================================
// Quality Gates & Archiving (Week 3-4)
// ============================================================================

/**
 * Check quality gates for task completion
 * GET /api/kanban/tasks/{id}/quality-gate
 */
export async function checkQualityGate(id: string): Promise<{
  passed: boolean
  checks: Array<{ name: string; passed: boolean; message: string }>
}> {
  return apiFetch(`/tasks/${id}/quality-gate`)
}

/**
 * Archive completed task (Q6: Done-End archiving)
 * POST /api/kanban/tasks/{id}/archive
 */
export async function archiveTask(id: string): Promise<{
  message: string
  archived_task: KanbanTask
}> {
  return apiFetch(`/tasks/${id}/archive`, {
    method: 'POST',
  })
}

// ============================================================================
// Batch Operations
// ============================================================================

/**
 * Bulk update task statuses (for optimization)
 * PUT /api/kanban/tasks/bulk/status
 */
export async function bulkUpdateStatus(
  updates: Array<{ id: string; status: TaskStatus }>
): Promise<{ updated: number; tasks: KanbanTask[] }> {
  return apiFetch('/tasks/bulk/status', {
    method: 'PUT',
    body: JSON.stringify({ updates }),
  })
}

// ============================================================================
// Export API client object for convenience
// ============================================================================

export const kanbanAPI = {
  // CRUD
  fetchTasks,
  fetchTaskById,
  createTask,
  updateTask,
  deleteTask,

  // Status/Phase/Priority
  updateTaskStatus,
  updateTaskPhase,
  updateTaskPriority,

  // Quality & Archiving
  checkQualityGate,
  archiveTask,

  // Batch
  bulkUpdateStatus,
}

export default kanbanAPI
