import React, { useState } from 'react';

function FilterSidebar({ onFilterChange }) {
  const [filters, setFilters] = useState({
    wallet: null,
    status: null,
    execution_type: null,
    date_from: null,
    date_to: null,
  });

  const handleWalletChange = (wallet) => {
    const newFilters = { ...filters, wallet: filters.wallet === wallet ? null : wallet };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleStatusChange = (status) => {
    const newFilters = { ...filters, status: filters.status === status ? null : status };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleDateFromChange = (e) => {
    const newFilters = { ...filters, date_from: e.target.value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleDateToChange = (e) => {
    const newFilters = { ...filters, date_to: e.target.value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleReset = () => {
    const resetFilters = {
      wallet: null,
      status: null,
      execution_type: null,
      date_from: null,
      date_to: null,
    };
    setFilters(resetFilters);
    onFilterChange(resetFilters);
  };

  return (
    <aside className="w-64 bg-gray-800 border-r border-gray-700 p-6 space-y-6 overflow-y-auto">
      <div>
        <h3 className="text-lg font-semibold mb-3 text-blue-400">🔍 Filters</h3>
      </div>

      {/* Wallet Filter */}
      <div>
        <label className="text-sm font-semibold text-gray-300 mb-2 block">Wallet</label>
        <div className="space-y-2">
          {['Gopi', 'Ramki', 'Capital'].map((wallet) => (
            <label key={wallet} className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={filters.wallet === wallet}
                onChange={() => handleWalletChange(wallet)}
                className="w-4 h-4 rounded"
              />
              <span className="ml-2 text-sm text-gray-300">{wallet}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Status Filter */}
      <div>
        <label className="text-sm font-semibold text-gray-300 mb-2 block">Status</label>
        <div className="space-y-2">
          {['Active', 'Completed', 'Stopped'].map((status) => (
            <label key={status} className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={filters.status === status}
                onChange={() => handleStatusChange(status)}
                className="w-4 h-4 rounded"
              />
              <span className="ml-2 text-sm text-gray-300">{status}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Date Range Filter */}
      <div>
        <label className="text-sm font-semibold text-gray-300 mb-2 block">Date Range</label>
        <div className="space-y-2">
          <input
            type="date"
            value={filters.date_from || ''}
            onChange={handleDateFromChange}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-gray-300"
            placeholder="From"
          />
          <input
            type="date"
            value={filters.date_to || ''}
            onChange={handleDateToChange}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-gray-300"
            placeholder="To"
          />
        </div>
      </div>

      {/* Reset Button */}
      <button
        onClick={handleReset}
        className="w-full px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-sm font-medium transition-colors"
      >
        ✕ Reset Filters
      </button>
    </aside>
  );
}

export default FilterSidebar;
