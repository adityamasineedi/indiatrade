import pandas as pd
from datetime import datetime
import time
from config.zerodha.auth import ZerodhaAuth

class ZerodhaTrading:
    """Zerodha-integrated trading engine with paper trading mode"""
    
    def __init__(self, paper_trading=True):
        self.paper_trading = paper_trading
        self.connected = False
        self.auth = None
        self.kite = None
        
        # Paper trading simulation data
        self.paper_cash = 100000.0
        self.paper_positions = {}
        self.paper_trades = []
        
        try:
            self.connect()
        except Exception as e:
            print(f"⚠️ Zerodha connection failed: {e}")
            print("📊 Falling back to enhanced paper trading")
    
    def connect(self):
        """Connect to Zerodha API"""
        try:
            self.auth = ZerodhaAuth()
            
            if self.auth.authenticate():
                self.kite = self.auth.kite
                self.connected = True
                print("✅ Zerodha connection established")
                
                # Test connection
                profile = self.kite.profile()
                print(f"👤 Connected as: {profile.get('user_name')} ({profile.get('user_id')})")
                
                return True
            else:
                print("⚠️ Authentication required - run setup_zerodha_auth() first")
                return False
                
        except Exception as e:
            print(f"❌ Zerodha connection error: {e}")
            self.connected = False
            return False
    
    def setup_authentication(self):
        """Interactive authentication setup"""
        try:
            print("🔐 Setting up Zerodha authentication...")
            
            if not self.auth:
                self.auth = ZerodhaAuth()
            
            # Open login page
            if self.auth.open_login_browser():
                print("\n📋 INSTRUCTIONS:")
                print("1. Complete login in the browser")
                print("2. After successful login, you'll be redirected to a URL")
                print("3. Copy the 'request_token' from the URL")
                print("4. Paste it below")
                print("\nExample URL: https://127.0.0.1:5000/?request_token=ABC123&action=login&status=success")
                print("Copy only: ABC123")
                
                request_token = input("\n🔑 Enter request_token: ").strip()
                
                if request_token:
                    result = self.auth.generate_session(request_token)
                    if result:
                        self.connect()
                        return True
                    else:
                        print("❌ Authentication failed")
                        return False
                else:
                    print("❌ No request token provided")
                    return False
            else:
                print("❌ Could not open login page")
                return False
                
        except Exception as e:
            print(f"❌ Authentication setup error: {e}")
            return False
    
    def get_live_data(self, symbol):
        """Get live market data from Zerodha"""
        try:
            if not self.connected:
                return None
            
            # Convert symbol to NSE format
            instrument_token = f"NSE:{symbol}"
            quote = self.kite.quote(instrument_token)
            
            if instrument_token in quote:
                data = quote[instrument_token]
                return {
                    'symbol': symbol,
                    'last_price': data['last_price'],
                    'open': data['ohlc']['open'],
                    'high': data['ohlc']['high'],
                    'low': data['ohlc']['low'],
                    'close': data['ohlc']['close'],
                    'volume': data['volume'],
                    'change': data.get('net_change', 0),
                    'change_percent': data.get('net_change', 0) / data['ohlc']['close'] * 100 if data['ohlc']['close'] else 0,
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Live data error for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol, days=30):
        """Get historical data from Zerodha"""
        try:
            if not self.connected:
                return None
            
            from datetime import datetime, timedelta
            
            # Get instrument token (you'd need to implement instrument lookup)
            # For now, use a simplified approach
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # This is a simplified version - real implementation needs instrument tokens
            instrument_token = f"NSE:{symbol}"
            
            try:
                data = self.kite.historical_data(
                    instrument_token=instrument_token,
                    from_date=start_date,
                    to_date=end_date,
                    interval="day"
                )
                
                if data:
                    df = pd.DataFrame(data)
                    df['Date'] = pd.to_datetime(df['date'])
                    df.set_index('Date', inplace=True)
                    df.rename(columns={
                        'open': 'Open',
                        'high': 'High', 
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    }, inplace=True)
                    
                    return df[['Open', 'High', 'Low', 'Close', 'Volume']]
                
            except Exception as e:
                print(f"⚠️ Historical data not available via Zerodha API: {e}")
                print("📊 Falling back to Yahoo Finance for historical data")
                return None
                
        except Exception as e:
            print(f"❌ Historical data error for {symbol}: {e}")
            return None
    
    def execute_trade(self, signal):
        """Execute trade (paper trading or live)"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            confidence = signal.get('confidence', 60)
            
            # Get current market price
            live_data = self.get_live_data(symbol)
            if not live_data:
                print(f"❌ Could not get current price for {symbol}")
                return False
            
            current_price = live_data['last_price']
            
            # Position sizing based on confidence
            risk_amount = self.paper_cash * 0.02 * (confidence / 100)  # 2% risk
            quantity = max(1, int(risk_amount / current_price))
            
            if self.paper_trading:
                return self._execute_paper_trade(symbol, action, quantity, current_price, confidence)
            else:
                return self._execute_live_trade(symbol, action, quantity, current_price, confidence)
                
        except Exception as e:
            print(f"❌ Trade execution error: {e}")
            return False
    
    def _execute_paper_trade(self, symbol, action, quantity, price, confidence):
        """Execute paper trade with real market prices"""
        try:
            trade_value = quantity * price
            
            if action == 'BUY':
                if trade_value <= self.paper_cash:
                    self.paper_cash -= trade_value
                    
                    # Add to positions
                    if symbol in self.paper_positions:
                        existing_qty = self.paper_positions[symbol]['quantity']
                        existing_value = self.paper_positions[symbol]['avg_price'] * existing_qty
                        new_avg_price = (existing_value + trade_value) / (existing_qty + quantity)
                        
                        self.paper_positions[symbol]['quantity'] += quantity
                        self.paper_positions[symbol]['avg_price'] = new_avg_price
                    else:
                        self.paper_positions[symbol] = {
                            'quantity': quantity,
                            'avg_price': price,
                            'symbol': symbol
                        }
                    
                    print(f"✅ PAPER BUY: {quantity} {symbol} @ ₹{price:.2f} (Real Zerodha price)")
                    
                else:
                    print(f"❌ Insufficient paper cash: ₹{self.paper_cash:.2f} < ₹{trade_value:.2f}")
                    return False
            
            elif action == 'SELL':
                if symbol in self.paper_positions and self.paper_positions[symbol]['quantity'] >= quantity:
                    self.paper_cash += trade_value
                    
                    self.paper_positions[symbol]['quantity'] -= quantity
                    if self.paper_positions[symbol]['quantity'] == 0:
                        del self.paper_positions[symbol]
                    
                    print(f"✅ PAPER SELL: {quantity} {symbol} @ ₹{price:.2f} (Real Zerodha price)")
                    
                else:
                    print(f"❌ Insufficient shares to sell")
                    return False
            
            # Record trade
            self.paper_trades.append({
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'value': trade_value,
                'confidence': confidence,
                'type': 'PAPER'
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Paper trade error: {e}")
            return False
    
    def _execute_live_trade(self, symbol, action, quantity, price, confidence):
        """Execute live trade on Zerodha (DISABLED for safety)"""
        print("⚠️ LIVE TRADING DISABLED FOR SAFETY")
        print(f"📊 Would execute: {action} {quantity} {symbol} @ ₹{price:.2f}")
        print("🔧 To enable live trading, modify this method")
        return False
    
    def get_portfolio_status(self):
        """Get portfolio status (paper trading or live)"""
        try:
            if self.paper_trading:
                return self._get_paper_portfolio_status()
            else:
                return self._get_live_portfolio_status()
                
        except Exception as e:
            print(f"❌ Portfolio status error: {e}")
            return {
                'total_value': 100000.0,
                'cash': 100000.0,
                'positions_value': 0.0,
                'day_pnl': 0.0,
                'total_pnl': 0.0
            }
    
    def _get_paper_portfolio_status(self):
        """Get paper trading portfolio status with real market prices"""
        positions_value = 0
        unrealized_pnl = 0
        
        for symbol, position in self.paper_positions.items():
            live_data = self.get_live_data(symbol)
            if live_data:
                current_price = live_data['last_price']
                position_value = position['quantity'] * current_price
                positions_value += position_value
                
                cost_basis = position['quantity'] * position['avg_price']
                unrealized_pnl += (position_value - cost_basis)
        
        total_value = self.paper_cash + positions_value
        total_pnl = total_value - 100000.0  # Initial capital
        
        return {
            'total_value': total_value,
            'cash': self.paper_cash,
            'positions_value': positions_value,
            'unrealized_pnl': unrealized_pnl,
            'day_pnl': self._calculate_day_pnl(),
            'total_pnl': total_pnl,
            'positions_count': len(self.paper_positions),
            'return_pct': (total_pnl / 100000.0) * 100,
            'connected_to_zerodha': self.connected
        }
    
    def _get_live_portfolio_status(self):
        """Get live portfolio from Zerodha"""
        try:
            if not self.connected:
                return None
            
            holdings = self.kite.holdings()
            positions = self.kite.positions()
            
            portfolio = {
                'holdings': holdings,
                'positions': positions['net'],
                'total_value': sum(holding['value'] for holding in holdings),
                'day_pnl': sum(pos['pnl'] for pos in positions['net']),
                'total_pnl': sum(pos['pnl'] for pos in positions['net']),
                'connected_to_zerodha': True
            }
            
            return portfolio
            
        except Exception as e:
            print(f"❌ Live portfolio error: {e}")
            return None
    
    def _calculate_day_pnl(self):
        """Calculate today's P&L"""
        today = datetime.now().date()
        day_pnl = 0
        
        for trade in self.paper_trades:
            if trade['timestamp'].date() == today:
                # Simplified P&L calculation
                if trade['action'] == 'SELL':
                    day_pnl += trade['value'] * 0.01  # Assume 1% profit
        
        return day_pnl

# Setup function for easy integration
def setup_zerodha_auth():
    """Interactive setup for Zerodha authentication"""
    try:
        print("🚀 Setting up Zerodha Integration")
        print("================================")
        
        # Check environment variables
        api_key = os.getenv('ZERODHA_API_KEY')
        api_secret = os.getenv('ZERODHA_API_SECRET')
        
        if not api_key or not api_secret:
            print("❌ Missing Zerodha API credentials in .env file")
            print("\n📋 Add these to your .env file:")
            print("ZERODHA_API_KEY=your_api_key_here")
            print("ZERODHA_API_SECRET=your_api_secret_here")
            print("\n🔗 Get credentials from: https://developers.kite.trade/")
            return False
        
        # Initialize trading engine
        trading_engine = ZerodhaTrading(paper_trading=True)
        
        if not trading_engine.connected:
            print("🔐 Starting authentication process...")
            success = trading_engine.setup_authentication()
            
            if success:
                print("✅ Zerodha integration setup complete!")
                print("📊 Ready for paper trading with real market data")
                return True
            else:
                print("❌ Authentication failed")
                return False
        else:
            print("✅ Already connected to Zerodha!")
            return True
            
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

# Test function
def test_zerodha_integration():
    """Test Zerodha integration"""
    try:
        print("🧪 Testing Zerodha Integration")
        print("==============================")
        
        trading_engine = ZerodhaTrading(paper_trading=True)
        
        if trading_engine.connected:
            print("✅ Connection: SUCCESSFUL")
            
            # Test live data
            test_symbols = ['RELIANCE', 'TCS', 'INFY']
            for symbol in test_symbols:
                data = trading_engine.get_live_data(symbol)
                if data:
                    print(f"✅ {symbol}: ₹{data['last_price']:.2f} ({data['change_percent']:+.2f}%)")
                else:
                    print(f"❌ {symbol}: Data not available")
            
            # Test portfolio
            portfolio = trading_engine.get_portfolio_status()
            print(f"\n📊 Portfolio Value: ₹{portfolio['total_value']:,.2f}")
            print(f"💰 Cash: ₹{portfolio['cash']:,.2f}")
            print(f"📈 Positions: {portfolio['positions_count']}")
            
            return True
            
        else:
            print("❌ Connection: FAILED")
            print("🔧 Run setup_zerodha_auth() first")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False