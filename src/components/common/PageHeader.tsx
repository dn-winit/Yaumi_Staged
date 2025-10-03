import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle: string;
  legend?: {
    items: Array<{ color: string; label: string }>;
  };
  onRefresh?: () => void;
  refreshing?: boolean;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, legend, onRefresh, refreshing }) => {
  return (
    <div className="ui-mb-header">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="ui-page-title">{title}</h1>
          <p className="ui-page-subtitle">{subtitle}</p>
        </div>
        <div className="flex items-center gap-4">
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Refresh data from database"
            >
              <svg
                className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span className="hidden sm:inline">{refreshing ? 'Refreshing...' : 'Refresh Data'}</span>
            </button>
          )}
          {legend && (
            <div className="hidden sm:flex items-center gap-4 text-xs text-gray-500">
              {legend.items.map((item, index) => (
                <div key={index} className="flex items-center gap-1.5">
                  <div className={`w-2.5 h-2.5 ${item.color} rounded-full`}></div>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PageHeader;
