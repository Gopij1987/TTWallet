"""
Tradetron Integrated API Automation - Ramki + Gopi (Sequential, Low RAM)
Runs both accounts one-by-one, reads cookies from shared VPS file,
falls back to individual files + Selenium refresh if needed.
Never overwrites the shared cookie file.

Usage:
    python tt_integrated_automation.py

Scheduling (VPS):
    cron: 30 7 * * 1-5 TZ=Asia/Kolkata /usr/bin/python3 /opt/tt-wallet/Wallet V1/tt_integrated_automation.py >> /var/log/tt-auto.log 2>&1
"""

import os
import sys
import time
import pickle
import base64
import traceback
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
except ImportError:
    pass

# ── Configuration ──────────────────────────────────────────────────────────
ACCOUNTS = {
    "Ramki": {
        "strategy_id_env": "STRATEGY_ID_RAMKI",
        "default_strategy_id": 22789265,
        "num_toggles_env": "NUM_TOGGLES_RAMKI",
        "default_num_toggles": 30,
        "username_env": "TRADETRON_USERNAME_RAMKI",
        "password_env": "TRADETRON_PASSWORD_RAMKI",
        "shared_file_env": "TT_COOKIES_RAMKI",
        "fallback_file_env": "TT_COOKIES_FALLBACK_RAMKI",
    },
    "Gopi": {
        "strategy_id_env": "STRATEGY_ID_GOPI",
        "default_strategy_id": 18713274,
        "num_toggles_env": "NUM_TOGGLES_GOPI",
        "default_num_toggles": 50,
        "username_env": "TRADETRON_USERNAME_GOPI",
        "password_env": "TRADETRON_PASSWORD_GOPI",
        "shared_file_env": "TT_COOKIES_GOPI",
        "fallback_file_env": "TT_COOKIES_FALLBACK_GOPI",
    },
}
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DELAY_SECONDS = int(os.getenv("DELAY_SECONDS", "1"))


def send_telegram_message(message):
    """Send message to Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  Telegram credentials not configured")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("  Telegram notification sent")
            return True
        else:
            print(f"  Telegram notification failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  Telegram error: {str(e)}")
        return False


def build_session_from_cookies(cookie_path):
    """Load cookies from a .b64 (base64-encoded pickle) or .pkl file and build a requests.Session."""
    if str(cookie_path).lower().endswith(".b64") or str(cookie_path).lower().endswith(".b64.txt"):
        with open(cookie_path, "r", encoding="ascii") as f:
            cookies = pickle.loads(base64.b64decode(f.read().strip()))
    else:
        with open(cookie_path, "rb") as f:
            cookies = pickle.load(f)
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=cookie.get("domain", ".tradetron.tech"),
        )
    return session


def validate_session(session):
    """Validate session by hitting a lightweight authenticated endpoint."""
    xsrf_token = session.cookies.get("XSRF-TOKEN") or session.cookies.get("X-XSRF-TOKEN")
    headers = {
        "Accept": "application/json",
        "Referer": "https://tradetron.tech/user/dashboard",
        "X-Requested-With": "XMLHttpRequest",
    }
    if xsrf_token:
        headers["X-XSRF-TOKEN"] = xsrf_token
        headers["X-CSRF-TOKEN"] = xsrf_token
    try:
        test = session.get("https://tradetron.tech/api/pricing/user-taxes", headers=headers, timeout=15)
        return test.status_code == 200
    except Exception:
        return False


def save_cookies_to_b64(session, output_path):
    """Extract cookies from session dict and save as base64-encoded pickle (.b64)."""
    cookies_list = []
    for cookie in session.cookies:
        cookies_list.append({
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain,
        })
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    # Force .b64 extension
    if not str(output_path).lower().endswith(".b64"):
        output_path = str(output_path) + ".b64"
    b64_data = base64.b64encode(pickle.dumps(cookies_list)).decode("ascii")
    with open(output_path, "w", encoding="ascii") as f:
        f.write(b64_data)


def resolve_session(account_name, cfg):
    """
    Cookie resolution order:
      1. Shared file -> validate
      2. Individual fallback file -> validate
      3. Selenium refresh -> save to fallback file -> validate
    Returns (session, source, error_msg) where source is 'shared', 'fallback', or None.
    """
    shared_path = os.getenv(cfg["shared_file_env"], "/opt/tt-wallet/cookies.b64")
    fallback_path = os.getenv(cfg["fallback_file_env"], f"./cookies_{account_name.lower()}_fallback.b64")
    sources = [
        ("shared", shared_path),
        ("fallback", fallback_path),
    ]

    for source_label, path in sources:
        if not Path(path).exists():
            print(f"  {source_label.capitalize()} cookie file not found: {path}")
            continue
        try:
            session = build_session_from_cookies(path)
        except Exception as e:
            print(f"  Failed to load {source_label} cookies from {path}: {e}")
            continue
        if validate_session(session):
            print(f"  Valid session from {source_label} file: {path}")
            return session, source_label, None
        else:
            print(f"  {source_label.capitalize()} cookies invalid: {path}")

    # ── Step 3: Selenium refresh ──────────────────────────────────────
    print(f"  Attempting Selenium cookie refresh for {account_name}...")
    username = os.getenv(cfg["username_env"])
    password = os.getenv(cfg["password_env"])
    if not username or not password:
        error_msg = f"Missing credentials for {account_name} ({cfg['username_env']} / {cfg['password_env']})"
        print(f"  {error_msg}")
        return None, None, error_msg

    fallback_path = os.getenv(cfg["fallback_file_env"], f"./cookies_{account_name.lower()}_fallback.b64")
    try:
        from cookie_refresh import refresh_cookies_via_selenium
        new_session = refresh_cookies_via_selenium(username, password)
        if new_session and validate_session(new_session):
            save_cookies_to_b64(new_session, fallback_path)
            print(f"  Refreshed cookies saved to fallback: {fallback_path}")
            return new_session, "fallback", None
        else:
            error_msg = f"Selenium refresh produced invalid session for {account_name}"
            print(f"  {error_msg}")
            return None, None, error_msg
    except Exception as e:
        error_msg = f"Selenium refresh failed for {account_name}: {str(e)}"
        print(f"  {error_msg}")
        traceback.print_exc()
        return None, None, error_msg


def toggle_strategy(session, strategy_id, status, retries=3, backoff_seconds=3):
    """Toggle strategy start/stop via API. status: 'Start' or 'Paused'."""
    url = "https://tradetron.tech/api/deployed/status"
    payload = {"status": status, "id": strategy_id}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    last_response = None
    for attempt in range(1, retries + 1):
        try:
            response = session.post(url, json=payload, headers=headers)
            last_response = response
        except Exception as e:
            print(f"    Request exception (attempt {attempt}/{retries}): {str(e)}")
            response = None
        if response is None:
            if attempt < retries:
                time.sleep(backoff_seconds * attempt)
                continue
            return None
        if response.status_code < 500:
            return response
        if attempt < retries:
            time.sleep(backoff_seconds * attempt)
    return last_response


def fetch_wallet_running_count(session):
    """Fetch running strategies count from wallet."""
    endpoint = "https://tradetron.tech/api/pricing/user-taxes"
    xsrf_token = session.cookies.get("XSRF-TOKEN") or session.cookies.get("X-XSRF-TOKEN")
    headers = {
        "Accept": "application/json",
        "Referer": "https://tradetron.tech/user/dashboard",
        "X-Requested-With": "XMLHttpRequest",
    }
    if xsrf_token:
        headers["X-XSRF-TOKEN"] = xsrf_token
        headers["X-CSRF-TOKEN"] = xsrf_token
    try:
        response = session.get(endpoint, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            balances = data.get("data", {}).get("balances", {})
            if isinstance(balances, dict) and "running" in balances:
                return int(balances.get("running"))
    except Exception as e:
        print(f"    Wallet API failed: {str(e)}")
    return None


def run_account_automation(account_name, cfg):
    """
    Run full Start/Stop toggle automation for one account.
    Returns dict with keys: success, error, toggles_done, running_count, strategy_id
    """
    strategy_id = int(os.getenv(cfg["strategy_id_env"], str(cfg["default_strategy_id"])))
    num_toggles = int(os.getenv(cfg["num_toggles_env"], str(cfg["default_num_toggles"])))

    print(f"\n{'='*70}")
    print(f" {account_name.upper()} ACCOUNT")
    print(f"{'='*70}")
    print(f"  Strategy ID: {strategy_id}")
    print(f"  Toggles: {num_toggles}")

    # Resolve cookies
    session, source, error_msg = resolve_session(account_name, cfg)
    if not session:
        send_telegram_message(f"<b>{account_name} TT Wallet</b>\n\nCookie resolution failed:\n<pre>{error_msg}</pre>")
        return {"success": False, "error": error_msg or "Cookie resolution failed", "toggles_done": 0, "running_count": None, "strategy_id": strategy_id, "source": None}

    print(f"  Using cookies from: {source}")

    # Toggle loop
    had_failure = False
    error_details = []
    toggles_done = 0

    for i in range(num_toggles):
        print(f"\n  [{i+1}/{num_toggles}] STOP...")
        response = toggle_strategy(session, strategy_id, "Paused")
        if not (response and response.status_code == 200):
            status_code = response.status_code if response else "no response"
            error_msg = f"STOP failed at {i+1}/{num_toggles} — Status: {status_code}"
            print(f"    {error_msg}")
            error_details.append(error_msg)
            had_failure = True
            break
        print(f"    STOPPED OK")
        time.sleep(DELAY_SECONDS)

        print(f"  [{i+1}/{num_toggles}] START...")
        response = toggle_strategy(session, strategy_id, "Start")
        if not (response and response.status_code == 200):
            status_code = response.status_code if response else "no response"
            error_msg = f"START failed at {i+1}/{num_toggles} — Status: {status_code}"
            print(f"    {error_msg}")
            error_details.append(error_msg)
            had_failure = True
            break
        print(f"    STARTED OK")
        toggles_done = i + 1

        if i < num_toggles - 1:
            time.sleep(DELAY_SECONDS)

    # Final STOP
    print("\n  Final STOP...")
    response = toggle_strategy(session, strategy_id, "Paused")
    if not (response and response.status_code == 200):
        status_code = response.status_code if response else "no response"
        error_msg = f"Final STOP failed — Status: {status_code}"
        print(f"    {error_msg}")
        error_details.append(error_msg)
        had_failure = True
    else:
        print("    Final STOP OK")

    # Running count
    running_count = None
    if session:
        try:
            running_count = fetch_wallet_running_count(session)
        except Exception:
            pass

    if had_failure:
        error_summary = "\n".join(error_details) if error_details else "Unknown error"
        return {"success": False, "error": error_summary, "toggles_done": toggles_done, "running_count": running_count, "strategy_id": strategy_id, "source": source}

    return {"success": True, "error": None, "toggles_done": toggles_done, "running_count": running_count, "strategy_id": strategy_id, "source": source}


_COOKIE_SOURCE_LABELS = {
    "shared": "Shared (TT Dash V3)",
    "fallback": "Fallback (individual)",
    None: "N/A",
}

def build_summary_message(results):
    """Build consolidated Telegram message from accounts' results."""
    lines = ["<b>TT Wallet Automation Summary</b>\n"]
    for account_name in [k for k in ["Ramki", "Gopi"] if k in results]:
        res = results[account_name]
        icon = "✅" if res["success"] else "❌"
        source_label = _COOKIE_SOURCE_LABELS.get(res.get("source"), str(res.get("source")))
        lines.append(f"{icon} <b>{account_name}</b>")
        lines.append(f"   Toggles: {res['toggles_done']}")
        lines.append(f"   Cookie: {source_label}")
        if res['running_count'] is not None:
            lines.append(f"   Running: {res['running_count']}")
        if res['error']:
            err = res['error'][:300]  # truncate
            lines.append(f"   Error: <pre>{err}</pre>")
        lines.append("")
    return "\n".join(lines)


def run_automation(accounts=None):
    """
    Run the full automation and return results dict.
    Does NOT send Telegram or exit — returns control to caller.
    accounts: optional list of account names to run (e.g. ['Gopi'] or ['Ramki']).
              If None or empty, runs all accounts.
    """
    print("\n" + "="*70)
    print(" TT INTEGRATED AUTOMATION (Ramki → Gopi)")
    print("="*70)

    # Validate required envs
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if missing:
        msg = f"Missing env vars: {', '.join(missing)}"
        print(msg)
        return {"_critical_error": msg}

    # Normalise filter to title-case to match ACCOUNTS keys
    filter_set = None
    if accounts:
        filter_set = {a.title() for a in accounts}

    results = {}
    for account_name, cfg in ACCOUNTS.items():
        if filter_set and account_name not in filter_set:
            continue
        results[account_name] = run_account_automation(account_name, cfg)

    return results


def main():
    """CLI entry point — runs automation, prints, sends Telegram, exits."""
    results = run_automation()

    # Critical error from run_automation
    if "_critical_error" in results:
        print(results["_critical_error"])
        sys.exit(1)

    # Consolidated Telegram
    print("\n" + "="*70)
    print(" SENDING CONSOLIDATED TELEGRAM REPORT")
    print("="*70)
    summary = build_summary_message(results)
    print(summary)
    send_telegram_message(summary)

    # Exit code
    all_ok = all(r["success"] for r in results.values())
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"CRITICAL ERROR: {str(e)}"
        print(f"\n{error_msg}")
        traceback.print_exc()
        tb_lines = traceback.format_exc().split("\n")
        error_details = "\n".join(tb_lines[-10:])
        send_telegram_message(f"<b>TT Wallet Automation - CRITICAL FAILURE</b>\n\n<pre>{error_details}</pre>")
        sys.exit(1)
