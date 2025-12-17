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

const initialState = {
  tasks: [],
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
        const newColumns: KanbanColumn[] = initialColumns.map((col) => ({
          ...col,
          tasks: tasks.filter((task) => task.status === col.id),
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
