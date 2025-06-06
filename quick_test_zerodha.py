# quick_test_zerodha.py
"""
Quick test script to verify Zerodha integration is working
Run this after setting up your integration
"""
import os
import sys
import time
from datetime import datetime

# Add paths
sys.path.append('src')
sys.path.append('config')

def test_imports():
    """Test if all required packages are available"""
    print("📦 Testing imports...")
    try:
        import kiteconnect
        print("  ✅ kiteconnect")
        
        import pandas
        print("  ✅ pandas")
        
        from config.zerodha.auth import ZerodhaAuth
        print("  ✅ ZerodhaAuth")
        
        from config.zerodha.instruments import ZerodhaInstruments
        print("  ✅ ZerodhaInstruments")
        
        from config.zerodha.rate_limiter import zerodha_rate_limiter
        print("  ✅ RateLimiter")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n⚙️ Testing environment...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['ZERODHA_API_KEY', 'ZERODHA_API_SECRET']
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or 'your_' in value:
            missing.append(var)
            print(f"  ❌ {var}: Not configured")
        else:
            print(f"  ✅ {var}: Configured")
    
    if missing:
        print(f"\n  ⚠️ Configure these in .env file: {', '.join(missing)}")
        return False
    
    return True

def test_authentication():
    """Test Zerodha authentication"""
    print("\n🔐 Testing authentication...")
    
    try:
        from config.zerodha.auth import ZerodhaAuth
        
        auth = ZerodhaAuth()
        if auth.authenticate():
            print("  ✅ Authentication successful")
            
            # Test profile
            try:
                profile = auth.kite.profile()
                print(f"  ✅ Profile: {profile.get('user_name')} ({profile.get('user_id')})")
                return True, auth
            except Exception as e:
                print(f"  ⚠️ Profile fetch failed: {e}")
                return True, auth  # Auth worked but profile failed
        else:
            print("  ❌ Authentication failed")
            print("  💡 Run: python setup_zerodha.py")
            return False, None
            
    except Exception as e:
        print(f"  ❌ Auth error: {e}")
        return False, None

def test_instruments(auth):
    """Test instruments functionality"""
    print("\n📊 Testing instruments...")
    
    try:
        from config.zerodha.instruments import ZerodhaInstruments
        
        instruments = ZerodhaInstruments(auth.kite)
        
        # Test symbol lookup
        reliance_token = instruments.get_instrument_token('RELIANCE')
        if reliance_token:
            print(f"  ✅ RELIANCE token: {reliance_token}")
        else:
            print("  ⚠️ RELIANCE token not found, downloading instruments...")
            if instruments.download_instruments():
                reliance_token = instruments.get_instrument_token('RELIANCE')
                if reliance_token:
                    print(f"  ✅ RELIANCE token after download: {reliance_token}")
                else:
                    print("  ❌ RELIANCE token still not found")
                    return False
        
        # Test search
        results = instruments.search_symbols('RELI')
        if results:
            print(f"  ✅ Search 'RELI': Found {len(results)} results")
        else:
            print("  ⚠️ Search returned no results")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Instruments error: {e}")
        return False

def test_live_data(auth):
    """Test live data fetching"""
    print("\n💎 Testing live data...")
    
    try:
        from config.zerodha.rate_limiter import zerodha_rate_limiter
        
        test_symbols = ['RELIANCE', 'TCS', 'INFY']
        success_count = 0
        
        for symbol in test_symbols:
            try:
                # Rate limiting
                zerodha_rate_limiter.wait_if_needed()
                zerodha_rate_limiter.record_call()
                
                # Fetch quote
                quote = auth.kite.quote([f"NSE:{symbol}"])
                
                if f"NSE:{symbol}" in quote:
                    data = quote[f"NSE:{symbol}"]
                    price = data['last_price']
                    change = data.get('net_change', 0)
                    volume = data.get('volume', 0)
                    
                    print(f"  ✅ {symbol}: ₹{price:.2f} ({change:+.2f}) Vol: {volume:,}")
                    success_count += 1
                else:
                    print(f"  ❌ {symbol}: No data in response")
                    
            except Exception as e:
                print(f"  ❌ {symbol}: {e}")
        
        if success_count > 0:
            print(f"  ✅ Live data: {success_count}/{len(test_symbols)} symbols successful")
            return True
        else:
            print("  ❌ No live data retrieved")
            return False
            
    except Exception as e:
        print(f"  ❌ Live data error: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n⚡ Testing rate limiting...")
    
    try:
        from config.zerodha.rate_limiter import zerodha_rate_limiter
        
        # Get initial stats
        stats = zerodha_rate_limiter.get_stats()
        print(f"  📊 Initial: {stats['calls_last_second']}/{stats['second_limit']} per second")
        print(f"  📊 Initial: {stats['calls_last_minute']}/{stats['minute_limit']} per minute")
        
        # Test multiple calls
        for i in range(5):
            zerodha_rate_limiter.wait_if_needed()
            zerodha_rate_limiter.record_call()
            time.sleep(0.1)
        
        stats = zerodha_rate_limiter.get_stats()
        print(f"  ✅ After 5 calls: {stats['calls_last_second']}/{stats['second_limit']} per second")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Rate limiting error: {e}")
        return False

def test_enhanced_data_fetcher():
    """Test enhanced data fetcher"""
    print("\n🔄 Testing enhanced data fetcher...")
    
    try:
        from src.data_fetcher import DataFetcher
        from config.zerodha.auth import ZerodhaAuth
        from config.zerodha.instruments import ZerodhaInstruments
        
        # Regular data fetcher
        regular_fetcher = DataFetcher()
        regular_data = regular_fetcher.get_stock_data('RELIANCE', days=5)
        
        if not regular_data.empty:
            print(f"  ✅ Regular fetcher: {len(regular_data)} days")
        else:
            print("  ⚠️ Regular fetcher: No data")
        
        # Enhanced with Zerodha
        auth = ZerodhaAuth()
        if auth.authenticate():
            instruments = ZerodhaInstruments(auth.kite)
            
            # Test current price
            price = regular_fetcher.get_current_price('RELIANCE')
            if price:
                print(f"  ✅ Current price: ₹{price:.2f}")
            else:
                print("  ⚠️ Current price: Not available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced data fetcher error: {e}")
        return False

def test_configuration():
    """Test enhanced configuration"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from config.settings import Config
        
        # Test trading mode
        mode = Config.get_trading_mode()
        print(f"  ✅ Trading mode: {mode}")
        
        # Test market status
        market_status = Config.get_market_status()
        print(f"  ✅ Market status: {market_status['status']} ({market_status['session']})")
        
        # Test validation
        try:
            Config.validate_config()
            print("  ✅ Configuration validation passed")
        except Exception as e:
            print(f"  ⚠️ Configuration validation: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Quick Zerodha Integration Test")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Test 1: Imports
    results['imports'] = test_imports()
    
    # Test 2: Environment
    results['environment'] = test_environment()
    
    if not results['environment']:
        print("\n❌ Environment test failed. Please configure .env file.")
        return False
    
    # Test 3: Authentication
    auth_success, auth = test_authentication()
    results['authentication'] = auth_success
    
    if not auth_success:
        print("\n❌ Authentication failed. Cannot proceed with API tests.")
        print("💡 Run: python setup_zerodha.py")
        return False
    
    # Test 4: Instruments
    results['instruments'] = test_instruments(auth)
    
    # Test 5: Live Data
    results['live_data'] = test_live_data(auth)
    
    # Test 6: Rate Limiting
    results['rate_limiting'] = test_rate_limiting()
    
    # Test 7: Enhanced Data Fetcher
    results['enhanced_fetcher'] = test_enhanced_data_fetcher()
    
    # Test 8: Configuration
    results['configuration'] = test_configuration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n📈 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Your Zerodha integration is ready!")
        print("💡 You can now run: python main.py")
    elif passed_tests >= total_tests * 0.75:
        print("\n✅ Most tests passed - integration mostly working!")
        print("⚠️ Check failed tests above for issues")
    else:
        print("\n❌ Several tests failed - please check your setup")
        print("💡 Try running: python setup_zerodha.py")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return passed_tests == total_tests

if __name__ == "__main__":
    main()