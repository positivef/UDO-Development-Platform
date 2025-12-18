/**
 * Kanban Dependencies API Client - Backend integration for task dependencies
 *
 * Week 6 Day 2: Dependencies UI implementation
 * Implements Q7 (Hard Block dependencies with emergency override)
 *
 * Base URL: http://localhost:8000/api/kanban/dependencies
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const DEPENDENCIES_API = `${API_BASE_URL}/api/kanban/dependencies`

// ============================================================================
// Types
// ============================================================================

export type DependencyType = 'blocks' | 'blocked_by' | 'related'
export type DependencyStatus = 'ACTIVE' | 'OVERRIDDEN' | 'RESOLVED'

export interface Dependency {
  dependency_id: string
  source_task_id: string
  target_task_id: string
  dependency_type: DependencyType
  hard_block: boolean
  status: DependencyStatus
  override_reason?: string
  overridden_by?: string
  overridden_at?: string
  created_at: string
  updated_at: string
}

export interface DependencyCreate {
  source_task_id: string
  target_task_id: string
  dependency_type: DependencyType
  hard_block?: boolean
}

export interface EmergencyOverride {
  dependency_id: string
  override_reason: string
  overridden_by?: string
}

export interface DependencyAudit {
  audit_id: string
  dependency_id: string
  action: string
  old_status: DependencyStatus
  new_status: DependencyStatus
  reason: string
  performed_by: string
  performed_at: string
}

export interface DependencyGraphNode {
  id: string
  title: string
  phase: string
  priority: string
  status: string
  blocked: boolean
  completeness: number
}

export interface DependencyGraphEdge {
  source: string
  target: string
  type: DependencyType
  hard_block: boolean
  status: DependencyStatus
}

export interface DependencyGraph {
  nodes: DependencyGraphNode[]
  edges: DependencyGraphEdge[]
  root_task_id: string
  depth: number
}

export interface TopologicalSortResult {
  sorted_task_ids: string[]
  execution_time_ms: number
  task_count: number
  has_cycle: boolean
}

export interface DAGStatistics {
  total_tasks: number
  total_dependencies: number
  max_depth: number
  avg_dependencies_per_task: number
  topological_sort_time_ms: number
  cycle_detection_time_ms: number
  meets_performance_target: boolean
}

// ============================================================================
// Error Handling
// ============================================================================

export class DependenciesAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string,
    public details?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'DependenciesAPIError'
  }
}

// Generic fetch wrapper with error handling
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${DEPENDENCIES_API}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new DependenciesAPIError(
        errorData.error?.message || `API request failed: ${response.statusText}`,
        response.status,
        errorData.error?.code,
        errorData.error?.details
      )
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  } catch (error) {
    if (error instanceof DependenciesAPIError) {
      throw error
    }
    throw new DependenciesAPIError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

// ============================================================================
// CRUD Operations
// ============================================================================

/**
 * Create new dependency with DAG cycle validation
 * POST /api/kanban/dependencies
 */
export async function createDependency(
  data: DependencyCreate
): Promise<Dependency> {
  return apiFetch<Dependency>('', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Get dependency by ID
 * GET /api/kanban/dependencies/{dependency_id}
 */
export async function getDependency(
  dependencyId: string
): Promise<Dependency> {
  return apiFetch<Dependency>(`/${dependencyId}`)
}

/**
 * Delete dependency
 * DELETE /api/kanban/dependencies/{dependency_id}
 */
export async function deleteDependency(
  dependencyId: string
): Promise<void> {
  return apiFetch<void>(`/${dependencyId}`, {
    method: 'DELETE',
  })
}

/**
 * Get dependency audit log
 * GET /api/kanban/dependencies/audit
 */
export async function getAuditLog(
  limit: number = 50,
  offset: number = 0
): Promise<DependencyAudit[]> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  })
  return apiFetch<DependencyAudit[]>(`/audit?${params}`)
}

// ============================================================================
// Task-Specific Operations
// ============================================================================

/**
 * Get all dependencies for a task (tasks this task depends on)
 * GET /api/kanban/dependencies/tasks/{task_id}/dependencies
 */
export async function getTaskDependencies(
  taskId: string
): Promise<Dependency[]> {
  return apiFetch<Dependency[]>(`/tasks/${taskId}/dependencies`)
}

/**
 * Get all dependents for a task (tasks that depend on this task)
 * GET /api/kanban/dependencies/tasks/{task_id}/dependents
 */
export async function getTaskDependents(
  taskId: string
): Promise<Dependency[]> {
  return apiFetch<Dependency[]>(`/tasks/${taskId}/dependents`)
}

/**
 * Get dependency graph for D3.js visualization
 * GET /api/kanban/dependencies/tasks/{task_id}/dependency-graph
 */
export async function getDependencyGraph(
  taskId: string,
  depth: number = 3
): Promise<DependencyGraph> {
  const params = new URLSearchParams({ depth: depth.toString() })
  return apiFetch<DependencyGraph>(`/tasks/${taskId}/dependency-graph?${params}`)
}

/**
 * Perform topological sort on task dependencies
 * GET /api/kanban/dependencies/topological-sort
 */
export async function topologicalSort(
  taskIds: string[]
): Promise<TopologicalSortResult> {
  const params = new URLSearchParams({ task_ids: taskIds.join(',') })
  return apiFetch<TopologicalSortResult>(`/topological-sort?${params}`)
}

/**
 * Get DAG performance statistics
 * GET /api/kanban/dependencies/statistics
 */
export async function getStatistics(
  taskIds: string[]
): Promise<DAGStatistics> {
  const params = new URLSearchParams({ task_ids: taskIds.join(',') })
  return apiFetch<DAGStatistics>(`/statistics?${params}`)
}

// ============================================================================
// Emergency Override (Q7)
// ============================================================================

/**
 * Emergency override for dependency
 * POST /api/kanban/dependencies/{dependency_id}/override
 *
 * Requires project_owner role (not developer)
 */
export async function emergencyOverride(
  dependencyId: string,
  reason: string
): Promise<Dependency> {
  const data: EmergencyOverride = {
    dependency_id: dependencyId,
    override_reason: reason,
  }
  return apiFetch<Dependency>(`/${dependencyId}/override`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// ============================================================================
// Export API client object for convenience
// ============================================================================

export const dependenciesAPI = {
  // CRUD
  createDependency,
  getDependency,
  deleteDependency,
  getAuditLog,

  // Task-specific
  getTaskDependencies,
  getTaskDependents,
  getDependencyGraph,
  topologicalSort,
  getStatistics,

  // Emergency override
  emergencyOverride,
}

export default dependenciesAPI
