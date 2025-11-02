def to_yfinance_symbol(exchange: str, symbol: str) -> str:
    """
    Map exchange+symbol to a yfinance-friendly ticker for overlay charts.
    Examples:
      (BINANCE, SOLUSDT) -> SOL-USD
      (COINBASE, SOL-USD) -> SOL-USD
      (KRAKEN, SOLUSD) -> SOL-USD
    """
    ex = (exchange or "").lower()
    sym = (symbol or "").upper().replace("/", "").replace("-", "")

    # If symbol ends with USDT or USD, map to -USD for yfinance
    if sym.endswith("USDT"):
        base = sym[:-4]
        return f"{base}-USD"
    if sym.endswith("USD"):
        base = sym[:-3]
        return f"{base}-USD"
    # Fallback: return as-is for equities/forex already supported by yfinance
    return symbol


EXCHANGE_TICKER_HINTS = {
    "binance": "USDT",
    "bybit": "USDT",
    "mexc": "USDT",
    "coinbase": "USD",
    "kraken": "USD",
}

def normalize_symbol_for_exchange(exchange: str, base: str) -> str:
    """Return a plausible exchange symbol for a given base (e.g., SOL -> SOLUSDT or SOL-USD)."""
    ex = (exchange or '').lower()
    hint = EXCHANGE_TICKER_HINTS.get(ex, 'USD')
    if ex == 'coinbase':
        return f"{base}-USD"
    if hint == 'USDT':
        return f"{base}USDT"
    return f"{base}{hint}"


