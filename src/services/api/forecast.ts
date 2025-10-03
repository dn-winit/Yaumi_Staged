/**
 * Forecast API Service
 * All forecast-related API calls
 */

import apiClient from './client';
import config from '../../config';
import { ForecastFilters, FilterOptions, ApiResponse, ForecastDataPoint } from '../../types';

const endpoints = config.endpoints.forecast;

export const forecastAPI = {
  // Get forecast predictions
  getPredictions: async (routeCode?: number, itemCode?: string, daysAhead: number = 7) => {
    return await apiClient.get(endpoints.predictions, {
      params: { route_code: routeCode, item_code: itemCode, days_ahead: daysAhead }
    });
  },

  // Get accuracy metrics
  getAccuracyMetrics: async (routeCode?: number, daysBack: number = 30) => {
    return await apiClient.get(endpoints.accuracy, {
      params: { route_code: routeCode, days_back: daysBack }
    });
  },

  // Get trend analysis
  getTrendAnalysis: async (routeCode?: number, itemCode?: string) => {
    return await apiClient.get(endpoints.trends, {
      params: { route_code: routeCode, item_code: itemCode }
    });
  },

  // Get seasonal patterns
  getSeasonalPatterns: async (routeCode?: number, itemCode?: string) => {
    return await apiClient.get(endpoints.seasonal, {
      params: { route_code: routeCode, item_code: itemCode }
    });
  },

  // Get filter options
  getFilterOptions: async (): Promise<FilterOptions> => {
    return await apiClient.get(endpoints.filterOptions);
  },

  // Get forecast data with filters
  getForecastData: async (filters: ForecastFilters): Promise<ApiResponse<ForecastDataPoint>> => {
    return await apiClient.post(endpoints.data, filters);
  },
};

// Maintain backward compatibility
export const getForecastFilterOptions = forecastAPI.getFilterOptions;
export const getForecastData = forecastAPI.getForecastData;