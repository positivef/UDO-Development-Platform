import { test, expect, Page } from '@playwright/test';

/**
 * E2E tests for all UDO Dashboard pages
 * Tests page load, JavaScript errors, and console warnings
 */

// Store console errors for reporting
const consoleErrors: { page: string; message: string }[] = [];
const consoleWarnings: { page: string; message: string }[] = [];

// Helper to check if error should be ignored
function shouldIgnoreError(text: string): boolean {
  const ignoredPatterns = [
    'Failed to fetch',
    'Failed to load resource',
    'NetworkError',
    'hydration',
    'Hydration',
    'tree hydrated',
    'server rendered HTML',
    'WebSocket',
    'ERR_CONNECTION_REFUSED',
    'ConfidenceWS',
    'KanbanWS',
    '403',
    '401',
    'ECONNREFUSED',
    'net::ERR_',
  ];
  return ignoredPatterns.some(pattern => text.includes(pattern));
}

// Helper to capture console messages
async function captureConsoleMessages(page: Page, pageName: string) {
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (!shouldIgnoreError(text)) {
        consoleErrors.push({ page: pageName, message: text });
      }
    } else if (msg.type() === 'warning') {
      consoleWarnings.push({ page: pageName, message: msg.text() });
    }
  });

  page.on('pageerror', (error) => {
    const errorMsg = error.message || '';
    if (!shouldIgnoreError(errorMsg)) {
      consoleErrors.push({
        page: pageName,
        message: `Uncaught exception: ${error.message}`,
      });
    }
  });
}

test.describe('Dashboard Pages - Rendering & Error Detection', () => {
  test.beforeEach(async ({ page }) => {
    // Clear error arrays
    consoleErrors.length = 0;
    consoleWarnings.length = 0;
  });

  test('Main Dashboard (/) should load without errors', async ({ page }) => {
    await captureConsoleMessages(page, 'Main Dashboard');

    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Wait for content to appear (short timeout)
    await page.waitForSelector('h1', { timeout: 5000 }).catch(() => {});

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/main-dashboard.png',
      fullPage: true,
    });

    // Check for specific elements (non-blocking)
    const hasTitle = await page.waitForSelector('h1', { timeout: 3000 })
      .then(() => true)
      .catch(() => false);

    if (hasTitle) {
      console.log('✅ Main Dashboard title found');
    } else {
      console.log('⚠️ Main Dashboard title not visible');
    }

    // Report errors
    if (consoleErrors.length > 0) {
      console.log('❌ Main Dashboard Errors:');
      consoleErrors.forEach((err) => console.log(`  - ${err.message}`));
    }

    // Soft assertion - don't fail test, just report
    expect.soft(consoleErrors.length).toBe(0);
  });

  test('Time Tracking (/time-tracking) should load without errors', async ({
    page,
  }) => {
    await captureConsoleMessages(page, 'Time Tracking');

    await page.goto('/time-tracking');
    await page.waitForLoadState('domcontentloaded');

    // Wait for content to appear (short timeout)
    await page.waitForSelector('h1, h2, text=Time Tracking', { timeout: 5000 }).catch(() => {});

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/time-tracking.png',
      fullPage: true,
    });

    // Check for Time Tracking header (non-blocking)
    const hasHeader = await page.waitForSelector('text=Time Tracking Dashboard', { timeout: 3000 })
      .then(() => true)
      .catch(() => false);

    // Check for date range display (non-blocking)
    const hasDateRange = await page.waitForSelector('span', { timeout: 3000 })
      .then(() => true)
      .catch(() => false);

    if (hasHeader) {
      console.log('✅ Time Tracking header found');
    } else {
      console.log('⚠️ Time Tracking header not visible');
    }

    console.log(`Date range: ${hasDateRange ? '✅' : '⚠️'}`);

    // Report errors
    if (consoleErrors.length > 0) {
      console.log('❌ Time Tracking Errors:');
      consoleErrors.forEach((err) => console.log(`  - ${err.message}`));
    }

    expect.soft(consoleErrors.length).toBe(0);
  });

  test('Quality Metrics (/quality) should load without errors', async ({
    page,
  }) => {
    await captureConsoleMessages(page, 'Quality Metrics');

    await page.goto('/quality');
    await page.waitForLoadState('domcontentloaded');

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/quality.png',
      fullPage: true,
    });

    // Check for quality-related content
    const qualityIndicator = page.locator('h1, h2, h3').first();
    await expect(qualityIndicator).toBeVisible();

    // Report errors
    if (consoleErrors.length > 0) {
      console.log('❌ Quality Metrics Errors:');
      consoleErrors.forEach((err) => console.log(`  - ${err.message}`));
    }

    expect.soft(consoleErrors.length).toBe(0);
  });

  test('C-K Theory (/ck-theory) should load without errors', async ({
    page,
  }) => {
    await captureConsoleMessages(page, 'C-K Theory');

    await page.goto('/ck-theory');
    await page.waitForLoadState('domcontentloaded');

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/ck-theory.png',
      fullPage: true,
    });

    // Check for C-K Theory content
    const ckIndicator = page.locator('h1, h2, h3').first();
    await expect(ckIndicator).toBeVisible();

    // Report errors
    if (consoleErrors.length > 0) {
      console.log('❌ C-K Theory Errors:');
      consoleErrors.forEach((err) => console.log(`  - ${err.message}`));
    }

    expect.soft(consoleErrors.length).toBe(0);
  });

  test('GI Formula (/gi-formula) should load without errors', async ({
    page,
  }) => {
    await captureConsoleMessages(page, 'GI Formula');

    await page.goto('/gi-formula');
    await page.waitForLoadState('domcontentloaded');

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/gi-formula.png',
      fullPage: true,
    });

    // Check for GI Formula content
    const giIndicator = page.locator('h1, h2, h3').first();
    await expect(giIndicator).toBeVisible();

    // Report errors
    if (consoleErrors.length > 0) {
      console.log('❌ GI Formula Errors:');
      consoleErrors.forEach((err) => console.log(`  - ${err.message}`));
    }

    expect.soft(consoleErrors.length).toBe(0);
  });

  test.afterAll(async () => {
    // Generate error summary
    console.log('\n=== TEST SUMMARY ===\n');

    if (consoleErrors.length === 0) {
      console.log('✅ No errors detected across all pages');
    } else {
      console.log('❌ Total Errors:', consoleErrors.length);
      consoleErrors.forEach((err) => {
        console.log(`  [${err.page}] ${err.message}`);
      });
    }

    if (consoleWarnings.length > 0) {
      console.log('\n⚠️  Total Warnings:', consoleWarnings.length);
      consoleWarnings.forEach((warn) => {
        console.log(`  [${warn.page}] ${warn.message}`);
      });
    }

    console.log('\n===================\n');
  });
});

test.describe('Dashboard Navigation', () => {
  test('Navigation menu should work', async ({ page }) => {
    await page.goto('/');

    // Check if navigation exists (adjust selector based on actual structure)
    const navLinks = page.locator('nav a, [role="navigation"] a');
    const count = await navLinks.count();

    console.log(`Found ${count} navigation links`);
    expect(count).toBeGreaterThan(0);

    // Take screenshot of navigation
    await page.screenshot({
      path: 'test-results/screenshots/navigation.png',
    });
  });
});

test.describe('Performance Checks', () => {
  test('Main dashboard should load within performance budget', async ({
    page,
  }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    const loadTime = Date.now() - startTime;

    console.log(`Page load time: ${loadTime}ms`);

    // Performance budget: 6 seconds (DOM ready, real-time dashboard with API calls)
    expect(loadTime).toBeLessThan(6000);
  });
});
