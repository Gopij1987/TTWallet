/**
 * Health check endpoint
 */

const express = require('express');
const { queryOne } = require('../db');

const router = express.Router();

router.get('/', async (req, res) => {
  try {
    // Test database connection
    const result = await queryOne('SELECT NOW() as timestamp');
    res.json({
      status: 'ok',
      timestamp: result.timestamp,
      environment: process.env.NODE_ENV || 'development'
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: 'Database connection failed',
      error: error.message
    });
  }
});

module.exports = router;
