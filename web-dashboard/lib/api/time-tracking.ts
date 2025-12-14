/**
 * Time Tracking API - ROI measurement and productivity tracking
 */

import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  TimeTrackingStats,
  Task,
  WeeklySummary,
  Bottleneck,
  AIPerformanceMetric,
} from '../types/api';

// Mock data for fallback
const MOCK_STATS: TimeTrackingStats = {
  total_time_spent: 120,
  ai_time_saved: 80,
  human_time: 40,
  automation_rate: 0.67,
  tasks_completed: 25,
  avg_task_duration: 4.8,
};

const MOCK_TASKS: Task[] = [
  {
    id: '1',
    title: 'Implement authentication',
    phase: 'implementation',
    duration: 45,
    ai_assisted: true,
    completed_at: new Date().toISOString(),
    baseline_time: 120,
    time_saved: 75,
  },
  {
    id: '2',
    title: 'Write unit tests',
    phase: 'testing',
    duration: 30,
    ai_assisted: true,
    completed_at: new Date().toISOString(),
    baseline_time: 60,
    time_saved: 30,
  },
];

const MOCK_WEEKLY_SUMMARY: WeeklySummary = {
  week_start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
  week_end: new Date().toISOString(),
  total_tasks: 25,
  time_spent: 120,
  time_saved: 80,
  productivity_gain: 0.67,
};

const MOCK_BOTTLENECKS: Bottleneck[] = [
  {
    category: 'Testing',
    count: 8,
    avg_duration: 45,
    impact_score: 8.5,
    recommendations: [
      'Implement automated test generation',
      'Use AI-powered test coverage analysis',
    ],
  },
  {
    category: 'Code Review',
    count: 5,
    avg_duration: 30,
    impact_score: 6.0,
    recommendations: [
      'Enable AI-assisted code review',
      'Setup automated style checking',
    ],
  },
];

const MOCK_AI_PERFORMANCE: AIPerformanceMetric[] = [
  {
    ai_model: 'Claude Sonnet 4.5',
    tasks_completed: 15,
    avg_accuracy: 0.95,
    time_saved: 60,
    usage_rate: 0.75,
  },
  {
    ai_model: 'Codex',
    tasks_completed: 8,
    avg_accuracy: 0.92,
    time_saved: 30,
    usage_rate: 0.40,
  },
];

/**
 * Get time tracking statistics
 */
export async function getTimeTrackingStats(params?: {
  period?: 'day' | 'week' | 'month';
}): Promise<TimeTrackingStats> {
  try {
    const response = await apiClient.get<TimeTrackingStats>(
      API_ENDPOINTS.TIME_TRACKING.STATS,
      { params }
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      console.warn('[Time Tracking API] Using mock data');
      return MOCK_STATS;
    }
    throw error;
  }
}

/**
 * Get task list
 */
export async function getTasks(params?: {
  phase?: string;
  ai_assisted?: boolean;
  limit?: number;
}): Promise<Task[]> {
  try {
    const response = await apiClient.get<Task[]>(
      API_ENDPOINTS.TIME_TRACKING.TASKS,
      { params }
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      return MOCK_TASKS;
    }
    throw error;
  }
}

/**
 * Get weekly summary
 */
export async function getWeeklySummary(params?: {
  week_offset?: number;
}): Promise<WeeklySummary> {
  try {
    const response = await apiClient.get<WeeklySummary>(
      API_ENDPOINTS.TIME_TRACKING.WEEKLY,
      { params }
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      return MOCK_WEEKLY_SUMMARY;
    }
    throw error;
  }
}

/**
 * Get bottlenecks analysis
 */
export async function getBottlenecks(): Promise<Bottleneck[]> {
  try {
    const response = await apiClient.get<Bottleneck[]>(
      API_ENDPOINTS.TIME_TRACKING.BOTTLENECKS
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      return MOCK_BOTTLENECKS;
    }
    throw error;
  }
}

/**
 * Get AI performance metrics
 */
export async function getAIPerformance(): Promise<AIPerformanceMetric[]> {
  try {
    const response = await apiClient.get<AIPerformanceMetric[]>(
      API_ENDPOINTS.TIME_TRACKING.AI_PERFORMANCE
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      return MOCK_AI_PERFORMANCE;
    }
    throw error;
  }
}

/**
 * Get time saved over period
 */
export async function getTimeSaved(params?: {
  period?: 'day' | 'week' | 'month' | 'year';
}): Promise<{ time_saved: number; baseline_time: number; efficiency: number }> {
  try {
    const response = await apiClient.get<{
      time_saved: number;
      baseline_time: number;
      efficiency: number;
    }>(API_ENDPOINTS.TIME_TRACKING.TIME_SAVED, { params });
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      return {
        time_saved: 80,
        baseline_time: 200,
        efficiency: 0.40,
      };
    }
    throw error;
  }
}

/**
 * Create a new task
 */
export async function createTask(task: Omit<Task, 'id' | 'completed_at'>): Promise<Task> {
  try {
    const response = await apiClient.post<Task>(
      API_ENDPOINTS.TIME_TRACKING.TASKS,
      task
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      return {
        ...task,
        id: Math.random().toString(36).substring(7),
        completed_at: new Date().toISOString(),
      };
    }
    throw error;
  }
}
