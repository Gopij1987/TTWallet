"""
Refresh Tradetron Cookies and save to file (Ramki Wallet)
Run locally to keep cookies fresh
"""

import requests
import pickle
import base64
import os
import subprocess
from shutil import which
from pathlib import Path
from config_TTRamkiWallet import load_credentials, validate_credentials

COOKIES_FILE = Path(__file__).parent / "tradetron_cookies_ramki.pkl"

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
    try:
        # Initialize driver with matching Chrome version
        driver = webdriver.Chrome(
            service=webdriver.ChromeService(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        print("Opening Tradetron login page...")
        driver.get("https://tradetron.tech/login")
        
        # Wait and fill email
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_field.send_keys(creds['username'])
        print("✓ Email entered")
        
        # Fill password
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(creds['password'])
        print("✓ Password entered")
        
        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[contains(., 'Login') or contains(., 'Sign in')]")
        login_button.click()
        print("✓ Login button clicked")

        # Wait for user to solve captcha and complete login
        print("\n⚠️ Solve the captcha in the browser, then press Enter here to continue...")
        input()

        # Wait for redirect (dashboard or logged-in state)
        WebDriverWait(driver, 60).until(
            lambda d: "dashboard" in d.current_url or "login" not in d.current_url
        )

        if "dashboard" in driver.current_url or "login" not in driver.current_url:
            print("✓ Login successful!")
            
            # Extract cookies
            cookies_list = []
            for cookie in driver.get_cookies():
                cookies_list.append({
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie.get('domain', '.tradetron.tech')
                })
            
            # Save cookies
            COOKIES_FILE.write_bytes(pickle.dumps(cookies_list))
            print(f"✓ Cookies saved to {COOKIES_FILE}")
            print(f"✓ Total cookies: {len(cookies_list)}")
            
            # Generate base64 for GitHub secret
            print("\n" + "="*70)
            print("📋 Base64 encoded cookies for GitHub secret TT_COOKIES_B64_RAMKI:")
            print("="*70)
            cookies_b64 = base64.b64encode(COOKIES_FILE.read_bytes()).decode('utf-8')
            print(cookies_b64)
            print("="*70)
            print("\nℹ️  Copy the above value and update the GitHub secret:")
            print("   https://github.com/Gopij1987/TTLogin/settings/secrets/actions")
            print("   Secret name: TT_COOKIES_B64_RAMKI")
            print("="*70)

            # Update the local TTRamkiWallet/.env (create if missing)
            env_path = Path(__file__).parent / ".env"
            update_env_with_cookies_b64(env_path, cookies_b64)
            print(f'✓ .env file updated with new TT_COOKIES_B64_RAMKI value at {env_path}')

            return True
        else:
            print(f"❌ Login failed. Current URL: {driver.current_url}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if driver:
            driver.quit()


def update_env_with_cookies_b64(env_path, b64_value):
    """Update TT_COOKIES_B64_RAMKI in .env file with new base64 value.

    If the file does not exist, create it.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text("# .env created by refresh_cookies_TTRamkiWallet\n", encoding='utf-8')

    with env_path.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    with env_path.open('w', encoding='utf-8') as f:
        found = False
        for line in lines:
            if line.strip().startswith('TT_COOKIES_B64_RAMKI='):
                f.write(f'TT_COOKIES_B64_RAMKI={b64_value}\n')
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f'TT_COOKIES_B64_RAMKI={b64_value}\n')

if __name__ == "__main__":
    success = login_and_save_cookies()
    exit(0 if success else 1)
