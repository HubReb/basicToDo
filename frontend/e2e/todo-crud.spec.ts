import { test, expect } from '@playwright/test';

import { deleteAllTodos } from './cleanup';

test.describe('Todo CRUD Operations', () => {
  test.beforeEach(async ({ page, request }) => {
    // Clean up test database before each test
    await deleteAllTodos(request);

    await page.goto('/');
  });

  test('should create a new todo', async ({ page }) => {
    // Find the input field and type a todo
    const input = page.getByPlaceholder('Add a todo item');
    await input.fill('Buy groceries');

    // Submit the form
    await input.press('Enter');

    // Wait for the todo to appear in the list
    await expect(page.getByText('Buy groceries')).toBeVisible();

    // Verify success toast appears
    await expect(page.getByText('Todo created')).toBeVisible();
  });

  test('should update an existing todo', async ({ page }) => {
    // First, create a todo
    const input = page.getByPlaceholder('Add a todo item');
    await input.fill('Original todo');
    await input.press('Enter');

    // Wait for todo to appear
    await expect(page.getByText('Original todo')).toBeVisible();

    // Click edit button
    await page.getByRole('button', { name: 'Edit' }).first().click();

    // Update the todo
    const editInput = page.getByPlaceholder('Edit todo');
    await editInput.fill('Updated todo');

    // Click save
    await page.getByRole('button', { name: 'Save' }).click();

    // Verify success toast appears immediately (before it disappears)
    await expect(page.getByText('Todo updated')).toBeVisible({ timeout: 3000 });

    // Verify updated todo appears
    await expect(page.getByText('Updated todo')).toBeVisible();

    // Verify original todo is gone
    await expect(page.getByText('Original todo')).not.toBeVisible();
  });

  test('should confirm a delete only after the server answers', async ({ page }) => {
    // Create a todo
    const input = page.getByPlaceholder('Add a todo item');
    await input.fill('Todo to delete');
    await input.press('Enter');
    await expect(page.getByText('Todo to delete')).toBeVisible();

    // Hold the DELETE request until released (Q6.9)
    let release: () => void = () => {};
    const released = new Promise<void>((resolve) => {
      release = resolve;
    });
    await page.route('**/todo/*', async (route) => {
      if (route.request().method() !== 'DELETE') {
        await route.fallback();
        return;
      }
      await released;
      await route.continue();
    });
    page.on('dialog', dialog => dialog.accept());

    await page.getByRole('button', { name: 'Delete Todo' }).first().click();

    // Removed at once, but not confirmed while the server has not answered
    await expect(page.getByText('Todo to delete')).not.toBeVisible();
    await page.waitForTimeout(1000);
    await expect(page.getByText('Todo deleted')).toHaveCount(0);

    release();
    await expect(page.getByText('Todo deleted')).toBeVisible({ timeout: 3000 });
    await expect(page.getByText('Todo to delete')).not.toBeVisible();
  });

  test('should show a failed delete and keep the todo', async ({ page }) => {
    const input = page.getByPlaceholder('Add a todo item');
    await input.fill('Todo to keep');
    await input.press('Enter');
    await expect(page.getByText('Todo to keep')).toBeVisible();

    await page.route('**/todo/*', async (route) => {
      if (route.request().method() !== 'DELETE') {
        await route.fallback();
        return;
      }
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal error' }),
      });
    });
    page.on('dialog', dialog => dialog.accept());

    await page.getByRole('button', { name: 'Delete Todo' }).first().click();

    await expect(page.getByText('Failed to delete todo')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('API Error 500: Internal error')).toBeVisible();
    await expect(page.getByText('Todo deleted')).toHaveCount(0);
    await expect(page.getByText('Todo to keep')).toBeVisible();
  });

  test('should cancel todo edit', async ({ page }) => {
    // Create a todo
    const input = page.getByPlaceholder('Add a todo item');
    await input.fill('Original todo');
    await input.press('Enter');

    // Wait for todo to appear
    await expect(page.getByText('Original todo')).toBeVisible();

    // Click edit
    await page.getByRole('button', { name: 'Edit' }).first().click();

    // Change the text
    const editInput = page.getByPlaceholder('Edit todo');
    await editInput.fill('Changed text');

    // Click cancel
    await page.getByRole('button', { name: 'Cancel' }).click();

    // Verify original todo is still there
    await expect(page.getByText('Original todo')).toBeVisible();

    // Verify changed text is not saved
    await expect(page.getByText('Changed text')).not.toBeVisible();
  });
});
