# config/zerodha/rate_limiter.py
"""
Rate Limiter for Zerodha API calls to prevent hitting limits
"""
import time
from collections import deque
from datetime import datetime, timedelta
import threading
from functools import wraps

class ZerodhaRateLimiter:
    """Rate limiter for Zerodha API calls"""
    
    def __init__(self, calls_per_second=10, calls_per_minute=100):
        self.calls_per_second = calls_per_second
        self.calls_per_minute = calls_per_minute
        
        # Track API calls
        self.second_calls = deque()
        self.minute_calls = deque()
        
        # Thread lock for thread safety
        self.lock = threading.Lock()
        
        print(f"📊 Rate Limiter: {calls_per_second}/sec, {calls_per_minute}/min")
    
    def can_make_call(self):
        """Check if we can make an API call without hitting limits"""
        with self.lock:
            now = datetime.now()
            
            # Clean old entries
            self._clean_old_calls(now)
            
            # Check limits
            second_limit_ok = len(self.second_calls) < self.calls_per_second
            minute_limit_ok = len(self.minute_calls) < self.calls_per_minute
            
            return second_limit_ok and minute_limit_ok
    
    def record_call(self):
        """Record an API call"""
        with self.lock:
            now = datetime.now()
            self.second_calls.append(now)
            self.minute_calls.append(now)
            
            # Clean old entries
            self._clean_old_calls(now)
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        while not self.can_make_call():
            print("⏳ Rate limit reached, waiting...")
            time.sleep(0.1)  # Wait 100ms and check again
    
    def _clean_old_calls(self, now):
        """Remove old call records"""
        # Remove calls older than 1 second
        second_cutoff = now - timedelta(seconds=1)
        while self.second_calls and self.second_calls[0] < second_cutoff:
            self.second_calls.popleft()
        
        # Remove calls older than 1 minute
        minute_cutoff = now - timedelta(minutes=1)
        while self.minute_calls and self.minute_calls[0] < minute_cutoff:
            self.minute_calls.popleft()
    
    def get_stats(self):
        """Get current rate limiting stats"""
        with self.lock:
            now = datetime.now()
            self._clean_old_calls(now)
            
            return {
                'calls_last_second': len(self.second_calls),
                'calls_last_minute': len(self.minute_calls),
                'second_limit': self.calls_per_second,
                'minute_limit': self.calls_per_minute,
                'can_call': self.can_make_call()
            }

def rate_limited(rate_limiter):
    """Decorator to apply rate limiting to API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Wait if needed
            rate_limiter.wait_if_needed()
            
            # Record the call
            rate_limiter.record_call()
            
            # Make the actual call
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"❌ API call failed: {e}")
                raise
        
        return wrapper
    return decorator

# Global rate limiter instance
zerodha_rate_limiter = ZerodhaRateLimiter()

# Convenience decorator using global instance
def zerodha_rate_limited(func):
    """Apply Zerodha rate limiting to a function"""
    return rate_limited(zerodha_rate_limiter)(func)