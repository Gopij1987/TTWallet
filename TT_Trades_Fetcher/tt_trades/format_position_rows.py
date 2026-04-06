import argparse
import csv
import json
from pathlib import Path


def split_instrument(symbol: str):
    parts = symbol.split("_")
    # Expected: OPTIDX_BANKNIFTY_24FEB2026_PE_59600
    if len(parts) >= 5:
        inst_type = parts[0]
        underlying = parts[1]
        expiry = parts[2]
        opt_type = parts[3]
        strike = "_".join(parts[4:])
    else:
        inst_type = parts[0] if len(parts) > 0 else ""
        underlying = parts[1] if len(parts) > 1 else ""
        expiry = parts[2] if len(parts) > 2 else ""
        opt_type = parts[3] if len(parts) > 3 else ""
        strike = parts[4] if len(parts) > 4 else ""

    return inst_type, underlying, expiry, opt_type, strike


def load_position_rows(counter: int, instrument: str, strategy_id: int):
    safe_name = instrument.replace("/", "_")
    file_pattern = f"position_rows_{strategy_id}_{counter}_{safe_name}.json"
    path = Path(__file__).parent / file_pattern

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path.name}. Run extract_position_rows.py first."
        )

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    rows = payload.get("response", {}).get("data", [])
    return rows, path


def format_rows(rows, instrument):
    inst_type, underlying, expiry, opt_type, strike = split_instrument(instrument)
    output = []

    for row in rows:
        dt = row.get("entry_date", "")  # example: 2026-02-19 11:30:04
        date_part = ""
        time_part = ""
        if " " in dt:
            date_part, time_part = dt.split(" ", 1)
        else:
            date_part = dt

        output.append(
            {
                "date": date_part,
                "time": time_part,
                "instrument_full": instrument,
                "inst_type": inst_type,
                "underlying": underlying,
                "expiry": expiry,
                "option_type": opt_type,
                "strike": strike,
                "qty": row.get("quantity", ""),
                "price": row.get("price", ""),
                "amount": row.get("amount", ""),
            }
        )

    return output


def print_sample(formatted_rows):
    print("Requested format:")
    print(
        "date | time | inst_type | underlying | expiry | option_type | strike | qty | price | amount"
    )
    print("-" * 110)

    for r in formatted_rows:
        print(
            f"{r['date']} | {r['time']} | {r['inst_type']} | {r['underlying']} | "
            f"{r['expiry']} | {r['option_type']} | {r['strike']} | {r['qty']} | "
            f"{r['price']} | {r['amount']}"
        )


def save_csv(formatted_rows, counter, instrument):
    safe_name = instrument.replace("/", "_")
    out_file = Path(__file__).parent / f"formatted_rows_{counter}_{safe_name}.csv"

    headers = [
        "date",
        "time",
        "instrument_full",
        "inst_type",
        "underlying",
        "expiry",
        "option_type",
        "strike",
        "qty",
        "price",
        "amount",
    ]

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(formatted_rows)

    return out_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("counter", type=int)
    parser.add_argument("instrument", type=str)
    parser.add_argument("--strategy-id", type=int, default=7147483)
    args = parser.parse_args()

    rows, src_file = load_position_rows(args.counter, args.instrument, args.strategy_id)
    formatted = format_rows(rows, args.instrument)

    print(f"Source: {src_file.name}")
    print_sample(formatted)

    csv_file = save_csv(formatted, args.counter, args.instrument)
    print(f"\nSaved CSV: {csv_file.name}")


if __name__ == "__main__":
    main()
