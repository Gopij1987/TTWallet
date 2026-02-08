"""
Tradetron API Automation - Direct API Calls (NO BROWSER!)
Toggles Start/Stop via API - instant and reliable
"""

import requests
import pickle
import json
import time
import os
import base64
import sys
import traceback
from pathlib import Path
from html.parser import HTMLParser

# Load environment variables from .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed or not needed in GitHub Actions

COOKIES_FILE = Path(__file__).parent / "tradetron_cookies_gopi.pkl"

def send_telegram_message(message):
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
        if response.status_code == 200:
            print("✓ Telegram notification sent")
            return True
        else:
            print(f"⚠️  Telegram notification failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Telegram error: {str(e)}")
        return False

def load_session():
    """Load session from saved cookies"""
    if not COOKIES_FILE.exists():
        encoded = os.getenv("TT_COOKIES_B64_GOPI")
        if encoded:
            try:
                COOKIES_FILE.write_bytes(base64.b64decode(encoded))
                print("✓ Cookies restored from TT_COOKIES_B64_GOPI")
            except Exception as e:
                error_msg = f"❌ Failed to decode TT_COOKIES_B64_GOPI: {str(e)}"
                print(error_msg)
                send_telegram_message(f"🤖 Gopi TT Wallet\n\n{error_msg}")
                return None
        else:
            print("❌ No cookies found! Run quick_login.py first")
            return None
    
    # Create session
    session = requests.Session()
    
    # Load cookies
    with open(COOKIES_FILE, 'rb') as f:
        cookies = pickle.load(f)
    
    # Add cookies to session
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))

    # Validate session early to catch expired cookies
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
        test = session.get("https://tradetron.tech/api/pricing/user-taxes", headers=headers)
        if test.status_code != 200:
            error_msg = f"❌ Cookie validation failed (status {test.status_code})"
            print(error_msg)
            send_telegram_message(f"🤖 Gopi TT Wallet\n\n{error_msg}\n\nCookies may be expired. Please refresh cookies.")
            return None
    except Exception as e:
        error_msg = f"❌ Cookie validation failed: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        send_telegram_message(f"🤖 Gopi TT Wallet\n\n{error_msg}")
        return None

    return session

def toggle_strategy(session, strategy_id, status, retries=3, backoff_seconds=3):
    """
    Toggle strategy start/stop via API
    status: "Start" or "Paused"
    """
    url = "https://tradetron.tech/api/deployed/status"
    
    payload = {
        "status": status,
        "id": strategy_id
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    last_response = None
    for attempt in range(1, retries + 1):
        try:
            response = session.post(url, json=payload, headers=headers)
            last_response = response
        except Exception as e:
            print(f"   ⚠️  Request exception (attempt {attempt}/{retries}): {str(e)}")
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

def get_status_label(response):
    """Extract status label from API response JSON."""
    try:
        data = response.json()
        return str(data.get("data", "")).strip()
    except Exception as e:
        print(f"   ⚠️  Failed to parse response JSON: {str(e)}")
        return ""

def normalize_status(label):
    return str(label).strip().lower().replace(" ", "").replace("_", "").replace("-", "")

class StatusHTMLParser(HTMLParser):
    def __init__(self, strategy_id):
        super().__init__()
        self.strategy_id = str(strategy_id)
        self.in_target = False
        self.target_depth = 0
        self.awaiting_status_span = False
        self.capture_status = False
        self.status = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "div":
            element_id = attrs_dict.get("id", "")
            if element_id and self.strategy_id in element_id and not self.in_target:
                self.in_target = True
                self.target_depth = 1
                return

        if self.in_target:
            self.target_depth += 1
            if tag == "span" and self.awaiting_status_span and not self.status:
                self.capture_status = True

    def handle_endtag(self, tag):
        if self.in_target:
            self.target_depth -= 1
            if self.capture_status and tag == "span":
                self.capture_status = False
                self.awaiting_status_span = False
            if self.target_depth <= 0:
                self.in_target = False
                self.target_depth = 0

    def handle_data(self, data):
        if not self.in_target:
            return
        text = data.strip()
        if not text:
            return
        if "Status" in text:
            self.awaiting_status_span = True
            return
        if self.capture_status and not self.status:
            self.status = text

def fetch_status_from_html(session, strategy_id):
    url = "https://tradetron.tech/user/dashboard"
    headers = {
        "Accept": "text/html",
        "Referer": "https://tradetron.tech/user/dashboard",
        "User-Agent": "Mozilla/5.0"
    }
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        return "", response

    parser = StatusHTMLParser(strategy_id)
    parser.feed(response.text)
    return parser.status, response

def fetch_current_status(session, strategy_id):
    """Fetch current status for a strategy from dashboard API."""
    xsrf_token = session.cookies.get("XSRF-TOKEN") or session.cookies.get("X-XSRF-TOKEN")
    base_headers = {
        "Accept": "application/json",
        "Referer": "https://tradetron.tech/user/dashboard",
        "X-Requested-With": "XMLHttpRequest"
    }
    if xsrf_token:
        base_headers["X-XSRF-TOKEN"] = xsrf_token
        base_headers["X-CSRF-TOKEN"] = xsrf_token

    probes = [
        {
            "method": "POST",
            "url": "https://tradetron.tech/api/user/filter/dashboard",
            "json": {
                "exchange": [],
                "creator_id": [],
                "execution": [],
                "status": [],
                "broker_id": [],
                "statuses": []
            },
            "headers": {**base_headers, "Content-Type": "application/json"}
        },
        {
            "method": "GET",
            "url": f"https://tradetron.tech/api/deployed/status?id={strategy_id}",
            "headers": base_headers
        },
        {
            "method": "GET",
            "url": f"https://tradetron.tech/api/deployed/details?id={strategy_id}",
            "headers": base_headers
        }
    ]

    data = None
    response = None

    for probe in probes:
        try:
            if probe["method"] == "POST":
                response = session.post(probe["url"], json=probe.get("json"), headers=probe.get("headers"))
            else:
                response = session.get(probe["url"], headers=probe.get("headers"))
        except Exception as e:
            print(f"   ⚠️  Probe request failed: {str(e)}")
            continue

        if response.status_code != 200:
            continue
        try:
            data = response.json()
        except Exception as e:
            print(f"   ⚠️  Probe JSON parse failed: {str(e)}")
            continue
        if data:
            break

    if not data:
        html_status, html_response = fetch_status_from_html(session, strategy_id)
        if html_status:
            return html_status, html_response
        return "", response

    id_keys = {
        "id",
        "deployment_id",
        "deployed_id",
        "strategy_id",
        "tradetron_id",
        "deployed_strategy_id",
        "deploy_id",
        "deploymentId",
        "deployedStrategyId",
        "strategy_deploy_id"
    }
    status_keys = {
        "status",
        "execution_status",
        "executionStatus",
        "execution_status_name",
        "state",
        "live_status",
        "current_status",
        "status_label",
        "statusText",
        "execution"
    }

    def find_status(node):
        if isinstance(node, dict):
            for key in id_keys:
                if key in node and str(node.get(key)) == str(strategy_id):
                    for s_key in status_keys:
                        if s_key in node:
                            value = node.get(s_key)
                            if isinstance(value, dict):
                                for inner_key in ("status", "label", "name", "text"):
                                    if inner_key in value:
                                        return str(value.get(inner_key))
                            return str(value)
            for value in node.values():
                result = find_status(value)
                if result:
                    return result
        elif isinstance(node, list):
            for item in node:
                result = find_status(item)
                if result:
                    return result
        return ""

    return find_status(data), response

def fetch_wallet_running_count(session):
    """Fetch the count of running strategies from wallet/dashboard."""
    # Primary endpoint (wallet modal)
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
        print(f"   ⚠️  Wallet API failed: {str(e)}")
    
    # Fallback: Parse from dashboard HTML
    try:
        url = "https://tradetron.tech/user/dashboard"
        response = session.get(url, headers={"Accept": "text/html"})
        if response.status_code == 200:
            html = response.text
            # Look for "Running" followed by a number
            import re
            patterns = [
                r'>Running</span>\s*(?:==\s*\$0)?\s*<[^>]*>[\s-]*(\d+)</[^>]*>',
                r'>Running<[^>]*>\s*(?:==\s*\$0)?\s*[\s-]*(\d+)',
                r'Running["\']?\s*[:\-]?\s*(\d+)',
                r'wallet.*?running.*?(\d+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    return int(match.group(1))
    except Exception as e:
        print(f"   ⚠️  HTML parsing failed: {str(e)}")
    
    return None

def main():
    # Detect local vs GitHub Actions run
    running_in_github = os.getenv('GITHUB_ACTIONS', '').lower() == 'true'

    # For local: use .env values. For GitHub: require secrets, no fallback except strategy ID.
    if running_in_github:
        required_secrets = [
            ("NUM_TOGGLES_GOPI", os.getenv("NUM_TOGGLES_GOPI")),
            ("TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN")),
            ("TELEGRAM_CHAT_ID", os.getenv("TELEGRAM_CHAT_ID")),
            ("TT_COOKIES_B64_GOPI", os.getenv("TT_COOKIES_B64_GOPI")),
        ]
        for secret_name, secret_value in required_secrets:
            if not secret_value or not secret_value.strip():
                error_msg = f"❌ GitHub Secret '{secret_name}' is missing or empty."
                print(error_msg)
                send_telegram_message(f"🤖 Gopi TT Wallet\n\n{error_msg}")
                sys.exit(1)
        num_toggles_gopi = os.getenv("NUM_TOGGLES_GOPI")
        STRATEGY_ID = int(os.getenv("STRATEGY_ID_GOPI") or "18713274")
    else:
        # Local: use .env, allow fallback for NUM_TOGGLES_GOPI
        num_toggles_gopi = os.getenv("NUM_TOGGLES_GOPI") or os.getenv("NUM_TOGGLES")
        STRATEGY_ID = int(os.getenv("STRATEGY_ID_GOPI") or "18713274")

    if not num_toggles_gopi or not num_toggles_gopi.strip():
        error_msg = "❌ NUM_TOGGLES_GOPI is missing or empty."
        print(error_msg)
        send_telegram_message(f"🤖 Gopi TT Wallet\n\n{error_msg}")
        sys.exit(1)

    NUM_TOGGLES = int(num_toggles_gopi)
    print("\n" + "="*70)
    print(" TRADETRON API AUTOMATION - NO BROWSER!")
    print("="*70)
    
    # Configuration
    strategy_id_gopi = os.getenv("STRATEGY_ID_GOPI")
    STRATEGY_ID = int(strategy_id_gopi) if strategy_id_gopi and strategy_id_gopi.strip() else 18713274  # Gopi strategy ID
    NUM_TOGGLES = int(os.getenv("NUM_TOGGLES_GOPI", os.getenv("NUM_TOGGLES", "50")))         # Number of times to toggle (configurable)
    DELAY_SECONDS = int(os.getenv("DELAY_SECONDS", "1"))      # Wait time between commands (in seconds)
    
    # Load session
    print("\n1. Loading session from saved cookies...")
    session = load_session()
    
    if not session:
        sys.exit(1)
    
    print("✓ Session loaded")
    
    # Toggle Start/Stop
    print(f"\n2. Toggling Start/Stop {NUM_TOGGLES} times via API...")
    print(f"   (with {DELAY_SECONDS} second delay between commands)")
    print("-" * 70)

    had_failure = False
    error_details = []  # Track all error details for Telegram notification

    for i in range(NUM_TOGGLES):
        print(f"\n   [{i+1}/{NUM_TOGGLES}] Sending STOP command...")
        try:
            response = toggle_strategy(session, STRATEGY_ID, "Paused")
            if response and response.status_code == 200:
                print(f"   ✓ STOPPED - Response: {response.status_code}")
                try:
                    print(f"      {response.json()}")
                except Exception as e:
                    error_details.append(f"STOP command JSON parse error: {str(e)}")
                    send_telegram_message(f"🤖 Gopi TT Wallet\n\nSTOP command JSON parse error: {str(e)}")
            else:
                status_code = response.status_code if response else "no response"
                error_msg = f"STOP command failed at iteration {i+1}/{NUM_TOGGLES} - Status: {status_code}"
                print(f"   ❌ Failed - Status: {status_code}")
                error_details.append(error_msg)
                if response is not None:
                    print(f"      {response.text}")
                    try:
                        error_details.append(f"Response: {response.text[:200]}")
                    except:
                        pass
                had_failure = True
                send_telegram_message(f"🤖 Gopi TT Wallet\n\n{error_msg}")
                break
        except Exception as e:
            had_failure = True
            error_msg = f"STOP command exception at iteration {i+1}/{NUM_TOGGLES}: {str(e)}"
            error_details.append(error_msg)
            send_telegram_message(f"🤖 Gopi TT Wallet\n\n{error_msg}")
            break

        time.sleep(DELAY_SECONDS)

        print("   Sending START command...")
        try:
            response = toggle_strategy(session, STRATEGY_ID, "Start")
            if response and response.status_code == 200:
                print(f"   ✓ STARTED - Response: {response.status_code}")
                try:
                    print(f"      {response.json()}")
                except Exception as e:
                    error_details.append(f"START command JSON parse error: {str(e)}")
                    send_telegram_message(f"🤖 Gopi TT Wallet\n\nSTART command JSON parse error: {str(e)}")
            else:
                status_code = response.status_code if response else "no response"
                error_msg = f"START command failed at iteration {i+1}/{NUM_TOGGLES} - Status: {status_code}"
                print(f"   ❌ Failed - Status: {status_code}")
                error_details.append(error_msg)
                if response is not None:
                    print(f"      {response.text}")
                    try:
                        error_details.append(f"Response: {response.text[:200]}")
                    except:
                        pass
                had_failure = True
                send_telegram_message(f"🤖 Gopi TT Wallet\n\n{error_msg}")
                break
        except Exception as e:
            had_failure = True
            error_msg = f"START command exception at iteration {i+1}/{NUM_TOGGLES}: {str(e)}"
            error_details.append(error_msg)
            send_telegram_message(f"🤖 Gopi TT Wallet\n\n{error_msg}")
            break

        # Wait before next toggle cycle (except on last iteration)
        if i < NUM_TOGGLES - 1:
            time.sleep(DELAY_SECONDS)

    print("\n   Finalizing: Sending STOP command to end in Paused state...")
    response = toggle_strategy(session, STRATEGY_ID, "Paused")
    if response and response.status_code == 200:
        print(f"   ✓ FINAL STOPPED - Response: {response.status_code}")
        try:
            print(f"      {response.json()}")
        except:
            pass
    else:
        status_code = response.status_code if response else "no response"
        error_msg = f"Final STOP command failed - Status: {status_code}"
        print(f"   ❌ Final stop failed - Status: {status_code}")
        error_details.append(error_msg)
        if response is not None:
            print(f"      {response.text}")
            try:
                error_details.append(f"Response: {response.text[:200]}")  # First 200 chars
            except:
                pass
        had_failure = True
    
    if had_failure:
        print("\n" + "="*70)
        print(" ❌ AUTOMATION FAILED")
        print("="*70)
        
        # Prepare detailed error message for Telegram
        error_summary = "\n".join(error_details) if error_details else "Unknown error during toggle operations"
        telegram_msg = f"🤖❌ <b>Gopi TT Wallet - FAILED</b>\n\n<b>Error Details:</b>\n<pre>{error_summary}</pre>"
        send_telegram_message(telegram_msg)
        sys.exit(1)

    print("\n" + "="*70)
    print(" ✓ AUTOMATION COMPLETED!")
    print("="*70)
    print(f"\nToggled Start/Stop {NUM_TOGGLES} times using direct API calls")
    print("No browser needed - instant execution!")
    
    # Fetch and display wallet running count
    print("\n" + "="*70)
    print(" WALLET SUMMARY")
    print("="*70)
    print("\nFetching running strategies count...")
    running_count = fetch_wallet_running_count(session)
    
    if running_count is not None:
        print(f"✓ Strategies Running: {running_count}")
    else:
        print("ℹ️  Check dashboard UI for current running count")
        print("   Visit: https://tradetron.tech/user/dashboard")

    # Send success notification to Telegram with toggle and running count
    msg = (
        f"🤖✅ <b>Gopi TT Wallet - SUCCESS</b>\n\n"
        f"Toggled Start/Stop: <b>{NUM_TOGGLES}</b> times\n"
        f"Strategies Running: <b>{running_count if running_count is not None else 'unknown'}</b>\n\n"
        f"Automation completed successfully!"
    )
    send_telegram_message(msg)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"❌ CRITICAL ERROR: {str(e)}"
        print(f"\n{error_msg}")
        print("\nFull traceback:")
        print(traceback.format_exc())
        # Send detailed error to Telegram
        tb_lines = traceback.format_exc().split('\n')
        error_details = '\n'.join(tb_lines[-10:])  # Last 10 lines of traceback
        telegram_msg = f"🤖❌ <b>Gopi TT Wallet - FAILED</b>\n\n<b>Error:</b> {str(e)}\n\n<b>Details:</b>\n<pre>{error_details}</pre>"
        send_telegram_message(telegram_msg)
        sys.exit(1)
