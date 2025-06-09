# zerodha_token_refresh.py
"""
Zerodha Access Token Refresh Script
Run this daily to get a new access token
"""
from kiteconnect import KiteConnect
import pyotp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your Zerodha credentials from .env
API_KEY = os.getenv('ZERODHA_API_KEY')
API_SECRET = os.getenv('ZERODHA_API_SECRET')

print("🔗 Zerodha Access Token Refresh")
print("=" * 40)

# Step 1: Initialize KiteConnect
kite = KiteConnect(api_key=API_KEY)

# Step 2: Get login URL
login_url = kite.login_url()
print(f"📱 Open this URL in your browser:")
print(f"{login_url}")
print()

# Step 3: Get request token from user
print("After logging in, you'll be redirected to a URL like:")
print("https://127.0.0.1:5000/?request_token=XXXXXX&action=login&status=success")
print()

request_token = input("📝 Enter the request_token from the URL: ").strip()

try:
    # Step 4: Generate session
    data = kite.generate_session(request_token, api_secret=API_SECRET)
    access_token = data["access_token"]
    
    print(f"✅ Success! New access token: {access_token}")
    print()
    
    # Step 5: Update .env file
    env_path = '.env'
    
    # Read current .env
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Replace old token with new one
    lines = env_content.split('\n')
    updated_lines = []
    
    for line in lines:
        if line.startswith('ZERODHA_ACCESS_TOKEN='):
            updated_lines.append(f'ZERODHA_ACCESS_TOKEN={access_token}')
            print(f"🔄 Updated ZERODHA_ACCESS_TOKEN in .env")
        else:
            updated_lines.append(line)
    
    # Write updated .env
    with open(env_path, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print("✅ .env file updated successfully!")
    print("🚀 You can now restart your trading system")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("💡 Make sure you:")
    print("   1. Used the correct request_token")
    print("   2. Have valid API credentials")
    print("   3. Haven't used this request_token before")
