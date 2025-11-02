"""
Strategies Module - Trading Strategies

This module provides various trading strategies with different approaches.

COMPONENTS:
- strategies/base.py: Abstract base class for all strategies
- strategies/manager.py: Strategy manager for regime-based selection
- strategies/client_weighted.py: Client-specific weighted strategy
- strategies/ema_crossover.py: EMA crossover strategy
- strategies/rsi_bbands.py: RSI + Bollinger Bands strategy
- strategies/grid.py: Grid trading strategy

Usage:
    from strategies.manager import StrategyManager
    
    # Initialize strategy manager
    manager = StrategyManager()
    
    # Select strategy by market regime
    strategy = manager.select_by_regime(df)
    
    # Generate signals
    signals = strategy.generate_signals(df)
"""

