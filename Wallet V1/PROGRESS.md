# TT Wallet V1 - Progress

## Status: FULLY DEPLOYED on VPS (Cron + Telegram Bot)

## Completed

### 1. Main Script (`tt_integrated_automation.py`)
- Sequential execution: Ramki → Gopi
- Cookie resolution order:
  1. Shared (TT Dash V3) — `/home/ubuntu/tt-dashboard/cookies/new_tr_cookies.b64`
  2. Fallback (individual `.b64`)
  3. Selenium refresh → save to fallback only
- `.b64` format (base64-encoded pickle), same as TT Dash V3
- Per-account shared cookie env vars: `TT_COOKIES_RAMKI`, `TT_COOKIES_GOPI`
- Telegram report shows **cookie source used** per account
- Added `run_automation()` function for module import (used by bot)

### 2. Selenium Helper (`cookie_refresh.py`)
- Shared module for both accounts
- Handles ALTCHA captcha

### 3. Telegram Bot Trigger (`telegram_bot.py`)
- Lightweight polling bot (~19 MB RAM)
- No open ports (outbound HTTPS only)
- Commands:
  - `/start` — Shows menu keyboard
  - `/runwallet` — Triggers full automation
  - `/status` — Shows bot health
- Systemd service: `tt-wallet-bot.service`
  - Auto-starts on boot, auto-restarts on crash

### 4. Cron (Mon–Fri 7:30 AM IST)
- Added to VPS crontab
- Runs independent of bot
- Zero idle RAM (script starts, exits)

### 5. Deploy (`push_to_vps.bat`)
- Pushes changed files to VPS
- Falls back to `scp` if `rsync` not available

## VPS Details

- IP: `43.205.116.126`
- User: `ubuntu`
- Key: `%USERPROFILE%\.ssh\LightsailDefaultKey.pem`
- Script path: `/home/ubuntu/tt-wallet/Wallet V1/`
- Automation log: `/var/log/tt-auto.log`
- Bot logs: `sudo journalctl -u tt-wallet-bot -f`

## Test Results (VPS)

| Test | Result |
|------|--------|
| Ramki automation | 5/5 toggles ✅ |
| Gopi automation | 5/5 toggles ✅ |
| Shared cookies loaded | ✅ |
| Telegram report (cron) | ✅ |
| Telegram bot `/status` | ✅ |
| Telegram bot `/runwallet` | ✅ |

## Files

```
Wallet V1/
  tt_integrated_automation.py     ← Main automation script
  cookie_refresh.py                ← Selenium login helper
  telegram_bot.py                  ← Telegram trigger bot
  requirements.txt                 ← Python dependencies
  .env                             ← Config (credentials + paths)
  .env.example                     ← Template
  push_to_vps.bat                  ← Deploy to VPS
  PROGRESS.md                      ← This file
  deploy/
    crontab.txt                    ← Cron job (Mon-Fri 7:30 AM IST)
    setup.sh                       ← VPS setup instructions
    tt-wallet-bot.service          ← Systemd service file
```

## How to Use

### Automatic (Cron)
- Runs Mon–Fri 7:30 AM IST automatically
- No action needed

### Manual via Telegram
```
/start      → Show menu
/runwallet  → Run automation now
/status     → Check bot status
```

### Manual via SSH
```bash
ssh -i ~/.ssh/LightsailDefaultKey.pem ubuntu@43.205.116.126
python3 ~/tt-wallet/Wallet\ V1/tt_integrated_automation.py
```

## Service Commands

```bash
# Check bot
sudo systemctl status tt-wallet-bot

# Restart bot
sudo systemctl restart tt-wallet-bot

# View bot logs
sudo journalctl -u tt-wallet-bot -f

# View automation logs
sudo tail -f /var/log/tt-auto.log
```
