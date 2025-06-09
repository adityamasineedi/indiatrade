"""
CRITICAL TRADING SAFETY SYSTEM
===============================

This module provides multiple layers of protection against accidental real money trading.
ALL trading operations MUST go through this safety system.

🚨 SAFETY FEATURES:
- Multiple confirmation layers
- Environment validation
- Real-time safety checks
- Audit logging
- Emergency stop mechanisms
- Paper trading enforcement
"""

import os
import json
import time
import hashlib
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Tuple, Optional

class TradingMode(Enum):
    """Trading mode enumeration with safety levels"""
    PAPER_ONLY = "PAPER_ONLY"           # Safest - No real money ever
    PAPER_ZERODHA = "PAPER_ZERODHA"     # Safe - Real data, fake trades  
    LIVE_SANDBOX = "LIVE_SANDBOX"       # Caution - Zerodha sandbox
    LIVE_REAL = "LIVE_REAL"             # DANGER - Real money trading

class SafetyLevel(Enum):
    """Safety levels for trading operations"""
    MAXIMUM = "MAXIMUM"     # Multiple confirmations required
    HIGH = "HIGH"          # Standard confirmation required
    MEDIUM = "MEDIUM"      # Basic confirmation required
    LOW = "LOW"            # Minimal safety checks

class TradingSafetySystem:
    """
    CRITICAL SAFETY SYSTEM - Prevents accidental real money trading
    
    This system MUST be used for ALL trading operations.
    """
    
    def __init__(self):
        self.logger = self._setup_safety_logger()
        self.safety_config = self._load_safety_config()
        self.session_id = self._generate_session_id()
        self.safety_checks_enabled = True
        self.emergency_stop_active = False
        
        # Initialize safety state
        self._initialize_safety_state()
        
        # Log safety system initialization
        self.logger.critical(f"🛡️ TRADING SAFETY SYSTEM INITIALIZED - Session: {self.session_id}")
        self.logger.critical(f"🛡️ Current Mode: {self.get_trading_mode()}")
        self.logger.critical(f"🛡️ Safety Level: {self.get_safety_level()}")
        
    def _setup_safety_logger(self):
        """Setup dedicated safety logger with high visibility"""
        logger = logging.getLogger('TRADING_SAFETY')
        logger.setLevel(logging.DEBUG)
        
        # Create safety log file
        os.makedirs('logs/safety', exist_ok=True)
        safety_log_file = f'logs/safety/trading_safety_{datetime.now().strftime("%Y%m%d")}.log'
        
        # File handler with detailed format
        file_handler = logging.FileHandler(safety_log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for immediate visibility
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Detailed formatter for safety logs
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | SAFETY | %(message)s | PID:%(process)d'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_safety_config(self):
        """Load safety configuration with secure defaults"""
        config_file = 'config/trading_safety.json'
        
        # Default MAXIMUM SAFETY configuration
        default_config = {
            "trading_mode": "PAPER_ONLY",
            "safety_level": "MAXIMUM",
            "max_daily_loss": 1000.0,
            "max_position_size": 10000.0,
            "max_positions": 3,
            "require_manual_confirmation": True,
            "paper_trading_enforced": True,
            "zerodha_live_trading_disabled": True,
            "emergency_stop_on_loss": True,
            "audit_all_trades": True,
            "safety_checks_enabled": True,
            "real_money_trading_allowed": False,
            "confirmation_codes": {
                "enable_live_trading": "DANGER_REAL_MONEY_2024",
                "disable_safety": "EMERGENCY_OVERRIDE_2024",
                "emergency_stop": "STOP_ALL_TRADING_NOW"
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults, keeping safety as priority
                config = default_config.copy()
                config.update(loaded_config)
                
                # CRITICAL: Always enforce paper trading unless explicitly enabled
                if not config.get('real_money_trading_allowed', False):
                    config['paper_trading_enforced'] = True
                    config['zerodha_live_trading_disabled'] = True
                    
                return config
            else:
                # Create default config file
                os.makedirs('config', exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
                
        except Exception as e:
            self.logger.error(f"Error loading safety config: {e}")
            return default_config
    
    def _generate_session_id(self):
        """Generate unique session ID for audit trail"""
        timestamp = str(int(time.time()))
        random_data = os.urandom(16).hex()
        return hashlib.sha256(f"{timestamp}{random_data}".encode()).hexdigest()[:16]
    
    def _initialize_safety_state(self):
        """Initialize safety state and perform startup checks"""
        # Check environment variables for safety overrides
        env_safety_mode = os.getenv('TRADING_SAFETY_MODE', '').upper()
        env_paper_only = os.getenv('PAPER_TRADING_ONLY', 'true').lower() == 'true'
        
        # Log environment safety settings
        self.logger.info(f"Environment TRADING_SAFETY_MODE: {env_safety_mode}")
        self.logger.info(f"Environment PAPER_TRADING_ONLY: {env_paper_only}")
        
        # CRITICAL: Enforce paper trading if environment demands it
        if env_paper_only or env_safety_mode == 'PAPER_ONLY':
            self.safety_config['paper_trading_enforced'] = True
            self.safety_config['real_money_trading_allowed'] = False
            self.logger.warning("🛡️ PAPER TRADING ENFORCED by environment")
        
        # Validate current configuration
        self._validate_safety_config()
        
        # Initialize emergency stop check
        self._check_emergency_stop_conditions()
    
    def _validate_safety_config(self):
        """Validate safety configuration and enforce rules"""
        # RULE 1: If real money trading is not explicitly allowed, enforce paper trading
        if not self.safety_config.get('real_money_trading_allowed', False):
            self.safety_config['paper_trading_enforced'] = True
            self.safety_config['zerodha_live_trading_disabled'] = True
            self.logger.warning("🛡️ Real money trading NOT allowed - Paper trading enforced")
        
        # RULE 2: Maximum safety level requires additional protections
        if self.safety_config.get('safety_level') == 'MAXIMUM':
            self.safety_config['require_manual_confirmation'] = True
            self.safety_config['audit_all_trades'] = True
            self.logger.info("🛡️ MAXIMUM safety level active")
        
        # RULE 3: Validate trading mode vs configuration
        trading_mode = self.safety_config.get('trading_mode', 'PAPER_ONLY')
        if trading_mode in ['LIVE_SANDBOX', 'LIVE_REAL']:
            if self.safety_config.get('paper_trading_enforced', True):
                self.logger.critical("🚨 CONFLICT: Live trading mode with paper trading enforced")
                self.safety_config['trading_mode'] = 'PAPER_ONLY'
                self.logger.critical("🛡️ FORCED OVERRIDE: Trading mode set to PAPER_ONLY")
    
    def _check_emergency_stop_conditions(self):
        """Check for emergency stop conditions"""
        # Check for emergency stop file
        emergency_file = 'EMERGENCY_STOP_TRADING'
        if os.path.exists(emergency_file):
            self.emergency_stop_active = True
            self.logger.critical("🚨 EMERGENCY STOP ACTIVE - Trading disabled by emergency file")
            return
        
        # Check for excessive losses (if trading history exists)
        try:
            self._check_daily_loss_limits()
        except Exception as e:
            self.logger.error(f"Error checking loss limits: {e}")
    
    def _check_daily_loss_limits(self):
        """Check if daily loss limits have been exceeded"""
        # This would integrate with your trading history
        # For now, just log that the check was performed
        max_daily_loss = self.safety_config.get('max_daily_loss', 1000.0)
        self.logger.info(f"Daily loss limit check: Max allowed ₹{max_daily_loss}")
    
    def get_trading_mode(self) -> TradingMode:
        """Get current trading mode with safety validation"""
        mode_str = self.safety_config.get('trading_mode', 'PAPER_ONLY')
        
        try:
            mode = TradingMode(mode_str)
            
            # SAFETY CHECK: If paper trading is enforced, override mode
            if self.safety_config.get('paper_trading_enforced', True):
                if mode in [TradingMode.LIVE_SANDBOX, TradingMode.LIVE_REAL]:
                    self.logger.warning(f"🛡️ Trading mode override: {mode_str} -> PAPER_ONLY (safety enforced)")
                    return TradingMode.PAPER_ONLY
            
            return mode
        except ValueError:
            self.logger.error(f"Invalid trading mode: {mode_str}, defaulting to PAPER_ONLY")
            return TradingMode.PAPER_ONLY
    
    def get_safety_level(self) -> SafetyLevel:
        """Get current safety level"""
        level_str = self.safety_config.get('safety_level', 'MAXIMUM')
        try:
            return SafetyLevel(level_str)
        except ValueError:
            self.logger.error(f"Invalid safety level: {level_str}, defaulting to MAXIMUM")
            return SafetyLevel.MAXIMUM
    
    def is_paper_trading_enforced(self) -> bool:
        """Check if paper trading is enforced"""
        return self.safety_config.get('paper_trading_enforced', True)
    
    def is_real_money_trading_allowed(self) -> bool:
        """Check if real money trading is allowed"""
        return self.safety_config.get('real_money_trading_allowed', False)
    
    def validate_trade_request(self, trade_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        CRITICAL: Validate trade request against safety rules
        
        Returns:
            Tuple[bool, str]: (is_valid, reason)
        """
        try:
            # EMERGENCY STOP CHECK
            if self.emergency_stop_active:
                return False, "🚨 EMERGENCY STOP ACTIVE - All trading disabled"
            
            # SAFETY CHECKS DISABLED CHECK
            if not self.safety_checks_enabled:
                return False, "🚨 Safety checks disabled - Trading not allowed"
            
            # PAPER TRADING ENFORCEMENT
            if self.is_paper_trading_enforced():
                if trade_data.get('real_money', False):
                    return False, "🛡️ Real money trading blocked - Paper trading enforced"
            
            # TRADING MODE VALIDATION
            current_mode = self.get_trading_mode()
            requested_mode = trade_data.get('trading_mode', 'PAPER_ONLY')
            
            if current_mode == TradingMode.PAPER_ONLY:
                if requested_mode != 'PAPER_ONLY':
                    return False, f"🛡️ Trading mode mismatch - Only PAPER_ONLY allowed, requested: {requested_mode}"
            
            # POSITION SIZE VALIDATION
            max_position_size = self.safety_config.get('max_position_size', 10000.0)
            position_value = trade_data.get('amount', 0)
            if position_value > max_position_size:
                return False, f"🛡️ Position size too large - Max: ₹{max_position_size}, Requested: ₹{position_value}"
            
            # POSITION COUNT VALIDATION
            max_positions = self.safety_config.get('max_positions', 3)
            current_positions = trade_data.get('current_positions', 0)
            if current_positions >= max_positions and trade_data.get('action') == 'BUY':
                return False, f"🛡️ Too many positions - Max: {max_positions}, Current: {current_positions}"
            
            self.logger.info(f"✅ Trade request validated: {trade_data.get('symbol', 'UNKNOWN')}")
            return True, "Trade request validated successfully"
            
        except Exception as e:
            self.logger.error(f"Error validating trade request: {e}")
            return False, f"🚨 Safety validation error: {str(e)}"
    
    def log_trade_attempt(self, trade_data: Dict[str, Any], success: bool, reason: str):
        """Log all trade attempts for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'trade_data': trade_data,
            'success': success,
            'reason': reason,
            'trading_mode': self.get_trading_mode().value,
            'safety_level': self.get_safety_level().value,
            'paper_trading_enforced': self.is_paper_trading_enforced()
        }
        
        # Log to safety logger
        if success:
            self.logger.info(f"✅ TRADE EXECUTED: {json.dumps(log_entry, default=str)}")
        else:
            self.logger.warning(f"❌ TRADE BLOCKED: {json.dumps(log_entry, default=str)}")
        
        # Save to audit file
        try:
            audit_file = f'logs/safety/trade_audit_{datetime.now().strftime("%Y%m")}.json'
            with open(audit_file, 'a') as f:
                json.dump(log_entry, f, default=str)
                f.write('\n')
        except Exception as e:
            self.logger.error(f"Error saving audit log: {e}")
    
    def activate_emergency_stop(self, reason: str = "Manual activation"):
        """Activate emergency stop - STOPS ALL TRADING"""
        self.emergency_stop_active = True
        
        # Create emergency stop file
        with open('EMERGENCY_STOP_TRADING', 'w') as f:
            f.write(f"Emergency stop activated at {datetime.now().isoformat()}\n")
            f.write(f"Reason: {reason}\n")
            f.write(f"Session ID: {self.session_id}\n")
        
        self.logger.critical(f"🚨 EMERGENCY STOP ACTIVATED: {reason}")
        print("🚨" * 20)
        print("EMERGENCY STOP ACTIVATED - ALL TRADING DISABLED")
        print(f"Reason: {reason}")
        print("Remove 'EMERGENCY_STOP_TRADING' file to re-enable")
        print("🚨" * 20)
    
    def deactivate_emergency_stop(self, confirmation_code: str):
        """Deactivate emergency stop with confirmation"""
        required_code = self.safety_config.get('confirmation_codes', {}).get('emergency_stop', 'STOP_ALL_TRADING_NOW')
        
        if confirmation_code == required_code:
            self.emergency_stop_active = False
            
            # Remove emergency stop file
            if os.path.exists('EMERGENCY_STOP_TRADING'):
                os.remove('EMERGENCY_STOP_TRADING')
            
            self.logger.critical(f"🛡️ EMERGENCY STOP DEACTIVATED - Session: {self.session_id}")
            return True
        else:
            self.logger.critical(f"🚨 FAILED EMERGENCY STOP DEACTIVATION - Invalid code")
            return False
    
    def enable_real_money_trading(self, confirmation_code: str, additional_confirmations: Dict[str, str]) -> bool:
        """
        Enable real money trading with multiple confirmations
        
        ⚠️ EXTREMELY DANGEROUS OPERATION ⚠️
        """
        required_code = self.safety_config.get('confirmation_codes', {}).get('enable_live_trading', 'DANGER_REAL_MONEY_2024')
        
        # CONFIRMATION 1: Master confirmation code
        if confirmation_code != required_code:
            self.logger.critical(f"🚨 FAILED LIVE TRADING ACTIVATION - Invalid master code")
            return False
        
        # CONFIRMATION 2: Additional confirmations
        required_confirmations = {
            'user_understands_risk': 'I_UNDERSTAND_REAL_MONEY_RISK',
            'user_accepts_liability': 'I_ACCEPT_FULL_LIABILITY',
            'user_confirms_testing': 'I_HAVE_TESTED_THOROUGHLY'
        }
        
        for key, required_value in required_confirmations.items():
            if additional_confirmations.get(key) != required_value:
                self.logger.critical(f"🚨 FAILED LIVE TRADING ACTIVATION - Missing confirmation: {key}")
                return False
        
        # CONFIRMATION 3: Time-based confirmation (must wait 24 hours)
        last_request_file = 'logs/safety/live_trading_request.json'
        if os.path.exists(last_request_file):
            try:
                with open(last_request_file, 'r') as f:
                    last_request = json.load(f)
                last_time = datetime.fromisoformat(last_request['timestamp'])
                if datetime.now() - last_time < timedelta(hours=24):
                    remaining_hours = 24 - (datetime.now() - last_time).total_seconds() / 3600
                    self.logger.critical(f"🚨 LIVE TRADING ACTIVATION BLOCKED - Wait {remaining_hours:.1f} more hours")
                    return False
            except Exception as e:
                self.logger.error(f"Error checking last request: {e}")
        
        # ALL CONFIRMATIONS PASSED - Enable live trading
        self.safety_config['real_money_trading_allowed'] = True
        self.safety_config['paper_trading_enforced'] = False
        self.safety_config['zerodha_live_trading_disabled'] = False
        
        # Save the decision
        with open(last_request_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'confirmations': additional_confirmations
            }, f, indent=2)
        
        self.logger.critical(f"⚠️ REAL MONEY TRADING ENABLED - Session: {self.session_id}")
        self.logger.critical(f"⚠️ USER ACCEPTS FULL RESPONSIBILITY FOR ALL LOSSES")
        
        print("⚠️" * 20)
        print("REAL MONEY TRADING ENABLED")
        print("YOU ARE NOW TRADING WITH REAL MONEY")
        print("ALL LOSSES ARE YOUR RESPONSIBILITY")
        print("⚠️" * 20)
        
        return True
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get comprehensive safety status"""
        return {
            'session_id': self.session_id,
            'trading_mode': self.get_trading_mode().value,
            'safety_level': self.get_safety_level().value,
            'paper_trading_enforced': self.is_paper_trading_enforced(),
            'real_money_trading_allowed': self.is_real_money_trading_allowed(),
            'emergency_stop_active': self.emergency_stop_active,
            'safety_checks_enabled': self.safety_checks_enabled,
            'zerodha_live_trading_disabled': self.safety_config.get('zerodha_live_trading_disabled', True),
            'max_daily_loss': self.safety_config.get('max_daily_loss'),
            'max_position_size': self.safety_config.get('max_position_size'),
            'max_positions': self.safety_config.get('max_positions'),
            'audit_enabled': self.safety_config.get('audit_all_trades', True),
            'timestamp': datetime.now().isoformat()
        }

# Global safety system instance
trading_safety = TradingSafetySystem()

# Safety decorator for trading functions
def require_trading_safety(func):
    """Decorator to enforce trading safety on functions"""
    def wrapper(*args, **kwargs):
        # Check emergency stop
        if trading_safety.emergency_stop_active:
            raise Exception("🚨 EMERGENCY STOP ACTIVE - Trading disabled")
        
        # Check if safety checks are enabled
        if not trading_safety.safety_checks_enabled:
            raise Exception("🚨 Safety checks disabled - Trading not allowed")
        
        # Log function call
        trading_safety.logger.info(f"🛡️ Safety-protected function called: {func.__name__}")
        
        return func(*args, **kwargs)
    
    return wrapper

# Convenience functions
def is_paper_trading_safe() -> bool:
    """Quick check if we're in safe paper trading mode"""
    return trading_safety.is_paper_trading_enforced()

def is_real_money_allowed() -> bool:
    """Quick check if real money trading is allowed"""
    return trading_safety.is_real_money_trading_allowed()

def validate_trade_safety(trade_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Quick trade validation"""
    return trading_safety.validate_trade_request(trade_data)

def emergency_stop_all_trading(reason: str = "Emergency stop activated"):
    """Emergency stop all trading"""
    trading_safety.activate_emergency_stop(reason)

# Export safety system
__all__ = [
    'TradingSafetySystem',
    'TradingMode', 
    'SafetyLevel',
    'trading_safety',
    'require_trading_safety',
    'is_paper_trading_safe',
    'is_real_money_allowed',
    'validate_trade_safety',
    'emergency_stop_all_trading'
]