/**
 * useRLKnowledge - React Query hooks for RL Knowledge system
 *
 * Implements Training-free GRPO frontend integration (ArXiv 2510.08191)
 *
 * Features:
 * - Token Prior statistics and validation
 * - Pattern scoring and retrieval
 * - Best solution recommendations
 * - Experiment tracking (multi-rollout)
 * - System summary dashboard
 */

import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { ENDPOINTS } from '../api/endpoints';

// ============================================================================
// Types
// ============================================================================

export interface TokenPriorStats {
  total_decisions: number;
  unique_hours: number;
  validated_count: number;
  accuracy: number | null;
  last_updated: string | null;
}

export interface PatternResponse {
  domain: string;
  name: string;
  score: number;
  resolution_time_minutes: number;
  recurrence_count: number;
  side_effects: number;
  solution_description: string;
  tags: string[];
}

export interface PatternCreate {
  domain: string;
  name: string;
  resolution_time_minutes: number;
  recurrence_count?: number;
  side_effects?: number;
  solution_description: string;
  tags?: string[];
}

export interface BestSolutionResponse {
  found: boolean;
  domain: string;
  pattern_name: string | null;
  score: number | null;
  solution: string | null;
  alternatives: Array<{ name: string; score: number }>;
}

export interface ExperimentAttempt {
  approach: string;
  result: string;
  reason?: string;
}

export interface ExperimentResponse {
  problem_id: string;
  attempts: ExperimentAttempt[];
  best_approach: string | null;
  created_at: string;
}

export interface ExperimentAttemptCreate {
  problem_id: string;
  approach: string;
  result: 'success' | 'partial' | 'failure';
  metrics?: Record<string, unknown>;
  notes?: string;
}

export interface RLSummary {
  token_prior: {
    total_decisions: number;
    validated_count: number;
    accuracy: number | null;
  };
  patterns: {
    total: number;
    by_domain: Record<string, number>;
  };
  experiments: {
    total: number;
    with_success: number;
  };
  system_status: string;
  last_updated: string;
}

// ============================================================================
// API Functions
// ============================================================================

async function fetchRLSummary(): Promise<RLSummary> {
  const response = await fetch(ENDPOINTS.RL.SUMMARY, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch RL summary' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

async function fetchTokenPriorStats(): Promise<TokenPriorStats> {
  const response = await fetch(ENDPOINTS.RL.TOKEN_PRIOR_STATS, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch stats' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

async function fetchDomainPatterns(domain: string, limit: number = 10): Promise<PatternResponse[]> {
  const url = `${ENDPOINTS.RL.PATTERNS(domain)}?limit=${limit}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch patterns' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

async function fetchBestSolution(domain: string, keywords?: string): Promise<BestSolutionResponse> {
  const params = new URLSearchParams({ domain });
  if (keywords) params.append('keywords', keywords);

  const response = await fetch(`${ENDPOINTS.RL.BEST_SOLUTION}?${params.toString()}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch solution' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

async function createPattern(pattern: PatternCreate): Promise<PatternResponse> {
  const response = await fetch(ENDPOINTS.RL.CREATE_PATTERN, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(pattern),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create pattern' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

async function recordExperimentAttempt(attempt: ExperimentAttemptCreate): Promise<{ status: string; problem_id: string }> {
  const response = await fetch(ENDPOINTS.RL.RECORD_ATTEMPT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(attempt),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to record attempt' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

async function fetchExperiments(limit: number = 20): Promise<ExperimentResponse[]> {
  const response = await fetch(`${ENDPOINTS.RL.EXPERIMENTS}?limit=${limit}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch experiments' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// React Query Hooks
// ============================================================================

/**
 * Hook for RL system summary (dashboard overview)
 */
export function useRLSummary(options?: {
  refetchInterval?: number;
}): UseQueryResult<RLSummary, Error> {
  return useQuery({
    queryKey: ['rl-summary'],
    queryFn: fetchRLSummary,
    refetchInterval: options?.refetchInterval ?? 30000, // 30 seconds
    staleTime: 10000, // 10 seconds
  });
}

/**
 * Hook for Token Prior statistics
 */
export function useTokenPriorStats(): UseQueryResult<TokenPriorStats, Error> {
  return useQuery({
    queryKey: ['rl-token-prior-stats'],
    queryFn: fetchTokenPriorStats,
    refetchInterval: 60000, // 1 minute
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook for domain patterns with Group Relative Scoring
 *
 * @param domain - Problem domain (e.g., 'websocket', 'auth', 'database')
 * @param limit - Maximum patterns to return
 */
export function useDomainPatterns(
  domain: string,
  limit: number = 10,
  options?: { enabled?: boolean }
): UseQueryResult<PatternResponse[], Error> {
  return useQuery({
    queryKey: ['rl-patterns', domain, limit],
    queryFn: () => fetchDomainPatterns(domain, limit),
    enabled: options?.enabled !== false && domain.length > 0,
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook for best solution recommendation (Policy Optimization)
 *
 * @param domain - Problem domain
 * @param keywords - Optional comma-separated keywords
 */
export function useBestSolution(
  domain: string,
  keywords?: string,
  options?: { enabled?: boolean }
): UseQueryResult<BestSolutionResponse, Error> {
  return useQuery({
    queryKey: ['rl-best-solution', domain, keywords],
    queryFn: () => fetchBestSolution(domain, keywords),
    enabled: options?.enabled !== false && domain.length > 0,
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook for listing experiments (Multi-rollout tracking)
 */
export function useExperiments(limit: number = 20): UseQueryResult<ExperimentResponse[], Error> {
  return useQuery({
    queryKey: ['rl-experiments', limit],
    queryFn: () => fetchExperiments(limit),
    refetchInterval: 60000, // 1 minute
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Mutation hook for creating a new pattern
 */
export function useCreatePattern(): UseMutationResult<PatternResponse, Error, PatternCreate> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createPattern,
    onSuccess: (data) => {
      // Invalidate patterns for this domain
      queryClient.invalidateQueries({ queryKey: ['rl-patterns', data.domain] });
      queryClient.invalidateQueries({ queryKey: ['rl-summary'] });
    },
  });
}

/**
 * Mutation hook for recording experiment attempt
 */
export function useRecordAttempt(): UseMutationResult<{ status: string; problem_id: string }, Error, ExperimentAttemptCreate> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: recordExperimentAttempt,
    onSuccess: () => {
      // Invalidate experiments list
      queryClient.invalidateQueries({ queryKey: ['rl-experiments'] });
      queryClient.invalidateQueries({ queryKey: ['rl-summary'] });
    },
  });
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get score color based on pattern score (0-1)
 */
export function getScoreColor(score: number): string {
  if (score >= 0.8) return 'text-green-600 font-bold';
  if (score >= 0.6) return 'text-blue-600 font-semibold';
  if (score >= 0.4) return 'text-yellow-600';
  return 'text-red-600';
}

/**
 * Get score badge color
 */
export function getScoreBadgeColor(score: number): string {
  if (score >= 0.8) return 'bg-green-100 text-green-800 border-green-300';
  if (score >= 0.6) return 'bg-blue-100 text-blue-800 border-blue-300';
  if (score >= 0.4) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
  return 'bg-red-100 text-red-800 border-red-300';
}

/**
 * Get side effects label
 */
export function getSideEffectsLabel(level: number): string {
  switch (level) {
    case 0:
      return 'None';
    case 1:
      return 'Minor';
    case 2:
      return 'Major';
    case 3:
      return 'Critical';
    default:
      return 'Unknown';
  }
}

/**
 * Get side effects color
 */
export function getSideEffectsColor(level: number): string {
  switch (level) {
    case 0:
      return 'text-green-600';
    case 1:
      return 'text-yellow-600';
    case 2:
      return 'text-orange-600';
    case 3:
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
}

/**
 * Get result badge color
 */
export function getResultBadgeColor(result: string): string {
  switch (result) {
    case 'success':
      return 'bg-green-100 text-green-800';
    case 'partial':
      return 'bg-yellow-100 text-yellow-800';
    case 'failure':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Format accuracy percentage
 */
export function formatAccuracy(accuracy: number | null): string {
  if (accuracy === null) return 'N/A';
  return `${(accuracy * 100).toFixed(1)}%`;
}

/**
 * Get system status color
 */
export function getSystemStatusColor(status: string): string {
  switch (status) {
    case 'operational':
      return 'bg-green-100 text-green-800';
    case 'degraded':
      return 'bg-yellow-100 text-yellow-800';
    case 'offline':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}
