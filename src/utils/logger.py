"""
Logging utility for Indian Stock Trading System
Provides structured logging with file and console output
"""
import logging
import logging.handlers
import os
from datetime import datetime
from config.settings import Config

def setup_logging():
    """Setup logging configuration for the trading system"""
    config = Config()
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create main logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Create separate loggers for different components
    setup_component_loggers()
    
    logger.info("Logging system initialized")
    return logger

def setup_component_loggers():
    """Setup specialized loggers for different components"""
    
    # Trading logger
    trading_logger = logging.getLogger('trading')
    trading_handler = logging.FileHandler('logs/trading.log')
    trading_handler.setFormatter(logging.Formatter(
        '%(asctime)s - TRADE - %(levelname)s - %(message)s'
    ))
    trading_logger.addHandler(trading_handler)
    
    # Signals logger
    signals_logger = logging.getLogger('signals')
    signals_handler = logging.FileHandler('logs/signals.log')
    signals_handler.setFormatter(logging.Formatter(
        '%(asctime)s - SIGNAL - %(levelname)s - %(message)s'
    ))
    signals_logger.addHandler(signals_handler)
    
    # Portfolio logger
    portfolio_logger = logging.getLogger('portfolio')
    portfolio_handler = logging.FileHandler('logs/portfolio.log')
    portfolio_handler.setFormatter(logging.Formatter(
        '%(asctime)s - PORTFOLIO - %(levelname)s - %(message)s'
    ))
    portfolio_logger.addHandler(portfolio_handler)
    
    # Error logger
    error_logger = logging.getLogger('errors')
    error_handler = logging.FileHandler('logs/errors.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - ERROR - %(name)s - %(funcName)s:%(lineno)d - %(message)s'
    ))
    error_logger.addHandler(error_handler)

class TradingLogger:
    """Specialized logger for trading operations"""
    
    def __init__(self):
        self.logger = logging.getLogger('trading')
        
    def log_signal_generated(self, signal):
        """Log when a trading signal is generated"""
        self.logger.info(
            f"SIGNAL_GENERATED | {signal['symbol']} | {signal['action']} | "
            f"Price: ₹{signal['price']:.2f} | Confidence: {signal['confidence']:.1f}% | "
            f"Reasons: {', '.join(signal.get('reasons', []))}"
        )
    
    def log_trade_executed(self, trade):
        """Log when a trade is executed"""
        pnl_str = f" | P&L: ₹{trade['pnl']:.2f}" if trade.get('pnl') is not None else ""
        self.logger.info(
            f"TRADE_EXECUTED | {trade['symbol']} | {trade['action']} | "
            f"Price: ₹{trade['price']:.2f} | Qty: {trade['quantity']} | "
            f"Amount: ₹{trade['amount']:.2f}{pnl_str}"
        )
    
    def log_position_update(self, symbol, action, details):
        """Log position updates"""
        self.logger.info(
            f"POSITION_UPDATE | {symbol} | {action} | {details}"
        )
    
    def log_risk_event(self, event_type, symbol, details):
        """Log risk management events"""
        self.logger.warning(
            f"RISK_EVENT | {event_type} | {symbol} | {details}"
        )
    
    def log_market_regime_change(self, old_regime, new_regime, confidence):
        """Log market regime changes"""
        self.logger.info(
            f"REGIME_CHANGE | {old_regime} → {new_regime} | Confidence: {confidence:.1f}%"
        )

class PerformanceLogger:
    """Logger for performance tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
        
    def log_daily_performance(self, date, portfolio_value, daily_pnl, trades_count):
        """Log daily performance metrics"""
        self.logger.info(
            f"DAILY_PERFORMANCE | {date} | Portfolio: ₹{portfolio_value:,.2f} | "
            f"Daily P&L: ₹{daily_pnl:,.2f} | Trades: {trades_count}"
        )
    
    def log_backtest_results(self, results):
        """Log backtest results"""
        summary = results.get('summary', {})
        self.logger.info(
            f"BACKTEST_COMPLETED | Return: {summary.get('total_return_pct', 0):.2f}% | "
            f"Win Rate: {summary.get('win_rate', 0):.1f}% | "
            f"Total Trades: {summary.get('total_trades', 0)} | "
            f"Profit Factor: {summary.get('profit_factor', 0):.2f}"
        )
    
    def log_strategy_performance(self, strategy_name, metrics):
        """Log strategy-specific performance"""
        self.logger.info(
            f"STRATEGY_PERFORMANCE | {strategy_name} | {metrics}"
        )

class SystemLogger:
    """Logger for system events and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('system')
        
    def log_system_startup(self, config_info):
        """Log system startup"""
        self.logger.info(f"SYSTEM_STARTUP | Config: {config_info}")
    
    def log_system_shutdown(self, reason="Normal"):
        """Log system shutdown"""
        self.logger.info(f"SYSTEM_SHUTDOWN | Reason: {reason}")
    
    def log_data_fetch(self, source, symbols_count, success_rate):
        """Log data fetching operations"""
        self.logger.info(
            f"DATA_FETCH | Source: {source} | Symbols: {symbols_count} | "
            f"Success Rate: {success_rate:.1f}%"
        )
    
    def log_api_call(self, api_name, endpoint, status, response_time=None):
        """Log API calls"""
        time_str = f" | Time: {response_time:.2f}s" if response_time else ""
        self.logger.info(
            f"API_CALL | {api_name} | {endpoint} | Status: {status}{time_str}"
        )
    
    def log_telegram_event(self, event_type, success, message=None):
        """Log Telegram bot events"""
        status = "SUCCESS" if success else "FAILED"
        msg_str = f" | Message: {message}" if message else ""
        self.logger.info(f"TELEGRAM | {event_type} | {status}{msg_str}")
    
    def log_database_operation(self, operation, table, records_affected=None):
        """Log database operations"""
        records_str = f" | Records: {records_affected}" if records_affected else ""
        self.logger.info(f"DATABASE | {operation} | {table}{records_str}")

class ErrorLogger:
    """Specialized error logger with context"""
    
    def __init__(self):
        self.logger = logging.getLogger('errors')
        
    def log_exception(self, context, exception, additional_info=None):
        """Log exceptions with context"""
        info_str = f" | Additional Info: {additional_info}" if additional_info else ""
        self.logger.error(
            f"EXCEPTION | Context: {context} | Error: {str(exception)}{info_str}",
            exc_info=True
        )
    
    def log_data_error(self, symbol, error_type, details):
        """Log data-related errors"""
        self.logger.error(f"DATA_ERROR | {symbol} | {error_type} | {details}")
    
    def log_trade_error(self, symbol, action, error, trade_data=None):
        """Log trading errors"""
        data_str = f" | Data: {trade_data}" if trade_data else ""
        self.logger.error(f"TRADE_ERROR | {symbol} | {action} | {error}{data_str}")
    
    def log_connection_error(self, service, error):
        """Log connection errors"""
        self.logger.error(f"CONNECTION_ERROR | {service} | {error}")

def get_logger(name):
    """Get a logger instance"""
    return logging.getLogger(name)

def get_trading_logger():
    """Get trading-specific logger"""
    return TradingLogger()

def get_performance_logger():
    """Get performance-specific logger"""
    return PerformanceLogger()

def get_system_logger():
    """Get system-specific logger"""
    return SystemLogger()

def get_error_logger():
    """Get error-specific logger"""
    return ErrorLogger()

class LogAnalyzer:
    """Analyze log files for insights"""
    
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        
    def analyze_trading_patterns(self, days=7):
        """Analyze trading patterns from logs"""
        try:
            patterns = {
                'total_signals': 0,
                'total_trades': 0,
                'win_rate': 0,
                'most_traded_symbols': {},
                'error_rate': 0,
                'peak_trading_hours': {}
            }
            
            # This would analyze log files and extract patterns
            # Implementation would parse log files and calculate metrics
            
            return patterns
            
        except Exception as e:
            get_error_logger().log_exception("log_analysis", e)
            return {}
    
    def get_error_summary(self, days=1):
        """Get summary of errors from logs"""
        try:
            error_summary = {
                'total_errors': 0,
                'error_types': {},
                'critical_errors': 0,
                'most_common_errors': []
            }
            
            # Implementation would parse error logs
            
            return error_summary
            
        except Exception as e:
            get_error_logger().log_exception("error_summary", e)
            return {}

# Context manager for performance logging
class LogPerformance:
    """Context manager to log function performance"""
    
    def __init__(self, operation_name, logger=None):
        self.operation_name = operation_name
        self.logger = logger or get_system_logger()
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.logger.info(f"PERFORMANCE | {self.operation_name} | Duration: {duration:.2f}s")
        else:
            self.logger.logger.error(
                f"PERFORMANCE | {self.operation_name} | FAILED | Duration: {duration:.2f}s | Error: {exc_val}"
            )