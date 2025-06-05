 
"""
Technical indicators module using pandas-ta for reliable calculations
"""
import pandas as pd
import numpy as np
import pandas_ta as ta
import logging
from config.settings import Config

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    def __init__(self):
        self.config = Config()
    
    def add_all_indicators(self, df):
        """
        Add all technical indicators to dataframe
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with all indicators added
        """
        if df.empty or len(df) < 50:
            logger.warning("Insufficient data for indicator calculation")
            return df
        
        try:
            # Make a copy to avoid modifying original
            data = df.copy()
            
            # Ensure proper column names
            if 'Close' in data.columns:
                data = data.rename(columns={
                    'Open': 'open', 'High': 'high', 'Low': 'low', 
                    'Close': 'close', 'Volume': 'volume'
                })
            
            # Add all indicators
            data = self.add_ema_indicators(data)
            data = self.add_rsi(data)
            data = self.add_macd(data)
            data = self.add_supertrend(data)
            data = self.add_volume_indicators(data)
            data = self.add_support_resistance(data)
            data = self.add_trend_signals(data)
            
            logger.info(f"Added all indicators to {len(data)} rows")
            return data
            
        except Exception as e:
            logger.error(f"Error adding indicators: {str(e)}")
            return df
    
    def add_ema_indicators(self, df):
        """Add EMA indicators"""
        try:
            df['ema_9'] = ta.ema(df['close'], length=self.config.EMA_FAST)
            df['ema_21'] = ta.ema(df['close'], length=self.config.EMA_MEDIUM)
            df['ema_50'] = ta.ema(df['close'], length=self.config.EMA_SLOW)
            
            # EMA crossover signals
            df['ema_bullish_cross'] = (
                (df['ema_9'] > df['ema_21']) & 
                (df['ema_9'].shift(1) <= df['ema_21'].shift(1))
            )
            
            df['ema_bearish_cross'] = (
                (df['ema_9'] < df['ema_21']) & 
                (df['ema_9'].shift(1) >= df['ema_21'].shift(1))
            )
            
            # Price vs EMA signals
            df['price_above_ema21'] = df['close'] > df['ema_21']
            df['price_above_ema50'] = df['close'] > df['ema_50']
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding EMA indicators: {str(e)}")
            return df
    
    def add_rsi(self, df):
        """Add RSI indicator"""
        try:
            df['rsi'] = ta.rsi(df['close'], length=self.config.RSI_PERIOD)
            
            # RSI signals
            df['rsi_overbought'] = df['rsi'] > self.config.RSI_OVERBOUGHT
            df['rsi_oversold'] = df['rsi'] < self.config.RSI_OVERSOLD
            
            # RSI divergence (simplified)
            df['rsi_bullish_div'] = (
                (df['close'] < df['close'].shift(5)) & 
                (df['rsi'] > df['rsi'].shift(5)) &
                (df['rsi'] < 50)
            )
            
            df['rsi_bearish_div'] = (
                (df['close'] > df['close'].shift(5)) & 
                (df['rsi'] < df['rsi'].shift(5)) &
                (df['rsi'] > 50)
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding RSI: {str(e)}")
            return df
    
    def add_macd(self, df):
        """Add MACD indicator"""
        try:
            macd_data = ta.macd(
                df['close'], 
                fast=self.config.MACD_FAST,
                slow=self.config.MACD_SLOW, 
                signal=self.config.MACD_SIGNAL
            )
            
            df['macd'] = macd_data[f'MACD_{self.config.MACD_FAST}_{self.config.MACD_SLOW}_{self.config.MACD_SIGNAL}']
            df['macd_signal'] = macd_data[f'MACDs_{self.config.MACD_FAST}_{self.config.MACD_SLOW}_{self.config.MACD_SIGNAL}']
            df['macd_histogram'] = macd_data[f'MACDh_{self.config.MACD_FAST}_{self.config.MACD_SLOW}_{self.config.MACD_SIGNAL}']
            
            # MACD signals
            df['macd_bullish_cross'] = (
                (df['macd'] > df['macd_signal']) & 
                (df['macd'].shift(1) <= df['macd_signal'].shift(1))
            )
            
            df['macd_bearish_cross'] = (
                (df['macd'] < df['macd_signal']) & 
                (df['macd'].shift(1) >= df['macd_signal'].shift(1))
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding MACD: {str(e)}")
            return df
    
    def add_supertrend(self, df):
        """Add Supertrend indicator"""
        try:
            supertrend_data = ta.supertrend(
                df['high'], df['low'], df['close'],
                length=self.config.SUPERTREND_PERIOD,
                multiplier=self.config.SUPERTREND_MULTIPLIER
            )
            
            df['supertrend'] = supertrend_data[f'SUPERT_{self.config.SUPERTREND_PERIOD}_{self.config.SUPERTREND_MULTIPLIER}']
            df['supertrend_direction'] = supertrend_data[f'SUPERTd_{self.config.SUPERTREND_PERIOD}_{self.config.SUPERTREND_MULTIPLIER}']
            
            # Supertrend signals
            df['supertrend_bullish'] = df['supertrend_direction'] == 1
            df['supertrend_bearish'] = df['supertrend_direction'] == -1
            
            # Supertrend trend change
            df['supertrend_bull_signal'] = (
                (df['supertrend_direction'] == 1) & 
                (df['supertrend_direction'].shift(1) == -1)
            )
            
            df['supertrend_bear_signal'] = (
                (df['supertrend_direction'] == -1) & 
                (df['supertrend_direction'].shift(1) == 1)
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding Supertrend: {str(e)}")
            return df
    
    def add_volume_indicators(self, df):
        """Add volume-based indicators"""
        try:
            # Volume moving average
            df['volume_ma'] = ta.sma(df['volume'], length=self.config.VOLUME_MA_PERIOD)
            
            # Volume spike detection
            df['volume_spike'] = df['volume'] > (df['volume_ma'] * self.config.VOLUME_SPIKE_THRESHOLD)
            
            # Volume trend
            df['volume_trend'] = df['volume'] > df['volume'].shift(1)
            
            # Volume Price Trend (VPT)
            df['vpt'] = ta.vpt(df['close'], df['volume'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding volume indicators: {str(e)}")
            return df
    
    def add_support_resistance(self, df, window=20):
        """Add basic support and resistance levels"""
        try:
            # Rolling highs and lows for S&R
            df['resistance'] = df['high'].rolling(window=window).max()
            df['support'] = df['low'].rolling(window=window).min()
            
            # Near support/resistance
            tolerance = 0.01  # 1%
            df['near_resistance'] = abs(df['close'] - df['resistance']) / df['close'] < tolerance
            df['near_support'] = abs(df['close'] - df['support']) / df['close'] < tolerance
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding support/resistance: {str(e)}")
            return df
    
    def add_trend_signals(self, df):
        """Add comprehensive trend signals"""
        try:
            # Overall trend score (0-100)
            trend_score = 0
            
            # EMA trend contribution (30 points)
            ema_points = 0
            if 'ema_9' in df.columns and 'ema_21' in df.columns and 'ema_50' in df.columns:
                ema_condition1 = df['ema_9'] > df['ema_21']  # 10 points
                ema_condition2 = df['ema_21'] > df['ema_50']  # 10 points  
                ema_condition3 = df['close'] > df['ema_21']   # 10 points
                
                ema_points = (ema_condition1.astype(int) * 10 + 
                            ema_condition2.astype(int) * 10 + 
                            ema_condition3.astype(int) * 10)
            
            # RSI contribution (20 points)
            rsi_points = 0
            if 'rsi' in df.columns:
                rsi_bullish = (df['rsi'] > 50) & (df['rsi'] < 70)  # Sweet spot
                rsi_points = rsi_bullish.astype(int) * 20
            
            # MACD contribution (25 points)
            macd_points = 0
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                macd_bullish = df['macd'] > df['macd_signal']
                macd_points = macd_bullish.astype(int) * 25
            
            # Supertrend contribution (25 points)
            supertrend_points = 0
            if 'supertrend_bullish' in df.columns:
                supertrend_points = df['supertrend_bullish'].astype(int) * 25
            
            # Calculate total trend score
            df['trend_score'] = ema_points + rsi_points + macd_points + supertrend_points
            
            # Trend classification
            df['trend_strength'] = pd.cut(
                df['trend_score'],
                bins=[0, 25, 50, 75, 100],
                labels=['Weak', 'Moderate', 'Strong', 'Very Strong'],
                include_lowest=True
            )
            
            # Binary trend signals
            df['bullish_trend'] = df['trend_score'] >= 60
            df['bearish_trend'] = df['trend_score'] <= 40
            df['neutral_trend'] = (df['trend_score'] > 40) & (df['trend_score'] < 60)
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding trend signals: {str(e)}")
            return df
    
    def get_latest_signals(self, df):
        """Get latest trading signals from dataframe"""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        signals = {
            'timestamp': latest.get('date', 'N/A'),
            'symbol': latest.get('symbol', 'N/A'),
            'close_price': latest.get('close', 0),
            'trend_score': latest.get('trend_score', 0),
            'trend_strength': latest.get('trend_strength', 'N/A'),
            'rsi': latest.get('rsi', 0),
            'macd_signal': latest.get('macd_bullish_cross', False),
            'ema_signal': latest.get('ema_bullish_cross', False),
            'supertrend_signal': latest.get('supertrend_bull_signal', False),
            'volume_spike': latest.get('volume_spike', False),
            'overall_bullish': latest.get('bullish_trend', False),
            'overall_bearish': latest.get('bearish_trend', False)
        }
        
        return signals