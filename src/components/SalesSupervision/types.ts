/**
 * Type definitions for Sales Supervision module
 */

export interface FilterOption {
  code: string;
  name: string;
}

export interface DemandItem {
  itemCode: string;
  itemName: string;
  allocatedQuantity: number;
  totalQuantity: number;
  avgPrice: number;
}

export interface CustomerItem {
  itemCode: string;
  itemName: string;
  actualQuantity: number;
  recommendedQuantity: number;
  tier: string;
  probabilityPercent: number;
  urgencyScore: number;
}

export interface Customer {
  customerCode: string;
  customerName: string;
  score: number;
  coverage: number;
  accuracy: number;
  items: CustomerItem[];
  totalItems: number;
  totalRecommendedQty: number;
  totalActualQty: number;
}

export interface EditingItemState {
  customerCode: string;
  itemCode: string;
  value: string;
}

export interface CustomerAnalysisResult {
  customer_code: string;
  performance_summary: string;
  strengths: string[];
  weaknesses: string[];
  likely_reasons: string[];
  immediate_actions: string[];
  follow_up_actions: string[];
  identified_patterns: string[];
  red_flags: string[];
  performance_score: number;
  coverage?: number;
  accuracy?: number;
  total_items: number;
  skus_sold?: number;
  total_recommended: number;
  total_actual: number;
}

export interface RouteAnalysisResult {
  route_code: string;
  route_summary: string;
  high_performers: string[];
  needs_attention: string[];
  route_strengths: string[];
  route_weaknesses: string[];
  optimization_opportunities: string[];
  overstocked_items: string[];
  understocked_items: string[];
  coaching_areas: string[];
  best_practices: string[];
  date?: string;
  metrics?: {
    totalCustomers: number;
    visitedCustomers: number;
    completionRate: number;
    averageScore: number;
  };
}

export interface SessionSummary {
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

export interface SalesData {
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

export interface RefreshMessage {
  type: 'success' | 'error';
  text: string;
}

export interface ToastMessage {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}
