/**
 * Kanban Store - Zustand state management for Kanban Board
 *
 * Manages tasks, columns, and drag-drop operations with optimistic updates
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { KanbanTask, TaskStatus, KanbanColumn, Phase, Priority } from '@/lib/types/kanban'

export interface KanbanFilters {
  phases: Phase[]
  statuses: TaskStatus[]
  priorities: Priority[]
}

interface KanbanState {
  // State
  tasks: KanbanTask[]
  columns: KanbanColumn[]
  filteredColumns: KanbanColumn[]
  filters: KanbanFilters
  isLoading: boolean
  error: string | null
  selectedTask: KanbanTask | null

  // Actions
  setTasks: (tasks: KanbanTask[]) => void
  addTask: (task: KanbanTask) => void
  updateTask: (id: string, updates: Partial<KanbanTask>) => void
  deleteTask: (id: string) => void
  moveTask: (taskId: string, newStatus: TaskStatus) => void
  setSelectedTask: (task: KanbanTask | null) => void

  // Filter management
  setFilters: (filters: KanbanFilters) => void
  clearFilters: () => void

  // Column management
  updateColumns: () => void

  // Loading & error
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void

  // Reset
  reset: () => void
}

const initialColumns: KanbanColumn[] = [
  { id: 'pending', title: 'To Do', tasks: [] },
  { id: 'in_progress', title: 'In Progress', tasks: [] },
  { id: 'blocked', title: 'Blocked', tasks: [] },
  { id: 'completed', title: 'Done', tasks: [] },
]

const initialFilters: KanbanFilters = {
  phases: [],
  statuses: [],
  priorities: [],
}

// Mock data for Week 6 testing (temporary)
// Using valid UUIDs for backend compatibility
const mockTasks: KanbanTask[] = [
  {
    id: '550e8400-e29b-41d4-a716-446655440001',
    title: 'Setup authentication system',
    description: 'Implement JWT-based authentication with refresh tokens',
    status: 'in_progress',
    phase: 'implementation',
    priority: 'critical',
    tags: ['backend', 'security'],
    created_at: '2025-12-01T00:00:00Z',
    updated_at: '2025-12-16T00:00:00Z',
    estimated_hours: 8,
    actual_hours: 5,
    due_date: '2025-12-20T00:00:00Z',  // Week 6 Day 4: Due date
    dependencies: ['550e8400-e29b-41d4-a716-446655440002'],  // Week 6 Day 2: Dependencies
    ai_suggested: true,  // Week 6 Day 3: AI suggested
    ai_confidence: 0.85,
    comments: [  // Week 6 Day 4: Comments
      {
        id: 'c1',
        author: 'developer',
        content: 'Started implementation, JWT library selected',
        created_at: '2025-12-16T10:00:00Z',
      },
    ],
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440002',
    title: 'Design database schema',
    description: 'Build PostgreSQL schema for user management',
    status: 'completed',
    phase: 'design',
    priority: 'high',
    tags: ['database', 'architecture'],
    created_at: '2025-11-28T00:00:00Z',
    updated_at: '2025-12-15T00:00:00Z',
    estimated_hours: 4,
    actual_hours: 3,
    due_date: '2025-12-10T00:00:00Z',  // Overdue (for testing)
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440003',
    title: 'Implement API rate limiting',
    description: 'Add rate limiting middleware to prevent abuse',
    status: 'blocked',
    phase: 'implementation',
    priority: 'medium',
    tags: ['backend', 'performance'],
    created_at: '2025-12-05T00:00:00Z',
    updated_at: '2025-12-16T00:00:00Z',
    estimated_hours: 6,
    blocked_by: ['550e8400-e29b-41d4-a716-446655440001'],  // Week 6 Day 2: Blocked by task 1
    due_date: '2025-12-18T00:00:00Z',  // Due soon (testing)
    comments: [
      {
        id: 'c2',
        author: 'tech-lead',
        content: 'Blocked until auth system is complete',
        created_at: '2025-12-16T14:00:00Z',
      },
    ],
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440004',
    title: 'Write E2E tests',
    description: 'Write Playwright tests for critical user flows',
    status: 'pending',
    phase: 'testing',
    priority: 'high',
    tags: ['testing', 'quality'],
    created_at: '2025-12-10T00:00:00Z',
    updated_at: '2025-12-16T00:00:00Z',
    estimated_hours: 10,
    due_date: '2025-12-25T00:00:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440005',
    title: 'UI polish and accessibility',
    description: 'Improve UI consistency and WCAG compliance',
    status: 'pending',
    phase: 'implementation',
    priority: 'low',
    tags: ['frontend', 'accessibility'],
    created_at: '2025-12-12T00:00:00Z',
    updated_at: '2025-12-16T00:00:00Z',
    estimated_hours: 12,
  },
]

// Export function to get mock tasks for page.tsx fallback
export const getMockTasks = () => mockTasks

const initialState = {
  tasks: mockTasks,  // Use mock tasks for testing
  columns: initialColumns,
  filteredColumns: initialColumns,
  filters: initialFilters,
  isLoading: false,
  error: null,
  selectedTask: null,
}

export const useKanbanStore = create<KanbanState>()(
  persist(
    (set, get) => ({
      // Initial state
      ...initialState,

      // Actions
      setTasks: (tasks) => {
        set({ tasks })
        get().updateColumns()
      },

      addTask: (task) => {
        set((state) => ({
          tasks: [...state.tasks, task],
        }))
        get().updateColumns()
      },

      updateTask: (id, updates) => {
        set((state) => ({
          tasks: state.tasks.map((task) =>
            task.id === id ? { ...task, ...updates } : task
          ),
        }))
        get().updateColumns()
      },

      deleteTask: (id) => {
        set((state) => ({
          tasks: state.tasks.filter((task) => task.id !== id),
          selectedTask: state.selectedTask?.id === id ? null : state.selectedTask,
        }))
        get().updateColumns()
      },

      moveTask: (taskId, newStatus) => {
        set((state) => ({
          tasks: state.tasks.map((task) =>
            task.id === taskId
              ? { ...task, status: newStatus, updated_at: new Date().toISOString() }
              : task
          ),
        }))
        get().updateColumns()
      },

      setSelectedTask: (task) => set({ selectedTask: task }),

      // Filter management
      setFilters: (filters) => set({ filters }),
      clearFilters: () => set({ filters: initialFilters }),

      // Update columns based on tasks
      updateColumns: () => {
        const { tasks } = get()
        // Ensure tasks is an array (fix undefined error)
        const safeTasks = tasks || []
        const newColumns: KanbanColumn[] = initialColumns.map((col) => ({
          ...col,
          tasks: safeTasks.filter((task) => task.status === col.id),
        }))
        set({ columns: newColumns })
      },

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error, isLoading: false }),

      clearError: () => set({ error: null }),

      reset: () => set(initialState),
    }),
    {
      name: 'kanban-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Persist tasks and selectedTask
        tasks: state.tasks,
        selectedTask: state.selectedTask,
      }),
    }
  )
)

// Selectors for optimized component re-renders
export const useTasks = () => useKanbanStore((state) => state.tasks)
export const useColumns = () => useKanbanStore((state) => state.columns)
export const useSelectedTask = () => useKanbanStore((state) => state.selectedTask)
export const useKanbanLoading = () => useKanbanStore((state) => state.isLoading)
export const useKanbanError = () => useKanbanStore((state) => state.error)
