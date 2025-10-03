/**
 * API Service Layer - Main Export
 * Professional API integration with backend
 */

export * from './dashboard';
export * from './forecast';
export * from './recommendedOrder';
export * from './salesSupervision';

// Re-export main API client
export { default as apiClient } from './client';