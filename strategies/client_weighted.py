"""
ClientWeightedStrategy - CLIENT-SPECIFIC WEIGHTED STRATEGY

This strategy implements a weighted signal system optimized for client requirements.

DEFAULT WEIGHTS:
- TradingView alerts: 40%
- RSI threshold: 40%
- WaveTrend crosses: 20%

Use this for:
- Strategy implementation with specific requirements
- Production trading with multiple signal sources
- Multi-timeframe signal aggregation

Related systems:
- indicators/weighted_signals.py: Generic weighted signals
- signals/trading_triggers.py: Priority-based hierarchy
- signals/engine.py: Multi-source alignment
"""

import pandas as pd
from typing import Optional

from strategies.base import Strategy
from indicators.rsi import rsi as rsi_calc
from indicators.wavetrend import wavetrend


class ClientWeightedStrategy(Strategy):
    """
    Client-weighted strategy combining:
    - 40% TradingView alert signal
    - 40% RSI threshold
    - 20% WaveTrend cross-up

    Inputs expected in df:
    - 'timestamp','open','high','low','close'
    Optional external columns:
    - 'tv_buy' (bool)  -> derived from TradingView alerts mapping
    - 'tv_sell' (bool) -> can be used for short logic if desired
    """

    name: str = "client_weighted"

    def generate_signals(
        self,
        df: pd.DataFrame,
        rsi_length: int = 14,
        rsi_buy_threshold: float = 53.0,
        rsi_sell_threshold: float = 47.0,
        wt_channel_length: int = 10,
        wt_average_length: int = 21,
        weight_tv: float = 0.40,
        weight_rsi: float = 0.40,
        weight_wt: float = 0.20,
        entry_threshold: float = 0.60,
        use_short: bool = False,
        # Optional multi-timeframe TV weights: dict of column->weight, e.g. {"tv_buy_5m":0.15, "tv_buy_15m":0.25}
        mtf_tv_weights: Optional[dict] = None,
    ) -> pd.Series:
        data = df.copy()

        # TradingView buy flag (0/1) — supports multi-timeframe aggregation if columns present
        tv_score = pd.Series(0.0, index=data.index)
        # primary single TF flag
        if 'tv_buy' in data.columns:
            tv_score = tv_score.add(data['tv_buy'].astype(float).fillna(0.0), fill_value=0.0)
        # optional multi-timeframe flags like tv_buy_5m, tv_buy_15m etc.
        if mtf_tv_weights:
            for col, w in mtf_tv_weights.items():
                if col in data.columns and w:
                    tv_score = tv_score.add(data[col].astype(float).fillna(0.0) * float(w), fill_value=0.0)
        data['tv_buy_flag'] = tv_score

        # RSI compute and map to 0/1 buy
        data['rsi_val'] = rsi_calc(data['close'], length=int(rsi_length))
        data['rsi_buy_flag'] = (data['rsi_val'] >= float(rsi_buy_threshold)).astype(float)

        # WaveTrend cross-up detection (green dot)
        if set(['high','low','close']).issubset(data.columns):
            wt_input = (data['high'] + data['low'] + data['close']) / 3.0
        else:
            wt_input = data['close']
        wt_df = wavetrend(wt_input, channel_length=int(wt_channel_length), average_length=int(wt_average_length))
        if isinstance(wt_df, pd.DataFrame):
            data['wt1'] = wt_df['wt1']
            data['wt2'] = wt_df['wt2']
        else:
            # Handle tuple/list
            data['wt1'], data['wt2'] = wt_df
        data['wt_buy_flag'] = ((data['wt1'].shift(1) <= data['wt2'].shift(1)) & (data['wt1'] > data['wt2'])).astype(float)

        # Weighted score for BUY
        data['score_buy'] = (
            weight_tv * data['tv_buy_flag'] +
            weight_rsi * data['rsi_buy_flag'] +
            weight_wt * data['wt_buy_flag']
        )

        data['final_buy'] = data['score_buy'] >= float(entry_threshold)

        # For compatibility: return a boolean 'signal' series (buy-only)
        signal = data['final_buy'].fillna(False).astype(bool)
        signal.name = 'signal'
        return signal


