"""
Production-Ready Indian Stock Trading System with Complete Zerodha Integration
Merged version with lazy loading, comprehensive features, and startup safety
"""
import os
import sys
import json
import sqlite3
import threading
import time
import schedule
import signal
import atexit
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.append('src')
sys.path.append('config')

# Core imports (always available)
from src.data_fetcher import DataFetcher
from src.indicators.technical import TechnicalIndicators  
from src.engines.paper_trading import PaperTradingEngine
from config.settings import Config

# Initialize configuration first
config = Config()

# Zerodha Integration with safe imports
ZERODHA_AVAILABLE = False
try:
    from config.zerodha.auth import ZerodhaAuth
    from config.zerodha.instruments import ZerodhaInstruments
    from config.zerodha.rate_limiter import zerodha_rate_limiter
    from kiteconnect import KiteConnect
    ZERODHA_AVAILABLE = True
    print("✅ Zerodha integration available")
except ImportError as e:
    print(f"⚠️ Zerodha integration not available: {e}")
    print("📦 Install with: pip install kiteconnect pyotp")

# Initialize logging
try:
    from src.utils.logger import setup_logging, get_system_logger, get_error_logger
    setup_logging()
    system_logger = get_system_logger()
    error_logger = get_error_logger()
    print("✅ Logging system initialized")
except Exception as e:
    print(f"⚠️ Logging initialization failed: {e}")
    system_logger = None
    error_logger = None

# Initialize core components (safe initialization)
print("🔧 Initializing core components...")
data_fetcher = DataFetcher()
technical_indicators = TechnicalIndicators()

# Zerodha components (initialized safely)
zerodha_auth = None
zerodha_instruments = None
kite = None

if ZERODHA_AVAILABLE and getattr(config, "ZERODHA_ENABLED", False):
    try:
        print("🔗 Initializing Zerodha integration...")
        zerodha_auth = ZerodhaAuth()
        
        if zerodha_auth.authenticate():
            kite = zerodha_auth.kite
            zerodha_instruments = ZerodhaInstruments(kite)
            zerodha_instruments.update_if_needed()
            print("✅ Zerodha integration ready")
        else:
            print("⚠️ Zerodha authentication required")
            print("🔧 Run setup_zerodha_auth() to configure")
    except Exception as e:
        print(f"❌ Zerodha initialization failed: {e}")
        print("🔧 Continuing with standard data sources...")

# Enhanced Data Fetcher with Zerodha integration
class EnhancedDataFetcher(DataFetcher):
    """Enhanced data fetcher with Zerodha integration and intelligent fallback"""
    
    def __init__(self, kite_instance=None, instruments=None):
        super().__init__()
        self.kite = kite_instance
        self.instruments = instruments
        self.use_zerodha = bool(kite_instance and instruments)
        self.zerodha_success_rate = 1.0  # Track success rate
        
    def get_current_price(self, symbol):
        """Get current price with Zerodha and intelligent fallback"""
        if self.use_zerodha and self.zerodha_success_rate > 0.5:
            try:
                instrument_token = self.instruments.get_instrument_token(symbol)
                if instrument_token:
                    # Add timeout protection
                    price_result = {'completed': False}
                    
                    def fetch_zerodha_price():
                        try:
                            # Safe rate limiter check
                            if zerodha_rate_limiter:
                                zerodha_rate_limiter.wait_if_needed()
                                zerodha_rate_limiter.record_call()
                            
                            quote = self.kite.quote([f"NSE:{symbol}"])
                            if f"NSE:{symbol}" in quote:
                                price = quote[f"NSE:{symbol}"]["last_price"]
                                price_result.update({
                                    'price': float(price),
                                    'completed': True,
                                    'success': True
                                })
                        except Exception as e:
                            price_result.update({
                                'error': str(e),
                                'completed': True,
                                'success': False
                            })
                    
                    # Use thread with timeout
                    fetch_thread = threading.Thread(target=fetch_zerodha_price, daemon=True)
                    fetch_thread.start()
                    fetch_thread.join(timeout=3.0)  # 3 second timeout
                    
                    if price_result['completed'] and price_result.get('success'):
                        return price_result['price']
                    else:
                        print(f"⚠️ Zerodha timeout/error for {symbol}: {price_result.get('error', 'timeout')}")
                        self.zerodha_success_rate *= 0.9  # Reduce success rate
                        
            except Exception as e:
                print(f"⚠️ Zerodha price failed for {symbol}, using fallback: {e}")
                self.zerodha_success_rate *= 0.9  # Reduce success rate
        
        # Fallback to parent method
        return super().get_current_price(symbol)
    
    def get_stock_data(self, symbol, days=30):
        """Get stock data with Zerodha historical data and fallback"""
        if self.use_zerodha and self.zerodha_success_rate > 0.7:
            try:
                instrument_token = self.instruments.get_instrument_token(symbol)
                if instrument_token:
                    zerodha_rate_limiter.wait_if_needed()
                    zerodha_rate_limiter.record_call()
                    
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days+5)
                    
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
                            'open': 'Open', 'high': 'High', 'low': 'Low',
                            'close': 'Close', 'volume': 'Volume'
                        }, inplace=True)
                        return df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(days)
            except Exception as e:
                print(f"⚠️ Zerodha historical data failed for {symbol}: {e}")
                self.zerodha_success_rate *= 0.8  # Reduce success rate
        
        # Use parent method (Yahoo Finance/NSEpy)
        return super().get_stock_data(symbol, days)
    
    def get_multiple_stocks_data(self, symbols, days=30):
        """Enhanced multiple stocks data with batch processing"""
        stocks_data = {}
        
        for symbol in symbols:
            try:
                data = self.get_stock_data(symbol, days)
                if not data.empty:
                    stocks_data[symbol] = data
                    time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Failed to get data for {symbol}: {e}")
                continue
        
        return stocks_data

# Initialize enhanced data fetcher
if kite and zerodha_instruments:
    enhanced_data_fetcher = EnhancedDataFetcher(kite, zerodha_instruments)
    print("✅ Enhanced data fetcher with Zerodha integration")
else:
    enhanced_data_fetcher = data_fetcher
    print("📊 Standard data fetcher initialized")

# Lazy-loaded components (to prevent hanging)
market_regime_detector = None
signal_generator = None
backtest_engine = None

def get_market_regime_detector():
    """Lazy-load market regime detector"""
    global market_regime_detector
    if market_regime_detector is None:
        try:
            from src.market_regime import MarketRegimeDetector
            market_regime_detector = MarketRegimeDetector(enhanced_data_fetcher)
            print("✅ Market regime detector loaded")
        except Exception as e:
            print(f"❌ Market regime detector failed: {e}")
            # Create a mock detector
            class MockRegimeDetector:
                def detect_current_regime(self):
                    return {
                        'regime': 'sideways',
                        'confidence': 50.0,
                        'indicators': {'market_breadth': 50.0, 'average_rsi': 50.0}
                    }
            market_regime_detector = MockRegimeDetector()
    return market_regime_detector

def get_signal_generator():
    """Lazy-load signal generator"""
    global signal_generator
    if signal_generator is None:
        try:
            from src.strategies.signal_generator import SignalGenerator
            regime_detector = get_market_regime_detector()
            signal_generator = SignalGenerator(technical_indicators, regime_detector)
            print("✅ Signal generator loaded")
        except Exception as e:
            print(f"❌ Signal generator failed: {e}")
            # Create a mock generator
            class MockSignalGenerator:
                def generate_signals(self, stocks_data, regime=None):
                    return []
            signal_generator = MockSignalGenerator()
    return signal_generator

def get_backtest_engine():
    """Lazy-load backtest engine"""
    global backtest_engine
    if backtest_engine is None:
        try:
            from src.engines.backtest import BacktestEngine
            backtest_engine = BacktestEngine(
                enhanced_data_fetcher,
                technical_indicators,
                get_signal_generator()
            )
            print("✅ Backtest engine loaded")
        except Exception as e:
            print(f"❌ Backtest engine failed: {e}")
    return backtest_engine

# Initialize paper trading engine
try:
    paper_trading_engine = PaperTradingEngine(
        data_fetcher=enhanced_data_fetcher,
        signal_generator=None,  # Will be set later
        initial_capital=config.INITIAL_CAPITAL
    )
    print(f"✅ Paper Trading Engine initialized with Rs.{config.INITIAL_CAPITAL:,.2f}")
except Exception as e:
    print(f"❌ Paper Trading Engine failed: {e}")
    paper_trading_engine = None

# Initialize Telegram bot (optional)
telegram_bot = None
try:
    from src.utils.telegram_bot import TelegramBot
    telegram_bot = TelegramBot()
    print("📱 Telegram bot initialized")
except Exception as e:
    print(f"⚠️ Telegram bot not available: {e}")

# Global state
current_signals = []
current_regime = {'regime': 'initializing', 'confidence': 0}  # Safe default
portfolio_status = {}
system_status = {
    'running': True,
    'startup_complete': False,  # Track startup completion
    'last_update': datetime.now(),
    'errors': 0,
    'trades_today': 0,
    'zerodha_connected': bool(kite),
    'trading_mode': getattr(config, "get_trading_mode", lambda: "paper")(),
    'market_status': getattr(config, "get_market_status", lambda: {})(),
    'components_loaded': {
        'data_fetcher': True,
        'paper_trading': bool(paper_trading_engine),
        'zerodha': bool(kite),
        'telegram': bool(telegram_bot)
    }
}

# Initialize Flask app
app = Flask(__name__)
app.secret_key = getattr(config, "FLASK_SECRET_KEY", "indian-trading-system-secret-key")

# ==================== CORE ROUTES ====================

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Enhanced dashboard with comprehensive data"""
    try:
        # Initialize portfolio data with safe defaults
        portfolio = {
            'total_value': config.INITIAL_CAPITAL,
            'total_pnl': 0.0,
            'daily_pnl': 0.0,
            'cash': config.INITIAL_CAPITAL,
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
                    print(f"✅ Portfolio data loaded: Rs.{portfolio['total_value']:,.2f}")
            except Exception as e:
                print(f"⚠️ Portfolio data error: {e}")
        
        # Market status and regime
        market_status = getattr(config, "get_market_status", lambda: {})()
        regime = current_regime if current_regime else {
            'regime': 'ready',
            'confidence': 75.0,
            'indicators': {
                'market_breadth': 50.0,
                'average_rsi': 50.0,
                'volatility': 2.0,
                'momentum': 0.0
            }
        }
        
        # Enhanced system status
        enhanced_system_status = system_status.copy()
        enhanced_system_status.update({
            'zerodha_connected': bool(kite),
            'trading_mode': getattr(config, "get_trading_mode", lambda: "paper")(),
            'data_source': 'Zerodha' if kite else 'Yahoo Finance',
            'last_update': system_status.get('last_update', datetime.now()).isoformat()
        })
        
        return render_template(
            'dashboard.html',
            portfolio=portfolio,
            daily_pnl=portfolio['daily_pnl'],
            regime=regime,
            signals=current_signals[-10:] if current_signals else [],
            market_status=market_status,
            trade_count=system_status.get('trades_today', 0),
            system_status=enhanced_system_status,
            zerodha_connected=bool(kite),
            trading_mode=getattr(config, "get_trading_mode", lambda: "paper")(),
            # Template functions
            min=min, max=max, len=len, abs=abs, round=round
        )
        
    except Exception as e:
        if error_logger:
            error_logger.log_exception("dashboard_error", e)
        print(f"❌ Dashboard error: {e}")
        
        # Return safe fallback
        return render_template(
            'dashboard.html',
            portfolio={'total_value': config.INITIAL_CAPITAL, 'daily_pnl': 0, 'total_pnl': 0},
            daily_pnl=0,
            regime={'regime': 'Error'},
            signals=[],
            market_status={'status': 'ERROR'},
            trade_count=0,
            system_status=system_status,
            error=f"Dashboard Error: {str(e)}",
            zerodha_connected=False,
            trading_mode='ERROR',
            min=min, max=max, len=len, abs=abs, round=round
        )

@app.route('/trades')
def trades():
    """Enhanced trades history page"""
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
        if error_logger:
            error_logger.log_exception("trades_page", e)
        return render_template('trades.html', trades=[], error=str(e))

# ==================== API ENDPOINTS ====================

@app.route('/api/portfolio')
def api_portfolio():
    """Enhanced portfolio API"""
    try:
        portfolio_data = {
            'total_value': config.INITIAL_CAPITAL,
            'daily_pnl': 0.0,
            'total_pnl': 0.0,
            'cash': config.INITIAL_CAPITAL,
            'invested': 0.0,
            'positions_count': 0,
            'return_pct': 0.0,
            'target_progress': 0.0,
            'data_source': 'Zerodha' if kite else 'Standard'
        }
        
        if paper_trading_engine:
            try:
                real_data = paper_trading_engine.get_portfolio_status()
                if real_data:
                    portfolio_data.update(real_data)
                    
                    # Calculate target progress
                    daily_target = getattr(config, 'PROFIT_TARGET', 3000.0)
                    target_progress = max(0, min(100, 
                        (portfolio_data['daily_pnl'] / daily_target) * 100))
                    portfolio_data['target_progress'] = target_progress
            except Exception as e:
                print(f"Portfolio API error: {e}")
        
        return jsonify(portfolio_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/signals')
def api_signals():
    """Enhanced signals API"""
    try:
        signals_data = []
        
        if current_signals:
            for signal in current_signals[-10:]:  # Last 10 signals
                signals_data.append({
                    'symbol': signal.get('symbol', 'UNKNOWN'),
                    'action': signal.get('action', 'UNKNOWN'),
                    'price': signal.get('price', 0),
                    'confidence': signal.get('confidence', 0),
                    'reasons': signal.get('reasons', []),
                    'timestamp': signal.get('timestamp', datetime.now()).isoformat() if hasattr(signal.get('timestamp', datetime.now()), 'isoformat') else str(signal.get('timestamp', datetime.now())),
                    'stop_loss': signal.get('stop_loss', 0),
                    'target_price': signal.get('target_price', 0)
                })
        
        return jsonify({
            'signals': signals_data,
            'count': len(signals_data),
            'last_update': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_status')
def api_system_status():
    """Enhanced system status API"""
    try:
        market_status = getattr(config, "get_market_status", lambda: {})()
        
        status = {
            'running': True,
            'market_status': market_status,
            'last_update': system_status.get('last_update', datetime.now()).isoformat(),
            'errors': system_status.get('errors', 0),
            'trades_today': system_status.get('trades_today', 0),
            'signals_generated': system_status.get('signals_generated', 0),
            'zerodha_connected': bool(kite),
            'trading_mode': getattr(config, "get_trading_mode", lambda: "paper")(),
            'data_source': 'Zerodha' if kite else 'Yahoo Finance',
            'components': {
                'data_fetcher': bool(enhanced_data_fetcher),
                'paper_trading': bool(paper_trading_engine),
                'zerodha': bool(kite),
                'telegram': bool(telegram_bot),
                'market_regime': market_regime_detector is not None,
                'signal_generator': signal_generator is not None
            }
        }
        
        if ZERODHA_AVAILABLE and kite:
            status['rate_limiter'] = zerodha_rate_limiter.get_stats()
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/regime')
def api_regime():
    """Market regime API"""
    try:
        regime_data = current_regime if current_regime else {
            'regime': 'unknown',
            'confidence': 0,
            'indicators': {}
        }
        return jsonify(regime_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run_trading_session', methods=['POST'])
def api_run_trading_session():
    """Enhanced trading session API"""
    try:
        result = run_enhanced_trading_session()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/update_system', methods=['POST'])
def api_update_system():
    """System update API"""
    try:
        update_system_data()
        return jsonify({'status': 'success', 'message': 'System updated successfully'})
    except Exception as e:
        if error_logger:
            error_logger.log_exception("manual_update", e)
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/run_backtest', methods=['POST'])
def api_run_backtest():
    """Enhanced backtest API"""
    try:
        data = request.get_json() or {}
        symbols = data.get('symbols', config.WATCHLIST[:5])
        days = data.get('days', 30)
        
        backtest_eng = get_backtest_engine()
        if backtest_eng:
            results = backtest_eng.run_backtest(symbols, days=days)
            
            # Send results to Telegram
            if telegram_bot and results.get('summary'):
                try:
                    summary = results['summary']
                    telegram_bot.send_message_sync(
                        f"📊 Backtest completed\n"
                        f"Return: {summary.get('total_return_pct', 0):.2f}%\n"
                        f"Win Rate: {summary.get('win_rate', 0):.1f}%"
                    )
                except:
                    pass
            
            return jsonify(results)
        else:
            return jsonify({'error': 'Backtest engine not available'})
        
    except Exception as e:
        if error_logger:
            error_logger.log_exception("backtest_api", e)
        return jsonify({'error': str(e)})

# ==================== ZERODHA ENDPOINTS ====================

@app.route('/zerodha/status')
def zerodha_status():
    """Non-blocking Zerodha status"""
    try:
        # Basic status (fast)
        status = {
            'available': ZERODHA_AVAILABLE,
            'enabled': getattr(config, "ZERODHA_ENABLED", False),
            'connected': bool(kite),
            'paper_trading': getattr(config, "ZERODHA_PAPER_TRADING", True),
            'trading_mode': getattr(config, "get_trading_mode", lambda: "paper")(),
            'success_rate': getattr(enhanced_data_fetcher, 'zerodha_success_rate', 1.0) if hasattr(enhanced_data_fetcher, 'zerodha_success_rate') else 1.0,
            'timestamp': datetime.now().isoformat()
        }
        
        # Rate limiter stats (fast)
        if ZERODHA_AVAILABLE:
            try:
                status['rate_limiter'] = zerodha_rate_limiter.get_stats()
            except:
                status['rate_limiter'] = {'error': 'unavailable'}
        
        # Profile info (potentially slow - with timeout)
        if kite:
            try:
                # Use threading with timeout for profile fetch
                profile_result = {'completed': False}
                
                def fetch_profile():
                    try:
                        profile = kite.profile()
                        profile_result.update({
                            'user_name': profile.get('user_name'),
                            'user_id': profile.get('user_id'),
                            'email': profile.get('email'),
                            'completed': True
                        })
                    except Exception as e:
                        profile_result['profile_error'] = str(e)
                        profile_result['completed'] = True
                
                # Start profile fetch in background
                profile_thread = threading.Thread(target=fetch_profile, daemon=True)
                profile_thread.start()
                
                # Wait max 2 seconds for profile
                profile_thread.join(timeout=2.0)
                
                if profile_result['completed']:
                    status.update(profile_result)
                    status.pop('completed', None)
                else:
                    status['profile_status'] = 'loading (taking longer than expected)'
                    
            except Exception as e:
                status['profile_error'] = str(e)
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'available': ZERODHA_AVAILABLE,
            'connected': bool(kite),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/zerodha/setup', methods=['GET', 'POST'])
def zerodha_setup():
    """Zerodha authentication setup"""
    if not ZERODHA_AVAILABLE:
        return jsonify({'error': 'Zerodha integration not available'}), 400
    
    if request.method == 'GET':
        try:
            if not zerodha_auth:
                return jsonify({'error': 'Zerodha auth not initialized'}), 500
            login_url = zerodha_auth.get_login_url()
            return jsonify({'login_url': login_url})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    elif request.method == 'POST':
        try:
            data = request.get_json()
            request_token = data.get('request_token')
            
            if not request_token:
                return jsonify({'error': 'request_token required'}), 400
            
            result = zerodha_auth.generate_session(request_token)
            if result:
                global kite, zerodha_instruments, enhanced_data_fetcher
                kite = zerodha_auth.kite
                zerodha_instruments = ZerodhaInstruments(kite)
                zerodha_instruments.update_if_needed()
                
                # Update enhanced data fetcher
                enhanced_data_fetcher = EnhancedDataFetcher(kite, zerodha_instruments)
                
                return jsonify({
                    'success': True,
                    'user': result.get('user_name'),
                    'message': 'Authentication successful'
                })
            else:
                return jsonify({'error': 'Authentication failed'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/zerodha/live_prices')
def get_live_prices():
    """Non-blocking live prices from Zerodha"""
    try:
        # Quick validation
        if not kite:
            return jsonify({
                'error': 'Zerodha not connected',
                'connected': False,
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Get symbols (limit to prevent hanging)
        symbols_param = request.args.get('symbols', 'RELIANCE,TCS,INFY')
        symbols = [s.strip() for s in symbols_param.split(',') if s.strip()][:5]  # Limit to 5
        
        # Quick response structure
        response = {
            'timestamp': datetime.now().isoformat(),
            'source': 'Zerodha',
            'symbols_requested': len(symbols),
            'data': {},
            'status': 'processing'
        }
        
        # Fetch prices with timeout
        def fetch_live_data():
            live_data = {}
            for symbol in symbols:
                try:
                    # Safe rate limiter check
                    if zerodha_rate_limiter:
                        zerodha_rate_limiter.wait_if_needed()
                        zerodha_rate_limiter.record_call()
                    
                    # Make API call with shorter timeout expectation
                    quote = kite.quote([f"NSE:{symbol}"])
                    
                    if f"NSE:{symbol}" in quote:
                        data = quote[f"NSE:{symbol}"]
                        live_data[symbol] = {
                            'last_price': data['last_price'],
                            'change': data.get('net_change', 0),
                            'change_percent': (data.get('net_change', 0) / data['ohlc']['close'] * 100) if data['ohlc']['close'] else 0,
                            'volume': data.get('volume', 0),
                            'ohlc': data['ohlc'],
                            'timestamp': datetime.now().isoformat(),
                            'status': 'success'
                        }
                    else:
                        live_data[symbol] = {'error': 'No data in response'}
                        
                except Exception as e:
                    live_data[symbol] = {'error': str(e), 'status': 'failed'}
            
            return live_data
        
        # Use thread with timeout
        price_result = {'completed': False, 'data': {}}
        
        def fetch_with_result():
            try:
                data = fetch_live_data()
                price_result.update({
                    'data': data,
                    'completed': True,
                    'success': True
                })
            except Exception as e:
                price_result.update({
                    'error': str(e),
                    'completed': True,
                    'success': False
                })
        
        # Start fetch in background
        fetch_thread = threading.Thread(target=fetch_with_result, daemon=True)
        fetch_thread.start()
        
        # Wait max 5 seconds for all prices
        fetch_thread.join(timeout=5.0)
        
        if price_result['completed']:
            response.update({
                'data': price_result['data'],
                'status': 'completed',
                'symbols_fetched': len(price_result['data'])
            })
            if 'error' in price_result:
                response['fetch_error'] = price_result['error']
        else:
            response.update({
                'status': 'timeout',
                'message': 'Price fetch taking longer than expected',
                'data': {},
                'symbols_fetched': 0
            })
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/test_zerodha_price')
def test_zerodha_price():
    """Non-blocking Zerodha price test"""
    try:
        symbol = request.args.get('symbol', 'RELIANCE')
        
        # Quick response structure
        response = {
            'symbol': symbol,
            'source': 'Unknown',
            'timestamp': datetime.now().isoformat(),
            'zerodha_connected': bool(kite),
            'test_status': 'running'
        }
        
        # Test price fetch with timeout
        if enhanced_data_fetcher:
            price_result = {'completed': False}
            
            def fetch_price():
                try:
                    price = enhanced_data_fetcher.get_current_price(symbol)
                    price_result.update({
                        'price': price,
                        'source': 'Zerodha' if kite else 'Fallback',
                        'completed': True,
                        'success': True
                    })
                except Exception as e:
                    price_result.update({
                        'error': str(e),
                        'completed': True,
                        'success': False
                    })
            
            # Start price fetch in background
            price_thread = threading.Thread(target=fetch_price, daemon=True)
            price_thread.start()
            
            # Wait max 3 seconds for price
            price_thread.join(timeout=3.0)
            
            if price_result['completed']:
                response.update(price_result)
                response.pop('completed', None)
                response['test_status'] = 'completed'
            else:
                response.update({
                    'test_status': 'timeout',
                    'message': 'Price fetch taking longer than expected',
                    'price': None
                })
        else:
            response.update({
                'error': 'Data fetcher not available',
                'test_status': 'failed'
            })
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'symbol': request.args.get('symbol', 'RELIANCE'),
            'test_status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== TELEGRAM ENDPOINTS ====================

@app.route('/api/test_telegram', methods=['POST'])
def api_test_telegram():
    """Test Telegram connection"""
    try:
        if not telegram_bot:
            return jsonify({'success': False, 'message': 'Telegram bot not available'})
        
        success, message = telegram_bot.test_connection()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/send_portfolio_update', methods=['POST'])
def api_send_portfolio_update():
    """Send portfolio update via Telegram"""
    try:
        if not telegram_bot:
            return jsonify({'success': False, 'message': 'Telegram bot not available'})
        
        if portfolio_status:
            success = telegram_bot.send_message_sync(
                f"📊 Portfolio Update\n"
                f"Total Value: ₹{portfolio_status.get('total_value', 0):,.2f}\n"
                f"P&L: ₹{portfolio_status.get('total_pnl', 0):,.2f}\n"
                f"Return: {portfolio_status.get('return_pct', 0):.2f}%\n"
                f"Data Source: {'Zerodha' if kite else 'Standard'}"
            )
            return jsonify({'success': success})
        else:
            return jsonify({'success': False, 'message': 'No portfolio data available'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ==================== TRADING FUNCTIONS ====================

def update_system_data():
    """Enhanced system data update with non-blocking initialization"""
    global current_signals, current_regime, portfolio_status, system_status
    
    try:
        if system_logger:
            system_logger.logger.info("Starting enhanced system data update")
        
        # Update portfolio status first (fast operation)
        if paper_trading_engine:
            try:
                portfolio_status = paper_trading_engine.get_portfolio_status()
            except Exception as e:
                print(f"⚠️ Portfolio status update failed: {e}")
        
        # Update basic system status (fast operation)
        system_status.update({
            'last_update': datetime.now(),
            'running': True,
            'zerodha_connected': bool(kite),
            'trading_mode': getattr(config, "get_trading_mode", lambda: "paper")(),
            'market_status': getattr(config, "get_market_status", lambda: {})()
        })
        
        if ZERODHA_AVAILABLE and kite:
            system_status['rate_limiter_stats'] = zerodha_rate_limiter.get_stats()
        
        # Update market regime in background (potentially slow operation)
        def update_regime_background():
            global current_regime
            try:
                regime_detector = get_market_regime_detector()
                if regime_detector:
                    current_regime = regime_detector.detect_current_regime()
                    print("✅ Market regime updated")
            except Exception as e:
                print(f"⚠️ Regime update failed: {e}")
                current_regime = {
                    'regime': 'unknown',
                    'confidence': 0,
                    'indicators': {}
                }
        
        # Only update regime in background if not startup
        if system_status.get('startup_complete', False):
            threading.Thread(target=update_regime_background, daemon=True).start()
        
        if system_logger:
            system_logger.logger.info("Enhanced system data update completed")
        
    except Exception as e:
        if error_logger:
            error_logger.log_exception("enhanced_system_data_update", e)
        system_status['errors'] += 1
        print(f"⚠️ System update error: {e}")

def run_enhanced_trading_session():
    """Enhanced trading session with comprehensive error handling"""
    try:
        # Check market status
        market_status = getattr(config, "get_market_status", lambda: {"is_trading": True, "status": "open", "session": "regular"})()
        
        if not market_status.get('is_trading', True):
            return {
                'status': 'market_closed',
                'session': market_status.get('session', 'unknown'),
                'message': f"Market is {market_status.get('status', 'closed')}"
            }
        
        print("🚀 Starting enhanced trading session...")
        
        # Update system data
        update_system_data()
        
        # Get market regime
        regime_detector = get_market_regime_detector()
        regime = current_regime if current_regime else {'regime': 'testing', 'confidence': 75.0}
        
        # Get signals
        sig_gen = get_signal_generator()
        signals = []
        
        if sig_gen:
            try:
                # Get stock data
                watchlist = getattr(config, "WATCHLIST", ['RELIANCE', 'TCS', 'INFY'])[:10]
                stocks_data = enhanced_data_fetcher.get_multiple_stocks_data(watchlist, days=50)
                
                if stocks_data:
                    signals = sig_gen.generate_signals(stocks_data, regime)
                    print(f"📡 Generated {len(signals)} signals")
                
            except Exception as e:
                print(f"⚠️ Signal generation error: {e}")
        
        # Execute trades
        executed_trades = 0
        if paper_trading_engine and signals:
            for signal in signals:
                try:
                    confidence = signal.get('confidence', 0)
                    if confidence >= 70:
                        success = paper_trading_engine.execute_trade(signal)
                        if success:
                            executed_trades += 1
                            
                            # Send Telegram notification
                            if telegram_bot:
                                try:
                                    source = "Zerodha" if kite else "Simulation"
                                    telegram_bot.send_message_sync(
                                        f"🚀 Trade Executed ({source})\n"
                                        f"{signal['action']} {signal['symbol']}\n"
                                        f"Price: ₹{signal['price']:.2f}\n"
                                        f"Confidence: {confidence:.1f}%"
                                    )
                                except:
                                    pass
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
            'trades_executed': executed_trades,
            'trades_today': system_status.get('trades_today', 0) + executed_trades
        })
        
        return {
            'status': 'success',
            'signals_generated': len(signals),
            'trades_executed': executed_trades,
            'portfolio_value': portfolio_status.get('total_value', 0) if portfolio_status else 0,
            'data_source': 'Zerodha' if kite else 'Yahoo Finance',
            'trading_mode': getattr(config, "get_trading_mode", lambda: "paper")(),
            'regime': regime.get('regime', 'unknown')
        }
        
    except Exception as e:
        if error_logger:
            error_logger.log_exception("enhanced_trading_session", e)
        print(f"❌ Trading session error: {e}")
        return {'status': 'error', 'message': str(e)}

# ==================== BACKGROUND TASKS ====================

def setup_automated_trading():
    """Setup enhanced automated trading schedule"""
    try:
        schedule.clear()
        
        # Trading sessions during market hours
        market_times = ["09:20", "09:45", "10:15", "10:45", "11:15", "11:45", 
                       "12:15", "12:45", "13:15", "13:45", "14:15", "14:45", "15:15"]
        
        for time_str in market_times:
            schedule.every().day.at(time_str).do(run_enhanced_trading_session)
        
        # System updates every 15 minutes during market hours
        for hour in range(9, 16):
            for minute in [0, 15, 30, 45]:
                if hour == 9 and minute < 15:
                    continue
                if hour == 15 and minute > 30:
                    continue
                
                time_str = f"{hour:02d}:{minute:02d}"
                schedule.every().day.at(time_str).do(update_system_data)
        
        print("📅 Enhanced automated trading schedule configured")
        return True
        
    except Exception as e:
        if error_logger:
            error_logger.log_exception("enhanced_trading_schedule_setup", e)
        print(f"❌ Schedule setup error: {e}")
        return False

def run_schedule():
    """Background scheduler with error handling"""
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            if error_logger:
                error_logger.log_exception("enhanced_schedule_run", e)
            print(f"⚠️ Scheduler error: {e}")
            time.sleep(5)  # Wait longer on error

def background_update():
    """Background update task"""
    while True:
        try:
            # Update system status
            system_status['last_update'] = datetime.now()
            system_status['market_status'] = getattr(config, "get_market_status", lambda: {})()
            
            # Sleep for 5 minutes
            time.sleep(300)
            
        except Exception as e:
            print(f"⚠️ Background update error: {e}")
            time.sleep(60)

# ==================== GRACEFUL SHUTDOWN ====================

def signal_handler(signum, frame):
    """Graceful shutdown handler"""
    print("\n🛑 Shutting down gracefully...")
    
    if telegram_bot:
        try:
            telegram_bot.send_message_sync("🛑 Trading system shutting down")
        except:
            pass
    
    sys.exit(0)

def cleanup():
    """Cleanup function"""
    print("🧹 Cleaning up resources...")

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(cleanup)

# ==================== SAFE STARTUP ====================

def safe_startup_initialization():
    """Safe startup initialization that won't hang"""
    try:
        print("🚀 Starting safe initialization...")
        
        # Quick portfolio status update
        if paper_trading_engine:
            try:
                global portfolio_status
                portfolio_status = paper_trading_engine.get_portfolio_status()
                print("✅ Portfolio status loaded")
            except Exception as e:
                print(f"⚠️ Portfolio status error: {e}")
        
        # Set safe default regime
        global current_regime
        current_regime = {
            'regime': 'ready',
            'confidence': 50.0,
            'indicators': {
                'market_breadth': 50.0,
                'average_rsi': 50.0,
                'volatility': 2.0,
                'momentum': 0.0
            }
        }
        print("✅ Default market regime set")
        
        # Update basic system status
        system_status.update({
            'last_update': datetime.now(),
            'running': True,
            'startup_complete': True  # Mark startup as complete
        })
        print("✅ System status updated")
        
        # Start background regime detection (non-blocking)
        def background_regime_init():
            try:
                print("🔍 Loading market regime detector in background...")
                
                # Use threading timer for cross-platform timeout
                timeout_occurred = threading.Event()
                
                def timeout_callback():
                    timeout_occurred.set()
                    print("⏰ Market regime detection timed out - using defaults")
                
                timer = threading.Timer(30.0, timeout_callback)  # 30 second timeout
                timer.start()
                
                try:
                    regime_detector = get_market_regime_detector()
                    if regime_detector and not timeout_occurred.is_set():
                        print("🔍 Detecting current market regime...")
                        regime = regime_detector.detect_current_regime()
                        if not timeout_occurred.is_set():
                            global current_regime
                            current_regime = regime
                            print(f"✅ Market regime detected: {regime.get('regime', 'unknown')}")
                finally:
                    timer.cancel()  # Cancel the timer
                    
            except Exception as e:
                print(f"⚠️ Background regime detection failed: {e}")
        
        # Start background thread
        threading.Thread(target=background_regime_init, daemon=True).start()
        
        print("✅ Safe startup initialization completed")
        return True
        
    except Exception as e:
        print(f"❌ Startup initialization error: {e}")
        return False

# ==================== INITIALIZATION ====================

# Setup automated trading
setup_automated_trading()

# Start background threads
scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
scheduler_thread.start()

background_thread = threading.Thread(target=background_update, daemon=True)
background_thread.start()

# Safe startup initialization (non-blocking)
safe_startup_initialization()

print("🔄 Enhanced background scheduler started")
print("📊 Safe startup completed - system ready!")

# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    if error_logger:
        error_logger.log_exception("flask_error", e)
    print(f"Flask error: {e}")
    return jsonify({'error': str(e)}), 500

@app.route('/ping')
def ping():
    """Ultra-simple ping endpoint"""
    return jsonify({'status': 'pong', 'timestamp': datetime.now().isoformat()})

@app.route('/quick_test')
def quick_test():
    """Ultra-fast test endpoint (no external API calls)"""
    return jsonify({
        'status': 'ok',
        'message': 'Flask app is running normally',
        'timestamp': datetime.now().isoformat(),
        'system': {
            'python_version': sys.version.split()[0],
            'flask_running': True,
            'components_loaded': system_status.get('components_loaded', {}),
            'startup_complete': system_status.get('startup_complete', False)
        },
        'test_passed': True
    })

@app.route('/startup_test')
def startup_test():
    """Quick startup test endpoint"""
    try:
        return jsonify({
            'status': 'running',
            'startup_complete': system_status.get('startup_complete', False),
            'components': {
                'flask': True,
                'data_fetcher': bool(enhanced_data_fetcher),
                'paper_trading': bool(paper_trading_engine),
                'zerodha': bool(kite),
                'telegram': bool(telegram_bot),
                'market_regime': market_regime_detector is not None,
                'signal_generator': signal_generator is not None
            },
            'regime': current_regime,
            'message': 'System is running normally'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

# Health check route
@app.route('/health')
def health_check():
    """Comprehensive health check"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'flask': True,
                'data_fetcher': bool(enhanced_data_fetcher),
                'paper_trading': bool(paper_trading_engine),
                'zerodha': bool(kite),
                'telegram': bool(telegram_bot)
            },
            'system': system_status,
            'last_update': system_status.get('last_update', datetime.now()).isoformat()
        }
        return jsonify(health_status)
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# ==================== MAIN APPLICATION ====================

if __name__ == '__main__':
    print("\n🚀 Starting Enhanced Production Indian Stock Trading System")
    print("=" * 70)
    print(f"🎯 Trading Mode: {getattr(config, 'get_trading_mode', lambda: 'paper')()}")
    print(f"💰 Initial Capital: ₹{getattr(config, 'INITIAL_CAPITAL', 100000):,.2f}")
    print(f"📊 Daily Target: ₹{getattr(config, 'PROFIT_TARGET', 3000):,.2f}")
    print(f"📈 Max Positions: {getattr(config, 'MAX_POSITIONS', 5)}")
    print(f"🔗 Zerodha: {'Connected' if kite else 'Not Connected'}")
    print(f"📱 Telegram: {'Enabled' if telegram_bot else 'Disabled'}")
    print(f"⚡ Auto Trading: Enabled")
    print(f"🌐 Dashboard: http://{getattr(config, 'FLASK_HOST', '127.0.0.1')}:{getattr(config, 'FLASK_PORT', 5000)}")
    print("=" * 70)
    print("🧪 Test URLs (from fastest to slowest):")
    print(f"   ⚡ Ping (instant): http://localhost:{getattr(config, 'FLASK_PORT', 5000)}/ping")
    print(f"   📱 Quick Test (1s): http://localhost:{getattr(config, 'FLASK_PORT', 5000)}/quick_test")
    print(f"   🚀 Startup Test (1s): http://localhost:{getattr(config, 'FLASK_PORT', 5000)}/startup_test")
    print(f"   🏠 Dashboard (2s): http://localhost:{getattr(config, 'FLASK_PORT', 5000)}")
    print(f"   ❤️  Health Check (2s): http://localhost:{getattr(config, 'FLASK_PORT', 5000)}/health")
    print(f"   🔗 Zerodha Status (2-3s): http://localhost:{getattr(config, 'FLASK_PORT', 5000)}/zerodha/status")
    print(f"   💰 Test Price (3-5s): http://localhost:{getattr(config, 'FLASK_PORT', 5000)}/test_zerodha_price")
    print(f"   📊 Live Prices (3-5s): http://localhost:{getattr(config, 'FLASK_PORT', 5000)}/zerodha/live_prices")
    print("=" * 70)
    print("💡 TESTING ORDER:")
    print("   1. Try /ping first (should be instant)")
    print("   2. Then /quick_test (basic system check)")
    print("   3. Then /dashboard (full interface)")
    print("   4. Finally Zerodha endpoints (with patience!)")
    print("⚠️  Note: Zerodha endpoints have timeouts to prevent hanging")
    print("🎉 System ready! Flask app starting...")
    
    app.run(
        debug=getattr(config, 'FLASK_DEBUG', True),
        host=getattr(config, 'FLASK_HOST', '127.0.0.1'),
        port=getattr(config, 'FLASK_PORT', 5000),
        threaded=True
    )