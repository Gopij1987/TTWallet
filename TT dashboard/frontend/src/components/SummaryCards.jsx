import React, { useEffect, useState } from 'react';
import { fetchDashboardSummary } from '../api';

function SummaryCards({ filters }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchDashboardSummary()
      .then(response => {
        setData(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Failed to fetch summary:', error);
        setLoading(false);
      });
  }, [filters]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="card p-6 animate-pulse">
            <div className="h-4 bg-gray-700 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-gray-700 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!data) return null;

  const cards = [
    {
      title: '💰 Total PnL',
      value: `₹${(data.overview.total_pnl || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
      color: (data.overview.total_pnl || 0) >= 0 ? 'bg-green-500/10' : 'bg-red-500/10',
      textColor: (data.overview.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400',
    },
    {
      title: '📊 Win Rate',
      value: `${data.overview.win_rate_percent}%`,
      color: 'bg-blue-500/10',
      textColor: 'text-blue-400',
      subtitle: `${data.overview.winning_strategies} wins / ${data.overview.total_strategies} total`,
    },
    {
      title: '🔴 Active Strategies',
      value: data.overview.active_strategies,
      color: 'bg-yellow-500/10',
      textColor: 'text-yellow-400',
    },
    {
      title: '📈 Total Strategies',
      value: data.overview.total_strategies,
      color: 'bg-purple-500/10',
      textColor: 'text-purple-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => (
        <div key={idx} className={`card p-6 ${card.color}`}>
          <p className="text-gray-400 text-sm mb-2">{card.title}</p>
          <p className={`text-2xl font-bold ${card.textColor}`}>{card.value}</p>
          {card.subtitle && <p className="text-gray-500 text-xs mt-2">{card.subtitle}</p>}
        </div>
      ))}
    </div>
  );
}

export default SummaryCards;
