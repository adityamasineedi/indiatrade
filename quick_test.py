# quick_test.py - Test the fixed data fetcher
import sys
sys.path.append('src')

from src.data_fetcher import DataFetcher
import pandas as pd

def quick_test():
    print("🧪 Quick Data Fetcher Test")
    print("=" * 40)
    
    fetcher = DataFetcher()
    
    # Test single stock
    print("📊 Testing RELIANCE data...")
    data = fetcher.get_stock_data('RELIANCE', days=10)
    
    if not data.empty:
        print(f"✅ SUCCESS! Got {len(data)} days of data")
        print(f"💰 Latest price: ₹{data['Close'].iloc[-1]:.2f}")
        print(f"📈 High: ₹{data['High'].iloc[-1]:.2f}")
        print(f"📉 Low: ₹{data['Low'].iloc[-1]:.2f}")
        print(f"📊 Volume: {data['Volume'].iloc[-1]:,}")
        
        # Show sample data
        print(f"\n📋 Sample data (last 3 days):")
        print(data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3))
        
    else:
        print("❌ FAILED - No data received")
        return False
    
    # Test multiple stocks
    print(f"\n📊 Testing multiple stocks...")
    symbols = ['TCS', 'INFY', 'HDFCBANK']
    stocks_data = fetcher.get_multiple_stocks_data(symbols, days=5)
    
    print(f"✅ Got data for {len(stocks_data)}/{len(symbols)} stocks:")
    for symbol, data in stocks_data.items():
        latest_price = data['Close'].iloc[-1]
        print(f"  📈 {symbol}: ₹{latest_price:.2f} ({len(data)} days)")
    
    # Test market overview
    print(f"\n🌐 Testing market overview...")
    overview = fetcher.get_market_overview()
    print(f"📊 Nifty: ₹{overview['nifty_price']:.2f} ({overview['nifty_change']:+.2f})")
    print(f"🕐 Market Status: {overview['market_status']}")
    
    return True

if __name__ == "__main__":
    success = quick_test()
    
    if success:
        print(f"\n🎉 DATA FETCHER IS WORKING!")
        print(f"🚀 Now run: python test_data_sources.py")
    else:
        print(f"\n❌ Data fetcher needs more fixes")