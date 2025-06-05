# config/zerodha/auth.py - Zerodha Authentication Handler
import os
import json
import webbrowser
from kiteconnect import KiteConnect
from datetime import datetime, timedelta

class ZerodhaAuth:
    """Handle Zerodha authentication and session management"""
    
    def __init__(self):
        self.api_key = os.getenv('ZERODHA_API_KEY')
        self.api_secret = os.getenv('ZERODHA_API_SECRET')
        self.access_token = os.getenv('ZERODHA_ACCESS_TOKEN')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("❌ Zerodha API credentials not found in .env file")
        
        self.kite = KiteConnect(api_key=self.api_key)
        self.session_file = 'config/zerodha/session.json'
        
    def get_login_url(self):
        """Generate login URL for authentication"""
        login_url = self.kite.login_url()
        print(f"🔐 Zerodha Login URL: {login_url}")
        return login_url
    
    def open_login_browser(self):
        """Open login URL in browser automatically"""
        try:
            login_url = self.get_login_url()
            webbrowser.open(login_url)
            print("🌐 Login page opened in browser")
            print("📋 After login, copy the 'request_token' from the URL")
            return True
        except Exception as e:
            print(f"❌ Browser open failed: {e}")
            return False
    
    def generate_session(self, request_token):
        """Generate access token from request token"""
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            
            # Save session data
            session_data = {
                'access_token': self.access_token,
                'user_id': data.get('user_id'),
                'user_name': data.get('user_name'),
                'email': data.get('email'),
                'generated_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=1)).isoformat()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print(f"✅ Session generated successfully!")
            print(f"👤 User: {data.get('user_name')} ({data.get('user_id')})")
            print(f"💾 Session saved to: {self.session_file}")
            print(f"🔑 Access Token: {self.access_token[:20]}...")
            
            # Update .env file
            self.update_env_file()
            
            return data
            
        except Exception as e:
            print(f"❌ Session generation failed: {e}")
            return None
    
    def update_env_file(self):
        """Update .env file with access token"""
        try:
            env_file = '.env'
            lines = []
            token_updated = False
            
            # Read existing .env file
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    lines = f.readlines()
            
            # Update or add access token
            for i, line in enumerate(lines):
                if line.startswith('ZERODHA_ACCESS_TOKEN='):
                    lines[i] = f'ZERODHA_ACCESS_TOKEN={self.access_token}\n'
                    token_updated = True
                    break
            
            if not token_updated:
                lines.append(f'ZERODHA_ACCESS_TOKEN={self.access_token}\n')
            
            # Write back to .env file
            with open(env_file, 'w') as f:
                f.writelines(lines)
            
            print(f"💾 Updated .env file with access token")
            
        except Exception as e:
            print(f"⚠️ Could not update .env file: {e}")
    
    def load_saved_session(self):
        """Load previously saved session"""
        try:
            if not os.path.exists(self.session_file):
                return False
            
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is still valid
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                print("⏰ Saved session expired")
                return False
            
            self.access_token = session_data['access_token']
            self.kite.set_access_token(self.access_token)
            
            print(f"✅ Loaded saved session for user: {session_data.get('user_name')}")
            return True
            
        except Exception as e:
            print(f"⚠️ Could not load saved session: {e}")
            return False
    
    def authenticate(self):
        """Complete authentication process"""
        try:
            # Try to load saved session first
            if self.load_saved_session():
                return True
            
            # If access token is in env, try to use it
            if self.access_token:
                self.kite.set_access_token(self.access_token)
                print("✅ Using access token from environment")
                return True
            
            # Need manual authentication
            print("🔐 Manual authentication required")
            return False
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
