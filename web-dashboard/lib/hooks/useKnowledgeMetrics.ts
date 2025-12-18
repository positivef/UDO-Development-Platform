/**
 * useKnowledgeMetrics - React Query hook for knowledge reuse metrics
 *
 * Week 6 Day 5: Metrics Dashboard
 *
 * Features:
 * - Overall accuracy metrics
 * - Top/low quality documents
 * - Improvement recommendations
 * - Real-time metrics refresh
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { ENDPOINTS } from '../api/endpoints';

// ============================================================================
// Types
// ============================================================================

export interface DocumentScore {
  document_id: string;
  usefulness_score: number;
  total_searches: number;
  helpful_count: number;
  unhelpful_count: number;
  acceptance_rate: number;
  last_updated: string;
}

export interface KnowledgeMetrics {
  search_accuracy: number;
  acceptance_rate: number;
  false_positive_rate: number;
  total_searches: number;
  total_feedback_count: number;
  avg_resolution_time_minutes?: number;
  top_documents: DocumentScore[];
  low_quality_documents: string[];
  period_start: string;
  period_end: string;
}

export interface ImprovementSuggestion {
  type: 'low_quality' | 'high_false_positive';
  document_id?: string;
  score?: number;
  false_positive_rate?: number;
  recommendation: string;
  priority: 'high' | 'medium' | 'low';
}

// ============================================================================
// API Functions
// ============================================================================

async function getKnowledgeMetrics(): Promise<KnowledgeMetrics> {
  const response = await fetch(ENDPOINTS.KNOWLEDGE.METRICS, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Failed to fetch metrics' },
    }));
    throw new Error(error.error?.message || `HTTP ${response.status}`);
  }

  return response.json();
}

async function getImprovementSuggestions(): Promise<ImprovementSuggestion[]> {
  const response = await fetch(ENDPOINTS.KNOWLEDGE.IMPROVEMENT_SUGGESTIONS, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Failed to fetch suggestions' },
    }));
    throw new Error(error.error?.message || `HTTP ${response.status}`);
  }

  return response.json();
}

async function getDocumentScore(documentId: string): Promise<DocumentScore> {
  const response = await fetch(ENDPOINTS.KNOWLEDGE.DOCUMENT_SCORE(documentId), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Document not found' },
    }));
    throw new Error(error.error?.message || `HTTP ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// React Query Hooks
// ============================================================================

/**
 * Hook for overall knowledge reuse metrics
 *
 * @param options - React Query options
 * @returns Query result with metrics
 *
 * @example
 * ```tsx
 * const { data: metrics } = useKnowledgeMetrics({
 *   refetchInterval: 30000 // Refresh every 30s
 * });
 * ```
 */
export function useKnowledgeMetrics(options?: {
  refetchInterval?: number;
  enabled?: boolean;
}): UseQueryResult<KnowledgeMetrics, Error> {
  return useQuery({
    queryKey: ['knowledge-metrics'],
    queryFn: getKnowledgeMetrics,
    refetchInterval: options?.refetchInterval ?? 30000, // Default: 30s
    enabled: options?.enabled ?? true,
    staleTime: 10 * 1000, // 10 seconds
  });
}

/**
 * Hook for improvement suggestions
 *
 * @returns Query result with suggestions
 *
 * @example
 * ```tsx
 * const { data: suggestions } = useImprovementSuggestions();
 * ```
 */
export function useImprovementSuggestions(): UseQueryResult<
  ImprovementSuggestion[],
  Error
> {
  return useQuery({
    queryKey: ['knowledge-improvement-suggestions'],
    queryFn: getImprovementSuggestions,
    refetchInterval: 60 * 1000, // Refresh every minute
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook for specific document score
 *
 * @param documentId - Document identifier
 * @returns Query result with document score
 *
 * @example
 * ```tsx
 * const { data: score } = useDocumentScore('Debug-Auth-401.md');
 * ```
 */
export function useDocumentScore(
  documentId: string
): UseQueryResult<DocumentScore, Error> {
  return useQuery({
    queryKey: ['knowledge-document-score', documentId],
    queryFn: () => getDocumentScore(documentId),
    enabled: !!documentId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get metric status color based on value
 */
export function getMetricStatusColor(
  metricType: 'accuracy' | 'acceptance' | 'false_positive',
  value: number
): string {
  switch (metricType) {
    case 'accuracy':
      // Target: 70%+
      if (value >= 70) return 'text-green-600';
      if (value >= 50) return 'text-yellow-600';
      return 'text-red-600';

    case 'acceptance':
      // Target: 40%+ (benchmarked against GitHub Copilot 26-40%)
      if (value >= 40) return 'text-green-600';
      if (value >= 25) return 'text-yellow-600';
      return 'text-red-600';

    case 'false_positive':
      // Target: <15%
      if (value < 10) return 'text-green-600';
      if (value < 20) return 'text-yellow-600';
      return 'text-red-600';
  }
}

/**
 * Get metric status badge
 */
export function getMetricStatusBadge(
  metricType: 'accuracy' | 'acceptance' | 'false_positive',
  value: number
): { label: string; color: string } {
  switch (metricType) {
    case 'accuracy':
      if (value >= 70)
        return { label: 'Excellent', color: 'bg-green-100 text-green-800' };
      if (value >= 50)
        return { label: 'Good', color: 'bg-yellow-100 text-yellow-800' };
      return { label: 'Needs Improvement', color: 'bg-red-100 text-red-800' };

    case 'acceptance':
      if (value >= 40)
        return { label: 'Excellent', color: 'bg-green-100 text-green-800' };
      if (value >= 25)
        return { label: 'Good', color: 'bg-yellow-100 text-yellow-800' };
      return { label: 'Needs Improvement', color: 'bg-red-100 text-red-800' };

    case 'false_positive':
      if (value < 10)
        return { label: 'Excellent', color: 'bg-green-100 text-green-800' };
      if (value < 20)
        return { label: 'Acceptable', color: 'bg-yellow-100 text-yellow-800' };
      return { label: 'High', color: 'bg-red-100 text-red-800' };
  }
}

/**
 * Get priority badge color
 */
export function getPriorityBadgeColor(
  priority: 'high' | 'medium' | 'low'
): string {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'low':
      return 'bg-blue-100 text-blue-800 border-blue-300';
  }
}

/**
 * Format document ID for display
 */
export function formatDocumentId(documentId: string): string {
  // Remove file extension
  const withoutExt = documentId.replace(/\.md$/, '');

  // Truncate if too long
  if (withoutExt.length > 50) {
    return withoutExt.substring(0, 47) + '...';
  }

  return withoutExt;
}
