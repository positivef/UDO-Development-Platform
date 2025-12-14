/**
 * useTimeTracking Hook - React Query hooks for time tracking (updated with API client)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTimeTrackingStats,
  getTasks,
  getWeeklySummary,
  getBottlenecks,
  getAIPerformance,
  getTimeSaved,
  createTask,
} from '../api/time-tracking';
import type {
  TimeTrackingStats,
  Task,
  Bottleneck,
  AIPerformanceMetric,
} from '../types/api';
import type {
  TimeMetrics,
  ROIReport,
  TrendDataPoint,
  WeeklySummary,
} from '../types/time-tracking';
import apiClient from '../api/client';
import { API_ENDPOINTS } from '../api/endpoints';

// Query keys
export const timeTrackingKeys = {
  all: ['time-tracking'] as const,
  stats: (period?: string) => [...timeTrackingKeys.all, 'stats', period] as const,
  tasks: (params?: any) => [...timeTrackingKeys.all, 'tasks', params] as const,
  weekly: (offset?: number) => [...timeTrackingKeys.all, 'weekly', offset] as const,
  bottlenecks: () => [...timeTrackingKeys.all, 'bottlenecks'] as const,
  aiPerformance: () => [...timeTrackingKeys.all, 'ai-performance'] as const,
  timeSaved: (period?: string) => [...timeTrackingKeys.all, 'time-saved', period] as const,
  // Legacy endpoints
  metrics: (period?: string) => [...timeTrackingKeys.all, 'metrics', period] as const,
  roi: (period?: string) => [...timeTrackingKeys.all, 'roi', period] as const,
  trends: (days?: number) => [...timeTrackingKeys.all, 'trends', days] as const,
};

/**
 * Hook to get time tracking statistics
 */
export function useTimeTrackingStats(period?: 'day' | 'week' | 'month') {
  return useQuery<TimeTrackingStats>({
    queryKey: timeTrackingKeys.stats(period),
    queryFn: () => getTimeTrackingStats({ period }),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 30000, // 30 seconds
  });
}

/**
 * Hook to get task list
 */
export function useTasks(params?: {
  phase?: string;
  ai_assisted?: boolean;
  limit?: number;
}) {
  return useQuery<Task[]>({
    queryKey: timeTrackingKeys.tasks(params),
    queryFn: () => getTasks(params),
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * Hook to get weekly summary
 */
/**
 * Hook to get weekly summary
 */
export function useWeeklySummary(week_offset?: number) {
  return useQuery<WeeklySummary>({
    queryKey: timeTrackingKeys.weekly(week_offset),
    queryFn: async () => {
      try {
        const response = await apiClient.get<any>(
          API_ENDPOINTS.TIME_TRACKING.WEEKLY,
          { params: { week_offset } }
        );

        const data = response.data;

        // Map backend WeeklyReport to frontend WeeklySummary
        // Backend: { week_start, week_end, roi_report, trends, recommendations }
        // Frontend: { period, highlights, top_performers, recommendations, overall_grade }

        const roi = data.roi_report || {};
        const topTimeSavers = roi.top_time_savers || [];

        // Calculate grade based on ROI
        let grade: WeeklySummary['overall_grade'] = 'C';
        const roiPercent = roi.roi_percentage || 0;
        if (roiPercent > 500) grade = 'A+';
        else if (roiPercent > 300) grade = 'A';
        else if (roiPercent > 200) grade = 'B+';
        else if (roiPercent > 100) grade = 'B';

        // Generate highlights from trends
        const highlights = [
          `ROI ${roi.roi_percentage > 0 ? 'increased' : 'decreased'} by ${Math.abs(roi.roi_percentage).toFixed(0)}%`,
          `${roi.time_saved_hours?.toFixed(1) || 0} hours saved this week`,
          `${roi.tasks_completed || 0} tasks completed successfully`
        ];

        const summaryData: WeeklySummary = {
          period: `${data.week_start} - ${data.week_end}`,
          highlights: highlights,
          top_performers: topTimeSavers.map((t: any) => ({
            task_type: t.task_type,
            time_saved: t.time_saved_hours * 60 // Convert hours to minutes for display
          })),
          recommendations: data.recommendations || [],
          overall_grade: grade
        };

        return summaryData;
      } catch (error: any) {
        if (error.useMockFallback) {
          return {
            period: 'Nov 18 - Nov 24, 2025',
            highlights: [
              'Productivity increased by 15% vs last week',
              'AI usage saved 12 hours of manual work',
              'Testing phase efficiency improved by 25%',
            ],
            top_performers: [
              { task_type: 'Error Resolution', time_saved: 480 },
              { task_type: 'Unit Testing', time_saved: 320 },
              { task_type: 'Documentation', time_saved: 180 },
            ],
            recommendations: [
              'Consider automating regression tests to reduce manual testing time',
              'Use Claude for initial documentation drafts to save ~2 hours/week',
              'Batch code review tasks to minimize context switching',
            ],
            overall_grade: 'A',
          };
        }
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30000,
  });
}

/**
 * Hook to get bottlenecks
 */
export function useBottlenecks() {
  return useQuery<Bottleneck[]>({
    queryKey: timeTrackingKeys.bottlenecks(),
    queryFn: getBottlenecks,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30000,
  });
}

/**
 * Hook to get AI performance metrics
 */
export function useAIPerformance() {
  return useQuery<AIPerformanceMetric[]>({
    queryKey: timeTrackingKeys.aiPerformance(),
    queryFn: getAIPerformance,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30000,
  });
}

/**
 * Hook to get time saved
 */
export function useTimeSaved(period?: 'day' | 'week' | 'month' | 'year') {
  return useQuery({
    queryKey: timeTrackingKeys.timeSaved(period),
    queryFn: () => getTimeSaved({ period }),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to create a new task
 */
export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      // Invalidate tasks and stats queries
      queryClient.invalidateQueries({ queryKey: timeTrackingKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: timeTrackingKeys.stats() });
    },
  });
}

// ============================================================
// Legacy Endpoints (for backward compatibility)
// ============================================================

/**
 * Hook to get time metrics (legacy endpoint)
 * NOTE: Using /roi endpoint as it contains the metrics data
 */
export function useTimeMetrics(period: string = 'week') {
  return useQuery<TimeMetrics>({
    queryKey: timeTrackingKeys.metrics(period),
    queryFn: async () => {
      try {
        // Map period to backend format (backend expects: daily|weekly|monthly|annual)
        const periodMap: Record<string, string> = {
          'day': 'daily',
          'week': 'weekly',
          'month': 'monthly',
          'year': 'annual'
        };
        const backendPeriod = periodMap[period] || 'weekly';

        const response = await apiClient.get<any>(
          `/api/time-tracking/roi?period=${backendPeriod}`
        );
        // Map ROI response to TimeMetrics format
        const data = response.data;
        return {
          period,
          date_range: {
            start: data.period_start,
            end: data.period_end,
          },
          time_saved_hours: data.time_saved_hours,
          baseline_hours: data.manual_time_hours,        // Backend field name
          actual_hours: data.actual_time_hours,          // Backend field name
          efficiency_gain_percent: data.efficiency_gain,
          tasks_completed: data.tasks_completed,
          avg_task_duration_minutes: (data.actual_time_hours * 60) / Math.max(data.tasks_completed, 1),
          tasks_by_phase: data.phase_breakdown || {},
          ai_performance: data.ai_breakdown || {},
        };
      } catch (error: any) {
        if (error.useMockFallback) {
          // Return mock data with fixed dates to prevent hydration mismatch
          return {
            period,
            date_range: {
              start: '2025-11-18T00:00:00Z',
              end: '2025-11-25T00:00:00Z',
            },
            time_saved_hours: 80,
            baseline_hours: 200,
            actual_hours: 120,
            efficiency_gain_percent: 40,
            tasks_completed: 25,
            avg_task_duration_minutes: 288,
            tasks_by_phase: {
              implementation: 10,
              testing: 8,
              design: 5,
              documentation: 2,
            },
            ai_performance: {
              'Claude Sonnet': {
                tasks: 15,
                avg_duration_minutes: 45,
                success_rate: 0.95,
              },
              Codex: {
                tasks: 8,
                avg_duration_minutes: 30,
                success_rate: 0.92,
              },
            },
          };
        }
        throw error;
      }
    },
    staleTime: 2 * 60 * 1000,
    refetchInterval: 30000,
  });
}

/**
 * Hook to get ROI report (legacy endpoint)
 */
export function useROIReport(period: string = 'week') {
  return useQuery<ROIReport>({
    queryKey: timeTrackingKeys.roi(period),
    queryFn: async () => {
      try {
        // Map period to backend format
        const periodMap: Record<string, string> = {
          'day': 'daily',
          'week': 'weekly',
          'month': 'monthly',
          'year': 'annual'
        };
        const backendPeriod = periodMap[period] || 'weekly';

        const response = await apiClient.get<ROIReport>(
          `/api/time-tracking/roi?period=${backendPeriod}`
        );
        return response.data;
      } catch (error: any) {
        if (error.useMockFallback) {
          return {
            period,
            roi_percentage: 67,
            time_saved_hours: 80,
            cost_saved_usd: 4000,
            productivity_multiplier: 1.67,
            comparison: {
              current: 67,
              previous: 55,
              change_percent: 21.8,
            },
          };
        }
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30000,
  });
}

/**
 * Hook to get trends (legacy endpoint)
 */
export function useTrends(days: number = 30) {
  return useQuery<TrendDataPoint[]>({
    queryKey: timeTrackingKeys.trends(days),
    queryFn: async () => {
      try {
        const response = await apiClient.get<TrendDataPoint[]>(
          `/api/time-tracking/trends?days=${days}`
        );
        return response.data;
      } catch (error: any) {
        if (error.useMockFallback) {
          // Generate mock trend data
          const trends: TrendDataPoint[] = [];
          for (let i = 0; i < days; i++) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            trends.push({
              date: date.toISOString().split('T')[0],
              time_saved_hours: 8 + Math.random() * 4,
              baseline_hours: 20 + Math.random() * 10,
              actual_hours: 12 + Math.random() * 5,
              tasks_completed: Math.floor(3 + Math.random() * 5),
            });
          }
          return trends.reverse();
        }
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30000,
  });
}

/**
 * Combined hook for backward compatibility (matches original useTimeTracking)
 */
export function useTimeTracking(period: string = 'week') {
  const metricsQuery = useTimeMetrics(period);
  const roiQuery = useROIReport(period);
  const bottlenecksQuery = useBottlenecks();
  const trendsQuery = useTrends(30);
  const summaryQuery = useWeeklySummary();

  return {
    metrics: metricsQuery.data,
    roi: roiQuery.data,
    bottlenecks: bottlenecksQuery.data || [],
    trends: trendsQuery.data || [],
    summary: summaryQuery.data,
    isLoading:
      metricsQuery.isLoading ||
      roiQuery.isLoading ||
      bottlenecksQuery.isLoading ||
      trendsQuery.isLoading ||
      summaryQuery.isLoading,
    isError:
      metricsQuery.isError ||
      roiQuery.isError ||
      bottlenecksQuery.isError ||
      trendsQuery.isError ||
      summaryQuery.isError,
    refetch: () => {
      metricsQuery.refetch();
      roiQuery.refetch();
      bottlenecksQuery.refetch();
      trendsQuery.refetch();
      summaryQuery.refetch();
    },
  };
}
