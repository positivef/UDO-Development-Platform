/**
 * API Client - Axios instance with interceptors and error handling
 *
 * Features:
 * - Automatic retry on network errors
 * - Mock fallback on server errors (500+)
 * - Request/response logging in development
 * - Timeout management
 */

import axios, { AxiosError, AxiosRequestConfig } from 'axios';

// Feature flag for database usage
const USE_REAL_DB = process.env.NEXT_PUBLIC_USE_DB === 'true';

// Circuit breaker state
let failureCount = 0;
const MAX_FAILURES = 3;

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor - Add auth tokens, logging
 */
apiClient.interceptors.request.use(
  (config) => {
    // Development logging
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }

    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - Error handling and mock fallback
 */
apiClient.interceptors.response.use(
  (response) => {
    // Reset failure count on success
    failureCount = 0;
    return response;
  },
  async (error: AxiosError) => {
    const config = error.config as AxiosRequestConfig;

    // Development error logging
    if (process.env.NODE_ENV === 'development') {
      console.error('[API Error]', {
        url: config?.url,
        status: error.response?.status,
        message: error.message,
      });
    }

    // Circuit breaker check
    if (error.response?.status && error.response.status >= 500) {
      failureCount++;

      if (failureCount >= MAX_FAILURES) {
        console.warn(`[Circuit Breaker] Too many failures (${failureCount}), consider switching to mock mode`);
      }
    }

    // Fallback to mock on server errors (if feature flag is off)
    if (!USE_REAL_DB && error.response?.status && error.response.status >= 500) {
      console.warn('[API] Server error detected, falling back to mock data');
      // Return mock data structure (will be handled by individual API functions)
      return Promise.reject({
        ...error,
        useMockFallback: true,
      });
    }

    // Retry logic for network errors
    if (!error.response && config && !config.headers?.['x-retry-count']) {
      console.log('[API] Network error, retrying once...');
      config.headers = {
        ...config.headers,
        'x-retry-count': '1',
      };
      return apiClient.request(config);
    }

    // Fallback to mock on network errors (no response means backend is unavailable)
    if (!USE_REAL_DB && !error.response) {
      console.warn('[API] Backend unavailable, falling back to mock data');
      return Promise.reject({
        ...error,
        useMockFallback: true,
      });
    }

    return Promise.reject(error);
  }
);

/**
 * Health check utility
 */
export async function checkAPIHealth(): Promise<boolean> {
  try {
    const response = await apiClient.get('/health');
    return response.status === 200;
  } catch (error) {
    console.error('[API Health Check] Failed', error);
    return false;
  }
}

/**
 * Get circuit breaker stats
 */
export function getCircuitBreakerStats() {
  return {
    failureCount,
    maxFailures: MAX_FAILURES,
    isOpen: failureCount >= MAX_FAILURES,
  };
}

/**
 * Reset circuit breaker
 */
export function resetCircuitBreaker() {
  failureCount = 0;
}

export default apiClient;
