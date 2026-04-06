#!/usr/bin/env python3
"""
Import extracted CSV data into PostgreSQL extractions table
Usage: python import_csv_to_postgres.py <CSV_FILE>
Example: python import_csv_to_postgres.py leg_wise_23894081_complete_20260309_130652.csv
"""

import os
import sys
import csv
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================
BATCH_SIZE = 1000  # Insert rows in batches for performance

def get_db_connection():
    """Get PostgreSQL database connection from .env"""
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'tradetron'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        print(f"\nPlease ensure the following are set in .env:")
        print(f"  DB_HOST=localhost")
        print(f"  DB_PORT=5432")
        print(f"  DB_NAME=tradetron")
        print(f"  DB_USER=postgres")
        print(f"  DB_PASSWORD=your_password")
        return None


def read_csv_file(csv_path):
    """Read and parse CSV file"""
    try:
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows
    except Exception as e:
        print(f"[ERROR] Failed to read CSV file: {e}")
        return None


def insert_data(conn, rows):
    """Insert CSV data into extractions table"""
    cursor = conn.cursor()
    
    insert_sql = """
        INSERT INTO extractions 
        (shared_code_id, strategy_id, counter, trade_date, trade_time, 
         instrument_full, inst_type, underlying, expiry, option_type, 
         strike, qty, price, amount, note, extraction_timestamp)
        VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (shared_code_id, strategy_id, counter, trade_date, trade_time, 
                     instrument_full, qty, price) DO NOTHING
    """
    
    inserted = 0
    duplicates = 0
    errors = 0
    
    try:
        batches = [rows[i:i+BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
        
        for batch_num, batch in enumerate(batches, 1):
            print(f"  Processing batch {batch_num}/{len(batches)}...", end=" ")
            
            batch_data = []
            for row in batch:
                try:
                    shared_code_id = int(row.get('shared_code_id', 0))
                    strategy_id = shared_code_id  # Same as shared_code_id
                    counter = int(row.get('counter', 0))
                    trade_date = row.get('date', '')
                    trade_time = row.get('time', '')
                    instrument_full = row.get('instrument_full', '')
                    inst_type = row.get('inst_type', '')
                    underlying = row.get('underlying', '')
                    expiry = row.get('expiry', '')
                    option_type = row.get('option_type', '')
                    strike = row.get('strike', '')
                    qty = float(row.get('qty', 0)) if row.get('qty') else None
                    price = float(row.get('price', 0)) if row.get('price') else None
                    amount = float(row.get('amount', 0)) if row.get('amount') else None
                    note = row.get('note', '')
                    extraction_timestamp = datetime.now()
                    
                    batch_data.append((
                        shared_code_id, strategy_id, counter, trade_date, trade_time,
                        instrument_full, inst_type, underlying, expiry, option_type,
                        strike, qty, price, amount, note, extraction_timestamp
                    ))
                except Exception as e:
                    errors += 1
                    print(f"[SKIP] Row error: {e}")
            
            if batch_data:
                try:
                    execute_batch(cursor, insert_sql, batch_data)
                    conn.commit()
                    inserted += cursor.rowcount
                    print(f"OK ({cursor.rowcount} rows)")
                except Exception as e:
                    conn.rollback()
                    print(f"ERROR: {e}")
                    errors += len(batch_data)
        
        return inserted, errors
    
    except Exception as e:
        print(f"[ERROR] Batch insert failed: {e}")
        return 0, len(rows)
    finally:
        cursor.close()


def show_summary(conn, shared_code_id, strategy_id):
    """Display import summary"""
    cursor = conn.cursor()
    
    try:
        # Total extractions
        cursor.execute("SELECT COUNT(*) FROM extractions WHERE strategy_id = %s", (strategy_id,))
        total = cursor.fetchone()[0]
        
        # Count by counter
        cursor.execute("""
            SELECT counter, COUNT(*) as count 
            FROM extractions 
            WHERE strategy_id = %s
            GROUP BY counter 
            ORDER BY counter DESC 
            LIMIT 10
        """, (strategy_id,))
        
        print(f"\n{'='*60}")
        print("[IMPORT SUMMARY]")
        print(f"{'='*60}")
        print(f"\nStrategy ID:        {strategy_id}")
        print(f"Total Rows:         {total:,}")
        
        print(f"\n[TOP 10 COUNTERS BY TRADE COUNT]")
        for counter, count in cursor.fetchall():
            print(f"  Counter {counter}: {count:,} trades")
        
        # Trades by date
        cursor.execute("""
            SELECT trade_date, COUNT(*) as count 
            FROM extractions 
            WHERE strategy_id = %s
            GROUP BY trade_date 
            ORDER BY trade_date DESC 
            LIMIT 5
        """, (strategy_id,))
        
        print(f"\n[RECENT TRADING DATES]")
        for date, count in cursor.fetchall():
            print(f"  {date}: {count:,} trades")
        
        # P&L summary
        cursor.execute("""
            SELECT 
              SUM(amount) as total_pnl,
              COUNT(DISTINCT counter) as unique_counters,
              COUNT(DISTINCT underlying) as unique_underlyings,
              COUNT(DISTINCT DATE(trade_date)) as trading_days
            FROM extractions 
            WHERE strategy_id = %s
        """, (strategy_id,))
        
        pnl, counters, underlyings, days = cursor.fetchone()
        
        print(f"\n[STATISTICS]")
        print(f"  Total P&L:          {pnl:,.2f}")
        print(f"  Unique Counters:    {counters}")
        print(f"  Unique Underlyings: {underlyings}")
        print(f"  Trading Days:       {days}")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch summary: {e}")
    finally:
        cursor.close()


def main():
    print(f"\n{'='*60}")
    print("IMPORT CSV DATA TO PostgreSQL")
    print(f"{'='*60}\n")
    
    # Get CSV file path
    if len(sys.argv) < 2:
        print("[ERROR] CSV file path is required")
        print(f"\nUsage: python import_csv_to_postgres.py <CSV_FILE>")
        print(f"Example: python import_csv_to_postgres.py leg_wise_23894081_complete_20260309_130652.csv")
        return
    
    csv_path = sys.argv[1]
    
    # Check if file exists
    if not Path(csv_path).exists():
        print(f"[ERROR] File not found: {csv_path}")
        return
    
    print(f"[1/3] Reading CSV file...")
    rows = read_csv_file(csv_path)
    if not rows:
        return
    
    print(f"      Rows to import: {len(rows):,}\n")
    
    # Connect to database
    print(f"[2/3] Connecting to PostgreSQL...")
    conn = get_db_connection()
    if not conn:
        return
    
    print(f"      Connection established\n")
    
    # Import data
    print(f"[3/3] Importing data...\n")
    
    # Get shared_code_id and strategy_id from first row
    if rows:
        shared_code_id = int(rows[0].get('shared_code_id', 0))
        strategy_id = shared_code_id
    else:
        print("[ERROR] No rows to import")
        return
    
    inserted, errors = insert_data(conn, rows)
    
    # Show summary
    show_summary(conn, shared_code_id, strategy_id)
    
    # Print results
    print(f"[RESULTS]")
    print(f"  Inserted:  {inserted:,} rows")
    if errors > 0:
        print(f"  Errors:    {errors:,} rows")
    
    print(f"\n[SUCCESS] Import complete!")
    
    conn.close()


if __name__ == "__main__":
    main()
