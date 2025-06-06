"""
DEBUG VERSION: Enhanced main.py with detailed logging to identify hanging issue
"""
import os
import sys
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.append('src')
sys.path.append('config')

def debug_print(message):
    """Print debug message with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] DEBUG: {message}")

# Initialize configuration first
debug_print("Loading configuration...")
from config.settings import Config
config = Config()
debug_print("Configuration loaded")

# Core imports with timing
debug_print("Importing core components...")
start_time = time.time()

try:
    debug_print("Importing DataFetcher...")
    from src.data_fetcher import DataFetcher
    debug_print(f"DataFetcher imported in {time.time() - start_time:.2f}s")
    
    debug_print("Importing TechnicalIndicators...")
    start_time = time.time()
    from src.indicators.technical import TechnicalIndicators
    debug_print(f"TechnicalIndicators imported in {time.time() - start_time:.2f}s")
    
    debug_print("Importing PaperTradingEngine...")
    start_time = time.time()
    from src.engines.paper_trading import PaperTradingEngine
    debug_print(f"PaperTradingEngine imported in {time.time() - start_time:.2f}s")
    
    debug_print("Importing MarketRegimeDetector...")
    start_time = time.time()
    from src.market_regime import MarketRegimeDetector
    debug_print(f"MarketRegimeDetector imported in {time.time() - start_time:.2f}s")
    
    debug_print("Importing SignalGenerator...")
    start_time = time.time()
    from src.strategies.signal_generator import SignalGenerator
    debug_print(f"SignalGenerator imported in {time.time() - start_time:.2f}s")
    
except Exception as e:
    debug_print(f"Import error: {e}")
    sys.exit(1)

# Zerodha Integration
debug_print("Checking Zerodha integration...")
ZERODHA_AVAILABLE = False
try:
    from config.zerodha.auth import ZerodhaAuth
    from config.zerodha.instruments import ZerodhaInstruments
    from config.zerodha.rate_limiter import zerodha_rate_limiter
    ZERODHA_AVAILABLE = True
    debug_print("Zerodha integration available")
except ImportError as e:
    debug_print(f"Zerodha integration not available: {e}")

# Initialize core components with timing
debug_print("Initializing core components...")

debug_print("Creating DataFetcher...")
start_time = time.time()
data_fetcher = DataFetcher()
debug_print(f"DataFetcher created in {time.time() - start_time:.2f}s")

debug_print("Creating TechnicalIndicators...")
start_time = time.time()
technical_indicators = TechnicalIndicators()
debug_print(f"TechnicalIndicators created in {time.time() - start_time:.2f}s")

# Initialize Zerodha components
zerodha_auth = None
zerodha_instruments = None
kite = None

if ZERODHA_AVAILABLE and config.ZERODHA_ENABLED:
    try:
        debug_print("Initializing Zerodha authentication...")
        start_time = time.time()
        zerodha_auth = ZerodhaAuth()
        debug_print(f"ZerodhaAuth created in {time.time() - start_time:.2f}s")
        
        debug_print("Authenticating with Zerodha...")
        start_time = time.time()
        if zerodha_auth.authenticate():
            debug_print(f"Zerodha authentication successful in {time.time() - start_time:.2f}s")
            kite = zerodha_auth.kite
            
            debug_print("Initializing instruments...")
            start_time = time.time()
            zerodha_instruments = ZerodhaInstruments(kite)
            debug_print(f"Instruments initialized in {time.time() - start_time:.2f}s")
            
            debug_print("Zerodha integration ready")
        else:
            debug_print("Zerodha authentication failed")
    except Exception as e:
        debug_print(f"Zerodha initialization error: {e}")

# Enhanced Data Fetcher
debug_print("Creating enhanced data fetcher...")
class DebugEnhancedDataFetcher(DataFetcher):
    def get_current_price(self, symbol):
        debug_print(f"Getting current price for {symbol}...")
        start_time = time.time()
        
        try:
            if kite and zerodha_instruments:
                debug_print(f"Using Zerodha for {symbol}")
                instrument_token = zerodha_instruments.get_instrument_token(symbol)
                if instrument_token:
                    zerodha_rate_limiter.wait_if_needed()
                    zerodha_rate_limiter.record_call()
                    
                    quote = kite.quote([f"NSE:{symbol}"])
                    if f"NSE:{symbol}" in quote:
                        price = quote[f"NSE:{symbol}"]["last_price"]
                        debug_print(f"Zerodha price for {symbol}: ₹{price:.2f} in {time.time() - start_time:.2f}s")
                        return price
        except Exception as e:
            debug_print(f"Zerodha price fetch failed for {symbol}: {e}")
        
        debug_print(f"Using fallback for {symbol}")
        result = super().get_current_price(symbol)
        debug_print(f"Fallback price for {symbol}: ₹{result:.2f} in {time.time() - start_time:.2f}s")
        return result

if kite and zerodha_instruments:
    enhanced_data_fetcher = DebugEnhancedDataFetcher()
    debug_print("Enhanced data fetcher with Zerodha created")
else:
    enhanced_data_fetcher = data_fetcher
    debug_print("Standard data fetcher created")

# Initialize Paper Trading Engine
debug_print("Creating PaperTradingEngine...")
start_time = time.time()
try:
    paper_trading_engine = PaperTradingEngine(
        data_fetcher=enhanced_data_fetcher,
        signal_generator=None,  # Skip for now
        initial_capital=config.INITIAL_CAPITAL
    )
    debug_print(f"PaperTradingEngine created in {time.time() - start_time:.2f}s")
except Exception as e:
    debug_print(f"PaperTradingEngine creation failed: {e}")
    paper_trading_engine = None

# Initialize Market Regime Detector (this might be the bottleneck)
debug_print("Creating MarketRegimeDetector...")
start_time = time.time()
try:
    market_regime_detector = MarketRegimeDetector(enhanced_data_fetcher)
    debug_print(f"MarketRegimeDetector created in {time.time() - start_time:.2f}s")
except Exception as e:
    debug_print(f"MarketRegimeDetector creation failed: {e}")
    market_regime_detector = None

# Initialize Signal Generator (this might also be the bottleneck)
debug_print("Creating SignalGenerator...")
start_time = time.time()
try:
    signal_generator = SignalGenerator(technical_indicators, market_regime_detector)
    debug_print(f"SignalGenerator created in {time.time() - start_time:.2f}s")
except Exception as e:
    debug_print(f"SignalGenerator creation failed: {e}")
    signal_generator = None

# Test Market Regime Detection (likely bottleneck)
debug_print("Testing market regime detection...")
start_time = time.time()
try:
    if market_regime_detector:
        debug_print("Calling detect_current_regime()...")
        regime = market_regime_detector.detect_current_regime()
        debug_print(f"Market regime detection completed in {time.time() - start_time:.2f}s")
        debug_print(f"Detected regime: {regime.get('regime', 'unknown')}")
    else:
        debug_print("Market regime detector not available")
except Exception as e:
    debug_print(f"Market regime detection failed: {e}")

# Initialize Flask app
debug_print("Creating Flask app...")
app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

# Basic routes
@app.route('/')
def home():
    return f"Debug version running. Zerodha: {'Connected' if kite else 'Not connected'}"

@app.route('/debug')
def debug_info():
    return jsonify({
        'zerodha_available': ZERODHA_AVAILABLE,
        'zerodha_connected': bool(kite),
        'components': {
            'data_fetcher': data_fetcher is not None,
            'technical_indicators': technical_indicators is not None,
            'paper_trading_engine': paper_trading_engine is not None,
            'market_regime_detector': market_regime_detector is not None,
            'signal_generator': signal_generator is not None
        }
    })

@app.route('/test_price/<symbol>')
def test_price(symbol):
    try:
        price = enhanced_data_fetcher.get_current_price(symbol.upper())
        return jsonify({
            'symbol': symbol.upper(),
            'price': price,
            'source': 'Zerodha' if kite else 'Fallback'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    debug_print("Starting Flask app...")
    print("\n🔧 DEBUG VERSION READY")
    print("=" * 40)
    print("🌐 Debug info: http://localhost:5000/debug")
    print("💰 Test price: http://localhost:5000/test_price/RELIANCE")
    print("=" * 40)
    
    app.run(
        debug=True,
        host='127.0.0.1',
        port=5000,
        threaded=True
    )