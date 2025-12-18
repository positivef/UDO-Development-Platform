/**
 * Project Store - Zustand state management for Multi-Project Context
 *
 * Week 6 Day 3: Multi-Project Selector
 * Q5 Decision: 1 Primary + max 3 Related projects
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
  // State (Q5: Multi-project support)
  currentProject: Project | null  // For backward compatibility
  primaryProject: Project | null  // Q5: Primary project (1)
  relatedProjects: Project[]      // Q5: Related projects (max 3)
  allProjects: Project[]          // All available projects for dropdown
  isLoading: boolean
  error: string | null

  // Actions
  setCurrentProject: (project: Project | null) => void
  setPrimaryProject: (project: Project) => void
  addRelatedProject: (project: Project) => void
  removeRelatedProject: (projectId: string) => void
  setAllProjects: (projects: Project[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void

  // Computed (Q5)
  canAddRelatedProject: () => boolean
  getCurrentProjects: () => Project[]

  // Reset
  reset: () => void
}

const initialState = {
  currentProject: null,
  primaryProject: null,
  relatedProjects: [],
  allProjects: [],
  isLoading: false,
  error: null,
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      // Initial state
      ...initialState,

      // Actions
      setCurrentProject: (project) =>
        set({ currentProject: project, error: null }),

      setPrimaryProject: (project) => {
        set({
          primaryProject: project,
          currentProject: project,  // Keep backward compatibility
          error: null,
        })
      },

      addRelatedProject: (project) => {
        const { relatedProjects, canAddRelatedProject } = get()

        // Q5: Max 3 related projects
        if (!canAddRelatedProject()) {
          console.warn('Cannot add more than 3 related projects')
          return
        }

        // Check if already added
        if (relatedProjects.find((p) => p.id === project.id)) {
          console.warn('Project already in related projects')
          return
        }

        set((state) => ({
          relatedProjects: [...state.relatedProjects, project],
        }))
      },

      removeRelatedProject: (projectId) => {
        set((state) => ({
          relatedProjects: state.relatedProjects.filter((p) => p.id !== projectId),
        }))
      },

      setAllProjects: (projects) => {
        set({ allProjects: projects })
      },

      setLoading: (loading) =>
        set({ isLoading: loading }),

      setError: (error) =>
        set({ error, isLoading: false }),

      clearError: () =>
        set({ error: null }),

      // Computed (Q5)
      canAddRelatedProject: () => {
        const { relatedProjects } = get()
        return relatedProjects.length < 3  // Q5: Max 3 related projects
      },

      getCurrentProjects: () => {
        const { primaryProject, relatedProjects } = get()
        const projects: Project[] = []
        if (primaryProject) {
          projects.push(primaryProject)
        }
        projects.push(...relatedProjects)
        return projects
      },

      reset: () =>
        set(initialState),
    }),
    {
      name: 'project-storage', // localStorage key
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Persist multi-project state (Q5)
        currentProject: state.currentProject,
        primaryProject: state.primaryProject,
        relatedProjects: state.relatedProjects,
      }),
    }
  )
)

// Selectors for optimized component re-renders
export const useCurrentProject = () => useProjectStore((state) => state.currentProject)
export const usePrimaryProject = () => useProjectStore((state) => state.primaryProject)
export const useRelatedProjects = () => useProjectStore((state) => state.relatedProjects)
export const useAllProjects = () => useProjectStore((state) => state.allProjects)
export const useProjectLoading = () => useProjectStore((state) => state.isLoading)
export const useProjectError = () => useProjectStore((state) => state.error)
export const useCanAddRelatedProject = () => useProjectStore((state) => state.canAddRelatedProject())
