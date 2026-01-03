import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for UDO Dashboard testing
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 3, // Reduced from undefined (6) to 3 to prevent resource contention
  reporter: 'html',
  timeout: 60000, // Increased global test timeout from 30s to 60s

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Increased timeout to 60s to reduce timeout failures
    actionTimeout: 60000,
    navigationTimeout: 60000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true, // Always reuse existing server to avoid timeout
    timeout: 180000, // Increased to 3 minutes as backup
    env: {
      NEXT_PUBLIC_API_URL: 'http://localhost:8001', // Ensure backend URL is set for tests
    },
  },
});
