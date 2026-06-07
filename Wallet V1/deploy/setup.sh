#!/bin/bash
# VPS one-time setup for TT Wallet V1
# Run as root or with sudo after copying Wallet V1/ to /opt/tt-wallet/

set -e

echo "=== TT Wallet V1 VPS Setup ==="

APP_DIR="/opt/tt-wallet/Wallet V1"
VENV_DIR="/opt/tt-wallet/venv"
LOG_FILE="/var/log/tt-auto.log"

# Create directories
mkdir -p /opt/tt-wallet
mkdir -p "$(dirname "$APP_DIR")"

# Install system dependencies (Debian/Ubuntu)
if command -v apt-get &> /dev/null; then
    echo "Installing system deps..."
    apt-get update
    apt-get install -y python3 python3-venv python3-pip wget gnupg
    # Chrome + ChromeDriver
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    apt-get update
    apt-get install -y google-chrome-stable
fi

# Create virtual environment
echo "Creating Python venv..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install Python deps
echo "Installing Python deps..."
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

# Touch log file
touch "$LOG_FILE"
chmod 666 "$LOG_FILE"

echo ""
echo ""
echo "=== VPS Automation Flow ==="
echo ""
echo "  cron (Mon-Fri 7:30 AM IST)"
echo "    |"
echo "    v  tt_integrated_automation.py starts, runs once, exits"
echo "    |     - Zero background RAM usage"
echo "    |     - Sequential: Ramki -> Gopi"
echo "    |"
echo "    v  Per account cookie resolution:"
echo "         1. Shared .b64 file (from TT Dash V3 cookie keeper)"
echo "         2. Individual fallback .b64 file"
echo "         3. Selenium login -> save to fallback only"
echo "    |"
echo "    v  Consolidated Telegram report sent"
echo "    v  Log output -> /var/log/tt-auto.log"
echo "    v  Process exits -> RAM freed"
echo ""
echo "Setup complete. Next steps:"
echo "  1. Copy your .env file to: $APP_DIR/.env"
echo "  2. Ensure shared cookie file exists at the path in .env (or let fallback run)"
echo "  3. Add the cron line from deploy/crontab.txt:"
echo "     crontab -e"
echo "     (paste the line from crontab.txt)"
echo ""
echo "  4. (Optional) Enable Telegram bot trigger:"
echo "     sudo cp deploy/tt-wallet-bot.service /etc/systemd/system/"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl enable tt-wallet-bot"
echo "     sudo systemctl start tt-wallet-bot"
echo ""
echo "  Manual test run:"
echo "     source $VENV_DIR/bin/activate"
echo "     python3 \"$APP_DIR/tt_integrated_automation.py\""
echo ""
echo "  View logs:"
echo "     tail -f /var/log/tt-auto.log"
echo ""
echo "  Bot status:"
echo "     sudo systemctl status tt-wallet-bot"
