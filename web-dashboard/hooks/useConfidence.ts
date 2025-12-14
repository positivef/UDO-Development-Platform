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

async function fetchConfidence(request: ConfidenceRequest): Promise<ConfidenceResponse> {
  const response = await apiClient.post<ConfidenceResponse>("/api/uncertainty/confidence", request)
  return response.data
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
