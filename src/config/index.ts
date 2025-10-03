/**
 * Yaumi Analytics Platform - Frontend Configuration
 * Professional configuration with no hardcoded values
 */

export const config = {
  // API Configuration
  api: {
    baseUrl: import.meta.env.VITE_API_URL || '/api/v1',  // Use relative path as fallback
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  },
  
  // App Configuration
  app: {
    name: 'Yaumi Analytics',
    version: '2.0.0',
    description: 'Professional Analytics Platform for Yaumi',
  },
  
  // Pagination
  pagination: {
    defaultPageSize: 20,
    pageSizeOptions: [10, 20, 50, 100],
  },
  
  // Date formats
  dateFormats: {
    display: 'DD/MM/YYYY',
    api: 'YYYY-MM-DD',
  },
  
  // Chart configuration
  charts: {
    colors: {
      primary: '#3b82f6',    // Blue
      secondary: '#10b981',  // Green
      success: '#22c55e',    // Light Green
      warning: '#f59e0b',    // Orange
      danger: '#ef4444',     // Red
      info: '#6366f1',       // Indigo
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    },
  },
  
  // Feature flags (all enabled)
  features: {
    dashboard: true,
    forecast: true,
    recommendedOrder: true,
    salesSupervision: true,
  },
  
  // API Endpoints
  endpoints: {
    dashboard: {
      summary: '/dashboard/summary',
      trends: '/dashboard/trends',
      topItems: '/dashboard/top-items',
      categoryPerformance: '/dashboard/category-performance',
      customerInsights: '/dashboard/customer-insights',
      filterOptions: '/dashboard/filter-options',
      data: '/dashboard/dashboard-data',
      historicalAverages: '/dashboard/historical-averages',
    },
    forecast: {
      predictions: '/forecast/predictions',
      accuracy: '/forecast/accuracy-metrics',
      trends: '/forecast/trend-analysis',
      seasonal: '/forecast/seasonal-patterns',
      filterOptions: '/forecast/forecast-filter-options',
      data: '/forecast/forecast-data',
    },
    recommendedOrder: {
      generate: '/recommended-order/generate-recommendations',
      list: '/recommended-order/list',
      history: '/recommended-order/history',
      availableDates: '/recommended-order/available-dates',
      filterOptions: '/recommended-order/filter-options',
      data: '/recommended-order/get-recommendations-data',
    },
    salesSupervision: {
      initSession: '/sales-supervision/init-session',
      processVisit: '/sales-supervision/process-visit',
      sessionSummary: '/sales-supervision/session-summary',
      endSession: '/sales-supervision/end-session',
      activeSessions: '/sales-supervision/active-sessions',
      filterOptions: '/sales-supervision/filter-options',
      data: '/sales-supervision/get-sales-data',
    },
  },
};

export default config;