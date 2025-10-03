import React, { useState, useEffect } from 'react';
import { Filter, RotateCcw, Search } from 'lucide-react';

import CustomSelect from '../common/CustomSelect';
import MultiSelect from '../common/MultiSelect';
import { getDashboardFilterOptions } from '../../services/api';
import { DashboardFilters, FilterOptions } from '../../types';

interface DashboardFiltersProps {
  onFiltersSubmit: (filters: DashboardFilters) => void;
}

const DashboardFiltersComponent: React.FC<DashboardFiltersProps> = ({ onFiltersSubmit }) => {
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DashboardFilters>({
    routeCodes: [],
    itemCodes: [],
    period: 'Daily',
    startDate: '',
    endDate: '',
  });

  useEffect(() => {
    const loadOptions = async () => {
      try {
        setLoading(true);
        setError(null);
        const options = await getDashboardFilterOptions();
        setFilterOptions(options);
      } catch (e) {
        console.error('Failed to load filter options', e);
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
      startDate: '',
      endDate: '',
    });
  };

  const canSubmit = filters.routeCodes.length > 0 && filters.startDate && filters.endDate;

  const handleSubmit = () => {
    if (!canSubmit) {
      if (!filters.routeCodes || filters.routeCodes.length === 0) {
        setError('Please select at least one route to continue');
      } else if (!filters.startDate || !filters.endDate) {
        setError('Please select both start and end dates');
      }
      return;
    }
    if (new Date(filters.endDate) < new Date(filters.startDate)) {
      setError('End date must be after start date');
      return;
    }
    setError(null);
    onFiltersSubmit(filters);
  };

  if (loading) {
    return (
      <div className="ui-card mb-5">
        <div className="flex items-center justify-center py-6">
          <div className="animate-spin rounded-full h-6 w-6 border-3 border-blue-200 border-t-blue-600 mr-2"></div>
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
            <Filter className="w-4 h-4 mr-1.5 text-blue-600" />
            Filters
          </h2>
          <p className="text-xs text-gray-600">Configure analysis parameters</p>
        </div>
        {error && (
          <div className="text-xs text-red-600 bg-red-50 px-2.5 py-1.5 rounded-md border border-red-200">
            {error}
          </div>
        )}
      </div>

      {filterOptions && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-3">
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
            <CustomSelect
              value={filters.period}
              onChange={(value) => setFilters({ ...filters, period: value as 'Daily' | 'Weekly' | 'Monthly' })}
              options={[
                { value: 'Daily', label: 'Daily' },
                { value: 'Weekly', label: 'Weekly' },
                { value: 'Monthly', label: 'Monthly' }
              ]}
              placeholder="Select Period"
            />
          </div>

          {/* Start Date */}
          <div>
            <label className="ui-filter-label">
              Start Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={filters.startDate}
              onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
              className="ui-filter-input"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="ui-filter-label">
              End Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={filters.endDate}
              min={filters.startDate}
              onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
              className="ui-filter-input"
            />
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

export default DashboardFiltersComponent;
export { DashboardFiltersComponent as DashboardFilters };