"""
Indicators Module - Technical Analysis Indicators

This module provides technical analysis indicators for trading signals.

COMPONENTS:
- indicators/rsi.py: Relative Strength Index (RSI)
- indicators/wavetrend.py: WaveTrend oscillator
- indicators/weighted_signals.py: Weighted signal generator

Usage:
    from indicators.rsi import rsi
    from indicators.wavetrend import wavetrend
    from indicators.weighted_signals import WeightedSignalGenerator
    
    # Calculate RSI
    df['rsi'] = rsi(df['close'], length=14)
    
    # Calculate WaveTrend
    df[['wt1', 'wt2']] = wavetrend(df['hlc3'], channel_length=10, average_length=21)
    
    # Generate weighted signals
    generator = WeightedSignalGenerator(rsi_weight=0.4, wavetrend_weight=0.4, buy_sell_weight=0.2)
    signals = generator.generate_weighted_signal(df)
"""

