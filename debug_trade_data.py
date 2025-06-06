# debug_trade_data.py
"""
Debug script to identify and fix today's trade data issues
Run this to check what's happening with your trading system
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add src to path
sys.path.append('src')

def check_database_exists():
    """Check if database exists and is accessible"""
    db_path = 'data/paper_trading.db'
    
    print("🔍 Checking Database...")
    
    if not os.path.exists('data'):
        print("❌ 'data' directory doesn't exist")
        return False
    
    if not os.path.exists(db_path):
        print("❌ Database file doesn't exist")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"✅ Database exists with tables: {[table[0] for table in tables]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_all_trades():
    """Check all trades in database"""
    try:
        conn = sqlite3.connect('data/paper_trading.db')
        cursor = conn.cursor()
        
        # Get all trades
        cursor.execute("SELECT * FROM paper_trades ORDER BY timestamp DESC LIMIT 10")
        trades = cursor.fetchall()
        
        print(f"\n📊 Total Trades in Database:")
        
        if not trades:
            print("❌ No trades found in database")
            conn.close()
            return
        
        print(f"✅ Found {len(trades)} recent trades:")
        for i, trade in enumerate(trades):
            print(f"  {i+1}. {trade[2]} {trade[3]} {trade[1]} @ Rs.{trade[4]:.2f} on {trade[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking trades: {e}")

def check_todays_trades():
    """Check specifically for today's trades"""
    try:
        conn = sqlite3.connect('data/paper_trading.db')
        cursor = conn.cursor()
        
        # Get today's date in different formats to test
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        
        print(f"\n📅 Checking Today's Trades ({today_str})...")
        
        # Method 1: Direct date comparison
        cursor.execute("""
            SELECT COUNT(*) FROM paper_trades 
            WHERE DATE(timestamp) = DATE('now', 'localtime')
        """)
        count1 = cursor.fetchone()[0]
        
        # Method 2: String comparison
        cursor.execute("""
            SELECT COUNT(*) FROM paper_trades 
            WHERE timestamp LIKE ?
        """, (f"{today_str}%",))
        count2 = cursor.fetchone()[0]
        
        # Method 3: Range comparison
        cursor.execute("""
            SELECT COUNT(*) FROM paper_trades 
            WHERE timestamp >= ? AND timestamp < ?
        """, (today_str, (today + timedelta(days=1)).strftime('%Y-%m-%d')))
        count3 = cursor.fetchone()[0]
        
        print(f"  Method 1 (DATE function): {count1} trades")
        print(f"  Method 2 (LIKE): {count2} trades")
        print(f"  Method 3 (Range): {count3} trades")
        
        # Get actual today's trades
        cursor.execute("""
            SELECT timestamp, symbol, action, price, quantity, pnl 
            FROM paper_trades 
            WHERE DATE(timestamp) = DATE('now', 'localtime')
            ORDER BY timestamp DESC
        """)
        todays_trades = cursor.fetchall()
        
        if todays_trades:
            print(f"\n✅ Today's Trades ({len(todays_trades)}):")
            for trade in todays_trades:
                pnl_str = f"P&L: Rs.{trade[5]:.2f}" if trade[5] else "No P&L"
                print(f"  {trade[0]} - {trade[2]} {trade[3]} {trade[1]} @ Rs.{trade[4]:.2f} ({pnl_str})")
        else:
            print("❌ No trades found for today")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking today's trades: {e}")

def check_trading_signals():
    """Check if trading signals are being generated"""
    try:
        conn = sqlite3.connect('data/paper_trading.db')
        cursor = conn.cursor()
        
        print(f"\n📡 Checking Trading Signals...")
        
        # Check signals table
        cursor.execute("SELECT COUNT(*) FROM trading_signals")
        total_signals = cursor.fetchone()[0]
        
        # Check today's signals
        cursor.execute("""
            SELECT COUNT(*) FROM trading_signals 
            WHERE DATE(timestamp) = DATE('now', 'localtime')
        """)
        todays_signals = cursor.fetchone()[0]
        
        # Check executed signals
        cursor.execute("""
            SELECT COUNT(*) FROM trading_signals 
            WHERE executed = TRUE AND DATE(timestamp) = DATE('now', 'localtime')
        """)
        executed_signals = cursor.fetchone()[0]
        
        print(f"  Total Signals: {total_signals}")
        print(f"  Today's Signals: {todays_signals}")
        print(f"  Executed Today: {executed_signals}")
        
        # Get recent signals
        cursor.execute("""
            SELECT timestamp, symbol, action, confidence, executed 
            FROM trading_signals 
            ORDER BY timestamp DESC LIMIT 5
        """)
        recent_signals = cursor.fetchall()
        
        if recent_signals:
            print(f"\n📊 Recent Signals:")
            for signal in recent_signals:
                status = "✅ Executed" if signal[4] else "⏳ Pending"
                print(f"  {signal[0]} - {signal[2]} {signal[1]} (Confidence: {signal[3]:.1f}%) {status}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking signals: {e}")

def check_market_status():
    """Check if market is open and system is running"""
    from datetime import datetime
    
    print(f"\n🕐 Market Status Check...")
    
    now = datetime.now()
    
    # Check day of week
    if now.weekday() >= 5:  # Saturday or Sunday
        print("❌ Market is closed - Weekend")
        return False
    
    # Check market hours (9:15 AM to 3:30 PM IST)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    if market_open <= now <= market_close:
        print("✅ Market is OPEN")
        return True
    else:
        print(f"❌ Market is CLOSED (opens at 9:15 AM, closes at 3:30 PM)")
        print(f"   Current time: {now.strftime('%H:%M:%S')}")
        return False

def test_paper_trading_engine():
    """Test if paper trading engine can execute a trade"""
    try:
        print(f"\n🧪 Testing Paper Trading Engine...")
        
        from src.engines.paper_trading import PaperTradingEngine
        
        # Initialize engine
        engine = PaperTradingEngine()
        
        # Check portfolio status
        status = engine.get_portfolio_status()
        print(f"✅ Engine initialized successfully")
        print(f"   Portfolio Value: Rs.{status['total_value']:,.2f}")
        print(f"   Cash: Rs.{status['cash']:,.2f}")
        print(f"   Positions: {status['positions_count']}")
        
        # Try to execute a sample trade
        print(f"\n🔄 Testing sample trade execution...")
        success = engine.execute_sample_trade()
        
        if success:
            print("✅ Sample trade executed successfully")
        else:
            print("❌ Sample trade failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Paper Trading Engine error: {e}")
        return False

def fix_daily_pnl_calculation():
    """Fix the daily P&L calculation method"""
    
    fix_code = '''
def _get_daily_pnl_fixed(self):
    """Fixed daily P&L calculation"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.now().date().strftime('%Y-%m-%d')
        
        # Method 1: Using date range
        cursor.execute("""
            SELECT SUM(pnl) FROM paper_trades 
            WHERE timestamp >= ? AND timestamp < ?
        """, (today, (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else 0.0
        
    except Exception as e:
        logger.error(f"Error calculating daily P&L: {e}")
        return 0.0
'''
    
    print(f"\n🔧 Daily P&L Fix Code:")
    print(fix_code)

def manual_trade_test():
    """Manually add a test trade to see if it shows up"""
    try:
        print(f"\n🧪 Adding Manual Test Trade...")
        
        conn = sqlite3.connect('data/paper_trading.db')
        cursor = conn.cursor()
        
        # Add a test trade for today
        test_trade = {
            'timestamp': datetime.now(),
            'symbol': 'TEST',
            'action': 'BUY',
            'price': 100.0,
            'quantity': 10,
            'amount': 1000.0,
            'commission': 1.0,
            'pnl': 0.0,
            'portfolio_value': 100000.0,
            'reason': 'Manual test trade',
            'stop_loss': 95.0,
            'target_price': 110.0
        }
        
        cursor.execute('''
            INSERT INTO paper_trades 
            (timestamp, symbol, action, price, quantity, amount, commission, pnl, 
             portfolio_value, reason, stop_loss, target_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_trade['timestamp'], test_trade['symbol'], test_trade['action'], 
            test_trade['price'], test_trade['quantity'], test_trade['amount'], 
            test_trade['commission'], test_trade['pnl'], test_trade['portfolio_value'], 
            test_trade['reason'], test_trade['stop_loss'], test_trade['target_price']
        ))
        
        conn.commit()
        conn.close()
        
        print("✅ Test trade added successfully")
        print("🔄 Now check if it appears in your dashboard/trades page")
        
    except Exception as e:
        print(f"❌ Error adding test trade: {e}")

def check_system_logs():
    """Check system logs for any errors"""
    print(f"\n📋 Checking System Logs...")
    
    log_files = ['logs/trading_system.log', 'logs/trading.log', 'logs/errors.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-10:] if len(lines) > 10 else lines
                
                print(f"\n📄 {log_file} (last 10 lines):")
                for line in recent_lines:
                    print(f"  {line.strip()}")
                    
            except Exception as e:
                print(f"❌ Error reading {log_file}: {e}")
        else:
            print(f"❌ {log_file} not found")

def run_complete_diagnosis():
    """Run complete diagnosis of trade data issue"""
    print("🔍 DIAGNOSING TRADE DATA ISSUE")
    print("=" * 50)
    
    # Step 1: Check database
    db_ok = check_database_exists()
    
    if db_ok:
        # Step 2: Check all trades
        check_all_trades()
        
        # Step 3: Check today's trades specifically
        check_todays_trades()
        
        # Step 4: Check trading signals
        check_trading_signals()
    
    # Step 5: Check market status
    market_open = check_market_status()
    
    # Step 6: Test paper trading engine
    engine_ok = test_paper_trading_engine()
    
    # Step 7: Check logs
    check_system_logs()
    
    print(f"\n" + "=" * 50)
    print("🎯 DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    print(f"Database: {'✅ OK' if db_ok else '❌ ISSUE'}")
    print(f"Market: {'✅ OPEN' if market_open else '❌ CLOSED'}")
    print(f"Engine: {'✅ OK' if engine_ok else '❌ ISSUE'}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not market_open:
        print("1. 🕐 Market is closed - trades only happen during market hours (9:15 AM - 3:30 PM, Mon-Fri)")
    
    if not engine_ok:
        print("2. 🔧 Paper trading engine has issues - check initialization")
    
    print("3. 🧪 Try manual test trade to see if data appears")
    print("4. 🔄 Run a manual trading session via API")
    print("5. ⏰ Wait for automated trading sessions (every 30 minutes during market hours)")
    
    # Offer to add test trade
    response = input(f"\n❓ Add a manual test trade to verify display? (y/n): ")
    if response.lower() == 'y':
        manual_trade_test()
    
    # Show fix code
    print(f"\n🔧 If daily P&L calculation is wrong, use this fix:")
    fix_daily_pnl_calculation()

if __name__ == "__main__":
    run_complete_diagnosis()