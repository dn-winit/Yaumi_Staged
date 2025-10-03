import React, { useState } from 'react';
import { DashboardDataPoint } from '../../types';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface DashboardTableProps {
  data: DashboardDataPoint[];
  onPredictedClick: (dataPoint: DashboardDataPoint) => void;
}

const DashboardTable: React.FC<DashboardTableProps> = ({ data, onPredictedClick }) => {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const toggleRow = (index: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  const hasItemBreakdown = (row: DashboardDataPoint) => row.itemBreakdown && row.itemBreakdown.length > 0;

  // Handle click on individual item's predicted value in breakdown
  const handleItemPredictedClick = (parentRow: DashboardDataPoint, item: { itemCode: string; itemName: string; actual: number; predicted: number }) => {
    // Skip "Others" category - no specific historical data
    if (item.itemCode === 'Others') {
      return;
    }

    // Create a data point for this specific item
    const itemDataPoint: DashboardDataPoint = {
      date: parentRow.date,
      route: parentRow.route,
      item: `${item.itemCode} - ${item.itemName}`,
      actual: item.actual,
      predicted: item.predicted,
      routeCode: parentRow.routeCode,
      itemCode: item.itemCode
      // No itemBreakdown - this is a single item
    };

    onPredictedClick(itemDataPoint);
  };

  return (
    <div className="ui-card">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-base font-semibold text-gray-900">Analytics Details</h3>
          <p className="text-xs text-gray-600">
            {data.some(d => hasItemBreakdown(d))
              ? 'Click rows to expand details, click predicted values for analysis'
              : 'Click predicted values for historical analysis'}
          </p>
        </div>
        <div className="text-xs text-gray-600">
          {data.length} items
        </div>
      </div>

      {/* Scrollable table container with max height and sticky header */}
      <div className="overflow-auto" style={{ maxHeight: '500px' }}>
        <table className="w-full table-auto text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Date</th>
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Route</th>
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Item</th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Actual</th>
              <th className="text-right py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Predicted</th>
              {data.some(d => hasItemBreakdown(d)) && (
                <th className="w-8 bg-gray-50"></th>
              )}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <React.Fragment key={index}>
                {/* Main Row */}
                <tr
                  className={`border-b border-gray-100 transition-colors ${
                    hasItemBreakdown(row) ? 'hover:bg-blue-50 cursor-pointer' : 'hover:bg-gray-50'
                  } ${expandedRows.has(index) ? 'bg-blue-50' : ''}`}
                  onClick={() => hasItemBreakdown(row) && toggleRow(index)}
                >
                  <td className="py-2 px-3 text-xs text-gray-900 font-medium">
                    {new Date(row.date).toLocaleDateString()}
                  </td>
                  <td className="py-2 px-3 text-xs text-gray-700">{row.route}</td>
                  <td className="py-2 px-3 text-xs">
                    <span className={`${hasItemBreakdown(row) ? 'font-semibold text-blue-900' : 'text-gray-700'}`}>
                      {row.item}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right text-xs text-blue-600 font-semibold">
                    {row.actual.toLocaleString()}
                  </td>
                  <td className="py-2 px-3 text-right text-xs">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onPredictedClick(row);
                      }}
                      className="text-blue-600 font-semibold hover:text-blue-700 hover:underline transition-colors cursor-pointer"
                    >
                      {row.predicted.toLocaleString()}
                    </button>
                  </td>
                  {data.some(d => hasItemBreakdown(d)) && (
                    <td className="py-2 px-3 text-center">
                      {hasItemBreakdown(row) && (
                        expandedRows.has(index)
                          ? <ChevronDown className="w-4 h-4 text-blue-600" />
                          : <ChevronRight className="w-4 h-4 text-gray-400" />
                      )}
                    </td>
                  )}
                </tr>

                {/* Expanded Item Breakdown */}
                {expandedRows.has(index) && hasItemBreakdown(row) && (
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <td colSpan={data.some(d => hasItemBreakdown(d)) ? 6 : 5} className="py-0">
                      <div className="px-6 py-3">
                        <div className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                          Items for {new Date(row.date).toLocaleDateString()}
                        </div>
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-gray-300">
                              <th className="text-left py-1.5 px-2 text-xs font-semibold text-gray-600">Item Code</th>
                              <th className="text-left py-1.5 px-2 text-xs font-semibold text-gray-600">Item Name</th>
                              <th className="text-right py-1.5 px-2 text-xs font-semibold text-gray-600">Actual</th>
                              <th className="text-right py-1.5 px-2 text-xs font-semibold text-gray-600">Predicted</th>
                            </tr>
                          </thead>
                          <tbody>
                            {row.itemBreakdown!.map((item, itemIdx) => (
                              <tr
                                key={itemIdx}
                                className="border-b border-gray-200 last:border-0 hover:bg-white transition-colors"
                              >
                                <td className="py-1.5 px-2 text-xs text-gray-700 font-mono">{item.itemCode}</td>
                                <td className="py-1.5 px-2 text-xs text-gray-700">{item.itemName}</td>
                                <td className="py-1.5 px-2 text-right text-xs text-blue-600 font-medium">{item.actual.toLocaleString()}</td>
                                <td className="py-1.5 px-2 text-right text-xs">
                                  {item.itemCode === 'Others' ? (
                                    <span className="text-blue-600 font-medium">
                                      {item.predicted.toLocaleString()}
                                    </span>
                                  ) : (
                                    <button
                                      onClick={() => handleItemPredictedClick(row, item)}
                                      className="text-blue-600 font-medium hover:text-blue-700 hover:underline transition-colors cursor-pointer"
                                    >
                                      {item.predicted.toLocaleString()}
                                    </button>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DashboardTable;