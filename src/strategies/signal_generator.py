"""
Advanced Signal Generator for Indian Stock Trading
Combines multiple indicators and market regime to generate high-quality signals
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from config.settings import Config

logger = logging.getLogger(__name__)

class SignalGenerator:
    def __init__(self, technical_indicators, market_regime_detector):
        self.indicators = technical_indicators
        self.regime_detector = market_regime_detector
        self.config = Config()
        self.signal_history = []
        
    def generate_signals(self, stocks_data, market_regime=None):
        """
        Enhanced signal generation with more flexible criteria
        """
        all_signals = []
        
        if not stocks_data:
            print("No stock data available for signal generation")
            return all_signals
        
        try:
            print(f"🔍 Analyzing {len(stocks_data)} stocks for signals...")
            
            for symbol, data in stocks_data.items():
                try:
                    if len(data) < 20:
                        continue
                    
                    # Add technical indicators
                    enhanced_data = self.indicators.add_all_indicators(data)
                    
                    if len(enhanced_data) < 10:
                        continue
                    
                    latest = enhanced_data.iloc[-1]
                    previous = enhanced_data.iloc[-2] if len(enhanced_data) > 1 else latest
                    
                    signals_for_stock = []
                    
                    # 1. RSI Signals (More flexible thresholds)
                    if 'RSI' in enhanced_data.columns and not pd.isna(latest['RSI']):
                        rsi = latest['RSI']
                        
                        if rsi <= 35:  # Relaxed from 30
                            signals_for_stock.append({
                                'symbol': symbol,
                                'action': 'BUY',
                                'price': float(latest['Close']),
                                'confidence': 75.0 if rsi <= 30 else 65.0,
                                'reasons': [f'RSI oversold ({rsi:.1f})'],
                                'quantity': self._calculate_quantity(latest['Close'], 65),
                                'timestamp': pd.Timestamp.now()
                            })
                        
                        elif rsi >= 65:  # Relaxed from 70
                            signals_for_stock.append({
                                'symbol': symbol,
                                'action': 'SELL',
                                'price': float(latest['Close']),
                                'confidence': 75.0 if rsi >= 70 else 65.0,
                                'reasons': [f'RSI overbought ({rsi:.1f})'],
                                'quantity': self._calculate_quantity(latest['Close'], 65),
                                'timestamp': pd.Timestamp.now()
                            })
                        
                        # RSI momentum signals
                        elif rsi > 50 and 'RSI' in enhanced_data.columns:
                            prev_rsi = previous['RSI'] if not pd.isna(previous['RSI']) else rsi
                            if prev_rsi <= 50:
                                signals_for_stock.append({
                                    'symbol': symbol,
                                    'action': 'BUY',
                                    'price': float(latest['Close']),
                                    'confidence': 60.0,
                                    'reasons': [f'RSI bullish momentum ({prev_rsi:.1f} → {rsi:.1f})'],
                                    'quantity': self._calculate_quantity(latest['Close'], 60),
                                    'timestamp': pd.Timestamp.now()
                                })
                    
                    # 2. MACD Signals
                    if all(col in enhanced_data.columns for col in ['MACD', 'MACD_Signal']):
                        macd = latest['MACD']
                        macd_signal = latest['MACD_Signal']
                        prev_macd = previous['MACD'] if not pd.isna(previous['MACD']) else macd
                        prev_macd_signal = previous['MACD_Signal'] if not pd.isna(previous['MACD_Signal']) else macd_signal
                        
                        if not any(pd.isna([macd, macd_signal, prev_macd, prev_macd_signal])):
                            # MACD crossovers
                            if macd > macd_signal and prev_macd <= prev_macd_signal:
                                signals_for_stock.append({
                                    'symbol': symbol,
                                    'action': 'BUY',
                                    'price': float(latest['Close']),
                                    'confidence': 75.0,
                                    'reasons': ['MACD bullish crossover'],
                                    'quantity': self._calculate_quantity(latest['Close'], 75),
                                    'timestamp': pd.Timestamp.now()
                                })
                            
                            elif macd < macd_signal and prev_macd >= prev_macd_signal:
                                signals_for_stock.append({
                                    'symbol': symbol,
                                    'action': 'SELL',
                                    'price': float(latest['Close']),
                                    'confidence': 75.0,
                                    'reasons': ['MACD bearish crossover'],
                                    'quantity': self._calculate_quantity(latest['Close'], 75),
                                    'timestamp': pd.Timestamp.now()
                                })
                    
                    # 3. Moving Average Signals
                    if all(col in enhanced_data.columns for col in ['EMA_10', 'EMA_20']):
                        ema10 = latest['EMA_10']
                        ema20 = latest['EMA_20']
                        prev_ema10 = previous['EMA_10'] if not pd.isna(previous['EMA_10']) else ema10
                        prev_ema20 = previous['EMA_20'] if not pd.isna(previous['EMA_20']) else ema20
                        
                        if not any(pd.isna([ema10, ema20, prev_ema10, prev_ema20])):
                            # EMA crossovers
                            if ema10 > ema20 and prev_ema10 <= prev_ema20:
                                signals_for_stock.append({
                                    'symbol': symbol,
                                    'action': 'BUY',
                                    'price': float(latest['Close']),
                                    'confidence': 70.0,
                                    'reasons': ['EMA golden cross (10 > 20)'],
                                    'quantity': self._calculate_quantity(latest['Close'], 70),
                                    'timestamp': pd.Timestamp.now()
                                })
                            
                            elif ema10 < ema20 and prev_ema10 >= prev_ema20:
                                signals_for_stock.append({
                                    'symbol': symbol,
                                    'action': 'SELL',
                                    'price': float(latest['Close']),
                                    'confidence': 70.0,
                                    'reasons': ['EMA death cross (10 < 20)'],
                                    'quantity': self._calculate_quantity(latest['Close'], 70),
                                    'timestamp': pd.Timestamp.now()
                                })
                    
                    # 4. Supertrend Signals
                    if 'Supertrend' in enhanced_data.columns:
                        price = latest['Close']
                        st = latest['Supertrend']
                        prev_price = previous['Close']
                        prev_st = previous['Supertrend']
                        
                        if not any(pd.isna([price, st, prev_price, prev_st])):
                            # Supertrend direction changes
                            if price > st and prev_price <= prev_st:
                                signals_for_stock.append({
                                    'symbol': symbol,
                                    'action': 'BUY',
                                    'price': float(latest['Close']),
                                    'confidence': 80.0,
                                    'reasons': [f'Supertrend bullish (₹{price:.2f} > ₹{st:.2f})'],
                                    'quantity': self._calculate_quantity(latest['Close'], 80),
                                    'timestamp': pd.Timestamp.now()
                                })
                            
                            elif price < st and prev_price >= prev_st:
                                signals_for_stock.append({
                                    'symbol': symbol,
                                    'action': 'SELL',
                                    'price': float(latest['Close']),
                                    'confidence': 80.0,
                                    'reasons': [f'Supertrend bearish (₹{price:.2f} < ₹{st:.2f})'],
                                    'quantity': self._calculate_quantity(latest['Close'], 80),
                                    'timestamp': pd.Timestamp.now()
                                })
                    
                    # 5. Bollinger Bands Signals
                    if all(col in enhanced_data.columns for col in ['BB_Upper', 'BB_Lower', 'BB_Middle']):
                        price = latest['Close']
                        bb_upper = latest['BB_Upper']
                        bb_lower = latest['BB_Lower']
                        bb_middle = latest['BB_Middle']
                        
                        if not any(pd.isna([price, bb_upper, bb_lower, bb_middle])):
                            # Near Bollinger Bands
                            if price <= bb_lower * 1.01:  # Within 1% of lower band
                                signals_for_stock.append({
                                    'symbol': symbol,
                                    'action': 'BUY',
                                    'price': float(latest['Close']),
                                    'confidence': 65.0,
                                    'reasons': ['Price near lower Bollinger Band'],
                                    'quantity': self._calculate_quantity(latest['Close'], 65),
                                    'timestamp': pd.Timestamp.now()
                                })
                            
                            elif price >= bb_upper * 0.99:  # Within 1% of upper band
                                signals_for_stock.append({
                                    'symbol': symbol,
                                    'action': 'SELL',
                                    'price': float(latest['Close']),
                                    'confidence': 65.0,
                                    'reasons': ['Price near upper Bollinger Band'],
                                    'quantity': self._calculate_quantity(latest['Close'], 65),
                                    'timestamp': pd.Timestamp.now()
                                })
                    
                    # 6. Price momentum signals
                    if len(enhanced_data) >= 5:
                        price_5d_ago = enhanced_data['Close'].iloc[-5]
                        current_price = latest['Close']
                        momentum = ((current_price - price_5d_ago) / price_5d_ago) * 100
                        
                        if momentum > 3:  # 3% gain in 5 days
                            signals_for_stock.append({
                                'symbol': symbol,
                                'action': 'BUY',
                                'price': float(latest['Close']),
                                'confidence': 60.0,
                                'reasons': [f'Strong momentum (+{momentum:.1f}% in 5 days)'],
                                'quantity': self._calculate_quantity(latest['Close'], 60),
                                'timestamp': pd.Timestamp.now()
                            })
                        
                        elif momentum < -3:  # 3% loss in 5 days
                            signals_for_stock.append({
                                'symbol': symbol,
                                'action': 'SELL',
                                'price': float(latest['Close']),
                                'confidence': 60.0,
                                'reasons': [f'Negative momentum ({momentum:.1f}% in 5 days)'],
                                'quantity': self._calculate_quantity(latest['Close'], 60),
                                'timestamp': pd.Timestamp.now()
                            })
                    
                    # Add signals for this stock
                    all_signals.extend(signals_for_stock)
                    
                    if signals_for_stock:
                        print(f"  📡 {symbol}: Generated {len(signals_for_stock)} signals")
                    
                except Exception as e:
                    print(f"⚠️ Error generating signals for {symbol}: {e}")
                    continue
            
            # Sort by confidence
            all_signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            # Limit to top signals
            if len(all_signals) > 10:
                all_signals = all_signals[:10]
            
            print(f"📡 Total signals generated: {len(all_signals)}")
            
            return all_signals
            
        except Exception as e:
            print(f"❌ Signal generation error: {e}")
            return []

    def _calculate_quantity(self, price, confidence):
        """Calculate position size based on price and confidence"""
        try:
            base_amount = 10000  # ₹10,000 base position
            confidence_multiplier = confidence / 100
            shares = int((base_amount * confidence_multiplier) / price)
            return max(1, min(shares, 50))  # Between 1-50 shares
        except:
            return 10  # Default quantity
    
    def _generate_stock_signal(self, symbol, data, market_regime):
        """Generate signal for individual stock"""
        try:
            latest = data.iloc[-1]
            prev = data.iloc[-2] if len(data) > 1 else latest
            
            # Base signal structure
            signal = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': 'HOLD',
                'confidence': 0,
                'price': latest['close'],
                'volume': latest['volume'],
                'regime': market_regime['regime'],
                'reasons': [],
                'risk_level': 'medium',
                'target_price': 0,
                'stop_loss': 0,
                'position_size': 0
            }
            
            # Strategy based on market regime
            if market_regime['regime'] == 'bull':
                signal = self._bull_market_strategy(signal, latest, prev, data)
            elif market_regime['regime'] == 'bear':
                signal = self._bear_market_strategy(signal, latest, prev, data)
            else:  # sideways
                signal = self._sideways_market_strategy(signal, latest, prev, data)
            
            # Add risk management
            signal = self._add_risk_management(signal, data)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {str(e)}")
            return None
    
    def _bull_market_strategy(self, signal, latest, prev, data):
        """Bull market trading strategy - focus on long positions"""
        try:
            buy_conditions = []
            sell_conditions = []
            confidence = 0
            
            # Condition 1: Strong uptrend (30 points)
            if latest.get('trend_score', 0) >= 70:
                buy_conditions.append("Strong uptrend")
                confidence += 30
            
            # Condition 2: EMA crossover (25 points)
            if latest.get('ema_bullish_cross', False):
                buy_conditions.append("EMA bullish crossover")
                confidence += 25
            
            # Condition 3: RSI in sweet spot (20 points)
            rsi = latest.get('rsi', 50)
            if 40 <= rsi <= 65:
                buy_conditions.append("RSI in buy zone")
                confidence += 20
            
            # Condition 4: MACD bullish (15 points)
            if latest.get('macd_bullish_cross', False):
                buy_conditions.append("MACD bullish crossover")
                confidence += 15
            
            # Condition 5: Supertrend bullish (15 points)
            if latest.get('supertrend_bullish', False):
                buy_conditions.append("Supertrend bullish")
                confidence += 15
            
            # Condition 6: Volume confirmation (10 points)
            if latest.get('volume_spike', False):
                buy_conditions.append("Volume spike")
                confidence += 10
            
            # Condition 7: Above key EMAs (10 points)
            if (latest.get('price_above_ema21', False) and 
                latest.get('price_above_ema50', False)):
                buy_conditions.append("Above key EMAs")
                confidence += 10
            
            # Sell conditions for existing positions
            if rsi > 75:
                sell_conditions.append("RSI overbought")
            
            if latest.get('ema_bearish_cross', False):
                sell_conditions.append("EMA bearish crossover")
            
            if latest.get('supertrend_bear_signal', False):
                sell_conditions.append("Supertrend bearish signal")
            
            # Determine action
            if confidence >= 60 and len(buy_conditions) >= 3:
                signal['action'] = 'BUY'
                signal['confidence'] = min(confidence, 100)
                signal['reasons'] = buy_conditions
                signal['risk_level'] = 'low' if confidence >= 80 else 'medium'
                
            elif sell_conditions:
                signal['action'] = 'SELL'
                signal['confidence'] = 70
                signal['reasons'] = sell_conditions
                signal['risk_level'] = 'low'
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in bull market strategy: {str(e)}")
            return signal
    
    def _bear_market_strategy(self, signal, latest, prev, data):
        """Bear market trading strategy - conservative approach"""
        try:
            sell_conditions = []
            buy_conditions = []  # Only for strong oversold bounces
            confidence = 0
            
            # Sell conditions (short opportunities)
            if latest.get('trend_score', 0) <= 30:
                sell_conditions.append("Strong downtrend")
                confidence += 30
            
            if latest.get('ema_bearish_cross', False):
                sell_conditions.append("EMA bearish crossover")
                confidence += 25
            
            rsi = latest.get('rsi', 50)
            if rsi >= 60:
                sell_conditions.append("RSI overbought in bear market")
                confidence += 20
            
            if latest.get('supertrend_bearish', False):
                sell_conditions.append("Supertrend bearish")
                confidence += 15
            
            # Conservative buy conditions (oversold bounce)
            if rsi <= 25 and latest.get('volume_spike', False):
                buy_conditions.append("Extremely oversold with volume")
                confidence = 40  # Lower confidence in bear market
            
            if (latest.get('rsi_bullish_div', False) and 
                latest.get('volume_spike', False)):
                buy_conditions.append("Bullish divergence with volume")
                confidence = 50
            
            # Determine action
            if confidence >= 60 and sell_conditions:
                signal['action'] = 'SELL'  # Short opportunity
                signal['confidence'] = min(confidence, 85)  # Lower max confidence
                signal['reasons'] = sell_conditions
                signal['risk_level'] = 'medium'
                
            elif confidence >= 40 and buy_conditions:
                signal['action'] = 'BUY'  # Bounce trade
                signal['confidence'] = confidence
                signal['reasons'] = buy_conditions
                signal['risk_level'] = 'high'  # Higher risk in bear market
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in bear market strategy: {str(e)}")
            return signal
    
    def _sideways_market_strategy(self, signal, latest, prev, data):
        """Sideways market strategy - range trading"""
        try:
            buy_conditions = []
            sell_conditions = []
            confidence = 0
            
            rsi = latest.get('rsi', 50)
            support = latest.get('support', 0)
            resistance = latest.get('resistance', 0)
            price = latest['close']
            
            # Buy at support levels
            if latest.get('near_support', False) and rsi <= 35:
                buy_conditions.append("Near support with oversold RSI")
                confidence += 35
            
            if latest.get('ema_bullish_cross', False) and rsi < 50:
                buy_conditions.append("EMA crossover near support")
                confidence += 25
            
            if latest.get('volume_spike', False) and price <= support * 1.02:
                buy_conditions.append("Volume spike near support")
                confidence += 20
            
            # Sell at resistance levels
            if latest.get('near_resistance', False) and rsi >= 65:
                sell_conditions.append("Near resistance with overbought RSI")
                confidence += 35
            
            if latest.get('ema_bearish_cross', False) and rsi > 50:
                sell_conditions.append("EMA bearish crossover near resistance")
                confidence += 25
            
            if price >= resistance * 0.98 and rsi > 60:
                sell_conditions.append("Price near resistance")
                confidence += 20
            
            # Breakout conditions
            if (price > resistance * 1.02 and 
                latest.get('volume_spike', False) and 
                latest.get('trend_score', 0) >= 60):
                buy_conditions.append("Resistance breakout with volume")
                confidence = 70
            
            # Determine action
            if confidence >= 50:
                if buy_conditions and (not sell_conditions or len(buy_conditions) > len(sell_conditions)):
                    signal['action'] = 'BUY'
                    signal['reasons'] = buy_conditions
                elif sell_conditions:
                    signal['action'] = 'SELL'
                    signal['reasons'] = sell_conditions
                
                signal['confidence'] = min(confidence, 90)
                signal['risk_level'] = 'medium'
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in sideways market strategy: {str(e)}")
            return signal
    
    def _add_risk_management(self, signal, data):
        """Add risk management parameters to signal"""
        try:
            if signal['action'] == 'HOLD':
                return signal
            
            price = signal['price']
            atr = self._calculate_atr(data, period=14)
            
            if signal['action'] == 'BUY':
                # Set stop loss and target
                stop_loss_distance = atr * 2
                target_distance = atr * 3
                
                signal['stop_loss'] = price - stop_loss_distance
                signal['target_price'] = price + target_distance
                
                # Position sizing based on risk
                risk_amount = self.config.INITIAL_CAPITAL * (self.config.RISK_PER_TRADE / 100)
                position_size = risk_amount / stop_loss_distance
                signal['position_size'] = min(position_size, self.config.INITIAL_CAPITAL * 0.2)  # Max 20% per position
                
            elif signal['action'] == 'SELL':
                # For sell signals (exit positions)
                signal['stop_loss'] = price + (atr * 2)
                signal['target_price'] = price - (atr * 3)
                signal['position_size'] = 0  # Exit signal
            
            return signal
            
        except Exception as e:
            logger.error(f"Error adding risk management: {str(e)}")
            return signal
    
    def _calculate_atr(self, data, period=14):
        """Calculate Average True Range"""
        try:
            high = data['high']
            low = data['low']
            close = data['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=period).mean().iloc[-1]
            
            return atr if not np.isnan(atr) else data['close'].iloc[-1] * 0.02  # 2% fallback
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return data['close'].iloc[-1] * 0.02
    
    def _filter_and_rank_signals(self, signals, market_regime):
        """Filter and rank signals by quality"""
        try:
            if not signals:
                return []
            
            # Filter by confidence threshold
            min_confidence = 50 if market_regime['regime'] == 'bull' else 60
            filtered = [s for s in signals if s['confidence'] >= min_confidence]
            
            # Sort by confidence and other factors
            def signal_score(signal):
                score = signal['confidence']
                
                # Bonus for volume confirmation
                if 'Volume spike' in signal.get('reasons', []):
                    score += 5
                
                # Bonus for multiple confirmations
                score += len(signal.get('reasons', [])) * 2
                
                # Penalty for high risk
                if signal['risk_level'] == 'high':
                    score -= 10
                
                return score
            
            # Sort by score (highest first)
            ranked_signals = sorted(filtered, key=signal_score, reverse=True)
            
            # Limit to max positions
            max_signals = self.config.MAX_POSITIONS
            final_signals = ranked_signals[:max_signals]
            
            # Store in history
            for signal in final_signals:
                self.signal_history.append(signal)
            
            # Keep only last 1000 signals
            if len(self.signal_history) > 1000:
                self.signal_history = self.signal_history[-1000:]
            
            return final_signals
            
        except Exception as e:
            logger.error(f"Error filtering signals: {str(e)}")
            return signals[:self.config.MAX_POSITIONS]
    
    def get_signal_performance(self, days=30):
        """Get performance statistics of past signals"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_signals = [
                s for s in self.signal_history 
                if s['timestamp'] >= cutoff_date
            ]
            
            if not recent_signals:
                return {'total_signals': 0}
            
            total_signals = len(recent_signals)
            buy_signals = len([s for s in recent_signals if s['action'] == 'BUY'])
            sell_signals = len([s for s in recent_signals if s['action'] == 'SELL'])
            
            avg_confidence = np.mean([s['confidence'] for s in recent_signals])
            
            return {
                'total_signals': total_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'avg_confidence': avg_confidence,
                'signals_per_day': total_signals / days
            }
            
        except Exception as e:
            logger.error(f"Error calculating signal performance: {str(e)}")
            return {'total_signals': 0}