"use client"

import { useState, useEffect, useRef, memo } from "react"
import { createPortal } from "react-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  FolderGit2,
  ChevronDown,
  Check,
  Loader2,
  AlertCircle,
  Clock,
  Activity
} from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const STORAGE_KEY = "udo_current_project_id"

interface Project {
  id: string
  name: string
  description: string | null
  current_phase: string
  last_active_at: string | null
  is_archived: boolean
  has_context: boolean
}

interface ProjectsResponse {
  projects: Project[]
  total: number
  current_project_id: string | null
}

interface CurrentProjectResponse {
  project_id: string | null
  project_name: string | null
}

interface SwitchProjectRequest {
  project_id: string
  auto_save_current: boolean
}

interface SwitchProjectResponse {
  previous_project_id: string | null
  new_project_id: string
  context_loaded: boolean
  context: unknown
  message: string
}

export const ProjectSelector = memo(function ProjectSelector() {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, right: 0 })
  const [mounted, setMounted] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const queryClient = useQueryClient()

  // Client-side only rendering for Portal
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true)
  }, [])

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedProjectId(stored)
    }
  }, [])

  // Save to localStorage when selection changes
  useEffect(() => {
    if (selectedProjectId) {
      localStorage.setItem(STORAGE_KEY, selectedProjectId)
    }
  }, [selectedProjectId])

  // Update dropdown position when opening
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      setDropdownPosition({
        top: rect.bottom + window.scrollY + 8, // 8px gap
        right: window.innerWidth - rect.right + window.scrollX
      })
    }
  }, [isOpen])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          buttonRef.current && !buttonRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  // Fetch projects list
  const { data: projectsData, isLoading: projectsLoading, error: projectsError } = useQuery<ProjectsResponse>({
    queryKey: ["projects"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/projects?limit=50`)
      if (!res.ok) {
        if (res.status === 503) {
          throw new Error("Database not available - project context features disabled")
        }
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }
      return res.json()
    },
    retry: 1,
    refetchOnWindowFocus: false,
    staleTime: 60000, // 1분 동안 fresh (프로젝트 목록은 자주 안 바뀜)
    placeholderData: (previousData) => previousData,
  })

  // Fetch current project
  const { data: currentProject } = useQuery<CurrentProjectResponse>({
    queryKey: ["current-project"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/projects/current`)
      if (!res.ok) {
        if (res.status === 503) {
          return { project_id: null, project_name: null }
        }
        throw new Error(`HTTP ${res.status}`)
      }
      return res.json()
    },
    retry: 1,
    refetchOnWindowFocus: false,
    staleTime: 30000,
    placeholderData: (previousData) => previousData,
  })

  // Project switch mutation
  const switchProjectMutation = useMutation({
    mutationFn: async (request: SwitchProjectRequest) => {
      const res = await fetch(`${API_URL}/api/project-context/switch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      })

      if (!res.ok) {
        const errorText = await res.text()

        if (res.status === 503) {
          throw new Error("Database not available - project context features disabled")
        }
        if (res.status === 404) {
          throw new Error(`Endpoint not found: ${res.url}. Backend might not be running.`)
        }

        let errorDetail = errorText
        try {
          const errorJson = JSON.parse(errorText)
          errorDetail = errorJson.detail || errorText
        } catch (e) {
          // Not JSON, use text as is
        }

        throw new Error(`HTTP ${res.status}: ${errorDetail}`)
      }
      return res.json() as Promise<SwitchProjectResponse>
    },
    onSuccess: (data, variables) => {
      toast.success("Project switched successfully")
      setSelectedProjectId(variables.project_id)
      queryClient.invalidateQueries({ queryKey: ["current-project"] })
      queryClient.invalidateQueries({ queryKey: ["metrics"] })
      queryClient.invalidateQueries({ queryKey: ["system-status"] })
      setIsOpen(false)
    },
    onError: (error: Error) => {
      toast.error(`Failed to switch project: ${error.message}`)
    },
  })

  const handleProjectSelect = (projectId: string) => {
    if (projectId === selectedProjectId || projectId === currentProject?.project_id) {
      setIsOpen(false)
      return
    }

    switchProjectMutation.mutate({
      project_id: projectId,
      auto_save_current: true,
    })
  }

  // Determine current project display
  const getCurrentProjectDisplay = (): { name: string; phase: string } => {
    const currentId = selectedProjectId || currentProject?.project_id
    if (!currentId) {
      return { name: "Select Project", phase: "" }
    }

    const project = projectsData?.projects?.find((p) => p.id === currentId)
    if (project) {
      return { name: project.name, phase: project.current_phase }
    }

    return { name: currentProject?.project_name || "Select Project", phase: "" }
  }

  const displayProject = getCurrentProjectDisplay()

  // Error state
  if (projectsError) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
        <AlertCircle className="h-5 w-5 text-yellow-400" />
        <span className="text-sm text-yellow-400">Projects unavailable</span>
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Dropdown Button */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        disabled={projectsLoading || switchProjectMutation.isPending}
        className={cn(
          "flex items-center gap-2 px-4 py-2 rounded-lg transition-all",
          "bg-purple-500/10 text-purple-400 hover:bg-purple-500/20",
          "border border-purple-500/20",
          (projectsLoading || switchProjectMutation.isPending) && "opacity-50 cursor-not-allowed"
        )}
      >
        {switchProjectMutation.isPending ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <FolderGit2 className="h-5 w-5" />
        )}
        <div className="flex flex-col items-start min-w-[120px]">
          <span className="text-sm font-medium">
            {displayProject.name}
          </span>
          {displayProject.phase && (
            <span className="text-xs text-purple-300/70">
              {displayProject.phase}
            </span>
          )}
        </div>
        <ChevronDown
          className={cn(
            "h-4 w-4 transition-transform",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {/*
        Portal을 사용하는 이유:
        1. backdrop-blur-lg가 새로운 stacking context 생성
        2. z-index만으로는 해결 불가 (부모 context에 갇힘)
        3. document.body에 렌더링하여 stacking context 우회

        참고: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_positioned_layout/Understanding_z-index/Stacking_context
      */}
      {/* Dropdown Menu - Rendered via Portal */}
      {mounted && createPortal(
        <AnimatePresence>
          {isOpen && (
            <motion.div
              ref={dropdownRef}
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              style={{
                position: 'fixed',
                top: `${dropdownPosition.top}px`,
                right: `${dropdownPosition.right}px`,
                zIndex: 99999,
              }}
              className="w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-xl overflow-hidden"
            >
            {/* Dropdown Header */}
            <div className="p-3 border-b border-gray-700">
              <h3 className="text-sm font-semibold text-white">Select Project</h3>
              <p className="text-xs text-gray-400 mt-1">
                {projectsData?.total || 0} projects available
              </p>
            </div>

            {/* Project List */}
            <div className="max-h-96 overflow-y-auto">
              {projectsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 text-purple-400 animate-spin" />
                </div>
              ) : projectsData?.projects && projectsData.projects.length > 0 ? (
                <div className="py-2">
                  {projectsData.projects.map((project) => {
                    const isActive =
                      project.id === selectedProjectId ||
                      project.id === currentProject?.project_id

                    return (
                      <button
                        key={project.id}
                        onClick={() => handleProjectSelect(project.id)}
                        disabled={switchProjectMutation.isPending}
                        className={cn(
                          "w-full px-4 py-3 flex items-start gap-3 hover:bg-gray-700/50 transition-colors",
                          isActive && "bg-purple-500/10",
                          switchProjectMutation.isPending && "opacity-50 cursor-not-allowed"
                        )}
                      >
                        {/* Check Icon */}
                        <div className="flex-shrink-0 mt-0.5">
                          {isActive ? (
                            <Check className="h-5 w-5 text-purple-400" />
                          ) : (
                            <div className="h-5 w-5" />
                          )}
                        </div>

                        {/* Project Info */}
                        <div className="flex-1 text-left">
                          <div className="flex items-center gap-2">
                            <span
                              className={cn(
                                "text-sm font-medium",
                                isActive ? "text-purple-400" : "text-white"
                              )}
                            >
                              {project.name}
                            </span>
                            {project.has_context && (
                              <span className="px-1.5 py-0.5 text-xs bg-green-500/20 text-green-400 rounded">
                                Saved
                              </span>
                            )}
                          </div>
                          {project.description && (
                            <p className="text-xs text-gray-400 mt-1 line-clamp-1">
                              {project.description}
                            </p>
                          )}
                          <div className="flex items-center gap-3 mt-1.5">
                            <span className="text-xs text-gray-500 flex items-center gap-1">
                              <Activity className="h-3 w-3" />
                              {project.current_phase}
                            </span>
                            {project.last_active_at && (
                              <span className="text-xs text-gray-500 flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {new Date(project.last_active_at).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                      </button>
                    )
                  })}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <p className="text-sm text-gray-400">No projects found</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>,
      document.body
    )}
    </div>
  )
})
