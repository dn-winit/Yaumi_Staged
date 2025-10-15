import React, { useState } from 'react';
import { PageHeader, LoadingState, EmptyState, Toast } from '../common';
import DashboardChart from './DashboardChart';
import DashboardTable from './DashboardTable';
import DashboardFilters from './DashboardFilters';
import HistoricalPopup from './HistoricalPopup';
import { getDashboardData, getHistoricalAverages, apiClient } from '../../services/api';
import { DashboardDataPoint, DashboardFilters as DashboardFiltersType, HistoricalAverages } from '../../types';

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardDataPoint[]>([]);
  const [currentFilters, setCurrentFilters] = useState<DashboardFiltersType | null>(null);
  const [historicalData, setHistoricalData] = useState<HistoricalAverages | null>(null);
  const [showPopup, setShowPopup] = useState(false);
  const [selectedItem, setSelectedItem] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedPredictedQuantity, setSelectedPredictedQuantity] = useState<number | undefined>();
  const [selectedActualQuantity, setSelectedActualQuantity] = useState<number | undefined>();
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState<{message: string; type: 'success' | 'error' | 'warning' | 'info'} | null>(null);

  const handleRefresh = async () => {
    setRefreshing(true);

    try {
      const result: any = await apiClient.post('/refresh-data');

      if (result.success) {
        setToast({ message: 'Data refreshed successfully!', type: 'success' });
      } else {
        setToast({ message: result.message || 'Failed to refresh data', type: 'error' });
      }
    } catch (error) {
      setToast({ message: 'Error connecting to server', type: 'error' });
    } finally {
      setRefreshing(false);
    }
  };

  const handleFiltersSubmit = async (filters: DashboardFiltersType) => {
    setLoading(true);
    try {
      const response = await getDashboardData(filters);
      setDashboardData(response.table_data);
      setCurrentFilters(filters);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setToast({ message: 'Failed to fetch dashboard data', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handlePredictedClick = async (dataPoint: DashboardDataPoint) => {
    try {
      const request: Record<string, unknown> = {
        date: dataPoint.date,
        period: currentFilters?.period || 'Daily',
      };

      if (dataPoint.routeCode === 'All Routes') {
        request.route_codes = currentFilters?.routeCodes || [];
      } else if (dataPoint.routeCode) {
        const isNumericRoute = !isNaN(Number(dataPoint.routeCode));
        if (isNumericRoute) {
          request.route_code = dataPoint.routeCode;
        } else {
          request.route_codes = currentFilters?.routeCodes || [dataPoint.routeCode];
        }
      }

      if (dataPoint.itemBreakdown && dataPoint.itemBreakdown.length > 0) {
        request.item_codes = dataPoint.itemBreakdown
          .filter(item => item.itemCode !== 'Others')
          .map(item => item.itemCode);
      } else {
        request.item_code = dataPoint.itemCode;
      }

      const response = await getHistoricalAverages(request);
      setHistoricalData(response);
      setSelectedItem(dataPoint.item);
      setSelectedDate(dataPoint.date);
      setSelectedPredictedQuantity(dataPoint.predicted);
      setSelectedActualQuantity(dataPoint.actual);
      setShowPopup(true);
    } catch (error) {
      console.error('Error fetching historical averages:', error);
      setToast({ message: 'Failed to fetch historical data', type: 'error' });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="ui-page-container">
        <PageHeader
          title="Analytics Dashboard"
          subtitle="Historical demand analysis with actual vs predicted performance"
          legend={{
            items: [
              { color: 'bg-blue-600', label: 'Actual' },
              { color: 'bg-blue-400', label: 'Predicted' }
            ]
          }}
          onRefresh={handleRefresh}
          refreshing={refreshing}
        />

        <DashboardFilters onFiltersSubmit={handleFiltersSubmit} />

        {loading && (
          <LoadingState
            title="Loading Dashboard Data"
            message="Fetching analytics..."
            spinnerColor="border-t-blue-600"
          />
        )}

        {!loading && dashboardData.length > 0 && (
          <div className="ui-space-y">
            <DashboardChart data={dashboardData} onPredictedClick={handlePredictedClick} />
            <DashboardTable data={dashboardData} onPredictedClick={handlePredictedClick} />
          </div>
        )}

        {!loading && dashboardData.length === 0 && currentFilters && (
          <EmptyState
            title="No Data Found"
            message="No data matches your current filter criteria. Try adjusting your filters."
          />
        )}

        <HistoricalPopup
          isOpen={showPopup}
          onClose={() => setShowPopup(false)}
          data={historicalData}
          itemName={selectedItem}
          date={selectedDate}
          predictedQuantity={selectedPredictedQuantity}
          actualQuantity={selectedActualQuantity}
        />

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

export default Dashboard;
