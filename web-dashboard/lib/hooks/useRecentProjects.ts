/**
 * useRecentProjects Hook - Manage recently accessed projects
 *
 * Week 6 Day 3: Multi-Project Selector
 * localStorage management for Cmd+K quick switcher
 */

import { useState, useEffect, useCallback } from 'react'
import type { Project } from '@/lib/stores/project-store'

const RECENT_PROJECTS_KEY = 'udo-recent-projects'
const MAX_RECENT_PROJECTS = 5

export interface RecentProject {
  id: string
  name: string
  last_accessed: string
}

export function useRecentProjects() {
  const [recentProjects, setRecentProjects] = useState<RecentProject[]>([])

  // Load recent projects from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(RECENT_PROJECTS_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as RecentProject[]
        setRecentProjects(parsed)
      }
    } catch (error) {
      console.error('Failed to load recent projects:', error)
      setRecentProjects([])
    }
  }, [])

  // Add project to recent list
  const addRecentProject = useCallback((project: Project) => {
    setRecentProjects((prev) => {
      // Remove if already exists
      const filtered = prev.filter((p) => p.id !== project.id)

      // Add to front with current timestamp
      const newRecent: RecentProject = {
        id: project.id,
        name: project.name,
        last_accessed: new Date().toISOString(),
      }

      // Keep only MAX_RECENT_PROJECTS (5)
      const updated = [newRecent, ...filtered].slice(0, MAX_RECENT_PROJECTS)

      // Save to localStorage
      try {
        localStorage.setItem(RECENT_PROJECTS_KEY, JSON.stringify(updated))
      } catch (error) {
        console.error('Failed to save recent projects:', error)
      }

      return updated
    })
  }, [])

  // Clear all recent projects
  const clearRecentProjects = useCallback(() => {
    setRecentProjects([])
    try {
      localStorage.removeItem(RECENT_PROJECTS_KEY)
    } catch (error) {
      console.error('Failed to clear recent projects:', error)
    }
  }, [])

  // Remove a specific project from recent list
  const removeRecentProject = useCallback((projectId: string) => {
    setRecentProjects((prev) => {
      const filtered = prev.filter((p) => p.id !== projectId)

      // Save to localStorage
      try {
        localStorage.setItem(RECENT_PROJECTS_KEY, JSON.stringify(filtered))
      } catch (error) {
        console.error('Failed to update recent projects:', error)
      }

      return filtered
    })
  }, [])

  return {
    recentProjects,
    addRecentProject,
    clearRecentProjects,
    removeRecentProject,
  }
}
