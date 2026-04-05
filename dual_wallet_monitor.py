import pickle
import json
def fetch_wallet_running_count(wallet_name, session):
    """Fetch the count of running strategies from wallet/dashboard for a given session."""
    endpoint = "https://tradetron.tech/api/pricing/user-taxes"
    xsrf_token = session.cookies.get("XSRF-TOKEN") or session.cookies.get("X-XSRF-TOKEN")
    headers = {
        "Accept": "application/json",
        "Referer": "https://tradetron.tech/user/dashboard",
        "X-Requested-With": "XMLHttpRequest"
    }
    if xsrf_token:
        headers["X-XSRF-TOKEN"] = xsrf_token
        headers["X-CSRF-TOKEN"] = xsrf_token
    try:
        response = session.get(endpoint, headers=headers)
        if response.status_code == 200:
            data = response.json()
            balances = data.get("data", {}).get("balances", {})
            if isinstance(balances, dict) and "running" in balances:
                return int(balances.get("running"))
    except Exception as e:
        print(f"   ⚠️  {wallet_name} Wallet API failed: {str(e)}")
    return None
"""
Dual Wallet Cookie Validator & Health Monitor
Checks both Gopi and Ramki wallet cookies every 6 hours
Sends Telegram notification with wallet status

For Local: Set credentials in .env file
For GitHub: Set as repository secrets
"""
import requests
import pickle
import base64
import os
import sys
import traceback
import time
from pathlib import Path
from datetime import datetime

# Load environment variables from wallet_monitor.env (for local development)
try:
    from dotenv import load_dotenv
    import os
    # Load wallet monitor env
    wallet_monitor_env = os.path.join(os.path.dirname(__file__), 'wallet_monitor.env')
    if os.path.exists(wallet_monitor_env):
        load_dotenv(dotenv_path=wallet_monitor_env, override=True)
    # Also load legacy wallet-specific env for compatibility
    gopi_env = os.path.join(os.path.dirname(__file__), 'TTGopiWallet', '.env')
    if os.path.exists(gopi_env):
        load_dotenv(dotenv_path=gopi_env, override=True)
    ramki_env = os.path.join(os.path.dirname(__file__), 'TTRamkiWallet', '.env')
    if os.path.exists(ramki_env):
        load_dotenv(dotenv_path=ramki_env, override=True)
except ImportError:
    pass  # dotenv not installed or not needed in GitHub Actions

def send_telegram_message(message, title="TT Wallet Monitor"):
    """Send message to Telegram bot"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not configured")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️  Telegram error: {str(e)}")
        return False

def check_wallet_cookie_and_api(wallet_name, env_var_name, strategy_id):
    """
    Check if a wallet cookie is valid and if API endpoint is accessible.
    Returns: (wallet_ok, wallet_info, api_ok, api_info)
    """
    print(f"\n🔍 Checking {wallet_name} wallet...")
    encoded = os.getenv(env_var_name)
    if not encoded:
        print(f"   ❌ {env_var_name} not found")
        return False, {"error": f"Environment variable {env_var_name} not found"}, False, {"error": "No cookie"}
    print(f"   ✓ Cookie loaded from {env_var_name}")
    try:
        cookies_bytes = base64.b64decode(encoded)
    except Exception as e:
        print(f"   ❌ Failed to decode base64: {str(e)}")
        return False, {"error": f"Base64 decode failed: {str(e)}"}, False, {"error": "No cookie"}
    try:
        session = requests.Session()
        cookies = pickle.loads(cookies_bytes)
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
        print(f"   ✓ Session created with {len(cookies)} cookies")
    except Exception as e:
        print(f"   ❌ Failed to load cookies: {str(e)}")
        return False, {"error": f"Cookie load failed: {str(e)}"}, False, {"error": "No session"}
    xsrf_token = session.cookies.get("XSRF-TOKEN") or session.cookies.get("X-XSRF-TOKEN")
    headers = {
        "Accept": "application/json",
        "Referer": "https://tradetron.tech/user/dashboard",
        "X-Requested-With": "XMLHttpRequest"
    }
    if xsrf_token:
        headers["X-XSRF-TOKEN"] = xsrf_token
        headers["X-CSRF-TOKEN"] = xsrf_token
    # Wallet check
    try:
        response = session.get("https://tradetron.tech/api/pricing/user-taxes", headers=headers, timeout=10)
        if response.status_code == 200:
            try:
                data = response.json()
                balances = data.get("data", {}).get("balances", {})
                print(f"   ✓ {wallet_name} cookie is VALID")
                wallet_ok = True
                wallet_info = balances
            except Exception as e:
                print(f"   ⚠️  Response received but JSON parse failed: {str(e)}")
                wallet_ok = False
                wallet_info = {"error": f"JSON parse failed: {str(e)}"}
        elif response.status_code == 401:
            print(f"   ❌ {wallet_name} cookie EXPIRED (401 Unauthorized)")
            wallet_ok = False
            wallet_info = {"error": "Cookie expired - Status 401"}
        else:
            print(f"   ❌ {wallet_name} API error (Status {response.status_code})")
            wallet_ok = False
            wallet_info = {"error": f"API error - Status {response.status_code}"}
    except requests.exceptions.Timeout:
        print(f"   ❌ {wallet_name} request timeout")
        wallet_ok = False
        wallet_info = {"error": "Request timeout"}
    except Exception as e:
        print(f"   ❌ {wallet_name} request failed: {str(e)}")
        wallet_ok = False
        wallet_info = {"error": str(e)}
    # API endpoint check (read-only, e.g., deployed status)
    api_url = f"https://tradetron.tech/api/deployed/status?id={strategy_id}"
    try:
        api_response = session.get(api_url, headers=headers, timeout=10)
        if api_response.status_code == 200:
            api_ok = True
            api_info = {"msg": "API OK"}
        elif api_response.status_code == 401:
            api_ok = False
            api_info = {"msg": "API Unauthorized (401)"}
        else:
            api_ok = False
            api_info = {"msg": f"API error: {api_response.status_code}"}
    except Exception as e:
        api_ok = False
        api_info = {"msg": f"API exception: {str(e)}"}
    return wallet_ok, wallet_info, api_ok, api_info

def format_telegram_message(wallets_status):
    """Format wallet and API status into concise Telegram message
    
    wallets_status: dict with wallet names as keys and tuples of (wallet_ok, api_ok, info, api_info)
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    def lines(name, wallet_ok, api_ok, info, api_info):
        w = "✅" if wallet_ok else "❌"
        a = "✅" if api_ok else "❌"
        if wallet_ok:
            wallet_part = f"Wallet OK"
        else:
            wallet_part = info.get('error', 'Wallet FAIL')
        if api_ok:
            api_part = "API OK"
        else:
            api_part = api_info.get('msg', 'API FAIL')
        # Show API status as next line
        return f"{w} {name}: {wallet_part}\n    {a} API: {api_part}"
    
    # Build lines for each wallet
    wallet_lines = []
    all_wallet_ok = True
    all_api_ok = True
    any_ok = False
    
    for wallet_name in sorted(wallets_status.keys()):
        wallet_ok, api_ok, info, api_info = wallets_status[wallet_name]
        wallet_lines.append(lines(wallet_name, wallet_ok, api_ok, info, api_info))
        if not (wallet_ok and api_ok):
            all_wallet_ok = False
        if not api_ok:
            all_api_ok = False
        if wallet_ok and api_ok:
            any_ok = True
    
    # Summary
    if all_wallet_ok and all_api_ok:
        summary = "✅ All Good"
    elif any_ok:
        summary = "⚠️ Check Needed"
    elif any(ws[0] or ws[2] for ws in wallets_status.values()):
        summary = "⚠️ Partial Down"
    else:
        summary = "❌ Down"
    
    msg = f"""<b>🤖 TT Wallet Health</b> {timestamp}\n\n{chr(10).join(wallet_lines)}\n\n{summary}"""
    return msg

def main():
    print("\n" + "="*70)
    print(" WALLET COOKIE & HEALTH CHECK")
    print("="*70)
    
    # Detect local vs GitHub Actions run
    running_in_github = os.getenv('GITHUB_ACTIONS', '').lower() == 'true'
    
    # Wallet configurations
    WALLETS = {
        "Gopi": {"cookie_var": "TT_COOKIES_B64_GOPI", "strategy_var": "STRATEGY_ID_GOPI", "default_strategy": 18713274},
        "Ramki": {"cookie_var": "TT_COOKIES_B64_RAMKI", "strategy_var": "STRATEGY_ID_RAMKI", "default_strategy": 12345678},
        "Capital": {"cookie_var": "TT_COOKIES_B64_CAPITAL", "strategy_var": "STRATEGY_ID_CAPITAL", "default_strategy": 87654321},
    }
    
    # For GitHub Actions: require all secrets
    if running_in_github:
        print("\n🔧 Running in GitHub Actions environment")
        required_secrets = [
            ("TT_COOKIES_B64_GOPI", os.getenv("TT_COOKIES_B64_GOPI")),
            ("TT_COOKIES_B64_RAMKI", os.getenv("TT_COOKIES_B64_RAMKI")),
            ("TT_COOKIES_B64_CAPITAL", os.getenv("TT_COOKIES_B64_CAPITAL")),
            ("TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN")),
            ("TELEGRAM_CHAT_ID", os.getenv("TELEGRAM_CHAT_ID")),
        ]
        for secret_name, secret_value in required_secrets:
            if not secret_value or not secret_value.strip():
                error_msg = f"❌ GitHub Secret '{secret_name}' is missing or empty."
                print(error_msg)
                sys.exit(1)
        print("✓ All required secrets found")
    else:
        print("\n💻 Running locally")

    # Check all wallets and API
    wallets_status = {}
    for wallet_name, config in WALLETS.items():
        strategy_id = int(os.getenv(config["strategy_var"]) or config["default_strategy"])
        wallet_ok, wallet_info, api_ok, api_info = check_wallet_cookie_and_api(
            wallet_name, config["cookie_var"], strategy_id
        )
        wallets_status[wallet_name] = (wallet_ok, api_ok, wallet_info, api_info)

    # Show wallet running count from API (if possible)
    print("\n" + "="*70)
    print(" WALLET CHECK SUMMARY")
    print("="*70)

    # Try to get running count for each wallet
    wallets_running = {}
    for wallet_name, config in WALLETS.items():
        wallet_ok, api_ok, _, _ = wallets_status[wallet_name]
        if wallet_ok:
            encoded = os.getenv(config["cookie_var"])
            try:
                cookies_bytes = base64.b64decode(encoded)
                session = requests.Session()
                cookies = pickle.loads(cookies_bytes)
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
                wallets_running[wallet_name] = fetch_wallet_running_count(wallet_name, session)
            except Exception as e:
                print(f"   ⚠️  {wallet_name} wallet running count error: {str(e)}")
                wallets_running[wallet_name] = None
        else:
            wallets_running[wallet_name] = None

    # Print running counts
    for wallet_name in sorted(wallets_running.keys()):
        running = wallets_running[wallet_name]
        if running is not None:
            print(f"👛 {wallet_name} Wallets checked: {running}")
        else:
            print(f"👛 {wallet_name} Wallets checked: unknown")

    # Format message
    telegram_msg = format_telegram_message(wallets_status)

    # Add wallet running counts to Telegram message
    wallet_lines = []
    for wallet_name in sorted(wallets_running.keys()):
        running = wallets_running[wallet_name]
        if running is not None:
            wallet_lines.append(f"👛 {wallet_name} Wallets checked: <b>{running}</b>")
        else:
            wallet_lines.append(f"👛 {wallet_name} Wallets checked: <b>unknown</b>")
    telegram_msg = telegram_msg + "\n" + "\n".join(wallet_lines)

    # Display result
    print("\n" + "="*70)
    print(" HEALTH CHECK RESULTS")
    print("="*70)
    print(telegram_msg)

    # Send to Telegram
    print("\n" + "="*70)
    print(" SENDING TELEGRAM NOTIFICATION...")
    print("="*70)
    if send_telegram_message(telegram_msg):
        print("✓ Telegram notification sent successfully")
    else:
        print("❌ Failed to send Telegram notification")

    # Return success/failure (all wallets must be OK)
    all_ok = all(wallet_ok and api_ok for wallet_ok, api_ok, _, _ in wallets_status.values())
    return 0 if all_ok else 1

def run_periodic_check(interval_hours=6):
    """
    Run periodic health checks every N hours
    Useful for long-running monitoring
    """
    print(f"\n🔄 Starting periodic checks every {interval_hours} hour(s)")
    print("   Press Ctrl+C to stop\n")
    
    check_count = 0
    try:
        while True:
            check_count += 1
            print(f"\n📋 Health Check #{check_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            main()
            
            # Wait for next check
            wait_seconds = interval_hours * 3600
            print(f"\n⏳ Next check in {interval_hours} hour(s)...")
            time.sleep(wait_seconds)
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TT Wallet Cookie Health Monitor")
    parser.add_argument(
        "--monitor", 
        action="store_true", 
        help="Run periodic checks every 6 hours (runs indefinitely)"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=6, 
        help="Interval in hours for periodic checks (default: 6)"
    )
    
    args = parser.parse_args()
    
    if args.monitor:
        run_periodic_check(interval_hours=args.interval)
    else:
        sys.exit(main())
