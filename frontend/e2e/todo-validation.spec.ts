import { test, expect } from '@playwright/test';

test.describe('Todo Validation', () => {
  test.beforeEach(async ({ page, request }) => {
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

  test('should prevent exceeding character limit', async ({ page }) => {
    const input = page.getByPlaceholder('Add a todo item');

    // The maxLength attribute should prevent typing more than 255 chars
    const tooLongText = 'a'.repeat(300);
    await input.fill(tooLongText);

    // Get the actual value
    const value = await input.inputValue();

    // Should be truncated to 255
    expect(value.length).toBeLessThanOrEqual(255);
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
