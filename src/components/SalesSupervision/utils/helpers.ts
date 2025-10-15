/**
 * Utility functions for Sales Supervision
 */

/**
 * API call with timeout wrapper
 */
export const apiCallWithTimeout = async <T,>(
  apiCall: Promise<T>,
  timeoutMs: number = 60000
): Promise<T> => {
  return Promise.race([
    apiCall,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error('Request timeout')), timeoutMs)
    )
  ]);
};

/**
 * Get customer name with fallback
 */
export const getCustomerName = (customer: { customerCode: string; customerName?: string }): string => {
  return customer.customerName || `Customer ${customer.customerCode}`;
};

/**
 * Calculate completion percentage
 */
export const calculateCompletionPercentage = (completed: number, total: number): number => {
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
};

/**
 * Format number with commas
 */
export const formatNumber = (num: number): string => {
  return num.toLocaleString();
};

/**
 * Get tier badge color class
 */
export const getTierColor = (tier: string): string => {
  switch (tier) {
    case 'CRITICAL':
      return 'bg-red-100 text-red-800';
    case 'HIGH':
      return 'bg-orange-100 text-orange-800';
    case 'MEDIUM':
      return 'bg-yellow-100 text-yellow-800';
    case 'LOW':
      return 'bg-green-100 text-green-800';
    case 'NEW_CUSTOMER':
      return 'bg-blue-100 text-blue-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

/**
 * Get score color class
 */
export const getScoreColor = (score: number): string => {
  if (score >= 80) return 'text-green-600';
  if (score >= 60) return 'text-yellow-600';
  if (score >= 40) return 'text-orange-600';
  return 'text-red-600';
};

/**
 * Get score background color class
 */
export const getScoreBgColor = (score: number): string => {
  if (score >= 80) return 'bg-green-100';
  if (score >= 60) return 'bg-yellow-100';
  if (score >= 40) return 'bg-orange-100';
  return 'bg-red-100';
};

/**
 * Format date for display
 */
export const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch {
    return dateString;
  }
};

/**
 * Check if LLM call should be throttled (max 1 call per 3 seconds per customer)
 */
export const shouldThrottleLLMCall = (
  customerCode: string,
  lastCallTimes: {[key: string]: number}
): boolean => {
  const THROTTLE_MS = 3000;
  const lastCall = lastCallTimes[customerCode];
  if (!lastCall) return false;

  const timeSinceLastCall = Date.now() - lastCall;
  return timeSinceLastCall < THROTTLE_MS;
};

/**
 * Calculate accuracy percentage
 */
export const calculateAccuracy = (actual: number, recommended: number): number => {
  if (recommended === 0) return actual === 0 ? 100 : 0;
  const accuracy = (actual / recommended) * 100;
  // Perfect zone: 75-120%
  if (accuracy >= 75 && accuracy <= 120) return 100;
  // Below 75%
  if (accuracy < 75) return Math.max(0, (accuracy / 75) * 100);
  // Above 120%
  if (accuracy >= 200) return 0;
  return Math.max(0, 100 - ((accuracy - 120) / 80 * 100));
};
