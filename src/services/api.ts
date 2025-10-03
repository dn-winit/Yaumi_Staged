/**
 * Main API Service - Clean re-exports from organized API modules
 */

// Re-export everything from the organized API structure
export * from './api/dashboard';
export * from './api/forecast';
export * from './api/recommendedOrder';
export * from './api/salesSupervision';
export { default as apiClient } from './api/client';