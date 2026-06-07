import React, { useEffect, useState } from 'react';
import { fetchStrategies, triggerRefresh } from '../api';

function StrategyTable({ filters }) {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchStrategies(filters)
      .then(response => {
        setStrategies(response.data.data || []);
        setLoading(false);
      })
      .catch(error => {
        console.error('Failed to fetch strategies:', error);
        setLoading(false);
      });
  }, [filters]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const response = await triggerRefresh();
      alert('✅ Refresh initiated! Check server logs for progress.');
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error) {
      alert('❌ Failed to trigger refresh: ' + error.message);
    } finally {
      setRefreshing(false);
    }
  };

  const getPnlColor = (pnl) => {
    if (pnl > 0) return 'text-green-400';
    if (pnl < 0) return 'text-red-400';
    return 'text-gray-400';
  };

  return (
    <div className="card p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">📋 Strategies</h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded flex items-center gap-2"
        >
          {refreshing ? '⏳ Refreshing...' : '🔄 Refresh Now'}
        </button>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-12 bg-gray-700/30 rounded animate-pulse"></div>
          ))}
        </div>
      ) : strategies.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 px-4 text-gray-400 font-semibold">ID</th>
                <th className="text-left py-3 px-4 text-gray-400 font-semibold">Name</th>
                <th className="text-left py-3 px-4 text-gray-400 font-semibold">Wallet</th>
                <th className="text-left py-3 px-4 text-gray-400 font-semibold">Status</th>
                <th className="text-right py-3 px-4 text-gray-400 font-semibold">PnL</th>
                <th className="text-center py-3 px-4 text-gray-400 font-semibold">Counters</th>
              </tr>
            </thead>
            <tbody>
              {strategies.map((strategy) => (
                <React.Fragment key={strategy.strategy_id}>
                  <tr
                    className="border-b border-gray-700 hover:bg-gray-700/50 cursor-pointer transition-colors"
                    onClick={() => setExpanded(expanded === strategy.strategy_id ? null : strategy.strategy_id)}
                  >
                    <td className="py-4 px-4 font-mono text-sm">{strategy.strategy_id}</td>
                    <td className="py-4 px-4 text-blue-300">{strategy.strategy_name}</td>
                    <td className="py-4 px-4 text-gray-400">{strategy.broker_name || 'N/A'}</td>
                    <td className="py-4 px-4">
                      <span className="px-2 py-1 rounded text-xs bg-yellow-500/20 text-yellow-400">
                        {strategy.status || 'Active'}
                      </span>
                    </td>
                    <td className={`py-4 px-4 text-right font-semibold ${getPnlColor(strategy.total_pnl)}`}>
                      ₹{(strategy.total_pnl || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-4 px-4 text-center text-gray-400">{strategy.counter_count || 0}</td>
                  </tr>

                  {/* Expanded row - Counter breakdown */}
                  {expanded === strategy.strategy_id && strategy.recent_counters && (
                    <tr className="bg-gray-700/30">
                      <td colSpan="6" className="py-4 px-4">
                        <div className="bg-gray-800 rounded p-4">
                          <h4 className="text-sm font-semibold mb-3 text-blue-300">Recent Counters:</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {strategy.recent_counters.map((counter) => (
                              <div key={counter.counter} className="bg-gray-700 rounded p-3">
                                <p className="text-xs text-gray-400">Round {counter.counter}</p>
                                <p className={`text-lg font-bold ${getPnlColor(counter.counter_pnl)}`}>
                                  ₹{(counter.counter_pnl || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="py-8 text-center text-gray-500">
          No strategies found matching the filters
        </div>
      )}
    </div>
  );
}

export default StrategyTable;
