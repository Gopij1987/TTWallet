import React, { useEffect, useState } from 'react';
import { fetchHeatmapData } from '../api';

function Heatmap({ filters }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchHeatmapData()
      .then(response => {
        setData(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Failed to fetch heatmap data:', error);
        setLoading(false);
      });
  }, [filters]);

  const getColor = (value) => {
    if (value === undefined || value === null) return 'bg-gray-700';
    if (value > 5000) return 'bg-green-700';
    if (value > 0) return 'bg-green-500';
    if (value > -5000) return 'bg-red-500';
    return 'bg-red-700';
  };

  if (loading) {
    return <div className="card p-6 animate-pulse h-80"></div>;
  }

  if (!data || !data.dates || data.dates.length === 0) {
    return (
      <div className="card p-6">
        <h2 className="text-xl font-semibold mb-4">🔥 PnL Heatmap</h2>
        <div className="h-64 flex items-center justify-center text-gray-500">
          No data available
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6 overflow-x-auto">
      <h2 className="text-xl font-semibold mb-4">🔥 PnL Heatmap (Date × Execution Type)</h2>
      <div className="inline-block">
        <table className="border-collapse text-sm">
          <thead>
            <tr>
              <th className="border border-gray-600 p-2 bg-gray-700">Date</th>
              {data.execution_types.map(type => (
                <th key={type} className="border border-gray-600 p-2 bg-gray-700 min-w-24">
                  {type}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.dates.slice(-10).map(date => (
              <tr key={date}>
                <td className="border border-gray-600 p-2 bg-gray-700 font-mono text-xs">
                  {date}
                </td>
                {data.execution_types.map(type => {
                  const value = data.matrix[date]?.[type];
                  return (
                    <td
                      key={`${date}-${type}`}
                      className={`border border-gray-600 p-2 text-center font-mono text-xs ${getColor(value)}`}
                      title={value !== undefined ? `₹${value.toFixed(0)}` : 'N/A'}
                    >
                      {value !== undefined ? `₹${(value / 1000).toFixed(1)}k` : '-'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-gray-500 text-xs mt-4">Showing latest 10 dates. Green = Profit, Red = Loss</p>
    </div>
  );
}

export default Heatmap;
