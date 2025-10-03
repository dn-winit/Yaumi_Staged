import React, { useState } from 'react';
import { RecommendedOrderDataPoint } from '../../types';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface RecommendedOrderChartProps {
  data: RecommendedOrderDataPoint[];
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
      <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900">📊 Why Recommend {row.recommendedQuantity}?</h3>
            <p className="text-sm text-gray-600 mt-1">{row.itemCode} - {row.itemName}</p>
            <p className="text-xs text-gray-500">Customer: {row.customerCode}</p>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
          >
            ×
          </button>
        </div>
        
        {/* Main Recommendation */}
        <div className="bg-gradient-to-r from-emerald-50 to-green-50 border-2 border-emerald-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-emerald-700">{row.recommendedQuantity}</div>
              <div className="text-sm text-emerald-600 font-medium">Recommended Quantity</div>
            </div>
            <div className="text-right">
              <div className="text-lg font-semibold text-gray-700">{row.actualQuantity || 0}</div>
              <div className="text-sm text-gray-500">Actual Quantity</div>
            </div>
          </div>
        </div>

        {/* Key Justification Metrics */}
        <div className="space-y-4">
          <h4 className="text-md font-semibold text-gray-800 border-b pb-1">📈 Key Insights</h4>
          
          {/* Average & Cycle */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="text-2xl font-bold text-blue-700">{row.avgQuantityPerVisit}</div>
              <div className="text-sm text-blue-600">Average per Visit</div>
              <div className="text-xs text-blue-500 mt-1">Historical buying pattern</div>
            </div>
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
              <div className="text-2xl font-bold text-indigo-700">{row.purchaseCycleDays}</div>
              <div className="text-sm text-indigo-600">Cycle Days</div>
              <div className="text-xs text-indigo-500 mt-1">Time between purchases</div>
            </div>
          </div>

          {/* Days Since & Probability */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
              <div className="text-2xl font-bold text-orange-700">{row.daysSinceLastPurchase}</div>
              <div className="text-sm text-orange-600">Days Since Last</div>
              <div className="text-xs text-orange-500 mt-1">
                {row.daysSinceLastPurchase > row.purchaseCycleDays ? "⚠️ Overdue" : "✅ On schedule"}
              </div>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="text-2xl font-bold text-green-700">{row.probabilityPercent}%</div>
              <div className="text-sm text-green-600">Buy Probability</div>
              <div className="text-xs text-green-500 mt-1">
                {row.probabilityPercent > 70 ? "🎯 Very likely" : row.probabilityPercent > 40 ? "📊 Moderate" : "👁️ Low chance"}
              </div>
            </div>
          </div>

          {/* Priority Tier */}
          <div className={`border-2 rounded-lg p-3 ${getTierColor(row.tier)}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-lg">{getTierIcon(row.tier)} {row.tier.replace('_', ' ')}</div>
                <div className="text-sm opacity-80">Priority Classification</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium">
                  {row.tier === 'MUST_STOCK' && "Critical - Stock immediately"}
                  {row.tier === 'SHOULD_STOCK' && "High priority - Recommended"}
                  {row.tier === 'CONSIDER' && "Medium priority - Consider stocking"}
                  {row.tier === 'MONITOR' && "Low priority - Monitor only"}
                  {row.tier === 'NEW_CUSTOMER' && "New customer - Trial quantity"}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            💡 This recommendation is based on AI analysis of purchase history, timing patterns, and demand probability.
          </div>
        </div>
      </div>
    </div>
  );
};

const RecommendedOrderChart: React.FC<RecommendedOrderChartProps> = ({ data }) => {
  const [selectedRow, setSelectedRow] = useState<RecommendedOrderDataPoint | null>(null);

  // Check if we have customer breakdown - if yes, aggregate from breakdown, otherwise from main data
  const hasCustomerBreakdown = data.some(d => d.customerBreakdown && d.customerBreakdown.length > 0);

  // Group by itemCode and sum quantities for chart display
  let itemData: Record<string, { actual: number; recommended: number; itemCode: string; itemName: string }>;

  if (hasCustomerBreakdown) {
    // Multiple customers: aggregate from customer breakdown
    itemData = data.reduce((acc, row) => {
      if (row.customerBreakdown && row.customerBreakdown.length > 0) {
        row.customerBreakdown.forEach(item => {
          const key = item.itemCode;
          if (!acc[key]) {
            acc[key] = { actual: 0, recommended: 0, itemCode: item.itemCode, itemName: item.itemName };
          }
          acc[key].actual += item.actualQuantity;
          acc[key].recommended += item.recommendedQuantity;
        });
      }
      return acc;
    }, {} as Record<string, { actual: number; recommended: number; itemCode: string; itemName: string }>);
  } else {
    // Single customer: use main data
    itemData = data.reduce((acc, item) => {
      const key = item.itemCode;
      if (!acc[key]) {
        acc[key] = { actual: 0, recommended: 0, itemCode: item.itemCode, itemName: item.itemName };
      }
      acc[key].actual += item.actualQuantity;
      acc[key].recommended += item.recommendedQuantity;
      return acc;
    }, {} as Record<string, { actual: number; recommended: number; itemCode: string; itemName: string }>);
  }

  // Sort items by accuracy (recommended vs actual difference) in ascending order
  // Closest match first, farthest last
  const sortedItems = Object.values(itemData).sort((a, b) => {
    const diffA = Math.abs(a.recommended - a.actual);
    const diffB = Math.abs(b.recommended - b.actual);
    return diffA - diffB; // Sort by smallest difference first
  });

  // Handle chart clicks - find the first item with the clicked itemCode
  const handleChartClick = (event: unknown, elements: unknown) => {
    if (elements && Array.isArray(elements) && elements.length > 0) {
      const clickedElement = elements[0] as any;
      const clickedIndex = clickedElement.index;
      const datasetIndex = clickedElement.datasetIndex;

      // Only show popup when clicking on recommended bars (index 1)
      if (datasetIndex !== 1) {
        return;
      }

      const clickedItemCode = sortedItems[clickedIndex]?.itemCode;

      // Find the first data point for this item code
      let clickedItem: RecommendedOrderDataPoint | null = null;

      if (hasCustomerBreakdown) {
        // Search in customer breakdown
        for (const row of data) {
          if (row.customerBreakdown && row.customerBreakdown.length > 0) {
            const foundItem = row.customerBreakdown.find(item => item.itemCode === clickedItemCode);
            if (foundItem) {
              clickedItem = foundItem as RecommendedOrderDataPoint;
              break;
            }
          }
        }
      } else {
        // Search in main data
        clickedItem = data.find(item => item.itemCode === clickedItemCode) || null;
      }

      if (clickedItem) {
        setSelectedRow(clickedItem);
      }
    }
  };

  const closePopup = () => {
    setSelectedRow(null);
  };

  const chartData = {
    labels: sortedItems.map(d => d.itemCode),
    datasets: [
      {
        label: 'Actual Quantity',
        data: sortedItems.map(d => d.actual),
        backgroundColor: '#3B82F6',
        borderColor: '#2563EB',
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false,
      },
      {
        label: 'Recommended Quantity',
        data: sortedItems.map(d => d.recommended),
        backgroundColor: '#10B981',
        borderColor: '#059669',
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false,
        hoverBackgroundColor: '#059669',
        hoverBorderColor: '#047857',
        hoverBorderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    onClick: handleChartClick,
    plugins: {
      legend: {
        display: false, // We'll use custom legend below
      },
      title: {
        display: true,
        text: 'Actual vs Recommended Quantities by Item',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: '#1F2937',
        padding: 20,
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#10B981',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: function(context: any) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            return `${label}: ${value} units`;
          },
          footer: function(tooltipItems: any[]) {
            const datasetLabel = tooltipItems[0]?.dataset?.label;
            if (datasetLabel?.includes('Recommended')) {
              return '💡 Click for detailed insights';
            }
            return '';
          }
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Quantity',
          font: {
            size: 14,
            weight: 'bold' as const,
          },
          color: '#374151',
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
        ticks: {
          color: '#6B7280',
          font: {
            size: 12,
          },
        },
      },
      x: {
        title: {
          display: true,
          text: 'Item Codes',
          font: {
            size: 14,
            weight: 'bold' as const,
          },
          color: '#374151',
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
        ticks: {
          color: '#6B7280',
          font: {
            size: 12,
          },
          maxRotation: 45,
          minRotation: 0,
        },
        categoryPercentage: 0.7,
        barPercentage: 0.9,
      },
    },
    onHover: (event: any, elements: any[]) => {
      const chart = event.chart;
      if (elements.length > 0) {
        const datasetIndex = elements[0].datasetIndex;
        // Show pointer cursor for recommended bars (index 1)
        if (datasetIndex === 1) {
          chart.canvas.style.cursor = 'pointer';
        } else {
          chart.canvas.style.cursor = 'default';
        }
      } else {
        chart.canvas.style.cursor = 'default';
      }
    },
  };

  return (
    <div className="ui-card">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Order Comparison</h3>
            <p className="text-sm text-gray-600">Actual vs recommended quantities by item</p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="overflow-x-auto overflow-y-hidden">
        <div style={{ minWidth: Math.max(800, sortedItems.length * 80), height: 400 }}>
          <Bar data={chartData} options={options} />
        </div>
      </div>

      {/* Custom Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#3B82F6' }}></div>
          <span className="text-sm text-gray-700 font-medium">Actual Quantity</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10B981' }}></div>
          <span className="text-sm text-gray-700 font-medium">Recommended Quantity</span>
        </div>
      </div>

      {/* Detail Popup */}
      {selectedRow && (
        <DetailPopup row={selectedRow} onClose={closePopup} />
      )}
    </div>
  );
};

export default RecommendedOrderChart;