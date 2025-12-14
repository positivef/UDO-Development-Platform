/**
 * Quality Metrics API - Code quality analysis and trends
 */

import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  QualityMetrics,
  QualityTrends,
  QualityAnalysis,
} from '../types/api';

// Mock data for fallback
const MOCK_QUALITY_METRICS: QualityMetrics = {
  timestamp: new Date().toISOString(),
  pylint_score: 8.5,
  eslint_score: 92,
  test_coverage: 85,
  code_complexity: 12,
  technical_debt_hours: 24,
  security_score: 90,
};

const MOCK_QUALITY_ANALYSIS: QualityAnalysis = {
  overall_score: 85,
  recommendations: [
    'Increase test coverage to 90%',
    'Reduce code complexity in auth module',
    'Fix 2 critical security issues',
  ],
  critical_issues: 2,
  warnings: 5,
  improvements: [
    'Added type hints to 15 functions',
    'Reduced cyclomatic complexity by 20%',
  ],
};

/**
 * Get current quality metrics
 */
export async function getCurrentQuality(): Promise<QualityMetrics> {
  try {
    const response = await apiClient.get<QualityMetrics>(
      API_ENDPOINTS.QUALITY.CURRENT
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      console.warn('[Quality API] Using mock data');
      return MOCK_QUALITY_METRICS;
    }
    throw error;
  }
}

/**
 * Get quality metrics history
 */
export async function getQualityHistory(params?: {
  days?: number;
  limit?: number;
}): Promise<QualityMetrics[]> {
  try {
    const response = await apiClient.get<QualityMetrics[]>(
      API_ENDPOINTS.QUALITY.HISTORY,
      { params }
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      // Generate mock history
      const history: QualityMetrics[] = [];
      const days = params?.days || 7;

      for (let i = 0; i < days; i++) {
        const date = new Date();
        date.setDate(date.getDate() - i);

        history.push({
          ...MOCK_QUALITY_METRICS,
          timestamp: date.toISOString(),
          pylint_score: 8.5 + (Math.random() - 0.5),
          eslint_score: 92 + Math.floor((Math.random() - 0.5) * 10),
          test_coverage: 85 + Math.floor((Math.random() - 0.5) * 5),
        });
      }

      return history;
    }
    throw error;
  }
}

/**
 * Get quality trends
 */
export async function getQualityTrends(
  period: 'day' | 'week' | 'month' = 'week'
): Promise<QualityTrends> {
  try {
    const response = await apiClient.get<QualityTrends>(
      API_ENDPOINTS.QUALITY.TRENDS,
      { params: { period } }
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      const history = await getQualityHistory({ days: 7 });
      return {
        period,
        metrics: history,
      };
    }
    throw error;
  }
}

/**
 * Get quality analysis
 */
export async function getQualityAnalysis(): Promise<QualityAnalysis> {
  try {
    const response = await apiClient.get<QualityAnalysis>(
      API_ENDPOINTS.QUALITY.ANALYSIS
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      return MOCK_QUALITY_ANALYSIS;
    }
    throw error;
  }
}

/**
 * Trigger quality analysis
 */
export async function triggerQualityAnalysis(options?: {
  include_security?: boolean;
  include_performance?: boolean;
}): Promise<QualityAnalysis> {
  try {
    const response = await apiClient.post<QualityAnalysis>(
      API_ENDPOINTS.QUALITY.ANALYSIS,
      options
    );
    return response.data;
  } catch (error: any) {
    if (error.useMockFallback) {
      console.warn('[Quality API] Mock analysis triggered');
      return MOCK_QUALITY_ANALYSIS;
    }
    throw error;
  }
}
