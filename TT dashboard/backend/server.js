#!/usr/bin/env node
/**
 * TT Dashboard Express API Server
 * Serves strategy PnL data from PostgreSQL
 * Provides refresh endpoint to sync with Tradetron API
 */

require('dotenv').config();
require('express-async-errors');
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 5000;

// ============================================================================
// MIDDLEWARE
// ============================================================================

app.use(cors({ origin: process.env.CORS_ORIGIN || '*' }));
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ limit: '50mb', extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// ============================================================================
// ROUTES
// ============================================================================

// Import route handlers
const strategiesRouter = require('./routes/strategies');
const dashboardRouter = require('./routes/dashboard');
const refreshRouter = require('./routes/refresh');
const healthRouter = require('./routes/health');

app.use('/api/strategies', strategiesRouter);
app.use('/api/dashboard', dashboardRouter);
app.use('/api/refresh', refreshRouter);
app.use('/api/health', healthRouter);

// ============================================================================
// ERROR HANDLING
// ============================================================================

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found', path: req.path });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error('Error:', err.message);
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
});

// ============================================================================
// SERVER START
// ============================================================================

const server = app.listen(PORT, () => {
  const environment = (process.env.NODE_ENV || 'development').padEnd(46);
  const portDisplay = PORT.toString().padEnd(52);
  const corsDisplay = (process.env.CORS_ORIGIN || 'localhost:3000').padEnd(42);
  const databaseDisplay = (process.env.DB_NAME || 'alphametrix').padEnd(44);

  console.log(`
╔════════════════════════════════════════════════════════════╗
║      🚀 TT Dashboard API Server Started                    ║
╠════════════════════════════════════════════════════════════╣
║  Environment: ${environment} ║
║  Port: ${portDisplay} ║
║  CORS Origin: ${corsDisplay} ║
║  Database: ${databaseDisplay} ║
╚════════════════════════════════════════════════════════════╝
  `);
  console.log('Available endpoints:');
  console.log('  GET  /api/health');
  console.log('  GET  /api/strategies?wallet=gopi&status=Active&date_from=2026-03-01&date_to=2026-03-31');
  console.log('  GET  /api/strategies/:id');
  console.log('  GET  /api/strategies/:id/trades');
  console.log('  GET  /api/dashboard/summary');
  console.log('  GET  /api/dashboard/pnl-chart-data');
  console.log('  GET  /api/dashboard/heatmap-data');
  console.log('  POST /api/refresh');
  console.log('');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received. Shutting down gracefully...');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

module.exports = app;
