import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import apiClient from "@/lib/api/client"

interface BayesianDetails {
  prior: number
  posterior: number
  likelihood: number
  credible_interval_lower: number
  credible_interval_upper: number
  confidence_width: number
}

interface Recommendation {
  action: string
  priority: "critical" | "high" | "medium" | "low"
  reason: string
  estimated_impact?: number
}

export interface ConfidenceResponse {
  confidence_score: number
  state: string
  decision: "GO" | "GO_WITH_CHECKPOINTS" | "NO_GO"
  risk_level: "low" | "medium" | "high" | "critical"
  monitoring_level: "standard" | "enhanced" | "intensive"
  recommendations: Recommendation[]
  metadata: BayesianDetails
  dominant_dimension?: string
}

interface ConfidenceRequest {
  phase: string
  context: {
    phase: string
    has_code: boolean
    validation_score: number
    team_size: number
    timeline_weeks: number
  }
  historical_outcomes?: boolean[]
  use_fast_mode?: boolean
}

interface BackendConfidenceResponse {
  confidence_score: number
  state: string
  decision: "GO" | "GO_WITH_CHECKPOINTS" | "NO_GO"
  metadata: {
    mode: string
    prior_mean: number
    likelihood: number
    posterior_mean: number | null
    credible_interval_lower: number
    credible_interval_upper: number
    effective_sample_size: number | null
    uncertainty_magnitude: number
    confidence_precision: number | null
    risk_level: "low" | "medium" | "high" | "critical"
    monitoring_level: "standard" | "enhanced" | "intensive"
    dominant_dimension?: string
  }
  recommendations: string[]
  timestamp: string
}

async function fetchConfidence(request: ConfidenceRequest): Promise<ConfidenceResponse> {
  const response = await apiClient.post<BackendConfidenceResponse>("/api/uncertainty/confidence", request)
  const backend = response.data

  // Map backend response to frontend expected format
  return {
    confidence_score: backend.confidence_score,
    state: backend.state,
    decision: backend.decision,
    risk_level: backend.metadata?.risk_level || "medium",
    monitoring_level: backend.metadata?.monitoring_level || "standard",
    dominant_dimension: backend.metadata?.dominant_dimension,
    recommendations: (backend.recommendations || []).map((rec, i) => ({
      action: rec,
      priority: i === 0 ? "high" : "medium" as "critical" | "high" | "medium" | "low",
      reason: "Based on Bayesian analysis"
    })),
    metadata: {
      prior: backend.metadata?.prior_mean || 0.5,
      posterior: backend.metadata?.posterior_mean || backend.confidence_score,
      likelihood: backend.metadata?.likelihood || 0.7,
      credible_interval_lower: backend.metadata?.credible_interval_lower || 0.5,
      credible_interval_upper: backend.metadata?.credible_interval_upper || 0.9,
      confidence_width: backend.metadata?.uncertainty_magnitude || 0.2
    }
  }
}

export function useConfidence(phase: string = "implementation") {
  const defaultRequest: ConfidenceRequest = {
    phase,
    context: {
      phase,
      has_code: true,
      validation_score: 0.7,
      team_size: 3,
      timeline_weeks: 8
    },
    historical_outcomes: [true, true, false, true, true],
    use_fast_mode: true
  }

  return useQuery({
    queryKey: ["confidence", phase],
    queryFn: () => fetchConfidence(defaultRequest),
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000,
  })
}

export function useConfidenceMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: fetchConfidence,
    onSuccess: (data) => {
      queryClient.setQueryData(["confidence", data.state], data)
    }
  })
}
