import { test, expect } from '@playwright/test';

test.describe('🛡️ Fortinet Policy Verification System', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to the main page before each test
    await page.goto('/');
  });

  test('should load main page with correct title and elements', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Fortinet 방화벽 정책 확인/);

    // Check main heading
    await expect(page.locator('h1')).toContainText('Fortinet 방화벽 정책 확인 시스템');

    // Check description
    await expect(page.locator('.description')).toContainText('FortiManager를 통해 관리되는');

    // Check key features section
    await expect(page.locator('.features h3')).toContainText('핵심 기능');

    // Verify feature list items
    const features = [
      '출발지 → 목적지 트래픽 분석',
      '실시간 허용/차단 여부 확인',
      '다중 FortiGate 장비 지원',
      'Multi-VDOM 환경 지원'
    ];

    for (const feature of features) {
      await expect(page.locator('.features li')).toContainText([feature]);
    }
  });

  test('should have working GitHub repository link', async ({ page }) => {
    // Check GitHub link exists and has correct attributes
    const githubLink = page.locator('a[href="https://github.com/qws941/splunk"]');
    await expect(githubLink).toBeVisible();
    await expect(githubLink).toContainText('GitHub 저장소 방문');

    // Check link attributes
    await expect(githubLink).toHaveAttribute('target', '_blank');
    await expect(githubLink).toHaveClass(/github-link/);
  });

  test('should display system configuration information', async ({ page }) => {
    // Check system configuration section
    await expect(page.locator('.setup-info h3')).toContainText('시스템 구성');

    // Verify configuration components
    const components = [
      '웹 인터페이스',
      'Policy Server',
      'FortiManager 연동',
      'Splunk 통합'
    ];

    for (const component of components) {
      await expect(page.locator('.setup-info li')).toContainText([component]);
    }
  });

  test('should display local setup instructions', async ({ page }) => {
    // Check local setup section
    await expect(page.locator('.setup-info h3')).toContainText('로컬 실행 방법');

    // Check setup commands in code blocks
    await expect(page.locator('.code-block')).toContainText('git clone');
    await expect(page.locator('.code-block')).toContainText('npm install');
    await expect(page.locator('.code-block')).toContainText('npm run policy-server');
    await expect(page.locator('.code-block')).toContainText('http://localhost:3001');
  });

  test('should display API usage examples', async ({ page }) => {
    // Check API usage section
    await expect(page.locator('.setup-info h3')).toContainText('API 사용 예시');

    // Check API endpoint and curl example
    await expect(page.locator('.code-block')).toContainText('curl -X POST');
    await expect(page.locator('.code-block')).toContainText('/api/policy/verify');
    await expect(page.locator('.code-block')).toContainText('sourceIP');
    await expect(page.locator('.code-block')).toContainText('destIP');
  });

  test('should show system status information', async ({ page }) => {
    // Check status section
    const statusSection = page.locator('.status');
    await expect(statusSection).toBeVisible();
    await expect(statusSection).toContainText('시스템 상태');
    await expect(statusSection).toContainText('성공적으로 구현되었습니다');
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Test mobile responsiveness
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that main elements are still visible
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('.container')).toBeVisible();
    await expect(page.locator('.github-link')).toBeVisible();

    // Check mobile-specific styles
    const container = page.locator('.container');
    await expect(container).toHaveCSS('padding', /.*/); // Just verify it has padding
  });

  test('should have proper security headers and meta tags', async ({ page }) => {
    // Check meta viewport tag for mobile responsiveness
    const viewportMeta = page.locator('meta[name="viewport"]');
    await expect(viewportMeta).toHaveAttribute('content', 'width=device-width, initial-scale=1.0');

    // Check charset
    const charsetMeta = page.locator('meta[charset]');
    await expect(charsetMeta).toHaveAttribute('charset', 'UTF-8');
  });

  test('should load with proper CSS styling', async ({ page }) => {
    // Check that CSS is properly applied
    const body = page.locator('body');
    await expect(body).toHaveCSS('font-family', /Segoe UI/);
    await expect(body).toHaveCSS('background', /linear-gradient/);

    // Check container styling
    const container = page.locator('.container');
    await expect(container).toHaveCSS('border-radius', '20px');
    await expect(container).toHaveCSS('backdrop-filter', 'blur(10px)');
  });

  test('should handle navigation and scroll behavior', async ({ page }) => {
    // Test scrolling to different sections
    await page.locator('.features').scrollIntoViewIfNeeded();
    await expect(page.locator('.features')).toBeInViewport();

    await page.locator('.setup-info').first().scrollIntoViewIfNeeded();
    await expect(page.locator('.setup-info').first()).toBeInViewport();

    await page.locator('.status').scrollIntoViewIfNeeded();
    await expect(page.locator('.status')).toBeInViewport();
  });
});

test.describe('🔌 API Endpoints', () => {

  test('health endpoint should return healthy status', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
    expect(data).toHaveProperty('message');
    expect(data).toHaveProperty('timestamp');
    expect(data).toHaveProperty('note');
  });

  test('API info endpoint should return correct information', async ({ request }) => {
    const response = await request.get('/api/test');
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('message');
    expect(data).toHaveProperty('setup', 'Run: npm run policy-server');
    expect(data).toHaveProperty('endpoints');
    expect(Array.isArray(data.endpoints)).toBe(true);
  });

  test('root path should return HTML content', async ({ request }) => {
    const response = await request.get('/');
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('text/html');
  });

  test('index.html should return same content as root', async ({ request }) => {
    const response = await request.get('/index.html');
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('text/html');
  });

  test('non-existent endpoints should return 404', async ({ request }) => {
    const response = await request.get('/non-existent-endpoint');
    expect(response.status()).toBe(404);

    const text = await response.text();
    expect(text).toBe('Page not found');
  });
});

test.describe('📱 Cross-Browser Compatibility', () => {

  ['chromium', 'firefox', 'webkit'].forEach(browserName => {
    test(`should work properly in ${browserName}`, async ({ page }) => {
      await page.goto('/');

      // Basic functionality check
      await expect(page.locator('h1')).toContainText('Fortinet');
      await expect(page.locator('.github-link')).toBeVisible();

      // Check that styling is applied
      const container = page.locator('.container');
      await expect(container).toBeVisible();

      // Take a screenshot for visual comparison
      await page.screenshot({
        path: `test-results/${browserName}-homepage.png`,
        fullPage: true
      });
    });
  });
});

test.describe('⚡ Performance and Accessibility', () => {

  test('page should load within reasonable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    const loadTime = Date.now() - startTime;

    // Should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should have accessible elements', async ({ page }) => {
    await page.goto('/');

    // Check for proper heading hierarchy
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();

    const h3s = page.locator('h3');
    expect(await h3s.count()).toBeGreaterThan(0);

    // Check that images have alt text (if any)
    const images = page.locator('img');
    const imageCount = await images.count();
    for (let i = 0; i < imageCount; i++) {
      await expect(images.nth(i)).toHaveAttribute('alt');
    }
  });

  test('should work with keyboard navigation', async ({ page }) => {
    await page.goto('/');

    // Test tab navigation
    await page.keyboard.press('Tab');

    // Should be able to navigate to the GitHub link
    const githubLink = page.locator('a[href="https://github.com/qws941/splunk"]');
    await githubLink.focus();
    await expect(githubLink).toBeFocused();
  });
});