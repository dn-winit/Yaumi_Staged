import React, { useState, useEffect } from 'react';
import { RotateCcw, Search, Filter } from 'lucide-react';

import MultiSelect from '../common/MultiSelect';
import { getForecastFilterOptions } from '../../services/api';
import { ForecastFilters, FilterOptions } from '../../types';

interface ForecastFiltersProps {
  onFiltersSubmit: (filters: ForecastFilters) => void;
}

const ForecastFiltersComponent: React.FC<ForecastFiltersProps> = ({ onFiltersSubmit }) => {
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ForecastFilters>({
    routeCodes: [],
    itemCodes: [],
    period: 'Daily',
  });

  useEffect(() => {
    const loadOptions = async () => {
      try {
        setLoading(true);
        setError(null);
        const options = await getForecastFilterOptions();
        setFilterOptions(options);
      } catch (e) {
        console.error('Failed to load forecast filter options', e);
        setError('Failed to load filter options. Please refresh the page to try again.');
      } finally {
        setLoading(false);
      }
    };
    loadOptions();
  }, []);

  const handleClearFilters = () => {
    setFilters({
      routeCodes: [],
      itemCodes: [],
      period: 'Daily',
    });
  };

  const canSubmit = filters.routeCodes && filters.routeCodes.length > 0 && filters.routeCodes[0] !== '';

  const handleSubmit = () => {
    if (!canSubmit) {
      setError('Please select at least one route to continue');
      return;
    }
    setError(null);
    onFiltersSubmit(filters);
  };

  if (loading) {
    return (
      <div className="ui-card mb-5">
        <div className="flex items-center justify-center py-6">
          <div className="animate-spin rounded-full h-6 w-6 border-3 border-blue-200 border-t-blue-500 mr-2"></div>
          <span className="text-xs text-gray-600">Loading filters...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="ui-card mb-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900 flex items-center mb-0.5">
            <Filter className="w-4 h-4 mr-1.5 text-blue-500" />
            Filters
          </h2>
          <p className="text-xs text-gray-600">Configure forecast parameters</p>
        </div>
        {error && (
          <div className="text-xs text-red-600 bg-red-50 px-2.5 py-1.5 rounded-md border border-red-200">
            {error}
          </div>
        )}
      </div>

      {filterOptions && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
          {/* Route Filter */}
          <div>
            <label className="ui-filter-label">
              Routes <span className="text-red-500">*</span>
            </label>
            <MultiSelect
              value={filters.routeCodes}
              onChange={(value) => setFilters({ ...filters, routeCodes: value })}
              options={[
                { value: 'All', label: 'All Routes' },
                ...filterOptions.routes.map(route => ({
                  value: route.code,
                  label: route.name
                }))
              ]}
              placeholder="Select Route"
            />
          </div>

          {/* Item Filter */}
          <div>
            <label className="ui-filter-label">Items</label>
            <MultiSelect
              value={filters.itemCodes || []}
              onChange={(value) => setFilters({ ...filters, itemCodes: value })}
              options={[
                { value: 'All', label: 'All Items' },
                ...filterOptions.items.map(item => ({
                  value: item.code,
                  label: item.name
                }))
              ]}
              placeholder="Select Item"
              maxSelection={10}
            />
          </div>

          {/* Period Filter */}
          <div>
            <label className="ui-filter-label">Period</label>
            <select
              value={filters.period}
              onChange={(e) => setFilters({ ...filters, period: e.target.value as 'Daily' | 'Weekly' | 'Monthly' })}
              className="ui-filter-select"
            >
              <option value="Daily">Daily</option>
              <option value="Weekly">Weekly</option>
              <option value="Monthly">Monthly</option>
            </select>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {filterOptions && (
        <div className="flex items-center gap-2">
          <button
            onClick={handleClearFilters}
            className="ui-button-neutral text-xs"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
            Clear
          </button>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className={`ui-button-primary text-xs ${!canSubmit ? 'disabled' : ''}`}
          >
            <Search className="w-3.5 h-3.5 mr-1.5" />
            Apply
          </button>
        </div>
      )}
    </div>
  );
};

export default ForecastFiltersComponent;
export { ForecastFiltersComponent as ForecastFilters };
