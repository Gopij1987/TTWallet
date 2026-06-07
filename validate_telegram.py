#!/usr/bin/env python3
"""Simple validator for Telegram bot token and optional chat_id.

Usage:
  python validate_telegram.py --token <BOT_TOKEN> [--chat <CHAT_ID>]
Or set env vars TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID and run without args.

This script calls `getMe` to verify the token and optionally `sendMessage` to verify chat_id.
"""
import os
import sys
import argparse
import requests


def mask_token(t):
    if not t:
        return '<empty>'
    if len(t) <= 10:
        return t
    return t[:4] + '...' + t[-4:]


def main():
    parser = argparse.ArgumentParser(description='Validate Telegram bot token and optional chat id')
    parser.add_argument('--token', '-t', help='Bot token (overrides TELEGRAM_BOT_TOKEN env)')
    parser.add_argument('--chat', '-c', help='Chat id to test sendMessage (overrides TELEGRAM_CHAT_ID env)')
    args = parser.parse_args()

    token = args.token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat = args.chat or os.getenv('TELEGRAM_CHAT_ID')

    if not token:
        print('❌ No bot token provided via --token or TELEGRAM_BOT_TOKEN')
        return 2

    print('Using token:', mask_token(token))

    # Check getMe
    try:
        r = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
    except Exception as e:
        print('❌ getMe request failed:', str(e))
        return 1

    print('getMe response:', r.status_code, r.text)
    if r.status_code != 200:
        print('❌ Token validation failed (getMe)')
        return 1

    try:
        data = r.json()
    except Exception:
        print('❌ getMe returned non-JSON response')
        return 1

    if not data.get('ok'):
        print('❌ getMe reported not ok:', data)
        return 1

    print('✅ Token is valid (getMe returned bot info)')

    if chat:
        print('Testing sendMessage to chat id:', chat)
        try:
            r2 = requests.post(f'https://api.telegram.org/bot{token}/sendMessage', json={'chat_id': chat, 'text': 'TT Wallet monitor: test message from validator'}, timeout=10)
            print('sendMessage response:', r2.status_code, r2.text)
            if r2.status_code == 200:
                print('✅ sendMessage succeeded')
                return 0
            else:
                print('❌ sendMessage failed')
                return 1
        except Exception as e:
            print('❌ sendMessage request failed:', str(e))
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
