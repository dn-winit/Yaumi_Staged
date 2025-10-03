/**
 * Dashboard API Service
 * All dashboard-related API calls
 */

import apiClient from './client';
import config from '../../config';
import { DashboardFilters, FilterOptions, ApiResponse, DashboardDataPoint, HistoricalAverages, HistoricalAveragesRequest } from '../../types';

const endpoints = config.endpoints.dashboard;

// Get filter options
export const getDashboardFilterOptions = async (): Promise<FilterOptions> => {
  return await apiClient.get(endpoints.filterOptions);
};

// Get dashboard data with filters
export const getDashboardData = async (filters: DashboardFilters): Promise<ApiResponse<DashboardDataPoint>> => {
  return await apiClient.post(endpoints.data, filters);
};

// Get historical averages
export const getHistoricalAverages = async (request: HistoricalAveragesRequest): Promise<HistoricalAverages> => {
  return await apiClient.post(endpoints.historicalAverages, request);
};