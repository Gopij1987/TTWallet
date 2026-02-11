"""
Tradetron API Automation - Direct API Calls (NO BROWSER!)
Toggles Start/Stop via API - instant and reliable (Ramki Wallet)
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

# Load environment variables from .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed or not needed in GitHub Actions

# Use Ramki-specific cookies file
COOKIES_FILE = Path(__file__).parent / "tradetron_cookies_ramki.pkl"

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
    """Load session from base64 encoded cookies"""
    encoded = os.getenv("TT_COOKIES_B64_RAMKI")
    if not encoded:
        print("❌ No cookies found! Set TT_COOKIES_B64_RAMKI environment variable")
        return None
    
    try:
        cookies_bytes = base64.b64decode(encoded)
        print("✓ Cookies loaded from TT_COOKIES_B64_RAMKI")
    except Exception as e:
        error_msg = f"❌ Failed to decode TT_COOKIES_B64_RAMKI: {str(e)}"
        print(error_msg)
        send_telegram_message(f"🤖 Ramki TT Wallet\n\n{error_msg}")
        return None
    
    session = requests.Session()
    cookies = pickle.loads(cookies_bytes)
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
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
            send_telegram_message(f"🤖 Ramki TT Wallet\n\n{error_msg}\n\nCookies may be expired. Please refresh cookies.")
            return None
    except Exception as e:
        error_msg = f"❌ Cookie validation failed: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        send_telegram_message(f"🤖 Ramki TT Wallet\n\n{error_msg}")
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

def fetch_wallet_running_count(session):
    """Fetch the count of running strategies from wallet/dashboard."""
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
    return None

def main():
    running_in_github = os.getenv('GITHUB_ACTIONS', '').lower() == 'true'
    if running_in_github:
        required_secrets = [
            ("NUM_TOGGLES_RAMKI", os.getenv("NUM_TOGGLES_RAMKI")),
            ("TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN")),
            ("TELEGRAM_CHAT_ID", os.getenv("TELEGRAM_CHAT_ID")),
            ("TT_COOKIES_B64_RAMKI", os.getenv("TT_COOKIES_B64_RAMKI")),
        ]
        for secret_name, secret_value in required_secrets:
            if not secret_value or not secret_value.strip():
                error_msg = f"❌ GitHub Secret '{secret_name}' is missing or empty."
                print(error_msg)
                send_telegram_message(f"🤖 Ramki TT Wallet\n\n{error_msg}")
                sys.exit(1)
        num_toggles_ramki = os.getenv("NUM_TOGGLES_RAMKI")
        STRATEGY_ID = int(os.getenv("STRATEGY_ID_RAMKI") or "22789265")
    else:
        num_toggles_ramki = os.getenv("NUM_TOGGLES_RAMKI") or os.getenv("NUM_TOGGLES")
        STRATEGY_ID = int(os.getenv("STRATEGY_ID_RAMKI") or "22789265")
    if not num_toggles_ramki or not num_toggles_ramki.strip():
        error_msg = "❌ NUM_TOGGLES_RAMKI is missing or empty."
        print(error_msg)
        send_telegram_message(f"🤖 Ramki TT Wallet\n\n{error_msg}")
        sys.exit(1)
    NUM_TOGGLES = int(num_toggles_ramki)
    print("\n" + "="*70)
    print(" TRADETRON API AUTOMATION - NO BROWSER! (RAMKI)")
    print("="*70)
    strategy_id_ramki = os.getenv("STRATEGY_ID_RAMKI")
    STRATEGY_ID = int(strategy_id_ramki) if strategy_id_ramki and strategy_id_ramki.strip() else 22789265
    NUM_TOGGLES = int(os.getenv("NUM_TOGGLES_RAMKI", os.getenv("NUM_TOGGLES", "30")))
    DELAY_SECONDS = int(os.getenv("DELAY_SECONDS", "1"))
    print("\n1. Loading session from saved cookies...")
    session = load_session()
    if not session:
        sys.exit(1)
    print("✓ Session loaded")
    print(f"\n2. Toggling Start/Stop {NUM_TOGGLES} times via API...")
    print(f"   (with {DELAY_SECONDS} second delay between commands)")
    print("-" * 70)
    had_failure = False
    error_details = []
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
                    send_telegram_message(f"🤖 Ramki TT Wallet\n\nSTOP command JSON parse error: {str(e)}")
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
                send_telegram_message(f"🤖 Ramki TT Wallet\n\n{error_msg}")
                break
        except Exception as e:
            had_failure = True
            error_msg = f"STOP command exception at iteration {i+1}/{NUM_TOGGLES}: {str(e)}"
            error_details.append(error_msg)
            send_telegram_message(f"🤖 Ramki TT Wallet\n\n{error_msg}")
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
                    send_telegram_message(f"🤖 Ramki TT Wallet\n\nSTART command JSON parse error: {str(e)}")
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
                send_telegram_message(f"🤖 Ramki TT Wallet\n\n{error_msg}")
                break
        except Exception as e:
            had_failure = True
            error_msg = f"START command exception at iteration {i+1}/{NUM_TOGGLES}: {str(e)}"
            error_details.append(error_msg)
            send_telegram_message(f"🤖 Ramki TT Wallet\n\n{error_msg}")
            break
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
                error_details.append(f"Response: {response.text[:200]}")
            except:
                pass
        had_failure = True
    if had_failure:
        print("\n" + "="*70)
        print(" ❌ AUTOMATION FAILED")
        print("="*70)
        error_summary = "\n".join(error_details) if error_details else "Unknown error during toggle operations"
        telegram_msg = f"🤖❌ <b>Ramki TT Wallet - FAILED</b>\n\n<b>Error Details:</b>\n<pre>{error_summary}</pre>"
        send_telegram_message(telegram_msg)
        sys.exit(1)
    print("\n" + "="*70)
    print(" ✓ AUTOMATION COMPLETED!")
    print("="*70)
    print(f"\nToggled Start/Stop {NUM_TOGGLES} times using direct API calls")
    print("No browser needed - instant execution!")
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
    msg = (
        f"🤖✅ <b>Ramki TT Wallet - SUCCESS</b>\n\n"
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
        tb_lines = traceback.format_exc().split('\n')
        error_details = '\n'.join(tb_lines[-10:])
        telegram_msg = f"🤖❌ <b>Ramki TT Wallet - FAILED</b>\n\n<b>Error:</b> {str(e)}\n\n<b>Details:</b>\n<pre>{error_details}</pre>"
        send_telegram_message(telegram_msg)
        sys.exit(1)
