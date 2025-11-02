"""
Signals Module - Trading Signal Generation and Processing

This module handles signal generation from multiple sources and webhook integration.

COMPONENTS:
- signals/engine.py: Multi-source signal alignment (consensus-based)
- signals/trading_triggers.py: Priority-based signal hierarchy
- signals/trading_triggers.py: 3-tier priority system (WT > Momentum > RSI)
- signals/tradingview_webhook.py: Full-featured webhook handler with execution
- signals/tradingview_webhook_server.py: Simple signal storage server

SIGNAL SYSTEM ARCHITECTURE:
┌─────────────────────────────────────────────────────────────┐
│ SIGNAL GENERATION (Choose ONE)                              │
├─────────────────────────────────────────────────────────────┤
│ 1. consensus_based (engine.py)                             │
│    - Requires ALL sources to agree                          │
│    - Highest confidence, fewer signals                      │
│                                                             │
│ 2. priority_based (trading_triggers.py)                     │
│    - Tier 1: WT crosses (highest priority)                 │
│    - Tier 2: Momentum signals                               │
│    - Tier 3: RSI thresholds                                 │
│                                                             │
│ 3. weighted_based (indicators/weighted_signals.py)          │
│    - Percentage-weighted averages                           │
│    - Customizable weights                                   │
└─────────────────────────────────────────────────────────────┘
"""

