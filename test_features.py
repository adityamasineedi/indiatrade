# test_features.py
"""
Test and configure specific trading system features
"""

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.append('src')

from src.engines.backtest import BacktestEngine
from src.engines.paper_trading import PaperTradingEngine
from src.utils.telegram_bot import TelegramBot
from src.data_fetcher import DataFetcher
from src.indicators.technical import TechnicalIndicators
from src.strategies.signal_generator import SignalGenerator
from src.market_regime import MarketRegimeDetector
from config.settings import Config

def test_backtesting_engine():
    """Test the backtesting functionality"""
    print("📊 Testing Backtesting Engine...")
    
    try:
        # Initialize components
        data_fetcher = DataFetcher()
        technical_indicators = TechnicalIndicators()
        regime_detector = MarketRegimeDetector(data_fetcher)
        signal_generator = SignalGenerator(technical_indicators, regime_detector)
        backtest_engine = BacktestEngine(data_fetcher, technical_indicators, signal_generator)
        
        # Run backtest on popular stocks
        test_symbols = ['RELIANCE', 'TCS', 'INFY']
        print(f"🔍 Running backtest on: {', '.join(test_symbols)}")
        
        # Run 30-day backtest
        results = backtest_engine.run_backtest(test_symbols, days=30)
        
        if results and 'summary' in results:
            summary = results['summary']
            
            print("📈 Backtest Results:")
            print(f"  💰 Total Return: {summary.get('total_return_pct', 0):.2f}%")
            print(f"  🎯 Win Rate: {summary.get('win_rate', 0):.1f}%")
            print(f"  📊 Total Trades: {summary.get('total_trades', 0)}")
            print(f"  📈 Profitable Trades: {summary.get('profitable_trades', 0)}")
            print(f"  📉 Losing Trades: {summary.get('losing_trades', 0)}")
            print(f"  💎 Max Drawdown: {summary.get('max_drawdown', 0):.2f}%")
            print(f"  ⚡ Sharpe Ratio: {summary.get('sharpe_ratio', 0):.2f}")
            
            # Show some individual trades
            if 'trades' in results and results['trades']:
                print(f"\n🔍 Sample Trades:")
                for i, trade in enumerate(results['trades'][:3]):  # First 3 trades
                    pnl_emoji = "💚" if trade.get('pnl', 0) > 0 else "❌"
                    print(f"  {i+1}. {trade.get('symbol', 'Unknown')} {trade.get('action', 'Unknown')} - "
                          f"P&L: {pnl_emoji} ₹{trade.get('pnl', 0):.2f}")
            
            return True
        else:
            print("❌ No backtest results generated")
            return False
            
    except Exception as e:
        print(f"❌ Backtesting Error: {e}")
        return False

def test_paper_trading():
    """Test paper trading functionality"""
    print("\n💼 Testing Paper Trading Engine...")
    
    try:
        # Initialize components
        data_fetcher = DataFetcher()
        regime_detector = MarketRegimeDetector(data_fetcher)
        technical_indicators = TechnicalIndicators()
        signal_generator = SignalGenerator(technical_indicators, regime_detector)
        paper_trading_engine = PaperTradingEngine(data_fetcher, signal_generator)
        
        # Get portfolio status
        portfolio = paper_trading_engine.get_portfolio_status()
        
        print("📊 Paper Trading Portfolio:")
        print(f"  💰 Total Value: ₹{portfolio.get('total_value', 0):,.2f}")
        print(f"  💵 Cash: ₹{portfolio.get('cash', 0):,.2f}")
        print(f"  📈 Invested: ₹{portfolio.get('invested', 0):,.2f}")
        print(f"  🎯 Total P&L: ₹{portfolio.get('total_pnl', 0):,.2f}")
        print(f"  📊 Positions: {portfolio.get('positions_count', 0)}")
        
        # Test placing a sample trade
        print("\n🧪 Testing Trade Execution:")
        
        # Try to execute a sample BUY order
        test_signal = {
            'symbol': 'RELIANCE',
            'action': 'BUY',
            'price': 2450.0,
            'confidence': 75.0,
            'quantity': 10
        }
        
        success = paper_trading_engine.execute_trade(test_signal)
        
        if success:
            print(f"  ✅ Sample trade executed: {test_signal['action']} {test_signal['quantity']} shares of {test_signal['symbol']}")
        else:
            print(f"  ⚠️  Sample trade not executed (might be due to existing position or other rules)")
        
        # Get trade history
        trade_history = paper_trading_engine.get_trade_history(days=7)
        print(f"\n📜 Recent Trades: {len(trade_history)} trades in last 7 days")
        
        if trade_history:
            for i, trade in enumerate(trade_history[:3]):  # Show first 3
                print(f"  {i+1}. {trade.get('symbol', 'Unknown')} {trade.get('action', 'Unknown')} - "
                      f"₹{trade.get('price', 0):.2f} x{trade.get('quantity', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Paper Trading Error: {e}")
        return False

def test_telegram_integration():
    """Test Telegram bot integration"""
    print("\n📱 Testing Telegram Integration...")
    
    try:
        telegram_bot = TelegramBot()
        
        # Test connection
        success, message = telegram_bot.test_connection()
        
        if success:
            print("  ✅ Telegram bot connected successfully")
            print(f"  📞 Bot Info: {message}")
            
            # Test sending a message
            test_message = f"🤖 Test message from Indian Trading System\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            try:
                telegram_bot.send_message_sync(test_message)
                print("  ✅ Test message sent successfully")
                return True
            except Exception as msg_error:
                print(f"  ⚠️  Message sending failed: {msg_error}")
                return False
                
        else:
            print(f"  ❌ Telegram connection failed: {message}")
            print("  💡 Tips:")
            print("    1. Check your TELEGRAM_BOT_TOKEN in .env file")
            print("    2. Make sure you've started a chat with your bot")
            print("    3. Send /start to your bot first")
            return False
            
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        print("💡 To configure Telegram:")
        print("  1. Create a bot with @BotFather on Telegram")
        print("  2. Get the bot token")
        print("  3. Add it to your .env file: TELEGRAM_BOT_TOKEN=your_token")
        print("  4. Start a chat with your bot and send /start")
        return False

def test_real_time_updates():
    """Test real-time dashboard updates"""
    print("\n🔄 Testing Real-time Updates...")
    
    import requests
    import time
    
    base_url = "http://127.0.0.1:5000"
    
    try:
        print("📊 Testing API endpoint responses over time...")
        
        # Test multiple calls to see if data updates
        for i in range(3):
            response = requests.get(f"{base_url}/api/portfolio", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  🔄 Call {i+1}: Portfolio value ₹{data.get('total_value', 0):,.2f}")
            else:
                print(f"  ❌ Call {i+1}: Failed")
                
            if i < 2:  # Don't sleep after last iteration
                time.sleep(2)
        
        # Test signals endpoint
        response = requests.get(f"{base_url}/api/signals", timeout=5)
        if response.status_code == 200:
            signals = response.json()
            print(f"  📡 Signals endpoint: {len(signals)} signals available")
        
        # Test system status
        response = requests.get(f"{base_url}/api/system_status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"  ⚡ System Status: Running={status.get('running', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Real-time Updates Error: {e}")
        return False

def configure_watchlist():
    """Help configure the trading watchlist"""
    print("\n📋 Configuring Trading Watchlist...")
    
    try:
        config = Config()
        current_watchlist = config.WATCHLIST
        
        print(f"📊 Current Watchlist ({len(current_watchlist)} stocks):")
        for i, symbol in enumerate(current_watchlist[:10], 1):  # Show first 10
            print(f"  {i:2d}. {symbol}")
        
        if len(current_watchlist) > 10:
            print(f"     ... and {len(current_watchlist) - 10} more")
        
        # Test data availability for watchlist
        print("\n🔍 Testing data availability for watchlist stocks...")
        data_fetcher = DataFetcher()
        
        available_count = 0
        for symbol in current_watchlist[:5]:  # Test first 5
            try:
                data = data_fetcher.get_stock_data(symbol, days=5)
                if not data.empty:
                    available_count += 1
                    print(f"  ✅ {symbol}: Data available")
                else:
                    print(f"  ❌ {symbol}: No data")
            except:
                print(f"  ⚠️  {symbol}: Error fetching data")
        
        print(f"\n📊 Summary: {available_count}/5 tested stocks have data available")
        
        # Suggest popular liquid stocks
        suggested_stocks = [
            'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
            'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT', 'ASIANPAINT'
        ]
        
        print(f"\n💡 Suggested liquid stocks for trading:")
        for stock in suggested_stocks:
            print(f"  📈 {stock}")
        
        return True
        
    except Exception as e:
        print(f"❌ Watchlist Configuration Error: {e}")
        return False

def run_feature_tests():
    """Run all feature tests"""
    print("🚀 Testing Trading System Features")
    print("=" * 50)
    
    test_results = {}
    
    # Test backtesting
    test_results['backtesting'] = test_backtesting_engine()
    
    # Test paper trading
    test_results['paper_trading'] = test_paper_trading()
    
    # Test Telegram
    test_results['telegram'] = test_telegram_integration()
    
    # Test real-time updates
    test_results['real_time'] = test_real_time_updates()
    
    # Configure watchlist
    test_results['watchlist'] = configure_watchlist()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 FEATURE TEST SUMMARY:")
    print("=" * 50)
    
    for feature, result in test_results.items():
        status = "✅ WORKING" if result else "❌ NEEDS ATTENTION"
        print(f"{feature.replace('_', ' ').title()}: {status}")
    
    working_features = sum(test_results.values())
    total_features = len(test_results)
    
    print(f"\n📊 Overall: {working_features}/{total_features} features working")
    
    if working_features == total_features:
        print("\n🎉 ALL FEATURES WORKING! Your trading system is fully operational!")
    elif working_features >= total_features * 0.8:
        print("\n✅ Most features working! Minor configuration needed.")
    else:
        print("\n⚠️  Several features need attention. Check the errors above.")
    
    # Next steps
    print(f"\n🎯 NEXT STEPS:")
    print("  1. 📱 Set up Telegram bot (if not working)")
    print("  2. 📊 Monitor live dashboard at http://localhost:5000")
    print("  3. 🔄 Run paper trading sessions")
    print("  4. 📈 Analyze backtest results")
    print("  5. ⚙️  Fine-tune strategy parameters")
    
    return working_features >= total_features * 0.8

if __name__ == "__main__":
    run_feature_tests()