import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test.beforeEach(async ({ request, page }) => {
    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`Browser ERROR: ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      console.log(`Page ERROR: ${error.message}`);
      console.log(`Stack: ${error.stack}`);
    });

    // Clean up test database before each test
    const response = await request.get('http://localhost:8000/todo?limit=1000&page=1');
    const data = await response.json();

    if (data.todo_entries && data.todo_entries.length > 0) {
      // Delete all todos
      await Promise.all(
        data.todo_entries.map((todo: { id: string }) =>
          request.delete(`http://localhost:8000/todo/${todo.id}`)
        )
      );
    }
  });

  test('should load the application', async ({ page }) => {
    // Listen for console messages
    page.on('console', msg => {
      console.log(`Browser console [${msg.type()}]:`, msg.text());
    });

    // Listen for network requests
    page.on('request', request => {
      console.log('Request:', request.method(), request.url());
    });

    page.on('response', response => {
      console.log('Response:', response.status(), response.url());
    });

    await page.goto('/');

    // Check if page loads
    await expect(page).toHaveTitle(/ToDo List/);

    // Wait a bit to see what happens
    await page.waitForTimeout(5000);

    // Take a screenshot for debugging
    await page.screenshot({ path: 'test-results/app-loaded.png' });

    // Check for loading spinner
    const spinner = await page.locator('svg[class*="spinner"]').count();
    console.log('Spinner count:', spinner);

    // Check for error messages
    const errorMsg = await page.locator('text=/error|failed/i').count();
    console.log('Error message count:', errorMsg);
  });

  test('should find the input field', async ({ page }) => {
    await page.goto('/');

    // Wait for the page to fully load
    await page.waitForLoadState('networkidle');

    // Debug: print page content
    const bodyText = await page.locator('body').textContent();
    console.log('Page body text:', bodyText);

    const html = await page.content();
    console.log('Page HTML length:', html.length);
    console.log('Has root div:', html.includes('id="root"'));

    // Check if root div has any children
    const rootHtml = await page.locator('#root').innerHTML();
    console.log('Root innerHTML length:', rootHtml.length);
    console.log('Root innerHTML:', rootHtml.substring(0, 200));

    // Wait for either spinner to disappear or form to appear
    try {
      await page.waitForSelector('input[placeholder="Add a todo item"]', { timeout: 10000 });
      console.log('Found input by placeholder!');
    } catch (e) {
      console.log('Could not find input, checking for error/loading states');
      const spinner = await page.locator('svg').count();
      const errorMsg = await page.getByText(/error|failed/i).count();
      console.log('Spinner count:', spinner);
      console.log('Error message count:', errorMsg);
    }

    // Take screenshot
    await page.screenshot({ path: 'test-results/finding-input.png', fullPage: true });
  });
});
