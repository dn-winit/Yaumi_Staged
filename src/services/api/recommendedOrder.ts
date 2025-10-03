/**
 * Recommended Order API Service
 * All recommendation-related API calls
 */

import apiClient from './client';
import config from '../../config';
import { RecommendedOrderFilters, FilterOptions, ApiResponse, RecommendedOrderDataPoint, GenerateRecommendationsRequest } from '../../types';

const endpoints = config.endpoints.recommendedOrder;

export const recommendedOrderAPI = {
  // Generate recommendations
  generateRecommendations: async (
    request: GenerateRecommendationsRequest
  ): Promise<{ message?: string; generated?: boolean; recommendations_count?: number }> => {
    return (await apiClient.post(endpoints.generate, request)) as unknown as {
      message?: string;
      generated?: boolean;
      recommendations_count?: number;
    };
  },

  // Get recommendations list
  getRecommendationsList: async (routeCode: number, targetDate: string) => {
    return await apiClient.get(endpoints.list, {
      params: { route_code: routeCode, target_date: targetDate }
    });
  },

  // Get recommendation history
  getHistory: async (routeCode?: number) => {
    return await apiClient.get(endpoints.history, {
      params: { route_code: routeCode }
    });
  },

  // Get available dates for journey planning
  getAvailableDates: async (routeCode: number) => {
    return await apiClient.get(endpoints.availableDates, {
      params: { route_code: routeCode }
    });
  },

  // Get filter options
  getFilterOptions: async (): Promise<FilterOptions> => {
    return await apiClient.get(endpoints.filterOptions);
  },

  // Get recommendations data with filters
  getRecommendationsData: async (filters: RecommendedOrderFilters): Promise<ApiResponse<RecommendedOrderDataPoint>> => {
    return await apiClient.post(endpoints.data, filters);
  },
};

// Maintain backward compatibility
export const getRecommendedOrderFilterOptions = recommendedOrderAPI.getFilterOptions;
export const generateRecommendations = recommendedOrderAPI.generateRecommendations;
export const getRecommendedOrderData = recommendedOrderAPI.getRecommendationsData;