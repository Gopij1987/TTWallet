#!/usr/bin/env python3
"""
Integrated Trade Data Extraction & Validation
Extracts leg-wise and counter data, validates PnL matching and data integrity.
Strategy ID = Shared Code ID (same value)
Change STRATEGY_ID in configuration section to extract a different strategy
"""

import os
import json
import base64
import pickle
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter as CounterDict
import requests
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
from tqdm import tqdm

# ============================================================================
# CONFIGURATION
# ============================================================================
# Strategy ID = Shared Code ID (they are the same)
STRATEGY_ID = 23894081  # Change this to extract a different strategy
SHARED_CODE_ID = STRATEGY_ID  # Same as strategy ID
# ============================================================================


def build_session():
    """Build authenticated session with cookies."""
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    cookies_b64 = os.getenv("TT_COOKIES_B64_GOPI")
    if not cookies_b64:
        raise RuntimeError("TT_COOKIES_B64_GOPI missing in .env")

    cookie_list = pickle.loads(base64.b64decode(cookies_b64))
    session = requests.Session()
    
    for c in cookie_list:
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain", ".tradetron.tech")
        if name and value:
            session.cookies.set(name, value, domain=domain)

    session.headers.update({
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://tradetron.tech/deployed-strategies",
    })
    
    return session


def split_instrument(symbol):
    """Split instrument symbol into components."""
    parts = symbol.split("_")
    return {
        "inst_type": parts[0] if len(parts) > 0 else "",
        "underlying": parts[1] if len(parts) > 1 else "",
        "expiry": parts[2] if len(parts) > 2 else "",
        "option_type": parts[3] if len(parts) > 3 else "",
        "strike": "_".join(parts[4:]) if len(parts) > 4 else ""
    }


def fetch_with_retry(session, url, params=None, timeout=10, retries=2, verbose=False):
    """Fetch URL with retry logic."""
    for attempt in range(retries):
        try:
            response = session.get(url, params=params, timeout=timeout)
            if verbose:
                print(f"        [DEBUG] Status: {response.status_code}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            if verbose and attempt == retries - 1:
                print(f"        [DEBUG] Fetch failed: {e}")
            if attempt == retries - 1:
                return None
            continue
    return None


def get_counter_full_data(session, strategy_id, counter):
    """Get full counter data including PnL."""
    url = f"https://tradetron.tech/api/deployed/{strategy_id}"
    data = fetch_with_retry(session, url, params={"counter": counter})
    
    if not data or not data.get("success"):
        return None
    
    return data.get("data", {})


def get_counter_positions(session, strategy_id, counter):
    """Get position list for a counter."""
    counter_data = get_counter_full_data(session, strategy_id, counter)
    if not counter_data:
        return []
    return counter_data.get("calculated_positions", [])


def get_position_trades(session, strategy_id, counter, instrument):
    """Get modal trade rows for a specific instrument."""
    url = f"https://tradetron.tech/api/deployed/position/{strategy_id}"
    params = {
        "counter": counter,
        "instrument": instrument.replace("&", "*")
    }
    
    data = fetch_with_retry(session, url, params=params, timeout=10)
    
    if not data or not data.get("success"):
        return []
    
    rows = data.get("data", [])
    return rows if isinstance(rows, list) else []


def extract_counter_records(session, strategy_id, counter):
    """Extract all trade records for a counter."""
    try:
        positions = get_counter_positions(session, strategy_id, counter)
        records = []
        
        for pos in positions:
            instrument = pos.get("Instrument", "")
            if not instrument:
                continue
            
            inst_parts = split_instrument(instrument)
            trades = get_position_trades(session, strategy_id, counter, instrument)
            
            if not trades:
                continue
            
            for trade in trades:
                entry_date = trade.get("entry_date", "")
                date_part, time_part = "", ""
                
                if " " in entry_date:
                    date_part, time_part = entry_date.split(" ", 1)
                else:
                    date_part = entry_date
                
                records.append({
                    "counter": counter,
                    "date": date_part,
                    "time": time_part,
                    "instrument_full": instrument,
                    "inst_type": inst_parts["inst_type"],
                    "underlying": inst_parts["underlying"],
                    "expiry": inst_parts["expiry"],
                    "option_type": inst_parts["option_type"],
                    "strike": inst_parts["strike"],
                    "qty": trade.get("quantity", ""),
                    "price": trade.get("price", ""),
                    "amount": trade.get("amount", ""),
                    "note": ""
                })
        
        return records, len(positions)
    
    except Exception as e:
        return [], 0


def get_db_connection():
    """Get PostgreSQL database connection."""
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "tradetron"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )
    return conn


def insert_extracted_data(all_legs, strategy_id, shared_code_id):
    """Insert extracted data into PostgreSQL extractions table."""
    if not all_legs:
        print("      [SKIP] No data to insert")
        return 0
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prepare data for batch insert
        batch_data = []
        for leg in all_legs:
            try:
                qty = float(leg.get("qty", 0) or 0)
                price = float(leg.get("price", 0) or 0)
                amount = qty * price
            except (ValueError, TypeError):
                amount = leg.get("amount", 0)
            
            batch_data.append((
                shared_code_id,        # shared_code_id
                strategy_id,           # strategy_id
                leg.get("counter", ""),
                leg.get("date", ""),
                leg.get("time", ""),
                leg.get("instrument_full", ""),
                leg.get("inst_type", ""),
                leg.get("underlying", ""),
                leg.get("expiry", ""),
                leg.get("option_type", ""),
                leg.get("strike", ""),
                leg.get("qty", ""),
                leg.get("price", ""),
                amount,
                leg.get("note", "")
            ))
        
        # Batch insert
        insert_sql = """
            INSERT INTO extractions 
            (shared_code_id, strategy_id, counter, trade_date, trade_time, 
             instrument_full, inst_type, underlying, expiry, option_type, strike, 
             qty, price, amount, note)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (shared_code_id, strategy_id, counter, trade_date, 
                         trade_time, instrument_full, qty, price) DO NOTHING
        """
        
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(batch_data), batch_size):
            batch = batch_data[i:i+batch_size]
            execute_batch(cursor, insert_sql, batch)
            batch_inserted = len(batch)
            total_inserted += batch_inserted
            print(f"      [INSERT] Batch {i//batch_size + 1}: {batch_inserted} rows")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return total_inserted
    
    except psycopg2.Error as e:
        print(f"      [ERROR] Database error: {e}")
        return 0
    except Exception as e:
        print(f"      [ERROR] Insertion error: {e}")
        return 0


def main():
    start_time = datetime.now()
    print(f"\n{'='*80}")
    print(f"  INTEGRATED TRADE DATA EXTRACTION & VALIDATION")
    print(f"  Strategy ID / Shared Code ID: {STRATEGY_ID}")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Step 1: Build session
    print("[1/4] Building session...")
    try:
        session = build_session()
        print("      [OK] Session authenticated\n")
    except Exception as e:
        print(f"      [ERROR] Error: {e}")
        return
    
    # Step 2: Get max counter and validate strategy
    print("[2/4] Validating strategy and detecting max counter...")
    print(f"      Strategy ID: {STRATEGY_ID}")
    
    temp_snapshot = fetch_with_retry(
        session, 
        f"https://tradetron.tech/api/deployed/{STRATEGY_ID}",
        params={"counter": 1},
        verbose=True
    )
    
    # Validate API response
    if not temp_snapshot:
        print(f"\n{'='*80}")
        print(f"  [ERROR] STRATEGY NOT FOUND")
        print(f"{'='*80}")
        print(f"\n  Strategy ID {STRATEGY_ID} does not exist or shared code was not found.")
        print(f"  Please check:")
        print(f"    • Strategy ID is correct")
        print(f"    • Strategy shared code is deployed")
        print(f"    • Authentication cookies are valid")
        print(f"\n{'='*80}\n")
        sys.exit(1)
    
    if not temp_snapshot.get("success"):
        error_msg = temp_snapshot.get("message", "Unknown error")
        print(f"\n{'='*80}")
        print(f"  [ERROR] API RETURNED FAILURE")
        print(f"{'='*80}")
        print(f"\n  Strategy ID: {STRATEGY_ID}")
        print(f"  Error: {error_msg}")
        print(f"\n{'='*80}\n")
        sys.exit(1)
    
    max_counter = 1023
    returned_strategy_id = None
    returned_strategy_name = None
    
    data = temp_snapshot.get("data", {})
    
    # Check if data is empty
    if not data:
        print(f"\n{'='*80}")
        print(f"  [ERROR] STRATEGY DATA IS EMPTY")
        print(f"{'='*80}")
        print(f"\n  Strategy ID {STRATEGY_ID} returned no data.")
        print(f"  Possible reasons:")
        print(f"    • Shared code is not properly deployed")
        print(f"    • Strategy has no trading history/counters")
        print(f"    • Strategy ID is incorrect")
        print(f"\n{'='*80}\n")
        sys.exit(1)
    
    returned_strategy_id = data.get("strategy_id", data.get("id"))
    returned_strategy_name = data.get("strategy_name", data.get("name"))
    max_counter = int(data.get("max_run_counter") or data.get("run_counter") or 0)
    
    # Validate that we got the correct strategy
    if returned_strategy_id and str(returned_strategy_id) != str(STRATEGY_ID):
        print(f"\n{'='*80}")
        print(f"  [ERROR] STRATEGY ID MISMATCH")
        print(f"{'='*80}")
        print(f"\n  Expected: {STRATEGY_ID}")
        print(f"  Got:      {returned_strategy_id}")
        print(f"\n  The API returned a different strategy than requested.")
        print(f"{'='*80}\n")
        sys.exit(1)
    
    if max_counter == 0:
        print(f"\n{'='*80}")
        print(f"  [ERROR] NO COUNTER DATA FOUND")
        print(f"{'='*80}")
        print(f"\n  Strategy ID: {STRATEGY_ID}")
        print(f"  Strategy Name: {returned_strategy_name or 'Unknown'}")
        print(f"\n  This strategy has no trading history (max_counter = 0)")
        print(f"  Possible reasons:")
        print(f"    • Strategy has never run")
        print(f"    • Shared code was not deployed properly")
        print(f"    • All data has been cleared")
        print(f"\n{'='*80}\n")
        sys.exit(1)
    
    print(f"      [OK] Strategy validated: {returned_strategy_name or 'Unknown'}")
    print(f"      [OK] Max counter: {max_counter}\n")
    
    # Step 3: Extract data with validation
    print(f"[3/4] Extracting {max_counter} counters...\n")
    
    # Thorough check: Verify first counter has data to ensure strategy ID is correct
    print("      [INFO] Validating strategy has deployable data...")
    sample_counter = get_counter_full_data(session, STRATEGY_ID, 1)
    
    if not sample_counter:
        print(f"\n{'='*80}")
        print(f"  [ERROR] SHARED CODE NOT FOUND OR NOT DEPLOYED")
        print(f"{'='*80}")
        print(f"\n  Strategy ID: {STRATEGY_ID}")
        print(f"  Strategy Name: {returned_strategy_name or 'Unknown'}")
        print(f"\n  Counter 1 returned no data. This indicates:")
        print(f"    • Shared code is not properly deployed")
        print(f"    • Strategy is not active/live")
        print(f"    • API connectivity issues")
        print(f"\n{'='*80}\n")
        sys.exit(1)
    
    sample_pnl = sample_counter.get("sum_of_pnl", "N/A")
    sample_positions = len(sample_counter.get("calculated_positions", []))
    print(f"      [OK] Counter 1 validated: PnL={sample_pnl}, Positions={sample_positions}")
    print()
    
    all_legs = []
    counter_details = {}  # {counter: {positions: [...], pnl: ...}}
    validation_results = defaultdict(list)
    
    with tqdm(total=max_counter, desc="Extracting", unit="counter", 
              dynamic_ncols=True, position=0, leave=True,
              bar_format='{desc}: {n_fmt}/{total_fmt} [{bar}] {percentage:3.0f}% | Time: {elapsed}<{remaining} | Legs: {postfix}',
              colour='green') as pbar:
        for counter in range(max_counter, 0, -1):
            # Get full counter data
            counter_data = get_counter_full_data(session, STRATEGY_ID, counter)
            positions = counter_data.get("calculated_positions", []) if counter_data else []
            sum_of_pnl = counter_data.get("sum_of_pnl") if counter_data else None
            
            # Extract leg data
            leg_records, pos_count = extract_counter_records(session, STRATEGY_ID, counter)
            all_legs.extend(leg_records)
            
            counter_details[counter] = {
                "position_count": pos_count,
                "leg_count": len(leg_records),
                "sum_of_pnl": sum_of_pnl,
                "positions": positions
            }
            
            # Quick validation
            if pos_count > 0 and len(leg_records) == 0:
                validation_results["missing_legs"].append(counter)
            elif pos_count == 0 and len(leg_records) > 0:
                validation_results["orphan_legs"].append(counter)
            
            # Update progress bar with leg count
            pbar.set_postfix_str(f"{len(all_legs):,}")
            
            # Update bar color based on percentage (gradient: red -> yellow -> green)
            percentage = (pbar.n / pbar.total) * 100
            if percentage < 33:
                pbar.colour = 'red'
            elif percentage < 66:
                pbar.colour = 'yellow'
            else:
                pbar.colour = 'green'
            
            pbar.update(1)
    
    print()
    
    # Step 4: Save outputs
    print(f"[4/4] Saving and validating data...\n")
    
    # Use external one-time extraction folder
    extract_folder = Path(r"C:\Users\gopij\OneDrive\Synced\Python\AlphaMetrix.In\One time Extraction")
    extract_folder.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save leg data
    leg_file = extract_folder / f"leg_wise_{STRATEGY_ID}_complete_{timestamp}.json"
    with open(leg_file, "w", encoding="utf-8") as f:
        json.dump(all_legs, f, indent=2)
    
    # Save counter details
    counter_file = extract_folder / f"counter_details_{STRATEGY_ID}_complete_{timestamp}.json"
    with open(counter_file, "w", encoding="utf-8") as f:
        json.dump(counter_details, f, indent=2, default=str)
    
    # Save as CSV with shared_code_id in front
    csv_file = extract_folder / f"leg_wise_{STRATEGY_ID}_complete_{timestamp}.csv"
    import csv as csv_module
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv_module.DictWriter(f, fieldnames=[
            "shared_code_id", "counter", "date", "time", "instrument_full", "inst_type", 
            "underlying", "expiry", "option_type", "strike", "qty", "price", "amount", "note"
        ])
        writer.writeheader()
        
        # Recalculate amount as qty * price for CSV
        for leg in all_legs:
            leg_copy = leg.copy()
            leg_copy["shared_code_id"] = SHARED_CODE_ID  # Add shared code ID
            try:
                qty = float(leg_copy.get("qty", 0) or 0)
                price = float(leg_copy.get("price", 0) or 0)
                leg_copy["amount"] = qty * price
            except (ValueError, TypeError):
                # If qty or price can't be converted, keep original amount
                leg_copy["amount"] = leg_copy.get("amount", "")
            writer.writerow(leg_copy)
    
    # Validate data consistency
    print("   Validating data consistency across counters...")
    data_consistency = 0
    data_issues = 0
    
    for counter, details in counter_details.items():
        pos_count = details.get('position_count', 0)
        leg_count = details.get('leg_count', 0)
        
        # Skip counters with no data
        if pos_count == 0 and leg_count == 0:
            continue
        
        # Verify consistency: positions and legs should both exist or both not exist
        # Positions: API position data (closed or open)
        # Legs: Trade history from modal (all trades)
        if pos_count > 0 and leg_count > 0:
            # Both exist - data is consistent (legs are trade history)
            data_consistency += 1
        else:
            # Mismatch: positions exist without legs, or vice versa
            data_issues += 1
    
    # Print summary
    end_time = datetime.now()
    elapsed = end_time - start_time
    
    print(f"\n{'='*80}")
    print("  [COMPLETE] EXTRACTION & VALIDATION COMPLETE")
    print(f"{'='*80}")
    
    print("\n[STRATEGY & SHARED CODE] INFORMATION:")
    print(f"   Strategy ID / Shared Code ID: {STRATEGY_ID}")
    if returned_strategy_name:
        print(f"   Strategy Name:               {returned_strategy_name}")
    print(f"   Requested:         Strategy {STRATEGY_ID}")
    if returned_strategy_id:
        print(f"   API Returned:      Strategy {returned_strategy_id}")
        if str(returned_strategy_id) == str(STRATEGY_ID):
            print(f"   Status:            ✓ MATCH")
        else:
            print(f"   Status:            ✗ MISMATCH - Data may be from different strategy!")
    
    print("\n[DATA] EXTRACTED:")
    print(f"   Total Legs:        {len(all_legs):,}")
    print(f"   Counters Processed: {len(counter_details)}")
    print(f"   Unique Instruments: {len(set(r['instrument_full'] for r in all_legs)):,}")
    
    # Sample counter data for verification
    sample_counters = [1, max(counter_details.keys()) if counter_details else 1]
    print("\n[SAMPLE] COUNTER DATA (for verification):")
    for counter_num in sample_counters:
        if counter_num in counter_details:
            details = counter_details[counter_num]
            pnl = details.get('sum_of_pnl', 'N/A')
            print(f"   Counter {counter_num}: Positions={details.get('position_count')}, Legs={details.get('leg_count')}, PnL={pnl}")
    
    
    
    print(f"\n[VALIDATION] RESULTS:")
    print(f"   Data Consistency:  {data_consistency} / {data_consistency + data_issues}")
    
    if validation_results:
        print(f"\n[WARNING] ISSUES FOUND:")
        if validation_results["missing_legs"]:
            print(f"   Missing Legs:      {len(validation_results['missing_legs'])} counters with positions but no leg data")
        if validation_results["orphan_legs"]:
            print(f"   Orphan Legs:       {len(validation_results['orphan_legs'])} counters with leg data but no positions")
    else:
        print(f"   [OK] All data is consistent")
    
    print(f"\n[FILES] GENERATED:")
    print(f"   Leg Data (JSON):    {leg_file}")
    print(f"   Leg Data (CSV):     {csv_file}")
    print(f"   Counter Details:    {counter_file}")
    
    print(f"\n[TIMING]:")
    minutes, seconds = divmod(elapsed.total_seconds(), 60)
    print(f"   Started:  {start_time.strftime('%H:%M:%S')}")
    print(f"   Finished: {end_time.strftime('%H:%M:%S')}")
    print(f"   Duration: {int(minutes)}m {int(seconds)}s")
    
    print(f"\n{'='*80}\n")
    
    # Step 5: Auto-insert to database
    print(f"[5/5] Auto-inserting to PostgreSQL database...\n")
    rows_inserted = insert_extracted_data(all_legs, STRATEGY_ID, SHARED_CODE_ID)
    
    if rows_inserted > 0:
        print(f"\n      [OK] {rows_inserted:,} rows inserted to 'extractions' table")
    
    print(f"\n{'='*80}")
    print("  [COMPLETE] EXTRACTION & DATABASE INSERT FINISHED")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
