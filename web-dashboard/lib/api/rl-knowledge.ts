/**
 * RL Knowledge API Client
 *
 * Training-free GRPO based knowledge optimization
 * Implements ArXiv 2510.08191 concepts
 */

import { API_URL } from "../api-config";

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

export interface BestSolutionResponse {
  found: boolean;
  domain: string;
  pattern_name: string | null;
  score: number | null;
  solution: string | null;
  alternatives: Array<{ name: string; score: number }>;
}

export interface ExperimentResponse {
  problem_id: string;
  attempts: Array<{
    approach: string;
    result: string;
    metrics: Record<string, unknown>;
    notes: string | null;
    timestamp: string;
  }>;
  best_approach: string | null;
  created_at: string;
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

export interface PatternCreate {
  domain: string;
  name: string;
  resolution_time_minutes: number;
  recurrence_count?: number;
  side_effects?: number;
  solution_description: string;
  tags?: string[];
}

export interface ExperimentAttemptCreate {
  problem_id: string;
  approach: string;
  result: "success" | "partial" | "failure";
  metrics?: Record<string, unknown>;
  notes?: string;
}

// ============================================================================
// API Error
// ============================================================================

export class RLKnowledgeAPIError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: string
  ) {
    super(message);
    this.name = "RLKnowledgeAPIError";
  }
}

// ============================================================================
// API Functions
// ============================================================================

const RL_BASE = `${API_URL}/api/rl`;

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new RLKnowledgeAPIError(
      errorData.detail || `HTTP ${response.status}`,
      response.status,
      JSON.stringify(errorData)
    );
  }
  return response.json();
}

/**
 * Get Token Prior statistics
 */
export async function getTokenPriorStats(): Promise<TokenPriorStats> {
  const response = await fetch(`${RL_BASE}/token-prior/stats`);
  return handleResponse<TokenPriorStats>(response);
}

/**
 * Validate a past prediction with actual outcome
 */
export async function validateDecision(
  decisionId: string,
  actualLevel: number
): Promise<{ validated: boolean; actual_level: number; predicted_level: number }> {
  const response = await fetch(
    `${RL_BASE}/token-prior/validate/${decisionId}?actual_level=${actualLevel}`,
    { method: "POST" }
  );
  return handleResponse(response);
}

/**
 * Get patterns for a domain, ranked by score
 */
export async function getDomainPatterns(
  domain: string,
  limit = 10
): Promise<PatternResponse[]> {
  const response = await fetch(`${RL_BASE}/patterns/${domain}?limit=${limit}`);
  return handleResponse<PatternResponse[]>(response);
}

/**
 * Create a new knowledge pattern
 */
export async function createPattern(
  pattern: PatternCreate
): Promise<PatternResponse> {
  const response = await fetch(`${RL_BASE}/pattern`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pattern),
  });
  return handleResponse<PatternResponse>(response);
}

/**
 * Get best solution for a problem domain
 */
export async function getBestSolution(
  domain: string,
  keywords?: string[]
): Promise<BestSolutionResponse> {
  const params = new URLSearchParams({ domain });
  if (keywords && keywords.length > 0) {
    params.append("keywords", keywords.join(","));
  }
  const response = await fetch(`${RL_BASE}/best-solution?${params}`);
  return handleResponse<BestSolutionResponse>(response);
}

/**
 * Record an experiment attempt
 */
export async function recordExperimentAttempt(
  attempt: ExperimentAttemptCreate
): Promise<{ status: string; problem_id: string }> {
  const response = await fetch(`${RL_BASE}/experiment/attempt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(attempt),
  });
  return handleResponse(response);
}

/**
 * List all experiments
 */
export async function listExperiments(
  limit = 20
): Promise<ExperimentResponse[]> {
  const response = await fetch(`${RL_BASE}/experiments?limit=${limit}`);
  return handleResponse<ExperimentResponse[]>(response);
}

/**
 * Get a specific experiment
 */
export async function getExperiment(
  problemId: string
): Promise<ExperimentResponse> {
  const response = await fetch(`${RL_BASE}/experiment/${problemId}`);
  return handleResponse<ExperimentResponse>(response);
}

/**
 * Get complete RL system summary
 */
export async function getRLSummary(): Promise<RLSummary> {
  const response = await fetch(`${RL_BASE}/summary`);
  return handleResponse<RLSummary>(response);
}
