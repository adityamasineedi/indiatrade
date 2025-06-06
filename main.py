"""
Main Flask Application for Indian Stock Trading System
Web dashboard with real-time updates and trading controls
"""
import os
import sys
import json
import sqlite3
import threading
import time
import schedule
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import pandas as pd
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
        initial_capital=config.INITIAL_CAPITAL,
        config=config  # <-- Add this argument
    )
    print(f"✅ Paper Trading Engine initialized with Rs.{config.INITIAL_CAPITAL:,.2f}")
except Exception as e:
    print(f"❌ Paper Trading Engine initialization failed: {e}")
    paper_trading_engine = PaperTradingEngine(config=config)

backtest_engine = BacktestEngine(
    data_fetcher,
    technical_indicators,
    signal_generator
)

# Initialize Telegram bot (optional)
telegram_bot = None
try:
    from src.utils.telegram_bot import TelegramBot
    telegram_bot = TelegramBot()
    print("📱 Telegram bot initialized")
except Exception as e:
    print(f"⚠️ Telegram bot initialization failed: {e}")

# Validate configuration
try:
    config.validate_config()
    print("✅ Configuration validated")
except Exception as e:
    print(f"⚠️ Configuration validation failed: {e}")

# Global state
current_signals = []
current_regime = {}
portfolio_status = {}
system_status = {
    'running': True,
    'last_update': datetime.now(),
    'errors': 0,
    'trades_today': 0
}

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'indian-trading-system-secret-key')

# ==================== UTILITY FUNCTIONS ====================

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

def run_automated_trading_session():
    """Run automated trading session during market hours"""
    try:
        now = datetime.now()
        
        # Check if market is open
        if now.weekday() >= 5:  # Weekend
            return {'status': 'market_closed', 'reason': 'weekend'}
        
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if not (market_open <= now <= market_close):
            return {'status': 'market_closed', 'reason': 'outside_hours'}
        
        print("🚀 Starting automated trading session")
        
        # Update system data
        update_system_data()
        
        # Get current market regime
        regime = market_regime_detector.detect_current_regime()
        
        # Get watchlist stocks
        watchlist = config.WATCHLIST[:10]  # Trade top 10 stocks
        
        # Fetch current market data
        stocks_data = data_fetcher.get_multiple_stocks_data(watchlist, days=50)
        
        if not stocks_data:
            return {'status': 'error', 'message': 'No stock data available'}
        
        # Generate trading signals
        signals = signal_generator.generate_signals(stocks_data, regime)
        
        if not signals:
            return {'status': 'success', 'message': 'No signals generated', 'signals': 0, 'trades': 0}
        
        # Execute high-confidence signals
        executed_trades = 0
        for signal in signals:
            try:
                confidence = signal.get('confidence', 0)
                
                if confidence >= 70:
                    success = paper_trading_engine.execute_trade(signal)
                    
                    if success:
                        executed_trades += 1
                        
                        # Send Telegram alert for executed trades
                        try:
                            if telegram_bot:
                                telegram_bot.send_message_sync(
                                    f"🚀 Trade Executed: {signal['action']} {signal['symbol']} @ Rs.{signal['price']:.2f}"
                                )
                        except:
                            pass  # Don't let telegram errors stop trading
                        
            except Exception as e:
                print(f"❌ Trade execution error: {e}")
                continue
        
        # Update global state
        global current_signals
        current_signals = signals
        
        # Update system status
        system_status.update({
            'last_trading_session': datetime.now(),
            'signals_generated': len(signals),
            'trades_executed': executed_trades
        })
        
        return {
            'status': 'success',
            'signals_generated': len(signals),
            'trades_executed': executed_trades,
            'portfolio_value': portfolio_status.get('total_value', 0)
        }
        
    except Exception as e:
        error_logger.log_exception("automated_trading_session", e)
        return {'status': 'error', 'message': str(e)}

def setup_automated_trading():
    """Setup automated trading schedule"""
    try:
        schedule.clear()
        
        # Schedule trading sessions every 30 minutes during market hours
        market_times = ["09:20", "09:45", "10:15", "10:45", "11:15", "11:45", 
                       "12:15", "12:45", "13:15", "13:45", "14:15", "14:45", "15:15"]
        
        for time_str in market_times:
            schedule.every().day.at(time_str).do(run_automated_trading_session)
        
        # Schedule system updates every 5 minutes during market hours
        for hour in range(9, 16):
            for minute in [0, 15, 30, 45]:
                if hour == 9 and minute < 15:
                    continue
                if hour == 15 and minute > 30:
                    continue
                
                time_str = f"{hour:02d}:{minute:02d}"
                schedule.every().day.at(time_str).do(update_system_data)
        
        print("📅 Automated trading schedule configured")
        return True
        
    except Exception as e:
        error_logger.log_exception("trading_schedule_setup", e)
        return False

# ==================== FLASK ROUTES ====================

@app.route('/')
def home():
    """Home route - redirect to dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Dashboard with portfolio overview and trading signals"""
    try:
        # Get portfolio data with safe defaults
        portfolio = {
            'total_value': 100000.0,
            'total_pnl': 0.0,
            'daily_pnl': 0.0,
            'cash': 100000.0,
            'invested': 0.0,
            'positions_count': 0,
            'return_pct': 0.0
        }
        
        # Try to get real portfolio data
        if paper_trading_engine:
            try:
                real_portfolio = paper_trading_engine.get_portfolio_status()
                if real_portfolio:
                    portfolio.update(real_portfolio)
            except Exception as e:
                print(f"⚠️ Could not fetch portfolio data: {e}")
        
        # Daily target calculations
        daily_target = 3000.0
        target_progress = max(0, min(100, (portfolio['daily_pnl'] / daily_target) * 100))
        
        # Market regime data
        regime = current_regime if current_regime else {
            'regime': 'sideways',
            'confidence': 50.0,
            'indicators': {
                'market_breadth': 50.0,
                'average_rsi': 50.0,
                'volatility': 2.0,
                'momentum': 0.0
            }
        }
        
        # Market status
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        is_market_hours = market_open <= now <= market_close
        
        market_status = {
            'is_open': is_market_hours and not is_weekend
        }
        
        # Recent signals
        signals = current_signals[-10:] if current_signals else []
        
        return render_template(
            'dashboard.html',
            portfolio=portfolio,
            daily_pnl=portfolio['daily_pnl'],
            regime=regime,
            signals=signals,
            market_status=market_status,
            trade_count=system_status.get('trades_today', 0),
            system_status=system_status,
            # Template functions
            min=min,
            max=max,
            len=len,
            abs=abs,
            round=round
        )
        
    except Exception as e:
        error_logger.log_exception("dashboard_error", e)
        return render_template(
            'dashboard.html',
            portfolio={'total_value': 100000, 'daily_pnl': 0, 'total_pnl': 0},
            daily_pnl=0,
            regime={'regime': 'Unknown'},
            signals=[],
            market_status={'is_open': False},
            trade_count=0,
            system_status=system_status,
            error=f"Dashboard Error: {str(e)}",
            min=min, max=max, len=len, abs=abs, round=round
        )

@app.route('/trades')
def trades():
    """Trades history page"""
    try:
        days = request.args.get('days', 30, type=int)
        trade_history = []
        
        if paper_trading_engine:
            try:
                trade_history = paper_trading_engine.get_trade_history(days=days)
            except Exception as e:
                print(f"⚠️ Trade history error: {e}")
        
        return render_template('trades.html', trades=trade_history, days=days)
        
    except Exception as e:
        error_logger.log_exception("trades_page", e)
        return render_template('trades.html', trades=[], error=str(e))

# ==================== API ENDPOINTS ====================

@app.route('/api/portfolio')
def api_portfolio():
    """API endpoint for portfolio data"""
    try:
        portfolio_data = {
            'total_value': 100000.0,
            'daily_pnl': 0.0,
            'total_pnl': 0.0,
            'cash': 100000.0,
            'invested': 0.0,
            'positions_count': 0,
            'return_pct': 0.0,
            'target_progress': 0.0
        }
        
        if paper_trading_engine:
            try:
                real_data = paper_trading_engine.get_portfolio_status()
                if real_data:
                    portfolio_data.update(real_data)
                    # Calculate target progress
                    daily_target = 3000.0
                    portfolio_data['target_progress'] = max(0, min(100, 
                        (portfolio_data['daily_pnl'] / daily_target) * 100))
            except Exception as e:
                print(f"Portfolio API error: {e}")
        
        return jsonify(portfolio_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/signals')
def api_signals():
    """API endpoint for trading signals"""
    try:
        signals_data = []
        
        if current_signals:
            for signal in current_signals[-10:]:
                signals_data.append({
                    'symbol': signal.get('symbol', 'UNKNOWN'),
                    'action': signal.get('action', 'UNKNOWN'),
                    'price': signal.get('price', 0),
                    'confidence': signal.get('confidence', 0),
                    'timestamp': signal.get('timestamp', datetime.now()).isoformat() if signal.get('timestamp') else datetime.now().isoformat(),
                    'reasons': signal.get('reasons', [])
                })
        
        return jsonify(signals_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/regime')
def api_regime():
    """API endpoint for market regime"""
    try:
        regime_data = {
            'regime': 'sideways',
            'confidence': 50.0,
            'strength': 'moderate',
            'trend_direction': 'neutral',
            'indicators': {
                'market_breadth': 50.0,
                'average_rsi': 50.0,
                'volatility': 2.0,
                'momentum': 0.0
            }
        }
        
        if current_regime:
            regime_data.update(current_regime)
        
        return jsonify(regime_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_status')
def api_system_status():
    """API endpoint for system status"""
    try:
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        is_market_hours = market_open <= now <= market_close
        
        status = {
            'running': True,
            'market_open': is_market_hours and not is_weekend,
            'last_update': system_status.get('last_update', datetime.now()).isoformat(),
            'errors': system_status.get('errors', 0),
            'trades_today': system_status.get('trades_today', 0),
            'signals_generated': system_status.get('signals_generated', 0)
        }
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_system', methods=['POST'])
def api_update_system():
    """API endpoint to manually update system"""
    try:
        update_system_data()
        return jsonify({'status': 'success', 'message': 'System updated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/run_trading_session', methods=['POST'])
def api_run_trading_session():
    """API endpoint to manually run trading session"""
    try:
        result = run_automated_trading_session()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/run_backtest', methods=['POST'])
def api_run_backtest():
    """API endpoint to run backtest"""
    try:
        data = request.get_json() or {}
        symbols = data.get('symbols', config.WATCHLIST[:5])
        days = data.get('days', 30)
        
        results = backtest_engine.run_backtest(symbols, days=days)
        
        # Send results to Telegram
        if telegram_bot and results.get('summary'):
            try:
                summary = results['summary']
                telegram_bot.send_message_sync(
                    f"📊 Backtest completed: {summary['total_return_pct']:.2f}% return, "
                    f"{summary['win_rate']:.1f}% win rate"
                )
            except Exception as e:
                print(f"Telegram send failed: {e}")
        
        return jsonify(results)
        
    except Exception as e:
        error_logger.log_exception("backtest_api", e)
        return jsonify({'error': str(e)})

@app.route('/api/test_telegram', methods=['POST'])
def api_test_telegram():
    """API endpoint to test Telegram connection"""
    try:
        if telegram_bot:
            success, message = telegram_bot.test_connection()
            return jsonify({'success': success, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'Telegram bot not initialized'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/send_portfolio_update', methods=['POST'])
def api_send_portfolio_update():
    """API endpoint to send portfolio update via Telegram"""
    try:
        if telegram_bot and portfolio_status:
            message = (
                f"📊 Portfolio Update\n"
                f"Total Value: ₹{portfolio_status.get('total_value', 0):,.2f}\n"
                f"P&L: ₹{portfolio_status.get('total_pnl', 0):,.2f}\n"
                f"Return: {portfolio_status.get('return_pct', 0):.2f}%"
            )
            success = telegram_bot.send_message_sync(message)
            return jsonify({'success': success})
        else:
            return jsonify({'success': False, 'message': 'Telegram not available or no portfolio data'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'data_fetcher': data_fetcher is not None,
            'paper_trading': paper_trading_engine is not None,
            'technical_indicators': technical_indicators is not None,
            'signal_generator': signal_generator is not None,
            'telegram_bot': telegram_bot is not None
        },
        'last_update': system_status.get('last_update', datetime.now()).isoformat()
    })

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    error_logger.log_exception("flask_500_error", error)
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_error(e):
    error_logger.log_exception("flask_error", e)
    return jsonify({'error': str(e)}), 500

# ==================== BACKGROUND SCHEDULER ====================

def run_schedule():
    """Background thread to run scheduled tasks"""
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            error_logger.log_exception("schedule_run", e)
            time.sleep(5)  # Wait a bit before retrying

# ==================== INITIALIZATION ====================

# Setup automated trading schedule
setup_automated_trading()

# Start the background scheduler
scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
scheduler_thread.start()
print("🔄 Background scheduler started")

# Initial system data update
update_system_data()
print("📊 Initial system data loaded")

# ==================== MAIN APPLICATION ====================

if __name__ == '__main__':
    print("🚀 Starting Indian Stock Trading System")
    print(f"📊 Initial Capital: ₹{config.INITIAL_CAPITAL:,.2f}")
    print(f"🎯 Daily Target: ₹{config.PROFIT_TARGET:,.2f}")
    print(f"📈 Max Positions: {config.MAX_POSITIONS}")
    print(f"⚡ Auto Trading: Enabled")
    print(f"📱 Telegram: {'Enabled' if telegram_bot else 'Disabled'}")
    print("🌐 Dashboard: http://localhost:5000")
    
    # Run Flask app
    app.run(
        debug=config.FLASK_DEBUG,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        threaded=True
    )
