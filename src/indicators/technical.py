"""
Fixed Technical Indicators with robust Supertrend calculation and column name handling
"""
import pandas as pd
import numpy as np

class TechnicalIndicators:
    def __init__(self):
        pass
    
    def sma(self, data, window):
        """Simple Moving Average"""
        return data.rolling(window=window).mean()
    
    def ema(self, data, window):
        """Exponential Moving Average"""
        return data.ewm(span=window).mean()
    
    def rsi(self, data, window=14):
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def macd(self, data, fast=12, slow=26, signal=9):
        """MACD Indicator"""
        ema_fast = self.ema(data, fast)
        ema_slow = self.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'MACD': macd_line,
            'MACD_Signal': signal_line,
            'MACD_Histogram': histogram
        })
    
    def bollinger_bands(self, data, window=20, std_dev=2):
        """Bollinger Bands"""
        rolling_mean = self.sma(data, window)
        rolling_std = data.rolling(window=window).std()
        
        upper_band = rolling_mean + (rolling_std * std_dev)
        lower_band = rolling_mean - (rolling_std * std_dev)
        
        return pd.DataFrame({
            'BB_Upper': upper_band,
            'BB_Middle': rolling_mean,
            'BB_Lower': lower_band
        })
    
    def stochastic(self, high, low, close, k_window=14, d_window=3):
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return pd.DataFrame({
            'Stoch_K': k_percent,
            'Stoch_D': d_percent
        })
    
    def atr(self, high, low, close, window=14):
        """Average True Range"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=window).mean()
        
        return atr
    
    def supertrend(self, high, low, close, atr_period=10, multiplier=3):
        """Fixed Supertrend Indicator"""
        try:
            atr = self.atr(high, low, close, atr_period)
            hl2 = (high + low) / 2
            
            upper_band = hl2 + (multiplier * atr)
            lower_band = hl2 - (multiplier * atr)
            
            # Initialize arrays
            supertrend = pd.Series(index=close.index, dtype=float)
            direction = pd.Series(index=close.index, dtype=int)
            
            # Initialize first values
            supertrend.iloc[0] = close.iloc[0]
            direction.iloc[0] = 1
            
            # Calculate supertrend
            for i in range(1, len(close)):
                if pd.isna(upper_band.iloc[i]) or pd.isna(lower_band.iloc[i]):
                    supertrend.iloc[i] = supertrend.iloc[i-1]
                    direction.iloc[i] = direction.iloc[i-1]
                    continue
                
                # Calculate final bands
                if i == 1:
                    final_upper = upper_band.iloc[i]
                    final_lower = lower_band.iloc[i]
                else:
                    prev_final_upper = upper_band.iloc[i-1] if i == 1 else supertrend.iloc[i-1] if direction.iloc[i-1] == -1 else upper_band.iloc[i-1]
                    prev_final_lower = lower_band.iloc[i-1] if i == 1 else supertrend.iloc[i-1] if direction.iloc[i-1] == 1 else lower_band.iloc[i-1]
                    
                    final_upper = upper_band.iloc[i] if upper_band.iloc[i] < prev_final_upper or close.iloc[i-1] > prev_final_upper else prev_final_upper
                    final_lower = lower_band.iloc[i] if lower_band.iloc[i] > prev_final_lower or close.iloc[i-1] < prev_final_lower else prev_final_lower
                
                # Determine direction
                if close.iloc[i] <= final_lower:
                    direction.iloc[i] = -1
                elif close.iloc[i] >= final_upper:
                    direction.iloc[i] = 1
                else:
                    direction.iloc[i] = direction.iloc[i-1]
                
                # Set supertrend value
                supertrend.iloc[i] = final_lower if direction.iloc[i] == 1 else final_upper
            
            return supertrend
            
        except Exception as e:
            print(f"⚠️ Supertrend calculation error: {e}")
            # Return simple moving average as fallback
            return self.sma(close, atr_period)
    
    def williams_r(self, high, low, close, window=14):
        """Williams %R"""
        highest_high = high.rolling(window=window).max()
        lowest_low = low.rolling(window=window).min()
        
        wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return wr
    
    def cci(self, high, low, close, window=20):
        """Commodity Channel Index"""
        typical_price = (high + low + close) / 3
        sma_tp = self.sma(typical_price, window)
        mad = typical_price.rolling(window=window).apply(lambda x: np.abs(x - x.mean()).mean())
        
        cci = (typical_price - sma_tp) / (0.015 * mad)
        return cci
    
    def momentum(self, data, window=10):
        """Price Momentum"""
        return data.diff(window)
    
    def roc(self, data, window=10):
        """Rate of Change"""
        return ((data - data.shift(window)) / data.shift(window)) * 100
    
    def standardize_columns(self, df):
        """Standardize column names to handle case variations"""
        df_copy = df.copy()
        
        # Map common variations to standard names
        column_mapping = {
            'open': 'Open',
            'high': 'High', 
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low', 
            'Close': 'Close',
            'Volume': 'Volume'
        }
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in df_copy.columns:
                df_copy = df_copy.rename(columns={old_name: new_name})
        
        return df_copy
    
    def add_all_indicators(self, df):
        """Add all technical indicators to DataFrame"""
        # Standardize column names first
        result_df = self.standardize_columns(df)
        
        try:
            # Verify required columns exist
            required_cols = ['Close']
            if not all(col in result_df.columns for col in required_cols):
                print(f"⚠️ Missing required columns. Available: {list(result_df.columns)}")
                return result_df
            
            # Basic moving averages
            result_df['SMA_10'] = self.sma(result_df['Close'], 10)
            result_df['SMA_20'] = self.sma(result_df['Close'], 20)
            result_df['SMA_50'] = self.sma(result_df['Close'], 50)
            result_df['EMA_10'] = self.ema(result_df['Close'], 10)
            result_df['EMA_20'] = self.ema(result_df['Close'], 20)
            result_df['EMA_50'] = self.ema(result_df['Close'], 50)
            
            # RSI
            result_df['RSI'] = self.rsi(result_df['Close'])
            
            # MACD
            macd_data = self.macd(result_df['Close'])
            result_df['MACD'] = macd_data['MACD']
            result_df['MACD_Signal'] = macd_data['MACD_Signal']
            result_df['MACD_Histogram'] = macd_data['MACD_Histogram']
            
            # Bollinger Bands
            bb_data = self.bollinger_bands(result_df['Close'])
            result_df['BB_Upper'] = bb_data['BB_Upper']
            result_df['BB_Middle'] = bb_data['BB_Middle']
            result_df['BB_Lower'] = bb_data['BB_Lower']
            
            # Advanced indicators (only if OHLC data available)
            if all(col in result_df.columns for col in ['High', 'Low']):
                # Stochastic
                stoch_data = self.stochastic(result_df['High'], result_df['Low'], result_df['Close'])
                result_df['Stoch_K'] = stoch_data['Stoch_K']
                result_df['Stoch_D'] = stoch_data['Stoch_D']
                
                # ATR
                result_df['ATR'] = self.atr(result_df['High'], result_df['Low'], result_df['Close'])
                
                # Supertrend (with error handling)
                try:
                    result_df['Supertrend'] = self.supertrend(result_df['High'], result_df['Low'], result_df['Close'])
                except Exception as e:
                    print(f"⚠️ Supertrend failed, using EMA fallback: {e}")
                    result_df['Supertrend'] = result_df['EMA_20']
                
                # Williams %R
                result_df['Williams_R'] = self.williams_r(result_df['High'], result_df['Low'], result_df['Close'])
                
                # CCI
                result_df['CCI'] = self.cci(result_df['High'], result_df['Low'], result_df['Close'])
            
            # Price momentum indicators
            result_df['Momentum'] = self.momentum(result_df['Close'])
            result_df['ROC'] = self.roc(result_df['Close'])
            
            # Volume indicators (if volume available)
            if 'Volume' in result_df.columns:
                result_df['Volume_SMA'] = self.sma(result_df['Volume'], 20)
                # Volume Price Trend
                price_change = result_df['Close'].pct_change()
                result_df['VPT'] = (result_df['Volume'] * price_change).cumsum()
            
            indicators_added = len([col for col in result_df.columns if col not in df.columns])
            print(f"✅ Added {indicators_added} technical indicators")
            
        except Exception as e:
            print(f"⚠️ Error adding indicators: {e}")
        
        return result_df
    
    def get_signals(self, df):
        """Generate trading signals based on indicators"""
        signals = []
        
        if len(df) < 20:
            return signals
        
        # Standardize columns
        df = self.standardize_columns(df)
        
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        
        try:
            # RSI signals
            if 'RSI' in df.columns and not pd.isna(latest['RSI']):
                if latest['RSI'] < 30:
                    signals.append(('BUY', 'RSI oversold', latest['RSI']))
                elif latest['RSI'] > 70:
                    signals.append(('SELL', 'RSI overbought', latest['RSI']))
            
            # MACD signals
            if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
                if not pd.isna(latest['MACD']) and not pd.isna(previous['MACD']):
                    if (latest['MACD'] > latest['MACD_Signal'] and 
                        previous['MACD'] <= previous['MACD_Signal']):
                        signals.append(('BUY', 'MACD bullish crossover', latest['MACD']))
                    elif (latest['MACD'] < latest['MACD_Signal'] and 
                          previous['MACD'] >= previous['MACD_Signal']):
                        signals.append(('SELL', 'MACD bearish crossover', latest['MACD']))
            
            # Moving average signals
            if all(col in df.columns for col in ['EMA_10', 'EMA_20']):
                if not pd.isna(latest['EMA_10']) and not pd.isna(previous['EMA_10']):
                    if (latest['EMA_10'] > latest['EMA_20'] and 
                        previous['EMA_10'] <= previous['EMA_20']):
                        signals.append(('BUY', 'EMA golden cross', latest['EMA_10']))
                    elif (latest['EMA_10'] < latest['EMA_20'] and 
                          previous['EMA_10'] >= previous['EMA_20']):
                        signals.append(('SELL', 'EMA death cross', latest['EMA_10']))
            
            # Bollinger Bands signals
            if all(col in df.columns for col in ['BB_Upper', 'BB_Lower', 'Close']):
                if not pd.isna(latest['BB_Lower']):
                    if latest['Close'] <= latest['BB_Lower']:
                        signals.append(('BUY', 'Price at lower Bollinger Band', latest['Close']))
                    elif latest['Close'] >= latest['BB_Upper']:
                        signals.append(('SELL', 'Price at upper Bollinger Band', latest['Close']))
            
            # Supertrend signals
            if 'Supertrend' in df.columns and 'Close' in df.columns:
                if not pd.isna(latest['Supertrend']) and not pd.isna(previous['Supertrend']):
                    if latest['Close'] > latest['Supertrend'] and previous['Close'] <= previous['Supertrend']:
                        signals.append(('BUY', 'Supertrend bullish', latest['Supertrend']))
                    elif latest['Close'] < latest['Supertrend'] and previous['Close'] >= previous['Supertrend']:
                        signals.append(('SELL', 'Supertrend bearish', latest['Supertrend']))
        
        except Exception as e:
            print(f"⚠️ Error generating signals: {e}")
        
        return signals

# Test the fixed indicators
if __name__ == "__main__":
    print("🧪 Testing Fixed Technical Indicators...")
    
    # Create sample data with proper column names
    dates = pd.date_range('2025-05-01', periods=50, freq='D')
    np.random.seed(42)
    
    # Generate realistic price data
    base_price = 1000
    returns = np.random.normal(0.001, 0.02, 50)
    prices = [base_price]
    
    for ret in returns:
        prices.append(prices[-1] * (1 + ret))
    
    # Create OHLCV data with proper capitalization
    df = pd.DataFrame({
        'Open': [p * (1 + np.random.normal(0, 0.005)) for p in prices[1:]],
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices[1:]],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices[1:]],
        'Close': prices[1:],
        'Volume': [np.random.randint(100000, 1000000) for _ in range(50)]
    }, index=dates)
    
    # Ensure High >= Close >= Low and High >= Open >= Low
    df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
    df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)
    
    # Test indicators
    indicators = TechnicalIndicators()
    result = indicators.add_all_indicators(df)
    
    print(f"✅ Generated {len(result.columns)} total columns")
    print(f"📊 Sample indicators for latest day:")
    
    latest = result.iloc[-1]
    print(f"  💰 Close: ₹{latest['Close']:.2f}")
    if not pd.isna(latest['RSI']):
        print(f"  🔄 RSI: {latest['RSI']:.2f}")
    if not pd.isna(latest['MACD']):
        print(f"  📊 MACD: {latest['MACD']:.4f}")
    if not pd.isna(latest['EMA_20']):
        print(f"  📈 EMA_20: ₹{latest['EMA_20']:.2f}")
    if 'Supertrend' in result.columns and not pd.isna(latest['Supertrend']):
        print(f"  ⭐ Supertrend: ₹{latest['Supertrend']:.2f}")
    
    # Test signals
    signals = indicators.get_signals(result)
    print(f"📡 Generated {len(signals)} signals")
    for signal in signals:
        print(f"  {signal[0]}: {signal[1]} ({signal[2]:.2f})")
    
    print("✅ Fixed indicators test completed!")