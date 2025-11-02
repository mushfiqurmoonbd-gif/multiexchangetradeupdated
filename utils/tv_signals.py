import json
from pathlib import Path
from typing import Optional, List

import pandas as pd
import requests

from .tv_mapper import to_yfinance_symbol


def load_tradingview_signals(store_path: str = "logs/tv_signals.jsonl", symbol: Optional[str] = None) -> pd.DataFrame:
    """
    Load TradingView signals that were stored by the webhook server.

    Returns a DataFrame with at least: timestamp, symbol, side, price.
    """
    p = Path(store_path)
    if not p.exists():
        return pd.DataFrame()

    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # Harmonize timestamp column
    ts_col = "time" if "time" in df.columns else ("received_at" if "received_at" in df.columns else None)
    if ts_col:
        df["timestamp"] = pd.to_datetime(df[ts_col])
    else:
        df["timestamp"] = pd.NaT

    if symbol is not None and "symbol" in df.columns:
        df = df[df["symbol"] == symbol]

    # Standardize key columns if present
    for col in ["symbol", "side", "price"]:
        if col not in df.columns:
            df[col] = None

    # Expand optional extra payload (e.g., rsi, wt1, wt2)
    df = _expand_extra(df)

    return df.sort_values("timestamp").reset_index(drop=True)


def fetch_recent_signals_http(base_url: str = "http://localhost:8001", symbol: Optional[str] = None, exchange: Optional[str] = None, limit: int = 200) -> pd.DataFrame:
    """Fetch recent signals from the realtime server if running."""
    try:
        params = {"limit": str(limit)}
        if symbol:
            params["symbol"] = symbol
        if exchange:
            params["exchange"] = exchange
        r = requests.get(f"{base_url}/signals/recent", params=params, timeout=1.5)
        if r.status_code != 200:
            return pd.DataFrame()
        items: List[dict] = r.json().get("items", [])
        if not items:
            return pd.DataFrame()
        df = pd.DataFrame(items)
        if 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['time'])
        elif 'received_at' in df.columns:
            df['timestamp'] = pd.to_datetime(df['received_at'])
        df = _expand_extra(df)
        return df.sort_values('timestamp').reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


def _expand_extra(df: pd.DataFrame) -> pd.DataFrame:
    """Extract fields from 'extra' JSON/dict into top-level columns if present."""
    if 'extra' not in df.columns:
        return df
    def _parse_extra(x):
        if isinstance(x, dict):
            return x
        try:
            return json.loads(x)
        except Exception:
            return {}
    extra = df['extra'].apply(_parse_extra)
    if not isinstance(extra, pd.Series):
        return df
    # Create columns if found
    for key in ['rsi', 'wt1', 'wt2']:
        try:
            df[key] = extra.apply(lambda d: d.get(key))
        except Exception:
            pass
    return df



