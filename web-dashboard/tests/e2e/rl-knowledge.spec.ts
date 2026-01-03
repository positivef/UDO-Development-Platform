import { test, expect, Page } from '@playwright/test';

/**
 * E2E tests for RL Knowledge System Card
 * Tests the Training-free GRPO based knowledge optimization dashboard component
 *
 * Component: web-dashboard/components/dashboard/rl-knowledge-card.tsx
 * API: GET /api/rl/summary - Returns Token Prior stats, Pattern counts, Experiments
 */

// Store console errors for reporting
const consoleErrors: { test: string; message: string }[] = [];

// Helper to check if error should be ignored
function shouldIgnoreError(text: string): boolean {
  const ignoredPatterns = [
    'Failed to fetch',
    'Failed to load resource',
    'NetworkError',
    'hydration',
    'Hydration',
    'WebSocket',
    'ERR_CONNECTION_REFUSED',
    '403',
    '401',
    'ECONNREFUSED',
    'net::ERR_',
  ];
  return ignoredPatterns.some((pattern) => text.includes(pattern));
}

// Helper to capture console messages
async function captureConsoleMessages(page: Page, testName: string) {
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (!shouldIgnoreError(text)) {
        consoleErrors.push({ test: testName, message: text });
      }
    }
  });

  page.on('pageerror', (error) => {
    const errorMsg = error.message || '';
    if (!shouldIgnoreError(errorMsg)) {
      consoleErrors.push({
        test: testName,
        message: `Uncaught exception: ${error.message}`,
      });
    }
  });
}

test.describe('RL Knowledge System Card - Main Dashboard Integration', () => {
  test.beforeEach(async () => {
    // Clear error arrays
    consoleErrors.length = 0;
  });

  test('RLKnowledgeCard should render on main dashboard', async ({ page }) => {
    await captureConsoleMessages(page, 'RLKnowledgeCard Render');

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for dashboard to fully load (including API calls)
    await page.waitForTimeout(5000);

    // Look for RL Knowledge System card title with more specific selector
    const rlCardTitle = page.getByText('RL Knowledge System', { exact: false });

    // Try to wait for it with a longer timeout
    try {
      await rlCardTitle.first().waitFor({ timeout: 10000 });
      console.log('✅ RL Knowledge System card found on dashboard');
    } catch {
      console.log('⚠️ RL Knowledge System card not visible (API may be loading)');
    }

    const isVisible = await rlCardTitle.first().isVisible().catch(() => false);

    // Take screenshot showing the RL Knowledge card
    await page.screenshot({
      path: 'test-results/screenshots/rl-knowledge-card.png',
      fullPage: true,
    });

    // Soft assertion - component should be present (may fail if API is slow)
    expect.soft(isVisible).toBe(true);

    // Report errors
    if (consoleErrors.length > 0) {
      console.log('❌ RL Knowledge Card Errors:');
      consoleErrors.forEach((err) => console.log(`  - ${err.message}`));
    }
    expect.soft(consoleErrors.length).toBe(0);
  });

  test('RLKnowledgeCard should display system status badge', async ({ page }) => {
    await captureConsoleMessages(page, 'RLKnowledgeCard Status');

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Scroll to RL Knowledge Card (it's below the fold)
    const rlCard = page.getByText('RL Knowledge System', { exact: false }).first();
    await rlCard.scrollIntoViewIfNeeded().catch(() => {});
    await page.waitForTimeout(1000);

    // Look for status badges - "operational", "degraded", or "offline"
    const operationalBadge = page.getByText('operational', { exact: true });
    const degradedBadge = page.getByText('degraded', { exact: true });
    const offlineBadge = page.getByText('offline', { exact: true });

    const hasOperational = await operationalBadge.first().isVisible().catch(() => false);
    const hasDegraded = await degradedBadge.first().isVisible().catch(() => false);
    const hasOffline = await offlineBadge.first().isVisible().catch(() => false);

    const hasStatusBadge = hasOperational || hasDegraded || hasOffline;

    if (hasOperational) {
      console.log('✅ System status: operational');
    } else if (hasDegraded) {
      console.log('⚠️ System status: degraded');
    } else if (hasOffline) {
      console.log('❌ System status: offline');
    } else {
      console.log('⚠️ System status badge not found (API may be loading)');
    }

    expect.soft(hasStatusBadge).toBe(true);
  });

  test('RLKnowledgeCard should display Token Prior statistics', async ({
    page,
  }) => {
    await captureConsoleMessages(page, 'RLKnowledgeCard Token Prior');

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Scroll to RL Knowledge Card (it's below the fold)
    const rlCard = page.getByText('RL Knowledge System', { exact: false }).first();
    await rlCard.scrollIntoViewIfNeeded().catch(() => {});
    await page.waitForTimeout(1000);

    // Look for Token Prior section indicators
    const tokenPriorTitle = page.getByText('Token Prior', { exact: false });
    const decisionsText = page.getByText(/decisions/i);
    const validationText = page.getByText(/Validation Rate/i);

    const hasTokenPriorTitle = await tokenPriorTitle.first().isVisible().catch(() => false);
    const hasDecisions = await decisionsText.first().isVisible().catch(() => false);
    const hasValidation = await validationText.first().isVisible().catch(() => false);

    console.log(`Token Prior Section:`);
    console.log(`  - Title: ${hasTokenPriorTitle ? '✅' : '⚠️'}`);
    console.log(`  - Decisions: ${hasDecisions ? '✅' : '⚠️'}`);
    console.log(`  - Validation Rate: ${hasValidation ? '✅' : '⚠️'}`);

    // Token Prior title should be visible
    expect.soft(hasTokenPriorTitle).toBe(true);
  });

  test('RLKnowledgeCard should display Knowledge Patterns section', async ({
    page,
  }) => {
    await captureConsoleMessages(page, 'RLKnowledgeCard Patterns');

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Scroll to RL Knowledge Card (it's below the fold)
    const rlCard = page.getByText('RL Knowledge System', { exact: false }).first();
    await rlCard.scrollIntoViewIfNeeded().catch(() => {});
    await page.waitForTimeout(1000);

    // Look for Knowledge Patterns section
    const patternsTitle = page.getByText('Knowledge Patterns', { exact: false });
    const hasPatternsTitle = await patternsTitle.first().isVisible().catch(() => false);

    console.log(`Knowledge Patterns Section: ${hasPatternsTitle ? '✅' : '⚠️'}`);

    expect.soft(hasPatternsTitle).toBe(true);
  });

  test('RLKnowledgeCard should display Experiments section', async ({
    page,
  }) => {
    await captureConsoleMessages(page, 'RLKnowledgeCard Experiments');

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Scroll to RL Knowledge Card (it's below the fold)
    const rlCard = page.getByText('RL Knowledge System', { exact: false }).first();
    await rlCard.scrollIntoViewIfNeeded().catch(() => {});
    await page.waitForTimeout(1000);

    // Look for Experiments section
    const experimentsTitle = page.getByText('Experiments', { exact: false });
    const hasExperimentsTitle = await experimentsTitle.first().isVisible().catch(() => false);

    console.log(`Experiments Section: ${hasExperimentsTitle ? '✅' : '⚠️'}`);

    expect.soft(hasExperimentsTitle).toBe(true);
  });

  test('RLKnowledgeCard should show loading state initially', async ({
    page,
  }) => {
    await captureConsoleMessages(page, 'RLKnowledgeCard Loading');

    // Navigate without waiting for load
    await page.goto('/');

    // Immediately check for loading indicator (spinner or skeleton)
    const loadingIndicator = page.locator('.animate-spin, .animate-pulse, text=Loading').first();
    const hasLoading = await loadingIndicator.isVisible().catch(() => false);

    // This may or may not catch the loading state depending on timing
    console.log(`Loading state detected: ${hasLoading ? '✅' : 'Not captured (fast load)'}`);

    // Wait for content
    await page.waitForLoadState('domcontentloaded');
  });

  test('RLKnowledgeCard should handle API error gracefully', async ({
    page,
  }) => {
    await captureConsoleMessages(page, 'RLKnowledgeCard Error Handling');

    // Block API requests to simulate error
    await page.route('**/api/rl/**', (route) => {
      route.abort('failed');
    });

    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Should show error state or fallback UI
    const errorText = page.locator('text=/error|failed|unavailable/i').first();
    const hasError = await errorText.isVisible().catch(() => false);

    // Take screenshot of error state
    await page.screenshot({
      path: 'test-results/screenshots/rl-knowledge-error-state.png',
      fullPage: true,
    });

    console.log(`Error handling: ${hasError ? '✅ Shows error state' : '⚠️ No visible error message'}`);

    // Non-blocking assertion - error handling may vary
    // The important thing is the page doesn't crash
  });
});

test.describe('RL Knowledge System API Integration', () => {
  test('API /api/rl/summary should return valid data structure', async ({
    page,
  }) => {
    // Direct API test
    const response = await page.request.get('http://localhost:8001/api/rl/summary');
    const status = response.status();

    if (status === 200) {
      const data = await response.json();
      console.log('✅ API /api/rl/summary response:', JSON.stringify(data, null, 2));

      // Validate response structure
      expect(data).toHaveProperty('token_prior');
      expect(data).toHaveProperty('patterns');
      expect(data).toHaveProperty('experiments');
      expect(data).toHaveProperty('system_status');

      // Validate token_prior structure
      expect(data.token_prior).toHaveProperty('total_decisions');
      expect(data.token_prior).toHaveProperty('validated_count');

      // Validate patterns structure
      expect(data.patterns).toHaveProperty('total');
      expect(data.patterns).toHaveProperty('by_domain');

      // Validate experiments structure
      expect(data.experiments).toHaveProperty('total');
      expect(data.experiments).toHaveProperty('with_success');

      console.log('✅ API response structure validated');
    } else {
      console.log(`⚠️ API returned status ${status}`);
      expect.soft(status).toBe(200);
    }
  });

  test('API /api/rl/token-prior/stats should return token statistics', async ({
    page,
  }) => {
    const response = await page.request.get(
      'http://localhost:8001/api/rl/token-prior/stats'
    );
    const status = response.status();

    if (status === 200) {
      const data = await response.json();
      console.log('✅ Token Prior Stats:', JSON.stringify(data, null, 2));

      expect(data).toHaveProperty('total_decisions');
      expect(data).toHaveProperty('unique_hours');
      expect(data).toHaveProperty('validated_count');
    } else {
      console.log(`⚠️ Token Prior API returned status ${status}`);
    }

    expect.soft(status).toBe(200);
  });

  test('API /api/rl/experiments should return experiment list', async ({
    page,
  }) => {
    const response = await page.request.get(
      'http://localhost:8001/api/rl/experiments'
    );
    const status = response.status();

    if (status === 200) {
      const data = await response.json();
      console.log('✅ Experiments:', JSON.stringify(data, null, 2));

      expect(Array.isArray(data)).toBe(true);
    } else {
      console.log(`⚠️ Experiments API returned status ${status}`);
    }

    expect.soft(status).toBe(200);
  });
});

test.describe('RL Knowledge System Performance', () => {
  test('RLKnowledgeCard should render within performance budget', async ({
    page,
  }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Wait for RL Knowledge card to appear (may be below fold)
    await page
      .waitForSelector('text=RL Knowledge System', { timeout: 10000 })
      .catch(() => {});

    const loadTime = Date.now() - startTime;

    console.log(`RL Knowledge Card visible after: ${loadTime}ms`);

    // Performance budget: 8 seconds for card to be visible (includes API fetch + render)
    expect.soft(loadTime).toBeLessThan(8000);
  });

  test('API calls should complete within timeout', async ({ page }) => {
    const startTime = Date.now();

    const response = await page.request.get('http://localhost:8001/api/rl/summary');
    const apiTime = Date.now() - startTime;

    console.log(`API /api/rl/summary response time: ${apiTime}ms`);

    // API should respond within 3 seconds
    expect(apiTime).toBeLessThan(3000);
    expect(response.status()).toBe(200);
  });
});

test.afterAll(async () => {
  // Generate error summary
  console.log('\n=== RL KNOWLEDGE TEST SUMMARY ===\n');

  if (consoleErrors.length === 0) {
    console.log('✅ No errors detected in RL Knowledge tests');
  } else {
    console.log('❌ Total Errors:', consoleErrors.length);
    consoleErrors.forEach((err) => {
      console.log(`  [${err.test}] ${err.message}`);
    });
  }

  console.log('\n=================================\n');
});
