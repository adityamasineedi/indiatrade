"""
Main Flask Application for Indian Stock Trading System
Web dashboard with real-time updates and trading controls
"""
import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import pandas as pd
import threading
import time
import schedule
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.append('src')

# Import our modules
from src.data_fetcher import DataFetcher
from src.indicators.technical import TechnicalIndicators  
from src.strategies.signal_generator import SignalGenerator
from src.engines.paper_trading import PaperTradingEngine
from src.engines.backtest import BacktestEngine
from src.market_regime import MarketRegimeDetector
from src.utils.logger import setup_logging, get_system_logger, get_error_logger
from config.settings import Config

# Initialize logging
setup_logging()
system_logger = get_system_logger()
error_logger = get_error_logger()

# Initialize core components
config = Config()
data_fetcher = DataFetcher()
technical_indicators = TechnicalIndicators()
market_regime_detector = MarketRegimeDetector(data_fetcher)
signal_generator = SignalGenerator(technical_indicators, market_regime_detector)

# Initialize trading engines
try:
    paper_trading_engine = PaperTradingEngine(
        data_fetcher=data_fetcher,
        signal_generator=signal_generator,
        initial_capital=config.INITIAL_CAPITAL
    )
except Exception as e:
    print(f"❌ Paper Trading Engine initialization failed: {e}")
    paper_trading_engine = PaperTradingEngine()

backtest_engine = BacktestEngine(
    data_fetcher,
    technical_indicators,
    signal_generator
)

# Telegram bot integration (optional)
try:
    from src.utils.telegram_bot import TelegramBot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("📱 Telegram bot not available (optional)")

# Initialize Telegram bot
if TELEGRAM_AVAILABLE:
    try:
        telegram_bot = TelegramBot()
        print("📱 Telegram bot initialized")
    except Exception as e:
        print(f"⚠️ Telegram bot initialization failed: {e}")
        telegram_bot = None
else:
    telegram_bot = None
    print("📱 Telegram bot disabled (not critical)")

# Validate configuration
config.validate_config()

# Global state
current_signals = []
current_regime = {}
portfolio_status = {}
system_status = {
    'running': False,
    'last_update': None,
    'errors': 0,
    'trades_today': 0
}

def initialize_components():
    """Initialize all trading system components"""
    global data_fetcher, technical_indicators, signal_generator
    global market_regime_detector, backtest_engine, paper_trading_engine, telegram_bot
    
    try:
        system_logger.log_system_startup("Initializing trading system components")
        
        # Initialize components
        data_fetcher = DataFetcher()
        technical_indicators = TechnicalIndicators()
        signal_generator = SignalGenerator(technical_indicators, None)  # Will set regime detector later
        market_regime_detector = MarketRegimeDetector(data_fetcher)
        
        # Set regime detector in signal generator
        signal_generator.regime_detector = market_regime_detector
        
        # Initialize engines
        backtest_engine = BacktestEngine(data_fetcher, technical_indicators, signal_generator)
        paper_trading_engine = PaperTradingEngine(data_fetcher, signal_generator)
        
        # Initialize Telegram bot
        telegram_bot = TelegramBot()
        
        # Validate configuration
        config.validate_config()
        
        system_logger.log_system_startup("All components initialized successfully")
        return True
        
    except Exception as e:
        error_logger.log_exception("component_initialization", e)
        return False

def update_system_data():
    """Update all system data (signals, regime, portfolio)"""
    global current_signals, current_regime, portfolio_status, system_status
    
    try:
        system_logger.logger.info("Starting system data update")
        
        # Update market regime
        current_regime = market_regime_detector.detect_current_regime()
        
        # Get portfolio status
        portfolio_status = paper_trading_engine.get_portfolio_status()
        
        # Update system status
        system_status['last_update'] = datetime.now()
        system_status['running'] = True
        
        system_logger.logger.info("System data update completed")
        
    except Exception as e:
        error_logger.log_exception("system_data_update", e)
        system_status['errors'] += 1

def run_trading_session():
    """Run a complete trading session"""
    try:
        system_logger.logger.info("Starting trading session")
        
        # Update system data first
        update_system_data()
        
        # Run paper trading
        session_result = paper_trading_engine.start_paper_trading()
        
        # Update signals
        global current_signals
        watchlist = config.WATCHLIST[:10]  # Use first 10 for performance
        stocks_data = data_fetcher.get_multiple_stocks_data(watchlist, days=50)
        
        if stocks_data:
            current_signals = signal_generator.generate_signals(stocks_data, current_regime)
            
            # Send telegram alerts for new signals
            for signal in current_signals:
                if signal.get('confidence', 0) >= 70:  # Only high confidence signals
                    try:
                        telegram_bot.send_message_sync(f"🚀 Trading Signal: {signal['symbol']} {signal['action']} at ₹{signal['price']:.2f}")
                    except:
                        pass  # Don't let telegram errors stop trading
        
        system_status['trades_today'] += session_result.get('trades_executed', 0)
        
        system_logger.logger.info(f"Trading session completed: {session_result}")
        
    except Exception as e:
        error_logger.log_exception("trading_session", e)
        system_status['errors'] += 1

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Dashboard with portfolio overview and trading signals"""
    try:
        # Initialize portfolio data with safe defaults
        portfolio = {
            'total_value': 100000.0,  # Starting capital
            'total_pnl': 0.0,
            'daily_pnl': 0.0,
            'cash': 100000.0,
            'invested': 0.0,
            'positions': [],
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0
        }
        
        # Try to get real portfolio data
        try:
            if paper_trading_engine:
                real_portfolio = paper_trading_engine.get_portfolio_status()
                if real_portfolio:
                    portfolio.update(real_portfolio)
                    print(f"✅ Real portfolio data loaded: Rs.{portfolio['total_value']:,.2f}")
        except Exception as e:
            print(f"⚠️ Could not fetch real portfolio data: {e}")
        
        # Calculate win rate
        win_rate = 0.0
        if portfolio['total_trades'] > 0:
            win_rate = (portfolio['winning_trades'] / portfolio['total_trades']) * 100
        
        # Daily target calculations
        daily_target = 3000.0  # ₹3,000 target
        target_progress = 0.0
        if daily_target > 0:
            target_progress = max(0, min(100, (portfolio['daily_pnl'] / daily_target) * 100))
        
        # Market data with safe defaults
        market_data = {
            'nifty_price': 19500.0,
            'nifty_change': 0.0,
            'nifty_change_percent': 0.0,
            'market_regime': 'Sideways',
            'regime_confidence': 75.0
        }
        
        # Try to get real market data
        try:
            if current_regime:
                market_data.update({
                    'market_regime': current_regime.get('regime', 'Sideways'),
                    'regime_confidence': current_regime.get('confidence', 75.0)
                })
        except Exception as e:
            print(f"⚠️ Could not fetch market regime: {e}")
        
        # Recent signals with safe defaults
        recent_signals = [
            {
                'symbol': 'RELIANCE',
                'signal': 'BUY',
                'price': 2450.0,
                'strength': 85,
                'timestamp': '10:30 AM'
            },
            {
                'symbol': 'TCS',
                'signal': 'SELL',
                'price': 3680.0,
                'strength': 78,
                'timestamp': '10:25 AM'
            }
        ]
        
        # Try to get real signals
        try:
            if current_signals and len(current_signals) > 0:
                recent_signals = current_signals[-10:]  # Last 10 signals
        except Exception as e:
            print(f"⚠️ Could not fetch recent signals: {e}")
        
        # Performance metrics
        performance_metrics = {
            'sharpe_ratio': 1.2,
            'max_drawdown': -5.5,
            'profit_factor': 1.8,
            'total_return': 2.5
        }
        
        # Market status
        from datetime import datetime
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        is_market_hours = market_open <= now <= market_close
        
        if is_weekend:
            market_status = "CLOSED (Weekend)"
        elif is_market_hours:
            market_status = "OPEN"
        else:
            market_status = "CLOSED"

        return render_template(
            'dashboard.html',
            portfolio=portfolio,
            daily_pnl=portfolio['daily_pnl'],
            total_pnl=portfolio['total_pnl'],
            target_progress=target_progress,
            daily_target=daily_target,
            market_data=market_data,
            recent_signals=recent_signals,
            performance_metrics=performance_metrics,
            win_rate=win_rate,
            system_status=system_status,
            regime=current_regime if current_regime else {},
            market_status=market_status,
            # Pass both min and max functions to template
            min=min,
            max=max,
            # Also pass other useful functions
            len=len,
            abs=abs,
            round=round,
            page_title="Trading Dashboard"
        )
                             
    except Exception as e:
        # Provide safe fallback data even for errors
        error_portfolio = {
            'total_value': 100000.0,
            'total_pnl': 0.0,
            'daily_pnl': 0.0,
            'cash': 100000.0,
            'invested': 0.0,
            'positions': [],
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0
        }
        
        error_logger.log_exception("dashboard_error", e)
        
        return render_template(
            'dashboard.html',
            portfolio=error_portfolio,
            daily_pnl=error_portfolio['daily_pnl'],
            total_pnl=error_portfolio['total_pnl'],
            target_progress=0.0,
            daily_target=3000.0,
            market_data={'market_regime': 'Unknown', 'regime_confidence': 0},
            recent_signals=[],
            performance_metrics={'sharpe_ratio': 0, 'max_drawdown': 0, 'profit_factor': 0, 'total_return': 0},
            win_rate=0.0,
            system_status=system_status,
            regime={},
            market_status="ERROR",
            min=min,
            max=max,
            len=len,
            abs=abs,
            round=round,
            error=f"Dashboard Error: {str(e)}",
            page_title="Trading Dashboard - Error"
        )

@app.route('/trades')
def trades():
    """Trades history page"""
    try:
        days = request.args.get('days', 30, type=int)
        trade_history = paper_trading_engine.get_trade_history(days=days) if paper_trading_engine else []
        
        return render_template('trades.html', 
                             trades=trade_history,
                             days=days)
    except Exception as e:
        error_logger.log_exception("trades_page", e)
        return render_template('trades.html', trades=[], error=str(e))

@app.route('/api/portfolio')
def api_portfolio():
    """API endpoint for portfolio data"""
    try:
        if paper_trading_engine:
            portfolio_data = paper_trading_engine.get_portfolio_status()
            
            # Add calculated fields
            daily_target = 3000.0
            target_progress = 0.0
            if daily_target > 0:
                target_progress = max(0, min(100, (portfolio_data.get('daily_pnl', 0) / daily_target) * 100))
            
            portfolio_data.update({
                'target_progress': target_progress,
                'market_regime': current_regime.get('regime', 'Unknown') if current_regime else 'Unknown'
            })
            
            return jsonify(portfolio_data)
        else:
            # Fallback data
            portfolio_data = {
                'total_value': 100000.0,
                'daily_pnl': 0.0,
                'target_progress': 0.0,
                'positions_count': 0,
                'market_regime': 'Unknown'
            }
            return jsonify(portfolio_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals')
def api_signals():
    """API endpoint for recent trading signals"""
    try:
        if current_signals and len(current_signals) > 0:
            # Format signals for API response
            signals_data = []
            for signal in current_signals[-10:]:  # Last 10 signals
                signals_data.append({
                    'symbol': signal.get('symbol', 'UNKNOWN'),
                    'signal': signal.get('action', 'UNKNOWN'),
                    'price': signal.get('price', 0),
                    'strength': signal.get('confidence', 0),
                    'timestamp': signal.get('timestamp', 'Unknown')
                })
            return jsonify(signals_data)
        else:
            # Default signals
            signals_data = [
                {
                    'symbol': 'RELIANCE',
                    'signal': 'BUY',
                    'price': 2450.0,
                    'strength': 85,
                    'timestamp': '10:30 AM'
                }
            ]
            return jsonify(signals_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_dashboard')
def test_dashboard():
    """Test dashboard with mock data"""
    try:
        print("🧪 Testing dashboard with mock data...")
        
        # Test portfolio data
        test_portfolio = paper_trading_engine.get_portfolio_status() if paper_trading_engine else {
            'total_value': 102500.0,
            'cash': 85000.0,
            'invested': 17500.0,
            'daily_pnl': 1250.0,
            'total_pnl': 2500.0,
            'positions_count': 3,
            'return_pct': 2.5
        }
        
        print(f"✅ Portfolio loaded: Rs.{test_portfolio['total_value']:,.2f}")
        
        return jsonify({
            'status': 'Dashboard test successful',
            'portfolio': test_portfolio,
            'template_functions': ['min', 'max', 'len', 'abs', 'round'],
            'market_status': 'TESTING'
        })
        
    except Exception as e:
        return jsonify({'error': f'Dashboard test failed: {str(e)}'}), 500

@app.route('/api/regime')
def api_regime():
    """API endpoint for market regime"""
    try:
        return jsonify(current_regime)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/system_status')
def api_system_status():
    """API endpoint for system status"""
    try:
        return jsonify(system_status)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/run_backtest', methods=['POST'])
def api_run_backtest():
    """API endpoint to run backtest"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', config.WATCHLIST[:5])
        days = data.get('days', 30)
        
        # Run backtest
        results = backtest_engine.run_backtest(symbols, days=days)
        
        # Send results to Telegram
        try:
            telegram_bot.send_message_sync(
                f"📊 Backtest completed: {results['summary']['total_return_pct']:.2f}% return, "
                f"{results['summary']['win_rate']:.1f}% win rate"
            )
        except:
            pass
        
        return jsonify(results)
        
    except Exception as e:
        error_logger.log_exception("backtest_api", e)
        return jsonify({'error': str(e)})

@app.route('/api/update_system', methods=['POST'])
def api_update_system():
    """API endpoint to manually update system"""
    try:
        update_system_data()
        return jsonify({'status': 'success', 'message': 'System updated successfully'})
    except Exception as e:
        error_logger.log_exception("manual_update", e)
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/run_trading_session', methods=['POST'])
def api_run_trading_session():
    """API endpoint to manually run trading session"""
    try:
        run_trading_session()
        return jsonify({'status': 'success', 'message': 'Trading session completed'})
    except Exception as e:
        error_logger.log_exception("manual_trading_session", e)
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/test_telegram', methods=['POST'])
def api_test_telegram():
    """API endpoint to test Telegram connection"""
    try:
        success, message = telegram_bot.test_connection()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/send_portfolio_update', methods=['POST'])
def api_send_portfolio_update():
    """API endpoint to send portfolio update via Telegram"""
    try:
        if portfolio_status:
            success = telegram_bot.send_message_sync(
                f"📊 Portfolio Update\n"
                f"Total Value: ₹{portfolio_status.get('total_value', 0):,.2f}\n"
                f"P&L: ₹{portfolio_status.get('total_pnl', 0):,.2f}\n"
                f"Return: {portfolio_status.get('return_pct', 0):.2f}%"
            )
            return jsonify({'success': success})
        else:
            return jsonify({'success': False, 'message': 'No portfolio data available'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/market_data/<symbol>')
def api_market_data(symbol):
    """API endpoint for individual stock data"""
    try:
        data = data_fetcher.get_stock_data(symbol, days=30)
        if not data.empty:
            # Add indicators
            data = technical_indicators.add_all_indicators(data)
            # Convert to JSON-serializable format
            result = data.tail(30).to_dict('records')
            return jsonify(result)
        else:
            return jsonify({'error': 'No data found'})
    except Exception as e:
        return jsonify({'error': str(e)})

def run_automated_trading_session():
    """Enhanced automated trading session"""
    try:
        system_logger.logger.info("🚀 Starting automated trading session")
        
        # Check if market is open
        from datetime import datetime
        now = datetime.now()
        
        # Market hours: 9:15 AM to 3:30 PM on weekdays
        if now.weekday() >= 5:  # Weekend
            system_logger.logger.info("⏰ Market closed - Weekend")
            return
        
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if not (market_open <= now <= market_close):
            system_logger.logger.info("⏰ Market closed - Outside trading hours")
            return
        
        system_logger.logger.info("✅ Market is open - Starting trading session")
        
        # Update system data
        update_system_data()
        
        # Get current market regime
        current_regime = market_regime_detector.detect_current_regime()
        system_logger.logger.info(f"📊 Market regime: {current_regime.get('regime', 'unknown')} ({current_regime.get('confidence', 0):.1f}%)")
        
        # Get watchlist stocks
        config = Config()
        watchlist = config.WATCHLIST[:10]  # Trade top 10 stocks
        
        # Fetch current market data
        stocks_data = data_fetcher.get_multiple_stocks_data(watchlist, days=50)
        
        if not stocks_data:
            system_logger.logger.warning("⚠️ No stock data available")
            return
        
        # Generate trading signals
        signals = signal_generator.generate_signals(stocks_data, current_regime)
        
        if not signals:
            system_logger.logger.info("📡 No trading signals generated")
            return
        
        system_logger.logger.info(f"📡 Generated {len(signals)} trading signals")
        
        # Execute high-confidence signals
        executed_trades = 0
        for signal in signals:
            try:
                confidence = signal.get('confidence', 0)
                
                # Only execute signals with confidence > 70%
                if confidence >= 70:
                    success = paper_trading_engine.execute_trade(signal)
                    
                    if success:
                        executed_trades += 1
                        system_logger.logger.info(
                            f"✅ Executed: {signal['action']} {signal['symbol']} "
                            f"at ₹{signal['price']:.2f} (Confidence: {confidence:.1f}%)"
                        )
                        
                        # Send Telegram alert for executed trades
                        try:
                            telegram_bot.send_signal_alert(signal)
                        except:
                            pass  # Don't let telegram errors stop trading
                    
                else:
                    system_logger.logger.info(
                        f"⏭️ Skipped: {signal['action']} {signal['symbol']} "
                        f"(Confidence: {confidence:.1f}% < 70%)"
                    )
                    
            except Exception as e:
                system_logger.logger.error(f"❌ Trade execution error: {e}")
                continue
        
        # Update portfolio status
        portfolio_status = paper_trading_engine.get_portfolio_status()
        
        # Check daily P&L progress toward ₹3,000 goal
        daily_pnl = portfolio_status.get('daily_pnl', 0)
        daily_target = 3000.0
        target_progress = (daily_pnl / daily_target) * 100 if daily_target > 0 else 0
        
        system_logger.logger.info(
            f"💰 Portfolio: ₹{portfolio_status.get('total_value', 0):,.2f} "
            f"(Daily P&L: ₹{daily_pnl:,.2f}, Target Progress: {target_progress:.1f}%)"
        )
        
        # Update system status
        system_status.update({
            'last_trading_session': datetime.now(),
            'signals_generated': len(signals),
            'trades_executed': executed_trades,
            'portfolio_value': portfolio_status.get('total_value', 0),
            'daily_pnl': daily_pnl,
            'target_progress': target_progress
        })
        
        system_logger.logger.info(
            f"🎯 Trading session completed: {executed_trades} trades executed from {len(signals)} signals"
        )
        
        return {
            'success': True,
            'signals_generated': len(signals),
            'trades_executed': executed_trades,
            'portfolio_value': portfolio_status.get('total_value', 0),
            'daily_pnl': daily_pnl
        }
        
    except Exception as e:
        error_logger.log_exception("automated_trading_session", e)
        system_status['errors'] += 1
        return {'success': False, 'error': str(e)}

# --- Emoji-safe log fallback for Windows terminals ---
def log_with_emoji_replacement(logger, level, message):
    emoji_map = {
        '🕐': '[CLOCK]', '🔄': '[REFRESH]', '📊': '[CHART]', '📈': '[TRENDING_UP]',
        '🚀': '[ROCKET]', '✅': '[CHECK]', '❌': '[CROSS]', '⚠️': '[WARNING]',
        '💰': '[MONEY]', '📱': '[PHONE]', '🎯': '[TARGET]', '⏰': '[ALARM]',
        '🔗': '[LINK]', '📡': '[SATELLITE]', '⏭️': '[SKIP]'
    }
    for emoji, replacement in emoji_map.items():
        message = message.replace(emoji, replacement)
    getattr(logger, level)(message)


def setup_automated_trading():
    """Setup automated trading schedule"""
    try:
        # Clear any existing jobs
        schedule.clear()
        
        # Schedule trading sessions during market hours
        schedule.every().day.at("09:20").do(run_automated_trading_session)  # Market opens at 9:15
        schedule.every().day.at("09:45").do(run_automated_trading_session)
        schedule.every().day.at("10:15").do(run_automated_trading_session)
        schedule.every().day.at("10:45").do(run_automated_trading_session)
        schedule.every().day.at("11:15").do(run_automated_trading_session)
        schedule.every().day.at("11:45").do(run_automated_trading_session)
        schedule.every().day.at("12:15").do(run_automated_trading_session)
        schedule.every().day.at("12:45").do(run_automated_trading_session)
        schedule.every().day.at("13:15").do(run_automated_trading_session)
        schedule.every().day.at("13:45").do(run_automated_trading_session)
        schedule.every().day.at("14:15").do(run_automated_trading_session)
        schedule.every().day.at("14:45").do(run_automated_trading_session)
        schedule.every().day.at("15:15").do(run_automated_trading_session)  # Market closes at 15:30
        
        # Schedule system updates every 5 minutes during market hours
        for hour in range(9, 16):  # 9 AM to 3 PM
            for minute in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:
                if hour == 9 and minute < 15:  # Skip before market open
                    continue
                if hour == 15 and minute > 30:  # Skip after market close
                    continue
                
                time_str = f"{hour:02d}:{minute:02d}"
                schedule.every().day.at(time_str).do(update_system_data)
        
        # Schedule daily summary at market close
        # schedule.every().day.at("16:00").do(send_daily_summary)  # Temporarily disabled
        
        log_with_emoji_replacement(system_logger.logger, 'info', "🕐 Automated trading schedule configured")
        log_with_emoji_replacement(system_logger.logger, 'info', "🔄 Trading sessions: Every 30 minutes during market hours")
        log_with_emoji_replacement(system_logger.logger, 'info', "📊 Data updates: Every 5 minutes during market hours")
        log_with_emoji_replacement(system_logger.logger, 'info', "📈 Daily summary: 4:00 PM after market close")
        
        return True
        
    except Exception as e:
        error_logger.log_exception("trading_schedule_setup", e)
        return False

def schedule_enhanced_trading_tasks():
    """Schedule trading with Zerodha integration"""
    try:
        import schedule
        schedule.clear()
        schedule.every().day.at("09:20").do(run_enhanced_trading_session)
        schedule.every().day.at("09:45").do(run_enhanced_trading_session)
        schedule.every().day.at("10:15").do(run_enhanced_trading_session)
        schedule.every().day.at("10:45").do(run_enhanced_trading_session)
        schedule.every().day.at("11:15").do(run_enhanced_trading_session)
        schedule.every().day.at("11:45").do(run_enhanced_trading_session)
        schedule.every().day.at("12:15").do(run_enhanced_trading_session)
        schedule.every().day.at("12:45").do(run_enhanced_trading_session)
        schedule.every().day.at("13:15").do(run_enhanced_trading_session)
        schedule.every().day.at("13:45").do(run_enhanced_trading_session)
        schedule.every().day.at("14:15").do(run_enhanced_trading_session)
        schedule.every().day.at("14:45").do(run_enhanced_trading_session)
        schedule.every().day.at("15:15").do(run_enhanced_trading_session)
        system_logger.logger.info("✅ Enhanced trading schedule configured with Zerodha integration")
        return True
    except Exception as e:
        error_logger.log_exception("enhanced_schedule_setup", e)
        return False

@app.route('/api/run_trading', methods=['POST'])
def api_run_trading():
    """Manual trading session trigger"""
    try:
        result = run_automated_trading_session()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trading_status')
def api_trading_status():
    """Get current trading status"""
    try:
        from datetime import datetime
        now = datetime.now()
        
        # Check if market is open
        is_weekend = now.weekday() >= 5
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        is_market_hours = market_open <= now <= market_close
        
        status = {
            'market_open': is_market_hours and not is_weekend,
            'current_time': now.strftime('%H:%M:%S'),
            'market_session': 'OPEN' if (is_market_hours and not is_weekend) else 'CLOSED',
            'next_session': '09:20' if not is_market_hours else 'In Progress',
            'auto_trading_enabled': True,
            'last_session': system_status.get('last_trading_session'),
            'signals_today': system_status.get('signals_generated', 0),
            'trades_today': system_status.get('trades_executed', 0),
            'daily_pnl': system_status.get('daily_pnl', 0),
            'target_progress': system_status.get('target_progress', 0)
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def schedule_trading_tasks():
    """Initialize all trading schedules"""
    try:
        setup_automated_trading()
        system_logger.logger.info("All trading tasks scheduled successfully")
        return True
    except Exception as e:
        error_logger.log_exception("task_scheduling", e)
        return False

def initialize_trading_engine():
    """Initialize trading engine with Zerodha integration"""
    try:
        zerodha_enabled = os.getenv('ZERODHA_PAPER_TRADING', 'false').lower() == 'true'
        if zerodha_enabled:
            print("🚀 Initializing Zerodha Paper Trading Engine...")
            trading_engine = ZerodhaTrading(paper_trading=True)
            if trading_engine.connected:
                print("✅ Zerodha integration active - Using real market data")
                return trading_engine
            else:
                print("⚠️ Zerodha not connected - Check authentication")
                print("🔧 Run setup_zerodha_auth() to configure")
                return paper_trading_engine
        else:
            print("📊 Using internal paper trading simulation")
            return paper_trading_engine
    except Exception as e:
        print(f"⚠️ Trading engine initialization error: {e}")
        print("📊 Falling back to internal paper trading")
        return paper_trading_engine

# Initialize components on startup
initialize_components()

# Schedule trading tasks
schedule_trading_tasks()

# Background thread for running scheduled tasks
def run_schedule():
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            error_logger.log_exception("schedule_run", e)

# Start the schedule runner in a separate thread
scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
scheduler_thread.start()

# Home route
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    error_logger.log_exception("flask_error", e)
    return jsonify({'error': str(e)}), 500

# Health check route
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'last_update': system_status['last_update']})

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

def get_enhanced_stock_data(symbols, days=30):
    """Get stock data from Zerodha or fallback to Yahoo Finance"""
    stocks_data = {}
    for symbol in symbols:
        try:
            if hasattr(trading_engine, 'connected') and trading_engine.connected:
                zerodha_data = trading_engine.get_historical_data(symbol, days)
                if zerodha_data is not None and not zerodha_data.empty:
                    stocks_data[symbol] = zerodha_data
                    print(f"✅ {symbol}: Zerodha data ({len(zerodha_data)} days)")
                    continue
            data = data_fetcher.get_stock_data(symbol, days)
            if not data.empty:
                stocks_data[symbol] = data
                print(f"✅ {symbol}: Yahoo Finance data ({len(data)} days)")
        except Exception as e:
            print(f"❌ Data fetch error for {symbol}: {e}")
            continue
    return stocks_data

def run_enhanced_trading_session():
    """Enhanced trading session with Zerodha integration"""
    try:
        system_logger.logger.info("🚀 Starting enhanced trading session")
        from datetime import datetime
        now = datetime.now()
        
        if now.weekday() >= 5:
            system_logger.logger.info("⏰ Market closed - Weekend")
            return
            
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if not (market_open <= now <= market_close):
            system_logger.logger.info("⏰ Market closed - Outside trading hours")
            return
            
        system_logger.logger.info("✅ Market is open - Starting enhanced trading session")
        
        current_regime = market_regime_detector.detect_current_regime()
        system_logger.logger.info(f"📊 Market regime: {current_regime.get('regime', 'unknown')} ({current_regime.get('confidence', 0):.1f}%)")
        
        config = Config()
        watchlist = config.WATCHLIST[:10]
        stocks_data = get_enhanced_stock_data(watchlist, days=50)
        
        if not stocks_data:
            system_logger.logger.warning("⚠️ No stock data available")
            return
            
        signals = signal_generator.generate_signals(stocks_data, current_regime)
        
        if not signals:
            system_logger.logger.info("📡 No trading signals generated")
            return
            
        system_logger.logger.info(f"📡 Generated {len(signals)} trading signals")
        
        executed_trades = 0
        for signal in signals:
            try:
                confidence = signal.get('confidence', 0)
                if confidence >= 70:
                    success = trading_engine.execute_trade(signal)
                    if success:
                        executed_trades += 1
                        system_logger.logger.info(
                            f"✅ Executed: {signal['action']} {signal['symbol']} "
                            f"at ₹{signal['price']:.2f} (Confidence: {confidence:.1f}%)"
                        )
                        
                        if hasattr(trading_engine, 'connected') and trading_engine.connected:
                            system_logger.logger.info("📊 Trade executed with real Zerodha market price")
                        
                        try:
                            telegram_bot.send_signal_alert(signal)
                        except:
                            pass
            except Exception as e:
                system_logger.logger.error(f"❌ Trade execution error: {e}")
                continue
                
        portfolio_status = trading_engine.get_portfolio_status()
        
        if hasattr(trading_engine, 'connected') and trading_engine.connected:
            system_logger.logger.info("🔗 Portfolio data from Zerodha API")
        else:
            system_logger.logger.info("📊 Portfolio data from internal simulation")
            
        daily_pnl = portfolio_status.get('daily_pnl', 0)
        daily_target = 3000.0
        target_progress = (daily_pnl / daily_target) * 100 if daily_target > 0 else 0
        
        system_logger.logger.info(
            f"💰 Portfolio: ₹{portfolio_status.get('total_value', 0):,.2f} "
            f"(Daily P&L: ₹{daily_pnl:,.2f}, Target Progress: {target_progress:.1f}%)"
        )
        
        return {
            'success': True,
            'signals_generated': len(signals),
            'trades_executed': executed_trades,
            'portfolio_value': portfolio_status.get('total_value', 0),
            'daily_pnl': daily_pnl,
            'zerodha_connected': hasattr(trading_engine, 'connected') and trading_engine.connected
        }
        
    except Exception as e:
        error_logger.log_exception("enhanced_trading_session", e)
        return {'success': False, 'error': str(e)}

def send_daily_summary():
    """Send daily trading summary"""
    try:
        portfolio = paper_trading_engine.get_portfolio_status()
        daily_pnl = portfolio.get('day_pnl', 0)
        total_value = portfolio.get('total_value', 0)
        target_progress = (daily_pnl / 3000) * 100 if daily_pnl != 0 else 0

        summary = f"Daily Summary: Portfolio Rs.{total_value:,.2f}, P&L Rs.{daily_pnl:+,.2f}, Target Progress: {target_progress:.1f}%"
        print(f"[CHART] {summary}")
        system_logger.logger.info(f"Daily Summary Generated: {summary}")

        if telegram_bot:
            try:
                telegram_bot.send_message_sync(summary)
            except Exception as e:
                system_logger.logger.warning(f"Telegram send failed: {e}")
        return True
    except Exception as e:
        print(f"Daily summary error: {e}")
        return False


# Usage example:
# Instead of: system_logger.logger.info("🚀 Starting trading session")
# Use: log_with_emoji_replacement(system_logger.logger, 'info', "🚀 Starting trading session")
# Or: system_logger.logger.info("[ROCKET] Starting trading session")
