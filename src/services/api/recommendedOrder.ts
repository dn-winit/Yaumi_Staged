/**
 * Recommended Order API Service - Optimized
 * Only essential API calls - no redundancy
 */

import apiClient from './client';
import config from '../../config';
import { RecommendedOrderFilters, FilterOptions, ApiResponse, RecommendedOrderDataPoint } from '../../types';

const endpoints = config.endpoints.recommendedOrder;

/**
 * Main endpoint - Get recommendations with auto-generation
 * - Fetches from DB if exists (instant)
 * - Auto-generates if missing (30-60s first time)
 * - Applies filters and returns data
 */
export const getRecommendedOrderData = async (
  filters: RecommendedOrderFilters
): Promise<ApiResponse<RecommendedOrderDataPoint>> => {
  return await apiClient.post(endpoints.data, filters, {
    timeout: 120000 // 2 minutes for potential generation
  });
};

/**
 * Get filter options for dropdowns
 * - Requires date parameter
 * - Optional route_code and customer_code for cascading filters
 */
export const getRecommendedOrderFilterOptions = async (
  date: string,
  routeCode?: string,
  customerCode?: string
): Promise<FilterOptions> => {
  const params = new URLSearchParams();
  params.append('date', date);
  if (routeCode && routeCode !== 'All') {
    params.append('route_code', routeCode);
  }
  if (customerCode && customerCode !== 'All') {
    params.append('customer_code', customerCode);
  }

  return await apiClient.get(`${endpoints.filterOptions}?${params.toString()}`);
};

// Export as default object for easy import
export const recommendedOrderAPI = {
  getData: getRecommendedOrderData,
  getFilterOptions: getRecommendedOrderFilterOptions,
};
