import { useEffect, useState } from 'react';
import TabNavigation from './components/common/TabNavigation';
import Home from './components/Home/Home';
import Dashboard from './components/Dashboard/Dashboard';
import Forecast from './components/Forecast/Forecast';
import RecommendedOrder from './components/RecommendedOrder/RecommendedOrder';
import SalesSupervision from './components/SalesSupervision/SalesSupervision';

function App() {
  const [activeTab, setActiveTab] = useState<'home' | 'dashboard' | 'forecast' | 'recommended-order' | 'sales-supervision'>('home');

  useEffect(() => {
    document.title = 'WINIT Analytics Platform';
  }, []);

  // Handle navigation with scroll to top
  const handleNavigation = (tab: 'home' | 'dashboard' | 'forecast' | 'recommended-order' | 'sales-supervision') => {
    setActiveTab(tab);
    // Scroll to top when navigating to any page
    if (tab !== 'home') {
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }, 50);
    }
  };

  const renderContent = () => {
    if (activeTab === 'home') {
      return <Home onNavigate={handleNavigation} />;
    }
    
    return (
      <>
        <header className="sticky top-0 z-40 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80 border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => handleNavigation('home')}
                  className="flex flex-col items-center hover:opacity-80 transition-opacity duration-200"
                >
                  {/* WINIT Logo: 1 dot on top, 3 dots below */}
                  <div className="flex flex-col items-center space-y-1 mb-1">
                    <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                      <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                      <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    </div>
                  </div>
                  <div className="text-xl font-bold text-gray-900">WINIT</div>
                </button>
                <div className="h-10 w-px bg-gray-300"></div>
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">
                    {activeTab === 'dashboard' ? 'Demand Analytics' :
                     activeTab === 'forecast' ? 'Demand Forecasting' :
                     activeTab === 'recommended-order' ? 'Recommended Orders' :
                     activeTab === 'sales-supervision' ? 'Sales Supervision' : 'Analytics'}
                  </h1>
                  <p className="text-sm text-gray-600">
                    {activeTab === 'dashboard' ? 'Historical insights & trends' :
                     activeTab === 'forecast' ? 'AI-powered predictions' :
                     activeTab === 'recommended-order' ? 'Smart order recommendations' :
                     activeTab === 'sales-supervision' ? 'Route monitoring & scoring' : 'Platform'}
                  </p>
                </div>
              </div>
              <div className="shrink-0">
                <TabNavigation activeTab={activeTab} onTabChange={handleNavigation} />
              </div>
            </div>
          </div>
        </header>

        <main className="min-h-screen bg-gradient-to-br from-blue-50 to-emerald-50 py-8">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'forecast' && <Forecast />}
          {activeTab === 'recommended-order' && <RecommendedOrder />}
          {activeTab === 'sales-supervision' && <SalesSupervision />}
        </main>

        <footer className="bg-gray-900 text-white border-t border-gray-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
            <div className="flex flex-col sm:flex-row justify-between items-center">
              <div className="mb-3 sm:mb-0 flex items-center gap-3">
                {/* WINIT Logo: 1 dot on top, 3 dots below */}
                <div className="flex flex-col items-center">
                  <div className="flex flex-col items-center space-y-1 mb-2">
                    <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                      <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                      <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    </div>
                  </div>
                  <div className="text-lg font-bold text-white">WINIT</div>
                </div>
              </div>
              <div className="text-center sm:text-right">
                <p className="text-gray-400 text-sm">
                  © 2024 WINIT. All rights reserved.
                </p>
                <p className="text-gray-500 text-xs mt-1">
                  Transformation to Excellence
                </p>
              </div>
            </div>
          </div>
        </footer>
      </>
    );
  };

  return (
    <div className="min-h-screen">
      {renderContent()}
    </div>
  );
}

export default App;