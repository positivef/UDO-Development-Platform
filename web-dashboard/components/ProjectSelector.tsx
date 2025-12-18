/**
 * ProjectSelector Component - Multi-Project Switcher
 *
 * Week 6 Day 3: Multi-Project Selector
 * Q5: 1 Primary + max 3 Related projects
 *
 * Features:
 * - Dropdown with all projects
 * - Cmd+K (Ctrl+K on Windows) quick switcher
 * - Recent projects list
 * - Set primary project API integration
 */

"use client"

import { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FolderKanban, Search, Clock, Star } from 'lucide-react'
import { useProjectStore, usePrimaryProject, useAllProjects } from '@/lib/stores/project-store'
import { useRecentProjects } from '@/lib/hooks/useRecentProjects'
import type { Project } from '@/lib/stores/project-store'

// Mock API client (replace with actual API when backend is ready)
const projectAPI = {
  fetchProjects: async (): Promise<Project[]> => {
    // Mock data for Week 6 Day 3 testing
    return [
      {
        id: 'udo-platform',
        name: 'UDO Platform v3.0',
        description: 'Main development platform',
        has_context: true,
        created_at: '2025-01-01T00:00:00Z',
      },
      {
        id: 'kanban-integration',
        name: 'Kanban Integration',
        description: 'Multi-project Kanban system',
        has_context: true,
        created_at: '2025-12-01T00:00:00Z',
      },
      {
        id: 'obsidian-sync',
        name: 'Obsidian Knowledge Sync',
        description: 'Knowledge base synchronization',
        has_context: false,
        created_at: '2025-11-15T00:00:00Z',
      },
    ]
  },

  setPrimaryProject: async (projectId: string): Promise<void> => {
    // Mock API call - replace with actual backend endpoint
    // POST /api/kanban/projects/set-primary
    console.log(`Setting primary project: ${projectId}`)
    return Promise.resolve()
  },
}

export function ProjectSelector() {
  const queryClient = useQueryClient()
  const primaryProject = usePrimaryProject()
  const allProjects = useAllProjects()
  const { setPrimaryProject, setAllProjects } = useProjectStore()
  const { recentProjects, addRecentProject } = useRecentProjects()

  // Cmd+K dialog state
  const [isCommandOpen, setIsCommandOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // Fetch all projects
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectAPI.fetchProjects,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Update store when projects are fetched
  useEffect(() => {
    if (projects.length > 0) {
      setAllProjects(projects)

      // Set first project as primary if none selected
      if (!primaryProject && projects.length > 0) {
        setPrimaryProject(projects[0])
      }
    }
  }, [projects, primaryProject, setAllProjects, setPrimaryProject])

  // Set primary project mutation
  const setProjectMutation = useMutation({
    mutationFn: projectAPI.setPrimaryProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  // Handle project selection
  const handleProjectSelect = useCallback(
    (projectId: string) => {
      const project = allProjects.find((p) => p.id === projectId)
      if (!project) return

      // Update store
      setPrimaryProject(project)

      // Add to recent projects
      addRecentProject(project)

      // Call API
      setProjectMutation.mutate(projectId)

      // Close command dialog if open
      setIsCommandOpen(false)
      setSearchQuery('')
    },
    [allProjects, setPrimaryProject, addRecentProject, setProjectMutation]
  )

  // Cmd+K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K (Mac) or Ctrl+K (Windows)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsCommandOpen((prev) => !prev)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Filter projects by search query
  const filteredProjects = allProjects.filter((project) =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Filter recent projects by search query
  const filteredRecentProjects = recentProjects.filter((recent) =>
    recent.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <>
      {/* Dropdown Selector */}
      <div className="flex items-center gap-2">
        <FolderKanban className="h-5 w-5 text-muted-foreground" />
        <Select
          value={primaryProject?.id || ''}
          onValueChange={handleProjectSelect}
          disabled={isLoading}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select project..." />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>All Projects</SelectLabel>
              {allProjects.map((project) => (
                <SelectItem key={project.id} value={project.id}>
                  <div className="flex items-center justify-between gap-2 w-full">
                    <span>{project.name}</span>
                    {project.id === primaryProject?.id && (
                      <Badge variant="outline" className="text-xs">
                        Primary
                      </Badge>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>

        {/* Cmd+K hint */}
        <Button
          variant="outline"
          size="sm"
          className="hidden sm:flex items-center gap-1 text-xs"
          onClick={() => setIsCommandOpen(true)}
        >
          <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
            <span className="text-xs">⌘</span>K
          </kbd>
        </Button>
      </div>

      {/* Cmd+K Quick Switcher Dialog */}
      <Dialog open={isCommandOpen} onOpenChange={setIsCommandOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Quick Project Switcher</DialogTitle>
            <DialogDescription>
              Search and switch between projects quickly
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search projects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
                autoFocus
              />
            </div>

            {/* Recent Projects */}
            {filteredRecentProjects.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>Recent</span>
                </div>
                <div className="space-y-1">
                  {filteredRecentProjects.map((recent) => (
                    <Button
                      key={recent.id}
                      variant="ghost"
                      className="w-full justify-start"
                      onClick={() => handleProjectSelect(recent.id)}
                    >
                      <FolderKanban className="h-4 w-4 mr-2" />
                      {recent.name}
                      {recent.id === primaryProject?.id && (
                        <Badge variant="outline" className="ml-auto text-xs">
                          <Star className="h-3 w-3 mr-1" />
                          Primary
                        </Badge>
                      )}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* All Projects */}
            {filteredProjects.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2 text-sm text-muted-foreground">
                  <FolderKanban className="h-4 w-4" />
                  <span>All Projects</span>
                </div>
                <div className="space-y-1">
                  {filteredProjects.map((project) => (
                    <Button
                      key={project.id}
                      variant="ghost"
                      className="w-full justify-start"
                      onClick={() => handleProjectSelect(project.id)}
                    >
                      <FolderKanban className="h-4 w-4 mr-2" />
                      <div className="flex-1 text-left">
                        <div>{project.name}</div>
                        {project.description && (
                          <div className="text-xs text-muted-foreground">
                            {project.description}
                          </div>
                        )}
                      </div>
                      {project.id === primaryProject?.id && (
                        <Badge variant="outline" className="ml-2 text-xs">
                          <Star className="h-3 w-3 mr-1" />
                          Primary
                        </Badge>
                      )}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {/* No results */}
            {filteredProjects.length === 0 &&
              filteredRecentProjects.length === 0 && (
                <div className="text-center py-6 text-muted-foreground">
                  No projects found
                </div>
              )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
