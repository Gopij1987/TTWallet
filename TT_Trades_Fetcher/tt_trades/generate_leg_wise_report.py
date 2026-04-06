#!/usr/bin/env python3
"""
Generate comprehensive validation and summary report from leg-wise transaction data.
This treats the leg-wise (modal) data as the source of truth.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def load_and_aggregate_leg_data(csv_file):
    """Load leg-wise data and aggregate by counter and instrument."""
    data = defaultdict(lambda: defaultdict(list))
    
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            counter = int(row["counter"])
            instrument = row["instrument_full"]
            qty = float(row["qty"])
            price = float(row["price"])
            amount = float(row["amount"])
            date = row["date"]
            time = row["time"]
            
            data[counter][instrument].append({
                "qty": qty,
                "price": price,
                "amount": amount,
                "date": date,
                "time": time,
                "datetime_str": f"{date} {time}"
            })
    
    return data

def calculate_position_summary(trades):
    """Calculate position summary from list of trades."""
    
    # Separate entry and exit
    entry_trades = [t for t in trades if t["qty"] > 0]
    exit_trades = [t for t in trades if t["qty"] < 0]
    
    # Calculate totals
    entry_qty = sum(t["qty"] for t in entry_trades)
    entry_amount = sum(t["amount"] for t in entry_trades)
    exit_qty = sum(abs(t["qty"]) for t in exit_trades)
    exit_amount = sum(abs(t["amount"]) for t in exit_trades)
    
    # Calculate average prices
    entry_price = entry_amount / entry_qty if entry_qty > 0 else 0
    exit_price = exit_amount / exit_qty if exit_qty > 0 else 0
    
    # Calculate net position and P&L
    net_qty = entry_qty - exit_qty
    realized_pnl = 0
    if entry_qty > 0 and exit_qty > 0:
        realized_pnl = (exit_price * exit_qty) - (entry_price * exit_qty)
    
    # Get first and last trade dates
    all_dates = [t["datetime_str"] for t in trades]
    first_trade = min(all_dates) if all_dates else ""
    last_trade = max(all_dates) if all_dates else ""
    
    return {
        "num_trades": len(trades),
        "entry_qty": entry_qty,
        "exit_qty": exit_qty,
        "net_qty": net_qty,
        "entry_price": round(entry_price, 2),
        "exit_price": round(exit_price, 2),
        "entry_amount": round(entry_amount, 2),
        "exit_amount": round(exit_amount, 2),
        "realized_pnl": round(realized_pnl, 2),
        "first_trade": first_trade,
        "last_trade": last_trade
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate leg-wise validation and summary report")
    parser.add_argument("--input", help="Input leg-wise CSV file")
    args = parser.parse_args()
    
    tt_trades = Path(__file__).parent
    
    if not args.input:
        leg_csvs = sorted(tt_trades.glob("counters_modal_rows_*.csv"))
        if leg_csvs:
            args.input = str(leg_csvs[-1])
            print(f"[*] Using: {args.input}")
    
    if not args.input or not Path(args.input).exists():
        print("Error: Leg CSV not found")
        return
    
    print(f"[*] Loading leg-wise data...")
    leg_data = load_and_aggregate_leg_data(args.input)
    print(f"    Loaded {len(leg_data)} counters with {sum(len(i) for i in leg_data.values())} instruments")
    
    # Generate summary report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"leg_wise_validation_report_{timestamp}.json"
    
    report = {
        "generated": datetime.now().isoformat(),
        "source_file": Path(args.input).name,
        "summary": {
            "total_counters": len(leg_data),
            "total_instruments": sum(len(i) for i in leg_data.values()),
            "total_trades": sum(sum(len(t) for t in insts.values()) for insts in leg_data.values())
        },
        "counters": {}
    }
    
    # Process each counter
    for counter in sorted(leg_data.keys(), reverse=True):
        instruments = leg_data[counter]
        counter_data = {
            "instruments": {},
            "summary": {
                "total_instruments": len(instruments),
                "total_trades": sum(len(t) for t in instruments.values())
            }
        }
        
        # Process each instrument
        for instrument, trades in sorted(instruments.items()):
            position_summary = calculate_position_summary(trades)
            counter_data["instruments"][instrument] = position_summary
        
        # Calculate counter-level totals
        counter_totals = {
            "total_qty_traded": sum(abs(p["entry_qty"]) for p in counter_data["instruments"].values()),
            "total_pnl": sum(p["realized_pnl"] for p in counter_data["instruments"].values()),
            "instruments_traded": len(instruments)
        }
        counter_data["totals"] = counter_totals
        
        report["counters"][str(counter)] = counter_data
    
    # Save report
    print(f"\n[*] Saving validation report to {report_file}...")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("LEG-WISE DATA VALIDATION REPORT")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"  Total Counters: {report['summary']['total_counters']}")
    print(f"  Total Instruments: {report['summary']['total_instruments']}")
    print(f"  Total Trades: {report['summary']['total_trades']}")
    
    # Top 10 counters by P&L
    print(f"\n💰 Top 10 Counters by P&L:")
    counters_by_pnl = [(c, report["counters"][c]["totals"]["total_pnl"]) 
                       for c in report["counters"].keys()]
    counters_by_pnl.sort(key=lambda x: x[1], reverse=True)
    for i, (counter, pnl) in enumerate(counters_by_pnl[:10], 1):
        print(f"  {i}. Counter {counter}: ₹{pnl:,.2f}")
    
    # Sample counter details
    print(f"\n📋 Sample Details (Counter 1023):")
    if "1023" in report["counters"]:
        c1023 = report["counters"]["1023"]
        print(f"  Total Instruments: {c1023['summary']['total_instruments']}")
        print(f"  Total Trades: {c1023['summary']['total_trades']}")
        for inst, pos in list(c1023["instruments"].items())[:2]:
            print(f"\n    {inst}:")
            print(f"      Trades: {pos['num_trades']}")
            print(f"      Entry Qty: {pos['entry_qty']} @ ₹{pos['entry_price']}")
            print(f"      Exit Qty: {pos['exit_qty']} @ ₹{pos['exit_price']}")
            print(f"      Net Qty: {pos['net_qty']}")
            print(f"      P&L: ₹{pos['realized_pnl']}")
    
    print(f"\n[✓] Report saved to: {report_file}")
    print("="*80)

if __name__ == "__main__":
    main()
