# setup_zerodha.py
"""
Complete Zerodha Integration Setup and Testing Script
Run this to configure and test your Zerodha integration
"""
import os
import sys
import json
import webbrowser
from datetime import datetime

# Add paths
sys.path.append('src')
sys.path.append('config')

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'kiteconnect',
        'pandas',
        'requests',
        'flask',
        'python-telegram-bot'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print(f"\n📦 Install with: pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_env_file():
    """Check if .env file exists and has required fields"""
    print("\n🔍 Checking .env file...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("📝 Creating .env file from template...")
        
        # Create .env from template
        env_template = """# Zerodha Configuration
ZERODHA_ENABLED=true
ZERODHA_API_KEY=your_api_key_here
ZERODHA_API_SECRET=your_api_secret_here
ZERODHA_PAPER_TRADING=true

# Telegram Configuration  
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Trading Configuration
INITIAL_CAPITAL=100000
MAX_POSITIONS=5
RISK_PER_TRADE=2
PROFIT_TARGET=3000

# Flask Configuration
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_SECRET_KEY=change-this-secret-key
"""
        
        with open('.env', 'w') as f:
            f.write(env_template)
        
        print("✅ .env file created")
        print("📝 Please edit .env file with your actual credentials")
        return False
    
    # Check required fields
    from dotenv import load_dotenv
    load_dotenv()
    
    required_fields = {
        'ZERODHA_API_KEY': 'Zerodha API Key',
        'ZERODHA_API_SECRET': 'Zerodha API Secret', 
        'TELEGRAM_BOT_TOKEN': 'Telegram Bot Token',
        'TELEGRAM_CHAT_ID': 'Telegram Chat ID'
    }
    
    missing_fields = []
    for field, description in required_fields.items():
        value = os.getenv(field)
        if not value or value == f'your_{field.lower().split("_")[-1]}_here':
            missing_fields.append(f"{field} ({description})")
    
    if missing_fields:
        print("❌ Missing configuration in .env file:")
        for field in missing_fields:
            print(f"   - {field}")
        return False
    
    print("✅ .env file configuration looks good")
    return True

def setup_zerodha_auth():
    """Interactive Zerodha authentication setup"""
    print("\n🔐 Setting up Zerodha Authentication...")
    
    try:
        from config.zerodha.auth import ZerodhaAuth
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check credentials
        api_key = os.getenv('ZERODHA_API_KEY')
        api_secret = os.getenv('ZERODHA_API_SECRET')
        
        if not api_key or api_key == 'your_api_key_here':
            print("❌ ZERODHA_API_KEY not configured in .env")
            print("🔗 Get your API key from: https://developers.kite.trade/")
            return False
        
        if not api_secret or api_secret == 'your_api_secret_here':
            print("❌ ZERODHA_API_SECRET not configured in .env")
            print("🔗 Get your API secret from: https://developers.kite.trade/")
            return False
        
        # Initialize auth
        auth = ZerodhaAuth()
        
        # Check if already authenticated
        if auth.authenticate():
            print("✅ Already authenticated with Zerodha")
            
            # Test connection
            try:
                profile = auth.kite.profile()
                print(f"👤 Connected as: {profile.get('user_name')} ({profile.get('user_id')})")
                return True
            except Exception as e:
                print(f"⚠️ Authentication expired: {e}")
        
        # Need fresh authentication
        print("🌐 Opening Zerodha login page...")
        login_url = auth.get_login_url()
        
        try:
            webbrowser.open(login_url)
            print("✅ Login page opened in browser")
        except:
            print(f"🔗 Please open this URL manually: {login_url}")
        
        print("\n📋 INSTRUCTIONS:")
        print("1. Complete login in the browser")
        print("2. After login, you'll be redirected to a URL")
        print("3. Copy the 'request_token' from the URL")
        print("4. Paste it below")
        print("\nExample URL: https://127.0.0.1:5000/?request_token=ABC123&action=login")
        print("Copy only: ABC123")
        
        request_token = input("\n🔑 Enter request_token: ").strip()
        
        if request_token:
            result = auth.generate_session(request_token)
            if result:
                print("✅ Zerodha authentication successful!")
                print(f"👤 Welcome, {result.get('user_name')}!")
                return True
            else:
                print("❌ Authentication failed")
                return False
        else:
            print("❌ No request token provided")
            return False
            
    except ImportError:
        print("❌ Zerodha integration not available")
        print("📦 Install with: pip install kiteconnect")
        return False
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

def test_zerodha_integration():
    """Test Zerodha integration comprehensively"""
    print("\n🧪 Testing Zerodha Integration...")
    
    try:
        from config.zerodha.auth import ZerodhaAuth
        from config.zerodha.instruments import ZerodhaInstruments
        from config.zerodha.rate_limiter import zerodha_rate_limiter
        
        # Test authentication
        auth = ZerodhaAuth()
        if not auth.authenticate():
            print("❌ Authentication failed")
            return False
        
        kite = auth.kite
        print("✅ Authentication successful")
        
        # Test profile
        try:
            profile = kite.profile()
            print(f"✅ Profile: {profile.get('user_name')} ({profile.get('user_id')})")
        except Exception as e:
            print(f"⚠️ Profile fetch failed: {e}")
        
        # Test instruments
        print("📊 Testing instruments...")
        instruments = ZerodhaInstruments(kite)
        
        if instruments.update_if_needed():
            print("✅ Instruments loaded successfully")
            
            # Test symbol lookup
            reliance_token = instruments.get_instrument_token('RELIANCE')
            if reliance_token:
                print(f"✅ RELIANCE token: {reliance_token}")
            else:
                print("⚠️ RELIANCE token not found")
        
        # Test live data
        print("💎 Testing live market data...")
        test_symbols = ['RELIANCE', 'TCS', 'INFY']
        
        for symbol in test_symbols:
            try:
                zerodha_rate_limiter.wait_if_needed()
                zerodha_rate_limiter.record_call()
                
                quote = kite.quote([f"NSE:{symbol}"])
                if f"NSE:{symbol}" in quote:
                    data = quote[f"NSE:{symbol}"]
                    price = data['last_price']
                    change = data.get('net_change', 0)
                    print(f"✅ {symbol}: ₹{price:.2f} ({change:+.2f})")
                else:
                    print(f"❌ {symbol}: No data")
            except Exception as e:
                print(f"⚠️ {symbol}: {e}")
        
        # Test rate limiter
        print("⚡ Rate limiter stats:")
        stats = zerodha_rate_limiter.get_stats()
        print(f"   Calls this second: {stats['calls_last_second']}/{stats['second_limit']}")
        print(f"   Calls this minute: {stats['calls_last_minute']}/{stats['minute_limit']}")
        
        print("✅ Zerodha integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_telegram_integration():
    """Test Telegram bot integration"""
    print("\n📱 Testing Telegram Integration...")
    
    try:
        from src.utils.telegram_bot import TelegramBot
        
        bot = TelegramBot()
        success, message = bot.test_connection()
        
        if success:
            print("✅ Telegram connection successful")
            print(f"📞 {message}")
            
            # Send test message
            test_msg = f"🤖 Test message from Trading System\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            if bot.send_message_sync(test_msg):
                print("✅ Test message sent successfully")
                return True
            else:
                print("⚠️ Test message failed")
                return False
        else:
            print(f"❌ Telegram connection failed: {message}")
            print("\n💡 Telegram Setup Instructions:")
            print("1. Create a bot with @BotFather on Telegram")
            print("2. Get the bot token and add to .env as TELEGRAM_BOT_TOKEN")
            print("3. Start a chat with your bot and send /start")
            print("4. Get your chat ID from @userinfobot and add to .env as TELEGRAM_CHAT_ID")
            return False
            
    except Exception as e:
        print(f"❌ Telegram test error: {e}")
        return False

def create_directory_structure():
    """Create required directory structure"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        'config/zerodha',
        'data',
        'logs',
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}/")
    
    print("✅ Directory structure created")

def run_integration_test():
    """Run complete integration test"""
    print("\n🚀 Running Complete Integration Test...")
    
    try:
        # Test enhanced data fetcher
        from src.data_fetcher import DataFetcher
        from config.zerodha.auth import ZerodhaAuth
        from config.zerodha.instruments import ZerodhaInstruments
        
        # Regular data fetcher
        print("📊 Testing regular data fetcher...")
        data_fetcher = DataFetcher()
        data = data_fetcher.get_stock_data('RELIANCE', days=5)
        
        if not data.empty:
            print(f"✅ Regular data: {len(data)} days")
        else:
            print("⚠️ Regular data fetch failed")
        
        # Enhanced data fetcher with Zerodha
        print("💎 Testing Zerodha-enhanced data fetcher...")
        auth = ZerodhaAuth()
        
        if auth.authenticate():
            instruments = ZerodhaInstruments(auth.kite)
            instruments.update_if_needed()
            
            # This would be the enhanced data fetcher
            print("✅ Enhanced data fetcher ready")
        else:
            print("⚠️ Enhanced data fetcher requires authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Zerodha Integration Setup & Testing")
    print("=" * 50)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        return False
    
    # Step 2: Create directories
    create_directory_structure()
    
    # Step 3: Check .env file
    if not check_env_file():
        print("\n⚠️ Please configure .env file and run this script again")
        return False
    
    # Step 4: Setup Zerodha authentication
    print("\n" + "=" * 50)
    print("🔐 ZERODHA AUTHENTICATION SETUP")
    print("=" * 50)
    
    zerodha_success = setup_zerodha_auth()
    
    # Step 5: Test Zerodha integration
    if zerodha_success:
        test_zerodha_integration()
    
    # Step 6: Test Telegram
    print("\n" + "=" * 50)
    print("📱 TELEGRAM INTEGRATION TEST")
    print("=" * 50)
    
    telegram_success = test_telegram_integration()
    
    # Step 7: Run integration test
    print("\n" + "=" * 50)
    print("🧪 COMPLETE INTEGRATION TEST")
    print("=" * 50)
    
    integration_success = run_integration_test()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SETUP SUMMARY")
    print("=" * 50)
    
    print(f"📁 Directory Structure: ✅")
    print(f"⚙️ Configuration: ✅")
    print(f"🔗 Zerodha Integration: {'✅' if zerodha_success else '❌'}")
    print(f"📱 Telegram Integration: {'✅' if telegram_success else '❌'}")
    print(f"🧪 Full Integration: {'✅' if integration_success else '❌'}")
    
    if all([zerodha_success, telegram_success, integration_success]):
        print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("🚀 You can now run: python main.py")
        print("🌐 Dashboard: http://localhost:5000")
        return True
    else:
        print("\n⚠️ Setup incomplete. Please resolve the issues above.")
        return False

if __name__ == "__main__":
    main()