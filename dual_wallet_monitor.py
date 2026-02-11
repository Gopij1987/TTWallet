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

# Load environment variables from .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
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

def check_wallet_cookie(wallet_name, env_var_name):
    """
    Check if a wallet cookie is valid and return wallet info
    Returns: (is_valid, wallet_info_dict)
    """
    print(f"\n🔍 Checking {wallet_name} wallet...")
    
    # Load cookie from environment
    encoded = os.getenv(env_var_name)
    
    if not encoded:
        print(f"   ❌ {env_var_name} not found")
        return False, {"error": f"Environment variable {env_var_name} not found"}
    
    print(f"   ✓ Cookie loaded from {env_var_name}")
    
    # Decode the base64 cookie
    try:
        cookies_bytes = base64.b64decode(encoded)
    except Exception as e:
        print(f"   ❌ Failed to decode base64: {str(e)}")
        return False, {"error": f"Base64 decode failed: {str(e)}"}
    
    # Load cookies into session
    try:
        session = requests.Session()
        cookies = pickle.loads(cookies_bytes)
        
        for cookie in cookies:
            session.cookies.set(
                cookie['name'], 
                cookie['value'], 
                domain=cookie.get('domain')
            )
        print(f"   ✓ Session created with {len(cookies)} cookies")
    except Exception as e:
        print(f"   ❌ Failed to load cookies: {str(e)}")
        return False, {"error": f"Cookie load failed: {str(e)}"}
    
    # Test the session with API call
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
        response = session.get(
            "https://tradetron.tech/api/pricing/user-taxes", 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                balances = data.get("data", {}).get("balances", {})
                print(f"   ✓ {wallet_name} cookie is VALID")
                return True, balances
            except Exception as e:
                print(f"   ⚠️  Response received but JSON parse failed: {str(e)}")
                return False, {"error": f"JSON parse failed: {str(e)}"}
        
        elif response.status_code == 401:
            print(f"   ❌ {wallet_name} cookie EXPIRED (401 Unauthorized)")
            return False, {"error": "Cookie expired - Status 401"}
        
        else:
            print(f"   ❌ {wallet_name} API error (Status {response.status_code})")
            return False, {"error": f"API error - Status {response.status_code}"}
            
    except requests.exceptions.Timeout:
        print(f"   ❌ {wallet_name} request timeout")
        return False, {"error": "Request timeout"}
    except Exception as e:
        print(f"   ❌ {wallet_name} request failed: {str(e)}")
        return False, {"error": str(e)}

def format_telegram_message(gopi_valid, gopi_info, ramki_valid, ramki_info):
    """Format wallet status into Telegram message - short and crispy"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    gopi_status = "✅" if gopi_valid else "❌"
    ramki_status = "✅" if ramki_valid else "❌"
    
    gopi_line = f"{gopi_status} Gopi: Running={gopi_info.get('running', '?')}"
    if not gopi_valid:
        gopi_line = f"{gopi_status} Gopi: {gopi_info.get('error', 'Error')}"
    
    ramki_line = f"{ramki_status} Ramki: Running={ramki_info.get('running', '?')}"
    if not ramki_valid:
        ramki_line = f"{ramki_status} Ramki: {ramki_info.get('error', 'Error')}"
    
    # Summary emoji
    if gopi_valid and ramki_valid:
        summary = "✅ All Good"
    elif gopi_valid or ramki_valid:
        summary = "⚠️ Check needed"
    else:
        summary = "❌ Down"
    
    msg = f"""<b>🤖 Cookie Check</b> {timestamp}

{gopi_line}
{ramki_line}

{summary}"""
    
    return msg

def main():
    print("\n" + "="*70)
    print(" DUAL WALLET COOKIE & HEALTH CHECK")
    print("="*70)
    
    # Detect local vs GitHub Actions run
    running_in_github = os.getenv('GITHUB_ACTIONS', '').lower() == 'true'
    
    # For GitHub Actions: require all secrets
    if running_in_github:
        print("\n🔧 Running in GitHub Actions environment")
        required_secrets = [
            ("TT_COOKIES_B64_GOPI", os.getenv("TT_COOKIES_B64_GOPI")),
            ("TT_COOKIES_B64_RAMKI", os.getenv("TT_COOKIES_B64_RAMKI")),
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
    
    # Check both wallets
    gopi_valid, gopi_info = check_wallet_cookie("Gopi", "TT_COOKIES_B64_GOPI")
    ramki_valid, ramki_info = check_wallet_cookie("Ramki", "TT_COOKIES_B64_RAMKI")
    
    # Format message
    telegram_msg = format_telegram_message(gopi_valid, gopi_info, ramki_valid, ramki_info)
    
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
    
    # Return success/failure
    return 0 if (gopi_valid and ramki_valid) else 1

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
