"""
Executor Module - Exchange Integration and Order Execution

This module provides unified interface for multiple cryptocurrency and stock exchanges.

COMPONENTS:
- executor/ccxt_executor.py: Universal CCXT-based executor (6+ exchanges)
- executor/bybit_v5_executor.py: Native Bybit V5 API executor
- executor/bybit_v5_data_fetcher.py: Bybit V5 market data fetcher

SUPPORTED EXCHANGES:
- Binance (crypto)
- Bybit (crypto) - Native V5 API
- MEXC (crypto)
- Alpaca (US stocks + crypto)
- Coinbase (crypto)
- Kraken (US-compliant crypto)

Usage:
    from executor.ccxt_executor import CCXTExecutor
    
    # Initialize for paper trading
    executor = CCXTExecutor(exchange_name='binance', paper=True)
    
    # Fetch market data
    df = executor.fetch_ohlcv_df(symbol='BTC/USDT', timeframe='1h', limit=500)
    
    # Place orders
    order = executor.place_market_order(symbol='BTC/USDT', side='buy', amount=0.001)
"""

