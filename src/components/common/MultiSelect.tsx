import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, X, Check } from 'lucide-react';

interface Option {
  value: string;
  label: string;
}

interface MultiSelectProps {
  value: string[];
  onChange: (value: string[]) => void;
  options: Option[];
  placeholder?: string;
  maxSelection?: number;
  showSelectAll?: boolean;
}

const MultiSelect: React.FC<MultiSelectProps> = ({
  value,
  onChange,
  options,
  placeholder = 'Select options',
  maxSelection,
  showSelectAll = true,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggle = (optionValue: string) => {
    if (optionValue === 'All') {
      // Toggle All
      if (value.includes('All')) {
        onChange([]);
      } else {
        onChange(['All']);
      }
    } else {
      // Toggle individual option
      const newValue = value.filter(v => v !== 'All'); // Remove 'All' if present

      if (newValue.includes(optionValue)) {
        onChange(newValue.filter(v => v !== optionValue));
      } else {
        if (maxSelection && newValue.length >= maxSelection) {
          alert(`Maximum ${maxSelection} items can be selected`);
          return;
        }
        onChange([...newValue, optionValue]);
      }
    }
  };

  const handleSelectAll = () => {
    if (value.includes('All')) {
      onChange([]);
    } else {
      onChange(['All']);
    }
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const getDisplayText = () => {
    if (value.length === 0) {
      return placeholder;
    }

    if (value.includes('All')) {
      const allOption = options.find(opt => opt.value === 'All');
      return allOption?.label || 'All';
    }

    if (value.length === 1) {
      const selected = options.find(opt => opt.value === value[0]);
      return selected?.label || value[0];
    }

    return `${value.length} selected`;
  };

  const isSelected = (optionValue: string) => {
    if (optionValue === 'All') {
      return value.includes('All');
    }
    return value.includes(optionValue);
  };

  const regularOptions = options.filter(opt => opt.value !== 'All');
  const allOption = options.find(opt => opt.value === 'All');

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="ui-input flex items-center justify-between w-full text-left cursor-pointer"
      >
        <span className={value.length === 0 ? 'text-gray-400' : 'text-gray-900'}>
          {getDisplayText()}
        </span>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-80 overflow-y-auto">
          {/* All option */}
          {allOption && (
            <>
              <div
                onClick={() => handleToggle('All')}
                className="px-3 py-2 hover:bg-blue-50 cursor-pointer flex items-center bg-blue-50 border-b-2 border-gray-200"
              >
                <div className={`w-4 h-4 border-2 rounded mr-2 flex items-center justify-center ${
                  isSelected('All') ? 'bg-blue-600 border-blue-600' : 'border-gray-300'
                }`}>
                  {isSelected('All') && <Check className="w-3 h-3 text-white" />}
                </div>
                <span className="font-semibold text-gray-900">{allOption.label}</span>
              </div>
              <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
                <span className="text-xs font-semibold text-gray-600 uppercase">
                  {maxSelection ? `Select specific items (Max ${maxSelection}):` : 'Select specific items:'}
                </span>
              </div>
            </>
          )}

          {/* Regular options */}
          {regularOptions.map((option) => (
            <div
              key={option.value}
              onClick={() => handleToggle(option.value)}
              className="px-3 py-2 hover:bg-gray-50 cursor-pointer flex items-center border-b border-gray-100 last:border-b-0"
            >
              <div className={`w-4 h-4 border-2 rounded mr-2 flex items-center justify-center ${
                isSelected(option.value) ? 'bg-blue-600 border-blue-600' : 'border-gray-300'
              }`}>
                {isSelected(option.value) && <Check className="w-3 h-3 text-white" />}
              </div>
              <span className="text-gray-700">{option.label}</span>
            </div>
          ))}

          {/* Action buttons */}
          {regularOptions.length > 0 && (
            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-3 py-2 flex gap-2">
              {showSelectAll && allOption && (
                <button
                  type="button"
                  onClick={handleSelectAll}
                  className="flex-1 text-xs py-1.5 px-2 bg-white border border-gray-300 rounded hover:bg-gray-50"
                >
                  Select All
                </button>
              )}
              <button
                type="button"
                onClick={handleClearAll}
                className="flex-1 text-xs py-1.5 px-2 bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                Clear All
              </button>
            </div>
          )}
        </div>
      )}

      {/* Selected badges */}
      {value.length > 0 && !value.includes('All') && (
        <div className="flex flex-wrap gap-1 mt-2">
          {value.slice(0, 3).map((val) => {
            const option = options.find(opt => opt.value === val);
            return (
              <span
                key={val}
                className="inline-flex items-center px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
              >
                {option?.label || val}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onChange(value.filter(v => v !== val));
                  }}
                  className="ml-1 hover:text-blue-900"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            );
          })}
          {value.length > 3 && (
            <span className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
              +{value.length - 3} more
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default MultiSelect;