/**
 * Kanban Types - Type definitions for Kanban Board
 *
 * Based on KANBAN_UI_COMPONENTS_DESIGN.md specification
 */

export type Phase = 'ideation' | 'design' | 'mvp' | 'implementation' | 'testing'
export type TaskStatus = 'pending' | 'in_progress' | 'blocked' | 'completed'
export type Priority = 'low' | 'medium' | 'high' | 'critical'

export interface KanbanTask {
  id: string
  title: string
  description: string
  status: TaskStatus
  phase: Phase
  priority: Priority
  tags: string[]
  created_at: string
  updated_at: string

  // Optional fields
  assigned_to?: string
  due_date?: string
  estimated_hours?: number
  actual_hours?: number

  // Project relationships (Q5: 1 Primary + max 3 Related)
  primary_project?: string
  related_projects?: string[]

  // Dependencies (Q7: Hard Block)
  dependencies?: string[]
  blocked_by?: string[]

  // Context
  context_notes?: string
  context_file_path?: string

  // AI metadata
  ai_suggested?: boolean
  ai_confidence?: number

  // Comments (Week 6 Day 4)
  comments?: TaskComment[]
}

// Comment type for task discussions
export interface TaskComment {
  id: string
  author: string
  content: string
  created_at: string
  edited_at?: string
}

export interface KanbanColumn {
  id: TaskStatus
  title: string
  tasks: KanbanTask[]
}

export interface DragEndEvent {
  active: {
    id: string
  }
  over: {
    id: string
  } | null
}
