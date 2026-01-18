/**
 * API Endpoints - Centralized endpoint definitions
 *
 * All API endpoints are defined here for easy maintenance and updates
 */

export const API_ENDPOINTS = {
  // Health & Status
  HEALTH: '/health',

  // Projects
  PROJECTS: {
    LIST: '/api/projects',
    DETAIL: (id: string) => `/api/projects/${id}`,
    CONTEXT: (id: string) => `/api/projects/${id}/context`,
    SWITCH: '/api/projects/switch',
    CURRENT: '/api/projects/current',
  },

  // Quality Metrics
  QUALITY: {
    CURRENT: '/api/quality/current',
    HISTORY: '/api/quality/history',
    TRENDS: '/api/quality/trends',
    ANALYSIS: '/api/quality/analysis',
  },

  // Time Tracking
  TIME_TRACKING: {
    STATS: '/api/time-tracking/stats',
    TASKS: '/api/time-tracking/tasks',
    WEEKLY: '/api/time-tracking/report/weekly',
    BOTTLENECKS: '/api/time-tracking/bottlenecks',
    AI_PERFORMANCE: '/api/time-tracking/ai-performance',
    TIME_SAVED: '/api/time-tracking/time-saved',
    ROI: '/api/time-tracking/roi',
    TRENDS: '/api/time-tracking/trends',
  },

  // C-K Theory
  CK_THEORY: {
    CONCEPTS: '/api/ck-theory/concepts',
    KNOWLEDGE: '/api/ck-theory/knowledge',
    ANALYSIS: '/api/ck-theory/analysis',
  },

  // GI Formula
  GI_FORMULA: {
    CALCULATE: '/api/gi-formula/calculate',
    HISTORY: '/api/gi-formula/history',
  },

  // Version History
  VERSION_HISTORY: {
    LIST: '/api/version-history',
    DETAIL: (id: string) => `/api/version-history/${id}`,
    COMPARE: '/api/version-history/compare',
  },

  // Uncertainty
  UNCERTAINTY: {
    STATUS: '/api/uncertainty/status',
    CURRENT: '/api/uncertainty/current',
    PREDICTIONS: '/api/uncertainty/predictions',
    MITIGATIONS: '/api/uncertainty/mitigations',
    ACK: (mitigationId: string) => `/api/uncertainty/ack/${mitigationId}`,
  },

  // Knowledge (Week 6 Day 4-5)
  KNOWLEDGE: {
    SEARCH: '/api/knowledge/search',
    SEARCH_STATS: '/api/knowledge/search/stats',
    FEEDBACK: '/api/knowledge/feedback',
    METRICS: '/api/knowledge/metrics',
    DOCUMENT_SCORE: (documentId: string) => `/api/knowledge/documents/${documentId}/score`,
    IMPROVEMENT_SUGGESTIONS: '/api/knowledge/improvement-suggestions',
  },

  // WebSocket
  WEBSOCKET: {
    URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8006/ws',
  },

  // RL Knowledge (Training-free GRPO - ArXiv 2510.08191)
  RL: {
    SUMMARY: '/api/rl/summary',
    TOKEN_PRIOR_STATS: '/api/rl/token-prior/stats',
    VALIDATE_DECISION: (decisionId: string) => `/api/rl/token-prior/validate/${decisionId}`,
    PATTERNS: (domain: string) => `/api/rl/patterns/${domain}`,
    CREATE_PATTERN: '/api/rl/pattern',
    BEST_SOLUTION: '/api/rl/best-solution',
    RECORD_ATTEMPT: '/api/rl/experiment/attempt',
    EXPERIMENTS: '/api/rl/experiments',
    EXPERIMENT: (problemId: string) => `/api/rl/experiment/${problemId}`,
  },
} as const;

// Export as both ENDPOINTS and API_ENDPOINTS for compatibility
export const ENDPOINTS = API_ENDPOINTS;
export default API_ENDPOINTS;
