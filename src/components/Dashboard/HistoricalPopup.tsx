import React from 'react';
import { X } from 'lucide-react';
import { HistoricalAverages, DailyAverages, WeeklyAverages, MonthlyAverages } from '../../types';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, TooltipItem } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface HistoricalPopupProps {
  isOpen: boolean;
  onClose: () => void;
  data: HistoricalAverages | null;
  itemName: string;
  date: string;
  predictedQuantity?: number;
  actualQuantity?: number;
}

const HistoricalPopup: React.FC<HistoricalPopupProps> = ({ isOpen, onClose, data, itemName, date, predictedQuantity, actualQuantity }) => {
  if (!isOpen || !data) return null;

  const getChartData = () => {
    if (data.period === 'Daily') {
      const dailyData = data.data as DailyAverages;
      return {
        labels: ['Last 1 Week', 'Last 1 Month', 'Last 3 Months', 'Last 6 Months', 'Last 1 Year'],
        values: [
          dailyData.last_1_week,
          dailyData.last_1_month,
          dailyData.last_3_months,
          dailyData.last_6_months,
          dailyData.last_1_year,
        ],
      };
    } else if (data.period === 'Weekly') {
      const weeklyData = data.data as WeeklyAverages;
      return {
        labels: ['Last 1 Week', 'Last 3 Weeks', 'Last 6 Weeks', 'Last 1 Year'],
        values: [
          weeklyData.last_1_week,
          weeklyData.last_3_weeks,
          weeklyData.last_6_weeks,
          weeklyData.last_1_year,
        ],
      };
    } else { // Monthly
      const monthlyData = data.data as MonthlyAverages;
      return {
        labels: ['Last 1 Month', 'Last 3 Months', 'Last 6 Months', 'Last 1 Year'],
        values: [
          monthlyData.last_1_month,
          monthlyData.last_3_months,
          monthlyData.last_6_months,
          monthlyData.last_1_year,
        ],
      };
    }
  };

  const { labels, values } = getChartData();

  const chartData = {
    labels,
    datasets: [
      {
        label: `${data.period} Averages`,
        data: values,
        backgroundColor: [
          '#EF4444',
          '#F97316',
          '#EAB308',
          '#22C55E',
          '#3B82F6',
        ].slice(0, labels.length),
        borderColor: [
          '#DC2626',
          '#EA580C',
          '#CA8A04',
          '#16A34A',
          '#2563EB',
        ].slice(0, labels.length),
        borderWidth: 2,
        borderRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: `${data.period} Historical Trends for ${itemName}`,
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: '#1F2937',
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#3B82F6',
        borderWidth: 1,
        cornerRadius: 8,
        callbacks: {
          label: function(context: TooltipItem<'bar'>) {
            return `Average: ${Math.round(context.parsed.y)}`;
          }
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Average Quantity',
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
        },
      },
      x: {
        title: {
          display: true,
          text: 'Time Period',
          font: {
            size: 14,
            weight: 'bold' as const,
          },
          color: '#374151',
        },
        grid: {
          display: false,
        },
        ticks: {
          color: '#6B7280',
        },
      },
    },
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-blue-100 flex-shrink-0">
          <div>
            <h3 className="text-base font-bold text-gray-900">Historical Trends</h3>
            <p className="text-xs text-gray-600">{itemName} - {new Date(date).toLocaleDateString()}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors hover:bg-gray-100 rounded-full p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 p-4 overflow-hidden flex flex-col">
          {/* Chart */}
          <div className="flex-1 mb-3">
            <div style={{ height: '220px' }}>
              <Bar data={chartData} options={options} />
            </div>
          </div>

          {/* Current Values - Compact Display */}
          <div className={`grid gap-2.5 mb-3 ${(actualQuantity !== undefined && predictedQuantity !== undefined) ? 'grid-cols-2' : 'grid-cols-1 max-w-xs mx-auto'}`}>
            {actualQuantity !== undefined && (
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-2.5 text-center">
                <div className="text-xs font-medium text-blue-600 mb-0.5">Actual</div>
                <div className="text-xl font-bold text-blue-900">{Math.round(actualQuantity)}</div>
              </div>
            )}
            {predictedQuantity !== undefined && (
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-2.5 text-center">
                <div className="text-xs font-medium text-blue-600 mb-0.5">Predicted</div>
                <div className="text-xl font-bold text-blue-900">{Math.round(predictedQuantity)}</div>
              </div>
            )}
          </div>

          {/* Historical Summary - Compact */}
          <div className="flex-shrink-0">
            <h4 className="text-xs font-semibold text-gray-700 mb-1.5">Historical Averages</h4>
            <div className={`grid gap-1.5 text-center ${labels.length === 4 ? 'grid-cols-4' : 'grid-cols-5'}`}>
              {labels.map((label, index) => {
                const colors = [
                  { bg: 'bg-blue-50', text: 'text-blue-600', bold: 'text-blue-700' },
                  { bg: 'bg-blue-100', text: 'text-blue-600', bold: 'text-blue-700' },
                  { bg: 'bg-slate-50', text: 'text-slate-600', bold: 'text-slate-700' },
                  { bg: 'bg-slate-100', text: 'text-slate-600', bold: 'text-slate-700' },
                  { bg: 'bg-cyan-50', text: 'text-cyan-600', bold: 'text-cyan-700' }
                ];
                const color = colors[index];

                return (
                  <div key={label} className={`${color.bg} p-2 rounded-lg`}>
                    <div className={`text-xs ${color.text} font-medium mb-0.5 truncate`}>{label}</div>
                    <div className={`text-sm font-bold ${color.bold}`}>{Math.round(values[index])}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HistoricalPopup;