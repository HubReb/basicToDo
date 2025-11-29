import { test, expect } from '@playwright/test';

test.describe('Todo CRUD Operations', () => {
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

  test('should delete a todo', async ({ page }) => {
    // Create a todo
    const input = page.getByPlaceholder('Add a todo item');
    await input.fill('Todo to delete');
    await input.press('Enter');

    // Wait for todo to appear
    await expect(page.getByText('Todo to delete')).toBeVisible();

    // Set up dialog handler to confirm deletion
    page.on('dialog', dialog => dialog.accept());

    // Click delete button
    await page.getByRole('button', { name: 'Delete Todo' }).first().click();

    // Verify success toast appears immediately (shown before mutation in the component)
    await expect(page.getByText('Todo deleted')).toBeVisible({ timeout: 3000 });

    // Verify todo is removed
    await expect(page.getByText('Todo to delete')).not.toBeVisible();
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
