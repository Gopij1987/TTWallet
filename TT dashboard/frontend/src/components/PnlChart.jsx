import React, { useEffect, useState } from 'react';
import { fetchPnlChartData } from '../api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function PnlChart({ filters }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [groupBy, setGroupBy] = useState('date');

  useEffect(() => {
    setLoading(true);
    fetchPnlChartData(null, groupBy)
      .then(response => {
        setData(response.data.data || []);
        setLoading(false);
      })
      .catch(error => {
        console.error('Failed to fetch chart data:', error);
        setLoading(false);
      });
  }, [groupBy, filters]);

  return (
    <div className="card p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">📈 PnL Over Time</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setGroupBy('date')}
            className={`px-3 py-1 rounded text-sm ${groupBy === 'date' ? 'bg-blue-500' : 'bg-gray-700'}`}
          >
            By Date
          </button>
          <button
            onClick={() => setGroupBy('counter')}
            className={`px-3 py-1 rounded text-sm ${groupBy === 'counter' ? 'bg-blue-500' : 'bg-gray-700'}`}
          >
            By Counter
          </button>
        </div>
      </div>

      {loading ? (
        <div className="h-80 bg-gray-700/30 rounded animate-pulse"></div>
      ) : data.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="label" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
              cursor={{ stroke: '#6366f1' }}
            />
            <Legend />
            <Line type="monotone" dataKey="pnl" stroke="#10b981" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="cumulative_pnl" stroke="#3b82f6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-80 flex items-center justify-center text-gray-500">
          No data available
        </div>
      )}
    </div>
  );
}

export default PnlChart;
