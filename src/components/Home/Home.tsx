import React from 'react';
import { BarChart3, TrendingUp, ShoppingCart, ClipboardCheck, ArrowRight, Building2 } from 'lucide-react';

interface HomeProps {
  onNavigate?: (tab: 'dashboard' | 'forecast' | 'recommended-order' | 'sales-supervision') => void;
}

const Home: React.FC<HomeProps> = ({ onNavigate }) => {
  const modules = [
    {
      id: 'dashboard',
      icon: BarChart3,
      title: "Demand Analytics",
      description: "Comprehensive historical analysis with trends and performance insights",
      color: "blue"
    },
    {
      id: 'forecast',
      icon: TrendingUp,
      title: "Demand Forecasting",
      description: "AI-powered predictive analytics across multiple time horizons",
      color: "blue"
    },
    {
      id: 'recommended-order',
      icon: ShoppingCart,
      title: "Recommended Orders",
      description: "Intelligent order optimization with tiered priority system",
      color: "blue"
    },
    {
      id: 'sales-supervision',
      icon: ClipboardCheck,
      title: "Sales Supervision",
      description: "Real-time route monitoring with customer performance analytics",
      color: "blue"
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Compact Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex flex-col items-center">
              <div className="flex flex-col items-center space-y-1 mb-1">
                <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                  <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                  <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                </div>
              </div>
              <div className="text-xl font-bold text-gray-900">WINIT</div>
            </div>
            <div className="text-xs text-gray-500">Developed for Yaumi</div>
          </div>
        </div>
      </div>

      {/* Compact Hero */}
      <div className="bg-gradient-to-br from-blue-600 to-blue-700">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="max-w-4xl text-white">
            <div className="flex items-center gap-2 mb-3">
              <Building2 className="w-4 h-4" />
              <span className="text-xs font-medium text-blue-100">Enterprise Solution</span>
            </div>
            <h1 className="text-3xl font-bold mb-3">
              Demand Analytics & Forecasting Platform
            </h1>
            <p className="text-sm text-blue-50 leading-relaxed mb-4">
              Complete demand management solution with analytics, AI forecasting, order recommendations, and sales supervision.
            </p>
            <div className="grid grid-cols-4 gap-3 text-xs">
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2">
                <div className="font-semibold mb-0.5">Analytics</div>
                <div className="text-blue-100">Trends & insights</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2">
                <div className="font-semibold mb-0.5">Forecasting</div>
                <div className="text-blue-100">AI predictions</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2">
                <div className="font-semibold mb-0.5">Orders</div>
                <div className="text-blue-100">Recommendations</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2">
                <div className="font-semibold mb-0.5">Supervision</div>
                <div className="text-blue-100">Performance tracking</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modules Section */}
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-1">Platform Modules</h2>
          <p className="text-sm text-gray-600">Integrated solutions for demand management</p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {modules.map((module) => {
            const Icon = module.icon;

            return (
              <button
                key={module.id}
                onClick={() => onNavigate?.(module.id as 'dashboard' | 'forecast' | 'recommended-order' | 'sales-supervision')}
                className="group bg-white border border-gray-200 rounded-lg p-5 text-left transition-all hover:border-blue-400 hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="bg-blue-50 rounded-lg p-2 group-hover:bg-blue-100 transition-colors">
                      <Icon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-base font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
                        {module.title}
                      </h3>
                      <p className="text-xs text-gray-600 leading-relaxed">
                        {module.description}
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all mt-1" />
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Key Features */}
      <div className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-10">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-1">Core Capabilities</h2>
            <p className="text-sm text-gray-600">Enterprise-grade features for operational excellence</p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-5 border border-gray-200">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <BarChart3 className="w-5 h-5 text-blue-600" />
              </div>
              <h3 className="text-base font-semibold text-gray-900 mb-3">Advanced Analytics</h3>
              <ul className="space-y-2 text-xs text-gray-600">
                <li className="flex items-start">
                  <span className="text-blue-600 font-bold mr-2">•</span>
                  <span>Multi-dimensional filtering and analysis</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 font-bold mr-2">•</span>
                  <span>Interactive visualization and insights</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 font-bold mr-2">•</span>
                  <span>Real-time KPI tracking</span>
                </li>
              </ul>
            </div>

            <div className="bg-gray-50 rounded-lg p-5 border border-gray-200">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="w-5 h-5 text-blue-600" />
              </div>
              <h3 className="text-base font-semibold text-gray-900 mb-3">AI-Powered Forecasting</h3>
              <ul className="space-y-2 text-xs text-gray-600">
                <li className="flex items-start">
                  <span className="text-blue-600 font-bold mr-2">•</span>
                  <span>Machine learning predictions</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 font-bold mr-2">•</span>
                  <span>Multiple forecasting horizons</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 font-bold mr-2">•</span>
                  <span>Pattern and trend detection</span>
                </li>
              </ul>
            </div>

            <div className="bg-gray-50 rounded-lg p-5 border border-gray-200">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <ShoppingCart className="w-5 h-5 text-blue-600" />
              </div>
              <h3 className="text-base font-semibold text-gray-900 mb-3">Operational Excellence</h3>
              <ul className="space-y-2 text-xs text-gray-600">
                <li className="flex items-start">
                  <span className="text-blue-600 font-bold mr-2">•</span>
                  <span>Smart order recommendations</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 font-bold mr-2">•</span>
                  <span>Performance scoring and monitoring</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 font-bold mr-2">•</span>
                  <span>Actionable insights</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="grid md:grid-cols-3 gap-6 mb-6">
            <div>
              <div className="flex flex-col items-start mb-3">
                <div className="flex flex-col items-center space-y-1 mb-2">
                  <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                  </div>
                </div>
                <div className="text-2xl font-bold text-white">WINIT</div>
              </div>
              <p className="text-gray-400 text-xs">Transformation to Excellence</p>
            </div>

            <div>
              <h4 className="font-semibold mb-2 text-sm">Platform</h4>
              <ul className="space-y-1 text-xs text-gray-400">
                <li>Demand Analytics</li>
                <li>Demand Forecasting</li>
                <li>Recommended Orders</li>
                <li>Sales Supervision</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold mb-2 text-sm">Client</h4>
              <p className="text-xs text-gray-400">
                Developed by WINIT for Yaumi, providing enterprise-grade demand management.
              </p>
            </div>
          </div>

          <div className="border-t border-gray-800 pt-6">
            <div className="flex flex-col md:flex-row justify-between items-center text-xs text-gray-400">
              <div>© 2024 WINIT. All rights reserved.</div>
              <div className="mt-2 md:mt-0">
                <a href="https://www.winitsoftware.com" target="_blank" rel="noopener noreferrer" className="hover:text-blue-400 transition-colors">
                  www.winitsoftware.com
                </a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
