/**
 * Environment configuration for API URLs.
 * Supports dev, staging, and production environments.
 * @module config/env
 */

type Environment = 'development' | 'staging' | 'production';

/** Detect current environment based on hostname or VITE_ENV variable */
function detectEnvironment(): Environment {
  const viteEnv = import.meta.env.VITE_ENV as string | undefined;
  if (viteEnv === 'staging') return 'staging';
  if (viteEnv === 'production') return 'production';
  
  // Auto-detect from hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') return 'development';
    if (hostname.includes('staging') || hostname.includes('dev')) return 'staging';
    return 'production';
  }
  
  return 'development';
}

/** API base URLs for each environment */
const API_BASE_URLS: Record<Environment, string> = {
  development: import.meta.env.VITE_API_URL || '',
  staging: import.meta.env.VITE_API_URL || '',
  production: import.meta.env.VITE_API_URL || '',
};

export const environment = detectEnvironment();
export const API_BASE_URL = API_BASE_URLS[environment];

/** Check if we're running in development mode */
export const isDevelopment = environment === 'development';

/** Check if we're running in production mode */
export const isProduction = environment === 'production';

/** API timeout in milliseconds */
export const API_TIMEOUT = 30000;

/** Retry configuration */
export const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000, // ms
};