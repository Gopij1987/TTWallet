#!/usr/bin/env python3
"""Validate Gopi and Ramki wallet cookies and API access.

Reads `wallet_monitor.env` and legacy .env files when running locally.
Prints the HTTP status and response bodies for the wallet check and strategy API.
"""
import os
import base64
import pickle
import requests
from dotenv import load_dotenv

# Load local envs (if present)
base_dir = os.path.dirname(__file__)
load_dotenv(os.path.join(base_dir, 'wallet_monitor.env'))
load_dotenv(os.path.join(base_dir, 'TTGopiWallet', '.env'))
load_dotenv(os.path.join(base_dir, 'TTRamkiWallet', '.env'))

WALLETS = {
    'Gopi': {'cookie_var': 'TT_COOKIES_B64_GOPI', 'strategy_var': 'STRATEGY_ID_GOPI', 'default_strategy': 18713274},
    'Ramki': {'cookie_var': 'TT_COOKIES_B64_RAMKI', 'strategy_var': 'STRATEGY_ID_RAMKI', 'default_strategy': 12345678},
}


def check(wallet_name, cookie_env, strategy_id):
    print('\n' + '='*60)
    print(f'Checking {wallet_name} (strategy {strategy_id})')
    print('='*60)
    encoded = os.getenv(cookie_env)
    if not encoded:
        print(f'  ❌ Env {cookie_env} not set')
        return
    try:
        cookies_bytes = base64.b64decode(encoded)
        cookies = pickle.loads(cookies_bytes)
    except Exception as e:
        print('  ❌ Failed to decode/load cookies:', e)
        return
    session = requests.Session()
    for cookie in cookies:
        try:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
        except Exception:
            pass
    # Wallet endpoint
    wallet_url = 'https://tradetron.tech/api/pricing/user-taxes'
    try:
        r = session.get(wallet_url, timeout=10)
        print('  Wallet endpoint:', r.status_code)
        try:
            print('   Response body:', r.text[:400])
        except Exception:
            pass
    except Exception as e:
        print('  Wallet request failed:', e)
    # Strategy API
    api_url = f'https://tradetron.tech/api/deployed/status?id={strategy_id}'
    try:
        r2 = session.get(api_url, timeout=10)
        print('  Strategy API:', r2.status_code)
        try:
            print('   Response body:', r2.text[:400])
        except Exception:
            pass
    except Exception as e:
        print('  Strategy request failed:', e)


if __name__ == '__main__':
    for name, cfg in WALLETS.items():
        strategy = int(os.getenv(cfg['strategy_var']) or cfg['default_strategy'])
        check(name, cfg['cookie_var'], strategy)
    print('\nDone')
