/**
 * Kanban AI API Client - Backend integration for AI task suggestions
 *
 * Week 6 Day 3: AI Task Suggestion Modal implementation
 * Implements Q2: AI Hybrid (suggest + approve) with Constitutional compliance (P1-P17)
 *
 * Base URL: http://localhost:8000/api/kanban/ai
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const AI_API = `${API_BASE_URL}/api/kanban/ai`

// ============================================================================
// Types
// ============================================================================

export type PhaseName = 'ideation' | 'design' | 'mvp' | 'implementation' | 'testing'
export type SuggestionConfidence = 'high' | 'medium' | 'low'

export interface TaskSuggestionRequest {
  project_id?: string
  phase_name: PhaseName
  context: string
  num_suggestions?: number  // 1-5, default 3
  include_dependencies?: boolean
}

export interface TaskSuggestion {
  suggestion_id: string
  title: string
  description: string
  phase_name: PhaseName
  priority: 'critical' | 'high' | 'medium' | 'low'
  estimated_hours?: number
  confidence: SuggestionConfidence
  reasoning: string
  suggested_dependencies: string[]
  constitutional_compliance: Record<string, boolean>
  metadata: Record<string, unknown>
  created_at: string
}

export interface TaskSuggestionResponse {
  request_id: string
  suggestions: TaskSuggestion[]
  generation_time_ms: number
  model_used: string
  context_summary: string
  remaining_suggestions_today: number
  created_at: string
}

export interface TaskSuggestionApproval {
  suggestion_id: string
  approved_by?: string
  modifications?: Record<string, unknown>
  approval_notes?: string
}

export interface TaskSuggestionApprovalResponse {
  task_id: string
  suggestion_id: string
  success: boolean
  message: string
  created_task?: Record<string, unknown>
}

export interface RateLimitStatus {
  user_id: string
  suggestions_used_today: number
  suggestions_remaining: number
  limit_per_period: number
  period_reset_at: string
  is_limited: boolean
}

// ============================================================================
// Error Handling
// ============================================================================

export class KanbanAIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string,
    public details?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'KanbanAIError'
  }
}

export class RateLimitError extends KanbanAIError {
  constructor(
    message: string,
    public status: RateLimitStatus
  ) {
    super(message, 429, 'RATE_LIMIT_EXCEEDED', {
      suggestions_used: status.suggestions_used_today,
      limit: status.limit_per_period,
      reset_at: status.period_reset_at,
    })
    this.name = 'RateLimitError'
  }
}

// Generic fetch wrapper with error handling
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${AI_API}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    // Handle error responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))

      // Handle rate limit specifically
      if (response.status === 429 && errorData.error?.details) {
        const status: RateLimitStatus = {
          user_id: 'current_user',
          suggestions_used_today: errorData.error.details.suggestions_used || 0,
          suggestions_remaining: 0,
          limit_per_period: errorData.error.details.limit || 10,
          period_reset_at: errorData.error.details.reset_at || '',
          is_limited: true,
        }
        throw new RateLimitError(errorData.error?.message || 'Rate limit exceeded', status)
      }

      throw new KanbanAIError(
        errorData.error?.message || `API request failed: ${response.statusText}`,
        response.status,
        errorData.error?.code,
        errorData.error?.details
      )
    }

    return response.json()
  } catch (error) {
    if (error instanceof KanbanAIError) {
      throw error
    }
    throw new KanbanAIError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Generate AI task suggestions using Claude Sonnet 4.5
 * POST /api/kanban/ai/suggest
 *
 * @param request - Task suggestion request with context and phase
 * @returns TaskSuggestionResponse with multiple suggestions
 * @throws RateLimitError if rate limit exceeded (10/hour)
 */
export async function suggestTasks(
  request: TaskSuggestionRequest
): Promise<TaskSuggestionResponse> {
  return apiFetch<TaskSuggestionResponse>('/suggest', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Approve AI suggestion and create actual task
 * POST /api/kanban/ai/approve/{suggestion_id}
 *
 * @param suggestionId - ID of the suggestion to approve
 * @param approval - Approval details with optional modifications
 * @returns TaskSuggestionApprovalResponse with created task
 */
export async function approveSuggestion(
  suggestionId: string,
  approval: TaskSuggestionApproval
): Promise<TaskSuggestionApprovalResponse> {
  return apiFetch<TaskSuggestionApprovalResponse>(`/approve/${suggestionId}`, {
    method: 'POST',
    body: JSON.stringify({
      ...approval,
      suggestion_id: suggestionId,
    }),
  })
}

/**
 * Check current rate limit status for AI suggestions
 * GET /api/kanban/ai/rate-limit
 *
 * @returns RateLimitStatus with remaining suggestions
 */
export async function getRateLimitStatus(): Promise<RateLimitStatus> {
  return apiFetch<RateLimitStatus>('/rate-limit')
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get confidence color class based on confidence level
 */
export function getConfidenceColor(confidence: SuggestionConfidence): string {
  switch (confidence) {
    case 'high':
      return 'bg-green-500/10 text-green-600 border-green-500/20'
    case 'medium':
      return 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20'
    case 'low':
      return 'bg-red-500/10 text-red-600 border-red-500/20'
    default:
      return 'bg-gray-500/10 text-gray-600 border-gray-500/20'
  }
}

/**
 * Get confidence label with percentage range
 */
export function getConfidenceLabel(confidence: SuggestionConfidence): string {
  switch (confidence) {
    case 'high':
      return 'High (>90%)'
    case 'medium':
      return 'Medium (70-90%)'
    case 'low':
      return 'Low (<70%)'
    default:
      return 'Unknown'
  }
}

/**
 * Format rate limit reset time
 */
export function formatResetTime(resetAt: string): string {
  const date = new Date(resetAt)
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffMins = Math.ceil(diffMs / 60000)

  if (diffMins <= 0) return 'now'
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''}`
  const diffHours = Math.ceil(diffMins / 60)
  return `${diffHours} hour${diffHours > 1 ? 's' : ''}`
}

// ============================================================================
// Export API client object for convenience
// ============================================================================

export const kanbanAIAPI = {
  suggestTasks,
  approveSuggestion,
  getRateLimitStatus,

  // Helpers
  getConfidenceColor,
  getConfidenceLabel,
  formatResetTime,
}

export default kanbanAIAPI
