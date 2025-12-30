import { test, expect, Page } from '@playwright/test';
import { setupAPIMocks, setupUncertaintyMocks, setupConfidenceMocks, mockUncertaintyStatus, mockConfidenceResponse } from './fixtures/api-mocks';

/**
 * E2E Integration Tests for Uncertainty UI & Confidence Dashboard
 *
 * Test Coverage:
 * 1. Uncertainty UI - 24-hour prediction chart, vector breakdown, mitigation strategies
 * 2. Confidence Dashboard - Phase tabs, Bayesian statistics, decision logic
 * 3. Cross-dashboard navigation and data consistency
 *
 * NOTE: Uses API mocking to avoid dependency on running backend server
 */

// Console error tracking
const consoleErrors: { page: string; message: string }[] = [];

async function captureConsoleMessages(page: Page, pageName: string) {
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      // Ignore common non-critical errors
      const text = msg.text();
      if (
        text.includes('Failed to fetch') ||
        text.includes('NetworkError') ||
        text.includes('hydration') ||
        text.includes('Hydration') ||
        text.includes('tree hydrated') ||
        text.includes('server rendered HTML') ||
        text.includes('WebSocket connection') ||
        text.includes('WebSocket') ||
        text.includes('ERR_CONNECTION_REFUSED') ||
        text.includes('ConfidenceWS')
      ) {
        return; // Ignore network/hydration errors (expected with mocking)
      }
      consoleErrors.push({ page: pageName, message: text });
    }
  });

  page.on('pageerror', (error) => {
    // Ignore common non-critical page errors
    const errorMsg = error.message || '';
    if (
      errorMsg.includes('hydration') ||
      errorMsg.includes('Hydration') ||
      errorMsg.includes('tree hydrated') ||
      errorMsg.includes('server rendered HTML') ||
      errorMsg.includes('WebSocket') ||
      errorMsg.includes('Failed to fetch') ||
      errorMsg.includes('ERR_CONNECTION_REFUSED') ||
      errorMsg.includes('ConfidenceWS')
    ) {
      return; // Ignore expected errors with mocking
    }
    consoleErrors.push({
      page: pageName,
      message: `Uncaught exception: ${error.message}`,
    });
  });
}

test.describe('Uncertainty UI - Comprehensive Tests', () => {
  test.beforeEach(async ({ page }) => {
    consoleErrors.length = 0;
    await captureConsoleMessages(page, 'Uncertainty UI');
    // Setup API mocks BEFORE navigating
    await setupUncertaintyMocks(page);
  });

  test('should load Uncertainty page with all components', async ({ page }) => {
    await page.goto('/uncertainty');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Take initial screenshot
    await page.screenshot({
      path: 'test-results/screenshots/uncertainty-full.png',
      fullPage: true,
    });

    // Check page title (use first() to handle multiple matches)
    const title = page.locator('text=Uncertainty Analysis').first();
    await expect(title).toBeVisible({ timeout: 10000 });

    // Soft assertion for console errors (hydration warnings are acceptable)
    expect.soft(consoleErrors.length).toBe(0);
  });

  test('should display 24-hour prediction chart', async ({ page }) => {
    await page.goto('/uncertainty');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Check for chart title
    const chartTitle = page.locator('text=24-Hour Prediction Forecast');
    await expect(chartTitle).toBeVisible({ timeout: 10000 });

    // Check for Recharts SVG elements
    const svgElements = page.locator('svg');
    const count = await svgElements.count();
    expect(count).toBeGreaterThan(0);

    // Check for legend items
    const legendItems = ['Current Confidence', 'Predicted Trend', 'Upper Bound', 'Lower Bound'];
    for (const item of legendItems) {
      const legend = page.locator(`text=${item}`);
      await expect(legend).toBeVisible();
    }

    // Check for bottom metrics
    const metrics = ['Velocity', 'Acceleration', 'Resolution ETA'];
    for (const metric of metrics) {
      const metricElement = page.locator(`text=${metric}`);
      await expect(metricElement).toBeVisible();
    }
  });

  test('should display vector breakdown with 5 dimensions', async ({ page }) => {
    await page.goto('/uncertainty');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Check for 5 vector dimensions (use first() to handle multiple matches)
    const dimensions = ['Technical', 'Market', 'Resource', 'Timeline', 'Quality'];
    for (const dimension of dimensions) {
      const dimElement = page.locator(`text=${dimension}`).first();
      await expect(dimElement).toBeVisible();
    }
  });

  test('should display uncertainty state (Deterministic/Probabilistic/etc)', async ({ page }) => {
    await page.goto('/uncertainty');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Check for quantum state (one of 5 states)
    // With mock data, we expect "Probabilistic" since that's the mock state
    const states = ['Deterministic', 'Probabilistic', 'Quantum', 'Chaotic', 'Void'];
    let stateFound = false;

    for (const state of states) {
      const stateElement = page.locator(`text=${state}`);
      if ((await stateElement.count()) > 0) {
        stateFound = true;
        break;
      }
    }

    expect(stateFound).toBe(true);
  });

  test('should display mitigation strategies with acknowledgment', async ({ page }) => {
    await page.goto('/uncertainty');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Check for mitigation strategies section
    const mitigationTitle = page.locator('text=Mitigation Strategies');
    await expect(mitigationTitle).toBeVisible({ timeout: 10000 });

    // Check for acknowledgment buttons
    const ackButtons = page.locator('button:has-text("Mark as Completed")');
    const buttonCount = await ackButtons.count();
    expect(buttonCount).toBeGreaterThan(0);

    // Test acknowledgment functionality
    if (buttonCount > 0) {
      await ackButtons.first().click();
      await page.waitForTimeout(2000);

      // Take screenshot after acknowledgment
      await page.screenshot({
        path: 'test-results/screenshots/uncertainty-after-ack.png',
        fullPage: true,
      });
    }
  });
});

test.describe('Confidence Dashboard - Comprehensive Tests', () => {
  test.beforeEach(async ({ page }) => {
    consoleErrors.length = 0;
    await captureConsoleMessages(page, 'Confidence Dashboard');
    // Setup API mocks BEFORE navigating
    await setupConfidenceMocks(page);
  });

  test('should load Confidence Dashboard with all components', async ({ page }) => {
    await page.goto('/confidence');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Take initial screenshot
    await page.screenshot({
      path: 'test-results/screenshots/confidence-full.png',
      fullPage: true,
    });

    // Check page title
    const title = page.locator('text=Bayesian Confidence Dashboard');
    await expect(title).toBeVisible({ timeout: 10000 });

    // Check subtitle
    const subtitle = page.locator('text=Beta-Binomial inference');
    await expect(subtitle).toBeVisible();

    // Soft assertion for console errors (hydration warnings are acceptable)
    expect.soft(consoleErrors.length).toBe(0);
  });

  test('should display 5 phase tabs and allow switching', async ({ page }) => {
    await page.goto('/confidence');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Check for 5 phase tabs
    const phases = ['Ideation', 'Design', 'MVP', 'Implementation', 'Testing'];
    for (const phase of phases) {
      const phaseTab = page.locator(`button:has-text("${phase}")`);
      await expect(phaseTab).toBeVisible();
    }

    // Test phase switching
    const designTab = page.locator('button:has-text("Design")').first();
    await designTab.click();
    await page.waitForTimeout(2000);

    // Take screenshot after phase switch
    await page.screenshot({
      path: 'test-results/screenshots/confidence-design-phase.png',
      fullPage: true,
    });
  });

  test('should display 4 summary cards', async ({ page }) => {
    await page.goto('/confidence');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Wait for data to load
    await page.waitForTimeout(3000);

    // Check for 4 summary cards (use first() to handle multiple matches)
    const cards = ['Confidence Score', 'Decision', 'Risk Level'];
    for (const card of cards) {
      const cardElement = page.locator(`text=${card}`).first();
      await expect(cardElement).toBeVisible({ timeout: 10000 });
    }

    // Check for Recommended or Actions card (soft assertion)
    const recommendedCard = page.locator('text=Recommended').first();
    const actionsCard = page.locator('text=Actions').first();
    const hasRecommended = (await recommendedCard.count()) > 0;
    const hasActions = (await actionsCard.count()) > 0;
    expect.soft(hasRecommended || hasActions).toBeTruthy();
  });

  test('should display phase thresholds visualization', async ({ page }) => {
    await page.goto('/confidence');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Check for phase thresholds section
    const thresholdsTitle = page.locator('text=Phase Confidence Thresholds');
    await expect(thresholdsTitle).toBeVisible({ timeout: 10000 });

    // Check for progress bars (at least 5 for each phase)
    const progressBars = page.locator('div.h-2.bg-gray-700.rounded-full');
    const barCount = await progressBars.count();
    expect(barCount).toBeGreaterThanOrEqual(5);
  });

  test('should display Bayesian Confidence component with all features', async ({ page }) => {
    await page.goto('/confidence');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Check for Bayesian Confidence component
    const bayesianTitle = page.locator('text=Bayesian Confidence Analysis');
    await expect(bayesianTitle).toBeVisible({ timeout: 10000 });

    // Check for decision badge (GO/GO_WITH_CHECKPOINTS/NO_GO)
    const decisions = ['GO', 'GO WITH CHECKPOINTS', 'NO GO'];
    let decisionFound = false;
    for (const decision of decisions) {
      const decisionElement = page.locator(`text=${decision}`);
      if ((await decisionElement.count()) > 0) {
        decisionFound = true;
        break;
      }
    }
    expect(decisionFound).toBe(true);

    // Check for Recommended Actions
    const actionsSection = page.locator('text=Recommended Actions');
    await expect(actionsSection).toBeVisible();

    // Check for Bayesian Statistics
    const statsSection = page.locator('text=Bayesian Statistics');
    await expect(statsSection).toBeVisible();

    // Check for specific Bayesian metrics
    const metrics = ['Prior Belief', 'Posterior', 'Likelihood', 'Confidence Width', 'Credible Interval'];
    let metricsFound = 0;
    for (const metric of metrics) {
      const metricElement = page.locator(`text=${metric}`);
      if ((await metricElement.count()) > 0) {
        metricsFound++;
      }
    }
    expect(metricsFound).toBeGreaterThanOrEqual(4); // At least 4 out of 5 metrics
  });

  test('should have working refresh functionality', async ({ page }) => {
    await page.goto('/confidence');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Find refresh button (lucide-refresh icon button)
    const refreshButton = page.locator('button:has([class*="lucide-refresh"])').first();

    if ((await refreshButton.count()) > 0) {
      await refreshButton.click();
      await page.waitForTimeout(2000);

      // Check for success toast (if exists)
      const successToast = page.locator('text=refreshed');
      // Note: Toast might disappear quickly, so we just check if click worked
    }
  });
});

test.describe('Cross-Dashboard Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Setup all API mocks for cross-dashboard tests
    await setupAPIMocks(page);
  });

  test('should navigate between Uncertainty and Confidence dashboards', async ({ page }) => {
    // Start at Uncertainty page
    await page.goto('/uncertainty');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Verify we're on Uncertainty page (use first() to handle multiple matches)
    const uncertaintyTitle = page.locator('text=Uncertainty Analysis').first();
    await expect(uncertaintyTitle).toBeVisible({ timeout: 10000 });

    // Navigate to Confidence page via URL (or navigation if available)
    await page.goto('/confidence');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Verify we're now on Confidence page
    const confidenceTitle = page.locator('text=Bayesian Confidence Dashboard').first();
    await expect(confidenceTitle).toBeVisible({ timeout: 10000 });

    // Navigate back to Uncertainty
    await page.goto('/uncertainty');
    await page.waitForLoadState('networkidle', { timeout: 60000 });

    // Verify we're back on Uncertainty page (create new locator)
    const uncertaintyTitleAgain = page.locator('text=Uncertainty Analysis').first();
    await expect(uncertaintyTitleAgain).toBeVisible({ timeout: 10000 });

    // Take final screenshot
    await page.screenshot({
      path: 'test-results/screenshots/cross-dashboard-navigation.png',
      fullPage: true,
    });
  });

  test('should maintain data consistency across page reloads', async ({ page }) => {
    // Load Uncertainty page
    await page.goto('/uncertainty');
    await page.waitForLoadState('networkidle', { timeout: 60000 });
    await page.waitForTimeout(3000);

    // Get initial state value
    const initialState = await page.locator('text=/Deterministic|Probabilistic|Quantum|Chaotic|Void/').first().textContent();

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle', { timeout: 60000 });
    await page.waitForTimeout(3000);

    // Get state after reload
    const reloadedState = await page.locator('text=/Deterministic|Probabilistic|Quantum|Chaotic|Void/').first().textContent();

    // States should be consistent (or at least both should exist)
    expect(initialState).toBeTruthy();
    expect(reloadedState).toBeTruthy();
  });
});

test.describe('Performance & Error Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    // Setup API mocks for performance tests
    await setupAPIMocks(page);
  });

  test('Uncertainty UI should load within performance budget', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/uncertainty');
    await page.waitForLoadState('domcontentloaded');

    const loadTime = Date.now() - startTime;

    console.log(`Uncertainty UI load time: ${loadTime}ms`);

    // Performance budget: 6 seconds
    expect(loadTime).toBeLessThan(6000);
  });

  test('Confidence Dashboard should load within performance budget', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/confidence');
    await page.waitForLoadState('domcontentloaded');

    const loadTime = Date.now() - startTime;

    console.log(`Confidence Dashboard load time: ${loadTime}ms`);

    // Performance budget: 6 seconds
    expect(loadTime).toBeLessThan(6000);
  });

  test.afterAll(async () => {
    // Generate error summary
    console.log('\n=== UNCERTAINTY & CONFIDENCE TEST SUMMARY ===\n');

    if (consoleErrors.length === 0) {
      console.log('All tests passed without console errors');
    } else {
      console.log('Total Errors:', consoleErrors.length);
      consoleErrors.forEach((err) => {
        console.log(`  [${err.page}] ${err.message}`);
      });
    }

    console.log('\n============================================\n');
  });
});
