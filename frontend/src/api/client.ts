/**
 * Centralized API client with auth headers, base URL config, and error handling.
 * Uses axios for HTTP requests with interceptors for auth injection.
 * @module api/client
 */

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL, API_TIMEOUT, RETRY_CONFIG } from '../config/env';

/** API Error response structure */
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  request_id?: string;
}

/** Auth token storage key */
const TOKEN_KEY = 'solfoundry_auth_token';

/** Get stored auth token */
export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/** Set auth token in storage */
export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/** Clear auth token from storage */
export function clearAuthToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/** Create configured axios instance */
function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor: inject auth token if available
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = getAuthToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor: handle errors uniformly
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ApiError>) => {
      const apiError: ApiError = {
        message: error.message || 'An unexpected error occurred',
        status: error.response?.status,
      };

      if (error.response?.data) {
        apiError.message = error.response.data.message || apiError.message;
        apiError.code = error.response.data.code;
        apiError.request_id = error.response.data.request_id;
      }

      // Handle 401 Unauthorized - clear token and redirect to login
      if (error.response?.status === 401) {
        clearAuthToken();
        // Only redirect if not already on auth pages
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/auth')) {
          window.location.href = '/auth/login';
        }
      }

      return Promise.reject(apiError);
    }
  );

  return client;
}

/** Singleton API client instance */
export const apiClient = createApiClient();

/** Retry wrapper for API calls with exponential backoff */
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = RETRY_CONFIG.maxRetries,
  delay: number = RETRY_CONFIG.retryDelay
): Promise<T> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry on client errors (4xx)
      if ((error as ApiError).status && (error as ApiError).status! < 500) {
        throw error;
      }
      
      // Wait before retrying (exponential backoff)
      if (attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, delay * Math.pow(2, attempt)));
      }
    }
  }
  
  throw lastError;
}

/** Generic fetch wrapper for when axios is not needed */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = API_BASE_URL + endpoint;
  const token = getAuthToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const error: ApiError = {
      message: `HTTP ${response.status}: ${response.statusText}`,
      status: response.status,
    };
    
    try {
      const data = await response.json();
      error.message = data.message || error.message;
      error.code = data.code;
      error.request_id = data.request_id;
    } catch {
      // Ignore JSON parse errors
    }
    
    throw error;
  }
  
  return response.json();
}

export default apiClient;