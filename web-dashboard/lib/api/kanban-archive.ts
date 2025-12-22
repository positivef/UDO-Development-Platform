/**
 * Kanban Archive API Client - Week 6 Day 5
 */
import type { Phase, Priority, TaskStatus } from '@/lib/types/kanban'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const ARCHIVE_API = `${API_BASE_URL}/api/kanban/archive`

export interface ArchivedTask {
  id: string
  title: string
  description: string
  phase: Phase
  priority: Priority
  status: TaskStatus
  tags: string[]
  estimated_hours?: number
  actual_hours?: number
  archived_at: string
  archived_by: string
  obsidian_synced: boolean
  obsidian_url?: string
}

export interface ArchiveFilter {
  phase?: Phase
  page: number
  page_size: number
}

export interface ArchiveStats {
  total_archived: number
  total_estimated_hours: number
  total_actual_hours: number
}

export interface ArchiveListResponse {
  items: ArchivedTask[]
  total: number
  page: number
  roi_statistics: ArchiveStats
}

async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${ARCHIVE_API}${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) throw new Error(`API failed: ${res.statusText}`)
  return res.json()
}

export async function fetchArchivedTasks(filters: ArchiveFilter): Promise<ArchiveListResponse> {
  const params = new URLSearchParams()
  if (filters.phase) params.append('phase', filters.phase)
  params.append('page', String(filters.page))
  params.append('per_page', String(filters.page_size))
  return apiFetch<ArchiveListResponse>(`?${params.toString()}`)
}

export async function restoreTask(taskId: string) {
  return apiFetch<{message: string}>(`/${taskId}/restore`, { method: 'POST' })
}

export async function permanentlyDeleteTask(taskId: string) {
  return apiFetch<{message: string}>(`/${taskId}`, { method: 'DELETE' })
}

export async function getArchiveStats(phase?: Phase) {
  const query = phase ? `?phase=${phase}` : ''
  return apiFetch<ArchiveStats>(`/statistics/roi${query}`)
}

export const archiveAPI = {
  fetchArchivedTasks,
  restoreTask,
  permanentlyDeleteTask,
  getArchiveStats,
}

export default archiveAPI
