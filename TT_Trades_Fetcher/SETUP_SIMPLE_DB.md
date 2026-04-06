# Simple Database Setup Guide

## Quick Start

### 1. Add PostgreSQL credentials to `.env`

```env
# PostgreSQL Database Connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tradetron
DB_USER=postgres
DB_PASSWORD=your_password
```

### 2. Install PostgreSQL driver (if not already installed)

```powershell
.\.venv\Scripts\Activate.ps1
pip install psycopg2-binary
```

### 3. Run the setup script

```powershell
python tt_trades/setup_simple_db.py
```

## What Gets Created

### Table 1: `shared_codes`
- Stores shared strategy code versions
- Shared Code ID: 23894081 (Directional Option Selling BNF With Hedge V4)

### Table 2: `instruments`
- All parsed instruments linked to shared code ID
- Columns: instrument_full, inst_type, underlying, expiry, option_type, strike, exchange
- Indexes on: shared_code_id, underlying, expiry, option_type

## Sample Data

The script inserts sample instruments:
- 7 SENSEX options
- 8 NIFTY options

## Next Steps

After setup, you can:
1. Extract data using `extract_and_validate.py`
2. Later, import extracted data (counters, trades, positions) into enhanced schema
3. Upgrade schema as needed with more tables (strategies, counters, trades, positions)

## Example Queries

```sql
-- Show all instruments
SELECT * FROM instruments WHERE shared_code_id = 23894081;

-- Count by underlying
SELECT underlying, COUNT(*) FROM instruments 
WHERE shared_code_id = 23894081 
GROUP BY underlying;

-- Show all expiries
SELECT DISTINCT expiry FROM instruments 
WHERE shared_code_id = 23894081 
ORDER BY expiry DESC;
```

## Troubleshooting

**Error: "psycopg2 not found"**
- Run: `pip install psycopg2-binary`

**Error: "Failed to connect to database"**
- Check .env file for correct DB credentials
- Ensure PostgreSQL is running on your machine
- Verify database exists (create with: `CREATE DATABASE tradetron;`)

**Error: "database does not exist"**
```sql
-- Create database
CREATE DATABASE tradetron;
```
