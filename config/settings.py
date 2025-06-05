 
"""
Configuration settings for the Indian Trading System
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
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_system.db')
    
    # Flask Configuration
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/trading_system.log')
    
    # Market Configuration
    TIMEZONE = pytz.timezone('Asia/Kolkata')
    MARKET_START_TIME = os.getenv('MARKET_START_TIME', '09:15')
    MARKET_END_TIME = os.getenv('MARKET_END_TIME', '15:30')
    
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
    
    # Paper Trading
    PAPER_TRADING = True  # Set to False for live trading
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_fields = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
        missing_fields = []
        
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True