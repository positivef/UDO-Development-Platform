/**
 * Uncertainty API Client - Backend integration for Uncertainty Analysis
 *
 * Connects frontend to FastAPI backend endpoints
 * Base URL: http://localhost:8000/api/uncertainty
 */

import type {
  UncertaintyStatusResponse,
  UncertaintyVector,
} from "@/types/uncertainty";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const UNCERTAINTY_API = `${API_BASE_URL}/api/uncertainty`;

// ============================================================================
// Error Handling
// ============================================================================

export class UncertaintyAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message);
    this.name = "UncertaintyAPIError";
  }
}

// Generic fetch wrapper with error handling
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${UNCERTAINTY_API}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new UncertaintyAPIError(
        errorData.detail || `API request failed: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof UncertaintyAPIError) {
      throw error;
    }
    throw new UncertaintyAPIError(
      `Network error: ${error instanceof Error ? error.message : "Unknown error"}`
    );
  }
}

// ============================================================================
// Request/Response Types
// ============================================================================

// Mitigation Acknowledgment
export interface MitigationAckRequest {
  applied_by: string;
  notes?: string;
  applied_at?: string;
}

export interface MitigationAckResponse {
  success: boolean;
  message: string;
  acknowledged_at: string;
  new_state?: string;
  new_confidence?: number;
}

// Context Analysis
export interface ContextAnalysisRequest {
  phase: "ideation" | "design" | "mvp" | "implementation" | "testing";
  has_code: boolean;
  validation_score: number; // 0.0-1.0
  team_size: number; // >=1
  timeline_weeks: number; // >=1
}

// Health Check
export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  last_update: string;
  cache_size: number;
  circuit_breaker_status: "closed" | "open" | "half_open";
}

// Time Tracking Integration
export interface UncertaintyAwareTrackingRequest {
  task_type: string;
  phase: string;
  baseline_hours: number;
  actual_hours?: number;
  context: ContextAnalysisRequest;
}

export interface UncertaintyAwareTrackingResponse {
  adjusted_baseline: number;
  uncertainty_factor: number;
  recommended_buffer: number;
  tracking_id: string;
}

export interface AdjustedBaselineResponse {
  original_baseline: number;
  adjusted_baseline: number;
  uncertainty_multiplier: number;
  recommended_buffer_hours: number;
  confidence_level: number;
}

// Bayesian Confidence
export interface BayesianConfidenceRequest {
  evidence: {
    test_passing_rate: number;
    code_coverage: number;
    review_approval_count: number;
    dependency_health_score: number;
  };
  prior_confidence?: number;
}

export interface BayesianConfidenceResponse {
  posterior_confidence: number;
  prior_confidence: number;
  likelihood_ratio: number;
  evidence_strength: "weak" | "moderate" | "strong" | "very_strong";
  breakdown: {
    test_contribution: number;
    coverage_contribution: number;
    review_contribution: number;
    dependency_contribution: number;
  };
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get current uncertainty status
 * GET /api/uncertainty/status
 */
export async function getUncertaintyStatus(): Promise<UncertaintyStatusResponse> {
  return apiFetch<UncertaintyStatusResponse>("/status");
}

/**
 * Acknowledge a mitigation strategy
 * POST /api/uncertainty/ack/{mitigation_id}
 */
export async function acknowledgeMitigation(
  mitigationId: string,
  request: MitigationAckRequest
): Promise<MitigationAckResponse> {
  return apiFetch<MitigationAckResponse>(`/ack/${mitigationId}`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Analyze custom context
 * POST /api/uncertainty/analyze
 */
export async function analyzeContext(
  context: ContextAnalysisRequest
): Promise<UncertaintyStatusResponse> {
  return apiFetch<UncertaintyStatusResponse>("/analyze", {
    method: "POST",
    body: JSON.stringify(context),
  });
}

/**
 * Get uncertainty system health
 * GET /api/uncertainty/health
 */
export async function getUncertaintyHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

/**
 * Track time with uncertainty adjustment
 * POST /api/uncertainty/track-with-uncertainty
 */
export async function trackWithUncertainty(
  request: UncertaintyAwareTrackingRequest
): Promise<UncertaintyAwareTrackingResponse> {
  return apiFetch<UncertaintyAwareTrackingResponse>(
    "/track-with-uncertainty",
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

/**
 * Get adjusted baseline for task
 * POST /api/uncertainty/adjusted-baseline/{task_type}/{phase}
 */
export async function getAdjustedBaseline(
  taskType: string,
  phase: string,
  context: ContextAnalysisRequest
): Promise<AdjustedBaselineResponse> {
  return apiFetch<AdjustedBaselineResponse>(
    `/adjusted-baseline/${taskType}/${phase}`,
    {
      method: "POST",
      body: JSON.stringify(context),
    }
  );
}

/**
 * Calculate Bayesian confidence
 * POST /api/uncertainty/confidence
 */
export async function calculateBayesianConfidence(
  request: BayesianConfidenceRequest
): Promise<BayesianConfidenceResponse> {
  return apiFetch<BayesianConfidenceResponse>("/confidence", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// ============================================================================
// Convenience Helpers
// ============================================================================

/**
 * Check if uncertainty system is healthy
 */
export async function isUncertaintyHealthy(): Promise<boolean> {
  try {
    const health = await getUncertaintyHealth();
    return health.status === "healthy";
  } catch (error) {
    console.error("Health check failed:", error);
    return false;
  }
}

/**
 * Get uncertainty state description
 */
export function getUncertaintyStateDescription(
  state: string
): { emoji: string; label: string; description: string } {
  const stateMap = {
    deterministic: {
      emoji: "🟢",
      label: "Deterministic",
      description: "Fully predictable, low risk",
    },
    probabilistic: {
      emoji: "🔵",
      label: "Probabilistic",
      description: "Statistical confidence, manageable risk",
    },
    quantum: {
      emoji: "🟠",
      label: "Quantum",
      description: "Multiple possibilities, moderate risk",
    },
    chaotic: {
      emoji: "🔴",
      label: "Chaotic",
      description: "High uncertainty, significant risk",
    },
    void: {
      emoji: "⚫",
      label: "Void",
      description: "Unknown territory, extreme risk",
    },
  };

  return (
    stateMap[state as keyof typeof stateMap] || {
      emoji: "❓",
      label: "Unknown",
      description: "State not recognized",
    }
  );
}

/**
 * Format ROI percentage
 */
export function formatROI(roi: number): string {
  return `${(roi * 100).toFixed(1)}%`;
}

/**
 * Get mitigation priority label
 */
export function getMitigationPriorityLabel(priority: number): string {
  if (priority >= 4) return "Critical";
  if (priority >= 3) return "High";
  if (priority >= 2) return "Medium";
  return "Low";
}

// ============================================================================
// Exports
// ============================================================================

export const uncertaintyAPI = {
  getStatus: getUncertaintyStatus,
  acknowledgeMitigation,
  analyzeContext,
  getHealth: getUncertaintyHealth,
  trackWithUncertainty,
  getAdjustedBaseline,
  calculateConfidence: calculateBayesianConfidence,
  isHealthy: isUncertaintyHealthy,
};

export default uncertaintyAPI;
