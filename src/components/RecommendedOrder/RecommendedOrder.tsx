import React, { useState } from 'react';
import { PageHeader, LoadingState, EmptyState } from '../common';
import RecommendedOrderChart from './RecommendedOrderChart';
import RecommendedOrderTable from './RecommendedOrderTable';
import RecommendedOrderFiltersComponent from './RecommendedOrderFilters';
import { RecommendedOrderDataPoint, RecommendedOrderFilters } from '../../types';

const RecommendedOrder: React.FC = () => {
  const [recommendedOrderData, setRecommendedOrderData] = useState<RecommendedOrderDataPoint[]>([]);
  const [currentFilters, setCurrentFilters] = useState<RecommendedOrderFilters | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshMessage(null);

    try {
      const response = await fetch('/api/v1/refresh-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await response.json();

      if (result.success) {
        setRefreshMessage({
          type: 'success',
          text: 'Data refreshed successfully!'
        });
        setTimeout(() => setRefreshMessage(null), 5000);
      } else {
        setRefreshMessage({
          type: 'error',
          text: result.message || 'Failed to refresh data'
        });
      }
    } catch (error) {
      setRefreshMessage({
        type: 'error',
        text: 'Error connecting to server'
      });
    } finally {
      setRefreshing(false);
    }
  };

  const handleFiltersSubmit = (
    filtersWithData: RecommendedOrderFilters & {
      chartData?: unknown[];
      tableData?: unknown[];
    }
  ) => {
    setLoading(true);
    try {
      const filteredData = (filtersWithData.tableData || []) as RecommendedOrderDataPoint[];
      setRecommendedOrderData(filteredData);
      setCurrentFilters(filtersWithData);
    } catch (error) {
      console.error('Error processing recommended order data:', error);
      alert('Failed to process recommended order data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="ui-page-container">
        <PageHeader
          title="Recommended Orders"
          subtitle="Intelligent order recommendations with priority tiers"
          legend={{
            items: [
              { color: 'bg-blue-600', label: 'Recommended' },
              { color: 'bg-blue-400', label: 'Actual' }
            ]
          }}
          onRefresh={handleRefresh}
          refreshing={refreshing}
        />

        {refreshMessage && (
          <div className={`mb-4 p-4 rounded-md ${
            refreshMessage.type === 'success'
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}>
            <div className="flex items-center">
              {refreshMessage.type === 'success' ? (
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              )}
              <span className="text-sm font-medium">{refreshMessage.text}</span>
            </div>
          </div>
        )}

        <RecommendedOrderFiltersComponent onFiltersSubmit={handleFiltersSubmit} />

        {loading && (
          <LoadingState
            title="Loading Order Recommendations"
            message="Generating recommendations..."
            spinnerColor="border-t-indigo-600"
          />
        )}

        {!loading && recommendedOrderData.length > 0 && (
          <div className="ui-space-y">
            <RecommendedOrderChart data={recommendedOrderData} />
            <RecommendedOrderTable data={recommendedOrderData} />
          </div>
        )}

        {!loading && currentFilters && recommendedOrderData.length === 0 && (
          <EmptyState
            title="No Recommended Order Data Found"
            message="No recommended order data matches your current filter criteria. Try adjusting your route, customer, item, or date settings."
            icon={
              <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            }
          />
        )}
      </div>
    </div>
  );
};

export default RecommendedOrder;