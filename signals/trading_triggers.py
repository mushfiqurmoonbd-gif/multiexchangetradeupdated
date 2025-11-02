"""
TradingTriggerEngine - PRIORITY-BASED SIGNAL SYSTEM

This module implements a 3-tier hierarchy signal system for trading decisions.

HIERARCHY:
1. WT cross green/red dots (buy/sell) - HIGHEST PRIORITY
2. TradingView Webhook signals (buy/sell) - MEDIUM PRIORITY  
3. RSI thresholds (above 53 buy, below 47 sell) - LOWEST PRIORITY

Use this for:
- Priority-based signal filtering
- Ensuring only high-confidence signals trigger trades
- Prevents conflicting signals

Alternative systems:
- indicators/weighted_signals.py: Percentage-weighted signals (40% TradingView, 40% RSI, 20% WT)
- strategies/client_weighted.py: Strategy-specific weighted signals
- signals/engine.py: Multi-source signal alignment
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from indicators.wavetrend import wavetrend
from indicators.rsi import rsi

class TradingTriggerEngine:
    """
    Trading trigger engine implementing the 3-tier hierarchy:
    1. WT cross green dot (buy signal) or red dot (sell signal) - HIGHEST PRIORITY
    2. TradingView Webhook buy/sell signals - MEDIUM PRIORITY  
    3. RSI below 47 sell or above 53 buy - LOWEST PRIORITY
    """
    
    def __init__(self):
        self.trigger_hierarchy = [
            'wt_cross_signals',  # Priority 1
            'buy_sell_signals',  # Priority 2
            'rsi_thresholds'     # Priority 3
        ]
    
    def generate_wt_cross_signals(self, df: pd.DataFrame, 
                                 channel_length: int = 10, 
                                 average_length: int = 21) -> Dict[str, pd.Series]:
        """
        Generate WaveTrend cross signals (green/red dots)
        
        Args:
            df: DataFrame with OHLC data
            channel_length: WT channel length
            average_length: WT average length
            
        Returns:
            Dict with 'wt_buy' and 'wt_sell' signals
        """
        # Calculate hlc3 for WaveTrend
        if set(['high', 'low', 'close']).issubset(df.columns):
            hlc3 = (df['high'] + df['low'] + df['close']) / 3.0
        else:
            hlc3 = df['close']
        
        # Calculate WaveTrend
        wt = wavetrend(hlc3, channel_length=channel_length, average_length=average_length)
        wt1 = wt['wt1']
        wt2 = wt['wt2']
        
        # Detect crossovers
        wt_cross_up = (wt1.shift(1) <= wt2.shift(1)) & (wt1 > wt2)
        wt_cross_down = (wt1.shift(1) >= wt2.shift(1)) & (wt1 < wt2)
        
        # Green dot: WT1 crosses above WT2 (buy signal)
        wt_buy = wt_cross_up.copy()
        
        # Red dot: WT1 crosses below WT2 (sell signal)  
        wt_sell = wt_cross_down.copy()
        
        return {
            'wt_buy': wt_buy,
            'wt_sell': wt_sell,
            'wt1': wt1,
            'wt2': wt2
        }
    
    def generate_buy_sell_signals(self, df: pd.DataFrame,
                                 lookback: int = 20,
                                 ema_fast: int = 50,
                                 ema_slow: int = 200) -> Dict[str, pd.Series]:
        """
        Generate TradingView webhook-based signals (Priority 2)
        
        Args:
            df: DataFrame with price data and webhook signals
            lookback: Lookback period for momentum (unused, kept for compatibility)
            ema_fast: Fast EMA period (unused, kept for compatibility)
            ema_slow: Slow EMA period (unused, kept for compatibility)
            
        Returns:
            Dict with 'momentum_buy' and 'momentum_sell' signals from webhook
        """
        # Check if webhook column exists, otherwise create empty signals
        if 'webhook' in df.columns:
            # Use webhook signals directly
            momentum_buy = df['webhook'].astype(bool)
            momentum_sell = pd.Series(False, index=df.index)  # Webhook only provides buy signals typically
        else:
            # Fallback: No webhook signals available
            momentum_buy = pd.Series(False, index=df.index)
            momentum_sell = pd.Series(False, index=df.index)
        
        return {
            'momentum_buy': momentum_buy,
            'momentum_sell': momentum_sell
        }
    
    def generate_rsi_thresholds(self, df: pd.DataFrame,
                               rsi_length: int = 14,
                               rsi_buy_threshold: float = 53.0,
                               rsi_sell_threshold: float = 47.0) -> Dict[str, pd.Series]:
        """
        Generate RSI threshold signals
        
        Args:
            df: DataFrame with price data
            rsi_length: RSI calculation length
            rsi_buy_threshold: RSI buy threshold (above this = buy)
            rsi_sell_threshold: RSI sell threshold (below this = sell)
            
        Returns:
            Dict with 'rsi_buy' and 'rsi_sell' signals
        """
        rsi_values = rsi(df['close'], length=rsi_length)
        
        # Buy when RSI > buy_threshold
        rsi_buy = rsi_values > rsi_buy_threshold
        
        # Sell when RSI < sell_threshold
        rsi_sell = rsi_values < rsi_sell_threshold
        
        return {
            'rsi_buy': rsi_buy,
            'rsi_sell': rsi_sell,
            'rsi': rsi_values
        }
    
    def generate_combined_signals(self, df: pd.DataFrame,
                                 # WT parameters
                                 wt_channel_length: int = 10,
                                 wt_average_length: int = 21,
                                 # EMA parameters  
                                 ema_fast: int = 50,
                                 ema_slow: int = 200,
                                 # RSI parameters
                                 rsi_length: int = 14,
                                 rsi_buy_threshold: float = 53.0,
                                 rsi_sell_threshold: float = 47.0,
                                 show_intermediate: bool = False) -> Dict[str, pd.Series]:
        """
        Generate combined trading signals following the 3-tier hierarchy
        
        Args:
            df: DataFrame with OHLC data
            wt_channel_length: WaveTrend channel length
            wt_average_length: WaveTrend average length
            ema_fast: Fast EMA period (default: 50)
            ema_slow: Slow EMA period (default: 200)
            rsi_length: RSI calculation length
            rsi_buy_threshold: RSI buy threshold
            rsi_sell_threshold: RSI sell threshold
            show_intermediate: Whether to return intermediate signals
            
        Returns:
            Dict with final signals and optionally intermediate signals
        """
        # Generate all signal types
        wt_signals = self.generate_wt_cross_signals(df, wt_channel_length, wt_average_length)
        momentum_signals = self.generate_buy_sell_signals(df, ema_fast=ema_fast, ema_slow=ema_slow)
        rsi_signals = self.generate_rsi_thresholds(df, rsi_length, rsi_buy_threshold, rsi_sell_threshold)
        
        # Initialize final signals
        final_buy = pd.Series(False, index=df.index)
        final_sell = pd.Series(False, index=df.index)
        
        # Apply hierarchy: Priority 1 - WT Cross Signals
        wt_buy_mask = wt_signals['wt_buy']
        wt_sell_mask = wt_signals['wt_sell']
        
        final_buy |= wt_buy_mask
        final_sell |= wt_sell_mask
        
        # Apply hierarchy: Priority 2 - Buy/Sell Signals (only where no WT signal)
        momentum_buy_mask = momentum_signals['momentum_buy'] & ~wt_buy_mask & ~wt_sell_mask
        momentum_sell_mask = momentum_signals['momentum_sell'] & ~wt_buy_mask & ~wt_sell_mask
        
        final_buy |= momentum_buy_mask
        final_sell |= momentum_sell_mask
        
        # Apply hierarchy: Priority 3 - RSI Thresholds (only where no higher priority signal)
        rsi_buy_mask = rsi_signals['rsi_buy'] & ~final_buy & ~final_sell
        rsi_sell_mask = rsi_signals['rsi_sell'] & ~final_buy & ~final_sell
        
        final_buy |= rsi_buy_mask
        final_sell |= rsi_sell_mask
        
        result = {
            'final_buy': final_buy,
            'final_sell': final_sell,
            'rsi': rsi_signals['rsi'],
            'wt1': wt_signals['wt1'],
            'wt2': wt_signals['wt2']
        }
        
        if show_intermediate:
            result.update({
                'wt_buy': wt_signals['wt_buy'],
                'wt_sell': wt_signals['wt_sell'],
                'momentum_buy': momentum_signals['momentum_buy'],
                'momentum_sell': momentum_signals['momentum_sell'],
                'rsi_buy': rsi_signals['rsi_buy'],
                'rsi_sell': rsi_signals['rsi_sell']
            })
        
        return result
    
    def get_signal_strength(self, signals: Dict[str, pd.Series], idx: int) -> Dict[str, str]:
        """
        Get signal strength description for a specific index
        
        Args:
            signals: Signal dictionary
            idx: Index to analyze
            
        Returns:
            Dict with signal strength descriptions
        """
        result = {}
        
        # Check each signal type
        if signals.get('wt_buy', pd.Series()).iloc[idx] if idx < len(signals.get('wt_buy', pd.Series())) else False:
            result['primary'] = "WT Green Dot (BUY)"
        elif signals.get('wt_sell', pd.Series()).iloc[idx] if idx < len(signals.get('wt_sell', pd.Series())) else False:
            result['primary'] = "WT Red Dot (SELL)"
        elif signals.get('momentum_buy', pd.Series()).iloc[idx] if idx < len(signals.get('momentum_buy', pd.Series())) else False:
            result['primary'] = "Momentum BUY"
        elif signals.get('momentum_sell', pd.Series()).iloc[idx] if idx < len(signals.get('momentum_sell', pd.Series())) else False:
            result['primary'] = "Momentum SELL"
        elif signals.get('rsi_buy', pd.Series()).iloc[idx] if idx < len(signals.get('rsi_buy', pd.Series())) else False:
            result['primary'] = "RSI BUY"
        elif signals.get('rsi_sell', pd.Series()).iloc[idx] if idx < len(signals.get('rsi_sell', pd.Series())) else False:
            result['primary'] = "RSI SELL"
        else:
            result['primary'] = "No Signal"
        
        return result
