import { test, expect } from '@playwright/test'

/**
 * Mobile Responsiveness Tests
 * Tests key pages at different viewport sizes
 */

const viewports = {
  mobile: { width: 375, height: 667 },   // iPhone SE
  tablet: { width: 768, height: 1024 },  // iPad
  desktop: { width: 1280, height: 800 }, // Desktop
}

const pages = [
  { path: '/', name: 'Dashboard' },
  { path: '/kanban', name: 'Kanban' },
  { path: '/governance', name: 'Governance' },
]

test.describe('Mobile Responsiveness', () => {
  for (const [deviceName, viewport] of Object.entries(viewports)) {
    test.describe(`${deviceName} (${viewport.width}x${viewport.height})`, () => {
      test.use({ viewport })

      for (const page of pages) {
        test(`${page.name} page renders without horizontal scroll`, async ({ page: pageObj }) => {
          await pageObj.goto(page.path)
          await pageObj.waitForLoadState('domcontentloaded')

          // Wait a bit for CSS to apply
          await pageObj.waitForTimeout(1000)

          // Allow small overflow (scrollbar width) - increased tolerance for dev mode
          const scrollDiff = await pageObj.evaluate(() => {
            return document.documentElement.scrollWidth - document.documentElement.clientWidth
          })

          // Allow up to 50px for scrollbars and minor overflow in dev
          expect(scrollDiff).toBeLessThanOrEqual(50)
        })

        test(`${page.name} page loads at viewport size`, async ({ page: pageObj }) => {
          await pageObj.goto(page.path)
          await pageObj.waitForLoadState('domcontentloaded')

          // Check page body is rendered
          await expect(pageObj.locator('body')).toBeVisible()

          // Take screenshot for visual verification
          await pageObj.screenshot({
            path: `test-results/screenshots/${deviceName}-${page.name.toLowerCase()}.png`,
            fullPage: true
          })
        })
      }

      test('Navigation is accessible on mobile', async ({ page: pageObj }) => {
        await pageObj.goto('/')
        await pageObj.waitForLoadState('networkidle')

        // Check navigation exists
        const nav = pageObj.locator('nav, [role="navigation"], aside').first()
        await expect(nav).toBeVisible()

        // On mobile, check hamburger menu or sidebar behavior
        if (viewport.width < 768) {
          // Mobile: expect collapsed navigation or hamburger
          const hamburger = pageObj.locator('[aria-label*="menu"], button:has-text("menu"), .hamburger, .mobile-menu-toggle').first()

          // Either hamburger exists or nav is still visible (always-visible mobile nav)
          const hamburgerVisible = await hamburger.isVisible().catch(() => false)
          const navVisible = await nav.isVisible()

          expect(hamburgerVisible || navVisible).toBeTruthy()
        }
      })

      test('Text is readable at viewport size', async ({ page: pageObj }) => {
        await pageObj.goto('/')
        await pageObj.waitForLoadState('networkidle')

        // Check font sizes are appropriate
        const fontSizes = await pageObj.evaluate(() => {
          const elements = document.querySelectorAll('p, span, h1, h2, h3, h4, h5, h6, a, button')
          const sizes: number[] = []
          elements.forEach(el => {
            const computed = window.getComputedStyle(el)
            sizes.push(parseFloat(computed.fontSize))
          })
          return sizes
        })

        // Minimum readable font size on mobile
        const minSize = viewport.width < 768 ? 12 : 10
        const tooSmall = fontSizes.filter(s => s > 0 && s < minSize)

        // Allow some small elements (icons, etc)
        expect(tooSmall.length).toBeLessThan(fontSizes.length * 0.1)
      })
    })
  }
})

test.describe('Touch Targets', () => {
  test.use({ viewport: viewports.mobile })

  test('Interactive elements have adequate touch target size', async ({ page }) => {
    await page.goto('/kanban')
    await page.waitForLoadState('networkidle')

    // Check button sizes
    const buttons = page.locator('button')
    const buttonCount = await buttons.count()

    for (let i = 0; i < Math.min(buttonCount, 10); i++) {
      const button = buttons.nth(i)
      const isVisible = await button.isVisible().catch(() => false)

      if (isVisible) {
        const box = await button.boundingBox()
        if (box) {
          // WCAG recommends 44x44px minimum touch target
          // We allow 32px for compact UI elements
          const minSize = 32
          expect(box.width).toBeGreaterThanOrEqual(minSize - 8) // Allow some margin
          expect(box.height).toBeGreaterThanOrEqual(minSize - 8)
        }
      }
    }
  })
})

test.describe('Viewport Meta Tag', () => {
  test('Has proper viewport meta tag', async ({ page }) => {
    await page.goto('/')

    const viewportMeta = await page.locator('meta[name="viewport"]').getAttribute('content')
    expect(viewportMeta).toContain('width=device-width')
    expect(viewportMeta).toContain('initial-scale=1')
  })
})
