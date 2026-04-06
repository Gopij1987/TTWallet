"""
Login to Tradetron using cookies from .env file
Uses TT_COOKIES_B64_GOPI for authenticated session
"""

import os
import sys
import pickle
import base64
from pathlib import Path
from dotenv import load_dotenv
import requests
from urllib.parse import urljoin

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

def load_cookies_from_env():
    """Load and decode cookies from .env TT_COOKIES_B64_GOPI"""
    
    cookies_b64 = os.getenv("TT_COOKIES_B64_GOPI")
    
    if not cookies_b64:
        print("❌ TT_COOKIES_B64_GOPI not found in .env")
        return None
    
    try:
        # Decode base64
        cookies_pickle = base64.b64decode(cookies_b64)
        
        # Unpickle the cookies
        cookies = pickle.loads(cookies_pickle)
        
        print(f"✓ Loaded {len(cookies)} cookies from .env")
        print(f"  Cookie names: {', '.join([c.get('name', 'unknown') for c in cookies[:3]])}...")
        
        return cookies
    except Exception as e:
        print(f"❌ Error decoding cookies: {e}")
        return None

def create_session_with_cookies(cookies):
    """Create authenticated requests session with cookies"""
    
    session = requests.Session()
    
    # Add cookies to session
    for cookie_dict in cookies:
        domain = cookie_dict.get('domain', '.tradetron.tech')
        name = cookie_dict.get('name')
        value = cookie_dict.get('value')
        
        if name and value:
            session.cookies.set(name, value, domain=domain)
    
    print(f"✓ Created session with {len(session.cookies)} cookies")
    return session

def validate_login(session):
    """Test if authentication is working by calling API"""
    
    print("\n" + "=" * 80)
    print("VALIDATING LOGIN")
    print("=" * 80)
    
    endpoints = [
        ("Profile Check", "https://tradetron.tech/api/profile"),
        ("Dashboard Check", "https://tradetron.tech/api/dashboard"),
        ("Deployments Check", "https://tradetron.tech/api/deployed"),
    ]
    
    for endpoint_name, url in endpoints:
        try:
            print(f"\nTesting {endpoint_name}...")
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✓ {endpoint_name}: SUCCESS (200)")
                if 'data' in response.json():
                    data = response.json()['data']
                    if isinstance(data, dict):
                        print(f"    Response keys: {', '.join(list(data.keys())[:3])}...")
            elif response.status_code == 401:
                print(f"  ❌ {endpoint_name}: UNAUTHORIZED (401)")
            elif response.status_code == 404:
                print(f"  ⚠️  {endpoint_name}: NOT FOUND (404)")
            else:
                print(f"  ⚠️  {endpoint_name}: Status {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Try to get user info
    try:
        print(f"\nGetting user info...")
        response = session.get("https://tradetron.tech/api/user/profile", timeout=10)
        
        if response.status_code == 200:
            user_data = response.json().get('data', {})
            print(f"  ✓ Logged in as: {user_data.get('name', 'Unknown')}")
            print(f"  Email: {user_data.get('email', 'N/A')}")
            return True
        else:
            print(f"  Status: {response.status_code}")
            
    except Exception as e:
        print(f"  Error: {str(e)}")
    
    return False

def test_authenticated_request(session):
    """Test an authenticated request using cookies"""
    
    print("\n" + "=" * 80)
    print("TESTING AUTHENTICATED REQUESTS")
    print("=" * 80)
    
    # Test deployment API
    try:
        print("\nFetching deployments...")
        response = session.get("https://tradetron.tech/api/deployed", timeout=10)
        
        if response.status_code == 200:
            print(f"  ✓ Connected successfully (200)")
            data = response.json()
            if 'data' in data and isinstance(data['data'], list):
                print(f"  ✓ Found {len(data['data'])} deployments")
                if data['data']:
                    first = data['data'][0]
                    print(f"  First deployment: {first.get('id', 'N/A')}")
            return True
        else:
            print(f"  Status code: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    return False

def main():
    """Main login flow"""
    
    print("=" * 80)
    print("TRADETRON LOGIN WITH COOKIES")
    print("=" * 80)
    
    # Step 1: Load cookies
    print("\n[1/4] Loading cookies from .env...")
    cookies = load_cookies_from_env()
    
    if not cookies:
        print("\n❌ Failed to load cookies")
        sys.exit(1)
    
    # Step 2: Create session
    print("\n[2/4] Creating authenticated session...")
    session = create_session_with_cookies(cookies)
    
    # Step 3: Validate login
    print("\n[3/4] Validating authentication...")
    is_valid = validate_login(session)
    
    # Step 4: Test authenticated requests
    print("\n[4/4] Testing authenticated requests...")
    is_working = test_authenticated_request(session)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if is_working:
        print("\n✓ LOGIN SUCCESSFUL!")
        print("✓ Authenticated session is ready to use")
        print("✓ Cookies are valid and working")
        return 0
    else:
        print("\n⚠️  LOGIN VALIDATION INCOMPLETE")
        print("  Cookies loaded but API endpoints may be unreachable")
        return 1

if __name__ == "__main__":
    sys.exit(main())
