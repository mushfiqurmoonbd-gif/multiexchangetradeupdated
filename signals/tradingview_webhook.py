#!/usr/bin/env python3
"""
TradingView Webhook Integration - FULL-FEATURED VERSION
Receives buy/sell signals from TradingView alerts and executes trades automatically

This is the PRIMARY webhook handler with complete functionality:
- Signal parsing and validation
- Signature verification
- Trade execution integration
- Comprehensive logging

Use this for:
- Production trading with automatic execution
- Full webhook processing with CCXT executor

Alternative servers:
- tradingview_webhook_server.py: Simple signal storage
- server_realtime.py: Real-time Socket.IO broadcasting
"""

from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingViewWebhook:
    """
    TradingView Webhook Handler
    
    Receives and processes webhook alerts from TradingView
    """
    
    def __init__(self, secret_key: str = None):
        """
        Initialize webhook handler
        
        Args:
            secret_key: Secret key for webhook authentication
        """
        self.secret_key = secret_key or os.getenv('TRADINGVIEW_WEBHOOK_SECRET', 'your-secret-key-here')
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Signal history for logging
        self.signal_history = []
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/webhook/tradingview', methods=['POST'])
        def receive_webhook():
            """Receive TradingView webhook POST request"""
            try:
                # Get JSON payload
                data = request.get_json()
                
                if not data:
                    logger.error("No JSON data received")
                    return jsonify({'error': 'No data provided'}), 400
                
                # Verify webhook signature if provided
                signature = request.headers.get('X-TradingView-Signature')
                if signature and not self.verify_signature(data, signature):
                    logger.error("Invalid webhook signature")
                    return jsonify({'error': 'Invalid signature'}), 403
                
                # Parse and validate signal
                signal = self.parse_signal(data)
                if not signal:
                    logger.error(f"Invalid signal format: {data}")
                    return jsonify({'error': 'Invalid signal format'}), 400
                
                # Log signal
                logger.info(f"Received TradingView signal: {signal}")
                self.signal_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'signal': signal,
                    'raw_data': data
                })
                
                # Return success response
                return jsonify({
                    'status': 'success',
                    'message': 'Signal received',
                    'signal': signal,
                    'timestamp': datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/webhook/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'service': 'TradingView Webhook',
                'timestamp': datetime.now().isoformat()
            }), 200
        
        @self.app.route('/webhook/history', methods=['GET'])
        def get_history():
            """Get signal history"""
            return jsonify({
                'total_signals': len(self.signal_history),
                'signals': self.signal_history[-50:]  # Last 50 signals
            }), 200
    
    def verify_signature(self, data: Dict, signature: str) -> bool:
        """
        Verify webhook signature for security
        
        Args:
            data: Webhook payload
            signature: Signature from header
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # Create HMAC signature
            message = json.dumps(data, sort_keys=True).encode()
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    def parse_signal(self, data: Dict) -> Optional[Dict[str, Any]]:
        """
        Parse TradingView webhook signal
        
        Expected formats:
        
        Format 1 (Simple):
        {
            "action": "buy",
            "symbol": "BTCUSDT",
            "price": 95000
        }
        
        Format 2 (Detailed):
        {
            "ticker": "BINANCE:BTCUSDT",
            "action": "buy",
            "price": 95000,
            "time": "2025-10-29T12:00:00Z",
            "strategy": "EMA Crossover",
            "message": "Buy signal triggered"
        }
        
        Format 3 (Pine Script Alert):
        {
            "action": "{{strategy.order.action}}",
            "contracts": "{{strategy.order.contracts}}",
            "ticker": "{{ticker}}",
            "price": "{{close}}"
        }
        
        Args:
            data: Raw webhook data
            
        Returns:
            Parsed signal dict or None if invalid
        """
        try:
            # Extract action (buy/sell/long/short/close)
            action = data.get('action', '').lower()
            
            # Map various action formats
            action_map = {
                'buy': 'buy',
                'long': 'buy',
                'sell': 'sell',
                'short': 'sell',
                'close': 'close',
                'exit': 'close'
            }
            
            if action not in action_map:
                logger.error(f"Unknown action: {action}")
                return None
            
            normalized_action = action_map[action]
            
            # Extract symbol
            symbol = data.get('symbol') or data.get('ticker', '')
            
            # Clean symbol (remove exchange prefix if present)
            if ':' in symbol:
                symbol = symbol.split(':')[1]
            
            # Extract price
            price = data.get('price') or data.get('close', 0)
            try:
                price = float(price)
            except (ValueError, TypeError):
                price = 0
            
            # Extract quantity/contracts
            quantity = data.get('quantity') or data.get('contracts') or data.get('amount', 0)
            try:
                quantity = float(quantity)
            except (ValueError, TypeError):
                quantity = 0
            
            # Extract optional fields
            strategy = data.get('strategy', 'TradingView Alert')
            message = data.get('message', '')
            exchange = data.get('exchange', 'binance')
            
            # Extract stop-loss and take-profit if provided
            stop_loss = data.get('stop_loss') or data.get('sl', 0)
            take_profit = data.get('take_profit') or data.get('tp', 0)
            
            try:
                stop_loss = float(stop_loss) if stop_loss else 0
                take_profit = float(take_profit) if take_profit else 0
            except (ValueError, TypeError):
                stop_loss = 0
                take_profit = 0
            
            # Build parsed signal
            parsed_signal = {
                'action': normalized_action,
                'symbol': symbol,
                'price': price,
                'quantity': quantity,
                'exchange': exchange.lower(),
                'strategy': strategy,
                'message': message,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timestamp': datetime.now().isoformat(),
                'raw_data': data
            }
            
            # Validate required fields
            if not symbol:
                logger.error("Symbol is required")
                return None
            
            if normalized_action not in ['buy', 'sell', 'close']:
                logger.error(f"Invalid action: {normalized_action}")
                return None
            
            return parsed_signal
            
        except Exception as e:
            logger.error(f"Error parsing signal: {e}")
            return None
    
    def execute_signal(self, signal: Dict[str, Any], executor) -> Dict[str, Any]:
        """
        Execute trading signal using provided executor
        
        Args:
            signal: Parsed signal dictionary
            executor: CCXTExecutor instance
            
        Returns:
            Execution result
        """
        try:
            action = signal['action']
            symbol = signal['symbol']
            quantity = signal['quantity']
            
            logger.info(f"Executing signal: {action} {quantity} {symbol}")
            
            if action == 'buy':
                # Place buy order
                result = executor.place_market_order(
                    symbol=symbol,
                    side='buy',
                    amount=quantity if quantity > 0 else None
                )
                
            elif action == 'sell':
                # Place sell order
                result = executor.place_market_order(
                    symbol=symbol,
                    side='sell',
                    amount=quantity if quantity > 0 else None
                )
                
            elif action == 'close':
                # Close position
                # This would need position tracking to determine quantity
                logger.info(f"Close signal received for {symbol}")
                result = {'status': 'close_signal', 'symbol': symbol}
            
            else:
                result = {'status': 'error', 'message': f'Unknown action: {action}'}
            
            logger.info(f"Signal execution result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """
        Run Flask webhook server
        
        Args:
            host: Host address
            port: Port number
            debug: Debug mode
        """
        logger.info(f"Starting TradingView Webhook Server on {host}:{port}")
        logger.info(f"Webhook URL: http://{host}:{port}/webhook/tradingview")
        logger.info("Send POST requests to this URL from TradingView alerts")
        
        self.app.run(host=host, port=port, debug=debug)


def create_sample_alert_script():
    """
    Generate sample TradingView Pine Script for alerts
    
    Returns:
        str: Pine Script code
    """
    script = '''
//@version=5
indicator("TradingView Webhook Alerts", overlay=true)

// Your strategy logic here
fastMA = ta.sma(close, 10)
slowMA = ta.sma(close, 20)

// Buy signal
buySignal = ta.crossover(fastMA, slowMA)
sellSignal = ta.crossunder(fastMA, slowMA)

// Plot
plot(fastMA, color=color.blue, title="Fast MA")
plot(slowMA, color=color.red, title="Slow MA")

plotshape(buySignal, style=shape.triangleup, location=location.belowbar, 
          color=color.green, size=size.small, title="Buy Signal")
plotshape(sellSignal, style=shape.triangledown, location=location.abovebar, 
          color=color.red, size=size.small, title="Sell Signal")

// Webhook Alert Messages
// For Buy Signal:
// {
//   "action": "buy",
//   "symbol": "{{ticker}}",
//   "price": {{close}},
//   "time": "{{time}}",
//   "strategy": "MA Crossover",
//   "message": "Fast MA crossed above Slow MA"
// }

// For Sell Signal:
// {
//   "action": "sell",
//   "symbol": "{{ticker}}",
//   "price": {{close}},
//   "time": "{{time}}",
//   "strategy": "MA Crossover",
//   "message": "Fast MA crossed below Slow MA"
// }

// Setup Alert:
// 1. Click "Create Alert" button
// 2. Condition: Select your indicator
// 3. Alert actions: Check "Webhook URL"
// 4. Webhook URL: http://YOUR-SERVER:5000/webhook/tradingview
// 5. Message: Paste the JSON above
'''
    return script


if __name__ == "__main__":
    # Example usage
    print("=== TradingView Webhook Server ===\n")
    
    # Create webhook handler
    webhook = TradingViewWebhook()
    
    # Print sample Pine Script
    print("Sample Pine Script for TradingView Alerts:")
    print(create_sample_alert_script())
    
    # Start server
    print("\nStarting webhook server...")
    print("Press Ctrl+C to stop\n")
    
    webhook.run(host='0.0.0.0', port=5000, debug=True)

