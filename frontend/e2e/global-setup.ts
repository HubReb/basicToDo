import { request } from '@playwright/test';

async function globalSetup() {
  // Clean up test database before running tests
  const context = await request.newContext();

  try {
    const response = await context.get('http://localhost:8000/todo?limit=1000&page=1');
    const data = await response.json();

    if (data.todo_entries && data.todo_entries.length > 0) {
      // Delete all todos
      await Promise.all(
        data.todo_entries.map((todo: { id: string }) =>
          context.delete(`http://localhost:8000/todo/${todo.id}`)
        )
      );
    }
  } catch (error) {
    console.log('Note: Could not clean database in global setup (server may not be running yet)');
  } finally {
    await context.dispose();
  }
}

export default globalSetup;
