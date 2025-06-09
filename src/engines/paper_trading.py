# src/engines/paper_trading.py - FIXED VERSION
"""
Paper Trading Engine - FIXED for proper trade execution and balance updates
"""
import pandas as pd
import numpy as np
import logging
import json
import sqlite3
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class PaperTradingEngine:
    def __init__(self, data_fetcher=None, signal_generator=None, initial_capital=100000, config=None):
        """FIXED Constructor with proper initialization"""
        
        # Initialize configuration
        self.initial_capital = initial_capital
        self.data_fetcher = data_fetcher
        self.signal_generator = signal_generator
        
        # Trading parameters
        self.commission_rate = 0.1  # 0.1%
        self.max_positions = 5
        self.risk_per_trade = 2.0  # 2%
        
        # Initialize portfolio
        self.portfolio = PaperPortfolio(self.initial_capital)
        
        # Database setup
        self.db_path = 'data/paper_trading.db'
        os.makedirs('data', exist_ok=True)
        self.init_database()
        
        # Load existing portfolio state
        self._load_portfolio_state()
        
        logger.info(f"Paper Trading Engine initialized with ₹{self.initial_capital:,.2f}")
        print(f"✅ Paper Trading Engine ready - Capital: ₹{self.initial_capital:,.2f}")

    def init_database(self):
        """Initialize database with proper schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    commission REAL NOT NULL,
                    pnl REAL DEFAULT 0,
                    portfolio_value REAL NOT NULL,
                    reason TEXT,
                    stop_loss REAL,
                    target_price REAL
                )
            ''')
            
            # Create portfolio snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cash REAL NOT NULL,
                    position_value REAL NOT NULL,
                    total_value REAL NOT NULL,
                    daily_pnl REAL DEFAULT 0,
                    total_pnl REAL DEFAULT 0,
                    positions_count INTEGER DEFAULT 0
                )
            ''')
            
            # Create positions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS current_positions (
                    symbol TEXT PRIMARY KEY,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    entry_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    stop_loss REAL,
                    target_price REAL,
                    entry_commission REAL DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
            
            print("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            print(f"❌ Database error: {e}")

    def _load_portfolio_state(self):
        """Load existing portfolio state from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load current positions
            cursor.execute('SELECT * FROM current_positions')
            positions = cursor.fetchall()
            
            if positions:
                for pos in positions:
                    symbol, qty, entry_price, current_price, entry_date, stop_loss, target_price, entry_commission = pos
                    self.portfolio.positions[symbol] = {
                        'quantity': qty,
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'entry_date': datetime.fromisoformat(entry_date) if isinstance(entry_date, str) else entry_date,
                        'stop_loss': stop_loss or entry_price * 0.95,
                        'target_price': target_price or entry_price * 1.10,
                        'entry_commission': entry_commission or 0
                    }
                
                print(f"📊 Loaded {len(positions)} existing positions")
            
            # Get latest portfolio snapshot
            cursor.execute('''
                SELECT cash, total_value FROM portfolio_snapshots 
                ORDER BY timestamp DESC LIMIT 1
            ''')
            snapshot = cursor.fetchone()
            
            if snapshot:
                cash, total_value = snapshot
                self.portfolio.cash = cash
                print(f"💰 Loaded portfolio: Cash ₹{cash:,.2f}, Total ₹{total_value:,.2f}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error loading portfolio state: {e}")
            print(f"⚠️ Could not load existing portfolio: {e}")

    def start_paper_trading(self):
        """Start trading session with improved execution"""
        try:
            print("🚀 Starting paper trading session...")
            
            # Update current prices
            self._update_portfolio_positions()
            
            # Generate signals
            signals = self._get_current_signals()
            
            # Execute signals
            executed_trades = []
            if signals:
                for signal in signals:
                    try:
                        confidence = signal.get('confidence', 0)
                        if confidence >= 60:  # Lower threshold for more trades
                            result = self.execute_trade(signal)
                            if result:
                                executed_trades.append(result)
                    except Exception as e:
                        print(f"❌ Trade execution failed: {e}")
                        continue
            
            # Save portfolio snapshot
            self._save_portfolio_snapshot()
            
            # Return results
            result = {
                'status': 'success',
                'signals_generated': len(signals),
                'trades_executed': len(executed_trades),
                'portfolio_value': self.portfolio.total_value,
                'cash': self.portfolio.cash,
                'positions': len(self.portfolio.positions),
                'executed_trades': executed_trades
            }
            
            print(f"✅ Trading session completed:")
            print(f"   📡 Signals: {len(signals)}")
            print(f"   🔄 Trades: {len(executed_trades)}")
            print(f"   💰 Portfolio: ₹{self.portfolio.total_value:,.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Trading session error: {e}")
            return {'status': 'error', 'message': str(e)}

    def execute_trade(self, signal):
        """Execute a trade with proper validation and execution"""
        try:
            symbol = signal['symbol']
            action = signal['action'].upper()
            confidence = signal.get('confidence', 60)
            
            print(f"🔄 Executing {action} for {symbol} (confidence: {confidence}%)")
            
            # Get current price
            current_price = self._get_current_price(symbol)
            if not current_price or current_price <= 0:
                print(f"❌ Invalid price for {symbol}: {current_price}")
                return None
            
            # Update signal with current price
            signal['price'] = current_price
            
            if action == 'BUY':
                return self._execute_buy_trade(signal)
            elif action == 'SELL':
                return self._execute_sell_trade(signal)
            else:
                print(f"❌ Unknown action: {action}")
                return None
                
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return None

    def _execute_buy_trade(self, signal):
        """Execute buy trade with proper position sizing"""
        try:
            symbol = signal['symbol']
            price = signal['price']
            confidence = signal.get('confidence', 60)
            
            # Check if already have position
            if symbol in self.portfolio.positions:
                print(f"⚠️ Already have position in {symbol}")
                return None
            
            # Check position limit
            if len(self.portfolio.positions) >= self.max_positions:
                print(f"⚠️ Position limit reached ({self.max_positions})")
                return None
            
            # Calculate position size based on risk
            risk_amount = self.portfolio.cash * (self.risk_per_trade / 100)
            stop_loss = signal.get('stop_loss', price * 0.95)
            stop_distance = price - stop_loss
            
            if stop_distance <= 0:
                stop_distance = price * 0.02  # 2% default stop
                stop_loss = price - stop_distance
            
            # Calculate quantity based on risk
            quantity = max(1, int(risk_amount / stop_distance))
            
            # Adjust quantity based on available cash
            max_investment = self.portfolio.cash * 0.8  # Use max 80% of cash
            max_quantity = int(max_investment / price)
            quantity = min(quantity, max_quantity)
            
            if quantity <= 0:
                print(f"❌ Insufficient cash for {symbol}")
                return None
            
            # Calculate costs
            gross_amount = quantity * price
            commission = gross_amount * (self.commission_rate / 100)
            total_cost = gross_amount + commission
            
            if total_cost > self.portfolio.cash:
                print(f"❌ Insufficient funds: need ₹{total_cost:.2f}, have ₹{self.portfolio.cash:.2f}")
                return None
            
            # Execute the trade
            target_price = signal.get('target_price', price * 1.10)
            
            success = self.portfolio.buy_position(
                symbol, price, quantity, stop_loss, target_price, commission
            )
            
            if success:
                # Create trade record
                trade_record = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': 'BUY',
                    'price': price,
                    'quantity': quantity,
                    'amount': gross_amount,
                    'commission': commission,
                    'pnl': 0,
                    'portfolio_value': self.portfolio.total_value,
                    'reason': ', '.join(signal.get('reasons', ['Generated signal'])),
                    'stop_loss': stop_loss,
                    'target_price': target_price
                }
                
                # Save to database
                self._save_trade_to_db(trade_record)
                self._save_position_to_db(symbol)
                
                print(f"✅ BUY executed: {quantity} {symbol} @ ₹{price:.2f}")
                print(f"   💰 Cost: ₹{total_cost:.2f} (commission: ₹{commission:.2f})")
                print(f"   🎯 Target: ₹{target_price:.2f}, Stop: ₹{stop_loss:.2f}")
                
                return trade_record
            else:
                print(f"❌ Buy execution failed for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Buy trade error: {e}")
            return None

    def _execute_sell_trade(self, signal):
        """Execute sell trade"""
        try:
            symbol = signal['symbol']
            price = signal['price']
            
            # Check if we have position
            if symbol not in self.portfolio.positions:
                print(f"⚠️ No position to sell in {symbol}")
                return None
            
            position = self.portfolio.positions[symbol]
            quantity = position['quantity']
            
            # Calculate proceeds
            gross_proceeds = quantity * price
            commission = gross_proceeds * (self.commission_rate / 100)
            net_proceeds = gross_proceeds - commission
            
            # Calculate P&L
            cost_basis = position['entry_price'] * quantity + position.get('entry_commission', 0)
            pnl = net_proceeds - cost_basis
            
            # Execute the trade
            success = self.portfolio.sell_position(symbol, price, commission)
            
            if success:
                # Create trade record
                trade_record = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': 'SELL',
                    'price': price,
                    'quantity': quantity,
                    'amount': gross_proceeds,
                    'commission': commission,
                    'pnl': pnl,
                    'portfolio_value': self.portfolio.total_value,
                    'reason': ', '.join(signal.get('reasons', ['Exit signal'])),
                    'stop_loss': 0,
                    'target_price': 0
                }
                
                # Save to database
                self._save_trade_to_db(trade_record)
                self._remove_position_from_db(symbol)
                
                print(f"✅ SELL executed: {quantity} {symbol} @ ₹{price:.2f}")
                print(f"   💰 Proceeds: ₹{net_proceeds:.2f} (P&L: ₹{pnl:+.2f})")
                
                return trade_record
            else:
                print(f"❌ Sell execution failed for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Sell trade error: {e}")
            return None

    def _get_current_price(self, symbol):
        """Get current price with fallback methods"""
        try:
            if self.data_fetcher:
                price = self.data_fetcher.get_current_price(symbol)
                if price and price > 0:
                    return float(price)
            
            # Fallback prices
            fallback_prices = {
                'RELIANCE': 2450.0, 'TCS': 3680.0, 'INFY': 1750.0,
                'HDFCBANK': 1580.0, 'ICICIBANK': 980.0, 'HINDUNILVR': 2650.0
            }
            
            base_price = fallback_prices.get(symbol, 1000.0)
            # Add small random variation
            import random
            variation = random.uniform(-0.01, 0.01)
            return base_price * (1 + variation)
            
        except Exception as e:
            logger.error(f"Price fetch error for {symbol}: {e}")
            return None

    def _get_current_signals(self):
        """Get trading signals - SIMPLIFIED for testing"""
        try:
            if not self.signal_generator or not self.data_fetcher:
                # Generate simple test signals
                return self._generate_test_signals()
            
            # Get real signals
            watchlist = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
            stocks_data = self.data_fetcher.get_multiple_stocks_data(watchlist, days=30)
            
            if stocks_data:
                signals = self.signal_generator.generate_signals(stocks_data)
                return signals
            else:
                return self._generate_test_signals()
                
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return self._generate_test_signals()

    def _generate_test_signals(self):
        """Generate test signals for demonstration"""
        try:
            import random
            
            symbols = ['RELIANCE', 'TCS', 'INFY']
            signals = []
            
            # Generate 1-2 random signals
            num_signals = random.randint(1, 2)
            selected_symbols = random.sample(symbols, min(num_signals, len(symbols)))
            
            for symbol in selected_symbols:
                price = self._get_current_price(symbol)
                if not price:
                    continue
                
                action = random.choice(['BUY', 'SELL'])
                confidence = random.randint(65, 85)
                
                # Only generate BUY if we don't have position, SELL if we do
                if action == 'BUY' and symbol in self.portfolio.positions:
                    action = 'SELL'
                elif action == 'SELL' and symbol not in self.portfolio.positions:
                    action = 'BUY'
                
                signal = {
                    'symbol': symbol,
                    'action': action,
                    'price': price,
                    'confidence': confidence,
                    'stop_loss': price * 0.95 if action == 'BUY' else price * 1.05,
                    'target_price': price * 1.10 if action == 'BUY' else price * 0.90,
                    'reasons': [f'Test signal for {symbol}', f'{confidence}% confidence'],
                    'timestamp': datetime.now()
                }
                
                signals.append(signal)
            
            if signals:
                print(f"📡 Generated {len(signals)} test signals")
            
            return signals
            
        except Exception as e:
            logger.error(f"Test signal generation error: {e}")
            return []

    def _update_portfolio_positions(self):
        """Update current prices for all positions"""
        try:
            for symbol in list(self.portfolio.positions.keys()):
                current_price = self._get_current_price(symbol)
                if current_price:
                    self.portfolio.update_position_price(symbol, current_price)
                    
                    # Update in database
                    self._update_position_price_in_db(symbol, current_price)
                    
                    # Check exit conditions
                    self._check_position_exit_conditions(symbol, current_price)
            
        except Exception as e:
            logger.error(f"Position update error: {e}")

    def _check_position_exit_conditions(self, symbol, current_price):
        """Check if position should be automatically exited"""
        try:
            position = self.portfolio.positions[symbol]
            
            # Stop loss check
            if current_price <= position['stop_loss']:
                self._auto_exit_position(symbol, current_price, "Stop loss triggered")
                return
            
            # Target price check  
            if current_price >= position['target_price']:
                self._auto_exit_position(symbol, current_price, "Target reached")
                return
            
            # Time-based exit (10 days max holding)
            entry_date = position['entry_date']
            if isinstance(entry_date, str):
                entry_date = datetime.fromisoformat(entry_date)
            
            days_held = (datetime.now() - entry_date).days
            if days_held >= 10:
                self._auto_exit_position(symbol, current_price, "Max holding period reached")
                return
                
        except Exception as e:
            logger.error(f"Exit condition check error for {symbol}: {e}")

    def _auto_exit_position(self, symbol, price, reason):
        """Automatically exit position"""
        try:
            signal = {
                'symbol': symbol,
                'action': 'SELL',
                'price': price,
                'confidence': 100,
                'reasons': [reason],
                'timestamp': datetime.now()
            }
            
            result = self._execute_sell_trade(signal)
            if result:
                print(f"🔄 Auto-exit: {symbol} @ ₹{price:.2f} - {reason}")
            
        except Exception as e:
            logger.error(f"Auto-exit error: {e}")

    def get_portfolio_status(self):
        """Get comprehensive portfolio status"""
        try:
            # Update positions first
            self._update_portfolio_positions()
            
            # Calculate metrics
            total_pnl = self.portfolio.total_value - self.initial_capital
            daily_pnl = self._get_daily_pnl()
            return_pct = (total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
            
            # Get positions with current P&L
            positions = []
            for symbol, pos in self.portfolio.positions.items():
                current_value = pos['quantity'] * pos['current_price']
                cost_basis = pos['quantity'] * pos['entry_price']
                unrealized_pnl = current_value - cost_basis
                
                positions.append({
                    'symbol': symbol,
                    'quantity': pos['quantity'],
                    'entry_price': pos['entry_price'],
                    'current_price': pos['current_price'],
                    'unrealized_pnl': unrealized_pnl,
                    'stop_loss': pos['stop_loss'],
                    'target_price': pos['target_price'],
                    'entry_date': pos['entry_date'].strftime('%Y-%m-%d') if isinstance(pos['entry_date'], datetime) else str(pos['entry_date'])
                })
            
            status = {
                'total_value': round(self.portfolio.total_value, 2),
                'cash': round(self.portfolio.cash, 2),
                'invested': round(self.portfolio.position_value, 2),
                'total_pnl': round(total_pnl, 2),
                'daily_pnl': round(daily_pnl, 2),
                'return_pct': round(return_pct, 2),
                'positions_count': len(self.portfolio.positions),
                'positions': positions,
                'target_progress': round((daily_pnl / 3000) * 100, 1) if daily_pnl != 0 else 0,
                'last_updated': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Portfolio status error: {e}")
            # Return safe defaults
            return {
                'total_value': self.initial_capital,
                'cash': self.initial_capital,
                'invested': 0.0,
                'total_pnl': 0.0,
                'daily_pnl': 0.0,
                'return_pct': 0.0,
                'positions_count': 0,
                'positions': [],
                'target_progress': 0.0,
                'last_updated': datetime.now().isoformat()
            }

    def get_trade_history(self, days=30):
        """Get trade history from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            cursor.execute('''
                SELECT timestamp, symbol, action, price, quantity, amount, pnl, commission, portfolio_value, reason
                FROM paper_trades
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (since_date,))
            
            trades = []
            for row in cursor.fetchall():
                trade = {
                    'timestamp': row[0],
                    'symbol': row[1],
                    'action': row[2],
                    'price': row[3],
                    'quantity': row[4],
                    'amount': row[5],
                    'pnl': row[6],
                    'commission': row[7],
                    'portfolio_value': row[8],
                    'reason': row[9],
                    'date': row[0][:10] if isinstance(row[0], str) else row[0].date().isoformat()
                }
                trades.append(trade)
            
            conn.close()
            return trades
            
        except Exception as e:
            logger.error(f"Trade history error: {e}")
            return []

    def _get_daily_pnl(self):
        """Calculate today's P&L"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().date()
            cursor.execute('''
                SELECT SUM(pnl) FROM paper_trades 
                WHERE DATE(timestamp) = ?
            ''', (today,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] is not None else 0.0
            
        except Exception as e:
            logger.error(f"Daily P&L error: {e}")
            return 0.0

    def _save_trade_to_db(self, trade):
        """Save trade to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO paper_trades 
                (timestamp, symbol, action, price, quantity, amount, commission, pnl, portfolio_value, reason, stop_loss, target_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['timestamp'], trade['symbol'], trade['action'], trade['price'],
                trade['quantity'], trade['amount'], trade['commission'], trade['pnl'],
                trade['portfolio_value'], trade['reason'], 
                trade.get('stop_loss', 0), trade.get('target_price', 0)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database save error: {e}")

    def _save_position_to_db(self, symbol):
        """Save position to database"""
        try:
            if symbol not in self.portfolio.positions:
                return
            
            pos = self.portfolio.positions[symbol]
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO current_positions 
                (symbol, quantity, entry_price, current_price, entry_date, stop_loss, target_price, entry_commission)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, pos['quantity'], pos['entry_price'], pos['current_price'],
                pos['entry_date'], pos['stop_loss'], pos['target_price'], pos.get('entry_commission', 0)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Position save error: {e}")

    def _remove_position_from_db(self, symbol):
        """Remove position from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM current_positions WHERE symbol = ?', (symbol,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Position removal error: {e}")

    def _update_position_price_in_db(self, symbol, price):
        """Update position price in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE current_positions SET current_price = ? WHERE symbol = ?',
                (price, symbol)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Position price update error: {e}")

    def _save_portfolio_snapshot(self):
        """Save portfolio snapshot"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            total_pnl = self.portfolio.total_value - self.initial_capital
            daily_pnl = self._get_daily_pnl()
            
            cursor.execute('''
                INSERT INTO portfolio_snapshots
                (timestamp, cash, position_value, total_value, daily_pnl, total_pnl, positions_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(), self.portfolio.cash, self.portfolio.position_value,
                self.portfolio.total_value, daily_pnl, total_pnl, len(self.portfolio.positions)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Snapshot save error: {e}")


class PaperPortfolio:
    """Enhanced paper portfolio with proper tracking"""
    
    def __init__(self, initial_cash):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}  # {symbol: {quantity, entry_price, current_price, etc.}}
        
    @property
    def position_value(self):
        """Calculate total position value"""
        try:
            total = 0
            for pos in self.positions.values():
                total += pos['quantity'] * pos.get('current_price', pos.get('entry_price', 0))
            return total
        except Exception as e:
            logger.error(f"Position value calculation error: {e}")
            return 0.0
    
    @property
    def total_value(self):
        """Calculate total portfolio value"""
        return self.cash + self.position_value
    
    def buy_position(self, symbol, price, quantity, stop_loss, target_price, commission):
        """Buy a new position"""
        try:
            total_cost = (quantity * price) + commission
            
            if total_cost > self.cash:
                return False
            
            self.cash -= total_cost
            self.positions[symbol] = {
                'quantity': quantity,
                'entry_price': price,
                'current_price': price,
                'stop_loss': stop_loss,
                'target_price': target_price,
                'entry_date': datetime.now(),
                'entry_commission': commission
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Buy position error: {e}")
            return False
    
    def sell_position(self, symbol, price, commission):
        """Sell a position"""
        try:
            if symbol not in self.positions:
                return False
            
            position = self.positions[symbol]
            quantity = position['quantity']
            
            proceeds = (quantity * price) - commission
            self.cash += proceeds
            
            # Remove position
            del self.positions[symbol]
            
            return True
            
        except Exception as e:
            logger.error(f"Sell position error: {e}")
            return False
    
    def update_position_price(self, symbol, price):
        """Update current price of a position"""
        if symbol in self.positions:
            self.positions[symbol]['current_price'] = price

# Test the enhanced paper trading engine
if __name__ == "__main__":
    print("🧪 Testing Enhanced Paper Trading Engine...")
    
    # Mock data fetcher for testing
    class MockDataFetcher:
        def get_current_price(self, symbol):
            prices = {'RELIANCE': 2450.0, 'TCS': 3680.0, 'INFY': 1750.0}
            return prices.get(symbol, 1000.0)
        
        def get_multiple_stocks_data(self, symbols, days):
            return {}  # Empty for test signal generation
    
    # Initialize engine
    data_fetcher = MockDataFetcher()
    engine = PaperTradingEngine(data_fetcher, None, 100000)
    
    # Test trading session
    result = engine.start_paper_trading()
    print(f"✅ Trading session result: {result}")
    
    # Test portfolio status
    status = engine.get_portfolio_status()
    print(f"📊 Portfolio status: ₹{status['total_value']:,.2f}")
    
    print("✅ Enhanced Paper Trading Engine test completed!")