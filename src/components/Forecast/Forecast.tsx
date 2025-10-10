import React, { useState } from 'react';
import { PageHeader, LoadingState, EmptyState, Toast } from '../common';
import ForecastChart from './ForecastChart';
import ForecastTable from './ForecastTable';
import ForecastFilters from './ForecastFilters';
import { getForecastData } from '../../services/api';
import { ForecastDataPoint, ForecastFilters as ForecastFiltersType } from '../../types';

const Forecast: React.FC = () => {
  const [forecastData, setForecastData] = useState<ForecastDataPoint[]>([]);
  const [currentFilters, setCurrentFilters] = useState<ForecastFiltersType | null>(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{message: string; type: 'success' | 'error' | 'warning' | 'info'} | null>(null);

  const handleFiltersSubmit = async (filters: ForecastFiltersType) => {
    setLoading(true);
    try {
      const response = await getForecastData(filters);
      setForecastData(response.table_data);
      setCurrentFilters(filters);
    } catch (error) {
      console.error('Error fetching forecast data:', error);
      setToast({ message: 'Failed to fetch forecast data', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="ui-page-container">
        <PageHeader
          title="Demand Forecast"
          subtitle="AI-powered demand predictions across multiple time horizons"
          legend={{
            items: [
              { color: 'bg-blue-600', label: 'Predicted' }
            ]
          }}
        />

        <ForecastFilters onFiltersSubmit={handleFiltersSubmit} />

        {loading && (
          <LoadingState
            title="Loading Forecast Data"
            message="Generating demand predictions..."
            spinnerColor="border-t-blue-600"
          />
        )}

        {!loading && forecastData.length > 0 && (
          <div className="ui-space-y">
            <ForecastChart data={forecastData} />
            <ForecastTable data={forecastData} />
          </div>
        )}

        {!loading && forecastData.length === 0 && currentFilters && (
          <EmptyState
            title="No Forecast Data Found"
            message="No forecast data matches your current filter criteria. Try adjusting your route, period, or item settings."
            icon={
              <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
          />
        )}

        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
            duration={5000}
          />
        )}
      </div>
    </div>
  );
};

export default Forecast;