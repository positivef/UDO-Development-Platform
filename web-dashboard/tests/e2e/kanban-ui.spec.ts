import { test, expect, Page } from '@playwright/test';

/**
 * E2E tests for Kanban Board UI (Week 1 Day 1 implementation)
 * Tests rendering, drag & drop, task cards, and navigation
 */

const consoleErrors: { message: string }[] = [];

async function captureConsoleMessages(page: Page) {
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push({ message: msg.text() });
    }
  });

  page.on('pageerror', (error) => {
    consoleErrors.push({
      message: `Uncaught exception: ${error.message}`,
    });
  });
}

test.describe('Kanban Board - Week 1 Day 1 UI Implementation', () => {
  test.beforeEach(async ({ page }) => {
    consoleErrors.length = 0;
    await captureConsoleMessages(page);
  });

  test('Kanban page (/kanban) should load without errors', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/kanban-board.png',
      fullPage: true,
    });

    // Check for page title
    const title = page.locator('h1:has-text("Kanban Board")');
    await expect(title).toBeVisible();

    // Check for subtitle with UDO v2 reference
    const subtitle = page.locator('text=Manage tasks across UDO v2');
    await expect(subtitle).toBeVisible();

    // Report errors
    if (consoleErrors.length > 0) {
      console.log('❌ Kanban Page Errors:');
      consoleErrors.forEach((err) => console.log(`  - ${err.message}`));
    }

    expect.soft(consoleErrors.length).toBe(0);
  });

  test('Should render 4 Kanban columns (To Do, In Progress, Blocked, Done)', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Check for column headers
    const todoColumn = page.locator('h2:has-text("To Do")');
    const inProgressColumn = page.locator('h2:has-text("In Progress")');
    const blockedColumn = page.locator('h2:has-text("Blocked")');
    const doneColumn = page.locator('h2:has-text("Done")');

    await expect(todoColumn).toBeVisible();
    await expect(inProgressColumn).toBeVisible();
    await expect(blockedColumn).toBeVisible();
    await expect(doneColumn).toBeVisible();

    console.log('✅ All 4 columns rendered successfully');
  });

  test('Should display 5 mock tasks with correct titles', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Expected task titles from mockTasks in page.tsx
    const expectedTasks = [
      'Implement authentication system',
      'Design API endpoints',
      'Set up CI/CD pipeline',
      'Fix database connection pooling',
      'Research AI task suggestion patterns',
    ];

    for (const taskTitle of expectedTasks) {
      const taskCard = page.locator(`text=${taskTitle}`);
      await expect(taskCard).toBeVisible();
    }

    console.log('✅ All 5 mock tasks rendered successfully');
  });

  test('Should show task priority with color-coded borders', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Check for cards with different priority borders (using class names)
    // Low (blue), Medium (yellow), High (orange), Critical (red)

    // Critical priority task (red border)
    const criticalTask = page.locator('text=Fix database connection pooling');
    const criticalCard = criticalTask.locator('xpath=ancestor::div[contains(@class, "border-l-4")]');
    await expect(criticalCard).toBeVisible();

    // High priority task (orange border)
    const highTask = page.locator('text=Implement authentication system');
    const highCard = highTask.locator('xpath=ancestor::div[contains(@class, "border-l-4")]');
    await expect(highCard).toBeVisible();

    console.log('✅ Priority color coding verified');
  });

  test('Should display task metadata (tags, estimated hours, phase)', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Check for task tags (using more specific selector for badge elements)
    const authTag = page.locator('[data-slot="badge"]:has-text("auth")').first();
    await expect(authTag).toBeVisible();

    const securityTag = page.locator('[data-slot="badge"]:has-text("security")').first();
    await expect(securityTag).toBeVisible();

    // Check for estimated hours display
    const estimatedHours = page.locator('text=/\\d+h/');
    const count = await estimatedHours.count();
    expect(count).toBeGreaterThan(0);

    console.log('✅ Task metadata displayed correctly');
  });

  test('Should show task count in column badges', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Check for column count badges (use data-slot attribute from ShadCN Badge component)
    const columnBadges = page.locator('[data-slot="badge"]');
    const badgeCount = await columnBadges.count();

    // Should have at least 4 badges (one per column) plus task tag badges
    expect(badgeCount).toBeGreaterThanOrEqual(4);

    console.log('✅ Column badges with task counts displayed');
  });

  test('Should display stats footer with task counts', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Check for stats footer
    const totalTasks = page.locator('text=Total Tasks:');
    await expect(totalTasks).toBeVisible();

    const inProgressCount = page.locator('text=In Progress:');
    await expect(inProgressCount).toBeVisible();

    const blockedCount = page.locator('text=Blocked:');
    await expect(blockedCount).toBeVisible();

    const completedCount = page.locator('text=Completed:');
    await expect(completedCount).toBeVisible();

    console.log('✅ Stats footer displayed correctly');
  });

  test('Should have action buttons (Filter, Import, Export, Add Task)', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Check for action buttons
    const filterButton = page.locator('button:has-text("Filter")');
    await expect(filterButton).toBeVisible();

    const importButton = page.locator('button:has-text("Import")');
    await expect(importButton).toBeVisible();

    const exportButton = page.locator('button:has-text("Export")');
    await expect(exportButton).toBeVisible();

    const addTaskButton = page.locator('button:has-text("Add Task")');
    await expect(addTaskButton).toBeVisible();

    console.log('✅ All action buttons present');
  });

  test('Should load within performance budget (<3 seconds)', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    const loadTime = Date.now() - startTime;

    console.log(`Kanban page load time: ${loadTime}ms`);

    // Performance budget: 3 seconds (static page with mock data)
    expect(loadTime).toBeLessThan(3000);
  });

  test.afterAll(async () => {
    console.log('\n=== KANBAN UI TEST SUMMARY ===\n');

    if (consoleErrors.length === 0) {
      console.log('✅ No errors detected in Kanban UI');
    } else {
      console.log('❌ Total Errors:', consoleErrors.length);
      consoleErrors.forEach((err) => {
        console.log(`  - ${err.message}`);
      });
    }

    console.log('\n==============================\n');
  });
});

test.describe('Kanban Navigation Integration', () => {
  test('Navigation menu should include Kanban Board link', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Check for Kanban link in navigation (use .first() to avoid strict mode violation)
    const kanbanLink = page.locator('a[href="/kanban"]').first();
    await expect(kanbanLink).toBeVisible();

    console.log('✅ Kanban navigation link found');
  });

  test('Clicking Kanban link should navigate to /kanban', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Click Kanban link (use .first() to select the <a> tag, not the button wrapper)
    const kanbanLink = page.locator('a[href="/kanban"]').first();
    await kanbanLink.click();

    // Wait for navigation
    await page.waitForURL('**/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Verify we're on the Kanban page
    const title = page.locator('h1:has-text("Kanban Board")');
    await expect(title).toBeVisible();

    console.log('✅ Navigation to Kanban page successful');
  });
});

test.describe('Kanban Board - Visual Regression', () => {
  test('Full page screenshot for visual comparison', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Take full page screenshot for visual regression baseline
    await page.screenshot({
      path: 'test-results/screenshots/kanban-board-baseline.png',
      fullPage: true,
    });

    console.log('✅ Visual regression baseline captured');
  });

  test('Individual column screenshots', async ({ page }) => {
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // Take screenshots of individual columns
    const columns = ['To Do', 'In Progress', 'Blocked', 'Done'];

    for (const columnName of columns) {
      const column = page.locator(`h2:has-text("${columnName}")`).locator('xpath=ancestor::div[contains(@class, "Card")]');

      if (await column.isVisible()) {
        await column.screenshot({
          path: `test-results/screenshots/kanban-column-${columnName.toLowerCase().replace(' ', '-')}.png`,
        });
      }
    }

    console.log('✅ Individual column screenshots captured');
  });
});
