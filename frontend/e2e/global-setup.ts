import { request } from '@playwright/test';

import { deleteAllTodos } from './cleanup';

async function globalSetup() {
  // Clean up test database before running tests
  const context = await request.newContext();

  try {
    await deleteAllTodos(context);
  } catch {
    console.log('Note: Could not clean database in global setup (server may not be running yet)');
  } finally {
    await context.dispose();
  }
}

export default globalSetup;
