import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle: string;
  legend?: {
    items: Array<{ color: string; label: string }>;
  };
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, legend }) => {
  return (
    <div className="ui-mb-header">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="ui-page-title">{title}</h1>
          <p className="ui-page-subtitle">{subtitle}</p>
        </div>
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
  );
};

export default PageHeader;
