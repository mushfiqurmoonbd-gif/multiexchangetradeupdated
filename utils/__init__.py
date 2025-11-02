"""
Utils Module - Supporting Utilities

This module provides utilities for risk management, logging, metrics, and helpers.

RISK MANAGEMENT HIERARCHY:
- utils/risk.py: Simple helper functions (position sizing, SL/TP)
- utils/advanced_risk.py: AdvancedRiskManager - Base class with TP1/TP2/Runner, daily breaker
- utils/configurable_risk.py: ConfigurableRiskManager - Extends AdvancedRiskManager with multiple stop-loss methods

Usage:
    from utils.risk import position_size_from_risk, apply_sl_tp
    from utils.advanced_risk import AdvancedRiskManager
    from utils.configurable_risk import ConfigurableRiskManager, StopLossType
    
    # Simple risk calculation
    size = position_size_from_risk(10000, 0.02, 50000)
    
    # Advanced risk management
    risk_mgr = AdvancedRiskManager(initial_capital=10000)
    position = risk_mgr.open_position(symbol="BTCUSDT", side="buy", 
                                     entry_price=50000, stop_loss_price=49000)
    
    # Configurable risk with ATR-based stops
    config_risk = ConfigurableRiskManager(default_stop_loss_type=StopLossType.ATR)
"""

