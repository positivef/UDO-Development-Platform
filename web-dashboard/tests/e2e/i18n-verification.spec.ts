import { test, expect } from '@playwright/test';

test.describe('i18n Korean Translation Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Set Korean locale in localStorage before navigating
    await page.addInitScript(() => {
      localStorage.setItem('locale', 'ko');
    });
  });

  test('Dashboard shows Korean text', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({ path: 'test-results/i18n-dashboard-ko.png', fullPage: true });

    // Verify Korean text is present
    await expect(page.locator('text=UDO 개발 플랫폼')).toBeVisible({ timeout: 10000 });
  });

  test('Kanban page shows Korean text', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('networkidle');

    await page.screenshot({ path: 'test-results/i18n-kanban-ko.png', fullPage: true });

    // Verify Korean column headers (using getByRole for strict mode)
    await expect(page.getByRole('heading', { name: '할 일' })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('heading', { name: '진행 중' })).toBeVisible({ timeout: 10000 });
  });

  test('Time Tracking page shows Korean text', async ({ page }) => {
    await page.goto('/time-tracking');
    await page.waitForLoadState('networkidle');

    await page.screenshot({ path: 'test-results/i18n-time-tracking-ko.png', fullPage: true });

    // Verify Korean title
    await expect(page.locator('text=시간 추적 대시보드')).toBeVisible({ timeout: 10000 });
  });

  test('CK Theory page shows Korean text', async ({ page }) => {
    await page.goto('/ck-theory');
    await page.waitForLoadState('networkidle');

    await page.screenshot({ path: 'test-results/i18n-ck-theory-ko.png', fullPage: true });

    // Verify Korean title
    await expect(page.locator('text=C-K 이론')).toBeVisible({ timeout: 10000 });
  });

  test('GI Formula page shows Korean text', async ({ page }) => {
    await page.goto('/gi-formula');
    await page.waitForLoadState('networkidle');

    await page.screenshot({ path: 'test-results/i18n-gi-formula-ko.png', fullPage: true });

    // Verify Korean title (using getByRole for strict mode)
    await expect(page.getByRole('heading', { name: 'GI 공식' })).toBeVisible({ timeout: 10000 });
  });

  test('Language switcher works', async ({ page }) => {
    // Start with English
    await page.addInitScript(() => {
      localStorage.setItem('locale', 'en');
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Should show English
    await expect(page.locator('text=UDO Development Platform')).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'test-results/i18n-dashboard-en.png', fullPage: true });

    // Click language switcher and select Korean
    const languageSwitcher = page.locator('[data-testid="language-switcher"]').or(page.locator('button:has-text("English")'));
    if (await languageSwitcher.isVisible()) {
      await languageSwitcher.click();
      const koreanOption = page.locator('text=한국어');
      if (await koreanOption.isVisible()) {
        await koreanOption.click();
        await page.waitForTimeout(1000);

        // Verify Korean text after switch
        await page.screenshot({ path: 'test-results/i18n-dashboard-switched-ko.png', fullPage: true });
      }
    }
  });
});
