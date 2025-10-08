import React, { useRef, useState, useEffect } from 'react';
import { ForecastDataPoint, ItemBreakdown } from '../../types';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, TooltipItem } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface ForecastChartProps {
  data: ForecastDataPoint[];
}

const ITEM_COLORS = [
  '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1',
  '#14b8a6', '#f43f5e', '#a855f7', '#eab308', '#22c55e'
];

const ForecastChart: React.FC<ForecastChartProps> = ({ data }) => {
  const chartRef = useRef<ChartJS<'bar'> | null>(null);
  const [selectedItems, setSelectedItems] = useState<string[]>(['All']);
  const [availableItems, setAvailableItems] = useState<ItemBreakdown[]>([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const hasMultipleItems = data.length > 0 && data[0].itemBreakdown && data[0].itemBreakdown.length > 0;

  // Extract available items from first data point
  useEffect(() => {
    if (hasMultipleItems && data[0].itemBreakdown) {
      setAvailableItems(data[0].itemBreakdown);
    }
  }, [data, hasMultipleItems]);

  const getChartData = () => {
    const labels = data.map(d => new Date(d.date).toLocaleDateString());

    if (!hasMultipleItems) {
      // Simple case: Single item selected
      return {
        labels,
        datasets: [
          {
            label: 'Predicted',
            data: data.map(d => d.predicted),
            backgroundColor: '#10b981',
            stack: 'predicted',
          }
        ]
      };
    }

    // Complex case: Multiple items with breakdown
    const datasets: any[] = [];

    // Determine which items to show
    const itemsToShow = selectedItems.includes('All') || selectedItems.length === 0
      ? availableItems.slice(0, 10) // Top 10
      : availableItems.filter(item => selectedItems.includes(item.itemCode));

    const showOthers = (selectedItems.includes('All') || selectedItems.length === 0) && availableItems.length > 10;

    // Build datasets for Predicted (stacked)
    itemsToShow.forEach((item, index) => {
      datasets.push({
        label: `${item.itemName}`,
        data: data.map(d => {
          const breakdown = d.itemBreakdown?.find(b => b.itemCode === item.itemCode);
          return breakdown?.predicted || 0;
        }),
        backgroundColor: ITEM_COLORS[index % ITEM_COLORS.length],
        stack: 'predicted',
      });
    });

    // Add "Others" for Predicted if needed
    if (showOthers) {
      datasets.push({
        label: 'Others',
        data: data.map(d => {
          const topItemCodes = itemsToShow.map(item => item.itemCode);
          const othersTotal = d.itemBreakdown
            ?.filter(b => !topItemCodes.includes(b.itemCode))
            .reduce((sum, b) => sum + b.predicted, 0) || 0;
          return othersTotal;
        }),
        backgroundColor: '#9ca3af',
        stack: 'predicted',
      });
    }

    return {
      labels,
      datasets
    };
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: !hasMultipleItems,
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          pointStyle: 'rect' as const,
          padding: 15,
          font: {
            size: 13,
            weight: 'normal' as const,
          },
        },
      },
      title: {
        display: true,
        text: hasMultipleItems
          ? (selectedItems.includes('All') || selectedItems.length === 0
              ? (availableItems.length > 10 ? 'Forecast Breakdown: Top 10 + Others' : `Forecast Breakdown: All ${availableItems.length} Items`)
              : `Forecast Breakdown: ${selectedItems.length} Selected Items`)
          : 'Predicted Forecast Values',
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
        borderColor: '#10b981',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          footer: function(tooltipItems: TooltipItem<'bar'>[]) {
            let predictedTotal = 0;
            tooltipItems.forEach(item => {
              predictedTotal += item.parsed.y;
            });
            return `Total Predicted: ${predictedTotal}`;
          }
        }
      },
    },
    scales: {
      y: {
        stacked: true,
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
        stacked: true,
        title: {
          display: true,
          text: 'Date',
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
        categoryPercentage: 0.7,
        barPercentage: 0.9,
      },
    },
  };

  const handleItemSelection = (itemCode: string) => {
    if (itemCode === 'All') {
      setSelectedItems(['All']);
    } else {
      let newSelection = selectedItems.filter(s => s !== 'All');

      if (newSelection.includes(itemCode)) {
        newSelection = newSelection.filter(s => s !== itemCode);
      } else {
        if (newSelection.length >= 10) {
          alert('Maximum 10 items can be selected');
          return;
        }
        newSelection.push(itemCode);
      }

      setSelectedItems(newSelection.length === 0 ? ['All'] : newSelection);
    }
  };

  const getDisplayText = () => {
    if (selectedItems.includes('All') || selectedItems.length === 0) {
      return availableItems.length > 10
        ? 'All Items (Top 10 + Others)'
        : `All ${availableItems.length} Items`;
    }
    return `${selectedItems.length} Items Selected`;
  };

  return (
    <div className="ui-card">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Forecast Chart</h3>
            <p className="text-sm text-gray-600">Predicted quantities visualization</p>
          </div>

          {hasMultipleItems && (
            <div className="relative">
              <button
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="px-4 py-2 border-2 border-gray-300 rounded-md hover:border-blue-500 flex items-center gap-2 text-sm font-medium text-gray-700"
              >
                <span>{getDisplayText()}</span>
                <svg className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {isDropdownOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white border-2 border-gray-200 rounded-md shadow-lg z-50 max-h-80 overflow-y-auto">
                  <div
                    onClick={() => handleItemSelection('All')}
                    className="px-3 py-2 hover:bg-blue-50 cursor-pointer flex items-center bg-blue-50 border-b-2 border-gray-200"
                  >
                    <input
                      type="checkbox"
                      checked={selectedItems.includes('All')}
                      readOnly
                      className="mr-2"
                    />
                    <span className="font-semibold">
                      {availableItems.length > 10
                        ? 'All Items (Top 10 + Others)'
                        : `All ${availableItems.length} Items`}
                    </span>
                  </div>

                  <div className="px-3 py-2 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-600 uppercase">
                    Select Specific Items (Max 10):
                  </div>

                  {availableItems.filter(item => item.itemCode !== 'Others').map((item) => (
                    <div
                      key={item.itemCode}
                      onClick={() => handleItemSelection(item.itemCode)}
                      className="px-3 py-2 hover:bg-gray-50 cursor-pointer flex items-center border-b border-gray-100"
                    >
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(item.itemCode)}
                        readOnly
                        className="mr-2"
                      />
                      <span className="text-sm">{item.itemName}</span>
                    </div>
                  ))}

                  <div className="px-3 py-2 bg-gray-50 border-t border-gray-200 flex gap-2">
                    <button
                      onClick={() => setSelectedItems([])}
                      className="flex-1 text-xs py-1.5 px-2 bg-white border border-gray-300 rounded hover:bg-gray-50"
                    >
                      Clear All
                    </button>
                    <button
                      onClick={() => setIsDropdownOpen(false)}
                      className="flex-1 text-xs py-1.5 px-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Apply
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="overflow-x-auto overflow-y-hidden">
        <div style={{ minWidth: Math.max(800, data.length * 60), height: 400 }}>
          <Bar ref={chartRef} data={getChartData()} options={options} />
        </div>
      </div>
    </div>
  );
};

export default ForecastChart;