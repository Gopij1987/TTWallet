#!/usr/bin/env python3
"""
Cross-validate leg-wise and counter-wise API data.
Shows detailed comparison for each counter's instruments.
"""

import json
import csv
from pathlib import Path
from collections import defaultdict

def load_leg_data(csv_file):
    """Load and aggregate leg-wise data."""
    leg_data = defaultdict(lambda: defaultdict(lambda: {"trades": []}))
    
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            counter = int(row["counter"])
            instrument = row["instrument_full"]
            qty = float(row["qty"])
            price = float(row["price"])
            amount = float(row["amount"])
            
            leg_data[counter][instrument]["trades"].append({
                "qty": qty,
                "price": price,
                "amount": amount
            })
    
    # Calculate summaries
    for counter in leg_data:
        for instrument in leg_data[counter]:
            trades = leg_data[counter][instrument]["trades"]
            entry_trades = [t for t in trades if t["qty"] > 0]
            exit_trades = [t for t in trades if t["qty"] < 0]
            
            entry_qty = sum(t["qty"] for t in entry_trades)
            exit_qty = sum(abs(t["qty"]) for t in exit_trades)
            
            leg_data[counter][instrument].update({
                "entry_qty": entry_qty,
                "exit_qty": exit_qty,
                "net_qty": entry_qty - exit_qty,
                "trade_count": len(trades)
            })
    
    return leg_data

def load_api_data(json_file):
    """Load API counter-wise data."""
    api_data = defaultdict(dict)
    
    with open(json_file) as f:
        data = json.load(f)
    
    for counter_data in data:
        counter = counter_data["counter"]
        total_pnl = counter_data.get("pnl", 0)
        total_positions = counter_data.get("total_positions", 0)
        
        api_data[counter] = {
            "total_pnl": total_pnl,
            "total_positions": total_positions,
            "summary": {
                "pnl": total_pnl,
                "num_positions": total_positions
            }
        }
    
    return api_data

def generate_comparison_report(leg_data, api_data):
    """Generate detailed comparison report."""
    
    report = {
        "summary": {
            "leg_counters": len(leg_data),
            "api_counters": len(api_data),
            "leg_instruments": sum(len(insts) for insts in leg_data.values()),
            "api_positions": sum(api_data[c]["total_positions"] for c in api_data),
            "total_trades": sum(sum(inst["trade_count"] for inst in counter.values()) 
                               for counter in leg_data.values())
        },
        "validation": {
            "counters_in_both": 0,
            "counters_only_leg": [],
            "counters_only_api": [],
            "pnl_match_details": []
        }
    }
    
    leg_counters = set(leg_data.keys())
    api_counters = set(api_data.keys())
    
    # Counters in both
    counters_both = leg_counters & api_counters
    report["validation"]["counters_in_both"] = len(counters_both)
    
    # Counters only in leg (extracted from transactions)
    report["validation"]["counters_only_leg"] = sorted(list(leg_counters - api_counters))
    
    # Counters only in API
    report["validation"]["counters_only_api"] = sorted(list(api_counters - leg_counters))
    
    # Detailed comparison for sample counters
    for counter in sorted(counters_both, reverse=True)[:10]:
        leg_inst_count = len(leg_data[counter])
        api_pos_count = api_data[counter]["total_positions"]
        
        # Calculate leg-wise total P&L
        leg_total_pnl = 0
        for instrument in leg_data[counter]:
            entry_qty = leg_data[counter][instrument]["entry_qty"]
            exit_qty = leg_data[counter][instrument]["exit_qty"]
            trades = leg_data[counter][instrument]["trades"]
            
            if entry_qty > 0 and exit_qty > 0:
                entry_trades = [t for t in trades if t["qty"] > 0]
                exit_trades = [t for t in trades if t["qty"] < 0]
                entry_price = sum(t["amount"] for t in entry_trades) / entry_qty
                exit_price = sum(abs(t["amount"]) for t in exit_trades) / exit_qty
                leg_total_pnl += (exit_price * exit_qty) - (entry_price * exit_qty)
        
        api_pnl = api_data[counter]["total_pnl"]
        
        report["validation"]["pnl_match_details"].append({
            "counter": counter,
            "leg_instruments": leg_inst_count,
            "api_positions": api_pos_count,
            "leg_total_pnl": round(leg_total_pnl, 2),
            "api_total_pnl": round(api_pnl, 2),
            "pnl_match": "✓" if abs(leg_total_pnl - api_pnl) < 100 else "✗",
            "pnl_diff": round(abs(leg_total_pnl - api_pnl), 2)
        })
    
    return report

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cross-validate leg-wise vs API counter data")
    parser.add_argument("--leg-csv", help="Leg-wise CSV")
    parser.add_argument("--api-json", help="API JSON")
    args = parser.parse_args()
    
    tt_trades = Path(__file__).parent
    
    if not args.leg_csv:
        leg_csvs = sorted(tt_trades.glob("counters_modal_rows_*.csv"))
        args.leg_csv = str(leg_csvs[-1]) if leg_csvs else None
    
    if not args.api_json:
        api_jsons = sorted(tt_trades.glob("counterwise_snapshot_7147483_*.json"))
        args.api_json = str(api_jsons[-1]) if api_jsons else None
    
    print(f"[*] Loading leg-wise data from {Path(args.leg_csv).name}...")
    leg_data = load_leg_data(args.leg_csv)
    print(f"    {len(leg_data)} counters, {sum(len(i) for i in leg_data.values())} instruments")
    
    print(f"[*] Loading API data from {Path(args.api_json).name}...")
    api_data = load_api_data(args.api_json)
    print(f"    {len(api_data)} counters")
    
    print(f"[*] Comparing data...")
    report = generate_comparison_report(leg_data, api_data)
    
    # Save report
    timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"cross_validation_report_{timestamp}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print report
    print("\n" + "="*90)
    print("CROSS-VALIDATION REPORT: Leg-Wise vs API Counter Data")
    print("="*90)
    
    print(f"\n📊 Summary:")
    print(f"  Leg-Wise Counters: {report['summary']['leg_counters']}")
    print(f"  API Counters: {report['summary']['api_counters']}")
    print(f"  Leg-Wise Instruments: {report['summary']['leg_instruments']}")
    print(f"  API Positions: {report['summary']['api_positions']}")
    print(f"  Total Trades Extracted: {report['summary']['total_trades']}")
    
    print(f"\n✓ Counters in Both Sources: {report['validation']['counters_in_both']}")
    print(f"  Only in Leg-Wise: {len(report['validation']['counters_only_leg'])}")
    print(f"  Only in API: {len(report['validation']['counters_only_api'])}")
    
    print(f"\n💰 P&L Comparison (Top 10 matched counters):")
    print(f"  {'Counter':<10} {'Leg Inst':<12} {'API Pos':<12} {'Leg PnL':<15} {'API PnL':<15} {'Diff':<12} {'Match':<8}")
    print(f"  {'-'*98}")
    for detail in report['validation']['pnl_match_details'][:10]:
        print(f"  {detail['counter']:<10} {detail['leg_instruments']:<12} {detail['api_positions']:<12} "
              f"₹{detail['leg_total_pnl']:<14,.2f} ₹{detail['api_total_pnl']:<14,.2f} "
              f"₹{detail['pnl_diff']:<11,.2f} {detail['pnl_match']:<8}")
    
    print(f"\n[✓] Detailed report saved to: {report_file}")
    print("="*90)

if __name__ == "__main__":
    main()
