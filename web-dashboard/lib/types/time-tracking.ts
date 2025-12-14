export interface TimeMetrics {
  period: string
  date_range: {
    start: string
    end: string
  }
  time_saved_hours: number
  baseline_hours: number
  actual_hours: number
  efficiency_gain_percent: number
  tasks_completed: number
  avg_task_duration_minutes: number
  tasks_by_phase: {
    [phase: string]: number
  }
  ai_performance: {
    [service: string]: {
      tasks: number
      avg_duration_minutes: number
      success_rate: number
    }
  }
}

export interface ROIReport {
  period: string
  roi_percentage: number
  time_saved_hours: number
  cost_saved_usd: number
  productivity_multiplier: number
  comparison: {
    current: number
    previous: number
    change_percent: number
  }
}

export interface Bottleneck {
  task_type: string
  avg_duration: number
  baseline: number
  overrun: number
  severity: "low" | "medium" | "high" | "critical"
  count: number
  recent_tasks: string[]
}

export interface TrendDataPoint {
  date: string
  time_saved_hours: number
  baseline_hours: number
  actual_hours: number
  tasks_completed: number
}

export interface WeeklySummary {
  period: string
  highlights: string[]
  top_performers: {
    task_type: string
    time_saved: number
  }[]
  recommendations: string[]
  overall_grade: "A+" | "A" | "B+" | "B" | "C" | "F"
}

export interface TaskDetail {
  id: string
  task_type: string
  phase: string
  duration_minutes: number
  baseline_minutes: number
  ai_service: string
  completed_at: string
  success: boolean
}
