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
    def __init__(self, data_fetcher=None, signal_generator=None, initial_capital=None, config=None):
        """Enhanced constructor - FIXED VERSION"""
        
        # CRITICAL FIX: Set up configuration FIRST
        if config is not None:
            self.config = config
        else:
            try:
                from config.settings import Config
                self.config = Config()
            except Exception as e:
                logger.warning(f"Could not load Config: {e}")
                from types import SimpleNamespace
                self.config = SimpleNamespace()
                self.config.INITIAL_CAPITAL = 100000
                self.config.RISK_PER_TRADE = 2.0
                self.config.COMMISSION = 0.1
                self.config.MAX_POSITIONS = 5
                self.config.WATCHLIST = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
        
        # Set initial capital
        if initial_capital is not None:
            self.initial_capital = initial_capital
            self.config.INITIAL_CAPITAL = initial_capital
        else:
            self.initial_capital = getattr(self.config, 'INITIAL_CAPITAL', 100000)
        
        self.data_fetcher = data_fetcher
        self.signal_generator = signal_generator

        self.portfolio = PaperPortfolio(self.initial_capital)
        self.db_path = 'data/paper_trading.db'
        import os
        os.makedirs('data', exist_ok=True)
        self.init_database()
        logger.info(f"Enhanced Paper Trading Engine initialized with Rs.{self.initial_capital:,.2f}")
        print(f"✅ Enhanced Paper Trading Engine initialized with Rs.{self.initial_capital:,.2f}")

    def get_real_time_price(self, symbol):
        """Get real-time price from Yahoo Finance as fallback"""
        try:
            try:
                price = self.data_fetcher.get_current_price(symbol)
                if price and price > 0:
                    return float(price)
            except:
                pass
            try:
                import yfinance as yf
                import pandas as pd
                ticker = yf.Ticker(f"{symbol}.NS")
                data = ticker.history(period="1d", interval="1m")
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    if not pd.isna(current_price) and current_price > 0:
                        logger.info(f"Real-time price for {symbol}: Rs.{current_price:.2f} (Yahoo Finance)")
                        return float(current_price)
                data = ticker.history(period="2d", interval="1d")
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    logger.info(f"Daily price for {symbol}: Rs.{current_price:.2f} (Yahoo Finance)")
                    return float(current_price)
            except ImportError:
                logger.warning("yfinance not available, install with: pip install yfinance")
            except Exception as e:
                logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting real-time price for {symbol}: {e}")
            return None

    def init_database(self):
        """Initialize SQLite database for paper trading"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
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
            try:
                if not self.data_fetcher.is_market_open():
                    logger.info("Market is closed. Paper trading will simulate based on last available prices.")
            except:
                logger.info("Market status unknown, proceeding with trading session")
            current_signals = self._get_current_signals()
            executed_trades = self._execute_signals(current_signals)
            self._update_portfolio_positions()
            self._save_portfolio_snapshot()
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
            watchlist = self.config.WATCHLIST
            stocks_data = self.data_fetcher.get_multiple_stocks_data(watchlist, days=50)
            if not stocks_data:
                logger.warning("No stock data available for signal generation")
                return []
            signals = self.signal_generator.generate_signals(stocks_data)
            enhanced_signals = []
            for signal in signals:
                enhanced_signal = signal.copy()
                if 'stop_loss' not in enhanced_signal:
                    price = enhanced_signal.get('price', 0)
                    enhanced_signal['stop_loss'] = price * 0.95
                if 'target_price' not in enhanced_signal:
                    price = enhanced_signal.get('price', 0)
                    enhanced_signal['target_price'] = price * 1.10
                if 'reasons' not in enhanced_signal:
                    enhanced_signal['reasons'] = ['Signal generated']
                enhanced_signals.append(enhanced_signal)
            self._save_signals_to_db(enhanced_signals)
            logger.info(f"Generated {len(enhanced_signals)} trading signals")
            return enhanced_signals
        except Exception as e:
            logger.error(f"Error getting current signals: {str(e)}")
            return []
    
    def _execute_signals(self, signals):
        """Execute trading signals"""
        executed_trades = []
        for signal in signals:
            try:
                confidence = signal.get('confidence', 0)
                if confidence < 60:
                    logger.info(f"Skipping {signal.get('symbol')} signal with low confidence: {confidence}%")
                    continue
                if signal['action'] == 'BUY':
                    trade = self._execute_buy_signal(signal)
                elif signal['action'] == 'SELL':
                    trade = self._execute_sell_signal(signal)
                else:
                    continue
                if trade:
                    executed_trades.append(trade)
                    self._mark_signal_executed(signal)
            except Exception as e:
                logger.error(f"Error executing signal for {signal.get('symbol', 'unknown')}: {str(e)}")
                continue
        logger.info(f"Executed {len(executed_trades)} trades")
        return executed_trades
    
    def _execute_buy_signal(self, signal):
        """Execute a buy signal with enhanced error handling"""
        try:
            symbol = signal['symbol']
            price = signal.get('price', 0)
            stop_loss = signal.get('stop_loss', price * 0.95)
            target_price = signal.get('target_price', price * 1.10)
            real_time_price = self.get_real_time_price(symbol)
            if real_time_price:
                price = real_time_price
                stop_loss = price * 0.95
                target_price = price * 1.10
            if symbol in self.portfolio.positions:
                logger.info(f"Already have position in {symbol}, skipping buy signal")
                return None
            if len(self.portfolio.positions) >= self.config.MAX_POSITIONS:
                logger.info(f"Max positions reached ({self.config.MAX_POSITIONS}), skipping buy signal")
                return None
            risk_amount = self.portfolio.cash * (self.config.RISK_PER_TRADE / 100)
            stop_distance = max(price - stop_loss, price * 0.02)
            quantity = max(1, int(risk_amount / stop_distance))
            commission = price * quantity * (self.config.COMMISSION / 100)
            total_cost = (price * quantity) + commission
            if total_cost > self.portfolio.cash:
                available_for_stock = self.portfolio.cash * 0.95
                quantity = max(1, int(available_for_stock / (price * (1 + self.config.COMMISSION / 100))))
                if quantity <= 0:
                    logger.warning(f"Insufficient cash for {symbol} buy signal")
                    return None
                commission = price * quantity * (self.config.COMMISSION / 100)
                total_cost = (price * quantity) + commission
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
                logger.info(f"Bought {quantity} shares of {symbol} at Rs.{price:.2f}")
                print(f"✅ BUY EXECUTED: {quantity} {symbol} @ Rs.{price:.2f}")
                return trade
            else:
                logger.error(f"Failed to execute buy order for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error executing buy signal: {str(e)}")
            return None
    
    def _execute_sell_signal(self, signal):
        """Execute a sell signal with enhanced error handling"""
        try:
            symbol = signal['symbol']
            price = signal.get('price', 0)
            real_time_price = self.get_real_time_price(symbol)
            if real_time_price:
                price = real_time_price
            if symbol not in self.portfolio.positions:
                logger.info(f"No position in {symbol} to sell")
                return None
            position = self.portfolio.positions[symbol]
            quantity = position['quantity']
            gross_proceeds = price * quantity
            commission = gross_proceeds * (self.config.COMMISSION / 100)
            net_proceeds = gross_proceeds - commission
            cost_basis = position['entry_price'] * quantity + position['entry_commission']
            pnl = net_proceeds - cost_basis
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
                logger.info(f"Sold {quantity} shares of {symbol} at Rs.{price:.2f} (P&L: Rs.{pnl:.2f})")
                print(f"✅ SELL EXECUTED: {quantity} {symbol} @ Rs.{price:.2f} (P&L: Rs.{pnl:+.2f})")
                return trade
            else:
                logger.error(f"Failed to execute sell order for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error executing sell signal: {str(e)}")
            return None
    
    def _update_portfolio_positions(self):
        """Update current prices for all positions with real-time data"""
        try:
            for symbol in list(self.portfolio.positions.keys()):
                current_price = self.get_real_time_price(symbol)
                if current_price:
                    self.portfolio.update_position_price(symbol, current_price)
                    self._check_exit_conditions(symbol, current_price)
                else:
                    logger.warning(f"Could not get current price for {symbol}")
        except Exception as e:
            logger.error(f"Error updating portfolio positions: {str(e)}")
    
    def _check_exit_conditions(self, symbol, current_price):
        """Check if position should be automatically exited"""
        try:
            position = self.portfolio.positions[symbol]
            if current_price <= position['stop_loss']:
                self._auto_exit_position(symbol, current_price, "Stop loss triggered")
                return
            if current_price >= position['target_price']:
                self._auto_exit_position(symbol, current_price, "Target price reached")
                return
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
            gross_proceeds = price * quantity
            commission = gross_proceeds * (self.config.COMMISSION / 100)
            net_proceeds = gross_proceeds - commission
            cost_basis = position['entry_price'] * quantity + position['entry_commission']
            pnl = net_proceeds - cost_basis
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
                logger.info(f"Auto-exited {symbol} at Rs.{price:.2f}: {reason} (P&L: Rs.{pnl:.2f})")
                print(f"🔄 AUTO-EXIT: {symbol} @ Rs.{price:.2f} - {reason} (P&L: Rs.{pnl:+.2f})")
        except Exception as e:
            logger.error(f"Error auto-exiting position: {str(e)}")

    def execute_sample_trade(self):
        """Execute a sample trade for testing purposes"""
        try:
            sample_signal = {
                'symbol': 'RELIANCE',
                'action': 'BUY',
                'price': 2450.0,
                'confidence': 75,
                'reasons': ['RSI oversold', 'MACD bullish'],
                'stop_loss': 2350.0,
                'target_price': 2600.0
            }
            real_price = self.get_real_time_price('RELIANCE')
            if real_price:
                sample_signal['price'] = real_price
                sample_signal['stop_loss'] = real_price * 0.95
                sample_signal['target_price'] = real_price * 1.10
                print(f"📊 Using real-time price: Rs.{real_price:.2f} for sample trade")
            trade = self._execute_buy_signal(sample_signal)
            if trade:
                print(f"  ✅ Sample trade executed: BUY {trade['quantity']} shares of RELIANCE @ Rs.{trade['price']:.2f}")
                print(f"  💰 Total cost: Rs.{(trade['amount'] + trade['commission']):,.2f}")
                print(f"  🎯 Stop Loss: Rs.{trade['stop_loss']:.2f}")
                print(f"  🚀 Target: Rs.{trade['target_price']:.2f}")
                return True
            else:
                print(f"  ❌ Sample trade failed")
                return False
        except Exception as e:
            print(f"  ❌ Sample trade error: {e}")
            return False

    def get_portfolio_status(self):
        """Get current portfolio status with real-time values - FIXED VERSION"""
        try:
            # CRITICAL FIX: Ensure config exists
            if not hasattr(self, 'config') or self.config is None:
                try:
                    from config.settings import Config
                    self.config = Config()
                except:
                    from types import SimpleNamespace
                    self.config = SimpleNamespace()
                    self.config.INITIAL_CAPITAL = getattr(self, 'initial_capital', 100000)
            
            # Ensure required config attributes exist
            if not hasattr(self.config, 'INITIAL_CAPITAL'):
                self.config.INITIAL_CAPITAL = getattr(self, 'initial_capital', 100000)

            # Update positions if possible
            try:
                self._update_portfolio_positions()
            except Exception as e:
                logger.debug(f"Could not update portfolio positions: {e}")

            # Calculate metrics safely
            initial_capital = self.config.INITIAL_CAPITAL
            total_pnl = self.portfolio.total_value - initial_capital
            daily_pnl = self._get_daily_pnl()
            
            return {
                'total_value': round(self.portfolio.total_value, 2),
                'cash': round(self.portfolio.cash, 2),
                'invested': round(self.portfolio.position_value, 2),
                'total_pnl': round(total_pnl, 2),
                'daily_pnl': round(daily_pnl, 2),
                'positions_count': len(self.portfolio.positions),  # FIXED: was 'positions'
                'return_pct': round((total_pnl / initial_capital) * 100, 2) if initial_capital > 0 else 0,
                'target_progress': round((daily_pnl / 3000) * 100, 1) if daily_pnl != 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Portfolio status error: {e}")
            # Return safe fallback values
            return {
                'total_value': 100000.0,
                'cash': 100000.0,
                'invested': 0.0,
                'total_pnl': 0.0,
                'daily_pnl': 0.0,
                'positions_count': 0,  # FIXED: was 'positions'
                'return_pct': 0.0,
                'target_progress': 0.0
            }

    def _get_daily_pnl(self):
        """Calculate today's P&L from trades - FIXED VERSION"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get today's date range
            today = datetime.now().date()
            today_str = today.strftime('%Y-%m-%d')
            tomorrow_str = (today + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Use date range instead of DATE() function for better compatibility
            cursor.execute('''
                SELECT SUM(pnl) FROM paper_trades 
                WHERE timestamp >= ? AND timestamp < ?
            ''', (today_str, tomorrow_str))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] is not None else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating daily P&L: {e}")
            return 0.0

    def get_recent_trades(self, days=7):
        """Get recent trades from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            cursor.execute('''
                SELECT symbol, action, price, quantity, pnl, timestamp, reason
                FROM paper_trades 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (cutoff_date,))
            trades = []
            for row in cursor.fetchall():
                trades.append({
                    'symbol': row[0],
                    'action': row[1],
                    'price': row[2],
                    'quantity': row[3],
                    'pnl': row[4],
                    'timestamp': row[5],
                    'reason': row[6]
                })
            conn.close()
            return trades
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []

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
            summary = f"""
            Paper Trading Session Summary:
            - Trades Executed: {len(executed_trades)}
            - Current Positions: {len(self.portfolio.positions)}
            - Cash: Rs.{self.portfolio.cash:,.2f}
            - Position Value: Rs.{self.portfolio.position_value:,.2f}
            - Total Portfolio: Rs.{self.portfolio.total_value:,.2f}
            - Daily P&L: Rs.{daily_pnl:,.2f}
            - Total P&L: Rs.{total_pnl:,.2f}
            - Return: {(total_pnl/self.config.INITIAL_CAPITAL)*100:.2f}%
            """
            logger.info(summary)
            print("📊 Trading Session Summary:")
            print(f"   Trades Executed: {len(executed_trades)}")
            print(f"   Portfolio Value: Rs.{self.portfolio.total_value:,.2f}")
            print(f"   Daily P&L: Rs.{daily_pnl:+,.2f}")
        except Exception as e:
            logger.error(f"Error logging session summary: {str(e)}")

    def execute_trade(self, signal):
        """Execute a trade based on signal (compatibility method for tests)"""
        try:
            if not signal or 'symbol' not in signal:
                return False
            
            symbol = signal['symbol']
            action = signal['action']
            price = signal.get('price', 0)
            confidence = signal.get('confidence', 60)
            
            print(f"📊 Executing {action} for {symbol} at Rs.{price:.2f} (Confidence: {confidence}%)")
            
            # Create enhanced signal with required fields
            enhanced_signal = signal.copy()
            
            # Add missing fields if not present
            if 'stop_loss' not in enhanced_signal:
                enhanced_signal['stop_loss'] = price * 0.95  # 5% stop loss
            
            if 'target_price' not in enhanced_signal:
                enhanced_signal['target_price'] = price * 1.10  # 10% target
            
            if 'reasons' not in enhanced_signal:
                enhanced_signal['reasons'] = ['Test signal generated']
            
            # Get real-time price if possible
            real_time_price = self.get_real_time_price(symbol)
            if real_time_price:
                enhanced_signal['price'] = real_time_price
                enhanced_signal['stop_loss'] = real_time_price * 0.95
                enhanced_signal['target_price'] = real_time_price * 1.10
                print(f"📊 Updated to real-time price: Rs.{real_time_price:.2f}")
            
            # Execute the trade using existing methods
            if action == 'BUY':
                trade_result = self._execute_buy_signal(enhanced_signal)
            elif action == 'SELL':
                trade_result = self._execute_sell_signal(enhanced_signal)
            else:
                print(f"⚠️ Unknown action: {action}")
                return False
            
            if trade_result:
                print(f"✅ {action} order executed: {trade_result['quantity']} {symbol} @ Rs.{trade_result['price']:.2f}")
                return True
            else:
                print(f"❌ {action} order failed for {symbol}")
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
        try:
            return sum(
                pos['quantity'] * pos.get('current_price', pos.get('entry_price', 0))
                for pos in self.positions.values()
            )
        except Exception as e:
            logger.error(f"Error calculating position value: {e}")
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
            del self.positions[symbol]
            return True
        except Exception as e:
            logger.error(f"Error selling position: {str(e)}")
            return False
    
    def update_position_price(self, symbol, price):
        """Update current price of a position"""
        if symbol in self.positions:
            self.positions[symbol]['current_price'] = price

# DO NOT ADD ANY INITIALIZATION CODE AT MODULE LEVEL
# Classes should be instantiated in main.py, not in this file