"""
Fixed Market Regime Detection with proper column name handling
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MarketRegimeDetector:
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher
        
    def standardize_columns(self, df):
        """Standardize column names to handle case variations"""
        if df.empty:
            return df
            
        df_copy = df.copy()
        
        # Map common variations to standard names
        column_mapping = {
            'open': 'Open',
            'high': 'High', 
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in df_copy.columns:
                df_copy = df_copy.rename(columns={old_name: new_name})
        
        return df_copy
    
    def detect_current_regime(self):
        """Detect current market regime"""
        try:
            # Get data for multiple stocks to analyze market
            symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 
                      'ICICIBANK', 'KOTAKBANK', 'BHARTIARTL', 'ITC', 'SBIN']
            
            stocks_data = self.data_fetcher.get_multiple_stocks_data(symbols, days=30)
            
            if not stocks_data:
                print("No stock data available for regime detection")
                return self._default_regime()
            
            # Analyze market breadth and trends
            regime_indicators = self._calculate_regime_indicators(stocks_data)
            
            # Determine regime based on indicators
            regime = self._classify_regime(regime_indicators)
            
            return regime
            
        except Exception as e:
            print(f"⚠️ Regime detection error: {e}")
            return self._default_regime()
    
    def _calculate_regime_indicators(self, stocks_data):
        """Calculate indicators for regime detection"""
        indicators = {
            'stocks_above_ema': 0,
            'average_rsi': 50,
            'market_breadth': 0,
            'volatility': 0,
            'volume_trend': 0,
            'price_momentum': 0,
            'total_stocks': len(stocks_data)
        }
        
        if not stocks_data:
            return indicators
        
        try:
            stocks_above_ema = 0
            rsi_values = []
            volatilities = []
            volume_trends = []
            momentum_values = []
            
            for symbol, data in stocks_data.items():
                try:
                    # Standardize column names
                    data = self.standardize_columns(data)
                    
                    if len(data) < 20 or 'Close' not in data.columns:
                        continue
                    
                    # Calculate EMA
                    ema_20 = data['Close'].ewm(span=20).mean()
                    latest_price = data['Close'].iloc[-1]
                    latest_ema = ema_20.iloc[-1]
                    
                    # Check if stock is above EMA
                    if not pd.isna(latest_ema) and latest_price > latest_ema:
                        stocks_above_ema += 1
                    
                    # Calculate RSI
                    delta = data['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    if not pd.isna(rsi.iloc[-1]):
                        rsi_values.append(rsi.iloc[-1])
                    
                    # Calculate volatility (20-day rolling std of returns)
                    returns = data['Close'].pct_change()
                    volatility = returns.rolling(window=20).std().iloc[-1]
                    if not pd.isna(volatility):
                        volatilities.append(volatility * 100)  # Convert to percentage
                    
                    # Volume trend (if volume data available)
                    if 'Volume' in data.columns:
                        volume_ma_short = data['Volume'].rolling(window=10).mean()
                        volume_ma_long = data['Volume'].rolling(window=20).mean()
                        if not pd.isna(volume_ma_short.iloc[-1]) and not pd.isna(volume_ma_long.iloc[-1]):
                            volume_trend = volume_ma_short.iloc[-1] / volume_ma_long.iloc[-1]
                            volume_trends.append(volume_trend)
                    
                    # Price momentum (10-day)
                    if len(data) >= 10:
                        momentum = (data['Close'].iloc[-1] / data['Close'].iloc[-10] - 1) * 100
                        if not pd.isna(momentum):
                            momentum_values.append(momentum)
                
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
                    continue
            
            # Calculate final indicators
            indicators['stocks_above_ema'] = stocks_above_ema
            indicators['average_rsi'] = np.mean(rsi_values) if rsi_values else 50
            indicators['market_breadth'] = (stocks_above_ema / len(stocks_data)) * 100 if stocks_data else 50
            indicators['volatility'] = np.mean(volatilities) if volatilities else 2.0
            indicators['volume_trend'] = np.mean(volume_trends) if volume_trends else 1.0
            indicators['price_momentum'] = np.mean(momentum_values) if momentum_values else 0
            
        except Exception as e:
            print(f"Error calculating regime indicators: {e}")
        
        return indicators
    
    def _classify_regime(self, indicators):
        """Classify market regime based on indicators"""
        try:
            # Extract indicators
            market_breadth = indicators.get('market_breadth', 50)
            avg_rsi = indicators.get('average_rsi', 50)
            volatility = indicators.get('volatility', 2.0)
            volume_trend = indicators.get('volume_trend', 1.0)
            momentum = indicators.get('price_momentum', 0)
            
            # Classification logic
            bullish_signals = 0
            bearish_signals = 0
            total_signals = 5
            
            # Market breadth
            if market_breadth > 60:
                bullish_signals += 1
            elif market_breadth < 40:
                bearish_signals += 1
            
            # RSI
            if avg_rsi > 55:
                bullish_signals += 1
            elif avg_rsi < 45:
                bearish_signals += 1
            
            # Momentum
            if momentum > 2:
                bullish_signals += 1
            elif momentum < -2:
                bearish_signals += 1
            
            # Volume trend
            if volume_trend > 1.1:
                bullish_signals += 1
            elif volume_trend < 0.9:
                bearish_signals += 1
            
            # Volatility (low volatility can indicate trending market)
            if volatility < 1.5:
                bullish_signals += 0.5
            elif volatility > 3.0:
                bearish_signals += 0.5
            
            # Determine regime
            if bullish_signals >= 3:
                regime = 'bull'
                confidence = (bullish_signals / total_signals) * 100
                strength = 'strong' if bullish_signals >= 4 else 'moderate'
                trend_direction = 'up'
            elif bearish_signals >= 3:
                regime = 'bear'
                confidence = (bearish_signals / total_signals) * 100
                strength = 'strong' if bearish_signals >= 4 else 'moderate'
                trend_direction = 'down'
            else:
                regime = 'sideways'
                confidence = 50 + (abs(bullish_signals - bearish_signals) / total_signals) * 20
                strength = 'weak'
                trend_direction = 'neutral'
            
            return {
                'regime': regime,
                'confidence': round(confidence, 1),
                'strength': strength,
                'trend_direction': trend_direction,
                'indicators': {
                    'market_breadth': round(market_breadth, 1),
                    'average_rsi': round(avg_rsi, 1),
                    'volatility': round(volatility, 2),
                    'volume_trend': round(volume_trend, 2),
                    'momentum': round(momentum, 2)
                }
            }
            
        except Exception as e:
            print(f"Error classifying regime: {e}")
            return self._default_regime()
    
    def _default_regime(self):
        """Return default regime when calculation fails"""
        return {
            'regime': 'sideways',
            'confidence': 50.0,
            'strength': 'Unknown',
            'trend_direction': 'Unknown',
            'indicators': {
                'market_breadth': 50.0,
                'average_rsi': 50.0,
                'volatility': 2.0,
                'volume_trend': 1.0,
                'momentum': 0.0
            }
        }
    
    def get_regime_signals(self, regime):
        """Get trading signals based on current regime"""
        signals = []
        
        try:
            regime_type = regime.get('regime', 'sideways')
            confidence = regime.get('confidence', 50)
            
            if regime_type == 'bull' and confidence > 70:
                signals.append({
                    'signal': 'BULLISH_MARKET',
                    'description': 'Strong bullish market regime detected',
                    'confidence': confidence,
                    'action': 'Favor long positions'
                })
            elif regime_type == 'bear' and confidence > 70:
                signals.append({
                    'signal': 'BEARISH_MARKET',
                    'description': 'Strong bearish market regime detected', 
                    'confidence': confidence,
                    'action': 'Favor short positions or cash'
                })
            elif regime_type == 'sideways':
                signals.append({
                    'signal': 'SIDEWAYS_MARKET',
                    'description': 'Sideways market regime - range trading',
                    'confidence': confidence,
                    'action': 'Use range trading strategies'
                })
            
        except Exception as e:
            print(f"Error generating regime signals: {e}")
        
        return signals

# Test the market regime detector
if __name__ == "__main__":
    print("🧪 Testing Fixed Market Regime Detector...")
    
    # Mock data fetcher for testing
    class MockDataFetcher:
        def get_multiple_stocks_data(self, symbols, days):
            stocks_data = {}
            
            for symbol in symbols[:3]:  # Test with first 3 symbols
                dates = pd.date_range('2025-05-01', periods=days, freq='D')
                
                # Generate sample data
                np.random.seed(hash(symbol) % 100)
                base_price = 1000 + hash(symbol) % 1000
                
                prices = [base_price]
                for _ in range(days-1):
                    change = np.random.normal(0.001, 0.02)
                    prices.append(prices[-1] * (1 + change))
                
                df = pd.DataFrame({
                    'Open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
                    'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                    'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                    'Close': prices,
                    'Volume': [np.random.randint(100000, 1000000) for _ in range(days)]
                }, index=dates)
                
                # Ensure OHLC integrity
                df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
                df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)
                
                stocks_data[symbol] = df
            
            return stocks_data
    
    # Test regime detection
    mock_fetcher = MockDataFetcher()
    detector = MarketRegimeDetector(mock_fetcher)
    
    regime = detector.detect_current_regime()
    
    print(f"📊 Detected Market Regime:")
    print(f"  🎭 Regime: {regime['regime']}")
    print(f"  🎯 Confidence: {regime['confidence']:.1f}%")
    print(f"  💪 Strength: {regime['strength']}")
    print(f"  📈 Trend: {regime['trend_direction']}")
    
    if 'indicators' in regime:
        print(f"  📊 Market Breadth: {regime['indicators']['market_breadth']:.1f}%")
        print(f"  🔄 Average RSI: {regime['indicators']['average_rsi']:.1f}")
        print(f"  📈 Momentum: {regime['indicators']['momentum']:.2f}%")
    
    # Test regime signals
    signals = detector.get_regime_signals(regime)
    print(f"\n📡 Regime Signals: {len(signals)}")
    for signal in signals:
        print(f"  {signal['signal']}: {signal['description']}")
    
    print("✅ Fixed market regime detector test completed!")