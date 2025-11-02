#!/usr/bin/env python3
"""
Local TradingView Webhook Server - WITH AUTOMATIC TRADE EXECUTION
Receives alerts from TradingView and executes trades automatically

This server:
- Simple webhook endpoint
- File-based signal storage (JSONL)
- Automatic trade execution via CCXT executor

Use this for:
- Production trading with automatic execution
- Signal collection and execution
- Automated trading from TradingView alerts

Alternative servers:
- tradingview_webhook.py: Full-featured with execution
- server_realtime.py: Real-time Socket.IO broadcasting
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import executor
try:
    from webhook_signal_executor import WebhookSignalExecutor
    AUTO_EXECUTE = True
except ImportError:
    print("Warning: WebhookSignalExecutor not found. Auto-execution disabled.")
    AUTO_EXECUTE = False


load_dotenv()

APP_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))
SECRET = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "CHANGE_ME_SECRET")
STORE_PATH = Path(os.getenv("TRADINGVIEW_SIGNAL_STORE", "logs/tv_signals.jsonl"))
AUTO_EXECUTE_ENABLED = os.getenv("AUTO_EXECUTE_WEBHOOK", "false").lower() == "true"

STORE_PATH.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

# Initialize executor if auto-execution is enabled
executor = None
if AUTO_EXECUTE and AUTO_EXECUTE_ENABLED:
    try:
        executor = WebhookSignalExecutor()
        print("✅ Webhook auto-execution enabled")
    except Exception as e:
        print(f"❌ Failed to initialize executor: {e}")
        executor = None
else:
    print("ℹ️ Webhook auto-execution disabled")


def validate_payload(req) -> Tuple[bool, Dict[str, Any]]:
    try:
        data = req.get_json(force=True, silent=False)
    except Exception:
        return False, {}
    if not isinstance(data, dict):
        return False, {}
    if data.get("secret") != SECRET:
        return False, {}
    return True, data


@app.post("/webhook/tradingview")
def webhook_tradingview():
    ok, data = validate_payload(request)
    if not ok:
        return jsonify({"ok": False, "error": "unauthorized or invalid payload"}), 401

    # Attach receive timestamp if not provided
    data.setdefault("received_at", datetime.utcnow().isoformat())

    # Auto-execute trade if enabled
    exec_result = None
    if executor:
        try:
            exec_result = executor.process_signal(data)
            print(f"📊 Execution result: {exec_result.get('status')} - {exec_result.get('message')}")
        except Exception as e:
            print(f"❌ Execution error: {e}")
            exec_result = {'status': 'error', 'message': str(e)}

    # Persist one JSON per line for easy incremental reads
    with STORE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

    response = {"ok": True}
    if exec_result:
        response["execution"] = exec_result
    
    return jsonify(response)


if __name__ == "__main__":
    print("TradingView Webhook listening on http://{}:{}".format(APP_HOST, APP_PORT))
    print("POST alerts to: http://localhost:{}/webhook/tradingview".format(APP_PORT))
    app.run(host=APP_HOST, port=APP_PORT)


