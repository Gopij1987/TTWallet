"""
GET DETAILS FOR SPECIFIC RUN
Extract and display detailed information for a specific run/trade
"""

import json
from pathlib import Path
import statistics

def get_run_details(strategy_id: int, run_number: int):
    """Get detailed information for a specific run"""
    
    # Find the API extraction file
    search_pattern = f"api_extraction_{strategy_id}_*.json"
    files = list(Path(__file__).parent.glob(search_pattern))
    
    if not files:
        print(f"❌ No extraction file found for strategy {strategy_id}")
        return None
    
    # Use the most recent file
    latest_file = sorted(files)[-1]
    
    print(f"Reading: {latest_file.name}")
    
    with open(latest_file, 'r') as f:
        strategy_data = json.load(f)
    
    # Get run history
    run_history = strategy_data.get('filtered_run_counter', [])
    
    if not run_history:
        print("❌ No run history found")
        return None
    
    # Find the specific run
    target_run = None
    for run in run_history:
        if run.get('run_counter') == run_number:
            target_run = run
            break
    
    if not target_run:
        print(f"❌ Run {run_number} not found")
        available = [r.get('run_counter') for r in run_history]
        print(f"Available runs: {min(available)} to {max(available)}")
        return None
    
    return target_run, run_history, strategy_data

def display_run_details(strategy_id: int, run_number: int):
    """Display detailed information for a run"""
    
    print("\n" + "=" * 90)
    print(f"RUN #{run_number} - STRATEGY {strategy_id} DETAILS")
    print("=" * 90)
    
    result = get_run_details(strategy_id, run_number)
    
    if not result:
        return
    
    target_run, run_history, strategy_data = result
    
    # Extract run data
    run_pnl = target_run.get('pnl', 0)
    
    print("\n📊 RUN INFORMATION")
    print("-" * 90)
    print(f"Run Number:           {target_run.get('run_counter')}")
    print(f"P&L (₹):              {run_pnl:,.2f}")
    print(f"Status:               {'✓ PROFIT' if run_pnl > 0 else '✗ LOSS' if run_pnl < 0 else '= BREAK-EVEN'}")
    
    # Position data from the extraction
    positions = strategy_data.get('calculated_positions', [])
    
    print("\n📍 POSITIONS AT TIME OF RUN")
    print("-" * 90)
    
    if positions:
        print(f"{'Instrument':<45} {'Type':<5} {'Qty':<6} {'Entry':<10} {'LTP':<10}")
        print("-" * 90)
        
        for pos in positions:
            symbol = pos.get('Instrument', 'N/A')[:42]
            opt_type = pos.get('option_type', '')
            qty = pos.get('quantity', 0)
            entry = pos.get('price', 0)
            ltp = pos.get('ltp', 0)
            
            print(f"{symbol:<45} {opt_type:<5} {qty:<6} ₹{entry:<9.2f} ₹{ltp:<9.2f}")
    
    # Statistics about this run
    print("\n📈 RUN STATISTICS")
    print("-" * 90)
    
    total_runs = len(run_history)
    pnls = [r.get('pnl', 0) for r in run_history]
    
    # Find position in ranking
    sorted_pnls = sorted(enumerate(pnls), key=lambda x: x[1], reverse=True)
    for rank, (idx, pnl) in enumerate(sorted_pnls, 1):
        if pnls[idx] == run_pnl and run_history[idx].get('run_counter') == run_number:
            print(f"Rank (Best P&L):      #{rank} of {total_runs}")
            break
    
    # Compare to average
    avg_pnl = statistics.mean(pnls)
    std_dev = statistics.stdev(pnls) if len(pnls) > 1 else 0
    
    print(f"vs Average P&L:       {run_pnl - avg_pnl:+,.2f}")
    print(f"Average P&L:          ₹{avg_pnl:,.2f}")
    print(f"Std Deviation:        ₹{std_dev:,.2f}")
    
    # Percentiles
    best = max(pnls)
    worst = min(pnls)
    
    print(f"Best Run P&L:         ₹{best:,.2f}")
    print(f"Worst Run P&L:        ₹{worst:,.2f}")
    print(f"Range:                ₹{best - worst:,.2f}")
    
    # Percentage of best/worst
    if best != 0:
        pct_of_best = (run_pnl / best * 100) if best > 0 else 0
        print(f"% of Best Run:        {pct_of_best:.1f}%")
    
    # Count runs around this value
    within_range = sum(1 for p in pnls if abs(p - run_pnl) < abs(std_dev))
    print(f"Runs within ±1σ:      {within_range} ({within_range/total_runs*100:.1f}%)")
    
    # Win/Loss stats
    wins = sum(1 for p in pnls if p > 0)
    losses = sum(1 for p in pnls if p < 0)
    breakeven = sum(1 for p in pnls if p == 0)
    
    print("\n📊 OVERALL STRATEGY STATS")
    print("-" * 90)
    print(f"Total Runs:           {total_runs}")
    print(f"Winning Runs:         {wins} ({wins/total_runs*100:.1f}%)")
    print(f"Losing Runs:          {losses} ({losses/total_runs*100:.1f}%)")
    print(f"Break-even Runs:      {breakeven}")
    print(f"Total Strategy P&L:   ₹{strategy_data.get('sum_of_pnl', 0):,.2f}")
    
    # Context around this run
    run_index = next((i for i, r in enumerate(run_history) if r.get('run_counter') == run_number), -1)
    
    if run_index >= 0:
        print("\n📋 SURROUNDING RUNS (Context)")
        print("-" * 90)
        
        start = max(0, run_index - 2)
        end = min(len(run_history), run_index + 3)
        
        print(f"{'Run':<8} {'P&L':<15} {'Status':<12}")
        print("-" * 90)
        
        for i in range(start, end):
            run = run_history[i]
            r_num = run.get('run_counter')
            r_pnl = run.get('pnl', 0)
            r_status = "✓ PROFIT" if r_pnl > 0 else ("✗ LOSS" if r_pnl < 0 else "= BREAK-EVEN")
            
            marker = " << THIS RUN" if r_num == run_number else ""
            print(f"Run {r_num:<6} ₹{r_pnl:>13,.2f}  {r_status:<12}{marker}")
    
    print("\n" + "=" * 90)

if __name__ == "__main__":
    import sys
    
    strategy_id = int(sys.argv[1]) if len(sys.argv) > 1 else 7147483
    run_number = int(sys.argv[2]) if len(sys.argv) > 2 else 1023
    
    display_run_details(strategy_id, run_number)
