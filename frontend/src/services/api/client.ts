/**
 * API Client
 * Provides a configured HTTP client with base URL, headers, and error handling
 */

import { config } from '../../config/env';
import type { ApiError } from '../../types/todo';

/**
 * Custom error class for API errors
 */
export class ApiClientError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public detail?: string
  ) {
    super(`API Error ${status}: ${detail || statusText}`);
    this.name = 'ApiClientError';
  }
}

/**
 * A readable message for an error response's detail (Q6.3). A 422 gets one
 * part per problem, without Pydantic's "Value error, " prefix, named by its
 * field unless the message already starts with it, and never with the
 * rejected input.
 */
export const formatErrorDetail = (detail: ApiError['detail'] | undefined): string | undefined => {
  if (typeof detail === 'string') {
    return detail || undefined
  }
  if (!Array.isArray(detail)) {
    return undefined
  }
  const parts = detail.flatMap((issue) => {
    if (typeof issue?.msg !== 'string') {
      return []
    }
    const message = issue.msg.replace(/^Value error, /, '')
    const field = Array.isArray(issue.loc)
      ? issue.loc.filter((part) => part !== 'body').join('.')
      : ''
    return [field && !message.startsWith(`${field} `) ? `${field}: ${message}` : message]
  })
  return parts.length > 0 ? parts.join('; ') : undefined
}

/**
 * HTTP client options
 */
interface RequestOptions extends RequestInit {
  params?: Record<string, string | number>;
}

/**
 * API Client class
 */
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * Build URL with query parameters
   */
  private buildUrl(endpoint: string, params?: Record<string, string | number>): string {
    const url = new URL(endpoint, this.baseUrl);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, String(value));
      });
    }

    return url.toString();
  }

  /**
   * Handle API response and errors
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorDetail = response.statusText;

      try {
        const errorBody = await response.json() as ApiError;
        errorDetail = formatErrorDetail(errorBody.detail) || errorDetail;
      } catch {
        // If response body is not JSON, use statusText
      }

      throw new ApiClientError(response.status, response.statusText, errorDetail);
    }

    return response.json();
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params);

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options?.headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params);

    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options?.headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params);

    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    return this.handleResponse<T>(response);
  }
}

// Export singleton instance
export const apiClient = new ApiClient(config.apiBaseUrl);
