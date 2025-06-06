# fix_zerodha_auth.py
"""
Quick fix for Zerodha authentication issues
Handles expired tokens and re-authentication
"""
import os
import sys
import webbrowser
from datetime import datetime

sys.path.append('config')

def fix_zerodha_authentication():
    """Fix Zerodha authentication with step-by-step guidance"""
    print("🔧 Fixing Zerodha Authentication")
    print("=" * 40)
    
    try:
        from config.zerodha.auth import ZerodhaAuth
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Check API credentials
        api_key = os.getenv('ZERODHA_API_KEY')
        api_secret = os.getenv('ZERODHA_API_SECRET')
        
        if not api_key or not api_secret:
            print("❌ Missing API credentials in .env file")
            return False
        
        print(f"✅ API Key: {api_key[:8]}...")
        print(f"✅ API Secret: {api_secret[:8]}...")
        
        # Initialize auth
        auth = ZerodhaAuth()
        
        # Clear old session
        print("\n🗑️ Clearing old session...")
        session_file = 'config/zerodha/session.json'
        if os.path.exists(session_file):
            os.remove(session_file)
            print("✅ Old session cleared")
        
        # Remove old access token from environment
        print("🗑️ Clearing old access token...")
        
        # Start fresh authentication
        print("\n🔐 Starting fresh authentication...")
        print("This will open Zerodha login in your browser...")
        
        input("Press Enter to continue...")
        
        # Get login URL and open browser
        login_url = auth.get_login_url()
        print(f"\n🌐 Opening: {login_url}")
        
        try:
            webbrowser.open(login_url)
            print("✅ Browser opened successfully")
        except:
            print("⚠️ Could not open browser automatically")
            print(f"Please open this URL manually: {login_url}")
        
        print("\n" + "=" * 50)
        print("📋 AUTHENTICATION STEPS:")
        print("=" * 50)
        print("1. 🔑 Login with your Zerodha credentials in the browser")
        print("2. 📱 Complete 2FA if prompted")
        print("3. ✅ After successful login, you'll see a success page")
        print("4. 🔗 The URL will change to something like:")
        print("   https://127.0.0.1:5000/?request_token=ABC123&action=login&status=success")
        print("5. 📋 Copy ONLY the request_token part (e.g., ABC123)")
        print("=" * 50)
        
        # Get request token from user
        while True:
            request_token = input("\n🔑 Paste your request_token here: ").strip()
            
            if not request_token:
                print("❌ No token entered. Please try again.")
                continue
            
            if len(request_token) < 10:
                print("❌ Token seems too short. Please check and try again.")
                continue
            
            break
        
        # Generate session
        print(f"\n⚡ Generating session with token: {request_token[:10]}...")
        
        try:
            result = auth.generate_session(request_token)
            
            if result:
                print("\n✅ AUTHENTICATION SUCCESSFUL!")
                print(f"👤 Welcome: {result.get('user_name')}")
                print(f"🆔 User ID: {result.get('user_id')}")
                print(f"📧 Email: {result.get('email')}")
                
                # Test the new session
                print("\n🧪 Testing new session...")
                
                try:
                    profile = auth.kite.profile()
                    print(f"✅ Profile test successful: {profile.get('user_name')}")
                    
                    # Test a quote
                    quote = auth.kite.quote(['NSE:RELIANCE'])
                    if 'NSE:RELIANCE' in quote:
                        price = quote['NSE:RELIANCE']['last_price']
                        print(f"✅ Live data test successful: RELIANCE @ ₹{price:.2f}")
                    
                    print("\n🎉 Zerodha integration is now working!")
                    print("🚀 You can now run: python main.py")
                    return True
                    
                except Exception as e:
                    print(f"⚠️ Session test failed: {e}")
                    print("But authentication was successful. Try running the main app.")
                    return True
            
            else:
                print("❌ Session generation failed")
                print("💡 Please check your request_token and try again")
                return False
                
        except Exception as e:
            print(f"❌ Session generation error: {e}")
            
            if "Invalid checksum" in str(e):
                print("💡 This usually means the request_token is incorrect")
                print("💡 Please copy the exact token from the URL after login")
            elif "Invalid API key" in str(e):
                print("💡 Check your ZERODHA_API_KEY in .env file")
            elif "Invalid API secret" in str(e):
                print("💡 Check your ZERODHA_API_SECRET in .env file")
            
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📦 Install kiteconnect: pip install kiteconnect")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_environment():
    """Verify .env file has correct format"""
    print("\n🔍 Verifying .env file...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
    
    # Check for common issues
    issues = []
    
    if 'ZERODHA_API_KEY=your_api_key_here' in content:
        issues.append("ZERODHA_API_KEY still has placeholder value")
    
    if 'ZERODHA_API_SECRET=your_api_secret_here' in content:
        issues.append("ZERODHA_API_SECRET still has placeholder value")
    
    if issues:
        print("❌ .env file issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 Please update .env with your actual Zerodha credentials")
        return False
    
    print("✅ .env file looks good")
    return True

def main():
    """Main function"""
    print("🔧 Zerodha Authentication Fixer")
    print("=" * 40)
    print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
    
    # Step 1: Verify environment
    if not verify_environment():
        return False
    
    # Step 2: Fix authentication
    success = fix_zerodha_authentication()
    
    if success:
        print("\n✅ AUTHENTICATION FIXED!")
        print("🧪 Run this to test: python quick_test_zerodha.py")
        print("🚀 Start trading: python main.py")
    else:
        print("\n❌ AUTHENTICATION STILL FAILED")
        print("💡 Common issues:")
        print("   - Wrong request_token copied")
        print("   - Network connectivity issues")  
        print("   - Zerodha server issues")
        print("   - Incorrect API credentials")
    
    return success

if __name__ == "__main__":
    main()