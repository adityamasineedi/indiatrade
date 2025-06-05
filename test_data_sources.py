# test_data_sources.py
"""
Test script to configure and verify real data sources
Run this to test NSE data connectivity and system components
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.append('src')

from src.data_fetcher import DataFetcher
from src.indicators.technical import TechnicalIndicators
from src.strategies.signal_generator import SignalGenerator
from src.market_regime import MarketRegimeDetector
from config.settings import Config

def test_nse_data_connectivity():
    """Test NSE data fetching capabilities"""
    print("🔍 Testing NSE Data Connectivity...")
    
    try:
        data_fetcher = DataFetcher()
        
        # Test with popular stocks
        test_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
        
        for symbol in test_symbols:
            print(f"\n📊 Testing {symbol}:")
            
            # Fetch recent data
            data = data_fetcher.get_stock_data(symbol, days=30)
            
            if not data.empty:
                latest_price = data['Close'].iloc[-1]
                latest_date = data.index[-1]
                data_points = len(data)
                
                print(f"  ✅ Success: {data_points} days of data")
                print(f"  💰 Latest Price: ₹{latest_price:.2f}")
                print(f"  📅 Latest Date: {latest_date.strftime('%Y-%m-%d')}")
                
                # Check data quality
                if data_points >= 20:
                    print(f"  ✅ Sufficient data for analysis")
                else:
                    print(f"  ⚠️  Limited data: {data_points} days")
                    
            else:
                print(f"  ❌ Failed to fetch data for {symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ NSE Data Error: {e}")
        return False

def test_technical_indicators():
    """Test technical indicator calculations with real data"""
    print("\n🔧 Testing Technical Indicators...")
    
    try:
        data_fetcher = DataFetcher()
        technical_indicators = TechnicalIndicators()
        
        # Get data for a liquid stock
        symbol = 'RELIANCE'
        data = data_fetcher.get_stock_data(symbol, days=50)
        
        if data.empty:
            print(f"❌ No data available for {symbol}")
            return False
        
        print(f"📊 Testing indicators on {symbol} (50 days data):")
        
        # Add all indicators
        data_with_indicators = technical_indicators.add_all_indicators(data)
        
        # Check latest values
        latest = data_with_indicators.iloc[-1]
        
        print(f"  📈 Price: ₹{latest['Close']:.2f}")
        print(f"  🔄 RSI: {latest['RSI']:.2f}")
        print(f"  📊 MACD: {latest['MACD']:.4f}")
        print(f"  📉 EMA_20: ₹{latest['EMA_20']:.2f}")
        print(f"  ⭐ Supertrend: ₹{latest['Supertrend']:.2f}")
        
        # Validate indicators
        if not pd.isna(latest['RSI']) and 0 <= latest['RSI'] <= 100:
            print("  ✅ RSI calculation working")
        else:
            print("  ⚠️  RSI calculation issue")
            
        if not pd.isna(latest['MACD']):
            print("  ✅ MACD calculation working")
        else:
            print("  ⚠️  MACD calculation issue")
            
        return True
        
    except Exception as e:
        print(f"❌ Technical Indicators Error: {e}")
        return False

def test_market_regime_detection():
    """Test market regime detection"""
    print("\n🎯 Testing Market Regime Detection...")
    
    try:
        data_fetcher = DataFetcher()
        regime_detector = MarketRegimeDetector(data_fetcher)
        
        # Detect current regime
        regime = regime_detector.detect_current_regime()
        
        print(f"📊 Current Market Regime:")
        print(f"  🎭 Regime: {regime.get('regime', 'Unknown')}")
        print(f"  🎯 Confidence: {regime.get('confidence', 0):.1f}%")
        print(f"  💪 Strength: {regime.get('strength', 'Unknown')}")
        print(f"  📈 Trend: {regime.get('trend_direction', 'Unknown')}")
        
        # Validate regime detection
        if regime.get('regime') in ['bull', 'bear', 'sideways']:
            print("  ✅ Regime detection working")
            return True
        else:
            print("  ⚠️  Regime detection needs tuning")
            return False
            
    except Exception as e:
        print(f"❌ Market Regime Error: {e}")
        return False

def test_signal_generation():
    """Test trading signal generation"""
    print("\n🚀 Testing Signal Generation...")
    
    try:
        data_fetcher = DataFetcher()
        technical_indicators = TechnicalIndicators()
        regime_detector = MarketRegimeDetector(data_fetcher)
        signal_generator = SignalGenerator(technical_indicators, regime_detector)
        
        # Get current regime
        current_regime = regime_detector.detect_current_regime()
        
        # Test with watchlist stocks
        config = Config()
        test_symbols = config.WATCHLIST[:5]  # First 5 stocks
        
        print(f"🔍 Generating signals for: {', '.join(test_symbols)}")
        
        # Get multiple stocks data
        stocks_data = data_fetcher.get_multiple_stocks_data(test_symbols, days=50)
        
        if stocks_data:
            signals = signal_generator.generate_signals(stocks_data, current_regime)
            
            print(f"\n📡 Generated {len(signals)} signals:")
            
            for signal in signals:
                action_emoji = "🟢" if signal['action'] == 'BUY' else "🔴"
                print(f"  {action_emoji} {signal['symbol']}: {signal['action']} at ₹{signal['price']:.2f} (Confidence: {signal['confidence']:.1f}%)")
                
                # Show reasoning
                if 'reasons' in signal:
                    print(f"    💡 Reasons: {', '.join(signal['reasons'][:3])}")  # First 3 reasons
            
            return len(signals) > 0
        else:
            print("❌ No stock data available for signal generation")
            return False
            
    except Exception as e:
        print(f"❌ Signal Generation Error: {e}")
        return False

def test_live_api_endpoints():
    """Test live API endpoints"""
    print("\n🌐 Testing Live API Endpoints...")
    
    import requests
    
    base_url = "http://127.0.0.1:5000"
    endpoints = [
        "/api/portfolio",
        "/api/signals", 
        "/api/regime",
        "/api/system_status"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ {endpoint}: Working ({len(str(data))} chars response)")
            else:
                print(f"  ❌ {endpoint}: Error {response.status_code}")
        except Exception as e:
            print(f"  ⚠️  {endpoint}: Connection error - {e}")

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting Comprehensive System Test")
    print("=" * 50)
    
    results = {}
    
    # Test data connectivity
    results['nse_data'] = test_nse_data_connectivity()
    
    # Test technical indicators
    results['indicators'] = test_technical_indicators()
    
    # Test market regime
    results['regime'] = test_market_regime_detection()
    
    # Test signal generation
    results['signals'] = test_signal_generation()
    
    # Test API endpoints
    print("\n🌐 Testing API Endpoints...")
    test_live_api_endpoints()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    overall_success = all(results.values())
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED! Your system is ready for trading!")
        print("\n🎯 Next Steps:")
        print("  1. Configure Telegram bot token in .env")
        print("  2. Adjust watchlist in config/settings.py") 
        print("  3. Start paper trading")
        print("  4. Monitor dashboard at http://localhost:5000")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        
    return overall_success

if __name__ == "__main__":
    run_comprehensive_test()