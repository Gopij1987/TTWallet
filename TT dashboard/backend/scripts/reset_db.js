const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });
const { Pool } = require('pg');

async function run() {
  const root = path.join(__dirname, '..', 'db');
  const schemaFile = path.join(root, 'schema.sql');
  const seedFile = path.join(root, 'seed.sql');

  if (!fs.existsSync(schemaFile)) {
    console.error('Schema file not found:', schemaFile);
    process.exit(1);
  }

  const schemaSql = fs.readFileSync(schemaFile, 'utf8');
  const seedSql = fs.existsSync(seedFile) ? fs.readFileSync(seedFile, 'utf8') : '';

  const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432', 10),
    database: process.env.DB_NAME || 'alphametrix',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || '',
  });

  const client = await pool.connect();
  try {
    console.log('Executing schema...');
    await client.query('BEGIN');
    await client.query(schemaSql);
    if (seedSql && seedSql.trim()) {
      console.log('Seeding sample data...');
      await client.query(seedSql);
    }
    await client.query('COMMIT');
    console.log('Database reset complete.');
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('Error resetting DB:', err.message);
    process.exitCode = 1;
  } finally {
    client.release();
    await pool.end();
  }
}

run();
