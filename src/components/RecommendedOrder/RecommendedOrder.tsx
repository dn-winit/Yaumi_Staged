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
              { color: 'bg-indigo-600', label: 'Recommended' },
              { color: 'bg-blue-600', label: 'Actual' }
            ]
          }}
        />

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