import React from 'react';
import { Home, BarChart3, TrendingUp, ShoppingCart, ClipboardCheck } from 'lucide-react';

interface TabNavigationProps {
  activeTab: 'home' | 'dashboard' | 'forecast' | 'recommended-order' | 'sales-supervision';
  onTabChange: (tab: 'home' | 'dashboard' | 'forecast' | 'recommended-order' | 'sales-supervision') => void;
}

const TabNavigation: React.FC<TabNavigationProps> = ({ activeTab, onTabChange }) => {
  return (
    <div className="flex space-x-1 bg-gray-100 p-1.5 rounded-lg w-fit shadow-sm">
      <button
        onClick={() => onTabChange('home')}
        className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
          activeTab === 'home'
            ? 'bg-white text-blue-600 shadow-md'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        }`}
      >
        <Home className="w-5 h-5" />
        <span>Home</span>
      </button>
      <button
        onClick={() => onTabChange('dashboard')}
        className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
          activeTab === 'dashboard'
            ? 'bg-white text-blue-600 shadow-md'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        }`}
      >
        <BarChart3 className="w-5 h-5" />
        <span>Demand Dashboard</span>
      </button>
      <button
        onClick={() => onTabChange('forecast')}
        className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
          activeTab === 'forecast'
            ? 'bg-white text-blue-600 shadow-md'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        }`}
      >
        <TrendingUp className="w-5 h-5" />
        <span>Demand Forecast</span>
      </button>
      <button
        onClick={() => onTabChange('recommended-order')}
        className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
          activeTab === 'recommended-order'
            ? 'bg-white text-blue-600 shadow-md'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        }`}
      >
        <ShoppingCart className="w-5 h-5" />
        <span>Recommended Order</span>
      </button>
      <button
        onClick={() => onTabChange('sales-supervision')}
        className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
          activeTab === 'sales-supervision'
            ? 'bg-white text-blue-600 shadow-md'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        }`}
      >
        <ClipboardCheck className="w-5 h-5" />
        <span>Sales Supervision</span>
      </button>
    </div>
  );
};

export default TabNavigation;