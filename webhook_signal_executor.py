#!/usr/bin/env python3
"""
Webhook Signal Executor
Automatically executes trades when TradingView webhook signals are received
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Import executor and risk manager
from executor.ccxt_executor import CCXTExecutor
from utils.configurable_risk import ConfigurableRiskManager, StopLossType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class WebhookSignalExecutor:
    """
    Executes trades based on webhook signals from TradingView
    """
    
    def __init__(self):
        """Initialize the signal executor"""
        # Initialize executor
        exchange_name = os.getenv('EXCHANGE', 'binance')
        self.executor = CCXTExecutor(exchange_name=exchange_name, paper=True)
        
        # Initialize risk manager
        self.risk_manager = ConfigurableRiskManager(
            initial_capital=float(os.getenv('INITIAL_CAPITAL', 10000.0)),
            risk_per_trade=float(os.getenv('RISK_PER_TRADE', 0.02)),
            daily_loss_limit=float(os.getenv('DAILY_LOSS_LIMIT', 0.05)),
            max_positions=int(os.getenv('MAX_POSITIONS', 5)),
            default_stop_loss_pct=float(os.getenv('STOP_LOSS_PCT', 0.02)),
            default_stop_loss_type=StopLossType.PERCENTAGE
        )
        
        # Track open positions
        self.open_positions = {}
        
        logger.info("Webhook Signal Executor initialized")
    
    def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook signal and execute trade
        
        Args:
            signal: Signal dict with action, symbol, price, etc.
            
        Returns:
            Dict with execution result
        """
        try:
            action = signal.get('action', '').lower()
            symbol = signal.get('symbol', '').upper()
            
            if not symbol:
                logger.error("No symbol in signal")
                return {'status': 'error', 'message': 'No symbol provided'}
            
            if action == 'buy':
                return self._execute_buy(signal)
            elif action == 'sell':
                return self._execute_sell(signal)
            elif action == 'close':
                return self._execute_close(signal)
            else:
                logger.warning(f"Unknown action: {action}")
                return {'status': 'error', 'message': f'Unknown action: {action}'}
                
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _execute_buy(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute buy order"""
        try:
            symbol = signal.get('symbol', '').upper()
            price = signal.get('price', 0)
            
            # Check if position already exists
            if symbol in self.open_positions:
                logger.info(f"Position already exists for {symbol}")
                return {'status': 'skipped', 'message': 'Position already exists'}
            
            # Calculate position size using risk manager
            position_size = self.risk_manager.calculate_position_size(
                entry_price=price,
                stop_loss_price=price * 0.98  # 2% stop loss default
            )
            
            if position_size <= 0:
                logger.warning(f"Position size too small or risk limit reached")
                return {'status': 'skipped', 'message': 'Risk limit reached'}
            
            # Execute buy order (paper trading by default)
            result = self.executor.place_order(
                symbol=symbol,
                side='buy',
                amount=position_size,
                order_type='market',
                paper_trading=True
            )
            
            if result.get('success'):
                # Track position
                self.open_positions[symbol] = {
                    'entry_price': price,
                    'quantity': position_size,
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"Buy order executed: {symbol} @ ${price}, qty: {position_size}")
                return {'status': 'success', 'message': f'Buy executed: {symbol}', 'result': result}
            else:
                logger.error(f"Buy order failed: {result.get('error')}")
                return {'status': 'error', 'message': result.get('error')}
                
        except Exception as e:
            logger.error(f"Error executing buy: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _execute_sell(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sell order"""
        try:
            symbol = signal.get('symbol', '').upper()
            price = signal.get('price', 0)
            
            # Check if position exists
            if symbol not in self.open_positions:
                logger.info(f"No position exists for {symbol}")
                return {'status': 'skipped', 'message': 'No position to close'}
            
            position = self.open_positions[symbol]
            quantity = position['quantity']
            
            # Execute sell order
            result = self.executor.place_order(
                symbol=symbol,
                side='sell',
                amount=quantity,
                order_type='market',
                paper_trading=True
            )
            
            if result.get('success'):
                # Calculate P&L
                pnl = (price - position['entry_price']) * quantity
                logger.info(f"Sell order executed: {symbol} @ ${price}, P&L: ${pnl:.2f}")
                
                # Remove position
                del self.open_positions[symbol]
                return {'status': 'success', 'message': f'Sell executed: {symbol}', 'pnl': pnl, 'result': result}
            else:
                logger.error(f"Sell order failed: {result.get('error')}")
                return {'status': 'error', 'message': result.get('error')}
                
        except Exception as e:
            logger.error(f"Error executing sell: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _execute_close(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Close position (same as sell)"""
        return self._execute_sell(signal)
    
    def get_positions(self) -> Dict[str, Any]:
        """Get current open positions"""
        return self.open_positions


if __name__ == "__main__":
    print("=" * 60)
    print("Webhook Signal Executor")
    print("=" * 60)
    print("\nThis executor processes TradingView webhook signals")
    print("and executes trades automatically.\n")
    
    # Example usage
    executor = WebhookSignalExecutor()
    
    # Example signal
    test_signal = {
        'action': 'buy',
        'symbol': 'BTCUSDT',
        'price': 95000
    }
    
    print(f"Example signal: {json.dumps(test_signal, indent=2)}\n")
    print("To use with webhook server:")
    print("  1. Start server_realtime.py (port 8001)")
    print("  2. Configure TradingView alert to send to webhook")
    print("  3. Integrate this executor into the webhook handler\n")

