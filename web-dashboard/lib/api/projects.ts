/**
 * Projects API - Project management and context operations
 */

import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  Project,
  ProjectContext,
  ProjectSwitchRequest,
  ProjectSwitchResponse,
  PaginatedResponse,
} from '../types/api';

// Mock data for fallback
const MOCK_PROJECTS: Project[] = [
  {
    id: '1',
    name: 'UDO-Development-Platform',
    description: 'Unified Development Orchestrator Platform',
    current_phase: 'implementation',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    last_active_at: new Date().toISOString(),
    is_archived: false,
    has_context: true,
    context_saved_at: new Date().toISOString(),
  },
];

/**
 * List all projects
 */
export async function listProjects(params?: {
  include_archived?: boolean;
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<Project>> {
  try {
    const response = await apiClient.get<PaginatedResponse<Project>>(
      API_ENDPOINTS.PROJECTS.LIST,
      { params }
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      console.warn('[Projects API] Using mock data');
      return {
        items: MOCK_PROJECTS,
        total: MOCK_PROJECTS.length,
        page: 1,
        pageSize: 50,
        hasNext: false,
      };
    }
    throw error;
  }
}

/**
 * Get project by ID
 */
export async function getProject(id: string): Promise<Project> {
  try {
    const response = await apiClient.get<Project>(
      API_ENDPOINTS.PROJECTS.DETAIL(id)
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      const project = MOCK_PROJECTS.find((p) => p.id === id);
      if (project) return project;
    }
    throw error;
  }
}

/**
 * Get current active project
 */
export async function getCurrentProject(): Promise<Project | null> {
  try {
    const response = await apiClient.get<Project | null>(
      API_ENDPOINTS.PROJECTS.CURRENT
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      return MOCK_PROJECTS[0];
    }
    throw error;
  }
}

/**
 * Get project context
 */
export async function getProjectContext(id: string): Promise<ProjectContext | null> {
  try {
    const response = await apiClient.get<ProjectContext>(
      API_ENDPOINTS.PROJECTS.CONTEXT(id)
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      return {
        project_id: id,
        udo_state: { phase: 'implementation', confidence: 0.85 },
        ml_models: {},
        recent_executions: [],
        ai_preferences: {},
        editor_state: {},
        saved_at: new Date().toISOString(),
      };
    }
    throw error;
  }
}

/**
 * Switch to another project
 */
export async function switchProject(
  request: ProjectSwitchRequest
): Promise<ProjectSwitchResponse> {
  try {
    const response = await apiClient.post<ProjectSwitchResponse>(
      API_ENDPOINTS.PROJECTS.SWITCH,
      request
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      const targetProject = MOCK_PROJECTS.find(
        (p) => p.id === request.target_project_id
      );
      return {
        previous_project_id: '1',
        new_project_id: request.target_project_id,
        project_name: targetProject?.name || 'Unknown',
        context_loaded: true,
        message: 'Switched to mock project',
      };
    }
    throw error;
  }
}

/**
 * Save project context
 */
export async function saveProjectContext(
  id: string,
  context: Partial<ProjectContext>
): Promise<ProjectContext> {
  try {
    const response = await apiClient.post<ProjectContext>(
      API_ENDPOINTS.PROJECTS.CONTEXT(id),
      context
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      return {
        project_id: id,
        udo_state: context.udo_state || {},
        ml_models: context.ml_models || {},
        recent_executions: context.recent_executions || [],
        ai_preferences: context.ai_preferences || {},
        editor_state: context.editor_state || {},
        saved_at: new Date().toISOString(),
      };
    }
    throw error;
  }
}
