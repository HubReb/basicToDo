import type { APIRequestContext } from '@playwright/test';

const API = 'http://localhost:8000';

/**
 * Soft-deletes every active todo. A list page holds at most 100 todos
 * (Q6.4), so page 1 is fetched again until it comes back empty.
 */
export async function deleteAllTodos(request: APIRequestContext): Promise<void> {
  for (let round = 0; round < 1000; round++) {
    const response = await request.get(`${API}/todo?limit=100&page=1`);
    if (!response.ok()) {
      throw new Error(`Listing todos for cleanup failed: ${response.status()}`);
    }
    const data = (await response.json()) as { todo_entries: { id: string }[] };
    if (data.todo_entries.length === 0) {
      return;
    }
    await Promise.all(
      data.todo_entries.map((todo) => request.delete(`${API}/todo/${todo.id}`))
    );
  }
  throw new Error('Cleanup did not empty the todo list');
}
