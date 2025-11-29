import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test.beforeEach(async ({ request }) => {
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

    // Wait a bit for React to render
    await page.waitForTimeout(2000);

    // Try different selectors
    const input1 = page.getByPlaceholder('Add a todo item');
    const input2 = page.locator('input[type="text"]');
    const input3 = page.locator('input');

    console.log('Input 1 count:', await input1.count());
    console.log('Input 2 count:', await input2.count());
    console.log('Input 3 count:', await input3.count());

    // Take screenshot
    await page.screenshot({ path: 'test-results/finding-input.png' });
  });
});
