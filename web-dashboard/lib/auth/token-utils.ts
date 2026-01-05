/**
 * Token Utilities for Authentication
 *
 * Provides utilities for managing JWT tokens across the application,
 * including WebSocket connections.
 */

// Storage key for auth token
const AUTH_TOKEN_KEY = 'auth_token';

/**
 * Get the current authentication token from localStorage
 * @returns The JWT token or null if not found
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Set the authentication token in localStorage
 * @param token - The JWT token to store
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') {
    return;
  }
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

/**
 * Remove the authentication token from localStorage
 */
export function removeAuthToken(): void {
  if (typeof window === 'undefined') {
    return;
  }
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

/**
 * Check if user is authenticated (has a valid token)
 * Note: This only checks for token existence, not validity
 * @returns True if token exists
 */
export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}

/**
 * Build a WebSocket URL with authentication token
 * @param baseUrl - The base WebSocket URL (without query params)
 * @param additionalParams - Optional additional query parameters
 * @returns WebSocket URL with token parameter if available
 */
export function buildAuthenticatedWebSocketUrl(
  baseUrl: string,
  additionalParams?: Record<string, string>
): string {
  const url = new URL(baseUrl);

  // Add auth token if available
  const token = getAuthToken();
  if (token) {
    url.searchParams.set('token', token);
  }

  // Add any additional params
  if (additionalParams) {
    Object.entries(additionalParams).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }

  return url.toString();
}

/**
 * Check if we're in development mode
 * In development, we may allow unauthenticated WebSocket connections
 */
export function isDevelopmentMode(): boolean {
  return process.env.NODE_ENV === 'development';
}

/**
 * Get WebSocket auth configuration
 * Returns token and whether to allow connection without auth
 */
export function getWebSocketAuthConfig(): {
  token: string | null;
  allowUnauthenticated: boolean;
} {
  const token = getAuthToken();
  const allowUnauthenticated = isDevelopmentMode();

  return {
    token,
    allowUnauthenticated,
  };
}
