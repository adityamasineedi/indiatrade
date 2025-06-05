"""
Paper Trading Engine for Indian Stock Trading System
Simulates real trading without actual money to test strategies
"""
import pandas as pd
import numpy as np
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from config.settings import Config

logger = logging.getLogger(__name__)

class PaperTradingEngine:
    def __init__(self, data_fetcher, signal_generator):
        self.data_fetcher = data_fetcher
        self.signal_generator = signal_generator
        self.config = Config()
        self.portfolio = PaperPortfolio(self.config.INITIAL_CAPITAL)
        self.db_path = 'paper_trading.db'
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for paper trading"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    symbol TEXT,
                    action TEXT,
                    price REAL,
                    quantity INTEGER,
                    amount REAL,
                    commission REAL,
                    pnl REAL,
                    portfolio_value REAL,
                    reason TEXT,
                    stop_loss REAL,
                    target_price REAL
                )
            ''')
            
            # Create portfolio snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    cash REAL,
                    position_value REAL,
                    total_value REAL,
                    daily_pnl REAL,
                    total_pnl REAL,
                    positions_count INTEGER
                )
            ''')
            
            # Create signals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    symbol TEXT,
                    action TEXT,
                    confidence REAL,
                    price REAL,
                    reasons TEXT,
                    executed BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Paper trading database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    def start_paper_trading(self):
        """Start the paper trading session"""
        logger.info("Starting paper trading session")
        
        try:
            # Check if market is open
            if not self.data_fetcher.is_market_open():
                logger.info("Market is closed. Paper trading will simulate based on last available prices.")
            
            # Generate current signals
            current_signals = self._get_current_signals()
            
            # Execute signals
            executed_trades = self._execute_signals(current_signals)
            
            # Update portfolio
            self._update_portfolio_positions()
            
            # Save portfolio snapshot
            self._save_portfolio_snapshot()
            
            # Log session summary
            self._log_session_summary(executed_trades)
            
            return {
                'status': 'success',
                'signals_generated': len(current_signals),
                'trades_executed': len(executed_trades),
                'portfolio_value': self.portfolio.total_value,
                'cash': self.portfolio.cash,
                'positions': len(self.portfolio.positions)
            }
            
        except Exception as e:
            logger.error(f"Error in paper trading session: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_current_signals(self):
        """Get current trading signals"""
        try:
            # Get data for watchlist
            watchlist = self.config.WATCHLIST
            stocks_data = self.data_fetcher.get_multiple_stocks_data(watchlist, days=50)
            
            if not stocks_data:
                logger.warning("No stock data available for signal generation")
                return []
            
            # Generate signals
            signals = self.signal_generator.generate_signals(stocks_data)
            
            # Save signals to database
            self._save_signals_to_db(signals)
            
            logger.info(f"Generated {len(signals)} trading signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error getting current signals: {str(e)}")
            return []
    
    def _execute_signals(self, signals):
        """Execute trading signals"""
        executed_trades = []
        
        for signal in signals:
            try:
                if signal['action'] == 'BUY':
                    trade = self._execute_buy_signal(signal)
                elif signal['action'] == 'SELL':
                    trade = self._execute_sell_signal(signal)
                else:
                    continue  # Skip HOLD signals
                
                if trade:
                    executed_trades.append(trade)
                    self._mark_signal_executed(signal)
                    
            except Exception as e:
                logger.error(f"Error executing signal for {signal.get('symbol', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"Executed {len(executed_trades)} trades")
        return executed_trades
    
    def _execute_buy_signal(self, signal):
        """Execute a buy signal"""
        try:
            symbol = signal['symbol']
            price = signal['price']
            stop_loss = signal['stop_loss']
            target_price = signal['target_price']
            
            # Check if we already have a position
            if symbol in self.portfolio.positions:
                logger.info(f"Already have position in {symbol}, skipping buy signal")
                return None
            
            # Check if we've reached max positions
            if len(self.portfolio.positions) >= self.config.MAX_POSITIONS:
                logger.info(f"Max positions reached ({self.config.MAX_POSITIONS}), skipping buy signal")
                return None
            
            # Calculate position size
            risk_amount = self.portfolio.cash * (self.config.RISK_PER_TRADE / 100)
            stop_distance = max(price - stop_loss, price * 0.02)  # Minimum 2% stop
            quantity = int(risk_amount / stop_distance)
            
            # Calculate total cost including commission
            commission = price * quantity * (self.config.COMMISSION / 100)
            total_cost = (price * quantity) + commission
            
            # Check if we have enough cash
            if total_cost > self.portfolio.cash:
                # Adjust quantity to fit available cash
                available_for_stock = self.portfolio.cash * 0.95  # Keep 5% buffer
                quantity = int(available_for_stock / (price * (1 + self.config.COMMISSION / 100)))
                
                if quantity <= 0:
                    logger.warning(f"Insufficient cash for {symbol} buy signal")
                    return None
                
                commission = price * quantity * (self.config.COMMISSION / 100)
                total_cost = (price * quantity) + commission
            
            # Execute the trade
            success = self.portfolio.buy_position(
                symbol, price, quantity, stop_loss, target_price, commission
            )
            
            if success:
                trade = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': 'BUY',
                    'price': price,
                    'quantity': quantity,
                    'amount': price * quantity,
                    'commission': commission,
                    'pnl': 0,
                    'portfolio_value': self.portfolio.total_value,
                    'reason': ', '.join(signal.get('reasons', [])),
                    'stop_loss': stop_loss,
                    'target_price': target_price
                }
                
                self._save_trade_to_db(trade)
                logger.info(f"Bought {quantity} shares of {symbol} at ₹{price:.2f}")
                return trade
            else:
                logger.error(f"Failed to execute buy order for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing buy signal: {str(e)}")
            return None
    
    def _execute_sell_signal(self, signal):
        """Execute a sell signal"""
        try:
            symbol = signal['symbol']
            price = signal['price']
            
            # Check if we have a position to sell
            if symbol not in self.portfolio.positions:
                logger.info(f"No position in {symbol} to sell")
                return None
            
            position = self.portfolio.positions[symbol]
            quantity = position['quantity']
            
            # Calculate proceeds and commission
            gross_proceeds = price * quantity
            commission = gross_proceeds * (self.config.COMMISSION / 100)
            net_proceeds = gross_proceeds - commission
            
            # Calculate P&L
            cost_basis = position['entry_price'] * quantity + position['entry_commission']
            pnl = net_proceeds - cost_basis
            
            # Execute the trade
            success = self.portfolio.sell_position(symbol, price, commission)
            
            if success:
                trade = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': 'SELL',
                    'price': price,
                    'quantity': quantity,
                    'amount': gross_proceeds,
                    'commission': commission,
                    'pnl': pnl,
                    'portfolio_value': self.portfolio.total_value,
                    'reason': ', '.join(signal.get('reasons', [])),
                    'stop_loss': 0,
                    'target_price': 0
                }
                
                self._save_trade_to_db(trade)
                logger.info(f"Sold {quantity} shares of {symbol} at ₹{price:.2f} (P&L: ₹{pnl:.2f})")
                return trade
            else:
                logger.error(f"Failed to execute sell order for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing sell signal: {str(e)}")
            return None
    
    def _update_portfolio_positions(self):
        """Update current prices for all positions"""
        try:
            for symbol in list(self.portfolio.positions.keys()):
                current_price = self.data_fetcher.get_current_price(symbol)
                
                if current_price:
                    self.portfolio.update_position_price(symbol, current_price)
                    
                    # Check for automatic exit conditions
                    self._check_exit_conditions(symbol, current_price)
                else:
                    logger.warning(f"Could not get current price for {symbol}")
                    
        except Exception as e:
            logger.error(f"Error updating portfolio positions: {str(e)}")
    
    def _check_exit_conditions(self, symbol, current_price):
        """Check if position should be automatically exited"""
        try:
            position = self.portfolio.positions[symbol]
            
            # Check stop loss
            if current_price <= position['stop_loss']:
                self._auto_exit_position(symbol, current_price, "Stop loss triggered")
                return
            
            # Check target price
            if current_price >= position['target_price']:
                self._auto_exit_position(symbol, current_price, "Target price reached")
                return
            
            # Check maximum holding period (e.g., 10 days)
            entry_date = position['entry_date']
            if (datetime.now() - entry_date).days >= 10:
                self._auto_exit_position(symbol, current_price, "Maximum holding period reached")
                return
                
        except Exception as e:
            logger.error(f"Error checking exit conditions for {symbol}: {str(e)}")
    
    def _auto_exit_position(self, symbol, price, reason):
        """Automatically exit a position"""
        try:
            position = self.portfolio.positions[symbol]
            quantity = position['quantity']
            
            # Calculate proceeds and commission
            gross_proceeds = price * quantity
            commission = gross_proceeds * (self.config.COMMISSION / 100)
            net_proceeds = gross_proceeds - commission
            
            # Calculate P&L
            cost_basis = position['entry_price'] * quantity + position['entry_commission']
            pnl = net_proceeds - cost_basis
            
            # Execute the exit
            success = self.portfolio.sell_position(symbol, price, commission)
            
            if success:
                trade = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': 'SELL',
                    'price': price,
                    'quantity': quantity,
                    'amount': gross_proceeds,
                    'commission': commission,
                    'pnl': pnl,
                    'portfolio_value': self.portfolio.total_value,
                    'reason': reason,
                    'stop_loss': 0,
                    'target_price': 0
                }
                
                self._save_trade_to_db(trade)
                logger.info(f"Auto-exited {symbol} at ₹{price:.2f}: {reason} (P&L: ₹{pnl:.2f})")
                
        except Exception as e:
            logger.error(f"Error auto-exiting position: {str(e)}")
    
    def _save_trade_to_db(self, trade):
        """Save trade to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO paper_trades 
                (timestamp, symbol, action, price, quantity, amount, commission, pnl, 
                 portfolio_value, reason, stop_loss, target_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['timestamp'], trade['symbol'], trade['action'], trade['price'],
                trade['quantity'], trade['amount'], trade['commission'], trade['pnl'],
                trade['portfolio_value'], trade['reason'], trade['stop_loss'], trade['target_price']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving trade to database: {str(e)}")
    
    def _save_portfolio_snapshot(self):
        """Save current portfolio snapshot"""
        try:
            # Calculate daily P&L
            yesterday_value = self._get_yesterday_portfolio_value()
            daily_pnl = self.portfolio.total_value - yesterday_value
            total_pnl = self.portfolio.total_value - self.config.INITIAL_CAPITAL
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO portfolio_snapshots
                (timestamp, cash, position_value, total_value, daily_pnl, total_pnl, positions_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                self.portfolio.cash,
                self.portfolio.position_value,
                self.portfolio.total_value,
                daily_pnl,
                total_pnl,
                len(self.portfolio.positions)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving portfolio snapshot: {str(e)}")
    
    def _save_signals_to_db(self, signals):
        """Save signals to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for signal in signals:
                cursor.execute('''
                    INSERT INTO trading_signals
                    (timestamp, symbol, action, confidence, price, reasons)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    signal['symbol'],
                    signal['action'],
                    signal['confidence'],
                    signal['price'],
                    ', '.join(signal.get('reasons', []))
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving signals to database: {str(e)}")
    
    def _mark_signal_executed(self, signal):
        """Mark signal as executed in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE trading_signals 
                SET executed = TRUE 
                WHERE symbol = ? AND action = ? AND executed = FALSE
                ORDER BY timestamp DESC LIMIT 1
            ''', (signal['symbol'], signal['action']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error marking signal as executed: {str(e)}")
    
    def _get_yesterday_portfolio_value(self):
        """Get yesterday's portfolio value"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            yesterday = datetime.now() - timedelta(days=1)
            cursor.execute('''
                SELECT total_value FROM portfolio_snapshots 
                WHERE DATE(timestamp) = DATE(?)
                ORDER BY timestamp DESC LIMIT 1
            ''', (yesterday,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else self.config.INITIAL_CAPITAL
            
        except Exception as e:
            logger.error(f"Error getting yesterday's portfolio value: {str(e)}")
            return self.config.INITIAL_CAPITAL
    
    def _log_session_summary(self, executed_trades):
        """Log paper trading session summary"""
        try:
            total_pnl = self.portfolio.total_value - self.config.INITIAL_CAPITAL
            daily_pnl = sum(trade.get('pnl', 0) for trade in executed_trades)
            
            logger.info(f"""
            Paper Trading Session Summary:
            - Trades Executed: {len(executed_trades)}
            - Current Positions: {len(self.portfolio.positions)}
            - Cash: ₹{self.portfolio.cash:,.2f}
            - Position Value: ₹{self.portfolio.position_value:,.2f}
            - Total Portfolio: ₹{self.portfolio.total_value:,.2f}
            - Daily P&L: ₹{daily_pnl:,.2f}
            - Total P&L: ₹{total_pnl:,.2f}
            - Return: {(total_pnl/self.config.INITIAL_CAPITAL)*100:.2f}%
            """)
            
        except Exception as e:
            logger.error(f"Error logging session summary: {str(e)}")
    
    def get_portfolio_status(self):
        """Get current portfolio status"""
        try:
            # Initialize default values if not set
            if not hasattr(self, 'cash'):
                self.cash = 100000.0
            if not hasattr(self, 'positions'):
                self.positions = {}
            
            total_invested = sum(pos.get('value', 0) for pos in self.positions.values())
            total_value = self.cash + total_invested
            total_pnl = total_value - 100000.0  # Assuming 100k starting capital
            
            return {
                'total_value': total_value,
                'cash': self.cash,
                'invested': total_invested,
                'total_pnl': total_pnl,
                'daily_pnl': 0.0,  # Would need trade history to calculate
                'positions_count': len(self.positions),
                'return_pct': (total_pnl / 100000.0) * 100 if total_pnl != 0 else 0.0
            }
            
        except Exception as e:
            print(f"❌ Portfolio status error: {e}")
            return {
                'total_value': 100000.0,
                'cash': 100000.0,
                'invested': 0.0,
                'total_pnl': 0.0,
                'daily_pnl': 0.0,
                'positions_count': 0,
                'return_pct': 0.0
            }
    
    def get_trade_history(self, days=30):
        """Get trade history from the database for the last N days"""
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

            rows = cursor.fetchall()
            conn.close()

            history = []
            for row in rows:
                trade = {
                    'timestamp': datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f') if isinstance(row[0], str) else row[0],
                    'symbol': row[1],
                    'action': row[2],
                    'price': row[3],
                    'quantity': row[4],
                    'amount': row[5],
                    'pnl': row[6],
                    'commission': row[7],
                    'portfolio_value': row[8],
                    'reason': row[9],
                    'date': row[0].split(" ")[0] if isinstance(row[0], str) else row[0].date().isoformat()
                }
                history.append(trade)

            return history

        except Exception as e:
            logger.error(f"Error fetching trade history: {str(e)}")
            return []
    
    def execute_trade(self, signal):
        """Execute a trade based on signal"""
        try:
            if not signal or 'symbol' not in signal:
                return False
            
            symbol = signal['symbol']
            action = signal['action']
            price = signal.get('price', 0)
            quantity = signal.get('quantity', 10)
            
            print(f"📊 Executing {action} {quantity} shares of {symbol} at ₹{price:.2f}")
            
            # Simulate trade execution
            if action == 'BUY':
                cost = price * quantity
                if cost <= self.cash:
                    self.cash -= cost
                    # Add to positions (simplified)
                    print(f"✅ BUY order executed: {quantity} {symbol} @ ₹{price:.2f}")
                    return True
                else:
                    print(f"❌ Insufficient cash for BUY order")
                    return False
            
            elif action == 'SELL':
                # Simplified sell logic
                revenue = price * quantity
                self.cash += revenue
                print(f"✅ SELL order executed: {quantity} {symbol} @ ₹{price:.2f}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Trade execution error: {e}")
            return False
    

class PaperPortfolio:
    """Paper portfolio management"""
    
    def __init__(self, initial_cash):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}
        
    @property
    def position_value(self):
        """Calculate total position value"""
        return sum(
            pos['quantity'] * pos['current_price'] 
            for pos in self.positions.values()
        )
    
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
            logger.error(f"Error buying position: {str(e)}")
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
            logger.error(f"Error selling position: {str(e)}")
            return False
    
    def update_position_price(self, symbol, price):
        """Update current price of a position"""
        if symbol in self.positions:
            self.positions[symbol]['current_price'] = price