"""
Credentials loader for Tradetron automation
Reads from .env file or environment variables
"""

import os
from pathlib import Path

def load_credentials():
    """Load credentials from .env file or environment variables"""
    
    # Try loading from .env file first (local folder, then repo root)
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        env_file = Path(__file__).parent.parent / ".env"
    
    if env_file.exists():
        print(f"Loading credentials from {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    # Get credentials from environment (Gopi wallet specific)
    username = os.getenv('TRADETRON_USERNAME_GOPI')
    password = os.getenv('TRADETRON_PASSWORD_GOPI')
    headless = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
    timeout = int(os.getenv('TIMEOUT', 15))
    
    return {
        'username': username,
        'password': password,
        'headless': headless,
        'timeout': timeout
    }

def validate_credentials(creds):
    """Validate that credentials are provided"""
    if not creds['username'] or not creds['password']:
        raise ValueError(
            "Missing credentials!\n"
            "Option 1: Create .env file with TRADETRON_USERNAME_GOPI and TRADETRON_PASSWORD_GOPI\n"
            "Option 2: Set environment variables:\n"
            "  $env:TRADETRON_USERNAME_GOPI='your_email@example.com'\n"
            "  $env:TRADETRON_PASSWORD_GOPI='your_password'"
        )
    return True

if __name__ == "__main__":
    creds = load_credentials()
    print(f"Username: {creds['username']}")
    print(f"Password: {'*' * len(creds['password']) if creds['password'] else 'NOT SET'}")
    print(f"Headless: {creds['headless']}")
    print(f"Timeout: {creds['timeout']}s")
