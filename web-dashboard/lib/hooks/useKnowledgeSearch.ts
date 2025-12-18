/**
 * useKnowledgeSearch - React Query hook for 3-tier knowledge search
 *
 * Week 6 Day 4 PM: Frontend Integration
 *
 * Features:
 * - 3-tier search with tier breakdown
 * - Search performance metrics
 * - Error handling with retry logic
 * - Loading states
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { ENDPOINTS } from '../api/endpoints';

// ============================================================================
// Types
// ============================================================================

export interface SearchResultItem {
  document_id: string;
  document_path: string;
  relevance_score: number;
  tier1_score: number;
  tier2_score: number;
  tier3_score: number;
  freshness_bonus: number;
  usefulness_score: number;
  matched_query: string;
  snippet: string;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: SearchResultItem[];
  search_time_ms: number;
  tier_breakdown: {
    tier1: number;
    tier2: number;
    tier3: number;
  };
}

export interface SearchStats {
  total_searches: number;
  avg_search_time_ms: number;
  tier1_hit_rate: number;
  tier2_hit_rate: number;
  tier3_hit_rate: number;
  avg_results_per_search: number;
}

export interface SearchParams {
  query: string;
  error_type?: string;
  max_results?: number;
  min_score?: number;
}

// ============================================================================
// API Functions
// ============================================================================

async function searchKnowledge(params: SearchParams): Promise<SearchResponse> {
  const queryParams = new URLSearchParams({
    query: params.query,
    ...(params.error_type && { error_type: params.error_type }),
    max_results: String(params.max_results || 10),
    min_score: String(params.min_score || 5.0),
  });

  const response = await fetch(
    `${ENDPOINTS.KNOWLEDGE.SEARCH}?${queryParams.toString()}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Search request failed' },
    }));
    throw new Error(error.error?.message || `HTTP ${response.status}`);
  }

  return response.json();
}

async function getSearchStats(): Promise<SearchStats> {
  const response = await fetch(ENDPOINTS.KNOWLEDGE.SEARCH_STATS, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'Failed to fetch search stats' },
    }));
    throw new Error(error.error?.message || `HTTP ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// React Query Hooks
// ============================================================================

/**
 * Hook for knowledge search with 3-tier system
 *
 * @param params - Search parameters
 * @param options - React Query options
 * @returns Query result with search results and metadata
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useKnowledgeSearch({
 *   query: "ModuleNotFoundError pandas",
 *   max_results: 5
 * }, { enabled: query.length >= 3 });
 * ```
 */
export function useKnowledgeSearch(
  params: SearchParams,
  options?: {
    enabled?: boolean;
    refetchOnWindowFocus?: boolean;
  }
): UseQueryResult<SearchResponse, Error> {
  return useQuery({
    queryKey: ['knowledge-search', params],
    queryFn: () => searchKnowledge(params),
    enabled: options?.enabled !== false && params.query.length >= 3,
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    retry: 2,
    staleTime: 5 * 60 * 1000, // 5 minutes (search results are relatively stable)
  });
}

/**
 * Hook for search performance statistics
 *
 * @returns Query result with search stats
 *
 * @example
 * ```tsx
 * const { data: stats } = useSearchStats();
 * console.log(`Average search time: ${stats?.avg_search_time_ms}ms`);
 * ```
 */
export function useSearchStats(): UseQueryResult<SearchStats, Error> {
  return useQuery({
    queryKey: ['knowledge-search-stats'],
    queryFn: getSearchStats,
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
    staleTime: 10 * 1000, // 10 seconds
  });
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get tier badge color based on tier level
 */
export function getTierBadgeColor(tier: 1 | 2 | 3): string {
  switch (tier) {
    case 1:
      return 'bg-green-100 text-green-800 border-green-300';
    case 2:
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 3:
      return 'bg-purple-100 text-purple-800 border-purple-300';
  }
}

/**
 * Get tier label
 */
export function getTierLabel(tier: 1 | 2 | 3): string {
  switch (tier) {
    case 1:
      return 'Filename';
    case 2:
      return 'Frontmatter';
    case 3:
      return 'Content';
  }
}

/**
 * Calculate which tiers contributed to a result
 */
export function getActiveTiers(result: SearchResultItem): (1 | 2 | 3)[] {
  const tiers: (1 | 2 | 3)[] = [];
  if (result.tier1_score > 0) tiers.push(1);
  if (result.tier2_score > 0) tiers.push(2);
  if (result.tier3_score > 0) tiers.push(3);
  return tiers;
}

/**
 * Format search time for display
 */
export function formatSearchTime(ms: number): string {
  if (ms < 1) return '<1ms';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

/**
 * Get relevance score color
 */
export function getRelevanceScoreColor(score: number): string {
  if (score >= 50) return 'text-green-600 font-bold';
  if (score >= 20) return 'text-blue-600 font-semibold';
  if (score >= 10) return 'text-yellow-600';
  return 'text-gray-600';
}
