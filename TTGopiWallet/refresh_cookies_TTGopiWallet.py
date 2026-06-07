"""Refresh Tradetron Cookies and generate base64 for GitHub (Gopi Wallet)
Run in GitHub Actions weekly to keep cookies fresh
"""

import base64
import os
import pickle
import time
from pathlib import Path

from config_TTGopiWallet import load_credentials, validate_credentials

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
        from selenium.webdriver.chrome.service import Service
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
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Block common ad/cookie overlays and expose closed shadow roots where possible.
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": [
            "*nextroll.com*", "*adroll.com*", "*nr-data.net*",
            "*d.adroll.com*", "*s.adroll.com*"
        ]})
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": """
            const _attachShadow = Element.prototype.attachShadow;
            Element.prototype.attachShadow = function(init) {
                return _attachShadow.call(this, { ...init, mode: 'open' });
            };
        """})
        
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
        
        # Try to solve ALTCHA automatically before submitting the form.
        print("\n⚙️  Trying automated ALTCHA handling...")
        altcha_triggered = handle_altcha_captcha(driver)
        if not altcha_triggered:
            print("⚠️  ALTCHA was not solved automatically. You can solve it manually if prompted.")

        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[contains(., 'Login') or contains(., 'Sign in')]")
        login_button.click()
        print("✓ Login button clicked")

        # If the automated flow did not complete, allow a manual fallback.
        if not altcha_triggered:
            print("\n⚠️ Solve the captcha in the browser, then press Enter here to continue...")
            input()

        # Let the post-submit state settle, then capture cookies and continue the old flow.
        try:
            WebDriverWait(driver, 20).until(
                lambda d: "login" not in d.current_url or "dashboard" in d.current_url
            )
        except Exception:
            pass

        time.sleep(2)
        print(f"✓ Post-sign-in URL: {driver.current_url}")

        # Extract cookies immediately after the sign-in flow has settled.
        cookies_list = []
        for cookie in driver.get_cookies():
            cookies_list.append({
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain', '.tradetron.tech')
            })

        print(f"✓ Total cookies: {len(cookies_list)}")

        # Generate base64 for GitHub secret
        print("\n" + "="*70)
        print("📋 Base64 encoded cookies for GitHub secret TT_COOKIES_B64_GOPI:")
        print("="*70)
        cookies_b64 = base64.b64encode(pickle.dumps(cookies_list)).decode('utf-8')
        print(cookies_b64)
        print("="*70)
        print("\nℹ️  Copy the above value and update the GitHub secret:")
        print("   https://github.com/Gopij1987/TTLogin/settings/secrets/actions")
        print("   Secret name: TT_COOKIES_B64_GOPI")
        print("="*70)

        # Update the local TTGopiWallet/.env (create if missing)
        env_path = Path(__file__).parent / ".env"
        update_env_with_cookies_b64(env_path, cookies_b64)
        print(f'✓ .env file updated with new TT_COOKIES_B64_GOPI value at {env_path}')

        return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if driver:
            driver.quit()


def handle_altcha_captcha(driver):
    """Trigger ALTCHA verification if the widget is present."""
    try:
        from selenium.webdriver.common.by import By

        for attempt in range(8):
            result = driver.execute_script("""
                var widget = document.querySelector('altcha-widget');
                if (!widget) return 'no-widget';

                if (typeof widget.verify === 'function') {
                    try { widget.verify(); return 'verify-called'; } catch (e) {}
                }

                var root = widget.shadowRoot || widget;
                var cb = root.querySelector('input[type="checkbox"]');
                if (!cb) return 'no-checkbox';
                cb.click();
                return 'clicked';
            """)
            print(f"   ALTCHA attempt {attempt + 1}: {result}")
            if result in ("clicked", "verify-called"):
                break
            if result == "no-widget":
                time.sleep(1)
                continue
            time.sleep(1)

        cbs = driver.find_elements(By.CSS_SELECTOR, "altcha-widget input[type='checkbox']")
        if cbs:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cbs[0])
            time.sleep(0.3)
            cbs[0].click()
            print("   Selenium-clicked ALTCHA checkbox.")

        print("   Waiting for ALTCHA proof-of-work to complete (up to 30s)...")
        for _ in range(30):
            time.sleep(1)
            state = driver.execute_script("""
                var w = document.querySelector('altcha-widget');
                if (!w) return 'no-widget';
                var d = w.querySelector('[data-state]');
                return d ? d.getAttribute('data-state') : (w.getAttribute('state') || 'pending');
            """)
            print(f"   ALTCHA state: {state}")
            if state == "verified":
                print("   ✔ ALTCHA verified.")
                return True
    except Exception as e:
        print(f"   ALTCHA step error: {e} — continuing anyway...")

    return False

def update_env_with_cookies_b64(env_path, b64_value):
    """Update TT_COOKIES_B64_GOPI in .env file with new base64 value.

    If the file does not exist, create it.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text("# .env created by refresh_cookies_TTGopiWallet\n", encoding='utf-8')

    with env_path.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    with env_path.open('w', encoding='utf-8') as f:
        found = False
        for line in lines:
            if line.strip().startswith('TT_COOKIES_B64_GOPI='):
                f.write(f'TT_COOKIES_B64_GOPI={b64_value}\n')
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f'TT_COOKIES_B64_GOPI={b64_value}\n')

if __name__ == "__main__":
    success = login_and_save_cookies()
    exit(0 if success else 1)
