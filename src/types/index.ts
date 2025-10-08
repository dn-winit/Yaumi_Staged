export interface DashboardFilters {
  routeCodes: string[];  // Changed to support multiple routes
  itemCodes?: string[];  // Changed to support multiple items
  period: 'Daily' | 'Weekly' | 'Monthly';
  startDate: string;
  endDate: string;
}

export interface ForecastFilters {
  routeCodes: string[];  // Support multiple routes
  itemCodes?: string[];  // Support multiple items
  period: 'Daily' | 'Weekly' | 'Monthly';
}

export interface ItemBreakdown {
  itemCode: string;
  itemName: string;
  actual: number;
  predicted: number;
}

export interface DashboardDataPoint {
  date: string;
  route: string;
  item: string;
  actual: number;
  predicted: number;
  routeCode: string;
  itemCode: string;
  itemBreakdown?: ItemBreakdown[];  // For expandable rows and chart breakdown
}

export interface ForecastDataPoint {
  date: string;
  route: string;
  item: string;
  predicted: number;
  routeCode: string;
  itemCode: string;
  itemBreakdown?: ItemBreakdown[];  // For expandable rows
}

export interface DailyAverages {
  last_1_week: number;
  last_1_month: number;
  last_3_months: number;
  last_6_months: number;
  last_1_year: number;
}

export interface WeeklyAverages {
  last_1_week: number;
  last_3_weeks: number;
  last_6_weeks: number;
  last_1_year: number;
}

export interface MonthlyAverages {
  last_1_month: number;
  last_3_months: number;
  last_6_months: number;
  last_1_year: number;
}

export interface HistoricalAveragesRequest {
  route_code: string;
  item_code?: string;
  item_codes?: string[];  // For multiple items
  date: string;
  period: 'Daily' | 'Weekly' | 'Monthly';
}

export interface HistoricalAverages {
  period: 'Daily' | 'Weekly' | 'Monthly';
  data: DailyAverages | WeeklyAverages | MonthlyAverages;
}

export interface FilterOption {
  code: string;
  name: string;
}

export interface FilterOptions {
  routes: FilterOption[];
  customers: FilterOption[];
  items: FilterOption[];
}

export interface PaginationInfo {
  current_page: number;
  page_size: number;
  total_pages: number;
  total_records: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface RecommendedOrderFilters {
  routeCodes: string[];  // Support multiple routes
  customerCodes?: string[];  // Support multiple customers
  itemCodes?: string[];  // Support multiple items
  date: string;
}

export interface CustomerItemBreakdown {
  trxDate: string;
  routeCode: string;
  itemCode: string;
  itemName: string;
  actualQuantity: number;
  recommendedQuantity: number;
  tier: string;
  vanLoad: number;
  probabilityPercent: number;
  avgQuantityPerVisit: number;
  daysSinceLastPurchase: number;
  purchaseCycleDays: number;
  frequencyPercent: number;
  urgencyScore: number;
}

export interface RecommendedOrderDataPoint {
  trxDate: string;
  routeCode: string;
  customerCode: string;
  itemCode: string;
  itemName: string;
  actualQuantity: number;
  recommendedQuantity: number;
  tier: string;
  vanLoad: number;
  probabilityPercent: number;
  avgQuantityPerVisit: number;
  daysSinceLastPurchase: number;
  purchaseCycleDays: number;
  frequencyPercent: number;
  urgencyScore: number;
  customerBreakdown?: CustomerItemBreakdown[];  // For collapsible customer rows
}

export interface GenerateRecommendationsRequest {
  date: string;  // Expected format: YYYY-MM-DD
  routeCode?: string;  // Optional route code parameter
}

export interface ApiResponse<T> {
  chart_data: T[];
  table_data: T[];
  status?: string;
  message?: string;
}