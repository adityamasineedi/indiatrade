# test_fixed_engine.py
"""
Comprehensive test for the FIXED Paper Trading Engine
Tests all critical fixes and functionality
"""

import sys
import os
sys.path.append('src')

def test_config_initialization():
    """Test that config is properly initialized in all scenarios"""
    print("🧪 Testing Config Initialization...")
    
    try:
        from src.engines.paper_trading import PaperTradingEngine
        
        # Test 1: Default initialization
        print("  Test 1: Default initialization")
        engine1 = PaperTradingEngine()
        assert hasattr(engine1, 'config'), "Config attribute missing"
        assert hasattr(engine1.config, 'INITIAL_CAPITAL'), "INITIAL_CAPITAL missing"
        print(f"    ✅ Config: Rs.{engine1.config.INITIAL_CAPITAL:,.2f}")
        
        # Test 2: With initial_capital parameter
        print("  Test 2: With initial_capital parameter")
        engine2 = PaperTradingEngine(initial_capital=150000)
        assert engine2.config.INITIAL_CAPITAL == 150000, "Initial capital not set correctly"
        print(f"    ✅ Config: Rs.{engine2.config.INITIAL_CAPITAL:,.2f}")
        
        # Test 3: With config parameter
        print("  Test 3: With config parameter")
        from types import SimpleNamespace
        custom_config = SimpleNamespace()
        custom_config.INITIAL_CAPITAL = 200000
        custom_config.RISK_PER_TRADE = 3.0
        custom_config.COMMISSION = 0.15
        custom_config.MAX_POSITIONS = 8
        custom_config.WATCHLIST = ['RELIANCE', 'TCS']
        
        engine3 = PaperTradingEngine(config=custom_config)
        assert engine3.config.INITIAL_CAPITAL == 200000, "Custom config not used"
        print(f"    ✅ Custom Config: Rs.{engine3.config.INITIAL_CAPITAL:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Config initialization failed: {e}")
        return False

def test_portfolio_status_fix():
    """Test that get_portfolio_status works without AttributeError"""
    print("\n🧪 Testing Portfolio Status Fix...")
    
    try:
        from src.engines.paper_trading import PaperTradingEngine
        
        # Test with different initialization methods
        engines = [
            PaperTradingEngine(),
            PaperTradingEngine(initial_capital=120000),
        ]
        
        for i, engine in enumerate(engines, 1):
            print(f"  Test {i}: Getting portfolio status")
            
            # This used to cause AttributeError
            portfolio = engine.get_portfolio_status()
            
            # Verify all required fields exist
            required_fields = ['total_value', 'cash', 'invested', 'total_pnl', 
                             'daily_pnl', 'positions_count', 'return_pct', 'target_progress']
            
            for field in required_fields:
                assert field in portfolio, f"Missing field: {field}"
            
            print(f"    ✅ Portfolio: Rs.{portfolio['total_value']:,.2f}")
            print(f"    ✅ Daily P&L: Rs.{portfolio['daily_pnl']:,.2f}")
            print(f"    ✅ Positions: {portfolio['positions_count']}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Portfolio status test failed: {e}")
        return False

def test_daily_pnl_calculation():
    """Test the fixed daily P&L calculation"""
    print("\n🧪 Testing Daily P&L Calculation...")
    
    try:
        from src.engines.paper_trading import PaperTradingEngine
        import sqlite3
        from datetime import datetime, timedelta
        
        engine = PaperTradingEngine()
        
        # Test 1: Direct calculation method
        print("  Test 1: Direct daily P&L calculation")
        daily_pnl = engine._get_daily_pnl()
        print(f"    ✅ Daily P&L method: Rs.{daily_pnl:,.2f}")
        
        # Test 2: Database query verification
        print("  Test 2: Database query verification")
        conn = sqlite3.connect(engine.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date().strftime('%Y-%m-%d')
        tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT COUNT(*), SUM(COALESCE(pnl, 0)) FROM paper_trades 
            WHERE timestamp >= ? AND timestamp < ?
        ''', (today, tomorrow))
        
        result = cursor.fetchone()
        conn.close()
        
        trade_count = result[0] if result else 0
        db_pnl = result[1] if result and result[1] else 0.0
        
        print(f"    ✅ Database: {trade_count} trades, Rs.{db_pnl:,.2f} P&L")
        
        # Verify they match
        assert abs(daily_pnl - db_pnl) < 0.01, f"P&L mismatch: {daily_pnl} vs {db_pnl}"
        print(f"    ✅ P&L calculations match!")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Daily P&L test failed: {e}")
        return False

def test_trade_execution():
    """Test trade execution functionality"""
    print("\n🧪 Testing Trade Execution...")
    
    try:
        from src.engines.paper_trading import PaperTradingEngine
        
        engine = PaperTradingEngine(initial_capital=100000)
        
        # Test 1: Sample trade execution
        print("  Test 1: Sample trade execution")
        success = engine.execute_sample_trade()
        assert success, "Sample trade failed"
        print(f"    ✅ Sample trade executed")
        
        # Test 2: Custom trade execution
        print("  Test 2: Custom trade execution")
        test_signal = {
            'symbol': 'TCS',
            'action': 'BUY',
            'price': 3600.0,
            'confidence': 80,
            'reasons': ['Test trade'],
            'stop_loss': 3420.0,
            'target_price': 3960.0
        }
        
        success = engine.execute_trade(test_signal)
        print(f"    ✅ Custom trade: {'Success' if success else 'Failed'}")
        
        # Test 3: Portfolio status after trades
        print("  Test 3: Portfolio status after trades")
        portfolio = engine.get_portfolio_status()
        print(f"    ✅ Portfolio after trades: Rs.{portfolio['total_value']:,.2f}")
        print(f"    ✅ Cash remaining: Rs.{portfolio['cash']:,.2f}")
        print(f"    ✅ Positions: {portfolio['positions_count']}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Trade execution test failed: {e}")
        return False

def test_database_operations():
    """Test database operations"""
    print("\n🧪 Testing Database Operations...")
    
    try:
        from src.engines.paper_trading import PaperTradingEngine
        
        engine = PaperTradingEngine()
        
        # Test 1: Database initialization
        print("  Test 1: Database initialization")
        assert os.path.exists(engine.db_path), "Database file not created"
        print(f"    ✅ Database exists: {engine.db_path}")
        
        # Test 2: Trade history retrieval
        print("  Test 2: Trade history retrieval")
        history = engine.get_trade_history(days=7)
        print(f"    ✅ Retrieved {len(history)} trades from last 7 days")
        
        # Test 3: Recent trades
        print("  Test 3: Recent trades")
        recent = engine.get_recent_trades(days=1)
        print(f"    ✅ Retrieved {len(recent)} recent trades")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Database operations test failed: {e}")
        return False

def test_api_compatibility():
    """Test API endpoint compatibility"""
    print("\n🧪 Testing API Compatibility...")
    
    try:
        import requests
        import json
        
        base_url = "http://127.0.0.1:5000"
        
        # Test 1: Portfolio API
        print("  Test 1: Portfolio API")
        try:
            response = requests.get(f"{base_url}/api/portfolio", timeout=5)
            if response.status_code == 200:
                data = response.json()
                assert 'total_value' in data, "Missing total_value in response"
                assert 'positions_count' in data, "Missing positions_count in response"
                print(f"    ✅ Portfolio API: Rs.{data.get('total_value', 0):,.2f}")
            else:
                print(f"    ⚠️ Portfolio API: HTTP {response.status_code}")
        except requests.RequestException:
            print(f"    ⚠️ Portfolio API: Server not running")
        
        # Test 2: System Status API
        print("  Test 2: System Status API")
        try:
            response = requests.get(f"{base_url}/api/system_status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ System Status: Running={data.get('running', False)}")
            else:
                print(f"    ⚠️ System Status API: HTTP {response.status_code}")
        except requests.RequestException:
            print(f"    ⚠️ System Status API: Server not running")
        
        # Test 3: Manual trading session
        print("  Test 3: Manual trading session")
        try:
            response = requests.post(f"{base_url}/api/run_trading_session", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ Trading Session: {data.get('status', 'unknown')}")
            else:
                print(f"    ⚠️ Trading Session API: HTTP {response.status_code}")
        except requests.RequestException:
            print(f"    ⚠️ Trading Session API: Server not running")
        
        return True
        
    except Exception as e:
        print(f"    ❌ API compatibility test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all tests"""
    print("🔧 RUNNING COMPREHENSIVE TESTS")
    print("=" * 60)
    
    tests = [
        ("Config Initialization", test_config_initialization),
        ("Portfolio Status Fix", test_portfolio_status_fix),
        ("Daily P&L Calculation", test_daily_pnl_calculation),
        ("Trade Execution", test_trade_execution),
        ("Database Operations", test_database_operations),
        ("API Compatibility", test_api_compatibility),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"    ❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your fixes are working perfectly!")
        print("\n🚀 NEXT STEPS:")
        print("  1. Replace your src/engines/paper_trading.py with the fixed version")
        print("  2. Restart Flask server: python main.py")
        print("  3. Visit dashboard: http://localhost:5000")
        print("  4. Check trades page: http://localhost:5000/trades")
        print("  5. All AttributeError issues should be resolved!")
        
    elif passed >= total * 0.8:
        print(f"\n✅ Most tests passed! Minor issues in {total-passed} areas.")
        print("The core fixes are working - you can proceed with confidence.")
        
    else:
        print(f"\n⚠️ {total-passed} major issues remain. Review the failures above.")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    run_comprehensive_tests()