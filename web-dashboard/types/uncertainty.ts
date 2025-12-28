export type UncertaintyState =
  | "deterministic"
  | "probabilistic"
  | "quantum"
  | "chaotic"
  | "void";

export interface UncertaintyVector {
  technical: number;
  market: number;
  resource: number;
  timeline: number;
  quality: number;
  magnitude: number;
  dominant_dimension: string;
}

export interface PredictiveModel {
  trend: "increasing" | "decreasing" | "stable" | "oscillating";
  velocity: number;
  acceleration: number;
  predicted_resolution: string | null;
  confidence_interval_lower: number;
  confidence_interval_upper: number;
}

export interface MitigationStrategy {
  id: string;
  uncertainty_id: string;
  action: string;
  priority: number;
  estimated_impact: number;
  estimated_cost: number;
  prerequisites: string[];
  success_probability: number;
  fallback_strategy: string | null;
  roi: number;
}

export interface UncertaintyStatusResponse {
  vector: UncertaintyVector;
  state: UncertaintyState;
  confidence_score: number;
  prediction: PredictiveModel;
  mitigations: MitigationStrategy[];
  timestamp: string;
}
