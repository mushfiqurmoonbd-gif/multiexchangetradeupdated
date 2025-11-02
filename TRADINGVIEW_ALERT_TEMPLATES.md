# TradingView Alert Templates (Client Strategy)

Use these in the Alert "Message" field. Replace YOUR_SECRET and exchange/symbol.

## BUY
```
{
  "secret": "YOUR_SECRET",
  "exchange": "BINANCE",
  "symbol": "SOLUSDT",
  "tv_symbol": "BINANCE:SOLUSDT",
  "side": "buy",
  "price": {{close}},
  "time": "{{timenow}}",
  "timeframe": "{{interval}}",
  "strategy": "client_tv"
}
```

## SELL
```
{
  "secret": "YOUR_SECRET",
  "exchange": "BINANCE",
  "symbol": "SOLUSDT",
  "tv_symbol": "BINANCE:SOLUSDT",
  "side": "sell",
  "price": {{close}},
  "time": "{{timenow}}",
  "timeframe": "{{interval}}",
  "strategy": "client_tv"
}
```

- Set alert frequency to Once Per Bar Close for stability.
- Create separate alerts for each timeframe you want to drive signals for.
