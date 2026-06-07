/**
 * Database connection pool and query helpers
 */

const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'alphametrix',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'mcxdatabase',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
});

/**
 * Execute a query
 */
async function query(text, params = []) {
  const start = Date.now();
  try {
    const result = await pool.query(text, params);
    const duration = Date.now() - start;
    if (duration > 1000) {
      console.log(`[SLOW QUERY] ${duration}ms: ${text.substring(0, 80)}...`);
    }
    return result;
  } catch (error) {
    console.error('Database error:', error.message, 'Query:', text);
    throw error;
  }
}

/**
 * Get a single row
 */
async function queryOne(text, params = []) {
  const result = await query(text, params);
  return result.rows[0];
}

/**
 * Get all rows
 */
async function queryMany(text, params = []) {
  const result = await query(text, params);
  return result.rows;
}

/**
 * Close pool
 */
async function closePool() {
  await pool.end();
}

module.exports = {
  pool,
  query,
  queryOne,
  queryMany,
  closePool
};
