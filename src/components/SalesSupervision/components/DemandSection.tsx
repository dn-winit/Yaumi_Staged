/**
 * Demand Section Component
 * Displays demand data for selected route and date
 */

import React from 'react';
import { Package } from 'lucide-react';
import type { DemandItem } from '../types';

interface DemandSectionProps {
  items: DemandItem[];
}

const DemandSection: React.FC<DemandSectionProps> = ({ items }) => {
  return (
    <div className="ui-card">
      <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
        <Package className="w-5 h-5 mr-2 text-blue-600" />
        Demand Data
      </h3>

      {items.length > 0 ? (
        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full">
            <thead className="sticky top-0 bg-white z-10">
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-3 font-medium text-gray-700 text-sm">Item Code</th>
                <th className="text-left py-2 px-3 font-medium text-gray-700 text-sm">Item Name</th>
                <th className="text-right py-2 px-3 font-medium text-gray-700 text-sm">Allocated Qty</th>
                <th className="text-right py-2 px-3 font-medium text-gray-700 text-sm">Avg Price</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-3 text-gray-900 text-sm">{item.itemCode}</td>
                  <td className="py-2 px-3 text-gray-700 text-sm">{item.itemName}</td>
                  <td className="py-2 px-3 text-right text-gray-900 text-sm">{item.allocatedQuantity}</td>
                  <td className="py-2 px-3 text-right text-gray-900 text-sm">{item.avgPrice.toFixed(2)} AED</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-gray-500 text-center py-6 text-sm">
          No demand data available for the selected filters
        </p>
      )}
    </div>
  );
};

export default DemandSection;
