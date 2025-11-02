"""
Backtester Module - Backtesting and Performance Analysis

This module provides backtesting capabilities at different complexity levels.

COMPONENTS:
- backtester/core.py: Basic backtest engine (fast, simple)
- backtester/enhanced_backtester.py: Advanced backtest with multi-timeframe
- backtester/comprehensive_metrics.py: Detailed metrics calculator
- backtester/multi_timeframe_analyzer.py: Multi-TF analysis

BACKTEST HIERARCHY:
┌─────────────────────────────────────────────────────────────┐
│ BASIC BACKTEST (core.py)                                    │
│ - Fast execution                                            │
│ - Simple SL/TP                                              │
│ - Basic metrics                                             │
│                                                             │
│ ENHANCED BACKTEST (enhanced_backtester.py)                  │
│ - Historical data fetching                                  │
│ - Multi-timeframe support                                   │
│ - Advanced risk management                                  │
│ - TP1/TP2/Runner system                                     │
│                                                             │
│ COMPREHENSIVE METRICS (comprehensive_metrics.py)            │
│ - 60+ metrics                                               │
│ - Sortino, Calmar, VaR, CVaR                               │
│ - Monthly performance analysis                              │
└─────────────────────────────────────────────────────────────┘

Usage:
    from backtester.core import run_backtest
    from backtester.enhanced_backtester import EnhancedBacktester
    
    # Basic backtest
    result = run_backtest(df, entry_col='signal', initial_cap=10000)
    
    # Enhanced backtest
    backtester = EnhancedBacktester()
    result = backtester.run_enhanced_backtest(
        symbol='BTCUSDT', timeframe='1h',
        start_date='2024-01-01', end_date='2024-12-31'
    )
"""

