import React, { useEffect, useState } from 'react';
import axios from 'axios';
import SummaryCards from './components/SummaryCards';
import StrategyTable from './components/StrategyTable';
import PnlChart from './components/PnlChart';
import Heatmap from './components/Heatmap';
import FilterSidebar from './components/FilterSidebar';
import { checkHealth } from './api';

function App() {
  const [loading, setLoading] = useState(true);
  const [apiReady, setApiReady] = useState(false);
  const [filters, setFilters] = useState({
    wallet: null,
    status: null,
    execution_type: null,
    date_from: null,
    date_to: null,
  });

  useEffect(() => {
    // Check API health on mount
    checkHealth()
      .then(() => {
        setApiReady(true);
        setLoading(false);
      })
      .catch((error) => {
        console.error('API health check failed:', error);
        setLoading(false);
      });
  }, []);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center">
          <div className="mb-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          </div>
          <p className="text-white text-lg">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  if (!apiReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center">
          <p className="text-red-500 text-lg mb-2">❌ API Connection Failed</p>
          <p className="text-gray-400">Make sure the backend server is running on port 5000</p>
          <p className="text-gray-500 text-sm mt-4">http://localhost:5000</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">📈 Tradetron PnL Dashboard</h1>
            <p className="text-gray-400 text-sm mt-1">Real-time strategy performance across Gopi & Ramki wallets</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded text-sm">● Live</span>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar Filters */}
        <FilterSidebar onFilterChange={handleFilterChange} />

        {/* Main Content */}
        <main className="flex-1 p-6 space-y-6 overflow-y-auto">
          {/* Summary Cards */}
          <SummaryCards filters={filters} />

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PnlChart filters={filters} />
            <Heatmap filters={filters} />
          </div>

          {/* Strategy Table */}
          <StrategyTable filters={filters} />
        </main>
      </div>
    </div>
  );
}

export default App;
