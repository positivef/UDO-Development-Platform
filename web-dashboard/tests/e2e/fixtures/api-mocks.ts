/**
 * API Mock Fixtures for E2E Tests
 *
 * Provides mock data for backend API endpoints during E2E testing.
 * Uses Playwright route interception to avoid dependency on running backend.
 */

import { Page, Route } from '@playwright/test';

// ===== MOCK DATA =====

export const mockUncertaintyStatus = {
  state: 'probabilistic',
  confidence_score: 0.72,
  timestamp: '2025-12-30T10:00:00Z',
  vector: {
    technical: 0.30,
    market: 0.40,
    resource: 0.20,
    timeline: 0.50,
    quality: 0.35,
    dominant_dimension: 'timeline',
    magnitude: 0.45,
  },
  prediction: {
    trend: 'increasing',
    velocity: 0.02,
    acceleration: 0.001,
    predicted_resolution: '2025-01-15T10:00:00Z',
    confidence_24h: [
      { hour: 0, confidence: 0.72, upper: 0.78, lower: 0.66 },
      { hour: 4, confidence: 0.73, upper: 0.79, lower: 0.67 },
      { hour: 8, confidence: 0.75, upper: 0.81, lower: 0.69 },
      { hour: 12, confidence: 0.76, upper: 0.82, lower: 0.70 },
      { hour: 16, confidence: 0.77, upper: 0.83, lower: 0.71 },
      { hour: 20, confidence: 0.78, upper: 0.84, lower: 0.72 },
      { hour: 24, confidence: 0.79, upper: 0.85, lower: 0.73 },
    ],
  },
  mitigations: [
    {
      id: 'mit-001',
      action: 'Add comprehensive test coverage for critical paths',
      priority: 1,
      estimated_impact: 0.15,
      roi: 0.85,
      success_probability: 0.9,
      acknowledged: false,
    },
    {
      id: 'mit-002',
      action: 'Review and optimize CI/CD pipeline',
      priority: 2,
      estimated_impact: 0.10,
      roi: 0.7,
      success_probability: 0.85,
      acknowledged: false,
    },
    {
      id: 'mit-003',
      action: 'Document architecture decisions',
      priority: 3,
      estimated_impact: 0.08,
      roi: 0.6,
      success_probability: 0.95,
      acknowledged: true,
    },
  ],
};

export const mockConfidenceResponse = {
  confidence_score: 0.75,
  state: 'implementation',
  decision: 'GO_WITH_CHECKPOINTS',
  metadata: {
    mode: 'bayesian',
    prior_mean: 0.5,
    likelihood: 0.8,
    posterior_mean: 0.75,
    credible_interval_lower: 0.65,
    credible_interval_upper: 0.85,
    effective_sample_size: 100,
    uncertainty_magnitude: 0.2,
    confidence_precision: 0.95,
    risk_level: 'medium',
    monitoring_level: 'enhanced',
    dominant_dimension: 'technical',
  },
  recommendations: [
    'Add unit tests for new features',
    'Review code coverage metrics',
    'Document API changes',
    'Perform security audit',
  ],
  timestamp: '2025-12-30T10:00:00Z',
  evidence_breakdown: {
    test_contribution: 0.26,
    coverage_contribution: 0.19,
    review_contribution: 0.17,
    dependency_contribution: 0.13,
  },
  evidence_strength: 'strong',
};

// ===== ROUTE HANDLERS =====

/**
 * Handle uncertainty status requests
 */
function handleUncertaintyStatus(route: Route) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(mockUncertaintyStatus),
  });
}

/**
 * Handle confidence calculation requests
 */
function handleConfidence(route: Route) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(mockConfidenceResponse),
  });
}

/**
 * Handle mitigation acknowledgment requests
 */
function handleMitigationAck(route: Route) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, acknowledged: true }),
  });
}

/**
 * Handle health check requests
 */
function handleHealthCheck(route: Route) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ status: 'healthy', timestamp: new Date().toISOString() }),
  });
}

// ===== SETUP FUNCTIONS =====

/**
 * Setup all API mocks for a page
 * Call this in beforeEach to intercept all backend requests
 */
export async function setupAPIMocks(page: Page) {
  // Mock uncertainty status
  await page.route('**/api/uncertainty/status', handleUncertaintyStatus);

  // Mock confidence endpoint
  await page.route('**/api/uncertainty/confidence', handleConfidence);

  // Mock mitigation acknowledgment
  await page.route('**/api/uncertainty/mitigations/*/acknowledge', handleMitigationAck);

  // Mock health check
  await page.route('**/health', handleHealthCheck);

  // Log that mocks are active
  console.log('[API Mocks] Backend API mocks are active');
}

/**
 * Setup only uncertainty-related mocks
 */
export async function setupUncertaintyMocks(page: Page) {
  await page.route('**/api/uncertainty/status', handleUncertaintyStatus);
  await page.route('**/api/uncertainty/mitigations/*/acknowledge', handleMitigationAck);
  await page.route('**/health', handleHealthCheck);
}

/**
 * Setup only confidence-related mocks
 */
export async function setupConfidenceMocks(page: Page) {
  await page.route('**/api/uncertainty/confidence', handleConfidence);
  await page.route('**/health', handleHealthCheck);
}

/**
 * Clear all route handlers
 */
export async function clearAPIMocks(page: Page) {
  await page.unrouteAll();
}

// ===== CUSTOM MOCK OVERRIDES =====

/**
 * Override uncertainty status with custom data
 */
export async function mockUncertaintyWithState(page: Page, state: string, confidence: number) {
  const customData = {
    ...mockUncertaintyStatus,
    state,
    confidence_score: confidence,
  };

  await page.route('**/api/uncertainty/status', (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(customData),
    });
  });
}

/**
 * Override confidence with custom decision
 */
export async function mockConfidenceWithDecision(
  page: Page,
  decision: 'GO' | 'GO_WITH_CHECKPOINTS' | 'NO_GO',
  score: number
) {
  const customData = {
    ...mockConfidenceResponse,
    confidence_score: score,
    decision,
  };

  await page.route('**/api/uncertainty/confidence', (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(customData),
    });
  });
}

/**
 * Simulate API error for testing error states
 */
export async function mockAPIError(page: Page, endpoint: string, statusCode: number = 500) {
  await page.route(`**${endpoint}`, (route) => {
    return route.fulfill({
      status: statusCode,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Mock error for testing', statusCode }),
    });
  });
}
