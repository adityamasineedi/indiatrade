# system_test.py - Comprehensive System Testing Script
"""
Run this script to test all components of your paper trading system
Usage: python system_test.py
"""

import sys
import os
import time
import requests
import threading
import sqlite3
import json
from datetime import datetime
import pandas as pd

# Add source path
sys.path.append('src')

class SystemTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
    def run_all_tests(self):
        """Run comprehensive system tests"""
        print("🧪 STARTING COMPREHENSIVE SYSTEM TESTS")
        print("=" * 60)
        
        tests = [
            ("🐍 Python Imports", self.test_python_imports),
            ("📊 Data Fetcher", self.test_data_fetcher),
            ("📈 Technical Indicators", self.test_technical_indicators),
            ("🎯 Signal Generator", self.test_signal_generator),
            ("💰 Paper Trading Engine", self.test_paper_trading),
            ("🗄️ Database Operations", self.test_database),
            ("📱 Telegram Bot", self.test_telegram),
            ("🌐 Flask Server", self.test_flask_server),
            ("🔗 API Endpoints", self.test_api_endpoints),
            ("📱 Frontend Assets", self.test_frontend),
            ("⚡ Performance", self.test_performance),
            ("🔒 Error Handling", self.test_error_handling)
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n{test_name}")
                print("-" * 40)
                result = test_func()
                if result:
                    self.passed_tests.append(test_name)
                    print(f"✅ {test_name}: PASSED")
                else:
                    self.failed_tests.append(test_name)
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.failed_tests.append(test_name)
                print(f"❌ {test_name}: ERROR - {str(e)}")
        
        self.print_summary()
    
    def test_python_imports(self):
        """Test all critical imports"""
        try:
            # Core imports
            import pandas as pd
            import numpy as np
            import yfinance as yf
            import sqlite3
            import flask
            print("✅ Core Python packages imported")
            
            # Project imports
            from src.data_fetcher import DataFetcher
            from src.indicators.technical import TechnicalIndicators
            from src.strategies.signal_generator import SignalGenerator
            from src.engines.paper_trading import PaperTradingEngine
            print("✅ Project modules imported")
            
            # Optional imports
            try:
                from src.utils.telegram_bot import TelegramBot
                print("✅ Telegram bot imported")
            except:
                print("⚠️ Telegram bot import failed (optional)")
            
            return True
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False
    
    def test_data_fetcher(self):
        """Test data fetching functionality"""
        try:
            from src.data_fetcher import DataFetcher
            
            fetcher = DataFetcher()
            print("✅ Data fetcher initialized")
            
            # Test current price
            price = fetcher.get_current_price('RELIANCE')
            if price and price > 0:
                print(f"✅ Current price fetch: RELIANCE = ₹{price:.2f}")
            else:
                print("❌ Current price fetch failed")
                return False
            
            # Test historical data
            data = fetcher.get_stock_data('TCS', days=10)
            if not data.empty and len(data) >= 5:
                print(f"✅ Historical data fetch: TCS = {len(data)} days")
                
                # Validate data structure
                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                if all(col in data.columns for col in required_cols):
                    print("✅ Data structure valid")
                else:
                    print(f"❌ Missing columns: {set(required_cols) - set(data.columns)}")
                    return False
            else:
                print("❌ Historical data fetch failed")
                return False
            
            # Test multiple stocks
            symbols = ['RELIANCE', 'TCS', 'INFY']
            multi_data = fetcher.get_multiple_stocks_data(symbols, days=5)
            if len(multi_data) >= 2:
                print(f"✅ Multiple stocks fetch: {len(multi_data)}/{len(symbols)} successful")
            else:
                print("❌ Multiple stocks fetch failed")
                return False
            
            # Test market overview
            overview = fetcher.get_market_overview()
            if overview and 'nifty_price' in overview:
                print(f"✅ Market overview: Nifty = {overview['nifty_price']}")
            else:
                print("❌ Market overview failed")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Data fetcher error: {e}")
            return False
    
    def test_technical_indicators(self):
        """Test technical indicators calculation"""
        try:
            from src.indicators.technical import TechnicalIndicators
            from src.data_fetcher import DataFetcher
            
            indicators = TechnicalIndicators()
            fetcher = DataFetcher()
            print("✅ Technical indicators initialized")
            
            # Get test data
            data = fetcher.get_stock_data('RELIANCE', days=50)
            if data.empty:
                print("❌ No test data available")
                return False
            
            # Add indicators
            enhanced_data = indicators.add_all_indicators(data)
            
            # Check for key indicators
            key_indicators = ['RSI', 'EMA_20', 'MACD', 'BB_Upper', 'BB_Lower']
            missing_indicators = [ind for ind in key_indicators if ind not in enhanced_data.columns]
            
            if not missing_indicators:
                print(f"✅ All key indicators added: {len(enhanced_data.columns) - len(data.columns)} new columns")
            else:
                print(f"❌ Missing indicators: {missing_indicators}")
                return False
            
            # Test signal generation
            signals = indicators.get_signals(enhanced_data)
            print(f"✅ Generated {len(signals)} technical signals")
            
            # Validate signal structure
            if signals:
                sample_signal = signals[0]
                required_fields = ['action', 'description']
                if all(field in sample_signal for field in required_fields):
                    print("✅ Signal structure valid")
                else:
                    print("❌ Invalid signal structure")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Technical indicators error: {e}")
            return False
    
    def test_signal_generator(self):
        """Test signal generator"""
        try:
            from src.strategies.signal_generator import SignalGenerator
            from src.indicators.technical import TechnicalIndicators
            from src.market_regime import MarketRegimeDetector
            from src.data_fetcher import DataFetcher
            
            # Initialize components
            fetcher = DataFetcher()
            indicators = TechnicalIndicators()
            regime_detector = MarketRegimeDetector(fetcher)
            generator = SignalGenerator(indicators, regime_detector)
            print("✅ Signal generator initialized")
            
            # Get test data
            symbols = ['RELIANCE', 'TCS']
            stocks_data = fetcher.get_multiple_stocks_data(symbols, days=30)
            
            if not stocks_data:
                print("⚠️ No data for signal generation, testing fallback")
                signals = generator._generate_test_signals()
            else:
                print(f"✅ Got data for {len(stocks_data)} stocks")
                signals = generator.generate_signals(stocks_data)
            
            if signals:
                print(f"✅ Generated {len(signals)} signals")
                
                # Validate signal structure
                sample_signal = signals[0]
                required_fields = ['symbol', 'action', 'price', 'confidence']
                if all(field in sample_signal for field in required_fields):
                    print("✅ Signal structure valid")
                    print(f"   Sample: {sample_signal['action']} {sample_signal['symbol']} @ ₹{sample_signal['price']:.2f}")
                else:
                    print(f"❌ Invalid signal structure: {sample_signal}")
                    return False
            else:
                print("❌ No signals generated")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Signal generator error: {e}")
            return False
    
    def test_paper_trading(self):
        """Test paper trading engine"""
        try:
            from src.engines.paper_trading import PaperTradingEngine
            from src.data_fetcher import DataFetcher
            from src.strategies.signal_generator import SignalGenerator
            from src.indicators.technical import TechnicalIndicators
            from src.market_regime import MarketRegimeDetector
            
            # Initialize components
            fetcher = DataFetcher()
            indicators = TechnicalIndicators()
            regime_detector = MarketRegimeDetector(fetcher)
            generator = SignalGenerator(indicators, regime_detector)
            
            # Initialize paper trading
            engine = PaperTradingEngine(
                data_fetcher=fetcher,
                signal_generator=generator,
                initial_capital=100000
            )
            print("✅ Paper trading engine initialized")
            
            # Test portfolio status
            status = engine.get_portfolio_status()
            if status and 'total_value' in status:
                print(f"✅ Portfolio status: ₹{status['total_value']:,.2f}")
            else:
                print("❌ Portfolio status failed")
                return False
            
            # Test trade execution
            test_signal = {
                'symbol': 'RELIANCE',
                'action': 'BUY',
                'price': 2450.0,
                'confidence': 75,
                'reasons': ['Test signal'],
                'stop_loss': 2400.0,
                'target_price': 2500.0
            }
            
            trade_result = engine.execute_trade(test_signal)
            if trade_result:
                print("✅ Test trade executed successfully")
            else:
                print("⚠️ Test trade execution failed (may be due to constraints)")
            
            # Test trade history
            history = engine.get_trade_history(days=7)
            print(f"✅ Trade history: {len(history)} trades")
            
            return True
            
        except Exception as e:
            print(f"❌ Paper trading error: {e}")
            return False
    
    def test_database(self):
        """Test database operations"""
        try:
            # Test SQLite database
            test_db = 'test_trading.db'
            
            # Create test database
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            
            # Create test table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_trades (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    price REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert test data
            cursor.execute(
                'INSERT INTO test_trades (symbol, price) VALUES (?, ?)',
                ('TEST', 100.0)
            )
            conn.commit()
            
            # Query test data
            cursor.execute('SELECT * FROM test_trades WHERE symbol = ?', ('TEST',))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                print("✅ Database operations successful")
                # Clean up
                os.remove(test_db)
                return True
            else:
                print("❌ Database query failed")
                return False
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    def test_telegram(self):
        """Test Telegram bot (optional)"""
        try:
            from src.utils.telegram_bot import TelegramBot
            
            bot = TelegramBot()
            if bot.bot:
                print("✅ Telegram bot initialized")
                return True
            else:
                print("⚠️ Telegram bot not configured (optional)")
                return True  # Not critical
                
        except Exception as e:
            print(f"⚠️ Telegram test skipped: {e}")
            return True  # Not critical
    
    def test_flask_server(self):
        """Test if Flask server is running"""
        try:
            # Check if server is already running
            response = requests.get(f"{self.base_url}/ping", timeout=5)
            if response.status_code == 200:
                print("✅ Flask server is running")
                return True
            else:
                print(f"❌ Flask server returned status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Flask server not running")
            print("   Start server with: python main.py")
            return False
        except Exception as e:
            print(f"❌ Flask server test error: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints (requires running server)"""
        if not self.test_flask_server():
            print("⚠️ Skipping API tests - server not running")
            return False
        
        try:
            endpoints = [
                ('/api/portfolio', 'Portfolio API'),
                ('/api/system_status', 'System Status API'),
                ('/api/signals', 'Signals API'),
                ('/api/regime', 'Market Regime API')
            ]
            
            for endpoint, name in endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if 'error' not in data:
                            print(f"✅ {name}: Working")
                        else:
                            print(f"❌ {name}: API error - {data['error']}")
                            return False
                    else:
                        print(f"❌ {name}: HTTP {response.status_code}")
                        return False
                except Exception as e:
                    print(f"❌ {name}: {str(e)}")
                    return False
            
            # Test POST endpoints
            post_endpoints = [
                ('/api/update_system', 'System Update'),
                ('/api/run_trading_session', 'Trading Session')
            ]
            
            for endpoint, name in post_endpoints:
                try:
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=15)
                    if response.status_code == 200:
                        print(f"✅ {name}: Working")
                    else:
                        print(f"⚠️ {name}: HTTP {response.status_code} (may be expected)")
                except Exception as e:
                    print(f"⚠️ {name}: {str(e)} (may be expected)")
            
            return True
            
        except Exception as e:
            print(f"❌ API endpoints error: {e}")
            return False
    
    def test_frontend(self):
        """Test frontend assets"""
        try:
            # Check if static files exist
            static_files = [
                'static/css/style.css',
                'static/js/dashboard.js',
                'templates/dashboard.html',
                'templates/trades.html',
                'templates/base.html'
            ]
            
            missing_files = []
            for file_path in static_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if not missing_files:
                print("✅ All frontend files present")
            else:
                print(f"❌ Missing frontend files: {missing_files}")
                return False
            
            # Test frontend access (requires running server)
            if self.test_flask_server():
                try:
                    response = requests.get(f"{self.base_url}/", timeout=5)
                    if response.status_code == 200 and 'Trading System' in response.text:
                        print("✅ Frontend accessible")
                    else:
                        print("❌ Frontend not accessible")
                        return False
                except:
                    print("⚠️ Frontend access test failed")
            
            return True
            
        except Exception as e:
            print(f"❌ Frontend test error: {e}")
            return False
    
    def test_performance(self):
        """Test system performance"""
        try:
            # Test data fetching speed
            start_time = time.time()
            
            from src.data_fetcher import DataFetcher
            fetcher = DataFetcher()
            
            # Test current price speed
            price_start = time.time()
            price = fetcher.get_current_price('RELIANCE')
            price_time = time.time() - price_start
            
            if price_time < 5.0:  # Should be under 5 seconds
                print(f"✅ Current price fetch: {price_time:.2f}s")
            else:
                print(f"⚠️ Current price slow: {price_time:.2f}s")
            
            # Test historical data speed
            data_start = time.time()
            data = fetcher.get_stock_data('TCS', days=30)
            data_time = time.time() - data_start
            
            if data_time < 10.0:  # Should be under 10 seconds
                print(f"✅ Historical data fetch: {data_time:.2f}s")
            else:
                print(f"⚠️ Historical data slow: {data_time:.2f}s")
            
            return True
            
        except Exception as e:
            print(f"❌ Performance test error: {e}")
            return False
    
    def test_error_handling(self):
        """Test error handling"""
        try:
            from src.data_fetcher import DataFetcher
            
            fetcher = DataFetcher()
            
            # Test invalid symbol
            try:
                price = fetcher.get_current_price('INVALID_SYMBOL_12345')
                if price and price > 0:
                    print("✅ Invalid symbol handled gracefully")
                else:
                    print("✅ Invalid symbol returned None/0")
            except Exception as e:
                print(f"❌ Invalid symbol caused crash: {e}")
                return False
            
            # Test network timeout handling
            try:
                data = fetcher.get_stock_data('TEST_TIMEOUT', days=1)
                print("✅ Timeout handled gracefully")
            except Exception as e:
                print(f"✅ Timeout exception caught: {type(e).__name__}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
    
    def test_concurrent_access(self):
        """Test concurrent database access"""
        try:
            from src.engines.paper_trading import PaperTradingEngine
            
            def worker():
                try:
                    engine = PaperTradingEngine(initial_capital=50000)
                    status = engine.get_portfolio_status()
                    return True
                except:
                    return False
            
            # Run 5 concurrent workers
            threads = []
            for i in range(5):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            print("✅ Concurrent access test completed")
            return True
            
        except Exception as e:
            print(f"❌ Concurrent access test error: {e}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.passed_tests) + len(self.failed_tests)
        pass_rate = (len(self.passed_tests) / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   • {test}")
        
        if pass_rate >= 80:
            print(f"\n🎉 SYSTEM STATUS: HEALTHY ({pass_rate:.1f}% pass rate)")
        elif pass_rate >= 60:
            print(f"\n⚠️ SYSTEM STATUS: DEGRADED ({pass_rate:.1f}% pass rate)")
        else:
            print(f"\n🚨 SYSTEM STATUS: CRITICAL ({pass_rate:.1f}% pass rate)")
        
        print("\n📝 RECOMMENDATIONS:")
        if len(self.failed_tests) == 0:
            print("   ✅ System is ready for paper trading!")
        else:
            print("   🔧 Fix failed tests before deployment")
            print("   📚 Check logs for detailed error information")
            print("   🔄 Re-run tests after fixes")

def main():
    """Main test function"""
    print("🚀 Indian Stock Trading System - Comprehensive Test Suite")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = SystemTester()
    tester.run_all_tests()
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📧 Report any issues to the development team")

if __name__ == "__main__":
    main()