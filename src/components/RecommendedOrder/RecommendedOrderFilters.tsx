import React, { useState } from 'react';
import { RotateCcw, Search, ShoppingCart } from 'lucide-react';

import MultiSelect from '../common/MultiSelect';
import { RecommendedOrderFilters } from '../../types';
import { generateRecommendations, getRecommendedOrderData } from '../../services/api';

interface RecommendedOrderFiltersProps {
  onFiltersSubmit: (filters: RecommendedOrderFilters & {
    chartData?: unknown[];
    tableData?: unknown[];
  }) => void;
}

const RecommendedOrderFiltersComponent: React.FC<RecommendedOrderFiltersProps> = ({ onFiltersSubmit }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'date-selection' | 'processing' | 'filters-ready'>('date-selection');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [filters, setFilters] = useState<RecommendedOrderFilters>({
    routeCodes: [],
    customerCodes: [],
    itemCodes: [],
    date: '',
  });
  const [availableOptions, setAvailableOptions] = useState<{
    routes: { code: string; name: string; }[];
    customers: { code: string; name: string; }[];
    items: { code: string; name: string; }[];
  }>({ routes: [], customers: [], items: [] });

  const fetchRecommendationData = async (payload: RecommendedOrderFilters) => {
    const response = await getRecommendedOrderData(payload);
    return response;
  };

  const handleDateSubmit = async () => {
    if (!filters.date) {
      setError('Please select a date to continue');
      return;
    }

    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(filters.date)) {
      setError('Please select a valid date in YYYY-MM-DD format');
      return;
    }

    setLoading(true);
    setStep('processing');
    setError(null);
    setSuccessMessage(null);

    try {
      let hasData = false;
      try {
        const existing = await fetchRecommendationData({
          routeCodes: ['All'],
          customerCodes: ['All'],
          itemCodes: ['All'],
          date: filters.date,
        });
        const chart = Array.isArray(existing.chart_data) ? existing.chart_data : [];
        hasData = chart.length > 0;
        if (hasData) {
          await loadFilterOptions();
          setStep('filters-ready');
          setSuccessMessage(existing.message || `Found existing recommendations for ${filters.date}.`);
        }
      } catch {
        hasData = false;
      }

      if (!hasData) {
        const result = await generateRecommendations({ date: filters.date });
        await loadFilterOptions();
        setStep('filters-ready');
        setSuccessMessage(result.message || `Generated recommended orders for ${filters.date}.`);
      }
    } catch (e) {
      console.error('Failed to prepare recommendations', e);
      setError('Failed to prepare recommendations. Please try again.');
      setStep('date-selection');
    } finally {
      setLoading(false);
    }
  };

  const loadFilterOptions = async (customerCodes?: string[]) => {
    try {
      const params = new URLSearchParams();
      params.append('date', filters.date);
      if (filters.routeCodes && filters.routeCodes.length > 0 && !filters.routeCodes.includes('All')) {
        params.append('route_code', filters.routeCodes[0]); // For now, use first route
      }
      if (customerCodes && customerCodes.length > 0 && !customerCodes.includes('All')) {
        params.append('customer_code', customerCodes[0]); // For now, use first customer
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/recommended-order/filter-options?${params}`);
      const options = await response.json();

      if (options) {
        setAvailableOptions({
          routes: options.routes || [],
          customers: options.customers || [],
          items: options.items || []
        });
      }
    } catch (e) {
      console.error('Failed to load filter options', e);
      try {
        const result = await fetchRecommendationData({
          routeCodes: ['All'],
          customerCodes: ['All'],
          itemCodes: ['All'],
          date: filters.date,
        });

        const data = (result.chart_data || []) as Array<{
          routeCode: string;
          customerCode: string;
          itemCode: string;
          itemName: string;
        }>;

        if (data.length > 0) {
          const routes = Array.from(new Set(data.map((d) => String(d.routeCode)))).map((code) => ({ code, name: code }));
          const customers = Array.from(new Set(data.map((d) => String(d.customerCode)))).map((code) => ({ code, name: code }));
          const items = Array.from(
            new Map(
              data.map((d) => [String(d.itemCode), { code: String(d.itemCode), name: `${String(d.itemCode)} - ${String(d.itemName)}` }])
            ).values()
          );
          setAvailableOptions({ routes, customers, items });
        }
      } catch (fallbackError) {
        console.error('Fallback also failed', fallbackError);
      }
    }
  };

  const handleClearFilters = () => {
    setFilters({
      routeCodes: [],
      customerCodes: [],
      itemCodes: [],
      date: filters.date,
    });
  };

  const canSubmit = filters.routeCodes && filters.routeCodes.length > 0 && filters.routeCodes[0] !== '';

  const handleSubmit = async () => {
    if (!canSubmit) {
      setError('Please select at least one route to continue');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const result = await fetchRecommendationData(filters);

      onFiltersSubmit({
        ...filters,
        chartData: result.chart_data,
        tableData: result.table_data,
      });
    } catch (e) {
      console.error('Failed to get recommendation data', e);
      setError('Failed to get recommendation data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToDateSelection = () => {
    setStep('date-selection');
    setSuccessMessage(null);
    setError(null);
    setAvailableOptions({ routes: [], customers: [], items: [] });
  };

  return (
    <div className="ui-card mb-6">
      {step === 'date-selection' && (
        <div className="text-center py-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center justify-center mb-2">
              <ShoppingCart className="w-6 h-6 mr-2 text-emerald-600" />
              Generate Recommended Orders
            </h2>
            <p className="text-gray-600">Select a date to generate AI-powered order recommendations</p>
          </div>

          <div className="max-w-md mx-auto">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={filters.date}
              onChange={(e) => setFilters({ ...filters, date: e.target.value })}
              className="ui-input text-center text-lg py-3"
              required
            />

            {error && (
              <div className="mt-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded-md border border-red-200">
                {error}
              </div>
            )}

            <button
              onClick={handleDateSubmit}
              disabled={!filters.date || loading}
              className="mt-6 bg-emerald-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-emerald-700 transition-colors duration-300 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Generate Recommendations
            </button>
          </div>
        </div>
      )}

      {step === 'processing' && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-200 border-t-emerald-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Generating Recommendations</h3>
          <p className="text-gray-600">Running AI analysis for {filters.date}...</p>
        </div>
      )}

      {step === 'filters-ready' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-1">
                <ShoppingCart className="w-5 h-5 mr-2 text-emerald-600" />
                Filter Recommendations for {filters.date}
              </h2>
              <p className="text-sm text-gray-600">Apply filters to view specific recommendations</p>
            </div>
            {error && (
              <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md border border-red-200">
                {error}
              </div>
            )}
          </div>

          {successMessage && (
            <div className="mb-4 text-sm text-green-700 bg-green-50 px-4 py-3 rounded-md border border-green-200 flex items-center">
              <div className="w-4 h-4 bg-green-500 rounded-full mr-3 flex-shrink-0"></div>
              {successMessage}
              <button
                onClick={handleBackToDateSelection}
                className="ml-auto text-sm text-gray-500 hover:text-gray-700 underline"
              >
                Change Date
              </button>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="ui-label">
                Routes <span className="text-red-500">*</span>
              </label>
              <MultiSelect
                value={filters.routeCodes}
                onChange={(value) => setFilters({ ...filters, routeCodes: value })}
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
                value={filters.customerCodes || []}
                onChange={(value) => {
                  setFilters({ ...filters, customerCodes: value });
                  loadFilterOptions(value);
                }}
                options={[
                  { value: 'All', label: 'All Customers' },
                  ...availableOptions.customers.map(customer => ({
                    value: customer.code,
                    label: customer.name
                  }))
                ]}
                placeholder="Select Customer"
                maxSelection={10}
              />
            </div>

            <div>
              <label className="ui-label">Items</label>
              <MultiSelect
                value={filters.itemCodes || []}
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
              disabled={!canSubmit}
              className={`ui-button-primary ${!canSubmit ? 'disabled' : ''}`}
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