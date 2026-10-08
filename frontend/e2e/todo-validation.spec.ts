import { test, expect } from '@playwright/test';

import { deleteAllTodos } from './cleanup';

test.describe('Todo Validation', () => {
  test.beforeEach(async ({ page, request }) => {
    // Clean up test database before each test
    await deleteAllTodos(request);

    await page.goto('/');
  });

  test('should prevent creating empty todo', async ({ page }) => {
    const input = page.getByPlaceholder('Add a todo item');

    // Wait for page to load and check initial state (should be empty due to cleanup)
    await expect(page.getByText('No todos yet. Add one above!')).toBeVisible();

    // Try to submit empty todo
    await input.press('Enter');

    // Verify error message appears
    await expect(page.getByText('Todo title cannot be empty')).toBeVisible();

    // Verify empty state message is still visible (no todo was created)
    await expect(page.getByText('No todos yet. Add one above!')).toBeVisible();
  });

  test('should prevent creating whitespace-only todo', async ({ page }) => {
    const input = page.getByPlaceholder('Add a todo item');

    // Try to submit whitespace
    await input.fill('   ');
    await input.press('Enter');

    // Verify error message appears
    await expect(page.getByText('Todo title cannot be empty')).toBeVisible();
  });

  test('should show character limit warning', async ({ page }) => {
    const input = page.getByPlaceholder('Add a todo item');

    // Type a long string (over 205 chars to trigger the warning)
    const longText = 'a'.repeat(210);
    await input.fill(longText);

    // Verify character counter appears
    await expect(page.getByText(/characters remaining/)).toBeVisible();
  });

  test('should refuse a title over 255 characters', async ({ page }) => {
    const input = page.getByPlaceholder('Add a todo item');

    // No maxLength truncation any more (Q6.2): the form checks on submit
    await input.fill('a'.repeat(256));
    expect((await input.inputValue()).length).toBe(256);
    await input.press('Enter');

    await expect(page.getByText('Todo title cannot exceed 255 characters')).toBeVisible();
    await expect(page.getByText('No todos yet. Add one above!')).toBeVisible();
  });

  test('should accept 255 characters outside the BMP', async ({ page }) => {
    const input = page.getByPlaceholder('Add a todo item');
    // 255 code points, as the API counts them; 510 UTF-16 code units
    const title = '\u{1F600}'.repeat(255);

    await input.fill(title);
    await expect(page.getByText('0 characters remaining')).toBeVisible();
    await input.press('Enter');

    await expect(page.getByText('Todo created')).toBeVisible();
    await expect(page.getByText(title)).toBeVisible();
  });

  test('should show what the server rejected, readably', async ({ page }) => {
    const input = page.getByPlaceholder('Add a todo item');

    // A tab passes the form's checks; the API rejects it in titles (Q6.2)
    await input.fill('Tab\there');
    await input.press('Enter');

    await expect(page.getByText('Failed to create todo')).toBeVisible();
    await expect(
      page.getByText('API Error 422: title must not contain control characters')
    ).toBeVisible();
  });

  test('should clear error when user starts typing', async ({ page }) => {
    const input = page.getByPlaceholder('Add a todo item');

    // Submit empty to trigger error
    await input.press('Enter');

    // Verify error appears
    await expect(page.getByText('Todo title cannot be empty')).toBeVisible();

    // Start typing
    await input.fill('New todo');

    // Error should disappear
    await expect(page.getByText('Todo title cannot be empty')).not.toBeVisible();
  });

  test('should prevent updating todo to empty value', async ({ page }) => {
    // First create a todo
    const input = page.getByPlaceholder('Add a todo item');
    await input.fill('Test todo');
    await input.press('Enter');

    // Wait for todo to appear
    await expect(page.getByText('Test todo')).toBeVisible();

    // Click edit
    await page.getByRole('button', { name: 'Edit' }).first().click();

    // Clear the input
    const editInput = page.getByPlaceholder('Edit todo');
    await editInput.clear();

    // Try to save
    await page.getByRole('button', { name: 'Save' }).click();

    // Verify error message
    await expect(page.getByText('Todo title cannot be empty')).toBeVisible();

    // Verify save button is disabled
    const saveButton = page.getByRole('button', { name: 'Save' });
    await expect(saveButton).toBeDisabled();

    // Original todo should still exist
    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(page.getByText('Test todo')).toBeVisible();
  });

  test('should show visual error indicator on invalid input', async ({ page }) => {
    const input = page.getByPlaceholder('Add a todo item');

    // Submit empty to trigger error
    await input.press('Enter');

    // Check that input has error styling (red border)
    await expect(input).toHaveCSS('border-color', /red|rgb\(239, 68, 68\)/);
  });
});
