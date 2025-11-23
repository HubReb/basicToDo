/**
 * Todo API Service
 * Provides all Todo-related API operations
 * Single source of truth for all Todo API endpoints
 */

import { apiClient } from './client';
import type {
  Todo,
  TodoCreateRequest,
  TodoUpdateRequest,
  TodoResponse,
  GetTodoResponse,
  TodoListResponse,
  DeleteTodoResponse,
} from '../../types/todo';

/**
 * Todo API service
 */
export class TodoApi {
  /**
   * Create a new todo
   * POST /todo
   */
  async create(data: TodoCreateRequest): Promise<Todo> {
    const response = await apiClient.post<TodoResponse>('/todo', data);
    return response.todo_entry;
  }

  /**
   * Get a single todo by ID
   * GET /todo/{todo_id}
   */
  async getById(todoId: string): Promise<Todo> {
    const response = await apiClient.get<GetTodoResponse>(`/todo/${todoId}`);
    return response.todo_entry;
  }

  /**
   * Update a todo
   * PUT /todo/{todo_id}
   */
  async update(todoId: string, data: TodoUpdateRequest): Promise<Todo> {
    const response = await apiClient.put<TodoResponse>(`/todo/${todoId}`, data);
    return response.todo_entry;
  }

  /**
   * Delete a todo (soft delete)
   * DELETE /todo/{todo_id}
   */
  async delete(todoId: string): Promise<DeleteTodoResponse> {
    return apiClient.delete<DeleteTodoResponse>(`/todo/${todoId}`);
  }

  /**
   * List all todos with pagination
   * GET /todo?limit={limit}&page={page}
   */
  async list(limit: number = 10, page: number = 1): Promise<TodoListResponse> {
    return apiClient.get<TodoListResponse>('/todo', {
      params: { limit, page },
    });
  }

  /**
   * Toggle todo done status
   * PUT /todo/{todo_id}
   */
  async toggleDone(todoId: string, done: boolean): Promise<Todo> {
    const response = await apiClient.put<TodoResponse>(`/todo/${todoId}`, { done });
    return response.todo_entry;
  }
}

// Export singleton instance
export const todoApi = new TodoApi();
