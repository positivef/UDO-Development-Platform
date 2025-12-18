/**
 * Kanban Task Dependencies - TypeScript Types
 *
 * Aligned with backend models (backend/app/models/kanban_dependencies.py)
 */

export enum DependencyType {
  FINISH_TO_START = "FS",  // Task B starts after Task A finishes [default]
  START_TO_START = "SS",   // Task B starts when Task A starts
  FINISH_TO_FINISH = "FF", // Task B finishes when Task A finishes
  START_TO_FINISH = "SF",  // Task B finishes when Task A starts [rare]
}

export enum DependencyStatus {
  PENDING = "pending",       // Dependency active
  COMPLETED = "completed",   // Predecessor completed
  OVERRIDDEN = "overridden", // Emergency override (Q7)
}

export interface DependencyBase {
  task_id: string;          // Dependent task (successor)
  depends_on_task_id: string; // Predecessor task
  dependency_type: DependencyType;
  status: DependencyStatus;
}

export interface DependencyCreate extends DependencyBase {}

export interface Dependency extends DependencyBase {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface EmergencyOverride {
  dependency_id: string;
  reason: string; // min 10 chars
  overridden_by: string;
}

export interface DependencyAudit {
  id: string;
  dependency_id: string;
  task_id: string;
  depends_on_task_id: string;
  reason: string;
  overridden_by: string;
  overridden_at: string;
}

export interface TopologicalSortResult {
  ordered_tasks: string[];
  execution_time_ms: number;
  task_count: number;
  dependency_count: number;
}

/**
 * Node in dependency graph (for D3.js visualization)
 * Enhanced with task metadata for rich visualization
 */
export interface DependencyGraphNode {
  id: string;
  task_id: string;
  label: string;        // Task title
  type: string;         // "task", "milestone", etc.

  // Task metadata for D3.js visualization
  title?: string;       // Full task title
  phase?: string;       // ideation, design, mvp, implementation, testing
  status: string;       // pending, in_progress, blocked, completed, done_end
  priority?: string;    // critical, high, medium, low
  completeness: number; // Completion percentage (0-100)
  is_blocked: boolean;  // Whether task is blocked by dependencies
}

/**
 * Edge in dependency graph
 */
export interface DependencyGraphEdge {
  source: string;
  target: string;
  dependency_type: DependencyType;
  status: DependencyStatus;
}

/**
 * Complete dependency graph (for D3.js force-directed layout)
 */
export interface DependencyGraph {
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
  has_cycles: boolean;
  cycles: string[][];
}

/**
 * DAG performance statistics
 */
export interface DAGStatistics {
  total_tasks: number;
  total_dependencies: number;
  max_depth: number;                    // Longest dependency chain
  avg_dependencies_per_task: number;
  topological_sort_time_ms: number;
  cycle_detection_time_ms: number;
  meets_performance_target: boolean;    // <50ms for 1,000 tasks
}

/**
 * D3.js specific types for force-directed graph
 */
export interface D3Node extends DependencyGraphNode {
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface D3Link {
  source: string | D3Node;
  target: string | D3Node;
  dependency_type: DependencyType;
  status: DependencyStatus;
}
