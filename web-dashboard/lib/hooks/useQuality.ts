/**
 * useQuality Hook - React Query hooks for quality metrics
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getCurrentQuality,
  getQualityHistory,
  getQualityTrends,
  getQualityAnalysis,
  triggerQualityAnalysis,
} from '../api/quality';
import type { QualityMetrics, QualityTrends, QualityAnalysis } from '../types/api';

// Query keys
export const qualityKeys = {
  all: ['quality'] as const,
  current: () => [...qualityKeys.all, 'current'] as const,
  history: (params?: any) => [...qualityKeys.all, 'history', params] as const,
  trends: (period: string) => [...qualityKeys.all, 'trends', period] as const,
  analysis: () => [...qualityKeys.all, 'analysis'] as const,
};

/**
 * Hook to get current quality metrics
 */
export function useCurrentQuality() {
  return useQuery<QualityMetrics>({
    queryKey: qualityKeys.current(),
    queryFn: getCurrentQuality,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook to get quality history
 */
export function useQualityHistory(params?: { days?: number; limit?: number }) {
  return useQuery<QualityMetrics[]>({
    queryKey: qualityKeys.history(params),
    queryFn: () => getQualityHistory(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get quality trends
 */
export function useQualityTrends(period: 'day' | 'week' | 'month' = 'week') {
  return useQuery<QualityTrends>({
    queryKey: qualityKeys.trends(period),
    queryFn: () => getQualityTrends(period),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get quality analysis
 */
export function useQualityAnalysis() {
  return useQuery<QualityAnalysis>({
    queryKey: qualityKeys.analysis(),
    queryFn: getQualityAnalysis,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to trigger quality analysis
 */
export function useTriggerQualityAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (options?: {
      include_security?: boolean;
      include_performance?: boolean;
    }) => triggerQualityAnalysis(options),
    onSuccess: () => {
      // Invalidate all quality queries to refetch updated data
      queryClient.invalidateQueries({ queryKey: qualityKeys.all });
    },
  });
}

/**
 * Prefetch quality data
 */
export function usePrefetchQuality() {
  const queryClient = useQueryClient();

  return {
    current: () => {
      queryClient.prefetchQuery({
        queryKey: qualityKeys.current(),
        queryFn: getCurrentQuality,
      });
    },
    history: (params?: { days?: number }) => {
      queryClient.prefetchQuery({
        queryKey: qualityKeys.history(params),
        queryFn: () => getQualityHistory(params),
      });
    },
  };
}
