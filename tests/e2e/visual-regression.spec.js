import { test, expect } from '@playwright/test';

test.describe('📸 Visual Regression Tests', () => {

  test('homepage visual regression test - desktop', async ({ page }) => {
    await page.goto('/');

    // Wait for all content to load
    await page.waitForLoadState('networkidle');

    // Take full page screenshot
    await expect(page).toHaveScreenshot('homepage-desktop.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('homepage visual regression test - mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Wait for all content to load
    await page.waitForLoadState('networkidle');

    // Take full page screenshot
    await expect(page).toHaveScreenshot('homepage-mobile.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('homepage visual regression test - tablet', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    // Wait for all content to load
    await page.waitForLoadState('networkidle');

    // Take full page screenshot
    await expect(page).toHaveScreenshot('homepage-tablet.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('individual sections visual test', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Test header section
    await expect(page.locator('.header')).toHaveScreenshot('header-section.png');

    // Test features section
    await expect(page.locator('.features')).toHaveScreenshot('features-section.png');

    // Test system configuration section
    await expect(page.locator('.setup-info').first()).toHaveScreenshot('system-config-section.png');

    // Test status section
    await expect(page.locator('.status')).toHaveScreenshot('status-section.png');
  });

  test('dark mode compatibility visual test', async ({ page }) => {
    await page.goto('/');

    // Add dark mode preference
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.waitForLoadState('networkidle');

    // Take screenshot with dark mode
    await expect(page).toHaveScreenshot('homepage-dark-mode.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('print media visual test', async ({ page }) => {
    await page.goto('/');

    // Emulate print media
    await page.emulateMedia({ media: 'print' });
    await page.waitForLoadState('networkidle');

    // Take screenshot for print version
    await expect(page).toHaveScreenshot('homepage-print.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('hover state visual test', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Test GitHub button hover state
    const githubLink = page.locator('.github-link');
    await githubLink.hover();

    // Take screenshot of hovered state
    await expect(githubLink).toHaveScreenshot('github-button-hover.png');
  });

  test('accessibility high contrast visual test', async ({ page }) => {
    await page.goto('/');

    // Emulate high contrast preference
    await page.emulateMedia({
      colorScheme: 'dark',
      reducedMotion: 'reduce'
    });

    await page.waitForLoadState('networkidle');

    // Take screenshot with accessibility preferences
    await expect(page).toHaveScreenshot('homepage-high-contrast.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });
});

test.describe('🎨 Component-Level Visual Tests', () => {

  test('code blocks visual consistency', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Test all code blocks for visual consistency
    const codeBlocks = page.locator('.code-block');
    const count = await codeBlocks.count();

    for (let i = 0; i < count; i++) {
      await expect(codeBlocks.nth(i)).toHaveScreenshot(`code-block-${i}.png`);
    }
  });

  test('feature list items visual consistency', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Test feature list visual appearance
    await expect(page.locator('.features ul')).toHaveScreenshot('features-list.png');
  });

  test('setup info cards visual consistency', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Test each setup info card
    const setupCards = page.locator('.setup-info');
    const count = await setupCards.count();

    for (let i = 0; i < count; i++) {
      await expect(setupCards.nth(i)).toHaveScreenshot(`setup-card-${i}.png`);
    }
  });

  test('gradient background visual test', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Test the background gradient
    await expect(page.locator('body')).toHaveScreenshot('background-gradient.png', {
      clip: { x: 0, y: 0, width: 1200, height: 800 }
    });
  });
});

test.describe('🌍 Cross-Platform Visual Tests', () => {

  const viewports = [
    { name: 'iPhone-SE', width: 375, height: 667 },
    { name: 'iPhone-12', width: 390, height: 844 },
    { name: 'iPad', width: 768, height: 1024 },
    { name: 'Desktop-HD', width: 1920, height: 1080 },
    { name: 'Desktop-4K', width: 3840, height: 2160 }
  ];

  viewports.forEach(viewport => {
    test(`visual consistency on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height
      });

      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Take screenshot for this viewport
      await expect(page).toHaveScreenshot(`${viewport.name}-homepage.png`, {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });
});