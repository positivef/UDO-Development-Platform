/**
 * Kanban Archive API Client - Backend integration for Archive View
 *
 * Week 7 Day 3: Backend API Integration
 * Connects frontend to FastAPI Archive endpoints
 * Base URL: http://localhost:8000/api/kanban/archive
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const ARCHIVE_API = `${API_BASE_URL}/api/kanban/archive`

// Error handling helper
class ArchiveAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message)
    this.name = 'ArchiveAPIError'
  }
}

// Generic fetch wrapper with error handling
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${ARCHIVE_API}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ArchiveAPIError(
        errorData.error?.message || errorData.detail || `API request failed: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    return response.json()
  } catch (error) {
    if (error instanceof ArchiveAPIError) {
      throw error
    }
    throw new ArchiveAPIError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

// ============================================================================
// Archive Types (matching backend models)
// ============================================================================

export interface AISummary {
  summary: string
  key_learnings: string[]
  technical_insights: string[]
  next_steps_recommendation: string[]
}

export interface ROIMetrics {
  efficiency_score: number
  time_saved_hours: number
  quality_score: number
  constitutional_compliance_rate: number
}

export interface ObsidianKnowledgeEntry {
  extracted: boolean
  note_path?: string
  tags?: string[]
  linked_concepts?: string[]
}

export interface ArchivedTask {
  id: string
  task_id: string
  title: string
  description: string
  phase: string
  priority: string
  status: string
  archived_by: string
  archived_at: string
  ai_summary: AISummary
  roi_metrics: ROIMetrics
  obsidian_knowledge: ObsidianKnowledgeEntry
  was_ai_suggested: boolean
  original_confidence?: number
}

export interface ArchiveStats {
  total_count: number
  avg_efficiency: number
  total_time_saved: number
  avg_quality_score: number
}

export interface ArchiveListResponse {
  items: ArchivedTask[]
  total: number
  page: number
  per_page: number
  total_pages: number
  statistics: ArchiveStats
}

// ============================================================================
// Archive Operations
// ============================================================================

export interface ArchiveFilters {
  phase?: string
  archived_by?: string
  ai_suggested?: boolean
  obsidian_synced?: boolean
  min_quality_score?: number
  page?: number
  per_page?: number
}

/**
 * Get paginated list of archived tasks with filtering
 * GET /api/kanban/archive
 */
export async function fetchArchiveList(
  filters?: ArchiveFilters
): Promise<ArchiveListResponse> {
  const queryParams = new URLSearchParams()

  if (filters) {
    if (filters.phase) queryParams.append('phase', filters.phase)
    if (filters.archived_by) queryParams.append('archived_by', filters.archived_by)
    if (filters.ai_suggested !== undefined) queryParams.append('ai_suggested', filters.ai_suggested.toString())
    if (filters.obsidian_synced !== undefined) queryParams.append('obsidian_synced', filters.obsidian_synced.toString())
    if (filters.min_quality_score !== undefined) queryParams.append('min_quality_score', filters.min_quality_score.toString())
    if (filters.page !== undefined) queryParams.append('page', filters.page.toString())
    if (filters.per_page !== undefined) queryParams.append('per_page', filters.per_page.toString())
  }

  const query = queryParams.toString()
  return apiFetch<ArchiveListResponse>(query ? `?${query}` : '')
}

/**
 * Get specific archived task by ID
 * GET /api/kanban/archive/{id}
 */
export async function fetchArchivedTask(id: string): Promise<ArchivedTask> {
  return apiFetch<ArchivedTask>(`/${id}`)
}

/**
 * Get ROI statistics for all archived tasks
 * GET /api/kanban/archive/statistics/roi
 */
export async function fetchArchiveStatistics(): Promise<ArchiveStats> {
  return apiFetch<ArchiveStats>('/statistics/roi')
}

/**
 * Archive a completed task
 * POST /api/kanban/archive
 */
export interface ArchiveTaskRequest {
  task_id: string
  archived_by?: string  // Will be set by backend from current user
}

export async function archiveTask(
  request: ArchiveTaskRequest
): Promise<{ message: string; archived_task: ArchivedTask }> {
  return apiFetch('', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Restore archived task
 * POST /api/kanban/archive/{id}/restore
 */
export async function restoreArchivedTask(id: string): Promise<{
  message: string
  restored_task: any
}> {
  return apiFetch(`/${id}/restore`, {
    method: 'POST',
  })
}

// ============================================================================
// Export API client object for convenience
// ============================================================================

export const archiveAPI = {
  fetchArchiveList,
  fetchArchivedTask,
  fetchArchiveStatistics,
  archiveTask,
  restoreArchivedTask,
}

export default archiveAPI
