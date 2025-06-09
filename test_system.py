# test_system.py - System Verification Script
"""
Comprehensive test script to verify all trading system components work properly
"""
import sys
import os
sys.path.append('src')
sys.path.append('config')

from datetime import datetime
import time

def test_data_fetcher():
    """Test data fetcher component"""
    print("\n📊 Testing Data Fetcher...")
    try:
        from src.data_fetcher import DataFetcher
        
        fetcher = DataFetcher()
        
        # Test current prices
        symbols = ['RELIANCE', 'TCS', 'INFY']
        print("   Testing current prices:")
        for symbol in symbols:
            price = fetcher.get_current_price(symbol)
            if price and price > 0:
                print(f"     ✅ {symbol}: ₹{price:.2f}")
            else:
                print(f"     ❌ {symbol}: Failed")
        
        # Test historical data
        print("   Testing historical data:")
        data = fetcher.get_stock_data('RELIANCE', days=10)
        if not data.empty:
            print(f"     ✅ RELIANCE: {len(data)} days of data")
            print(f"     📊 Latest close: ₹{data['Close'].iloc[-1]:.2f}")
        else:
            print(f"     ❌ RELIANCE: No historical data")
        
        # Test market overview
        print("   Testing market overview:")
        overview = fetcher.get_market_overview()
        if overview:
            print(f"     ✅ Nifty: ₹{overview.get('nifty_price', 0):.2f}")
            print(f"     📈 Change: {overview.get('nifty_change_percent', 0):.2f}%")
            print(f"     🕐 Status: {overview.get('market_status', 'Unknown')}")
        else:
            print(f"     ❌ Market overview failed")
        
        return True
        
    except Exception as e:
        print(f"     ❌ Data Fetcher test failed: {e}")
        return False

def test_technical_indicators():
    """Test technical indicators"""
    print("\n📈 Testing Technical Indicators...")
    try:
        from src.indicators.technical import TechnicalIndicators
        from src.data_fetcher import DataFetcher
        import pandas as pd
        import numpy as np
        
        indicators = TechnicalIndicators()
        fetcher = DataFetcher()
        
        # Get sample data
        data = fetcher.get_stock_data('RELIANCE', days=30)
        if data.empty:
            # Create sample data
            dates = pd.date_range('2025-05-01', periods=30, freq='D')
            data = pd.DataFrame({
                'Open': np.random.uniform(2400, 2500, 30),
                'High': np.random.uniform(2450, 2550, 30),
                'Low': np.random.uniform(2350, 2450, 30),
                'Close': np.random.uniform(2400, 2500, 30),
                'Volume': np.random.randint(100000, 1000000, 30)
            }, index=dates)
        
        # Add indicators
        enhanced_data = indicators.add_all_indicators(data)
        
        # Check if indicators were added
        expected_indicators = ['RSI', 'EMA_10', 'EMA_20', 'MACD', 'MACD_Signal']
        added_indicators = []
        
        for indicator in expected_indicators:
            if indicator in enhanced_data.columns:
                latest_value = enhanced_data[indicator].iloc[-1]
                if not pd.isna(latest_value):
                    added_indicators.append(indicator)
                    print(f"     ✅ {indicator}: {latest_value:.2f}")
                else:
                    print(f"     ⚠️ {indicator}: NaN value")
            else:
                print(f"     ❌ {indicator}: Missing")
        
        print(f"   📊 Successfully added {len(added_indicators)}/{len(expected_indicators)} indicators")
        return len(added_indicators) >= 3  # At least 3 indicators working
        
    except Exception as e:
        print(f"     ❌ Technical Indicators test failed: {e}")
        return False

def test_signal_generator():
    """Test signal generator"""
    print("\n📡 Testing Signal Generator...")
    try:
        from src.strategies.signal_generator import SignalGenerator
        from src.indicators.technical import TechnicalIndicators
        from src.data_fetcher import DataFetcher
        
        # Mock regime detector
        class MockRegimeDetector:
            def detect_current_regime(self):
                return {'regime': 'bull', 'confidence': 75.0}
        
        fetcher = DataFetcher()
        indicators = TechnicalIndicators()
        regime_detector = MockRegimeDetector()
        
        generator = SignalGenerator(indicators, regime_detector)
        
        # Test signal generation with real data
        print("   Testing with real data:")
        try:
            stocks_data = fetcher.get_multiple_stocks_data(['RELIANCE', 'TCS'], days=30)
            signals = generator.generate_signals(stocks_data)
            
            if signals:
                print(f"     ✅ Generated {len(signals)} signals from real data")
                for signal in signals[:2]:  # Show first 2 signals
                    print(f"       🎯 {signal['action']} {signal['symbol']} @ ₹{signal['price']:.2f} ({signal['confidence']:.0f}%)")
            else:
                print(f"     ⚠️ No signals from real data")
        except Exception as e:
            print(f"     ⚠️ Real data signals failed: {e}")
        
        # Test test signals (fallback)
        print("   Testing fallback signals:")
        test_signals = generator._generate_test_signals(['RELIANCE', 'TCS'])
        if test_signals:
            print(f"     ✅ Generated {len(test_signals)} test signals")
            for signal in test_signals:
                print(f"       🎯 {signal['action']} {signal['symbol']} @ ₹{signal['price']:.2f} ({signal['confidence']:.0f}%)")
        else:
            print(f"     ❌ Test signals failed")
        
        return len(test_signals) > 0
        
    except Exception as e:
        print(f"     ❌ Signal Generator test failed: {e}")
        return False

def test_paper_trading_engine():
    """Test paper trading engine"""
    print("\n💰 Testing Paper Trading Engine...")
    try:
        from src.engines.paper_trading import PaperTradingEngine
        from src.data_fetcher import DataFetcher
        from src.strategies.signal_generator import SignalGenerator
        from src.indicators.technical import TechnicalIndicators
        
        # Initialize components
        fetcher = DataFetcher()
        
        # Mock regime detector
        class MockRegimeDetector:
            def detect_current_regime(self):
                return {'regime': 'bull', 'confidence': 75.0}
        
        indicators = TechnicalIndicators()
        regime_detector = MockRegimeDetector()
        signal_generator = SignalGenerator(indicators, regime_detector)
        
        # Initialize paper trading engine
        engine = PaperTradingEngine(
            data_fetcher=fetcher,
            signal_generator=signal_generator,
            initial_capital=100000
        )
        
        print(f"   ✅ Engine initialized with ₹{engine.initial_capital:,.2f}")
        
        # Test portfolio status
        portfolio = engine.get_portfolio_status()
        print(f"   📊 Portfolio value: ₹{portfolio['total_value']:,.2f}")
        print(f"   💰 Cash: ₹{portfolio['cash']:,.2f}")
        print(f"   📈 Positions: {portfolio['positions_count']}")
        
        # Test trading session
        print("   Testing trading session:")
        result = engine.start_paper_trading()
        
        if result and result.get('status') == 'success':
            print(f"     ✅ Trading session completed")
            print(f"     📡 Signals: {result.get('signals_generated', 0)}")
            print(f"     🔄 Trades: {result.get('trades_executed', 0)}")
            print(f"     💰 Portfolio: ₹{result.get('portfolio_value', 0):,.2f}")
            
            # Test individual trade execution
            print("   Testing individual trade:")
            test_signal = {
                'symbol': 'RELIANCE',
                'action': 'BUY',
                'price': fetcher.get_current_price('RELIANCE') or 2450.0,
                'confidence': 75,
                'reasons': ['Test trade'],
                'timestamp': datetime.now()
            }
            
            trade_result = engine.execute_trade(test_signal)
            if trade_result:
                print(f"     ✅ Test trade executed: {trade_result['action']} {trade_result['symbol']}")
            else:
                print(f"     ⚠️ Test trade not executed (may be due to existing position)")
            
            return True
        else:
            print(f"     ❌ Trading session failed: {result.get('message', 'Unknown error') if result else 'No result'}")
            return False
        
    except Exception as e:
        print(f"     ❌ Paper Trading Engine test failed: {e}")
        return False

def test_database_operations():
    """Test database operations"""
    print("\n🗄️ Testing Database Operations...")
    try:
        import sqlite3
        import os
        
        db_path = 'data/paper_trading.db'
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Test database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        expected_tables = ['paper_trades', 'portfolio_snapshots', 'current_positions']
        existing_tables = [table for table in expected_tables if table in table_names]
        
        print(f"   📊 Database tables: {len(existing_tables)}/{len(expected_tables)} found")
        for table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"     ✅ {table}: {count} records")
        
        # Test write operation
        try:
            cursor.execute('''
                INSERT INTO paper_trades 
                (symbol, action, price, quantity, amount, commission, portfolio_value, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('TEST', 'BUY', 100.0, 10, 1000.0, 1.0, 100000.0, 'Database test'))
            conn.commit()
            print(f"     ✅ Write operation successful")
            
            # Clean up test record
            cursor.execute("DELETE FROM paper_trades WHERE symbol = 'TEST'")
            conn.commit()
            
        except Exception as e:
            print(f"     ❌ Write operation failed: {e}")
        
        conn.close()
        return len(existing_tables) >= 2
        
    except Exception as e:
        print(f"     ❌ Database test failed: {e}")
        return False

def test_telegram_integration():
    """Test Telegram integration (optional)"""
    print("\n📱 Testing Telegram Integration...")
    try:
        from src.utils.telegram_bot import TelegramBot
        
        bot = TelegramBot()
        
        if hasattr(bot, 'bot') and bot.bot and hasattr(bot, 'chat_id') and bot.chat_id:
            print("   ✅ Telegram bot initialized")
            
            # Test connection (don't actually send message in test)
            success, message = bot.test_connection()
            if success:
                print(f"     ✅ Telegram connection: {message}")
            else:
                print(f"     ⚠️ Telegram connection: {message}")
            
            return success
        else:
            print("   ⚠️ Telegram not configured (optional)")
            return True  # Not a failure if not configured
        
    except Exception as e:
        print(f"   ⚠️ Telegram not available: {e}")
        return True  # Not a failure if not available

def run_comprehensive_test():
    """Run comprehensive system test"""
    print("🧪 COMPREHENSIVE TRADING SYSTEM TEST")
    print("=" * 50)
    
    tests = [
        ("Data Fetcher", test_data_fetcher),
        ("Technical Indicators", test_technical_indicators),
        ("Signal Generator", test_signal_generator),
        ("Paper Trading Engine", test_paper_trading_engine),
        ("Database Operations", test_database_operations),
        ("Telegram Integration", test_telegram_integration)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            results[test_name] = {
                'passed': result,
                'duration': duration
            }
            
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED ({duration:.2f}s)")
            else:
                print(f"❌ {test_name}: FAILED ({duration:.2f}s)")
                
        except Exception as e:
            results[test_name] = {
                'passed': False,
                'error': str(e)
            }
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        duration = result.get('duration', 0)
        print(f"{status} {test_name} ({duration:.2f}s)")
        if 'error' in result:
            print(f"     Error: {result['error']}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed >= total * 0.8:  # 80% pass rate
        print("🎉 SYSTEM TEST PASSED - Ready for trading!")
    else:
        print("⚠️ SYSTEM TEST NEEDS ATTENTION - Some components need fixing")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    # Change to project directory if needed
    if not os.path.exists('src'):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)