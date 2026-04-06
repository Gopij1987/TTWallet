#!/usr/bin/env python3
"""
Cross-check API counter-wise PnL with leg-wise summed PnL.

Objective:
- Use API snapshot data (counter-wise PnL) as one source.
- Compute leg-wise PnL sum per counter from extracted leg CSV.
- Compare both and report matches/mismatches.
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


def safe_float(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def load_leg_counter_pnl(leg_csv_path):
    """Compute counter-wise leg PnL from transaction rows.

    Per instrument per counter:
    - entries: qty > 0
    - exits: qty < 0
    - realized_pnl = (avg_exit - avg_entry) * matched_exit_qty
    Counter leg pnl is sum of instrument realized pnl.
    """
    per_counter_instrument = defaultdict(lambda: defaultdict(list))

    with open(leg_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            counter = int(row.get("counter", 0))
            instrument = row.get("instrument_full", "")
            qty = safe_float(row.get("qty", 0))
            amount = safe_float(row.get("amount", 0))
            per_counter_instrument[counter][instrument].append(
                {"qty": qty, "amount": amount}
            )

    counter_leg_pnl = {}
    counter_trade_count = {}

    for counter, inst_map in per_counter_instrument.items():
        total_pnl = 0.0
        total_trades = 0

        for _, trades in inst_map.items():
            total_trades += len(trades)
            entry_qty = sum(t["qty"] for t in trades if t["qty"] > 0)
            exit_qty = sum(abs(t["qty"]) for t in trades if t["qty"] < 0)
            entry_amt = sum(t["amount"] for t in trades if t["qty"] > 0)
            exit_amt = sum(abs(t["amount"]) for t in trades if t["qty"] < 0)

            if entry_qty > 0 and exit_qty > 0:
                avg_entry = entry_amt / entry_qty
                avg_exit = exit_amt / exit_qty
                matched_qty = min(entry_qty, exit_qty)
                total_pnl += (avg_exit - avg_entry) * matched_qty

        counter_leg_pnl[counter] = total_pnl
        counter_trade_count[counter] = total_trades

    return counter_leg_pnl, counter_trade_count


def load_api_counter_pnl(api_json_path):
    """Load counter-wise PnL from API snapshot export JSON."""
    with open(api_json_path, encoding="utf-8") as f:
        payload = json.load(f)

    api_counter_pnl = {}
    for item in payload:
        counter = int(item.get("counter", 0))
        api_counter_pnl[counter] = safe_float(item.get("pnl", 0.0))
    return api_counter_pnl


def compare_counter_pnl(leg_counter_pnl, api_counter_pnl, tolerance):
    all_counters = sorted(set(leg_counter_pnl.keys()) | set(api_counter_pnl.keys()))
    rows = []
    matches = 0

    for counter in all_counters:
        leg_pnl = leg_counter_pnl.get(counter)
        api_pnl = api_counter_pnl.get(counter)

        if leg_pnl is None:
            status = "missing_in_legs"
            diff = None
        elif api_pnl is None:
            status = "missing_in_api"
            diff = None
        else:
            diff = api_pnl - leg_pnl
            status = "match" if abs(diff) <= tolerance else "mismatch"
            if status == "match":
                matches += 1

        rows.append(
            {
                "counter": counter,
                "leg_pnl": leg_pnl,
                "api_pnl": api_pnl,
                "diff_api_minus_leg": diff,
                "status": status,
            }
        )

    summary = {
        "total_counters_union": len(all_counters),
        "total_leg_counters": len(leg_counter_pnl),
        "total_api_counters": len(api_counter_pnl),
        "matches": matches,
        "mismatches": sum(1 for r in rows if r["status"] == "mismatch"),
        "missing_in_legs": sum(1 for r in rows if r["status"] == "missing_in_legs"),
        "missing_in_api": sum(1 for r in rows if r["status"] == "missing_in_api"),
        "tolerance": tolerance,
    }
    return summary, rows


def autodetect_files(tt_dir):
    leg_candidates = sorted(tt_dir.glob("leg_wise_*_complete_*.csv"))
    if not leg_candidates:
        leg_candidates = sorted(tt_dir.glob("counters_modal_rows_*.csv"))

    api_candidates = sorted(tt_dir.glob("counterwise_snapshot_*.json"))

    leg_csv = str(leg_candidates[-1]) if leg_candidates else None
    api_json = str(api_candidates[-1]) if api_candidates else None
    return leg_csv, api_json


def print_report(summary, rows):
    print("\n" + "=" * 90)
    print("COUNTER-WISE PNL CHECK: API vs LEG-WISE SUM")
    print("=" * 90)
    print(f"Total counters (union): {summary['total_counters_union']}")
    print(f"Leg counters:            {summary['total_leg_counters']}")
    print(f"API counters:            {summary['total_api_counters']}")
    print(f"Matches:                 {summary['matches']}")
    print(f"Mismatches:              {summary['mismatches']}")
    print(f"Missing in legs:         {summary['missing_in_legs']}")
    print(f"Missing in API:          {summary['missing_in_api']}")
    print(f"Tolerance:               {summary['tolerance']}")

    mismatches = [r for r in rows if r["status"] == "mismatch"]
    if mismatches:
        mismatches = sorted(
            mismatches,
            key=lambda r: abs(r["diff_api_minus_leg"]) if r["diff_api_minus_leg"] is not None else 0,
            reverse=True,
        )
        print("\nTop mismatches (up to 10):")
        for r in mismatches[:10]:
            print(
                f"  counter={r['counter']} leg={r['leg_pnl']:.2f} "
                f"api={r['api_pnl']:.2f} diff={r['diff_api_minus_leg']:.2f}"
            )

    print("=" * 90)


def main():
    parser = argparse.ArgumentParser(
        description="Compare API counter-wise pnl with leg-wise summed pnl"
    )
    parser.add_argument("--leg-csv", help="Leg-wise CSV path")
    parser.add_argument("--api-json", help="API counterwise JSON path")
    parser.add_argument("--output", default="counter_pnl_match_report.json", help="Output JSON report path")
    parser.add_argument("--tolerance", type=float, default=0.01, help="Abs diff tolerance for match")
    args = parser.parse_args()

    tt_dir = Path(__file__).parent
    auto_leg, auto_api = autodetect_files(tt_dir)
    leg_csv = args.leg_csv or auto_leg
    api_json = args.api_json or auto_api

    if not leg_csv or not Path(leg_csv).exists():
        print("Error: leg CSV not found")
        sys.exit(1)
    if not api_json or not Path(api_json).exists():
        print("Error: API counterwise JSON not found")
        sys.exit(1)

    print(f"Using leg CSV: {leg_csv}")
    print(f"Using API JSON: {api_json}")

    leg_counter_pnl, trade_counts = load_leg_counter_pnl(leg_csv)
    api_counter_pnl = load_api_counter_pnl(api_json)

    summary, rows = compare_counter_pnl(leg_counter_pnl, api_counter_pnl, args.tolerance)

    output = {
        "summary": summary,
        "inputs": {"leg_csv": leg_csv, "api_json": api_json},
        "counter_rows": rows,
        "trade_counts": trade_counts,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print_report(summary, rows)
    print(f"Report saved: {args.output}")


if __name__ == "__main__":
    main()
