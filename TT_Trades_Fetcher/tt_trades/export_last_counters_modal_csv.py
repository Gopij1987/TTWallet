import os
import csv
import json
import base64
import pickle
import argparse
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv


def build_session():
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    cookies_b64 = os.getenv("TT_COOKIES_B64_GOPI")
    if not cookies_b64:
        raise RuntimeError("TT_COOKIES_B64_GOPI missing in .env")

    cookie_list = pickle.loads(base64.b64decode(cookies_b64))

    s = requests.Session()
    for c in cookie_list:
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain", ".tradetron.tech")
        if name and value:
            s.cookies.set(name, value, domain=domain)

    s.headers.update(
        {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://tradetron.tech/deployed-strategies",
        }
    )
    return s


def split_instrument(symbol: str):
    parts = symbol.split("_")
    inst_type = parts[0] if len(parts) > 0 else ""
    underlying = parts[1] if len(parts) > 1 else ""
    expiry = parts[2] if len(parts) > 2 else ""
    option_type = parts[3] if len(parts) > 3 else ""
    strike = "_".join(parts[4:]) if len(parts) > 4 else ""
    return inst_type, underlying, expiry, option_type, strike


def request_json_with_retry(session: requests.Session, url: str, params: dict, timeout: int = 8, retries: int = 2):
    last_error = None
    for _ in range(retries + 1):
        try:
            r = session.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last_error = RuntimeError(f"status {r.status_code}")
        except Exception as e:
            last_error = e
    raise RuntimeError(f"request failed for {url} params={params}: {last_error}")


def get_counter_snapshot(session: requests.Session, strategy_id: int, counter: int):
    url = f"https://tradetron.tech/api/deployed/{strategy_id}"
    j = request_json_with_retry(session, url, {"counter": counter})
    if not j.get("success"):
        raise RuntimeError(f"counter {counter}: API success false")

    return j.get("data", {})


def get_position_rows(session: requests.Session, strategy_id: int, counter: int, instrument: str):
    url = f"https://tradetron.tech/api/deployed/position/{strategy_id}"
    params = {"counter": counter, "instrument": instrument.replace("&", "*")}

    try:
        j = request_json_with_retry(session, url, params)
    except Exception:
        return []

    if not j.get("success"):
        return []

    data = j.get("data", [])
    if isinstance(data, list):
        return data
    return []


def build_records_for_counter(session: requests.Session, strategy_id: int, counter: int):
    snapshot = get_counter_snapshot(session, strategy_id, counter)
    positions = snapshot.get("calculated_positions", [])

    records = []
    for pos in positions:
        instrument = pos.get("Instrument", "")
        inst_type, underlying, expiry, option_type, strike = split_instrument(instrument)

        modal_rows = get_position_rows(session, strategy_id, counter, instrument)
        if not modal_rows:
            # Keep a placeholder row if modal rows are unavailable
            records.append(
                {
                    "counter": counter,
                    "date": "",
                    "time": "",
                    "instrument_full": instrument,
                    "inst_type": inst_type,
                    "underlying": underlying,
                    "expiry": expiry,
                    "option_type": option_type,
                    "strike": strike,
                    "qty": "",
                    "price": "",
                    "amount": "",
                    "note": "no modal rows",
                }
            )
            continue

        for row in modal_rows:
            entry_date = row.get("entry_date", "")
            date_part = ""
            time_part = ""
            if " " in entry_date:
                date_part, time_part = entry_date.split(" ", 1)
            else:
                date_part = entry_date

            records.append(
                {
                    "counter": counter,
                    "date": date_part,
                    "time": time_part,
                    "instrument_full": instrument,
                    "inst_type": inst_type,
                    "underlying": underlying,
                    "expiry": expiry,
                    "option_type": option_type,
                    "strike": strike,
                    "qty": row.get("quantity", ""),
                    "price": row.get("price", ""),
                    "amount": row.get("amount", ""),
                    "note": "",
                }
            )

    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy-id", type=int, default=7147483)
    parser.add_argument("--last", type=int, default=10, help="Export last N counters")
    parser.add_argument("--all", action="store_true", help="Export all counters from max to 1")
    parser.add_argument("--start", type=int, default=None, help="Optional start counter")
    parser.add_argument("--end", type=int, default=None, help="Optional end counter")
    args = parser.parse_args()

    strategy_id = args.strategy_id

    session = build_session()

    # Use current max counter from fresh snapshot
    latest = get_counter_snapshot(session, strategy_id, 1)
    max_counter = int(latest.get("max_run_counter") or latest.get("run_counter") or 0)
    if max_counter <= 0:
        raise RuntimeError("Unable to determine max counter")

    if args.start is not None and args.end is not None:
        start_counter = min(max_counter, args.start)
        end_counter = max(1, args.end)
        if end_counter > start_counter:
            start_counter, end_counter = end_counter, start_counter
    elif args.all:
        start_counter = max_counter
        end_counter = 1
    else:
        count_last = max(1, args.last)
        start_counter = max_counter
        end_counter = max(1, max_counter - count_last + 1)

    print(f"Exporting counters: {start_counter} down to {end_counter}")

    all_records = []
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    scope = f"{start_counter}_to_{end_counter}"
    out_csv = Path(__file__).parent / f"counters_modal_rows_{scope}_{ts}.csv"
    out_json = Path(__file__).parent / f"counters_modal_rows_{scope}_{ts}.json"

    headers = [
        "counter",
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
        "note",
    ]

    def save_checkpoint():
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_records)
        out_json.write_text(json.dumps(all_records, indent=2), encoding="utf-8")

    for counter in range(start_counter, end_counter - 1, -1):
        print(f"- counter {counter}")
        try:
            recs = build_records_for_counter(session, strategy_id, counter)
            all_records.extend(recs)
            print(f"  rows: {len(recs)}")
        except Exception as e:
            print(f"  error: {e}")
        # Save progress every counter so interruptions do not lose data
        save_checkpoint()

    print(f"\nSaved CSV: {out_csv.name}")
    print(f"Saved JSON: {out_json.name}")
    print(f"Total rows: {len(all_records)}")


if __name__ == "__main__":
    main()
