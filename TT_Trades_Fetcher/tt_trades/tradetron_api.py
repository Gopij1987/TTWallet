"""
Tradetron API Client for TT Wallet
Handles authentication, API requests, and trade data extraction
"""

import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_TTGopiWallet import load_cookies, validate_cookies

class TradetronAPIClient:
    """Client for making authenticated requests to Tradetron API"""
    
    BASE_URL = "https://tradetron.tech"
    API_ENDPOINTS = {
        'dashboard': '/dashboard',
        'strategies': '/api/strategies',
        'trades': '/api/trades',
        'strategy_details': '/api/strategy/{strategy_id}',
        'trades_by_strategy': '/api/strategy/{strategy_id}/trades',
        'portfolio': '/api/portfolio',
        'orders': '/api/orders',
        'reports': '/api/reports',
    }
    
    def __init__(self, cookies=None):
        """Initialize the API client with cookies"""
        
        if cookies is None:
            # Load cookies from .env
            cookies = load_cookies()
            validate_cookies(cookies)
        
        self.cookies = cookies
        self.session = self._create_session()
        print(f"✓ Initialized Tradetron API client with {len(self.cookies)} cookies")
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with cookies"""
        
        session = requests.Session()
        
        # Add cookies to session
        for cookie in self.cookies:
            session.cookies.set(
                name=cookie['name'],
                value=cookie['value'],
                domain=cookie.get('domain', '.tradetron.tech')
            )
        
        # Set user agent
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        return session
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make an authenticated API request"""
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            print(f"📡 {method.upper()} {endpoint}")
            
            response = self.session.request(method, url, timeout=30, **kwargs)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print(f"❌ Unauthorized (401). Cookies may be expired.")
                return None
            else:
                print(f"⚠️  Status {response.status_code}: {response.text[:200]}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return None
    
    def get_dashboard(self) -> Optional[Dict[str, Any]]:
        """Get dashboard data"""
        return self._make_request('GET', self.API_ENDPOINTS['dashboard'])
    
    def get_strategies(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of all strategies"""
        response = self._make_request('GET', self.API_ENDPOINTS['strategies'])
        if response and isinstance(response, dict) and 'strategies' in response:
            return response['strategies']
        return response
    
    def get_strategy_details(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """Get details of a specific strategy"""
        endpoint = self.API_ENDPOINTS['strategy_details'].format(strategy_id=strategy_id)
        return self._make_request('GET', endpoint)
    
    def get_all_trades(self, limit: int = 100, offset: int = 0) -> Optional[List[Dict[str, Any]]]:
        """Get all trades with pagination"""
        endpoint = f"{self.API_ENDPOINTS['trades']}?limit={limit}&offset={offset}"
        response = self._make_request('GET', endpoint)
        
        if response and isinstance(response, dict) and 'trades' in response:
            return response['trades']
        return response
    
    def get_strategy_trades(self, strategy_id: int, limit: int = 100, offset: int = 0) -> Optional[List[Dict[str, Any]]]:
        """Get trades for a specific strategy"""
        endpoint = self.API_ENDPOINTS['trades_by_strategy'].format(strategy_id=strategy_id)
        endpoint = f"{endpoint}?limit={limit}&offset={offset}"
        
        response = self._make_request('GET', endpoint)
        if response and isinstance(response, dict) and 'trades' in response:
            return response['trades']
        return response
    
    def get_portfolio(self) -> Optional[Dict[str, Any]]:
        """Get portfolio information"""
        return self._make_request('GET', self.API_ENDPOINTS['portfolio'])
    
    def get_orders(self, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get recent orders"""
        endpoint = f"{self.API_ENDPOINTS['orders']}?limit={limit}"
        response = self._make_request('GET', endpoint)
        
        if response and isinstance(response, dict) and 'orders' in response:
            return response['orders']
        return response
    
    def test_connection(self) -> bool:
        """Test if connection to Tradetron is working"""
        print("\n📡 Testing Tradetron connection...")
        response = self._make_request('GET', self.API_ENDPOINTS['dashboard'])
        
        if response:
            print("✓ Successfully connected to Tradetron!")
            return True
        else:
            print("❌ Connection failed. Cookies may be expired.")
            return False


def main():
    """Example usage of the API client"""
    
    print("="*70)
    print("Tradetron API Client - Trade Data Extractor")
    print("="*70)
    
    try:
        # Initialize client
        client = TradetronAPIClient()
        
        # Test connection
        if not client.test_connection():
            print("\n⚠️  Cannot proceed without valid connection")
            return False
        
        # Get strategies
        print("\n" + "="*70)
        print("Fetching strategies...")
        print("="*70)
        strategies = client.get_strategies()
        if strategies:
            print(f"✓ Found {len(strategies)} strategies")
            for strategy in strategies[:3]:  # Show first 3
                print(f"  - {strategy.get('name', 'Unknown')} (ID: {strategy.get('id')})")
        
        # Get all trades
        print("\n" + "="*70)
        print("Fetching trades...")
        print("="*70)
        trades = client.get_all_trades(limit=50)
        if trades:
            print(f"✓ Found {len(trades)} recent trades")
            for trade in trades[:3]:  # Show first 3
                symbol = trade.get('symbol', 'N/A')
                entry = trade.get('entry_price', 'N/A')
                exit_price = trade.get('exit_price', 'N/A')
                pnl = trade.get('pnl', 'N/A')
                print(f"  - {symbol}: Entry={entry}, Exit={exit_price}, P&L={pnl}")
        
        # Get portfolio
        print("\n" + "="*70)
        print("Fetching portfolio...")
        print("="*70)
        portfolio = client.get_portfolio()
        if portfolio:
            print("✓ Portfolio data retrieved")
            print(f"  {json.dumps(portfolio, indent=2)[:500]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
