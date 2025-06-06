# 🚀 Indian Stock Trading System

A comprehensive, automated paper trading system for Indian stock markets designed to earn ₹3,000/day consistently through technical analysis and market regime detection.

## 🎯 Key Features

- **📊 Advanced Technical Analysis**: RSI, MACD, EMA, Supertrend indicators
- **🔍 Market Regime Detection**: Bull, Bear, Sideways market identification
- **📈 Paper Trading Engine**: Risk-free trading simulation
- **⚡ Telegram Alerts**: Real-time trading signals and notifications
- **🌐 Web Dashboard**: Beautiful Flask-based interface
- **📋 Backtesting Engine**: 30-day P&L analysis and win rate tracking
- **🤖 Fully Automated**: Plug-and-play system with scheduled execution
- **💾 SQLite Database**: Local data storage for trades and signals
- **📱 Responsive Design**: Works on desktop and mobile devices

## 🏗️ System Architecture

```
indian_trading_system/
├── main.py                 # Flask web application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration template
├── README.md              # This file
├── config/
│   ├── __init__.py
│   └── settings.py        # Configuration management
├── src/
│   ├── __init__.py
│   ├── data_fetcher.py    # NSEpy data fetching
│   ├── market_regime.py   # Market regime detection
│   ├── indicators/
│   │   ├── __init__.py
│   │   └── technical.py   # Technical indicators (pandas-ta)
│   ├── strategies/
│   │   ├── __init__.py
│   │   └── signal_generator.py  # Trading signal generation
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── backtest.py    # Backtesting engine
│   │   └── paper_trading.py  # Paper trading engine
│   └── utils/
│       ├── __init__.py
│       ├── telegram_bot.py  # Telegram integration
│       └── logger.py      # Logging utilities
├── templates/
│   ├── base.html          # Base HTML template
│   ├── dashboard.html     # Main dashboard
│   └── trades.html        # Trade history page
├── static/
│   ├── css/
│   │   └── style.css      # Custom styles
│   └── js/
│       └── dashboard.js   # Dashboard JavaScript
├── logs/                  # Log files directory
└── data/                  # Data storage directory
```

## ⚡ Quick Start

### 1. Clone and Setup

```bash
# Create project directory
mkdir indian_trading_system
cd indian_trading_system

# Create folder structure
mkdir -p {data,src,templates,static,logs,config,tests}
mkdir -p static/{css,js,images}
mkdir -p src/{indicators,strategies,engines,utils}

# Create all required files (copy the code from artifacts)
```

### 2. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Configuration:**
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Trading Configuration
INITIAL_CAPITAL=100000
MAX_POSITIONS=5
RISK_PER_TRADE=2
PROFIT_TARGET=3000

# Other settings (optional)
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

### 4. Start the System

```bash
python main.py
```

Visit `http://localhost:5000` to access the dashboard.

## 🤖 Setting Up Telegram Bot

### 1. Create Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token to your `.env` file

### 2. Get Chat ID

1. Start a chat with your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find your chat ID in the response
4. Add it to your `.env` file

## 📊 Trading Strategy

### Market Regime Detection

The system identifies three market states:

- **🐂 Bull Market**: Aggressive long positions, trend following
- **🐻 Bear Market**: Conservative approach, short opportunities  
- **↔️ Sideways Market**: Range trading, support/resistance levels

### Technical Indicators Used

1. **EMA (9/21/50)**: Trend identification and crossover signals
2. **RSI (14)**: Overbought/oversold conditions and divergences
3. **MACD**: Momentum and trend strength confirmation
4. **Supertrend**: Simple trend-following filter
5. **Volume Analysis**: Confirmation of breakouts and signals

### Signal Generation Logic

```python
# Bull Market Strategy
- Strong uptrend (trend_score >= 70): 30 points
- EMA bullish crossover: 25 points  
- RSI in sweet spot (40-65): 20 points
- MACD bullish crossover: 15 points
- Supertrend bullish: 15 points
- Volume spike confirmation: 10 points
- Price above key EMAs: 10 points

# Minimum 60 points + 3 conditions for BUY signal
```

## 🔧 API Endpoints

### Portfolio Management
- `GET /api/portfolio` - Get current portfolio status
- `GET /api/system_status` - Get system health status

### Trading Operations  
- `POST /api/update_system` - Manual system update
- `POST /api/run_trading_session` - Execute trading session
- `POST /api/run_backtest` - Run backtesting analysis

### Data & Signals
- `GET /api/signals` - Get latest trading signals
- `GET /api/regime` - Get current market regime
- `GET /api/market_data/<symbol>` - Get stock data with indicators

### Telegram Integration
- `POST /api/test_telegram` - Test bot connection
- `POST /api/send_portfolio_update` - Send portfolio via Telegram

## 📈 Dashboard Features

### Real-Time Monitoring
- **Portfolio Value**: Live portfolio tracking with P&L
- **Daily Target Progress**: Visual progress toward ₹3,000 goal
- **Active Positions**: Current holdings with unrealized P&L
- **Market Regime**: Bull/Bear/Sideways detection with confidence

### Trading Signals
- **High-Confidence Alerts**: Signals with 70%+ confidence
- **Multi-Factor Analysis**: Combines multiple technical indicators
- **Risk Management**: Automatic stop-loss and target calculations
- **Volume Confirmation**: Ensures genuine breakouts

### Trade History
- **Complete Trade Log**: All paper trades with P&L tracking
- **Performance Analytics**: Win rate, profit factor, drawdown
- **Symbol Performance**: Per-stock trading statistics
- **Export Functionality**: CSV export for further analysis

## 🔄 Automated Scheduling

The system automatically runs:

- **Market Hours**: Trading sessions every hour (9:20 AM - 3:20 PM)
- **Data Updates**: Every 5 minutes during market hours
- **Daily Summary**: End-of-day Telegram report at 4:00 PM
- **System Health**: Continuous monitoring and error reporting

## ⚠️ Risk Management

### Position Sizing
- **Maximum Risk**: 2% of capital per trade
- **Position Limit**: Maximum 5 concurrent positions
- **Capital Allocation**: Maximum 20% per single position

### Stop Loss Strategy
- **ATR-Based**: 2x Average True Range for stop distance
- **Technical Levels**: Support/resistance based stops
- **Time-Based**: Maximum 10-day holding period

### Paper Trading Safety
- **No Real Money**: All trades are simulated
- **Real Market Data**: Uses actual NSE prices
- **Realistic Execution**: Includes commission and slippage

## 📊 Performance Metrics

### Daily Targets
- **Primary Goal**: ₹3,000 daily profit
- **Win Rate Target**: >60% successful trades
- **Risk-Reward**: Minimum 1.5:1 ratio
- **Maximum Drawdown**: <5% of capital

### Key Performance Indicators
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Worst peak-to-trough decline
- **Profit Factor**: Gross profit / Gross loss
- **Win Rate**: Percentage of profitable trades

## 🛠️ Customization

### Adding New Indicators

```python
# In src/indicators/technical.py
def add_custom_indicator(self, df):
    # Add your custom indicator logic
    df['custom_signal'] = your_calculation
    return df
```

### Modifying Strategy

```python
# In src/strategies/signal_generator.py
def custom_strategy(self, signal, latest, prev, data):
    # Implement your strategy logic
    if your_condition:
        signal['action'] = 'BUY'
        signal['confidence'] = 80
    return signal
```

### Adding New Watchlist

```python
# In config/settings.py
WATCHLIST = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY',
    # Add your preferred stocks
]
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Error**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Data Fetch Error**: NSEpy might be temporarily down
   ```bash
   # Check NSE website status
   # Wait and retry after some time
   ```

3. **Telegram Not Working**: Verify bot token and chat ID
   ```bash
   # Test API endpoint
   curl "https://api.telegram.org/bot<TOKEN>/getMe"
   ```

4. **Port Already in Use**: Change Flask port
   ```bash
   export FLASK_PORT=8000
   python main.py
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

### Log Files
- `logs/trading_system.log` - Main application log
- `logs/trading.log` - Trade-specific events
- `logs/signals.log` - Signal generation log
- `logs/errors.log` - Error tracking

## 📚 Educational Resources

### Technical Analysis
- [Investopedia Technical Analysis](https://www.investopedia.com/technical-analysis-4689657)
- [TradingView Education](https://www.tradingview.com/education/)

### Indian Stock Market
- [NSE Official Website](https://www.nseindia.com/)
- [BSE Official Website](https://www.bseindia.com/)

### Programming & APIs
- [NSEpy Documentation](https://nsepy.readthedocs.io/)
- [pandas-ta Documentation](https://github.com/twopirllc/pandas-ta)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## ⚖️ Legal Disclaimer

**Important**: This is a paper trading system for educational purposes only.

- **No Financial Advice**: This system is not providing financial advice
- **Educational Purpose**: Designed for learning technical analysis
- **No Guarantees**: Past performance does not guarantee future results
- **Risk Warning**: Real trading involves risk of capital loss
- **Compliance**: Ensure compliance with local trading regulations

## 📞 Support

- **Issues**: Create GitHub issue for bugs
- **Features**: Suggest improvements via discussions
- **Documentation**: Check README and code comments
- **Community**: Join trading discussions on relevant forums

## 🎉 Achievements

- ✅ **Reliable Data Source**: Uses NSEpy instead of unstable APIs
- ✅ **Professional UI**: Modern, responsive web interface
- ✅ **Real-time Updates**: Live dashboard with auto-refresh
- ✅ **Comprehensive Logging**: Detailed system monitoring
- ✅ **Paper Trading**: Safe learning environment
- ✅ **Telegram Integration**: Mobile notifications
- ✅ **Backtesting**: Historical performance analysis
- ✅ **Multi-timeframe**: Works in all market conditions

## 🚀 Future Enhancements (Phase 2+)

- **Machine Learning**: XGBoost + LSTM models
- **Auto-retraining**: Weekly model updates
- **Live Trading**: Zerodha API integration
- **Advanced Charts**: TradingView-style charts
- **Mobile App**: React Native application
- **Portfolio Optimization**: Kelly Criterion position sizing
- **Social Trading**: Copy trading features
- **News Sentiment**: News-based signal filtering

---

**Made with ❤️ for Indian Stock Market Traders**

*Target: ₹3,000/day | Strategy: Technical Analysis + Market Regime | Mode: Paper Trading*

.venv\Scripts\activate
pip install -r requirements.txt