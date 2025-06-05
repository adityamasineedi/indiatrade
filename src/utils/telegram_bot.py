"""
Telegram Bot for Indian Stock Trading System
Sends trading alerts and portfolio updates
"""
import asyncio
import logging
from datetime import datetime
import json
from telegram import Bot
from telegram.error import TelegramError
from config.settings import Config

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.config = Config()
        self.bot = None
        self.chat_id = self.config.TELEGRAM_CHAT_ID
        
        if self.config.TELEGRAM_BOT_TOKEN:
            self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
        else:
            logger.warning("Telegram bot token not configured")
    
    async def send_message(self, message, parse_mode='HTML'):
        """Send a message to Telegram"""
        if not self.bot or not self.chat_id:
            logger.warning("Telegram not configured, skipping message")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info("Telegram message sent successfully")
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False
    
    def send_message_sync(self, message, parse_mode='HTML'):
        """Synchronous wrapper for sending messages"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.send_message(message, parse_mode))
        except Exception as e:
            logger.error(f"Error in sync message send: {str(e)}")
            return False
    
    async def send_trading_signal(self, signal):
        """Send a trading signal alert"""
        try:
            emoji = "🚀" if signal['action'] == 'BUY' else "📉" if signal['action'] == 'SELL' else "⏸️"
            confidence_stars = "⭐" * min(5, int(signal['confidence'] / 20))
            
            message = f"""
{emoji} <b>TRADING SIGNAL</b> {emoji}

<b>Symbol:</b> {signal['symbol']}
<b>Action:</b> {signal['action']}
<b>Price:</b> ₹{signal['price']:.2f}
<b>Confidence:</b> {signal['confidence']:.1f}% {confidence_stars}

<b>Risk Management:</b>
• Stop Loss: ₹{signal.get('stop_loss', 0):.2f}
• Target: ₹{signal.get('target_price', 0):.2f}
• Risk Level: {signal.get('risk_level', 'Medium')}

<b>Reasons:</b>
{chr(10).join('• ' + reason for reason in signal.get('reasons', []))}

<b>Market Regime:</b> {signal.get('regime', 'Unknown')}
<b>Volume Spike:</b> {'✅' if signal.get('volume_spike') else '❌'}

<i>Generated at {signal.get('timestamp', datetime.now()).strftime('%H:%M:%S')}</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            logger.error(f"Error sending trading signal: {str(e)}")
            return False
    
    async def send_trade_execution(self, trade):
        """Send trade execution notification"""
        try:
            emoji = "✅" if trade['action'] == 'BUY' else "💰"
            pnl_emoji = "📈" if trade.get('pnl', 0) >= 0 else "📉"
            
            message = f"""
{emoji} <b>TRADE EXECUTED</b> {emoji}

<b>Symbol:</b> {trade['symbol']}
<b>Action:</b> {trade['action']}
<b>Price:</b> ₹{trade['price']:.2f}
<b>Quantity:</b> {trade['quantity']}
<b>Amount:</b> ₹{trade['amount']:,.2f}
            """
            
            if trade.get('pnl') is not None and trade['action'] == 'SELL':
                message += f"""
<b>P&L:</b> ₹{trade['pnl']:,.2f} {pnl_emoji}
<b>Portfolio Value:</b> ₹{trade['portfolio_value']:,.2f}
                """
            
            message += f"""
<b>Reason:</b> {trade.get('reason', 'Manual')}
<i>Executed at {trade.get('timestamp', datetime.now()).strftime('%H:%M:%S')}</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            logger.error(f"Error sending trade execution: {str(e)}")
            return False
    
    async def send_portfolio_update(self, portfolio_status):
        """Send portfolio status update"""
        try:
            total_pnl = portfolio_status.get('total_pnl', 0)
            return_pct = portfolio_status.get('return_pct', 0)
            
            trend_emoji = "📈" if total_pnl >= 0 else "📉"
            status_emoji = "🎯" if abs(return_pct) >= 3 else "📊"
            
            message = f"""
{status_emoji} <b>PORTFOLIO UPDATE</b> {status_emoji}

<b>Total Value:</b> ₹{portfolio_status.get('total_value', 0):,.2f}
<b>Cash:</b> ₹{portfolio_status.get('cash', 0):,.2f}
<b>Positions:</b> ₹{portfolio_status.get('position_value', 0):,.2f}

<b>P&L:</b> ₹{total_pnl:,.2f} {trend_emoji}
<b>Return:</b> {return_pct:.2f}%
<b>Positions Count:</b> {portfolio_status.get('positions_count', 0)}

<b>Today's Target:</b> ₹{self.config.PROFIT_TARGET:,.2f}
<b>Progress:</b> {min(100, (total_pnl/self.config.PROFIT_TARGET)*100) if self.config.PROFIT_TARGET > 0 else 0:.1f}%

<i>Updated at {datetime.now().strftime('%H:%M:%S')}</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            logger.error(f"Error sending portfolio update: {str(e)}")
            return False
    
    async def send_market_regime_update(self, regime_info):
        """Send market regime change notification"""
        try:
            regime = regime_info.get('regime', 'unknown')
            confidence = regime_info.get('confidence', 0)
            
            regime_emojis = {
                'bull': '🐂',
                'bear': '🐻',
                'sideways': '↔️'
            }
            
            emoji = regime_emojis.get(regime, '❓')
            confidence_stars = "⭐" * min(5, int(confidence / 20))
            
            message = f"""
{emoji} <b>MARKET REGIME UPDATE</b> {emoji}

<b>Current Regime:</b> {regime.upper()}
<b>Confidence:</b> {confidence:.1f}% {confidence_stars}

<b>Key Factors:</b>
• Stocks above EMA21: {regime_info.get('factors', {}).get('stocks_above_ema21', 0):.1f}%
• Average RSI: {regime_info.get('factors', {}).get('avg_rsi', 0):.1f}
• Market Breadth: {regime_info.get('factors', {}).get('market_breadth', 0):.1f}
• Price Momentum: {regime_info.get('factors', {}).get('price_momentum', 0):.2f}%

<b>Trading Recommendation:</b>
{self._get_regime_advice(regime)}

<i>Updated at {datetime.now().strftime('%H:%M:%S')}</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            logger.error(f"Error sending regime update: {str(e)}")
            return False
    
    def _get_regime_advice(self, regime):
        """Get trading advice based on regime"""
        advice = {
            'bull': "🟢 Aggressive long positions, follow trends, avoid shorting",
            'bear': "🔴 Conservative approach, look for shorts, protect capital",
            'sideways': "🟡 Range trading, buy support, sell resistance, small positions"
        }
        return advice.get(regime, "⚪ Monitor market closely, wait for clear signals")
    
    async def send_daily_summary(self, summary_data):
        """Send end-of-day summary"""
        try:
            trades_count = summary_data.get('trades_executed', 0)
            daily_pnl = summary_data.get('daily_pnl', 0)
            win_rate = summary_data.get('win_rate', 0)
            
            status_emoji = "🎉" if daily_pnl >= self.config.PROFIT_TARGET else "📊"
            trend_emoji = "📈" if daily_pnl >= 0 else "📉"
            
            message = f"""
{status_emoji} <b>DAILY TRADING SUMMARY</b> {status_emoji}

<b>Trades Executed:</b> {trades_count}
<b>Daily P&L:</b> ₹{daily_pnl:,.2f} {trend_emoji}
<b>Win Rate:</b> {win_rate:.1f}%
<b>Target Achievement:</b> {(daily_pnl/self.config.PROFIT_TARGET)*100:.1f}%

<b>Portfolio Performance:</b>
• Total Value: ₹{summary_data.get('portfolio_value', 0):,.2f}
• Total Return: {summary_data.get('total_return_pct', 0):.2f}%
• Active Positions: {summary_data.get('active_positions', 0)}

<b>Market Conditions:</b>
• Regime: {summary_data.get('market_regime', 'Unknown')}
• Signals Generated: {summary_data.get('signals_generated', 0)}

<i>Report generated at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {str(e)}")
            return False
    
    async def send_system_alert(self, alert_type, message_text):
        """Send system alerts (errors, warnings, etc.)"""
        try:
            alert_emojis = {
                'error': '🚨',
                'warning': '⚠️',
                'info': 'ℹ️',
                'success': '✅'
            }
            
            emoji = alert_emojis.get(alert_type, '📢')
            
            message = f"""
{emoji} <b>SYSTEM ALERT</b> {emoji}

<b>Type:</b> {alert_type.upper()}
<b>Message:</b> {message_text}
<b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            logger.error(f"Error sending system alert: {str(e)}")
            return False
    
    def test_connection(self):
        """Test Telegram bot connection"""
        try:
            if not self.bot:
                return False, "Bot not configured"
            
            # Send a test message
            test_message = "🤖 Trading Bot Connection Test\n\nIf you can see this message, the bot is working correctly!"
            success = self.send_message_sync(test_message)
            
            if success:
                return True, "Connection successful"
            else:
                return False, "Failed to send test message"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    async def send_backtest_results(self, results):
        """Send backtest results summary"""
        try:
            summary = results.get('summary', {})
            performance = results.get('performance', {})
            
            total_return = summary.get('total_return_pct', 0)
            win_rate = summary.get('win_rate', 0)
            total_trades = summary.get('total_trades', 0)
            
            emoji = "📊"
            trend_emoji = "📈" if total_return >= 0 else "📉"
            
            message = f"""
{emoji} <b>BACKTEST RESULTS</b> {emoji}

<b>Performance Summary:</b>
• Total Return: {total_return:.2f}% {trend_emoji}
• Win Rate: {win_rate:.1f}%
• Total Trades: {total_trades}
• Profit Factor: {summary.get('profit_factor', 0):.2f}

<b>Risk Metrics:</b>
• Max Drawdown: {performance.get('max_drawdown_pct', 0):.2f}%
• Sharpe Ratio: {performance.get('sharpe_ratio', 0):.2f}
• Volatility: {performance.get('volatility_pct', 0):.2f}%

<b>Trading Stats:</b>
• Winning Trades: {results.get('trades', {}).get('winning_trades', 0)}
• Losing Trades: {results.get('trades', {}).get('losing_trades', 0)}
• Avg Win: ₹{results.get('trades', {}).get('avg_win', 0):.2f}
• Avg Loss: ₹{results.get('trades', {}).get('avg_loss', 0):.2f}

<i>Backtest completed at {datetime.now().strftime('%H:%M:%S')}</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            logger.error(f"Error sending backtest results: {str(e)}")
            return False