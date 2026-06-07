"""
Telegram Bot Trigger for TT Wallet V1
Lightweight polling bot (~10 MB RAM). No open ports needed.

Commands:
  /run    — Trigger automation and reply with summary
  /status — Check if bot is running

Setup:
  systemd service: deploy/tt-wallet-bot.service
  Environment from .env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
"""

import os
import sys
import time
import requests
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
except ImportError:
    pass

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTH_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POLL_INTERVAL = 3  # seconds between polls


import json as _json

# Token V1 - Account configuration
TOKEN_ACCOUNTS = ["GJ114", "PP450", "RR1001"]

def get_main_menu_keyboard():
    """Main menu with Wallet, Token, Dashboard and Status options"""
    return {
        "keyboard": [
            [{"text": "🏦 Wallet"}, {"text": "🔑 Token"}],
            [{"text": "📊 Dashboard"}, {"text": "📊 Status"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }

def get_wallet_menu_keyboard():
    """Wallet submenu with Gopi, Ramki, All, and Back options"""
    return {
        "keyboard": [
            [{"text": "🏦 Gopi"}, {"text": "🏦 Ramki"}],
            [{"text": "🏦 All Accounts"}],
            [{"text": "🔙 Back to Main"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }

def get_token_menu_keyboard():
    """Token submenu with account selection"""
    # Build 2-column layout for accounts
    account_buttons = []
    for i in range(0, len(TOKEN_ACCOUNTS), 2):
        row = [{"text": f"🔐 {acc}"} for acc in TOKEN_ACCOUNTS[i:i+2]]
        account_buttons.append(row)
    
    # Add All Accounts and Back buttons
    account_buttons.append([{"text": "🔐 All Accounts"}])
    account_buttons.append([{"text": "🔙 Back to Main"}])
    
    return {
        "keyboard": account_buttons,
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }

def get_dashboard_menu_keyboard():
    """Dashboard submenu with restart option"""
    return {
        "keyboard": [
            [{"text": "🔄 Restart Dashboard"}],
            [{"text": "📊 Dashboard Status"}],
            [{"text": "🔙 Back to Main"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }

def send_telegram_reply(chat_id, text, reply_to_message_id=None, menu=False, token_menu=False, wallet_menu=False, dashboard_menu=False):
    """Send a text message reply via Telegram Bot API. Optionally show menu keyboard."""
    if not BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    if token_menu:
        payload["reply_markup"] = _json.dumps(get_token_menu_keyboard())
    elif wallet_menu:
        payload["reply_markup"] = _json.dumps(get_wallet_menu_keyboard())
    elif dashboard_menu:
        payload["reply_markup"] = _json.dumps(get_dashboard_menu_keyboard())
    elif menu:
        payload["reply_markup"] = _json.dumps(get_main_menu_keyboard())
    try:
        resp = requests.post(url, data=payload, timeout=15)
        if resp.status_code != 200:
            print(f"[telegram error] {resp.status_code}: {resp.text[:200]}")
        return resp.status_code == 200
    except Exception as e:
        print(f"[telegram exception] {e}")
        return False


def get_updates(offset=None):
    """Poll Telegram for new messages."""
    if not BOT_TOKEN:
        return []
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "limit": 10}
    try:
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        if data.get("ok"):
            return data.get("result", [])
    except Exception as e:
        print(f"[poll error] {e}")
    return []


def run_bot():
    """Main polling loop."""
    print("=" * 60)
    print(" TT Wallet + Token Bot - Polling Mode")
    print("=" * 60)

    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)
    if not AUTH_CHAT_ID:
        print("ERROR: TELEGRAM_CHAT_ID not set")
        sys.exit(1)

    print(f"Authorized chat: {AUTH_CHAT_ID}")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print("Commands: /runwallet | /runtoken | /status | /menu")
    print()

    offset = None

    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1

                message = update.get("message") or update.get("edited_message")
                if not message:
                    continue

                chat_id = str(message.get("chat", {}).get("id", ""))
                text = (message.get("text") or "").strip().lower()
                message_id = message.get("message_id")

                # Security: only respond to authorized chat
                if chat_id != str(AUTH_CHAT_ID):
                    continue

                if text in ["/start", "/menu", "🏦 wallet", "🔑 token", "📊 dashboard", "📊 status", "🔙 back to main"]:
                    print(f"[{time.strftime('%H:%M:%S')}] Received {text}")
                    
                    if text == "🔑 token":
                        send_telegram_reply(
                            chat_id,
                            "<b>🔑 Token V1</b>\n\nSelect account to generate token:",
                            message_id,
                            token_menu=True,
                        )
                    elif text == "📊 dashboard":
                        send_telegram_reply(
                            chat_id,
                            "<b>📊 Dashboard</b>\n\nSelect dashboard action:",
                            message_id,
                            dashboard_menu=True,
                        )
                    elif text == "🏦 wallet":
                        send_telegram_reply(
                            chat_id,
                            "<b>🏦 Wallet</b>\n\nSelect account to run:",
                            message_id,
                            wallet_menu=True,
                        )
                    else:
                        menu_text = "<b>TT Wallet + Token Bot</b>\n\nChoose an action:"
                        if text == "📊 status":
                            menu_text = "<b>📊 Bot Status</b>\n\n✅ Bot is running\n✅ Polling mode active\n✅ Authorized chat: OK"
                        send_telegram_reply(
                            chat_id,
                            menu_text,
                            message_id,
                            menu=True,
                        )

                elif text in ["🏦 gopi", "🏦 ramki", "🏦 all accounts", "/runwallet"]:
                    account_label = {
                        "🏦 gopi": "GOPI",
                        "🏦 ramki": "RAMKI",
                        "🏦 all accounts": "ALL",
                        "/runwallet": "ALL",
                    }.get(text, "ALL")
                    print(f"[{time.strftime('%H:%M:%S')}] Received wallet run for {account_label}")
                    send_telegram_reply(chat_id, f"🏦 Running wallet for <b>{account_label}</b>...", message_id)

                    try:
                        import tt_integrated_automation

                        if account_label == "GOPI":
                            results = tt_integrated_automation.run_automation(accounts=["GOPI"])
                        elif account_label == "RAMKI":
                            results = tt_integrated_automation.run_automation(accounts=["RAMKI"])
                        else:
                            results = tt_integrated_automation.run_automation()

                        if "_critical_error" in results:
                            send_telegram_reply(
                                chat_id,
                                f"<b>Automation Error</b>\n<pre>{results['_critical_error']}</pre>",
                                wallet_menu=True,
                            )
                        else:
                            summary = tt_integrated_automation.build_summary_message(results)
                            send_telegram_reply(chat_id, summary, wallet_menu=True)
                    except Exception as e:
                        print(f"[run error] {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_reply(
                            chat_id,
                            f"<b>Run Failed</b>\n<pre>{str(e)[:500]}</pre>",
                            wallet_menu=True,
                        )

                elif text in ["/runtoken gj114", "/runtoken pp450", "/runtoken rr1001", "/runtoken all",
                             "🔐 gj114", "🔐 pp450", "🔐 rr1001", "🔐 all accounts"]:
                    # Extract account tag
                    account = text.replace("/runtoken ", "").replace("🔐 ", "").upper()
                    if account == "ALL ACCOUNTS":
                        account = "ALL"
                    
                    print(f"[{time.strftime('%H:%M:%S')}] Received token request for {account}")
                    send_telegram_reply(chat_id, f"🔑 Running token generation for <b>{account}</b>...", message_id)
                    
                    # Run token automation
                    try:
                        # Add Token V1 path to sys.path if needed
                        # VPS path: /opt/token-v1/, Local path: Auto Login/Token V1
                        token_v1_path = Path("/opt/token-v1")
                        print(f"[token] Looking for Token V1 at: {token_v1_path}")
                        print(f"[token] Path exists: {token_v1_path.exists()}")
                        if not token_v1_path.exists():
                            token_v1_path = Path(__file__).parent.parent.parent / "Auto Login" / "Token V1"
                            print(f"[token] Fallback to: {token_v1_path}")
                        if str(token_v1_path) not in sys.path:
                            sys.path.insert(0, str(token_v1_path))
                            print(f"[token] Added to sys.path: {token_v1_path}")
                        print(f"[token] sys.path now: {sys.path[:3]}")
                        
                        import token_automation
                        print(f"[token] Successfully imported token_automation")
                        
                        if account == "ALL":
                            results = token_automation.run_all_accounts()
                            # Build summary
                            success_count = sum(1 for r in results.values() if r.get("success"))
                            summary = f"<b>🔑 Token V1 - All Accounts</b>\n\n"
                            for acc, result in results.items():
                                status = "✅" if result.get("success") else "❌"
                                summary += f"{status} {acc}\n"
                            summary += f"\n<b>Total: {success_count}/{len(results)} successful</b>"
                            send_telegram_reply(chat_id, summary, menu=True)
                        else:
                            result = token_automation.run_token_automation(account)
                            # token_automation already sends detailed notification
                            # No need for bot to send additional message
                    except Exception as e:
                        print(f"[token error] {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_reply(
                            chat_id,
                            f"<b>❌ Token Run Failed</b>\n<pre>{str(e)[:500]}</pre>",
                            token_menu=True,
                        )

                elif text in ["🔄 restart dashboard", "/restartdashboard"]:
                    print(f"[{time.strftime('%H:%M:%S')}] Received dashboard restart request")
                    send_telegram_reply(chat_id, "🔄 Restarting TT Dashboard...", message_id)
                    
                    try:
                        import subprocess
                        result = subprocess.run(
                            ["sudo", "systemctl", "restart", "tt-dashboard"],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            # Check if service is actually running
                            time.sleep(3)
                            status_result = subprocess.run(
                                ["sudo", "systemctl", "is-active", "tt-dashboard"],
                                capture_output=True,
                                text=True
                            )
                            
                            if status_result.stdout.strip() == "active":
                                send_telegram_reply(
                                    chat_id,
                                    "✅ <b>TT Dashboard restarted successfully!</b>\n\n🌐 http://43.205.116.126:8003\n⏰ Restarted at " + 
                                    time.strftime("%H:%M:%S IST", time.localtime(time.time() + 19800)),
                                    dashboard_menu=True
                                )
                            else:
                                send_telegram_reply(
                                    chat_id,
                                    f"⚠️ <b>Dashboard restart completed but service not active</b>\n\nStatus: {status_result.stdout.strip()}",
                                    dashboard_menu=True
                                )
                        else:
                            send_telegram_reply(
                                chat_id,
                                f"❌ <b>Failed to restart TT Dashboard</b>\n\nError: {result.stderr}",
                                dashboard_menu=True
                            )
                    except subprocess.TimeoutExpired:
                        send_telegram_reply(
                            chat_id,
                            "⚠️ <b>Dashboard restart timeout</b>\n\nCommand took too long to execute.",
                            dashboard_menu=True
                        )
                    except Exception as e:
                        send_telegram_reply(
                            chat_id,
                            f"❌ <b>Dashboard restart failed</b>\n\nError: {str(e)}",
                            dashboard_menu=True
                        )

                elif text in ["📊 dashboard status", "/dashboardstatus"]:
                    print(f"[{time.strftime('%H:%M:%S')}] Received dashboard status request")
                    
                    try:
                        import subprocess
                        
                        # Get service status
                        status_result = subprocess.run(
                            ["sudo", "systemctl", "status", "tt-dashboard", "--no-pager", "-l"],
                            capture_output=True,
                            text=True
                        )
                        
                        # Get memory usage
                        memory_result = subprocess.run(
                            ["sudo", "systemctl", "show", "tt-dashboard", "--property=MemoryCurrent"],
                            capture_output=True,
                            text=True
                        )
                        
                        # Parse memory
                        memory_mb = "Unknown"
                        if memory_result.stdout.startswith("MemoryCurrent="):
                            memory_bytes = int(memory_result.stdout.split("=")[1].strip())
                            memory_mb = f"{memory_bytes // 1024 // 1024} MB"
                        
                        # Parse status
                        status_lines = status_result.stdout.split('\n')
                        active_line = next((line for line in status_lines if "Active:" in line), "")
                        
                        status_msg = f"<b>📊 TT Dashboard Status</b>\n\n"
                        status_msg += f"{active_line}\n"
                        status_msg += f"💾 Memory: {memory_mb}\n"
                        status_msg += f"🌐 http://43.205.116.126:8003"
                        
                        send_telegram_reply(chat_id, status_msg, dashboard_menu=True)
                        
                    except Exception as e:
                        send_telegram_reply(
                            chat_id,
                            f"❌ <b>Failed to get dashboard status</b>\n\nError: {str(e)}",
                            dashboard_menu=True
                        )

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            print(f"[loop error] {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_bot()
