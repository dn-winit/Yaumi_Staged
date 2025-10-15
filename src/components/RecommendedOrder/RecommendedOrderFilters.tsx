import React, { useState, useEffect } from 'react';
import { RotateCcw, Search, ShoppingCart, Calendar } from 'lucide-react';

import MultiSelect from '../common/MultiSelect';
import { RecommendedOrderFilters } from '../../types';
import { getRecommendedOrderData, getRecommendedOrderFilterOptions } from '../../services/api';

interface RecommendedOrderFiltersProps {
  onFiltersSubmit: (filters: RecommendedOrderFilters & {
    chartData?: unknown[];
    tableData?: unknown[];
  }) => void;
}

const RecommendedOrderFiltersComponent: React.FC<RecommendedOrderFiltersProps> = ({ onFiltersSubmit }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [selectedDate, setSelectedDate] = useState('');
  const [dataLoaded, setDataLoaded] = useState(false);

  const [filters, setFilters] = useState<RecommendedOrderFilters>({
    routeCodes: ['All'],
    customerCodes: ['All'],
    itemCodes: ['All'],
    date: '',
  });

  const [availableOptions, setAvailableOptions] = useState<{
    routes: { code: string; name: string; }[];
    customers: { code: string; name: string; hasActualSales?: boolean; }[];
    items: { code: string; name: string; }[];
  }>({ routes: [], customers: [], items: [] });

  // Handle date selection (no auto-fetch)
  const handleDateChange = (date: string) => {
    setSelectedDate(date);
    setDataLoaded(false);
    setError(null);
    setSuccessMessage(null);
    setAvailableOptions({ routes: [], customers: [], items: [] });
  };

  // Get Recommendations button handler
  const handleGetRecommendations = async () => {
    if (!selectedDate) {
      setError('Please select a date first');
      return;
    }

    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(selectedDate)) {
      setError('Please select a valid date');
      return;
    }

    setError(null);
    setSuccessMessage(null);
    setLoading(true);

    try {
      // Fetch recommendations - auto-generates if doesn't exist
      const response = await getRecommendedOrderData({
        routeCodes: ['All'],
        customerCodes: ['All'],
        itemCodes: ['All'],
        date: selectedDate
      });

      if (response.chart_data && response.chart_data.length > 0) {
        setDataLoaded(true);
        setFilters({
          routeCodes: ['All'],
          customerCodes: ['All'],
          itemCodes: ['All'],
          date: selectedDate
        });

        // Load filter options from DB
        await loadFilterOptions(selectedDate);

        const message = response.status === 'generated'
          ? `Generated ${response.chart_data.length} recommendations for ${selectedDate}`
          : `Loaded ${response.chart_data.length} recommendations from database`;

        setSuccessMessage(message);
      } else {
        setError('No data available for this date. Please try another date.');
      }
    } catch (err) {
      console.error('Failed to load recommendations:', err);
      setError('Failed to load recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Load filter options from backend
  const loadFilterOptions = async (date: string, routeCode?: string, customerCode?: string) => {
    try {
      const options = await getRecommendedOrderFilterOptions(
        date,
        routeCode && routeCode !== 'All' ? routeCode : undefined,
        customerCode && customerCode !== 'All' ? customerCode : undefined
      );

      setAvailableOptions({
        routes: options.routes || [],
        customers: options.customers || [],
        items: options.items || []
      });
    } catch (err) {
      console.error('Failed to load filter options:', err);
    }
  };

  // When route changes, reload customers and items
  useEffect(() => {
    if (dataLoaded && filters.routeCodes.length > 0 && filters.routeCodes[0] !== '') {
      const routeCode = filters.routeCodes.includes('All') ? undefined : filters.routeCodes[0];
      loadFilterOptions(selectedDate, routeCode);
    }
  }, [filters.routeCodes]);

  // When customer changes, reload items
  useEffect(() => {
    if (dataLoaded && filters.customerCodes && filters.customerCodes.length > 0) {
      const routeCode = filters.routeCodes.includes('All') ? undefined : filters.routeCodes[0];
      const customerCode = filters.customerCodes.includes('All') ? undefined : filters.customerCodes[0];
      loadFilterOptions(selectedDate, routeCode, customerCode);
    }
  }, [filters.customerCodes]);

  const handleClearFilters = () => {
    setFilters({
      ...filters,
      routeCodes: ['All'],
      customerCodes: ['All'],
      itemCodes: ['All'],
    });
  };

  const handleSubmit = async () => {
    if (!dataLoaded) {
      setError('Please select a date first');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const result = await getRecommendedOrderData(filters);

      onFiltersSubmit({
        ...filters,
        chartData: result.chart_data,
        tableData: result.table_data,
      });
    } catch (err) {
      console.error('Failed to get recommendation data', err);
      setError('Failed to get recommendation data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ui-card mb-6">
      {/* Date Selection Section */}
      <div className="mb-6 pb-6 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center justify-center mb-6">
          <Calendar className="w-5 h-5 mr-2 text-blue-600" />
          Select Date for Recommendations
        </h2>

        <div className="flex items-center justify-center gap-3">
          <div className="w-64">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => handleDateChange(e.target.value)}
              className="ui-input"
              placeholder="Select date"
            />
          </div>

          <button
            onClick={handleGetRecommendations}
            disabled={loading || !selectedDate}
            className="ui-button-primary"
          >
            <ShoppingCart className="w-4 h-4 mr-2" />
            {loading ? 'Generating...' : 'Get Recommendations'}
          </button>
        </div>

        {loading && (
          <div className="mt-4 flex items-center justify-center text-blue-600">
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-200 border-t-blue-600 mr-2"></div>
            <span className="text-sm font-medium">Loading recommendations...</span>
          </div>
        )}

        {error && (
          <div className="mt-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded-md border border-red-200 max-w-2xl mx-auto">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="mt-4 text-sm text-green-700 bg-green-50 px-4 py-3 rounded-md border border-green-200 flex items-center max-w-2xl mx-auto">
            <div className="w-4 h-4 bg-green-500 rounded-full mr-3 flex-shrink-0"></div>
            {successMessage}
          </div>
        )}
      </div>

      {/* Filters Section - Only shown when data is loaded */}
      {dataLoaded && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <ShoppingCart className="w-5 h-5 mr-2 text-blue-600" />
            Filter Recommendations
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="ui-label">Routes</label>
              <MultiSelect
                value={filters.routeCodes}
                onChange={(value) => {
                  // Reset dependent selections when route changes
                  setFilters({
                    ...filters,
                    routeCodes: value,
                    customerCodes: ['All'],
                    itemCodes: ['All']
                  });
                }}
                options={[
                  { value: 'All', label: 'All Routes' },
                  ...availableOptions.routes.map(route => ({
                    value: route.code,
                    label: route.name
                  }))
                ]}
                placeholder="Select Route"
              />
            </div>

            <div>
              <label className="ui-label">Customers</label>
              <MultiSelect
                value={filters.customerCodes || ['All']}
                onChange={(value) => {
                  // Reset items when customer changes
                  setFilters({ ...filters, customerCodes: value, itemCodes: ['All'] });
                }}
                options={[
                  { value: 'All', label: 'All Customers' },
                  ...availableOptions.customers.map(customer => ({
                    value: customer.code,
                    label: customer.hasActualSales ? `${customer.name} ✅` : customer.name
                  }))
                ]}
                placeholder="Select Customer"
                maxSelection={10}
              />
            </div>

            <div>
              <label className="ui-label">Items</label>
              <MultiSelect
                value={filters.itemCodes || ['All']}
                onChange={(value) => setFilters({ ...filters, itemCodes: value })}
                options={[
                  { value: 'All', label: 'All Items' },
                  ...availableOptions.items.map(item => ({
                    value: item.code,
                    label: item.name
                  }))
                ]}
                placeholder="Select Item"
                maxSelection={10}
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleClearFilters}
              className="ui-button-neutral"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Clear Filters
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="ui-button-primary"
            >
              <Search className="w-4 h-4 mr-2" />
              {loading ? 'Loading...' : 'Apply Filters'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecommendedOrderFiltersComponent;
