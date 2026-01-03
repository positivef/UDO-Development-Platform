import { test, expect } from '@playwright/test';

test('Debug: Check API URL configuration', async ({ page }) => {
  // Capture console logs
  const consoleLogs: string[] = [];
  page.on('console', msg => {
    consoleLogs.push(`[${msg.type()}] ${msg.text()}`);
  });

  // Capture network requests to /api/rl/
  const apiRequests: string[] = [];
  page.on('request', req => {
    if (req.url().includes('/api/rl/')) {
      apiRequests.push(`REQUEST: ${req.method()} ${req.url()}`);
    }
  });
  page.on('response', res => {
    if (res.url().includes('/api/rl/')) {
      apiRequests.push(`RESPONSE: ${res.status()} ${res.url()}`);
    }
  });

  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  // Print findings
  console.log('\n=== API URL Debug ===');
  console.log('Console logs with API/error:', consoleLogs.filter(l =>
    l.toLowerCase().includes('api') ||
    l.toLowerCase().includes('rl') ||
    l.toLowerCase().includes('error') ||
    l.toLowerCase().includes('fetch')
  ));
  console.log('\nAll RL API Requests:', apiRequests);
  console.log('=====================\n');

  // Check for any RL API calls
  expect(apiRequests.length).toBeGreaterThan(0);
});
