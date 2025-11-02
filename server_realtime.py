#!/usr/bin/env python3
"""
Realtime server for TradingView alerts - SOCKET.IO VERSION

Endpoints:
- POST /webhook/tradingview  -> accept alerts (secret required)
- GET  /signals/recent       -> recent N alerts (optional filters)

Broadcasts Socket.IO event: "tv_signal"

This is a REAL-TIME server with WebSocket support:
- In-memory signal buffer
- Socket.IO broadcasting
- No file storage

Use this for:
- Real-time dashboard updates
- Live signal broadcasting
- Interactive frontends

Alternative servers:
- tradingview_webhook.py: Full-featured with execution
- tradingview_webhook_server.py: Simple file storage
"""

import os
import json
from collections import deque
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv


load_dotenv()

SECRET = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "CHANGE_ME_SECRET")
HOST = os.getenv("REALTIME_HOST", "0.0.0.0")
PORT = int(os.getenv("REALTIME_PORT", "8001"))

# In-memory ring buffer for most recent alerts
BUFFER_SIZE = int(os.getenv("REALTIME_BUFFER", "500"))
RECENT = deque(maxlen=BUFFER_SIZE)

app = Flask(__name__)
# Use threading async mode for wide Python compatibility (no eventlet/gevent needed)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


@app.post("/webhook/tradingview")
def webhook_tradingview():
    try:
        data: Dict[str, Any] = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "invalid_json"}), 400
    if not data or data.get("secret") != SECRET:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    # Normalize minimal fields
    data.setdefault("received_at", datetime.utcnow().isoformat())
    data.setdefault("strategy", "client_tv")
    # Append and broadcast
    RECENT.append(data)
    socketio.emit("tv_signal", data, broadcast=True)
    resp = jsonify({"ok": True})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.get("/signals/recent")
def signals_recent():
    symbol = request.args.get("symbol")
    exchange = request.args.get("exchange")
    limit = int(request.args.get("limit", "100"))

    def match(d: Dict[str, Any]) -> bool:
        ok = True
        if symbol:
            ok = ok and (d.get("symbol") == symbol or d.get("tv_symbol", "").endswith(symbol))
        if exchange:
            ok = ok and (str(d.get("exchange", "")).upper() == exchange.upper())
        return ok

    items = [x for x in list(RECENT)[-limit:] if match(x)]
    resp = jsonify({"ok": True, "items": items})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


if __name__ == "__main__":
    print(f"Realtime server listening on http://{HOST}:{PORT}")
    print("POST webhook: /webhook/tradingview | GET recent: /signals/recent")
    socketio.run(app, host=HOST, port=PORT)


