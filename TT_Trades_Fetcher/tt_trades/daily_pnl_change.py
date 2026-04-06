#!/usr/bin/env python3
"""
Daily P&L Change Tracker for Positional Strategies
Shows today's P&L change with counter-wise breakdown
Usage: python daily_pnl_change.py [STRATEGY_ID]
"""

import os
import json
import base64
import pickle
import sys
from datetime import datetime, date
from pathlib import Path
import requests
from dotenv import load_dotenv
from tqdm import tqdm

# ============================================================================
# CONFIGURATION
# ============================================================================
DEFAULT_STRATEGY_ID = 25896089

if len(sys.argv) > 1:
    try:
        STRATEGY_ID = int(sys.argv[1])
    except ValueError:
        print(f"[ERROR] Invalid strategy ID: {sys.argv[1]}")
        sys.exit(1)
else:
    STRATEGY_ID = DEFAULT_STRATEGY_ID
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


def fetch_with_retry(session, url, params=None, timeout=10, retries=2):
    """Fetch URL with retry logic."""
    for attempt in range(retries):
        try:
            response = session.get(url, params=params, timeout=timeout)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            if attempt == retries - 1:
                return None
            continue
    return None


def get_counter_pnl_data(session, strategy_id, counter):
    """Get counter P&L and position data."""
    url = f"https://tradetron.tech/api/deployed/{strategy_id}"
    data = fetch_with_retry(session, url, params={"counter": counter})
    
    if not data or not data.get("success"):
        return None
    
    return data.get("data", {})


def load_previous_snapshot(strategy_id):
    """Load previous P&L snapshot if available."""
    # Look for the most recent counter_details JSON file
    pattern = f"counter_details_{strategy_id}_complete_*.json"
    matching_files = sorted(Path(".").glob(pattern), reverse=True)
    
    if not matching_files:
        return None
    
    try:
        with open(matching_files[0], "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def save_current_snapshot(strategy_id, counter_details):
    """Save current snapshot for future comparison."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"counter_details_{strategy_id}_snapshot_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(counter_details, f, indent=2, default=str)
    
    return filename


def get_max_counter(session, strategy_id):
    """Get max counter number for the strategy."""
    url = f"https://tradetron.tech/api/deployed/{strategy_id}"
    data = fetch_with_retry(session, url, params={"counter": 1})
    
    if not data or not data.get("success"):
        return 1023  # Default fallback
    
    # Extract max counter from response
    max_counter = data.get("data", {}).get("max_run_counter") or \
                  data.get("data", {}).get("run_counter") or 1023
    
    return int(max_counter)


def format_number(value, decimals=2):
    """Format number with color indicators."""
    try:
        num = float(value) if value is not None else 0
        sign = "+" if num > 0 else ""
        return f"{sign}{num:,.{decimals}f}"
    except:
        return "N/A"


def main():
    """Main execution."""
    print(f"\n{'='*90}")
    print(f"  [DAILY P&L CHANGE] Strategy {STRATEGY_ID}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*90}")
    
    # Build session
    try:
        session = build_session()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    
    # Load previous snapshot
    previous_data = load_previous_snapshot(STRATEGY_ID)
    print(f"\n[SNAPSHOT] Previous data: {('Found' if previous_data else 'Not found')}")
    
    # Get max counter
    print(f"\n[FETCH] Detecting max counter...", end=" ", flush=True)
    max_counter = get_max_counter(session, STRATEGY_ID)
    print(f"Found {max_counter} counters")
    
    # Fetch current P&L data
    print(f"[FETCH] Getting current P&L data...")
    
    counter_details = {}
    total_current_pnl = 0
    total_previous_pnl = 0
    pnl_changes = []
    
    for counter in tqdm(range(1, max_counter + 1), desc="Counters", position=0, dynamic_ncols=True, colour='green'):
        counter_data = get_counter_pnl_data(session, STRATEGY_ID, counter)
        
        if not counter_data:
            continue
            
        current_pnl = counter_data.get("sum_of_pnl", 0)
        positions = counter_data.get("calculated_positions", [])
        position_count = len(positions) if positions else 0
        
        counter_details[counter] = {
            "sum_of_pnl": current_pnl,
            "position_count": position_count,
            "calculated_positions": positions,
            "timestamp": datetime.now().isoformat()
        }
        
        total_current_pnl += current_pnl if current_pnl else 0
        
        # Calculate previous P&L if available
        previous_pnl = 0
        if previous_data and counter in previous_data:
            previous_pnl = previous_data[counter].get("sum_of_pnl", 0)
            total_previous_pnl += previous_pnl if previous_pnl else 0
        
        pnl_change = (current_pnl or 0) - (previous_pnl or 0)
        
        if position_count > 0:  # Only show counters with active positions
            pnl_changes.append({
                'counter': counter,
                'current': current_pnl or 0,
                'previous': previous_pnl or 0,
                'change': pnl_change,
                'positions': position_count
            })
    
    # Save current snapshot
    snapshot_file = save_current_snapshot(STRATEGY_ID, counter_details)
    
    # Display results
    print(f"\n{'='*90}")
    print(f"  [SUMMARY] P&L CHANGES")
    print(f"{'='*90}")
    
    if pnl_changes:
        # Sort by P&L change (descending)
        pnl_changes.sort(key=lambda x: x['change'], reverse=True)
        
        print(f"\n{'Counter':<12} {'Positions':<12} {'Current P&L':<18} {'Previous P&L':<18} {'Change':<15}")
        print(f"{'-'*90}")
        
        for item in pnl_changes:
            change_str = format_number(item['change'], 2)
            current_str = format_number(item['current'], 2)
            previous_str = format_number(item['previous'], 2)
            
            # Color indicators
            if item['change'] > 0:
                change_indicator = f"[UP]   {change_str}"
            elif item['change'] < 0:
                change_indicator = f"[DOWN] {change_str}"
            else:
                change_indicator = f"[FLAT] {change_str}"
            
            print(f"{item['counter']:<12} {item['positions']:<12} {current_str:<18} {previous_str:<18} {change_indicator:<15}")
    
    # Print totals
    print(f"\n{'='*90}")
    print(f"  [TOTALS]")
    print(f"{'='*90}")
    print(f"\nCurrent Total P&L:  {format_number(total_current_pnl, 2)}")
    
    if previous_data:
        total_change = total_current_pnl - total_previous_pnl
        print(f"Previous Total P&L: {format_number(total_previous_pnl, 2)}")
        print(f"Change Today:       {format_number(total_change, 2)}")
        
        if total_change > 0:
            print(f"\n[UP] P&L improved by {format_number(total_change, 2)} since last snapshot")
        elif total_change < 0:
            print(f"\n[DOWN] P&L declined by {format_number(abs(total_change), 2)} since last snapshot")
        else:
            print(f"\n[FLAT] No change in P&L")
    
    print(f"\nCounters with positions: {len([x for x in pnl_changes if x['positions'] > 0])}")
    print(f"Snapshot saved: {snapshot_file}")
    
    print(f"\n{'='*90}\n")


if __name__ == "__main__":
    main()
