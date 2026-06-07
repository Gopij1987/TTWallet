---
description: How to run and check TT Wallet V1 automation
---

# TT Wallet V1 — Run & Status

## Automatic (cron)
Runs **Mon–Fri 7:30 AM IST** automatically. No action needed.

## Manual Trigger via Telegram

### Check bot status
```
/status
```
Reply shows: `Bot is running`, `Mode: Polling`, `Authorized chat: OK`

### Run automation now
```
/run
```
Bot triggers full automation (Ramki → Gopi) and replies with:
- Toggle count per account
- Cookie source used (Shared / Fallback)
- Running count
- Any errors

## SSH Manual Run (if needed)

```bash
ssh -i ~/.ssh/LightsailDefaultKey.pem ubuntu@43.205.116.126
python3 ~/tt-wallet/Wallet\ V1/tt_integrated_automation.py
```

## VPS Service Status

```bash
# Check bot service
sudo systemctl status tt-wallet-bot

# Restart bot
sudo systemctl restart tt-wallet-bot

# View bot logs
sudo journalctl -u tt-wallet-bot -f

# View automation logs
sudo tail -f /var/log/tt-auto.log
```
