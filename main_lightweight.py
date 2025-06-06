"""
Lightweight version of main.py for testing Zerodha integration
Minimal overhead, faster startup, focused on core functionality
"""
import os
import sys
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.append('src')
sys.path.append('config')

# Core imports only
from src.data_fetcher import DataFetcher
from src.indicators.technical import TechnicalIndicators
from src.engines.paper_trading import PaperTradingEngine
from config.settings import Config

# Zerodha Integration
ZERODHA_AVAILABLE = False
try:
    from config.zerodha.auth import ZerodhaAuth
    from config.zerodha.instruments import ZerodhaInstruments
    from config.zerodha.rate_limiter import zerodha_rate_limiter
    ZERODHA_AVAILABLE = True
    print("✅ Zerodha integration available")
except ImportError as e:
    print(f"⚠️ Zerodha integration not available: {e}")

# Initialize configuration
config = Config()
print(f"🎯 Trading Mode: {config.get_trading_mode()}")
print(f"💰 Initial Capital: ₹{config.INITIAL_CAPITAL:,.2f}")

# Initialize core components
data_fetcher = DataFetcher()
technical_indicators = TechnicalIndicators()

# Initialize Zerodha (if available)
zerodha_auth = None
zerodha_instruments = None
kite = None

if ZERODHA_AVAILABLE and config.ZERODHA_ENABLED:
    try:
        print("🔗 Initializing Zerodha...")
        zerodha_auth = ZerodhaAuth()
        
        if zerodha_auth.authenticate():
            kite = zerodha_auth.kite
            zerodha_instruments = ZerodhaInstruments(kite)
            print("✅ Zerodha connected")
        else:
            print("⚠️ Zerodha authentication required")
    except Exception as e:
        print(f"❌ Zerodha initialization failed: {e}")

# Enhanced Data Fetcher (Lightweight)
class LightweightEnhancedDataFetcher(DataFetcher):
    """Lightweight enhanced data fetcher"""
    
    def __init__(self, kite_instance=None, instruments=None):
        super().__init__()
        self.kite = kite_instance
        self.instruments = instruments
    
    def get_current_price(self, symbol):
        """Get current price with Zerodha integration"""
        try:
            if self.kite and self.instruments:
                instrument_token = self.instruments.get_instrument_token(symbol)
                if instrument_token:
                    zerodha_rate_limiter.wait_if_needed()
                    zerodha_rate_limiter.record_call()
                    
                    quote = self.kite.quote([f"NSE:{symbol}"])
                    if f"NSE:{symbol}" in quote:
                        price = quote[f"NSE:{symbol}"]["last_price"]
                        print(f"💎 {symbol}: ₹{price:.2f} (Zerodha)")
                        return price
        except Exception as e:
            print(f"⚠️ Zerodha price fetch failed for {symbol}: {e}")
        
        # Fallback to parent method
        return super().get_current_price(symbol)

# Initialize enhanced data fetcher
if kite and zerodha_instruments:
    enhanced_data_fetcher = LightweightEnhancedDataFetcher(kite, zerodha_instruments)
    print("✅ Enhanced data fetcher with Zerodha")
else:
    enhanced_data_fetcher = data_fetcher
    print("📊 Standard data fetcher")

# Initialize paper trading engine
try:
    paper_trading_engine = PaperTradingEngine(
        data_fetcher=enhanced_data_fetcher,
        signal_generator=None,  # Skip signal generator for now
        initial_capital=config.INITIAL_CAPITAL
    )
    print(f"✅ Paper trading engine: ₹{config.INITIAL_CAPITAL:,.2f}")
except Exception as e:
    print(f"❌ Paper trading engine failed: {e}")
    paper_trading_engine = None

# Initialize Telegram (optional)
telegram_bot = None
try:
    from src.utils.telegram_bot import TelegramBot
    telegram_bot = TelegramBot()
    print("📱 Telegram bot ready")
except Exception as e:
    print(f"⚠️ Telegram bot failed: {e}")

# Global state
portfolio_status = {}
system_status = {
    'running': True,
    'last_update': datetime.now(),
    'zerodha_connected': bool(kite),
    'trading_mode': config.get_trading_mode(),
    'market_status': config.get_market_status()
}

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

# ==================== CORE ROUTES ====================

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Lightweight dashboard"""
    try:
        # Simple portfolio data
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
            except Exception as e:
                print(f"⚠️ Portfolio error: {e}")
        
        # Market status
        market_status = config.get_market_status()
        
        # Simple regime data
        regime = {
            'regime': 'testing',
            'confidence': 75.0,
            'indicators': {'market_breadth': 50.0}
        }
        
        return render_template(
            'dashboard.html',
            portfolio=portfolio,
            daily_pnl=portfolio['daily_pnl'],
            regime=regime,
            signals=[],  # Empty for now
            market_status=market_status,
            trade_count=0,
            system_status=system_status,
            zerodha_connected=bool(kite),
            trading_mode=config.get_trading_mode(),
            min=min, max=max, len=len, abs=abs, round=round
        )
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return f"Dashboard Error: {str(e)}"

@app.route('/trades')
def trades():
    """Simple trades page"""
    return render_template('trades.html', trades=[], days=30)

# ==================== API ENDPOINTS ====================

@app.route('/api/portfolio')
def api_portfolio():
    """Portfolio API"""
    try:
        portfolio_data = {
            'total_value': config.INITIAL_CAPITAL,
            'daily_pnl': 0.0,
            'total_pnl': 0.0,
            'cash': config.INITIAL_CAPITAL,
            'positions_count': 0,
            'return_pct': 0.0,
            'target_progress': 0.0
        }
        
        if paper_trading_engine:
            try:
                real_data = paper_trading_engine.get_portfolio_status()
                if real_data:
                    portfolio_data.update(real_data)
            except Exception as e:
                print(f"Portfolio API error: {e}")
        
        return jsonify(portfolio_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_status')
def api_system_status():
    """System status API"""
    try:
        status = {
            'running': True,
            'zerodha_connected': bool(kite),
            'trading_mode': config.get_trading_mode(),
            'market_status': config.get_market_status(),
            'last_update': datetime.now().isoformat()
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/zerodha/status')
def zerodha_status():
    """Zerodha status"""
    try:
        status = {
            'available': ZERODHA_AVAILABLE,
            'enabled': config.ZERODHA_ENABLED,
            'connected': bool(kite),
            'trading_mode': config.get_trading_mode()
        }
        
        if kite:
            try:
                profile = kite.profile()
                status.update({
                    'user_name': profile.get('user_name'),
                    'user_id': profile.get('user_id')
                })
            except Exception as e:
                status['profile_error'] = str(e)
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/zerodha/live_prices')
def get_live_prices():
    """Get live prices"""
    try:
        if not kite:
            return jsonify({'error': 'Zerodha not connected'}), 400
        
        symbols = request.args.get('symbols', 'RELIANCE,TCS,INFY').split(',')
        live_data = {}
        
        for symbol in symbols[:5]:  # Limit to 5 symbols
            try:
                zerodha_rate_limiter.wait_if_needed()
                zerodha_rate_limiter.record_call()
                
                quote = kite.quote([f"NSE:{symbol}"])
                if f"NSE:{symbol}" in quote:
                    data = quote[f"NSE:{symbol}"]
                    live_data[symbol] = {
                        'last_price': data['last_price'],
                        'change': data.get('net_change', 0),
                        'volume': data.get('volume', 0)
                    }
            except Exception as e:
                live_data[symbol] = {'error': str(e)}
        
        return jsonify(live_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_zerodha_price')
def test_zerodha_price():
    """Test Zerodha price fetching"""
    try:
        if not enhanced_data_fetcher:
            return jsonify({'error': 'Data fetcher not available'})
        
        # Test getting current price
        price = enhanced_data_fetcher.get_current_price('RELIANCE')
        
        return jsonify({
            'symbol': 'RELIANCE',
            'price': price,
            'source': 'Zerodha' if kite else 'Yahoo Finance',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== MAIN APPLICATION ====================

if __name__ == '__main__':
    print("\n🚀 Starting Lightweight Indian Stock Trading System")
    print("=" * 60)
    print(f"🎯 Mode: {config.get_trading_mode()}")
    print(f"💰 Capital: ₹{config.INITIAL_CAPITAL:,.2f}")
    print(f"🔗 Zerodha: {'Connected' if kite else 'Not Connected'}")
    print(f"📱 Telegram: {'Ready' if telegram_bot else 'Not Available'}")
    print(f"🌐 Dashboard: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print("=" * 60)
    print("📊 This is a lightweight version for testing")
    print("🧪 Test Zerodha: http://localhost:5000/test_zerodha_price")
    print("📈 Live Prices: http://localhost:5000/zerodha/live_prices")
    print("=" * 60)
    
    app.run(
        debug=config.FLASK_DEBUG,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        threaded=True
    )