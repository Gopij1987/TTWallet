#!/usr/bin/env python3
"""
Simple PostgreSQL Database Setup
Creates tables for Shared Codes and Instruments
Shared Code ID: 23894081
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================
SHARED_CODE_ID = 23894081
SHARED_CODE_NAME = "Directional Option Selling BNF With Hedge V4"

# Sample instruments from your extracted data
INSTRUMENTS = [
    # SENSEX Options
    ('OPTIDX_SENSEX_12MAR2026_CE_79500', 'OPTIDX', 'SENSEX', '12MAR2026', 'CE', '79500', 'BFO'),
    ('OPTIDX_SENSEX_12MAR2026_PE_78500', 'OPTIDX', 'SENSEX', '12MAR2026', 'PE', '78500', 'BFO'),
    ('OPTIDX_SENSEX_04DEC2025_CE_85700', 'OPTIDX', 'SENSEX', '04DEC2025', 'CE', '85700', 'BFO'),
    ('OPTIDX_SENSEX_24DEC2025_CE_85300', 'OPTIDX', 'SENSEX', '24DEC2025', 'CE', '85300', 'BFO'),
    ('OPTIDX_SENSEX_18DEC2025_CE_85100', 'OPTIDX', 'SENSEX', '18DEC2025', 'CE', '85100', 'BFO'),
    ('OPTIDX_SENSEX_13NOV2025_CE_84200', 'OPTIDX', 'SENSEX', '13NOV2025', 'CE', '84200', 'BFO'),
    ('OPTIDX_SENSEX_08JAN2026_CE_85200', 'OPTIDX', 'SENSEX', '08JAN2026', 'CE', '85200', 'BFO'),
    
    # NIFTY Options
    ('OPTIDX_NIFTY_23DEC2025_CE_25750', 'OPTIDX', 'NIFTY 50', '23DEC2025', 'CE', '25750', 'NFO'),
    ('OPTIDX_NIFTY_23DEC2025_PE_25250', 'OPTIDX', 'NIFTY 50', '23DEC2025', 'PE', '25250', 'NFO'),
    ('OPTIDX_NIFTY_24FEB2026_PE_25300', 'OPTIDX', 'NIFTY 50', '24FEB2026', 'PE', '25300', 'NFO'),
    ('OPTIDX_NIFTY_30DEC2025_CE_25900', 'OPTIDX', 'NIFTY 50', '30DEC2025', 'CE', '25900', 'NFO'),
    ('OPTIDX_NIFTY_30DEC2025_PE_25900', 'OPTIDX', 'NIFTY 50', '30DEC2025', 'PE', '25900', 'NFO'),
    ('OPTIDX_NIFTY_02DEC2025_PE_26100', 'OPTIDX', 'NIFTY 50', '02DEC2025', 'PE', '26100', 'NFO'),
    ('OPTIDX_NIFTY_10MAR2026_CE_24550', 'OPTIDX', 'NIFTY 50', '10MAR2026', 'CE', '24550', 'NFO'),
]


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


def create_tables(conn):
    """Create shared_codes and instruments tables"""
    cursor = conn.cursor()
    
    try:
        # Create shared_codes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_codes (
                shared_code_id BIGINT PRIMARY KEY,
                code_name VARCHAR(255) NOT NULL,
                code_version VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
        """)
        print("[✓] Created table: shared_codes")
        
        # Create instruments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instruments (
                instrument_id BIGSERIAL PRIMARY KEY,
                shared_code_id BIGINT NOT NULL REFERENCES shared_codes(shared_code_id),
                instrument_full VARCHAR(100) NOT NULL UNIQUE,
                inst_type VARCHAR(20),
                underlying VARCHAR(50),
                expiry VARCHAR(20),
                option_type VARCHAR(5),
                strike VARCHAR(20),
                exchange VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_shared_code USING BTREE (shared_code_id),
                INDEX idx_underlying USING BTREE (underlying),
                INDEX idx_expiry USING BTREE (expiry),
                INDEX idx_option_type USING BTREE (option_type)
            );
        """)
        print("[✓] Created table: instruments")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"[✗] Error creating tables: {e}")
        return False
    finally:
        cursor.close()
    
    return True


def insert_shared_code(conn):
    """Insert shared code if not exists"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO shared_codes (shared_code_id, code_name, code_version, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (shared_code_id) DO NOTHING
        """, (SHARED_CODE_ID, SHARED_CODE_NAME, '1.0', 'Main shared strategy code'))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"[✓] Inserted shared code: {SHARED_CODE_ID}")
        else:
            print(f"[•] Shared code {SHARED_CODE_ID} already exists")
        
    except Exception as e:
        conn.rollback()
        print(f"[✗] Error inserting shared code: {e}")
        return False
    finally:
        cursor.close()
    
    return True


def insert_instruments(conn):
    """Insert instruments for shared code"""
    cursor = conn.cursor()
    
    try:
        # Prepare instrument data with shared_code_id
        instrument_data = [
            (SHARED_CODE_ID, inst_full, inst_type, underlying, expiry, opt_type, strike, exchange)
            for inst_full, inst_type, underlying, expiry, opt_type, strike, exchange in INSTRUMENTS
        ]
        
        # Bulk insert
        execute_values(cursor, """
            INSERT INTO instruments 
            (shared_code_id, instrument_full, inst_type, underlying, expiry, option_type, strike, exchange)
            VALUES %s
            ON CONFLICT (instrument_full) DO NOTHING
        """, instrument_data)
        
        conn.commit()
        
        inserted = cursor.rowcount
        print(f"[✓] Inserted {inserted} instruments for shared code {SHARED_CODE_ID}")
        
    except Exception as e:
        conn.rollback()
        print(f"[✗] Error inserting instruments: {e}")
        return False
    finally:
        cursor.close()
    
    return True


def show_summary(conn):
    """Display database summary"""
    cursor = conn.cursor()
    
    try:
        # Count shared codes
        cursor.execute("SELECT COUNT(*) FROM shared_codes")
        shared_code_count = cursor.fetchone()[0]
        
        # Count instruments
        cursor.execute("SELECT COUNT(*) FROM instruments")
        instrument_count = cursor.fetchone()[0]
        
        # Show instruments by underlying
        cursor.execute("""
            SELECT underlying, COUNT(*) as count 
            FROM instruments 
            WHERE shared_code_id = %s
            GROUP BY underlying 
            ORDER BY underlying
        """, (SHARED_CODE_ID,))
        
        print(f"\n{'='*60}")
        print("DATABASE SUMMARY")
        print(f"{'='*60}")
        print(f"\n[INFO] Shared Codes: {shared_code_count}")
        print(f"[INFO] Total Instruments: {instrument_count}")
        print(f"\n[INSTRUMENTS BY UNDERLYING]")
        
        for underlying, count in cursor.fetchall():
            print(f"  {underlying:<20} {count:>5} instruments")
        
        # Show sample expiries
        cursor.execute("""
            SELECT DISTINCT expiry 
            FROM instruments 
            WHERE shared_code_id = %s
            ORDER BY expiry DESC
            LIMIT 5
        """, (SHARED_CODE_ID,))
        
        print(f"\n[SAMPLE EXPIRIES]")
        for (expiry,) in cursor.fetchall():
            print(f"  {expiry}")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"[✗] Error fetching summary: {e}")
    finally:
        cursor.close()


def main():
    print(f"\n{'='*60}")
    print("SIMPLE TRADETRON DATABASE SETUP")
    print(f"{'='*60}\n")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        # Create tables
        print("[1/3] Creating tables...")
        if not create_tables(conn):
            return
        
        print()
        
        # Insert shared code
        print("[2/3] Inserting shared code...")
        if not insert_shared_code(conn):
            return
        
        print()
        
        # Insert instruments
        print("[3/3] Inserting instruments...")
        if not insert_instruments(conn):
            return
        
        print()
        
        # Show summary
        show_summary(conn)
        
        print("[SUCCESS] Database setup complete!")
        print(f"[INFO] Ready for data extraction & import")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
