/**
 * Project Store - Zustand state management for project selection
 *
 * Manages current project state and provides actions for project switching
 * with localStorage persistence.
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export interface Project {
  id: string
  name: string
  description?: string
  has_context: boolean
  last_loaded?: string
  created_at?: string
}

interface ProjectState {
  // State
  currentProject: Project | null
  isLoading: boolean
  error: string | null

  // Actions
  setCurrentProject: (project: Project | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void

  // Reset
  reset: () => void
}

const initialState = {
  currentProject: null,
  isLoading: false,
  error: null,
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set) => ({
      // Initial state
      ...initialState,

      // Actions
      setCurrentProject: (project) =>
        set({ currentProject: project, error: null }),

      setLoading: (loading) =>
        set({ isLoading: loading }),

      setError: (error) =>
        set({ error, isLoading: false }),

      clearError: () =>
        set({ error: null }),

      reset: () =>
        set(initialState),
    }),
    {
      name: 'project-storage', // localStorage key
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Only persist currentProject
        currentProject: state.currentProject
      }),
    }
  )
)

// Selectors for optimized component re-renders
export const useCurrentProject = () => useProjectStore((state) => state.currentProject)
export const useProjectLoading = () => useProjectStore((state) => state.isLoading)
export const useProjectError = () => useProjectStore((state) => state.error)
