"""
Shared Selenium cookie refresh helper.
Parametrized by username/password — works for any Tradetron account.

Usage:
    from cookie_refresh import refresh_cookies_via_selenium
    session = refresh_cookies_via_selenium("user@email.com", "password")
"""

import time
import pickle
import traceback


def refresh_cookies_via_selenium(username, password):
    """
    Login to Tradetron via Selenium, extract cookies, return a requests.Session.
    Requires Chrome + ChromeDriver on the VPS.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as e:
        raise ImportError("Required packages not installed. Run: pip install selenium webdriver-manager") from e

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # Headless to keep VPS RAM low; remove if captcha needs visual interaction
    chrome_options.add_argument("--headless")

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Block ad/cookie overlays
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

        print("  Opening Tradetron login page...")
        driver.get("https://tradetron.tech/login")

        # Fill email
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_field.send_keys(username)
        print("  Email entered")

        # Fill password
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        print("  Password entered")

        # Try ALTCHA
        altcha_triggered = _handle_altcha_captcha(driver)
        if not altcha_triggered:
            print("  ALTCHA not solved automatically (headless may fail here)")

        # Click login
        login_button = driver.find_element(By.XPATH, "//button[contains(., 'Login') or contains(., 'Sign in')]")
        login_button.click()
        print("  Login button clicked")

        # Wait for redirect
        try:
            WebDriverWait(driver, 20).until(
                lambda d: "login" not in d.current_url or "dashboard" in d.current_url
            )
        except Exception:
            pass
        time.sleep(2)
        print(f"  Post-login URL: {driver.current_url}")

        # Extract cookies
        cookies_list = []
        for cookie in driver.get_cookies():
            cookies_list.append({
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie.get("domain", ".tradetron.tech")
            })
        print(f"  Extracted {len(cookies_list)} cookies")

        # Build requests session
        import requests
        session = requests.Session()
        for c in cookies_list:
            session.cookies.set(c["name"], c["value"], domain=c.get("domain"))
        return session

    except Exception:
        traceback.print_exc()
        raise
    finally:
        if driver:
            driver.quit()


def _handle_altcha_captcha(driver):
    """Trigger ALTCHA verification if the widget is present."""
    from selenium.webdriver.common.by import By
    try:
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
            print(f"    ALTCHA attempt {attempt + 1}: {result}")
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
            print("    Selenium-clicked ALTCHA checkbox")

        print("    Waiting for ALTCHA verification (up to 30s)...")
        for _ in range(30):
            time.sleep(1)
            state = driver.execute_script("""
                var w = document.querySelector('altcha-widget');
                if (!w) return 'no-widget';
                var d = w.querySelector('[data-state]');
                return d ? d.getAttribute('data-state') : (w.getAttribute('state') || 'pending');
            """)
            print(f"    ALTCHA state: {state}")
            if state == "verified":
                print("    ALTCHA verified")
                return True
    except Exception as e:
        print(f"    ALTCHA step error: {e} — continuing")
    return False
