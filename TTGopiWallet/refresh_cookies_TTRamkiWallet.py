"""
Refresh Tradetron Cookies and save to file (Gopi Wallet)
Run in GitHub Actions weekly to keep cookies fresh
"""

import requests
import pickle
import base64
import os
import subprocess
from shutil import which
from pathlib import Path
from TTRamkiWallet.config_TTRamkiWallet import load_credentials, validate_credentials

<<<<<<< HEAD
COOKIES_FILE = Path(__file__).parent / "tradetron_cookies_gopi.pkl"
=======
COOKIES_FILE = Path(__file__).parent / "tradetron_cookies_ramki.pkl"
>>>>>>> 20f3c64 (Add Ramki workflow and env handling updates)

def login_and_save_cookies():
    """Login to Tradetron using Selenium and save cookies"""
    
    creds = load_credentials()
    validate_credentials(creds)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        print("❌ Required packages not installed. Run: pip install selenium webdriver-manager")
        return False
    
    # Setup Chrome options (force visible browser for captcha)
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    driver = None
        print("✓ Password entered")
=======

        driver = webdriver.Chrome(
