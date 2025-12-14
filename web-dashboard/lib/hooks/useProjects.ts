/**
 * useProjects Hook - React Query hooks for project operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listProjects,
  getProject,
  getCurrentProject,
  getProjectContext,
  switchProject,
  saveProjectContext,
} from '../api/projects';
import type {
  Project,
  ProjectContext,
  ProjectSwitchRequest,
  PaginatedResponse,
} from '../types/api';

// Query keys
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (params?: any) => [...projectKeys.lists(), params] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
  current: () => [...projectKeys.all, 'current'] as const,
  context: (id: string) => [...projectKeys.all, 'context', id] as const,
};

/**
 * Hook to list all projects
 */
export function useProjects(params?: {
  include_archived?: boolean;
  limit?: number;
  offset?: number;
}) {
  return useQuery<PaginatedResponse<Project>>({
    queryKey: projectKeys.list(params),
    queryFn: () => listProjects(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get a single project
 */
export function useProject(id: string, options?: { enabled?: boolean }) {
  return useQuery<Project>({
    queryKey: projectKeys.detail(id),
    queryFn: () => getProject(id),
    enabled: options?.enabled !== false && !!id,
  });
}

/**
 * Hook to get current active project
 */
export function useCurrentProject() {
  return useQuery<Project | null>({
    queryKey: projectKeys.current(),
    queryFn: getCurrentProject,
    staleTime: 2 * 60 * 1000, // 2 minutes (more frequent updates)
  });
}

/**
 * Hook to get project context
 */
export function useProjectContext(id: string, options?: { enabled?: boolean }) {
  return useQuery<ProjectContext | null>({
    queryKey: projectKeys.context(id),
    queryFn: () => getProjectContext(id),
    enabled: options?.enabled !== false && !!id,
  });
}

/**
 * Hook to switch projects
 */
export function useSwitchProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ProjectSwitchRequest) => switchProject(request),
    onSuccess: (data) => {
      // Invalidate current project query
      queryClient.invalidateQueries({ queryKey: projectKeys.current() });

      // Invalidate context for new project
      queryClient.invalidateQueries({
        queryKey: projectKeys.context(data.new_project_id),
      });

      // Optionally invalidate all projects list
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    },
  });
}

/**
 * Hook to save project context
 */
export function useSaveProjectContext(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (context: Partial<ProjectContext>) =>
      saveProjectContext(projectId, context),
    onSuccess: () => {
      // Invalidate context query for this project
      queryClient.invalidateQueries({
        queryKey: projectKeys.context(projectId),
      });
    },
  });
}

/**
 * Prefetch project data
 */
export function usePrefetchProject() {
  const queryClient = useQueryClient();

  return (id: string) => {
    queryClient.prefetchQuery({
      queryKey: projectKeys.detail(id),
      queryFn: () => getProject(id),
    });
  };
}
