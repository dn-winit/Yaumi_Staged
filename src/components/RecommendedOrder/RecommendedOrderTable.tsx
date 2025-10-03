import React, { useState } from 'react';
import { RecommendedOrderDataPoint, PaginationInfo } from '../../types';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface RecommendedOrderTableProps {
  data: RecommendedOrderDataPoint[];
  pagination?: PaginationInfo;
  onPageChange?: (page: number) => void;
}

interface DetailPopupProps {
  row: RecommendedOrderDataPoint;
  onClose: () => void;
}

const DetailPopup: React.FC<DetailPopupProps> = ({ row, onClose }) => {
  const getTierColor = (tier: string) => {
    switch (tier.toUpperCase()) {
      case 'MUST_STOCK': return 'bg-red-100 text-red-800 border-red-300';
      case 'SHOULD_STOCK': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'CONSIDER': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'MONITOR': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'NEW_CUSTOMER': return 'bg-purple-100 text-purple-800 border-purple-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getTierIcon = (tier: string) => {
    switch (tier.toUpperCase()) {
      case 'MUST_STOCK': return '🚨';
      case 'SHOULD_STOCK': return '⚠️';
      case 'CONSIDER': return '💭';
      case 'MONITOR': return '👁️';
      case 'NEW_CUSTOMER': return '🆕';
      default: return '📊';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg p-5 max-w-lg w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Recommendation Details</h3>
            <p className="text-xs text-gray-600 mt-0.5">{row.itemCode} - {row.itemName}</p>
            <p className="text-xs text-gray-500">Customer: {row.customerCode}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl font-bold leading-none"
          >
            ×
          </button>
        </div>

        {/* Main Recommendation */}
        <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-lg p-3 mb-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-indigo-700">{row.recommendedQuantity}</div>
              <div className="text-xs text-indigo-600 font-medium">Recommended</div>
            </div>
            <div className="text-right">
              <div className="text-lg font-semibold text-gray-700">{row.actualQuantity}</div>
              <div className="text-xs text-gray-500">Actual</div>
            </div>
          </div>
        </div>

        {/* Key Justification Metrics */}
        <div className="space-y-2.5">
          <h4 className="text-sm font-semibold text-gray-800 border-b pb-1">Key Insights</h4>

          {/* Average & Cycle */}
          <div className="grid grid-cols-2 gap-2.5">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-2.5">
              <div className="text-xl font-bold text-blue-700">{row.avgQuantityPerVisit}</div>
              <div className="text-xs text-blue-600 font-medium">Avg per Visit</div>
              <div className="text-xs text-blue-500 mt-0.5">Historical pattern</div>
            </div>
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-2.5">
              <div className="text-xl font-bold text-indigo-700">{row.purchaseCycleDays}</div>
              <div className="text-xs text-indigo-600 font-medium">Cycle Days</div>
              <div className="text-xs text-indigo-500 mt-0.5">Purchase frequency</div>
            </div>
          </div>

          {/* Days Since & Probability */}
          <div className="grid grid-cols-2 gap-2.5">
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-2.5">
              <div className="text-xl font-bold text-orange-700">{row.daysSinceLastPurchase}</div>
              <div className="text-xs text-orange-600 font-medium">Days Since Last</div>
              <div className="text-xs text-orange-500 mt-0.5">
                {row.daysSinceLastPurchase > row.purchaseCycleDays ? "Overdue" : "On schedule"}
              </div>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-2.5">
              <div className="text-xl font-bold text-green-700">{row.probabilityPercent}%</div>
              <div className="text-xs text-green-600 font-medium">Buy Probability</div>
              <div className="text-xs text-green-500 mt-0.5">
                {row.probabilityPercent > 70 ? "Very likely" : row.probabilityPercent > 40 ? "Moderate" : "Low chance"}
              </div>
            </div>
          </div>

          {/* Priority Tier */}
          <div className={`border rounded-lg p-2.5 ${getTierColor(row.tier)}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-sm">{row.tier.replace('_', ' ')}</div>
                <div className="text-xs opacity-75">Priority Classification</div>
              </div>
              <div className="text-right">
                <div className="text-xs font-medium">
                  {row.tier === 'MUST_STOCK' && "Critical"}
                  {row.tier === 'SHOULD_STOCK' && "High priority"}
                  {row.tier === 'CONSIDER' && "Medium priority"}
                  {row.tier === 'MONITOR' && "Low priority"}
                  {row.tier === 'NEW_CUSTOMER' && "New customer"}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            AI-based recommendation from historical data analysis
          </div>
        </div>
      </div>
    </div>
  );
};

const RecommendedOrderTable: React.FC<RecommendedOrderTableProps> = ({ data, pagination, onPageChange }) => {
  const [selectedRow, setSelectedRow] = useState<RecommendedOrderDataPoint | null>(null);
  const [expandedCustomers, setExpandedCustomers] = useState<Set<string>>(new Set());

  const handlePageChange = (page: number) => {
    if (pagination && page >= 1 && page <= pagination.total_pages && onPageChange) {
      onPageChange(page);
    }
  };

  const handleRecommendedClick = (row: RecommendedOrderDataPoint) => {
    setSelectedRow(row);
  };

  const closePopup = () => {
    setSelectedRow(null);
  };

  const toggleCustomer = (customerCode: string) => {
    const newExpanded = new Set(expandedCustomers);
    if (newExpanded.has(customerCode)) {
      newExpanded.delete(customerCode);
    } else {
      newExpanded.add(customerCode);
    }
    setExpandedCustomers(newExpanded);
  };

  // Check if we have customer breakdown (multiple customers scenario)
  const hasCustomerBreakdown = (row: RecommendedOrderDataPoint) =>
    row.customerBreakdown && row.customerBreakdown.length > 0;

  const renderPagination = () => {
    if (!pagination) return null;

    const { current_page, total_pages, has_previous, has_next } = pagination;
    
    return (
      <div className="flex items-center justify-between mt-4">
        <div className="text-sm text-gray-700">
          Showing page {current_page} of {total_pages}
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => handlePageChange(current_page - 1)}
            disabled={!has_previous}
            className={`px-3 py-1 rounded-md text-sm font-medium ${
              has_previous
                ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            Previous
          </button>
          
          {/* Page numbers */}
          {Array.from({ length: Math.min(5, total_pages) }, (_, i) => {
            let pageNum;
            if (total_pages <= 5) {
              pageNum = i + 1;
            } else if (current_page <= 3) {
              pageNum = i + 1;
            } else if (current_page >= total_pages - 2) {
              pageNum = total_pages - 4 + i;
            } else {
              pageNum = current_page - 2 + i;
            }
            
            return (
              <button
                key={pageNum}
                onClick={() => handlePageChange(pageNum)}
                className={`px-3 py-1 rounded-md text-sm font-medium ${
                  pageNum === current_page
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {pageNum}
              </button>
            );
          })}
          
          <button
            onClick={() => handlePageChange(current_page + 1)}
            disabled={!has_next}
            className={`px-3 py-1 rounded-md text-sm font-medium ${
              has_next
                ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="ui-card">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-base font-semibold text-gray-900">Order Recommendations</h3>
          <p className="text-xs text-gray-600">
            {data.some(d => hasCustomerBreakdown(d))
              ? 'Click customer rows to expand details'
              : 'AI-powered order recommendations'}
          </p>
        </div>
        {pagination && (
          <div className="text-xs text-gray-600">
            {pagination.total_records} items
          </div>
        )}
      </div>
      <div className="overflow-auto" style={{ maxHeight: '500px' }}>
        <table className="w-full table-auto text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Date</th>
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Route</th>
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Customer</th>
              <th className="text-left py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">
                {data.some(d => hasCustomerBreakdown(d)) ? 'Items' : 'Item Code'}
              </th>
              {!data.some(d => hasCustomerBreakdown(d)) && (
                <th className="text-left py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Item Name</th>
              )}
              <th className="text-center py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Actual</th>
              <th className="text-center py-2 px-3 text-xs font-semibold text-gray-700 bg-gray-50">Recommended</th>
              {data.some(d => hasCustomerBreakdown(d)) && (
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
                    hasCustomerBreakdown(row) ? 'hover:bg-indigo-50 cursor-pointer' : 'hover:bg-gray-50'
                  } ${expandedCustomers.has(row.customerCode) ? 'bg-indigo-50' : ''}`}
                  onClick={() => hasCustomerBreakdown(row) && toggleCustomer(row.customerCode)}
                >
                  <td className="py-2 px-3 text-xs text-gray-900">
                    {new Date(row.trxDate).toLocaleDateString()}
                  </td>
                  <td className="py-2 px-3 text-xs text-gray-700 font-medium">{row.routeCode}</td>
                  <td className="py-2 px-3 text-xs">
                    <span className={`${hasCustomerBreakdown(row) ? 'font-semibold text-indigo-900' : 'text-gray-700'}`}>
                      {row.customerCode}
                    </span>
                  </td>
                  {hasCustomerBreakdown(row) ? (
                    <>
                      <td className="py-2 px-3 text-xs text-gray-600 font-medium">
                        {row.customerBreakdown?.length || 0}
                      </td>
                      <td className="py-2 px-3 text-center text-xs text-blue-600 font-medium">
                        {row.actualQuantity}
                      </td>
                      <td className="py-2 px-3 text-center text-xs text-indigo-600 font-semibold">
                        {row.recommendedQuantity}
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="py-2 px-3 text-xs text-gray-700 font-mono">{row.itemCode}</td>
                      <td className="py-2 px-3 text-xs text-gray-600">{row.itemName}</td>
                      <td className="py-2 px-3 text-center text-xs text-blue-600 font-medium">
                        {row.actualQuantity}
                      </td>
                      <td className="py-2 px-3 text-center text-xs">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRecommendedClick(row);
                          }}
                          className="text-indigo-600 font-semibold hover:text-indigo-700 hover:underline transition-colors cursor-pointer"
                        >
                          {row.recommendedQuantity}
                        </button>
                      </td>
                    </>
                  )}
                  {data.some(d => hasCustomerBreakdown(d)) && (
                    <td className="py-2 px-3 text-center">
                      {hasCustomerBreakdown(row) && (
                        expandedCustomers.has(row.customerCode)
                          ? <ChevronDown className="w-4 h-4 text-indigo-600" />
                          : <ChevronRight className="w-4 h-4 text-gray-400" />
                      )}
                    </td>
                  )}
                </tr>

                {/* Expanded Customer Breakdown */}
                {expandedCustomers.has(row.customerCode) && hasCustomerBreakdown(row) && (
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <td colSpan={data.some(d => hasCustomerBreakdown(d)) ? 8 : 7} className="py-0">
                      <div className="px-6 py-3">
                        <div className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                          Items for {row.customerCode}
                        </div>
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-gray-300">
                              <th className="text-left py-1.5 px-2 text-xs font-semibold text-gray-600">Item Code</th>
                              <th className="text-left py-1.5 px-2 text-xs font-semibold text-gray-600">Item Name</th>
                              <th className="text-center py-1.5 px-2 text-xs font-semibold text-gray-600">Actual</th>
                              <th className="text-center py-1.5 px-2 text-xs font-semibold text-gray-600">Recommended</th>
                            </tr>
                          </thead>
                          <tbody>
                            {row.customerBreakdown!.map((item, itemIdx) => (
                              <tr
                                key={itemIdx}
                                className="border-b border-gray-200 last:border-0 hover:bg-white transition-colors"
                              >
                                <td className="py-1.5 px-2 text-xs text-gray-700 font-mono">{item.itemCode}</td>
                                <td className="py-1.5 px-2 text-xs text-gray-700">{item.itemName}</td>
                                <td className="py-1.5 px-2 text-center text-xs text-blue-600 font-medium">
                                  {item.actualQuantity}
                                </td>
                                <td className="py-1.5 px-2 text-center text-xs">
                                  <button
                                    onClick={() => handleRecommendedClick(item as RecommendedOrderDataPoint)}
                                    className="text-indigo-600 font-semibold hover:text-indigo-700 hover:underline transition-colors cursor-pointer"
                                  >
                                    {item.recommendedQuantity}
                                  </button>
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
      {renderPagination()}

      {/* Detail Popup */}
      {selectedRow && (
        <DetailPopup row={selectedRow} onClose={closePopup} />
      )}
    </div>
  );
};

export default RecommendedOrderTable;