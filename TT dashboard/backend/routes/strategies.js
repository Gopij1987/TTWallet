/**
 * Strategies routes
 * GET /api/strategies - List all strategies with filters
 * GET /api/strategies/:id - Get strategy detail with counter breakdown
 * GET /api/strategies/:id/trades - Get all trades for a strategy
 */

const express = require('express');
const { queryMany, queryOne } = require('../db');

const router = express.Router();

/**
 * GET /api/strategies
 * List all strategies with optional filters
 * Query params: wallet, status, execution_type, date_from, date_to
 */
router.get('/', async (req, res) => {
  const { wallet, status, execution_type, date_from, date_to } = req.query;

  try {
    let sql = `
      SELECT 
        id, strategy_id, strategy_name, status, creator_name, broker_name, 
        exchange, all_pnl as total_pnl, max_run_counter, created_at, updated_at
      FROM shared_codes
      WHERE 1=1
    `;
    const params = [];

    if (wallet) {
      sql += ` AND broker_name ILIKE $${params.length + 1}`;
      params.push(`%${wallet}%`);
    }

    if (status) {
      sql += ` AND status = $${params.length + 1}`;
      params.push(status);
    }

    if (execution_type) {
      sql += ` AND status = $${params.length + 1}`;
      params.push(execution_type);
    }

    sql += ` ORDER BY strategy_id DESC`;

    const strategies = await queryMany(sql, params);

    // For each strategy, get counter-wise PnL summary
    const enriched = await Promise.all(
      strategies.map(async (strat) => {
        const counterData = await queryMany(
          `SELECT counter, SUM(COALESCE(amount, 0)) as counter_pnl
           FROM ttdata 
           WHERE strategy_id = $1 
           GROUP BY counter 
           ORDER BY counter DESC 
           LIMIT 5`,
          [strat.strategy_id]
        );

        return {
          ...strat,
          recent_counters: counterData,
          counter_count: counterData.length
        };
      })
    );

    res.json({ data: enriched, count: enriched.length });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/strategies/:id
 * Get strategy detail with counter-wise PnL breakdown
 */
router.get('/:id', async (req, res) => {
  const { id } = req.params;

  try {
    // Get strategy metadata
    const strategy = await queryOne(
      `SELECT * FROM shared_codes WHERE strategy_id = $1`,
      [id]
    );

    if (!strategy) {
      return res.status(404).json({ error: 'Strategy not found' });
    }

    // Get counter-wise PnL breakdown
    const counters = await queryMany(
      `SELECT 
        counter,
        MIN(trade_date) as entry_date,
        MAX(trade_date) as exit_date,
        COUNT(DISTINCT instrument_full) as position_count,
        COUNT(*) as trade_count,
        SUM(COALESCE(amount, 0)) as total_pnl
       FROM ttdata 
       WHERE strategy_id = $1 
       GROUP BY counter 
       ORDER BY counter DESC`,
      [id]
    );

    res.json({
      strategy,
      counters,
      counter_count: counters.length,
      total_pnl: counters.reduce((sum, c) => sum + (c.total_pnl || 0), 0)
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/strategies/:id/trades
 * Get all individual trades (legs) for a strategy
 * Optional filter: counter, date_from, date_to
 */
router.get('/:id/trades', async (req, res) => {
  const { id } = req.params;
  const { counter, date_from, date_to } = req.query;

  try {
    let sql = `
      SELECT 
        counter, trade_date, trade_time, instrument_full, 
        inst_type, underlying, expiry, option_type, strike,
        qty, price, amount, note
      FROM ttdata 
      WHERE strategy_id = $1
    `;
    const params = [id];

    if (counter) {
      sql += ` AND counter = $${params.length + 1}`;
      params.push(counter);
    }

    if (date_from) {
      sql += ` AND trade_date >= $${params.length + 1}`;
      params.push(date_from);
    }

    if (date_to) {
      sql += ` AND trade_date <= $${params.length + 1}`;
      params.push(date_to);
    }

    sql += ` ORDER BY counter DESC, trade_date DESC, trade_time DESC`;

    const trades = await queryMany(sql, params);

    res.json({ data: trades, count: trades.length });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
