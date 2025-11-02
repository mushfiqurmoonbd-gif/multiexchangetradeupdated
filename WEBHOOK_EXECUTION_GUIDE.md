# Webhook Signal Execution Guide

## 📋 Overview

এখন আপনার ট্রেডিং সিস্টেমে **TradingView webhook signals থেকে স্বয়ংক্রিয় ট্রেড এক্সিকিউশন** সহজেই করতে পারবেন।

## 🚀 Quick Start

### 1. .env File Setup
`.env` file এ নিম্নলিখিত environment variables যোগ করুন:

```env
# Webhook Configuration
TRADINGVIEW_WEBHOOK_SECRET=your-secret-key-here
AUTO_EXECUTE_WEBHOOK=true

# Webhook Server
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000

# Exchange Configuration
EXCHANGE=binance  # or bybit, mexc, etc.

# Risk Management
INITIAL_CAPITAL=10000.0
RISK_PER_TRADE=0.02
DAILY_LOSS_LIMIT=0.05
MAX_POSITIONS=5
STOP_LOSS_PCT=0.02
```

### 2. Start Webhook Server

```bash
python signals/tradingview_webhook_server.py
```

Server চালু হলে দেখবেন:
```
✅ Webhook auto-execution enabled
TradingView Webhook listening on http://0.0.0.0:8000
POST alerts to: http://localhost:8000/webhook/tradingview
```

### 3. Configure TradingView Alert

TradingView এ alert create করার সময়:

1. **Alert Condition:** আপনার indicator signal
2. **Webhook URL:** `http://YOUR-SERVER-IP:8000/webhook/tradingview`
3. **Message (JSON):**

```json
{
  "secret": "your-secret-key-here",
  "action": "buy",
  "symbol": "BTCUSDT",
  "price": {{close}},
  "time": "{{time}}",
  "strategy": "EMA Cross",
  "message": "Fast EMA crossed above Slow EMA"
}
```

**Sell signal এর জন্য:**
```json
{
  "secret": "your-secret-key-here",
  "action": "sell",
  "symbol": "BTCUSDT",
  "price": {{close}},
  "time": "{{time}}"
}
```

## 📊 How It Works

### Signal Flow

```
TradingView Alert
       ↓
Webhook POST Request
       ↓
tradingview_webhook_server.py
       ↓
WebhookSignalExecutor
       ↓
Risk Management
       ↓
Trade Execution (CCXT)
       ↓
Position Tracking
```

### Components

1. **Webhook Server** (`signals/tradingview_webhook_server.py`)
   - Webhook signals receive করে
   - Signal validation করে
   - Signal file এ store করে
   - Executor কে call করে

2. **Signal Executor** (`webhook_signal_executor.py`)
   - Buy/Sell/Close signals process করে
   - Risk manager দিয়ে position size calculate করে
   - CCXT executor দিয়ে trade execute করে
   - Open positions track করে

3. **Risk Manager** (`utils/configurable_risk.py`)
   - Position size calculate করে
   - Daily loss limits check করে
   - Max positions limit করে
   - Stop-loss/Take-profit set করে

## 🎯 Signal Format

### Required Fields
```json
{
  "secret": "your-secret-key",
  "action": "buy|sell|close",
  "symbol": "BTCUSDT"
}
```

### Optional Fields
```json
{
  "price": 95000,
  "quantity": 0.01,
  "exchange": "binance",
  "strategy": "My Strategy",
  "message": "Custom message",
  "stop_loss": 93100,
  "take_profit": 97500
}
```

## 🔐 Security

### Webhook Secret
TradingView alert এ `secret` field ব্যবহার করুন:

```json
{
  "secret": "{{strategy.order.action}}-{{time}}"
}
```

### Signature Verification
Production এ HMAC signature verification enable করুন।

## 📈 Example Execution Flow

### Buy Signal
```python
Signal: {
  "action": "buy",
  "symbol": "BTCUSDT",
  "price": 95000
}

Process:
1. Validate signal
2. Calculate position size (2% risk = $200 on $10k capital)
3. Set stop-loss at $93,100 (2% below entry)
4. Execute buy order
5. Track position

Result:
{
  "status": "success",
  "message": "Buy executed: BTCUSDT",
  "result": {...}
}
```

### Sell Signal
```python
Signal: {
  "action": "sell",
  "symbol": "BTCUSDT",
  "price": 97500
}

Process:
1. Find open position for BTCUSDT
2. Execute sell order for full quantity
3. Calculate P&L
4. Remove position tracking

Result:
{
  "status": "success",
  "message": "Sell executed: BTCUSDT",
  "pnl": 250.0,
  "result": {...}
}
```

## 🛠️ Testing

### Test Signal Manually

```bash
curl -X POST http://localhost:8000/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "your-secret-key-here",
    "action": "buy",
    "symbol": "BTCUSDT",
    "price": 95000,
    "time": "2025-01-01T12:00:00Z",
    "strategy": "Test Strategy"
  }'
```

### Check Positions

```python
from webhook_signal_executor import WebhookSignalExecutor
executor = WebhookSignalExecutor()
print(executor.get_positions())
```

## ⚠️ Important Notes

1. **Paper Trading:** Default এ paper trading mode এ execute হয়
2. **Risk Limits:** Daily loss limit reach হলে নতুন position open হবে না
3. **Position Limits:** Max positions limit reach হলে buy signals skip হবে
4. **Stop Loss:** Default 2% stop-loss automatically set হয়

## 📝 Logs

All signals এবং executions `logs/tv_signals.jsonl` file এ store হয়।

```bash
# View recent signals
tail -f logs/tv_signals.jsonl | jq .
```

## 🚨 Safety Features

- ✅ Secret key verification
- ✅ Automatic stop-loss placement
- ✅ Position size based on risk
- ✅ Daily loss limits
- ✅ Max positions limit
- ✅ Paper trading mode
- ✅ Comprehensive logging

## 📞 Support

Issues বা questions থাকলে check করুন:
- `executor/ccxt_executor.py` - Order execution
- `utils/configurable_risk.py` - Risk management
- `webhook_signal_executor.py` - Signal processing

---

**Enjoy automated trading! 🚀📊**

