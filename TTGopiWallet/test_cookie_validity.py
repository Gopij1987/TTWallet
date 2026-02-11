"""
Test Cookie Validity - Quick validation of Tradetron login session
"""

import requests
import pickle
import base64
import os
import sys
import traceback
from pathlib import Path

# Load environment variables from .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_cookie_validity():
    """Test if the cookie from environment variable is a valid login session"""
    
    print("\n" + "="*70)
    print(" TRADETRON COOKIE VALIDITY TEST")
    print("="*70)
    
    # Step 1: Load cookie from environment
    print("\n1. Loading cookie from TT_COOKIES_B64_GOPI environment variable...")
    encoded = os.getenv("TT_COOKIES_B64_GOPI")
    
    if not encoded:
        print("   ❌ TT_COOKIES_B64_GOPI environment variable not found!")
        print("\n   How to set it:")
        print("   - For local testing: Create a .env file with: TT_COOKIES_B64_GOPI=<your_base64_cookie>")
        print("   - For GitHub Actions: Add as a secret in repository settings")
        return False
    
    print("   ✓ Environment variable found")
    
    # Step 2: Decode the base64 cookie
    print("\n2. Decoding base64 cookie...")
    try:
        cookies_bytes = base64.b64decode(encoded)
        print(f"   ✓ Decoded successfully ({len(cookies_bytes)} bytes)")
    except Exception as e:
        print(f"   ❌ Failed to decode base64: {str(e)}")
        return False
    
    # Step 3: Load cookies into session
    print("\n3. Creating session with cookies...")
    try:
        session = requests.Session()
        cookies = pickle.loads(cookies_bytes)
        
        # Add cookies to session
        for cookie in cookies:
            session.cookies.set(
                cookie['name'], 
                cookie['value'], 
                domain=cookie.get('domain')
            )
        print(f"   ✓ Loaded {len(cookies)} cookies into session")
        
        # Show cookie names (for debugging)
        cookie_names = [c['name'] for c in cookies]
        print(f"   Cookies: {', '.join(cookie_names)}")
    except Exception as e:
        print(f"   ❌ Failed to load cookies: {str(e)}")
        return False
    
    # Step 4: Test the session with API call
    print("\n4. Testing session with API call...")
    print("   Endpoint: https://tradetron.tech/api/pricing/user-taxes")
    
    xsrf_token = session.cookies.get("XSRF-TOKEN") or session.cookies.get("X-XSRF-TOKEN")
    headers = {
        "Accept": "application/json",
        "Referer": "https://tradetron.tech/user/dashboard",
        "X-Requested-With": "XMLHttpRequest"
    }
    if xsrf_token:
        headers["X-XSRF-TOKEN"] = xsrf_token
        headers["X-CSRF-TOKEN"] = xsrf_token
    
    try:
        response = session.get(
            "https://tradetron.tech/api/pricing/user-taxes", 
            headers=headers,
            timeout=10
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ Response received successfully")
            
            # Try to parse and display wallet info
            try:
                data = response.json()
                balances = data.get("data", {}).get("balances", {})
                if balances:
                    print("\n   📊 Wallet Information:")
                    for key, value in balances.items():
                        print(f"      {key}: {value}")
            except Exception as e:
                print(f"   ⚠️  Could not parse response JSON: {str(e)}")
                print(f"   Raw response: {response.text[:200]}...")
            
            return True
        
        elif response.status_code == 401:
            print("   ❌ Status 401: Unauthorized - Cookie is EXPIRED or INVALID")
            print("   Action: Get fresh cookies by running refresh_cookies_TTGopiWallet.py")
            return False
        
        elif response.status_code == 403:
            print("   ❌ Status 403: Forbidden - Access denied")
            return False
        
        else:
            print(f"   ❌ Status {response.status_code}: Unexpected response")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out - Check internet connection")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    is_valid = test_cookie_validity()
    
    print("\n" + "="*70)
    if is_valid:
        print(" ✅ COOKIE IS VALID - Ready for automation!")
    else:
        print(" ❌ COOKIE IS INVALID - Need to refresh cookies")
    print("="*70 + "\n")
    
    return 0 if is_valid else 1

if __name__ == "__main__":
    sys.exit(main())
