/**
 * Sales Supervision API Service
 * All supervision-related API calls
 */

import apiClient from './client';
import config from '../../config';
import { FilterOption } from '../../types';

// Type definitions for API responses
type SalesSupervisionFilters = { route_code: string; date: string };

interface DemandItem {
  itemCode: string;
  itemName: string;
  allocatedQuantity: number;
  totalQuantity: number;
  avgPrice: number;
}

interface CustomerItem {
  itemCode: string;
  itemName: string;
  actualQuantity: number;
  recommendedQuantity: number;
  tier: string;
  probabilityPercent: number;
  urgencyScore: number;
}

interface Customer {
  customerCode: string;
  customerName: string;
  score: number;
  items: CustomerItem[];
  totalItems: number;
  totalRecommendedQty: number;
  totalActualQty: number;
}

interface SalesData {
  route: string;
  date: string;
  demandSection: {
    items: DemandItem[];
    totalItems: number;
    totalAllocatedQty: number;
    totalQty: number;
  };
  recommendedOrderSection: {
    hasData: boolean;
    customers: Customer[];
    totalCustomers: number;
    avgScore: number;
  };
}

// Local types for API responses (structural typing compatible with component state)
interface SessionSummary {
  route_code: string;
  date: string;
  session_id: string;
  visited_customers: number;
  total_customers: number;
  performance_rate: number;
  redistribution_count: number;
  total_actual: number;
  total_recommended: number;
  visited_recommended: number;
  remaining_customers: number;
}

interface InitializeSessionResponse {
  session: SessionSummary;
}

interface RedistributionInfo {
  redistributed_count: number;
}

interface ProcessVisitResult {
  adjustments?: Record<string, Record<string, number>>;
  redistribution?: RedistributionInfo;
}

interface AnalysisMetrics {
  totalCustomers: number;
  visitedCustomers: number;
  completionRate: number;
  averageScore: number;
}

interface AnalysisResult {
  analysis: string;
  customer_code?: string;
  performance_score: number;
  total_items: number;
  total_recommended: number;
  total_actual: number;
  route_code?: string;
  date?: string;
  metrics?: AnalysisMetrics;
}

const endpoints = config.endpoints.salesSupervision;

export const salesSupervisionAPI = {

  // Get filter options
  getFilterOptions: async (): Promise<{ routes: FilterOption[]; dates: string[] }> => {
    return (await apiClient.get(endpoints.filterOptions)) as unknown as { routes: FilterOption[]; dates: string[] };
  },

  // Get sales data with filters
  getSalesData: async (filters: SalesSupervisionFilters): Promise<SalesData> => {
    return (await apiClient.post(endpoints.data, filters)) as unknown as SalesData;
  },

  // Initialize supervision session
  initializeDynamicSession: async (
    routeCode: string,
    date: string
  ): Promise<InitializeSessionResponse> => {
    return await apiClient.post('/sales-supervision/initialize-session', {
      route_code: routeCode,
      date: date
    });
  },

  // Process customer visit with actual sales
  processCustomerVisit: async (
    routeCode: string,
    date: string,
    customerCode: string,
    actualSales: Record<string, number>
  ): Promise<ProcessVisitResult> => {
    return await apiClient.post('/sales-supervision/process-visit', {
      route_code: routeCode,
      date: date,
      customer_code: customerCode,
      actual_sales: actualSales
    });
  },

  // Get session summary
  getDynamicSessionSummary: async (
    routeCode: string,
    date: string
  ): Promise<SessionSummary> => {
    return await apiClient.post('/sales-supervision/get-session-summary', {
      route_code: routeCode,
      date: date
    });
  },

  // Analyze individual customer performance
  analyzeCustomerPerformance: async (
    routeCode: string,
    date: string,
    customerCode: string
  ): Promise<AnalysisResult> => {
    return await apiClient.post('/sales-supervision/analyze-customer', {
      route_code: routeCode,
      date: date,
      customer_code: customerCode
    });
  },

  // Analyze customer performance with updated actual quantities
  analyzeCustomerPerformanceWithUpdates: async (
    routeCode: string,
    date: string,
    customerCode: string,
    actualQuantities: Record<string, number>
  ): Promise<AnalysisResult> => {
    return await apiClient.post('/sales-supervision/analyze-customer-with-updates', {
      route_code: routeCode,
      date: date,
      customer_code: customerCode,
      actual_quantities: actualQuantities
    });
  },

  // Analyze route performance with real visited customer data
  analyzeRoutePerformanceWithVisitedData: async (
    routeCode: string,
    date: string,
    allCustomers: Customer[],
    visitedCustomersData: Customer[]
  ): Promise<AnalysisResult> => {
    return await apiClient.post('/sales-supervision/analyze-route-with-visited-data', {
      route_code: routeCode,
      date: date,
      all_customers: allCustomers,
      visited_customers_data: visitedCustomersData
    });
  },

  // Check LLM service health
  checkLLMHealth: async () => {
    return await apiClient.get('/sales-supervision/llm-health');
  },
};

// Maintain backward compatibility
export const getSalesSupervisionFilterOptions: () => Promise<{ routes: FilterOption[]; dates: string[] }> = salesSupervisionAPI.getFilterOptions;
export const getSalesSupervisionData: (filters: SalesSupervisionFilters) => Promise<SalesData> = salesSupervisionAPI.getSalesData;