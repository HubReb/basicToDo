/**
 * Type definitions for Todo entities and API contracts
 * These types match the backend Pydantic schemas
 */

/**
 * Main Todo entity - matches backend ToDoSchema
 */
export interface Todo {
  id: string;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string | null;
  deleted: boolean;
  done: boolean;
}

/**
 * Create Todo request - matches backend ToDoCreateScheme
 */
export interface TodoCreateRequest {
  id: string;
  title: string;
  description?: string | null;
}

/**
 * Update Todo request - matches backend TodoUpdateScheme
 */
export interface TodoUpdateRequest {
  title?: string;
  description?: string | null;
  done?: boolean;
}

/**
 * Base API response structure
 */
export interface ApiResponse {
  success: boolean;
}

/**
 * Single Todo response - matches backend ToDoResponse
 */
export interface TodoResponse extends ApiResponse {
  todo_entry: Todo;
}

/**
 * Get single Todo response - matches backend GetToDoResponse
 */
export interface GetTodoResponse extends ApiResponse {
  todo_entry: Todo;
}

/**
 * List Todos response - matches backend ListToDoResponse
 */
export interface TodoListResponse extends ApiResponse {
  results: number;
  todo_entries: Todo[];
}

/**
 * Delete Todo response - matches backend DeleteToDoResponse
 */
export interface DeleteTodoResponse extends ApiResponse {
  message: string;
}

/**
 * API Error response structure
 */
export interface ApiError {
  detail: string;
}
