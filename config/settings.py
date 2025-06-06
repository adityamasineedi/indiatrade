# config/settings.py - Enhanced with Zerodha Integration
"""
Enhanced Configuration settings for the Indian Trading System with Zerodha Integration
"""
import os
from dotenv import load_dotenv
import pytz

load_dotenv()

class Config:
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Trading Configuration
    INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', 100000))
    MAX_POSITIONS = int(os.getenv('MAX_POSITIONS', 5))
    RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', 2))  # % of capital
    PROFIT_TARGET = float(os.getenv('PROFIT_TARGET', 3000))  # Daily target
    
    # Zerodha Configuration
    ZERODHA_ENABLED = os.getenv('ZERODHA_ENABLED', 'false').lower() == 'true'
    ZERODHA_API_KEY = os.getenv('ZERODHA_API_KEY')
    ZERODHA_API_SECRET = os.getenv('ZERODHA_API_SECRET')
    ZERODHA_ACCESS_TOKEN = os.getenv('ZERODHA_ACCESS_TOKEN')
    ZERODHA_PAPER_TRADING = os.getenv('ZERODHA_PAPER_TRADING', 'true').lower() == 'true'
    
    # Zerodha API Rate Limits
    ZERODHA_RATE_LIMIT_PER_SECOND = int(os.getenv('ZERODHA_RATE_LIMIT_PER_SECOND', 10))
    ZERODHA_RATE_LIMIT_PER_MINUTE = int(os.getenv('ZERODHA_RATE_LIMIT_PER_MINUTE', 100))
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_system.db')
    
    # Flask Configuration
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'indian-trading-system-secret')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/trading_system.log')
    
    # Market Configuration
    TIMEZONE = pytz.timezone('Asia/Kolkata')
    MARKET_START_TIME = os.getenv('MARKET_START_TIME', '09:15')
    MARKET_END_TIME = os.getenv('MARKET_END_TIME', '15:30')
    
    # Pre-market and post-market timings
    PRE_MARKET_START = os.getenv('PRE_MARKET_START', '09:00')
    PRE_MARKET_END = os.getenv('PRE_MARKET_END', '09:15')
    POST_MARKET_START = os.getenv('POST_MARKET_START', '15:30')
    POST_MARKET_END = os.getenv('POST_MARKET_END', '16:00')
    
    # Technical Indicators Settings
    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    
    EMA_FAST = 9
    EMA_MEDIUM = 21
    EMA_SLOW = 50
    
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    SUPERTREND_PERIOD = 10
    SUPERTREND_MULTIPLIER = 3
    
    # Volume Settings
    VOLUME_MA_PERIOD = 20
    VOLUME_SPIKE_THRESHOLD = 1.5  # 1.5x average volume
    
    # Stocks to Trade (NSE symbols)
    WATCHLIST = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
        'ICICIBANK', 'KOTAKBANK', 'BHARTIARTL', 'ITC', 'SBIN',
        'BAJFINANCE', 'ASIANPAINT', 'MARUTI', 'AXISBANK', 'LT',
        'HCLTECH', 'WIPRO', 'ULTRACEMCO', 'TATAMOTORS', 'POWERGRID'
    ]
    
    # Market Regime Settings
    BULL_THRESHOLD = 0.6  # 60% stocks above EMA21
    BEAR_THRESHOLD = 0.4  # 40% stocks above EMA21
    
    # Backtest Settings
    BACKTEST_DAYS = 30
    COMMISSION = 0.05  # 0.05% per trade
    
    # Paper Trading vs Live Trading
    PAPER_TRADING = not ZERODHA_ENABLED or ZERODHA_PAPER_TRADING
    
    # Order Configuration
    ORDER_VARIETY = 'regular'  # regular, bo, co, iceberg, auction
    ORDER_TYPE = 'MARKET'     # MARKET, LIMIT, SL, SL-M
    ORDER_PRODUCT = 'CNC'     # CNC, MIS, NRML
    
    # Risk Management
    MAX_DRAWDOWN_PERCENT = float(os.getenv('MAX_DRAWDOWN_PERCENT', 5))  # 5% max drawdown
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', 2))        # 2% stop loss
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', 4))    # 4% take profit
    
    # Position Sizing
    POSITION_SIZE_METHOD = os.getenv('POSITION_SIZE_METHOD', 'fixed_risk')  # fixed_risk, fixed_amount, percentage
    FIXED_POSITION_AMOUNT = float(os.getenv('FIXED_POSITION_AMOUNT', 10000))  # ₹10,000 per position
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        missing_fields = []
        
        # Telegram validation
        if not cls.TELEGRAM_BOT_TOKEN:
            missing_fields.append('TELEGRAM_BOT_TOKEN')
        if not cls.TELEGRAM_CHAT_ID:
            missing_fields.append('TELEGRAM_CHAT_ID')
        
        # Zerodha validation (if enabled)
        if cls.ZERODHA_ENABLED:
            if not cls.ZERODHA_API_KEY:
                missing_fields.append('ZERODHA_API_KEY')
            if not cls.ZERODHA_API_SECRET:
                missing_fields.append('ZERODHA_API_SECRET')
            if not cls.ZERODHA_PAPER_TRADING and not cls.ZERODHA_ACCESS_TOKEN:
                missing_fields.append('ZERODHA_ACCESS_TOKEN')
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True
    
    @classmethod
    def get_trading_mode(cls):
        """Get current trading mode"""
        if cls.ZERODHA_ENABLED and not cls.ZERODHA_PAPER_TRADING:
            return "LIVE_ZERODHA"
        elif cls.ZERODHA_ENABLED and cls.ZERODHA_PAPER_TRADING:
            return "PAPER_ZERODHA" 
        else:
            return "PAPER_SIMULATION"
    
    @classmethod
    def is_market_hours(cls):
        """Check if current time is within market hours"""
        from datetime import datetime
        
        now = datetime.now(cls.TIMEZONE)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Parse market times
        market_start = datetime.strptime(cls.MARKET_START_TIME, '%H:%M').time()
        market_end = datetime.strptime(cls.MARKET_END_TIME, '%H:%M').time()
        
        current_time = now.time()
        
        return market_start <= current_time <= market_end
    
    @classmethod
    def get_market_status(cls):
        """Get detailed market status"""
        from datetime import datetime
        
        now = datetime.now(cls.TIMEZONE)
        current_time = now.time()
        
        # Market timings
        pre_market_start = datetime.strptime(cls.PRE_MARKET_START, '%H:%M').time()
        pre_market_end = datetime.strptime(cls.PRE_MARKET_END, '%H:%M').time()
        market_start = datetime.strptime(cls.MARKET_START_TIME, '%H:%M').time()
        market_end = datetime.strptime(cls.MARKET_END_TIME, '%H:%M').time()
        post_market_start = datetime.strptime(cls.POST_MARKET_START, '%H:%M').time()
        post_market_end = datetime.strptime(cls.POST_MARKET_END, '%H:%M').time()
        
        if now.weekday() >= 5:
            return {
                'status': 'CLOSED',
                'session': 'WEEKEND',
                'is_trading': False,
                'next_open': 'Monday 09:15'
            }
        
        if pre_market_start <= current_time < pre_market_end:
            return {
                'status': 'PRE_MARKET',
                'session': 'PRE_OPEN',
                'is_trading': False,
                'next_session': f'Market opens at {cls.MARKET_START_TIME}'
            }
        elif market_start <= current_time <= market_end:
            return {
                'status': 'OPEN',
                'session': 'MARKET_HOURS',
                'is_trading': True,
                'closes_at': cls.MARKET_END_TIME
            }
        elif post_market_start <= current_time <= post_market_end:
            return {
                'status': 'POST_MARKET',
                'session': 'AFTER_MARKET',
                'is_trading': False,
                'next_session': 'Tomorrow 09:15'
            }
        else:
            return {
                'status': 'CLOSED',
                'session': 'AFTER_HOURS',
                'is_trading': False,
                'next_session': 'Tomorrow 09:15'
            }
    
    @classmethod
    def print_config_summary(cls):
        """Print configuration summary"""
        print("⚙️ Trading System Configuration")
        print("=" * 40)
        print(f"🎯 Trading Mode: {cls.get_trading_mode()}")
        print(f"💰 Initial Capital: ₹{cls.INITIAL_CAPITAL:,.2f}")
        print(f"📊 Max Positions: {cls.MAX_POSITIONS}")
        print(f"⚡ Risk per Trade: {cls.RISK_PER_TRADE}%")
        print(f"🎯 Daily Target: ₹{cls.PROFIT_TARGET:,.2f}")
        print(f"📈 Watchlist: {len(cls.WATCHLIST)} stocks")
        print(f"🔗 Zerodha: {'Enabled' if cls.ZERODHA_ENABLED else 'Disabled'}")
        print(f"📱 Telegram: {'Configured' if cls.TELEGRAM_BOT_TOKEN else 'Not configured'}")
        
        market_status = cls.get_market_status()
        print(f"🕐 Market: {market_status['status']} ({market_status['session']})")
        print("=" * 40)