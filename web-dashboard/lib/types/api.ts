/**
 * API Types - Type definitions for API requests and responses
 */

// ============================================================
// Common Types
// ============================================================

export interface APIResponse<T> {
  data: T;
  message?: string;
  timestamp?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
  code?: string;
  timestamp?: string;
}

// ============================================================
// Project Types
// ============================================================

export interface Project {
  id: string;
  name: string;
  description: string;
  current_phase: string;
  created_at: string;
  updated_at: string;
  last_active_at?: string;
  is_archived?: boolean;
  has_context?: boolean;
  context_saved_at?: string;
}

export interface ProjectContext {
  project_id: string;
  udo_state: Record<string, unknown>;
  ml_models: Record<string, unknown>;
  recent_executions: Array<Record<string, unknown>>;
  ai_preferences: Record<string, unknown>;
  editor_state: Record<string, unknown>;
  saved_at: string;
  loaded_at?: string;
}

export interface ProjectSwitchRequest {
  target_project_id: string;
  auto_save_current?: boolean;
}

export interface ProjectSwitchResponse {
  previous_project_id: string | null;
  new_project_id: string;
  project_name: string;
  context_loaded: boolean;
  context?: ProjectContext;
  message: string;
}

// ============================================================
// Quality Metrics Types
// ============================================================

export interface QualityMetrics {
  timestamp: string;
  pylint_score: number;
  eslint_score: number;
  test_coverage: number;
  code_complexity: number;
  technical_debt_hours: number;
  security_score: number;
}

export interface QualityTrends {
  period: 'day' | 'week' | 'month';
  metrics: QualityMetrics[];
}

export interface QualityAnalysis {
  overall_score: number;
  recommendations: string[];
  critical_issues: number;
  warnings: number;
  improvements: string[];
}

// ============================================================
// Time Tracking Types
// ============================================================

export interface TimeTrackingStats {
  total_time_spent: number;
  ai_time_saved: number;
  human_time: number;
  automation_rate: number;
  tasks_completed: number;
  avg_task_duration: number;
}

export interface Task {
  id: string;
  title: string;
  phase: string;
  duration: number;
  ai_assisted: boolean;
  completed_at: string;
  baseline_time?: number;
  time_saved?: number;
}

export interface WeeklySummary {
  week_start: string;
  week_end: string;
  total_tasks: number;
  time_spent: number;
  time_saved: number;
  productivity_gain: number;
}

export interface Bottleneck {
  category: string;
  count: number;
  avg_duration: number;
  impact_score: number;
  recommendations: string[];
}

export interface AIPerformanceMetric {
  ai_model: string;
  tasks_completed: number;
  avg_accuracy: number;
  time_saved: number;
  usage_rate: number;
}

// ============================================================
// C-K Theory Types
// ============================================================

export interface CKConcept {
  id: string;
  name: string;
  definition: string;
  properties: Record<string, unknown>;
  created_at: string;
}

export interface CKKnowledge {
  id: string;
  domain: string;
  facts: string[];
  rules: string[];
  validated: boolean;
}

export interface CKAnalysis {
  expansion_potential: number;
  knowledge_gaps: string[];
  innovative_concepts: string[];
  validation_status: 'pending' | 'partial' | 'complete';
}

// ============================================================
// GI Formula Types
// ============================================================

export interface GICalculation {
  novelty: number;
  usefulness: number;
  feasibility: number;
  risk: number;
  gi_score: number;
  rating: 'poor' | 'good' | 'excellent' | 'outstanding';
  timestamp: string;
}

export interface GIHistory {
  project_id: string;
  calculations: GICalculation[];
}

// ============================================================
// Version History Types
// ============================================================

export interface VersionHistory {
  id: string;
  version: string;
  commit_hash: string;
  author: string;
  message: string;
  timestamp: string;
  changes_summary: {
    files_changed: number;
    insertions: number;
    deletions: number;
  };
  metrics?: QualityMetrics;
}

export interface VersionComparison {
  from_version: string;
  to_version: string;
  metrics_delta: Partial<QualityMetrics>;
  improvements: string[];
  regressions: string[];
}

// ============================================================
// Uncertainty Types
// ============================================================

export type UncertaintyState = 'DETERMINISTIC' | 'PROBABILISTIC' | 'QUANTUM' | 'CHAOTIC' | 'VOID';

export interface UncertaintyMetric {
  timestamp: string;
  state: UncertaintyState;
  confidence: number;
  entropy: number;
  predictability: number;
}

export interface UncertaintyPrediction {
  hour: number;
  predicted_state: UncertaintyState;
  confidence: number;
  factors: string[];
}

export interface MitigationStrategy {
  strategy: string;
  effectiveness: number;
  cost: number;
  roi: number;
  recommended: boolean;
}
