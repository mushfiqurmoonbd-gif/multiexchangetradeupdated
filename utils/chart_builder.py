"""
Next-Gen Premium TradingView-Style Chart Builder
Professional multi-panel chart with advanced zooming, panning, and drag support
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_premium_chart(df: pd.DataFrame, symbol: str, show_volume: bool = False) -> go.Figure:
    """
    Create upgraded TradingView-style chart with professional UI and full zoom/pan support.
    """
    rows = 4 if show_volume else 3

    # Create professional subplot layout
    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.55, 0.2, 0.2] + ([0.12] if show_volume else []),
        subplot_titles=[
            f"{symbol} • Price Action",
            "WaveTrend Oscillator",
            "RSI / Stochastic",
        ] + (["Volume"] if show_volume else []),
    )

    # Candlestick chart (premium gradient colors)
    fig.add_trace(
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Price",
            increasing_line_color="#00FF88",
            decreasing_line_color="#FF4B5C",
            increasing_fillcolor="rgba(0,255,136,0.4)",
            decreasing_fillcolor="rgba(255,71,87,0.4)",
            line=dict(width=1),
        ),
        row=1,
        col=1,
    )

    # Add EMAs (20/50/200)
    for ema, color, name in zip(
        ["ema20", "ema50", "ema200"], ["#FFD700", "#00BFFF", "#FF6347"], ["EMA 20", "EMA 50", "EMA 200"]
    ):
        if ema in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["timestamp"],
                    y=df[ema],
                    name=name,
                    line=dict(color=color, width=1.8),
                    hovertemplate=f"{name}: $%{{y:.2f}}<extra></extra>",
                ),
                row=1,
                col=1,
            )

    # WaveTrend
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["wt1"],
            name="WT1",
            line=dict(color="#00FF88", width=2.2),
            hovertemplate="WT1: %{y:.2f}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["wt2"],
            name="WT2",
            fill="tonexty",
            fillcolor="rgba(155, 89, 182, 0.2)",
            line=dict(color="#9b59b6", width=2),
            hovertemplate="WT2: %{y:.2f}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    # WT levels
    for level, color in [(60, "#ff4757"), (-60, "#00ff88")]:
        fig.add_hline(y=level, line_dash="dot", line_color=color, opacity=0.6, row=2, col=1)

    # RSI and Stoch
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["rsi"],
            name="RSI",
            line=dict(color="#AB7FFF", width=2),
            fill="tozeroy",
            fillcolor="rgba(171,127,255,0.15)",
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["stoch"],
            name="Stochastic %K",
            line=dict(color="#FF9F43", width=1.8),
        ),
        row=3,
        col=1,
    )

    # RSI levels
    for level, color, style in [(70, "#ff4757", "dash"), (30, "#00ff88", "dash"), (50, "#a0aec0", "dot")]:
        fig.add_hline(y=level, line_dash=style, line_color=color, opacity=0.5, row=3, col=1)

    # Buy / Sell signals - Position correctly below/above candles
    if "signal" in df.columns or "final_buy" in df.columns:
        buy_col = "final_buy" if "final_buy" in df.columns else "signal"
        buys = df[df[buy_col] == True]
        if len(buys) > 0:
            fig.add_trace(
                go.Scatter(
                    x=buys["timestamp"],
                    y=buys["low"] * 0.995,  # BUY signals below candle (low - 0.5%)
                    mode="markers+text",
                    name="🟢 BUY",
                    marker=dict(symbol="triangle-up", size=20, color="#00ff88", line=dict(width=2, color="#fff")),
                    text=["BUY"] * len(buys),
                    textposition="top center",
                    textfont=dict(size=12, color="#00ff88", family="Arial Black"),
                    hovertemplate="<b>🟢 BUY Signal</b><br>Time: %{x}<br>Price: $%{y:.2f}<br>Entry: Low<extra></extra>",
                ),
                row=1,
                col=1,
            )
    if "sell_signal" in df.columns or "final_sell" in df.columns:
        sell_col = "final_sell" if "final_sell" in df.columns else "sell_signal"
        sells = df[df[sell_col] == True]
        if len(sells) > 0:
            fig.add_trace(
                go.Scatter(
                    x=sells["timestamp"],
                    y=sells["high"] * 1.005,  # SELL signals above candle (high + 0.5%)
                    mode="markers+text",
                    name="🔴 SELL",
                    marker=dict(symbol="triangle-down", size=20, color="#ff4757", line=dict(width=2, color="#fff")),
                    text=["SELL"] * len(sells),
                    textposition="bottom center",
                    textfont=dict(size=12, color="#ff4757", family="Arial Black"),
                    hovertemplate="<b>🔴 SELL Signal</b><br>Time: %{x}<br>Price: $%{y:.2f}<br>Exit: High<extra></extra>",
                ),
                row=1,
                col=1,
            )

    # Volume
    if show_volume and "volume" in df.columns:
        colors = ["#00ff88" if c >= o else "#ff4757" for c, o in zip(df["close"], df["open"])]
        fig.add_trace(
            go.Bar(
                x=df["timestamp"],
                y=df["volume"],
                marker_color=colors,
                name="Volume",
                opacity=0.8,
            ),
            row=4,
            col=1,
        )

    # === Layout ===
    fig.update_layout(
        template="plotly_dark",
        height=1000,
        margin=dict(l=50, r=40, t=90, b=60),
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(10, 10, 20, 0.8)",
            bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1,
            font=dict(size=10),
        ),
        hovermode="x unified",
        plot_bgcolor="rgba(8, 12, 24, 1)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=11, color="#ffffff"),
        transition_duration=300,
        dragmode="pan",  # Enables mouse drag in any direction
    )

    # === Axes Style ===
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
        showspikes=True,
        spikesnap="cursor",
        spikemode="across",
        spikecolor="rgba(255,255,255,0.3)",
        rangeslider_visible=False,
        zeroline=False,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
        zeroline=False,
        showspikes=True,
        spikesnap="cursor",
    )

    return fig


def get_chart_config() -> dict:
    """
    Enhanced Plotly chart config with full interactivity
    """
    return {
        "displaylogo": False,
        "responsive": True,
        "scrollZoom": True,
        "doubleClick": "reset+autosize",
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
        "modeBarButtonsToAdd": [
            "zoom2d",
            "pan2d",
            "drawline",
            "drawopenpath",
            "drawcircle",
            "drawrect",
            "eraseshape",
            "resetScale2d",
        ],
        "toImageButtonOptions": {
            "format": "png",
            "height": 900,
            "width": 1600,
            "scale": 2,
        },
    }
