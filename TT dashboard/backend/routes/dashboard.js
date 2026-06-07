/**
 * Dashboard summary and chart data routes
 * GET /api/dashboard/summary - Aggregate metrics
 * GET /api/dashboard/pnl-chart-data - Time-series PnL
 * GET /api/dashboard/heatmap-data - Date × execution type matrix
 */

const express = require('express');
const { queryMany, queryOne } = require('../db');

const router = express.Router();

/**
 * GET /api/dashboard/summary
 * Return aggregate metrics: total PnL, win rate, active count, by wallet
 */
router.get('/summary', async (req, res) => {
  try {
    // Total PnL and strategy count
    const overview = await queryOne(`
      SELECT 
        COUNT(*) as total_strategies,
        SUM(COALESCE(all_pnl, 0)) as total_pnl,
        COUNT(CASE WHEN all_pnl > 0 THEN 1 END) as winning_strategies,
        COUNT(CASE WHEN all_pnl < 0 THEN 1 END) as losing_strategies,
        COUNT(CASE WHEN status = 'Active' THEN 1 END) as active_strategies
      FROM shared_codes
    `);

    // By wallet
    const byWallet = await queryMany(`
      SELECT 
        broker_name as wallet,
        COUNT(*) as count,
        SUM(COALESCE(all_pnl, 0)) as total_pnl,
        COUNT(CASE WHEN status = 'Active' THEN 1 END) as active_count
      FROM shared_codes
      GROUP BY broker_name
      ORDER BY total_pnl DESC
    `);

    // By status
    const byStatus = await queryMany(`
      SELECT 
        status,
        COUNT(*) as count,
        SUM(COALESCE(all_pnl, 0)) as total_pnl
      FROM shared_codes
      GROUP BY status
      ORDER BY count DESC
    `);

    // Win rate
    const winRate = overview.total_strategies > 0 
      ? ((overview.winning_strategies / overview.total_strategies) * 100).toFixed(2)
      : 0;

    res.json({
      overview: {
        ...overview,
        win_rate_percent: winRate
      },
      by_wallet: byWallet,
      by_status: byStatus
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/dashboard/pnl-chart-data
 * Time-series PnL data for charting
 * Group by date or counter sequence
 */
router.get('/pnl-chart-data', async (req, res) => {
  const { strategy_id, group_by = 'date' } = req.query;

  try {
    let sql, params = [];

    if (group_by === 'counter') {
      // Group by counter sequence
      sql = `
        SELECT 
          counter as label,
          SUM(COALESCE(amount, 0)) as pnl,
          COUNT(DISTINCT instrument_full) as positions,
          COUNT(*) as trades
        FROM ttdata
      `;
      if (strategy_id) {
        sql += ` WHERE strategy_id = $1`;
        params.push(strategy_id);
      }
      sql += ` GROUP BY counter ORDER BY counter ASC`;
    } else {
      // Group by date (default)
      sql = `
        SELECT 
          trade_date as label,
          SUM(COALESCE(amount, 0)) as pnl,
          COUNT(DISTINCT instrument_full) as positions,
          COUNT(*) as trades
        FROM ttdata
      `;
      if (strategy_id) {
        sql += ` WHERE strategy_id = $1`;
        params.push(strategy_id);
      }
      sql += ` GROUP BY trade_date ORDER BY trade_date ASC`;
    }

    const data = await queryMany(sql, params);

    // Calculate cumulative PnL
    let cumulative = 0;
    const chartData = data.map(row => {
      cumulative += row.pnl || 0;
      return {
        ...row,
        cumulative_pnl: cumulative
      };
    });

    res.json({ data: chartData });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/dashboard/heatmap-data
 * Heatmap data: date × execution type with PnL values
 */
router.get('/heatmap-data', async (req, res) => {
  try {
    // Get execution types (approximated from status field for now)
    const heatmapData = await queryMany(`
      SELECT 
        sc.trade_date as date,
        sc.status as execution_type,
        SUM(COALESCE(sc.amount, 0)) as pnl,
        COUNT(*) as trade_count
      FROM (
        SELECT 
          trade_date, 
          (SELECT status FROM shared_codes WHERE strategy_id = ttdata.strategy_id LIMIT 1) as status,
          amount
        FROM ttdata
      ) sc
      GROUP BY sc.trade_date, sc.status
      ORDER BY sc.trade_date ASC
    `);

    // Transform to matrix format for heatmap visualization
    const matrix = {};
    const executionTypes = new Set();
    const dates = new Set();

    heatmapData.forEach(row => {
      const date = row.date;
      const type = row.execution_type || 'Unknown';
      
      if (!matrix[date]) matrix[date] = {};
      matrix[date][type] = row.pnl;
      
      dates.add(date);
      executionTypes.add(type);
    });

    res.json({
      matrix,
      dates: Array.from(dates).sort(),
      execution_types: Array.from(executionTypes)
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
