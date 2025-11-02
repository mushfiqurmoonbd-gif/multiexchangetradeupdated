"""
WeightedSignalGenerator - PERCENTAGE-WEIGHTED SIGNAL SYSTEM

This module generates signals based on weighted averages of multiple indicators.

DEFAULT WEIGHTS:
- EMA/TradingView Signals: 40%
- RSI: 40%
- WaveTrend: 20%

Use this for:
- Balanced multi-indicator signals
- Adjustable weight distribution
- Signal strength calculations

Alternative systems:
- signals/trading_triggers.py: Priority-based hierarchy
- strategies/client_weighted.py: Strategy-specific weights
- signals/engine.py: Multi-source alignment
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from .rsi import rsi
from .wavetrend import wavetrend

class WeightedSignalGenerator:
    """
    Weighted signal generator implementing:
    - EMA/TradingView Signals: 40% weight
    - RSI: 40% weight
    - WaveTrend: 20% weight
    """
    
    def __init__(self, 
                 ema_weight: float = 0.4,
                 rsi_weight: float = 0.4, 
                 wavetrend_weight: float = 0.2):
        """
        Initialize weighted signal generator
        
        Args:
            ema_weight: Weight for EMA/TradingView signals (default: 0.4)
            rsi_weight: Weight for RSI signals (default: 0.4)
            wavetrend_weight: Weight for WaveTrend signals (default: 0.2)
        """
        self.ema_weight = ema_weight
        self.rsi_weight = rsi_weight
        self.wavetrend_weight = wavetrend_weight
        
        # Validate weights sum to 1.0
        total_weight = ema_weight + rsi_weight + wavetrend_weight
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def generate_rsi_signal(self, df: pd.DataFrame, 
                           rsi_length: int = 14,
                           oversold: float = 30,
                           overbought: float = 70) -> pd.Series:
        """
        Generate RSI-based signals
        
        Returns:
            pd.Series: RSI signal strength (-1 to 1)
        """
        rsi_values = rsi(df['close'], length=rsi_length)
        
        # Normalize RSI to -1 to 1 range
        # Oversold (30) = 1 (strong buy)
        # Overbought (70) = -1 (strong sell)
        # Neutral (50) = 0
        
        rsi_signal = np.where(
            rsi_values <= oversold, 1.0,  # Strong buy
            np.where(
                rsi_values >= overbought, -1.0,  # Strong sell
                np.where(
                    rsi_values < 50, 
                    (50 - rsi_values) / (50 - oversold),  # Buy signal strength
                    -(rsi_values - 50) / (overbought - 50)  # Sell signal strength
                )
            )
        )
        
        return pd.Series(rsi_signal, index=df.index)
    
    def generate_wavetrend_signal(self, df: pd.DataFrame,
                                 channel_length: int = 10,
                                 average_length: int = 21) -> pd.Series:
        """
        Generate WaveTrend-based signals
        
        Returns:
            pd.Series: WaveTrend signal strength (-1 to 1)
        """
        # Calculate hlc3 for WaveTrend
        if set(['high', 'low', 'close']).issubset(df.columns):
            hlc3 = (df['high'] + df['low'] + df['close']) / 3.0
        else:
            hlc3 = df['close']
        
        wt = wavetrend(hlc3, channel_length=channel_length, average_length=average_length)
        
        # Generate signals based on WaveTrend crossovers and levels
        wt1 = wt['wt1']
        wt2 = wt['wt2']
        
        # Signal based on crossovers and extreme levels
        wt_signal = np.where(
            (wt1 > wt2) & (wt1 < -50), 1.0,  # Strong buy: WT1 above WT2 and oversold
            np.where(
                (wt1 < wt2) & (wt1 > 50), -1.0,  # Strong sell: WT1 below WT2 and overbought
                np.where(
                    wt1 > wt2, 0.5,  # Weak buy: WT1 above WT2
                    -0.5  # Weak sell: WT1 below WT2
                )
            )
        )
        
        return pd.Series(wt_signal, index=df.index)
    
    def generate_ema_signal(self, df: pd.DataFrame,
                           ema_fast: int = 50,
                           ema_slow: int = 200) -> pd.Series:
        """
        Generate EMA-based signals (EMA50/EMA200 crossover)
        
        Returns:
            pd.Series: EMA signal strength (-1 to 1)
        """
        close = df['close'] if 'close' in df.columns else df.iloc[:, 0]
        
        # Calculate EMA indicators
        ema_fast_series = close.ewm(span=ema_fast, adjust=False).mean()
        ema_slow_series = close.ewm(span=ema_slow, adjust=False).mean()
        
        # Calculate distance and crossover signals
        ema_dist = (ema_fast_series - ema_slow_series) / ema_slow_series
        
        # Normalize to -1 to 1 range
        ema_signal = np.clip(ema_dist * 20, -1, 1)
        
        return pd.Series(ema_signal, index=df.index)
    
    def generate_weighted_signal(self, df: pd.DataFrame,
                               rsi_length: int = 14,
                               rsi_oversold: float = 30,
                               rsi_overbought: float = 70,
                               wt_channel_length: int = 10,
                               wt_average_length: int = 21,
                               ema_fast: int = 50,
                               ema_slow: int = 200) -> Dict[str, pd.Series]:
        """
        Generate weighted signals combining all indicators (40% EMA, 40% RSI, 20% WaveTrend)
        
        Returns:
            Dict containing:
            - 'rsi_signal': RSI signal strength
            - 'wavetrend_signal': WaveTrend signal strength  
            - 'ema_signal': EMA signal strength
            - 'weighted_signal': Final weighted signal
            - 'final_long': Boolean buy signal
            - 'final_short': Boolean sell signal
        """
        # Generate individual signals
        rsi_sig = self.generate_rsi_signal(df, rsi_length, rsi_oversold, rsi_overbought)
        wt_sig = self.generate_wavetrend_signal(df, wt_channel_length, wt_average_length)
        ema_sig = self.generate_ema_signal(df, ema_fast, ema_slow)
        
        # Calculate weighted signal (40% EMA, 40% RSI, 20% WaveTrend)
        weighted_signal = (
            ema_sig * self.ema_weight +
            rsi_sig * self.rsi_weight +
            wt_sig * self.wavetrend_weight
        )
        
        # Generate final boolean signals
        # Long when weighted signal > 0.3, Short when < -0.3
        final_long = weighted_signal > 0.3
        final_short = weighted_signal < -0.3
        
        return {
            'rsi_signal': rsi_sig,
            'wavetrend_signal': wt_sig,
            'ema_signal': ema_sig,
            'weighted_signal': weighted_signal,
            'final_long': final_long,
            'final_short': final_short
        }
    
    def get_signal_strength(self, weighted_signal: float) -> str:
        """
        Convert weighted signal value to descriptive strength
        
        Args:
            weighted_signal: Signal value between -1 and 1
            
        Returns:
            str: Signal strength description
        """
        if weighted_signal >= 0.7:
            return "Very Strong Buy"
        elif weighted_signal >= 0.3:
            return "Strong Buy"
        elif weighted_signal >= 0.1:
            return "Weak Buy"
        elif weighted_signal <= -0.7:
            return "Very Strong Sell"
        elif weighted_signal <= -0.3:
            return "Strong Sell"
        elif weighted_signal <= -0.1:
            return "Weak Sell"
        else:
            return "Neutral"
