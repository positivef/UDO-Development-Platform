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

  // WebSocket
  WEBSOCKET: {
    URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
  },
} as const;

export default API_ENDPOINTS;
