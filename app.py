import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import time
import os
import sys
import types
import json
from datetime import datetime, timedelta
from indicators.rsi import rsi
from indicators.stoch import stochastic
from indicators.parabolic_sar import parabolic_sar
from utils.chart_builder import create_premium_chart, get_chart_config

def display_account_balance(paper_mode: bool, real_account_data: dict = None):
    """
    Consolidated function to display account balance information
    Always shows balance - paper or real based on mode
    """
    if not paper_mode and real_account_data and real_account_data.get('balance'):
        # Real account data
        real_balance = real_account_data['balance']
        usdt_balance = real_balance.get('USDT', {})
        real_cash = usdt_balance.get('free', 0)
        real_total = usdt_balance.get('total', 0)
        real_used = usdt_balance.get('used', 0)
        
        return f"""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); margin: 1rem 0;">
            <div style="text-align: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: var(--text-primary); display: flex; align-items: center; 
                           justify-content: center; gap: 0.5rem;">
                    💰 Real Account Balance
                </h4>
            </div>
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 2rem; font-weight: 700; color: var(--accent-green);">
                    ${real_cash:,.2f}
                </div>
                <div style="font-size: 0.9rem; color: var(--text-secondary);">Total Balance</div>
            </div>
            <div style="display: grid; gap: 0.5rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Available:</span>
                    <span style="color: var(--accent-green); font-weight: 600;">${real_cash:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">In Orders:</span>
                    <span style="color: var(--accent-blue); font-weight: 600;">${real_used:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Total:</span>
                    <span style="color: var(--text-primary); font-weight: 600;">${real_total:,.2f}</span>
                </div>
            </div>
        </div>
        """
    elif not paper_mode:
        # Real trading mode but no account data yet
        return f"""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); margin: 1rem 0;">
            <div style="text-align: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: var(--text-primary); display: flex; align-items: center; 
                           justify-content: center; gap: 0.5rem;">
                    💰 Real Account Balance
                </h4>
            </div>
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 1.5rem; font-weight: 700; color: var(--text-secondary);">
                    Loading...
                </div>
                <div style="font-size: 0.9rem; color: var(--text-secondary);">Connecting to exchange</div>
            </div>
            <div style="text-align: center;">
                <div style="color: var(--text-secondary); font-size: 0.8rem;">
                    Balance will appear automatically when connected
                </div>
            </div>
        </div>
        """
    else:
        # Paper trading mode
        account = st.session_state.get('account', {'cash': 10000, 'equity': [10000]})
        paper_cash = account.get('cash', 10000)
        paper_equity = account.get('equity', [10000])[-1] if account.get('equity') else 10000
        
        return f"""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); margin: 1rem 0;">
            <div style="text-align: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: var(--text-primary); display: flex; align-items: center; 
                           justify-content: center; gap: 0.5rem;">
                    📊 Paper Account Balance
                </h4>
            </div>
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 2rem; font-weight: 700; color: var(--accent-blue);">
                    ${paper_equity:,.2f}
                </div>
                <div style="font-size: 0.9rem; color: var(--text-secondary);">Paper Trading Balance</div>
            </div>
            <div style="display: grid; gap: 0.5rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Available Cash:</span>
                    <span style="color: var(--accent-blue); font-weight: 600;">${paper_cash:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Total Equity:</span>
                    <span style="color: var(--text-primary); font-weight: 600;">${paper_equity:,.2f}</span>
                </div>
            </div>
        </div>
        """
from indicators.wavetrend import wavetrend
from signals.engine import align_signals
from backtester.core import run_backtest
from utils.logger import log_trade, log_pnl
from utils.error_handler import error_handler, safe_execute, TradingError, APIError
from executor.ccxt_executor import CCXTExecutor
from strategies.manager import StrategyManager
from utils.risk import position_size_from_risk
from arbitrage.engine import ArbitrageEngine
from utils.configurable_risk import ConfigurableRiskManager, StopLossType
from backtester.enhanced_backtester import EnhancedBacktester
from backtester.comprehensive_metrics import ComprehensiveMetricsCalculator
from backtester.multi_timeframe_analyzer import MultiTimeframeAnalyzer
from signals.trading_triggers import TradingTriggerEngine
from indicators.weighted_signals import WeightedSignalGenerator
from utils.tv_signals import load_tradingview_signals, fetch_recent_signals_http
from utils.tv_mapper import to_yfinance_symbol

# Ensure yfinance uses standard requests (avoid curl_cffi impersonate)
os.environ.setdefault("YFINANCE_DISABLE_CURL_CFFI", "1")
try:
    import requests as _pyrequests
    _shim = types.ModuleType('curl_cffi')
    _shim.requests = _pyrequests
    sys.modules['curl_cffi'] = _shim
except Exception:
    pass
import yfinance as yf
from streamlit.components.v1 import html

st.set_page_config(
    page_title="Multi-Exchange Trading Platform", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈"
)

# Enhanced CSS styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root Variables */
    :root {
        --primary-bg: #0a0e1a;
        --secondary-bg: #1a1f2e;
        --card-bg: #252b3d;
        --border-color: #2d3748;
        --text-primary: #ffffff;
        --text-secondary: #a0aec0;
        --accent-green: #48bb78;
        --accent-red: #f56565;
        --accent-blue: #4299e1;
        --accent-purple: #9f7aea;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --border-radius: 12px;
        --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Global Styles */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background-color: var(--primary-bg);
        border-right: 1px solid var(--border-color);
    }
    
    /* Custom Sidebar Header */
    .sidebar-header {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
        padding: 1.5rem;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 var(--border-radius) var(--border-radius);
        text-align: center;
    }
    
    .sidebar-header h1 {
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .sidebar-header .subtitle {
        color: rgba(255,255,255,0.8);
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
    
    /* Section Headers */
    .section-header {
        background: var(--card-bg);
        padding: 0.75rem 1rem;
        margin: 1rem -1rem 1rem -1rem;
        border-left: 4px solid var(--accent-blue);
        border-radius: 0 var(--border-radius) var(--border-radius) 0;
        font-weight: 600;
        color: var(--text-primary);
        font-size: 0.95rem;
    }
    
    /* Control Groups */
    .control-group {
        background: var(--secondary-bg);
        padding: 1rem;
        border-radius: var(--border-radius);
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
    }
    
    /* Status Indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-trading {
        background: rgba(72, 187, 120, 0.1);
        color: var(--accent-green);
        border: 1px solid var(--accent-green);
    }
    
    .status-stopped {
        background: rgba(245, 101, 101, 0.1);
        color: var(--accent-red);
        border: 1px solid var(--accent-red);
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
    }
    
    /* Action Buttons */
    .action-button {
        width: 100%;
        padding: 0.75rem;
        border-radius: var(--border-radius);
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, var(--accent-green), #38a169);
        color: white;
    }
    
    .btn-primary:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    .btn-danger {
        background: linear-gradient(135deg, var(--accent-red), #e53e3e);
        color: white;
    }
    
    .btn-danger:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    /* Metric Cards */
    .metric-card {
        background: var(--card-bg);
        padding: 1rem;
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Strategy Tab Styles */
    .strategy-card {
        background: var(--secondary-bg);
        padding: 1.5rem;
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }
    
    .strategy-header {
        color: var(--text-primary);
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .conditions-list {
        background: var(--card-bg);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid var(--accent-blue);
    }
    
    .conditions-list h4 {
        color: var(--accent-blue);
        margin: 0 0 0.5rem 0;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .conditions-list ul {
        margin: 0;
        padding-left: 1.2rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    .conditions-list li {
        margin-bottom: 0.25rem;
    }
    
    .status-box {
        background: var(--card-bg);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid var(--border-color);
    }
    
    .status-text {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .status-details {
        font-size: 0.85rem;
        color: var(--text-secondary);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    # Header Section
    st.markdown("""
    <div class="sidebar-header">
        <h1>🚀 Trading Platform</h1>
        <div class="subtitle">Multi-Exchange Trading Dashboard</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Trading Status
    if 'is_trading' not in st.session_state:
        st.session_state['is_trading'] = False
    
    status_class = "status-trading" if st.session_state['is_trading'] else "status-stopped"
    if st.session_state['is_trading']:
        # Get paper mode from session state or default to True
        paper_mode = st.session_state.get('paper_mode', True)
        status_text = "📝 PAPER TRADING" if paper_mode else "🚀 LIVE TRADING"
    else:
        status_text = "STOPPED"
    status_dot = "status-dot"
    
    st.markdown(f"""
    <div class="status-indicator {status_class}">
        <div class="{status_dot}"></div>
        {status_text}
    </div>
    """, unsafe_allow_html=True)
    
    # Exchange Configuration
    st.markdown('<div class="section-header">🔗 Exchange Setup</div>', unsafe_allow_html=True)
    
    with st.container():
        ex_name = st.selectbox(
            "Select Exchange", 
            ["binance", "bybit", "mexc", "alpaca", "coinbase", "kraken"], 
            index=0,
            help="Choose your preferred exchange (crypto or stocks)",
            key="exchange_selector"
        )
        # Store in session state for backtester
        st.session_state['selected_exchange'] = ex_name
        
        # Enhanced Backtest Controls
        st.markdown('<div class="section-header">🧪 Enhanced Backtest</div>', unsafe_allow_html=True)
        
        # Initialize enhanced backtester
        enhanced_bt = EnhancedBacktester()
        
        # Ticker Selection
        ticker_category = st.selectbox(
            "📈 Asset Category",
            ["Crypto", "Stocks", "Forex"],
            index=0,
            help="Select the asset category for backtesting"
        )
        
        available_tickers = enhanced_bt.get_supported_tickers()[ticker_category]
        selected_ticker = st.selectbox(
            "🎯 Select Ticker",
            available_tickers,
            index=0,
            help=f"Choose from available {ticker_category} tickers"
        )
        
        # Timeframe Selection
        available_timeframes = enhanced_bt.get_supported_timeframes()
        selected_timeframe = st.selectbox(
            "⏰ Timeframe",
            available_timeframes,
            index=available_timeframes.index('1h') if '1h' in available_timeframes else 0,
            help="Select the timeframe for backtesting"
        )
        
        # RSI Thresholds (Adjustable)
        st.markdown("**🎛️ RSI Thresholds**")
        col_rsi1, col_rsi2 = st.columns(2)
        with col_rsi1:
            rsi_buy_threshold = st.number_input(
                "RSI Buy Threshold",
                min_value=50.0, max_value=60.0, value=53.0, step=0.5,
                help="RSI above this value triggers buy signal"
            )
        with col_rsi2:
            rsi_sell_threshold = st.number_input(
                "RSI Sell Threshold", 
                min_value=40.0, max_value=50.0, value=47.0, step=0.5,
                help="RSI below this value triggers sell signal"
            )
        
        # Date Range
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=90),
                help="Backtest start date"
            )
        with col_date2:
            end_date = st.date_input(
                "End Date", 
                value=datetime.now(),
                help="Backtest end date"
            )
        
        # Run Enhanced Backtest
        run_enhanced_bt = st.button("🚀 Run Enhanced Backtest", key="run_enhanced_backtest_btn")
        st.session_state.setdefault('enhanced_backtest_trigger', False)
        if run_enhanced_bt:
            st.session_state['enhanced_backtest_trigger'] = True
            st.session_state['enhanced_backtest_params'] = {
                'ticker': selected_ticker,
                'timeframe': selected_timeframe,
                'start_date': start_date,
                'end_date': end_date,
                'rsi_buy_threshold': rsi_buy_threshold,
                'rsi_sell_threshold': rsi_sell_threshold
            }

        # Signal Test
        st.markdown('<div class="section-header">🔎 Signal Test</div>', unsafe_allow_html=True)
        test_sig = st.button("🧪 Test Signals (Buy/Sell)", key="test_signals_btn")
        st.session_state.setdefault('signal_test_trigger', False)
        if test_sig:
            st.session_state['signal_test_trigger'] = True
        
        # Trading Mode Selection
        trading_mode = st.radio(
            "🎯 Trading Mode",
            ["📝 Paper Trading (Practice)", "🚀 Real Trading (Live)"],
            index=0,
            help="Choose between paper trading for practice or real trading with live orders"
        )
        
        paper = "Paper" in trading_mode
        st.session_state['paper_mode'] = paper
        
        # Mode-specific warnings
        if paper:
            st.markdown("""
            <div style="background: var(--accent-blue); color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600;">
                📝 PAPER TRADING MODE - Safe Practice Environment
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: var(--accent-green); color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600;">
                🚀 REAL TRADING MODE - Live Trading Enabled
            </div>
            """, unsafe_allow_html=True)
        
        dark_theme = st.checkbox(
            "🌙 Dark Theme", 
            value=True,
            help="Toggle between light and dark themes"
        )
    
    # Market Configuration
    st.markdown('<div class="section-header">📊 Market Settings</div>', unsafe_allow_html=True)
    
    with st.container():
        # Load API from .env when live trading
        ex_upper = ex_name.upper()
        api_key = os.getenv(f"{ex_upper}_API_KEY") if not paper else None
        api_secret = os.getenv(f"{ex_upper}_API_SECRET") if not paper else None
        
        # Special handling for Coinbase (requires passphrase)
        if ex_name.lower() == 'coinbase' and not paper:
            passphrase = os.getenv(f"{ex_upper}_PASSPHRASE")
            if api_key and api_secret and passphrase:
                # For Coinbase, we need to pass the passphrase as well
                _exec = CCXTExecutor(ex_name, api_key, api_secret, paper=paper)
                # Set the passphrase in the exchange options
                if hasattr(_exec.ex, 'options'):
                    _exec.ex.options['passphrase'] = passphrase
            else:
                _exec = CCXTExecutor(ex_name, api_key, api_secret, paper=paper)
        else:
            _exec = CCXTExecutor(ex_name, api_key, api_secret, paper=paper)
        
        # Set appropriate quote currency based on exchange
        if ex_name.lower() in ['alpaca']:
            # US stock exchanges use USD
            quote_currency = "USD"
            popular_pairs = [
                "BTCUSD", "ETHUSD", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
                "NVDA", "META", "NFLX", "AMD", "INTC", "CRM", "ADBE", "PYPL"
            ]
        elif ex_name.lower() in ['coinbase', 'kraken']:
            # US crypto exchanges use USD
            quote_currency = "USD"
            popular_pairs = [
                "BTC-USD", "ETH-USD", "LTC-USD", "BCH-USD", "ETC-USD",
                "XRP-USD", "ADA-USD", "DOT-USD", "LINK-USD", "UNI-USD"
            ]
        else:
            # International crypto exchanges use USDT
            quote_currency = "USDT"
        popular_pairs = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", 
            "XRPUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT",
            "LINKUSDT", "UNIUSDT", "LTCUSDT", "ATOMUSDT", "FTMUSDT"
        ]
        
        symbols = _exec.list_symbols(quote_currency)
        timeframes = _exec.list_timeframes()
        
        # Filter available symbols and prioritize popular pairs
        if symbols:
            # Convert symbols to uppercase for comparison
            symbols_upper = [s.upper() for s in symbols]
            available_popular = [pair for pair in popular_pairs if pair in symbols_upper]
            other_symbols = [s for s in symbols if s.upper() not in popular_pairs]
            ordered_symbols = available_popular + other_symbols
        else:
            ordered_symbols = popular_pairs
        
        # Find index of default symbol based on exchange
        default_index = 0
        if ex_name.lower() in ['alpaca']:
            # Default to BTCUSD for US stock exchanges
            if "BTCUSD" in ordered_symbols:
                default_index = ordered_symbols.index("BTCUSD")
            elif "BTC/USD" in ordered_symbols:
                default_index = ordered_symbols.index("BTC/USD")
        elif ex_name.lower() in ['coinbase', 'kraken']:
            # Default to BTC-USD for US crypto exchanges
            if "BTC-USD" in ordered_symbols:
                default_index = ordered_symbols.index("BTC-USD")
            elif "BTC/USD" in ordered_symbols:
                default_index = ordered_symbols.index("BTC/USD")
        else:
            # Default to BTCUSDT for international crypto exchanges
            if "BTCUSDT" in ordered_symbols:
                default_index = ordered_symbols.index("BTCUSDT")
            elif "BTC/USDT" in ordered_symbols:
                default_index = ordered_symbols.index("BTC/USDT")
        
        symbol = st.selectbox(
            "Trading Pair", 
            options=ordered_symbols, 
            index=default_index,
            help="Select the cryptocurrency pair to trade (popular pairs shown first)"
        )
        
        timeframe = st.selectbox(
            "Timeframe", 
            options=timeframes, 
            index=timeframes.index("1h") if "1h" in timeframes else 0,
            help="Choose the chart timeframe for analysis"
        )
        
        refresh_secs = st.slider(
            "🔄 Refresh Rate (seconds)", 
            min_value=5, 
            max_value=300, 
            value=30, 
            step=5,
            help="How often to refresh market data"
        )
        
        # Automatic periodic refresh using session timestamp
        # Rerun the app when the chosen refresh interval has elapsed
        now_ts = time.time()
        last_ts = st.session_state.get('last_auto_refresh_ts', 0.0)
        last_interval = st.session_state.get('last_auto_refresh_interval', refresh_secs)
        # If the interval changed, force a new schedule
        if last_interval != refresh_secs:
            st.session_state['last_auto_refresh_interval'] = refresh_secs
            st.session_state['last_auto_refresh_ts'] = now_ts
        elif now_ts - last_ts >= float(refresh_secs):
            st.session_state['last_auto_refresh_ts'] = now_ts
            st.rerun()
    
    # Strategy Configuration
    st.markdown('<div class="section-header">🎯 Strategy Configuration</div>', unsafe_allow_html=True)
    
    with st.container():
        strat_choice = st.selectbox(
            "Strategy Type", 
            ["auto", "ema_crossover", "rsi_bbands", "grid", "client_weighted"], 
            index=0,
            help="Select your trading strategy"
        )
        position_mode = st.radio(
            "Position Mode",
            options=["Long only", "Long + Short"],
            index=0,
            horizontal=True,
            help="Choose whether to allow short (sell) entries"
        )
        
        # Strategy-specific parameters
        if strat_choice in ["auto", "rsi_bbands", "client_weighted"]:
            rsi_length = st.number_input(
                "RSI Length", 
                min_value=5, 
                max_value=50, 
                value=14,
                help="Period for RSI calculation"
            )
            rsi_oversold = st.number_input(
                "RSI Oversold Level", 
                min_value=10, 
                max_value=50, 
                value=30,
                help="RSI level considered oversold"
            )
            rsi_overbought = st.number_input(
                "RSI Overbought Level", 
                min_value=50, 
                max_value=90, 
                value=70,
                help="RSI level considered overbought"
            )
        else:
            # Set default values for other strategies
            rsi_length = 14
            rsi_oversold = 30
            rsi_overbought = 70
        
        if strat_choice in ["auto", "client_weighted"]:
            wt_channel = st.number_input(
                "WaveTrend Channel", 
                min_value=5, 
                max_value=50, 
                value=10,
                help="Channel length for WaveTrend indicator"
            )
            wt_avg = st.number_input(
                "WaveTrend Average", 
                min_value=5, 
                max_value=50, 
                value=21,
                help="Average length for WaveTrend indicator"
            )
        else:
            # Set default values for other strategies
            wt_channel = 10
            wt_avg = 21

        if strat_choice == "client_weighted":
            entry_threshold = st.slider(
                "Entry Threshold (weighted score)", 
                min_value=0.0, max_value=1.0, value=0.60, step=0.05,
                help="Score ≥ threshold triggers BUY"
            )
            st.markdown("**Multi‑Timeframe TV Weights**")
            mtf_choices = ["5m", "15m", "1h", "4h", "1d"]
            selected_tfs_client = st.multiselect(
                "Select timeframes to weight",
                mtf_choices,
                default=["5m", "15m", "1h"],
                help="TradingView alerts from these timeframes will influence entries"
            )
            mtf_weight_inputs = {}
            cols = st.columns(min(3, len(selected_tfs_client)) or 1)
            for i, tf_sel in enumerate(selected_tfs_client):
                with cols[i % len(cols)]:
                    mtf_weight_inputs[tf_sel] = st.slider(
                        f"Weight {tf_sel}", min_value=0.0, max_value=1.0,
                        value=0.35 if tf_sel=="1h" else (0.25 if tf_sel=="15m" else (0.15 if tf_sel=="5m" else 0.10)),
                        step=0.05
                    )

            # Persist/Load settings controls
            from pathlib import Path
            settings_path = Path("logs/client_weighted_settings.json")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Save Settings", key="save_cw_settings"):
                    settings_path.parent.mkdir(parents=True, exist_ok=True)
                    import json
                    with settings_path.open("w", encoding="utf-8") as f:
                        json.dump({
                            "entry_threshold": float(entry_threshold),
                            "selected_tfs": selected_tfs_client,
                            "weights": mtf_weight_inputs,
                        }, f)
                    st.success("Settings saved")
            with c2:
                if st.button("📥 Load Settings", key="load_cw_settings") and settings_path.exists():
                    import json
                    try:
                        data = json.loads(settings_path.read_text(encoding="utf-8"))
                        entry_threshold = float(data.get("entry_threshold", entry_threshold))
                        selected_tfs_client = data.get("selected_tfs", selected_tfs_client)
                        mtf_weight_inputs = {k: float(v) for k, v in (data.get("weights", mtf_weight_inputs)).items()}
                        st.session_state["cw_loaded_threshold"] = entry_threshold
                        st.session_state["cw_loaded_tfs"] = selected_tfs_client
                        st.session_state["cw_loaded_weights"] = mtf_weight_inputs
                        st.success("Settings loaded")
                    except Exception as e:
                        st.error(f"Load failed: {e}")
    
    # Multi-Timeframe Analysis Configuration
    st.markdown('<div class="section-header">📊 Multi-Timeframe Analysis</div>', unsafe_allow_html=True)
    
    with st.expander("🔄 Multi-Timeframe Settings", expanded=False):
        enable_mtf = st.checkbox(
            "Enable Multi-Timeframe Analysis",
            value=False,
            help="Analyze multiple timeframes for stronger signals"
        )
        
        if enable_mtf:
            primary_tf = st.selectbox(
                "Primary Timeframe",
                ["15m", "30m", "1H", "4H", "1D"],
                index=2,
                help="Primary timeframe for analysis"
            )
            
            secondary_tfs = st.multiselect(
                "Secondary Timeframes",
                ["15m", "30m", "1H", "4H", "1D", "1W"],
                default=["15m", "4H", "1D"],
                help="Additional timeframes to analyze"
            )
            
            mtf_min_confidence = st.slider(
                "Minimum Confidence",
                min_value=0.3,
                max_value=1.0,
                value=0.6,
                step=0.1,
                help="Minimum confidence threshold for signals"
            )
            
            # Initialize multi-timeframe analyzer
            mtf_analyzer = MultiTimeframeAnalyzer()
            
            mtf_min_strength = st.selectbox(
                "Minimum Strength",
                ["weak", "moderate", "strong"],
                index=1,
                help="Minimum signal strength required"
            )
            
            # Timeframe weights
            st.markdown("**Timeframe Weights**")
            tf_weights = {}
            for tf in secondary_tfs:
                tf_weights[tf] = st.slider(
                    f"Weight for {tf}",
                    min_value=0.1,
                    max_value=1.0,
                    value=0.5 if tf in ["1H", "4H"] else 0.3,
                    step=0.1,
                    help=f"Weight for {tf} timeframe"
                )
        else:
            primary_tf = "1H"
            secondary_tfs = []
            mtf_min_confidence = 0.6
            mtf_min_strength = "moderate"
            tf_weights = {}
    
    # Risk Management
    st.markdown('<div class="section-header">⚠️ Risk Management</div>', unsafe_allow_html=True)
    
    with st.container():
        initial_cap = st.number_input(
            "💰 Initial Capital ($)", 
            min_value=100.0, 
            max_value=1000000.0, 
            value=10000.0,
            help="Starting capital for trading"
        )
        
        if 'initial_capital' not in st.session_state:
            st.session_state['initial_capital'] = initial_cap
        
        risk_per_trade = st.slider(
            "Risk per Trade (%)", 
            min_value=0.005, 
            max_value=0.10, 
            value=0.02, 
            step=0.005,
            help="Percentage of capital to risk per trade"
        )
        
    # Advanced Risk Management Configuration
    st.markdown('<div class="section-header">⚙️ Advanced Risk Management</div>', unsafe_allow_html=True)
    
    with st.expander("🔧 Configurable Stop-Loss Settings", expanded=False):
        stop_loss_type = st.selectbox(
            "Stop Loss Type",
            ["percentage", "atr", "support_resistance", "volatility"],
            index=0,
            help="Choose stop loss calculation method"
        )
        
        if stop_loss_type == "percentage":
            stop_loss_value = st.slider(
                "Stop Loss Percentage",
                min_value=0.5,
                max_value=10.0,
                value=2.0,
                step=0.1,
                format="%.1f%%",
                help="Stop loss as percentage of entry price"
            ) / 100
        elif stop_loss_type == "atr":
            stop_loss_value = st.slider(
                "ATR Multiplier",
                min_value=0.5,
                max_value=5.0,
                value=2.0,
                step=0.1,
                help="ATR multiplier for stop loss distance"
            )
        elif stop_loss_type == "support_resistance":
            stop_loss_value = st.slider(
                "Support/Resistance Distance",
                min_value=1.0,
                max_value=5.0,
                value=2.0,
                step=0.1,
                format="%.1f%%",
                help="Distance from support/resistance levels"
            ) / 100
        else:  # volatility
            stop_loss_value = st.slider(
                "Volatility Multiplier",
                min_value=1.0,
                max_value=3.0,
                value=2.0,
                step=0.1,
                help="Volatility multiplier for stop loss"
            )
        
        # TP1/TP2/Runner Configuration
        st.markdown("**Take Profit Configuration**")
        tp1_multiplier = st.slider(
            "TP1 Multiplier",
            min_value=1.0,
            max_value=3.0,
            value=1.5,
            step=0.1,
            help="TP1 as multiple of risk"
        )
        
        tp2_multiplier = st.slider(
            "TP2 Multiplier", 
            min_value=2.0,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="TP2 as multiple of risk"
        )
        
        runner_multiplier = st.slider(
            "Runner Multiplier",
            min_value=3.0,
            max_value=10.0,
            value=3.0,
            step=0.1,
            help="Runner activation as multiple of risk"
        )
        
        # Daily Breaker
        daily_breaker_active = st.checkbox(
            "Enable Daily Breaker",
            value=False,
            help="Stop trading after daily loss limit"
        )
        
        if daily_breaker_active:
            daily_loss_limit = st.slider(
                "Daily Loss Limit",
                min_value=1.0,
                max_value=10.0,
                value=5.0,
                step=0.5,
                format="%.1f%%",
                help="Maximum daily loss as percentage of capital"
            ) / 100
        else:
            daily_loss_limit = 0.05
        
        # Additional Risk Parameters
        st.markdown("**Additional Risk Parameters**")
        max_bars_in_trade = st.number_input(
            "Max Bars in Trade", 
            min_value=1, 
            max_value=10000, 
            value=100,
            help="Maximum number of bars to hold a position"
        )
        
        # Legacy parameters for backward compatibility
        stop_loss_pct = stop_loss_value if stop_loss_type == "percentage" else 0.03
        take_profit_pct = tp1_multiplier * stop_loss_pct if stop_loss_type == "percentage" else 0.06
    
    # Initialize session state
    if 'account' not in st.session_state:
        st.session_state['account'] = {'cash': float(initial_cap), 'equity': [float(initial_cap)]}
    if 'position' not in st.session_state:
        st.session_state['position'] = None
    if 'trades' not in st.session_state:
        st.session_state['trades'] = []
    if 'arb_running' not in st.session_state:
        st.session_state['arb_running'] = False
    if 'real_account_data' not in st.session_state:
        st.session_state['real_account_data'] = None
    if 'account_validation' not in st.session_state:
        st.session_state['account_validation'] = None
    
    # Real Account Data Fetching and Validation
    if not paper and api_key and api_secret:
        st.markdown('<div class="section-header">🔐 Account Validation</div>', unsafe_allow_html=True)
        
        # Validate account access
        if st.button("🔍 Validate Account Access", key="validate_account"):
            with st.spinner("Validating account access..."):
                try:
                    validation_result = _exec.validate_account()
                    st.session_state['account_validation'] = validation_result
                    
                    if validation_result['valid']:
                        st.success("✅ Account validation successful!")
                        st.info(f"Balance access: {'✅' if validation_result['balance_available'] else '❌'} | Market data: {'✅' if validation_result['market_data_available'] else '❌'}")
                    else:
                        error_msg = error_handler.get_user_friendly_message(Exception(validation_result['message']))
                        st.error(error_msg)
                        
                        # Show suggestions if available
                        suggestions = error_handler.get_error_suggestions(Exception(validation_result['message']))
                        if suggestions:
                            st.markdown("**💡 Suggestions:**")
                            for suggestion in suggestions:
                                st.markdown(f"• {suggestion}")
                except Exception as e:
                    error_msg = error_handler.get_user_friendly_message(e)
                    st.error(error_msg)
                    
                    # Show suggestions
                    suggestions = error_handler.get_error_suggestions(e)
                    if suggestions:
                        st.markdown("**💡 Suggestions:**")
                        for suggestion in suggestions:
                            st.markdown(f"• {suggestion}")
        
        # Display validation results
        if st.session_state['account_validation']:
            validation = st.session_state['account_validation']
            if validation['valid']:
                st.markdown("""
                <div style="background: var(--accent-green); color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600;">
                    ✅ ACCOUNT VALIDATED - Ready for Real Trading
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: var(--accent-red); color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600;">
                    ❌ ACCOUNT VALIDATION FAILED - {validation['message']}
                </div>
                """, unsafe_allow_html=True)
        
        # Fetch real account data
        if st.button("📊 Fetch Real Account Data", key="fetch_account_data"):
            with st.spinner("Fetching real account data..."):
                try:
                    account_data = _exec.get_account_info()
                    st.session_state['real_account_data'] = account_data
                    st.success("✅ Real account data fetched successfully!")
                except Exception as e:
                    error_msg = error_handler.get_user_friendly_message(e)
                    st.error(error_msg)
                    
                    # Show suggestions
                    suggestions = error_handler.get_error_suggestions(e)
                    if suggestions:
                        st.markdown("**💡 Suggestions:**")
                        for suggestion in suggestions:
                            st.markdown(f"• {suggestion}")
        
        # Always show balance - automatic display
        st.markdown(display_account_balance(paper, st.session_state.get('real_account_data')), unsafe_allow_html=True)
        
        # Display real account data
        if st.session_state['real_account_data']:
            real_data = st.session_state['real_account_data']
            
            # Real Positions Display
            if real_data.get('positions'):
                positions = real_data['positions']
                if positions:
                    st.markdown(f"""
                    <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin: 1rem 0;">
                        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">📈 Real Positions ({len(positions)})</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for pos in positions[:5]:  # Show first 5 positions
                        symbol = pos.get('symbol', 'Unknown')
                        size = pos.get('size', 0)
                        side = pos.get('side', 'Unknown')
                        unrealized_pnl = pos.get('unrealizedPnl', 0)
                        pnl_color = "var(--accent-green)" if float(unrealized_pnl) >= 0 else "var(--accent-red)"
                        
                        st.markdown(f"""
                        <div style="background: var(--secondary-bg); padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0; border-left: 4px solid {pnl_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: var(--text-primary); font-weight: 600;">{symbol}</span>
                                <span style="color: {pnl_color}; font-weight: 600;">${float(unrealized_pnl):,.2f}</span>
                            </div>
                            <div style="color: var(--text-secondary); font-size: 0.9rem;">
                                {side} • Size: {size}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin: 1rem 0; text-align: center;">
                        <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">📈 Real Positions</h4>
                        <p style="color: var(--text-secondary); margin: 0;">No open positions</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Real Orders Display
            if real_data.get('orders'):
                orders = real_data['orders']
                if orders:
                    st.markdown(f"""
                    <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin: 1rem 0;">
                        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">📋 Real Orders ({len(orders)})</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for order in orders[:5]:  # Show first 5 orders
                        order_id = order.get('orderId', 'Unknown')
                        symbol = order.get('symbol', 'Unknown')
                        side = order.get('side', 'Unknown')
                        qty = order.get('qty', 0)
                        status = order.get('orderStatus', 'Unknown')
                        
                        st.markdown(f"""
                        <div style="background: var(--secondary-bg); padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: var(--text-primary); font-weight: 600;">{symbol}</span>
                                <span style="color: var(--text-secondary); font-size: 0.9rem;">{status}</span>
                            </div>
                            <div style="color: var(--text-secondary); font-size: 0.9rem;">
                                {side} • Qty: {qty} • ID: {order_id[:8]}...
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); margin: 1rem 0; text-align: center;">
                        <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">📋 Real Orders</h4>
                        <p style="color: var(--text-secondary); margin: 0;">No open orders</p>
                    </div>
                    """, unsafe_allow_html=True)

    # Trading Controls
    st.markdown('<div class="section-header">🎮 Trading Controls</div>', unsafe_allow_html=True)
    
    # Mode-specific warnings and controls
    if paper:
        st.markdown("""
        <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 2px solid var(--accent-blue); margin: 1rem 0;">
            <h4 style="color: var(--accent-blue); margin: 0 0 0.5rem 0;">📝 PAPER TRADING MODE</h4>
            <p style="color: var(--text-secondary); margin: 0; font-size: 0.9rem;">
                Safe practice environment - No real money at risk:
                <br>• Simulated orders and positions
                <br>• Real market data for realistic testing
                <br>• Perfect for strategy development
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; border: 2px solid var(--accent-green); margin: 1rem 0;">
            <h4 style="color: var(--accent-green); margin: 0 0 0.5rem 0;">🚀 REAL TRADING MODE</h4>
            <p style="color: var(--text-secondary); margin: 0; font-size: 0.9rem;">
                Live Trading Enabled - Ensure you have:
                <br>• Valid API keys configured
                <br>• Sufficient account balance
                <br>• Proper risk management settings
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        button_text = "▶️ Start Paper Trading" if paper else "▶️ Start REAL Trading"
        
        # Check if real trading is ready
        real_trading_ready = True
        if not paper:
            if not api_key or not api_secret:
                real_trading_ready = False
            elif st.session_state['account_validation'] and not st.session_state['account_validation']['valid']:
                real_trading_ready = False
        
        if st.button(button_text, disabled=st.session_state['is_trading'] or not real_trading_ready, key="start_trading"):
            if paper:
                st.session_state['is_trading'] = True
                st.success("📝 PAPER TRADING STARTED - Safe practice mode!")
            else:
                # Additional safety check for real trading
                if api_key and api_secret:
                    if st.session_state['account_validation'] and st.session_state['account_validation']['valid']:
                        st.session_state['is_trading'] = True
                        st.success("🚀 REAL TRADING STARTED - Live trading enabled!")
                    else:
                        st.error("❌ Account validation required before real trading!")
                else:
                    st.error("❌ API keys required for real trading!")
        
        # Show trading readiness status
        if not paper and not real_trading_ready:
            if not api_key or not api_secret:
                st.error("❌ API keys required for real trading!")
            elif st.session_state['account_validation'] and not st.session_state['account_validation']['valid']:
                st.error("❌ Account validation failed - fix issues before trading!")
            else:
                st.warning("⚠️ Validate account access before starting real trading!")
    
    with col_b:
        stop_text = "⏹️ Stop Trading" if paper else "⏹️ EMERGENCY STOP"
        if st.button(stop_text, disabled=not st.session_state['is_trading'], key="stop_trading"):
            st.session_state['is_trading'] = False
            if paper:
                st.warning("📝 Paper trading stopped!")
            else:
                st.warning("🛑 REAL TRADING STOPPED - All positions closed!")
    
    # Arbitrage Scanner
    st.markdown('<div class="section-header">🔍 Arbitrage Scanner</div>', unsafe_allow_html=True)
    
    arb_enabled = st.toggle(
        "Enable Arbitrage Scanner", 
        value=st.session_state['arb_running'],
        help="Scan for arbitrage opportunities across exchanges"
    )
    st.session_state['arb_running'] = arb_enabled
    
    # Trading Mode Indicator
    if not paper and st.session_state['real_account_data'] and st.session_state['real_account_data'].get('balance'):
        mode_indicator = """
        <div style="background: linear-gradient(135deg, #48bb78, #38a169); color: white; padding: 0.75rem; 
                    border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600; font-size: 0.9rem;">
            🚀 REAL TRADING MODE - Live Account Data
        </div>
        """
    else:
        mode_indicator = """
        <div style="background: linear-gradient(135deg, #4299e1, #3182ce); color: white; padding: 0.75rem; 
                    border-radius: 8px; margin: 1rem 0; text-align: center; font-weight: 600; font-size: 0.9rem;">
            📊 PAPER TRADING MODE - Simulated Data
        </div>
        """
    
    st.markdown(mode_indicator, unsafe_allow_html=True)
    
    # Account Summary removed - Balance now only shows in sidebar
    
    # Position Summary - Only show if there's an active position
    if st.session_state['position'] is not None:
        p = st.session_state['position']
        # Use entry price as fallback since df is not available in sidebar
        pnl = 0.0  # Will be calculated in main section
        pnl_color = "#48bb78" if pnl >= 0 else "#f56565"
        
        st.markdown(f"""
        <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; 
                    border: 1px solid var(--border-color); margin: 1rem 0; text-align: center;">
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;">Active Position</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {pnl_color};">${pnl:,.2f}</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">Unrealized P&L</div>
        </div>
        """, unsafe_allow_html=True)

# Main Dashboard Header
st.markdown("""
<div style="background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple)); 
            padding: 2rem; border-radius: var(--border-radius); margin-bottom: 2rem; 
            text-align: center; color: white;">
    <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
        📊 Live Trading Dashboard
    </h1>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
        Real-time market analysis and automated trading
    </p>
</div>
""", unsafe_allow_html=True)

# Data Processing Section
with st.spinner("🔄 Loading market data..."):
    try:
        # Fetch OHLCV
        df = _exec.fetch_ohlcv_df(symbol, timeframe=timeframe, limit=500)
        
        # Validate required columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"DataFrame missing required columns: {required_columns}")
        
        # Check if data is empty
        if len(df) == 0:
            raise ValueError("No data returned from exchange")
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # If user requested signal test, compute and show quick summary
        if st.session_state.get('signal_test_trigger'):
            st.session_state['signal_test_trigger'] = False
            with st.spinner("Testing signals..."):
                try:
                    from indicators.weighted_signals import generate_weighted_signals
                    sig = generate_weighted_signals(df).astype(bool)
                    df['signal'] = sig
                    buy_count = int(sig.sum())
                    sell_count = int((~sig).sum())
                    last_sig = 'BUY' if bool(sig.iloc[-1]) else 'SELL'
                    st.success(f"Signals ready — BUY: {buy_count}, SELL: {sell_count}, Latest: {last_sig}")
                except Exception as e:
                    st.error(f"Signal test failed: {e}")
        
        # Indicators & signals
        df['rsi'] = rsi(df['close'], length=int(rsi_length))
        
        # Add EMA indicators for image-style chart
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # For Pine script compatibility
        df['ema_fast'] = df['ema50']
        df['ema_slow'] = df['ema200']
        
        # Add Stochastic indicator
        df['stoch'] = stochastic(df['high'], df['low'], df['close'], length=14)
        
        # Add Parabolic SAR indicator
        df['sar'] = parabolic_sar(df['high'], df['low'], df['close'], 
                                   af_start=0.02, af_increment=0.02, af_max=0.2)
        
        # Calculate hlc3 if columns exist
        if set(['high', 'low', 'close']).issubset(df.columns):
            df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3.0
            wt_input = df['hlc3']
        else:
            wt_input = df['close']
        
        # Compute wavetrend and ensure correct assignment
        wt = wavetrend(wt_input, channel_length=int(wt_channel), average_length=int(wt_avg))
        if isinstance(wt, pd.DataFrame):
            df[['wt1', 'wt2']] = wt[['wt1', 'wt2']]
        elif isinstance(wt, (list, tuple)) and len(wt) == 2:
            df['wt1'], df['wt2'] = wt
        else:
            raise ValueError("wavetrend function returned unexpected output format")
        
        # Load TradingView webhook signals
        df_sig_all = fetch_recent_signals_http(limit=500)
        if df_sig_all.empty:
            df_sig_all = load_tradingview_signals()
        
        # Map webhook signals to dataframe
        if not df_sig_all.empty and 'timestamp' in df_sig_all.columns:
            # Convert timestamp column
            df_sig_all['timestamp'] = pd.to_datetime(df_sig_all['timestamp'])
            
            # Merge webhook signals with main dataframe (both must be sorted by timestamp)
            df_sorted = df.sort_values('timestamp').copy()
            df_sig_sorted = df_sig_all.sort_values('timestamp').copy()
            df = pd.merge_asof(df_sorted, df_sig_sorted, on='timestamp', direction='backward', suffixes=('', '_webhook'))
            # Create webhook column from TradingView signals
            if 'side' in df.columns:
                # Webhook signal is True when side is 'buy'
                df['webhook'] = (df['side'].str.lower() == 'buy').fillna(False).astype(bool)
            elif 'signal' in df.columns:
                df['webhook'] = df['signal'].fillna(False).astype(bool)
            else:
                df['webhook'] = False
        else:
            df['webhook'] = False
        
        sm = StrategyManager()
        
        # Generate signals using TradingView Webhook + RSI + WaveTrend combo
        if strat_choice == 'auto':
            # Use TradingTriggerEngine for final_buy/final_sell signals
            trigger_engine = TradingTriggerEngine()
            signals_dict = trigger_engine.generate_combined_signals(
                df,
                wt_channel_length=int(wt_channel),
                wt_average_length=int(wt_avg),
                ema_fast=50,
                ema_slow=200,
                rsi_length=int(rsi_length),
                rsi_buy_threshold=53.0,
                rsi_sell_threshold=47.0,
                show_intermediate=True
            )
            
            # Assign final signals
            df['final_buy'] = signals_dict['final_buy']
            df['final_sell'] = signals_dict['final_sell']
            
            # Also keep intermediate signals for display
            if 'wt_buy' in signals_dict:
                df['wt_buy'] = signals_dict['wt_buy']
            if 'wt_sell' in signals_dict:
                df['wt_sell'] = signals_dict['wt_sell']
            if 'momentum_buy' in signals_dict:
                df['momentum_buy'] = signals_dict['momentum_buy']
            if 'momentum_sell' in signals_dict:
                df['momentum_sell'] = signals_dict['momentum_sell']
            if 'rsi_buy' in signals_dict:
                df['rsi_buy'] = signals_dict['rsi_buy']
            if 'rsi_sell' in signals_dict:
                df['rsi_sell'] = signals_dict['rsi_sell']
            
            # For backward compatibility
            df['signal'] = df['final_buy']
            df['sell_signal'] = df['final_sell']
        elif strat_choice == 'ema_crossover':
            return_mode = 'long_short' if position_mode == 'Long + Short' else 'long_only'
            sig_df = sm.strategies['ema_crossover'].generate_signals(df, return_mode=return_mode)
            if return_mode == 'long_short':
                df[['long', 'short']] = sig_df[['long', 'short']]
            else:
                df[['signal']] = sig_df[['signal']]
        elif strat_choice == 'rsi_bbands':
            df['signal'] = sm.strategies['rsi_bbands'].generate_signals(df, rsi_len=int(rsi_length))
        elif strat_choice == 'grid':
            df['signal'] = sm.strategies['grid'].generate_signals(df)
        elif strat_choice == 'client_weighted':
            # ---------------- TV multi-timeframe aggregator (lightweight) ----------------
            # Pull recent alerts (HTTP realtime server) then fall back to file store
            df_sig_all = fetch_recent_signals_http(limit=500)
            if df_sig_all.empty:
                df_sig_all = load_tradingview_signals()

            def _norm_tf(tf: str) -> str:
                tf = str(tf or '').upper()
                mapping = {
                    '1':'1m','3':'3m','5':'5m','10':'10m','15':'15m','20':'20m','30':'30m',
                    '60':'1h','120':'2h','180':'3h','240':'4h','360':'6h','480':'8h','720':'12h',
                    'D':'1d','2D':'2d','3D':'3d','5D':'5d','W':'1w','2W':'2w','3W':'3w','M':'1M'
                }
                return mapping.get(tf, tf.lower())

            def _add_flag(label: str, col: str):
                if df_sig_all.empty or 'time' not in df_sig_all.columns and 'received_at' not in df_sig_all.columns:
                    return
                tcol = 'time' if 'time' in df_sig_all.columns else 'received_at'
                sub = df_sig_all.copy()
                sub['timestamp'] = pd.to_datetime(sub[tcol])
                if 'side' in sub.columns:
                    sub = sub[sub['side'].str.lower()=='buy']
                if 'timeframe' in sub.columns:
                    sub = sub[_norm_tf(sub['timeframe']).astype(str)==label]
                # Initialize column
                df[col] = False
                if sub.empty:
                    return
                # mark on or after signal time
                ts = pd.to_datetime(df['timestamp'])
                for ts_sig in sub['timestamp']:
                    idx = ts.searchsorted(ts_sig, side='left')
                    if 0 <= idx < len(df):
                        df.at[df.index[idx], col] = True

            # Create timeframe flags based on selection
            tfs_for_flags = []
            if 'selected_tfs_client' in locals() and isinstance(selected_tfs_client, list):
                tfs_for_flags = selected_tfs_client
            else:
                tfs_for_flags = ['5m','15m','1h']

            for tf_lab in tfs_for_flags:
                _add_flag(tf_lab, f"tv_buy_{tf_lab}")
            # Backwards-compatible single-TF flag (current TF)
            _add_flag(str(timeframe).lower(), 'tv_buy')

            # Build weights dict from UI selections
            mtf_weights = {}
            if 'mtf_weight_inputs' in locals():
                for tf_lab, w in mtf_weight_inputs.items():
                    mtf_weights[f"tv_buy_{tf_lab}"] = float(w)

            df['signal'] = sm.strategies['client_weighted'].generate_signals(
                df,
                rsi_length=int(rsi_length),
                rsi_buy_threshold=float(rsi_overbought),
                rsi_sell_threshold=float(rsi_oversold),
                wt_channel_length=int(wt_channel),
                wt_average_length=int(wt_avg),
                entry_threshold=float(entry_threshold if 'entry_threshold' in locals() else 0.60),
                mtf_tv_weights=mtf_weights,
            )
        else:
            # Fallback to auto strategy
            rsi_oversold_condition = df['rsi'] < rsi_oversold
            wt_cross_up = (df['wt1'].shift(1) <= df['wt2'].shift(1)) & (df['wt1'] > df['wt2'])
            df['signal'] = rsi_oversold_condition & wt_cross_up
        
        # Market Overview Section
        last_close = float(df['close'].iat[-1]) if len(df) else 0.0
        prev_close = float(df['close'].iat[-2]) if len(df) > 1 else last_close

        # Calculate 24h change (last 24 bars for hourly data, or adjust based on timeframe)
        if len(df) >= 24:
            price_24h_ago = float(df['close'].iat[-24])
            price_change_24h = last_close - price_24h_ago
            price_change_24h_pct = (price_change_24h / price_24h_ago * 100) if price_24h_ago else 0
        else:
            # Fallback to previous bar if not enough data
            price_change_24h = last_close - prev_close
            price_change_24h_pct = (price_change_24h / prev_close * 100) if prev_close else 0

        # Current bar change
        price_change = last_close - prev_close
        price_change_pct = (price_change / prev_close * 100) if prev_close else 0
        up = price_change_24h >= 0
        
        st.success("✅ Market data loaded successfully!")

    except Exception as e:
        st.error(f"❌ Data Processing Error: {e}")
        st.markdown("""
        <div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); margin: 1rem 0;">
            <h3 style="color: var(--accent-red); margin-top: 0;">⚠️ Unable to Load Market Data</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                Please check your internet connection and exchange settings. 
                Make sure the selected trading pair is available on the chosen exchange.
            </p>
            <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; 
                        border-left: 4px solid var(--accent-red);">
                <strong>Error Details:</strong><br>
                <code style="color: var(--text-primary);">{}</code>
            </div>
        </div>
        """.format(str(e)), unsafe_allow_html=True)
        st.stop()

# Check if data was loaded successfully
if 'df' not in locals() or df is None or len(df) == 0:
    st.error("❌ No market data available. Please check your exchange settings and try again.")
    st.stop()

# Market Overview Section
last_close = float(df['close'].iat[-1]) if len(df) else 0.0
prev_close = float(df['close'].iat[-2]) if len(df) > 1 else last_close

# Calculate 24h change (last 24 bars for hourly data, or adjust based on timeframe)
if len(df) >= 24:
    price_24h_ago = float(df['close'].iat[-24])
    price_change_24h = last_close - price_24h_ago
    price_change_24h_pct = (price_change_24h / price_24h_ago * 100) if price_24h_ago else 0
else:
    # Fallback to previous bar if not enough data
    price_change_24h = last_close - prev_close
    price_change_24h_pct = (price_change_24h / prev_close * 100) if prev_close else 0

# Current bar change
price_change = last_close - prev_close
price_change_pct = (price_change / prev_close * 100) if prev_close else 0
up = price_change_24h >= 0

# Market Header with Key Metrics
st.markdown(f"""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div>
            <h2 style="margin: 0; color: var(--text-primary); font-size: 1.8rem;">
                📈 {symbol} • {ex_name.upper()}
            </h2>
            <p style="margin: 0.25rem 0 0 0; color: var(--text-secondary); font-size: 0.95rem;">
                {timeframe} • Last updated: {pd.Timestamp.now().strftime('%H:%M:%S')}
            </p>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 2rem; font-weight: 700; color: var(--text-primary);">
                ${last_close:,.6f}
            </div>
            <div style="font-size: 1rem; color: {'var(--accent-green)' if up else 'var(--accent-red)'}; 
                        font-weight: 600;">
                24h: {price_change_24h:+.6f} ({price_change_24h_pct:+.2f}%)
            </div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">
                1h: {price_change:+.6f} ({price_change_pct:+.2f}%)
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Enhanced Professional Chart Section
st.markdown("""
<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 2rem; border-radius: 16px; 
            border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <h3 style="margin: 0; color: #fff; display: flex; align-items: center; gap: 0.75rem; font-size: 1.5rem; font-weight: 600;">
            📊 Real-Time Price Chart & Technical Analysis
        </h3>
        <div style="display: flex; gap: 0.5rem; align-items: center;">
            <div style="padding: 0.5rem 1rem; background: rgba(72, 187, 120, 0.2); border-radius: 20px; border: 1px solid rgba(72, 187, 120, 0.3);">
                <span style="color: #48bb78; font-size: 0.9rem; font-weight: 600;">LIVE</span>
            </div>
            <div style="padding: 0.5rem 1rem; background: rgba(160, 174, 192, 0.2); border-radius: 20px; border: 1px solid rgba(160, 174, 192, 0.3);">
                <span style="color: #a0aec0; font-size: 0.9rem;">{}</span>
            </div>
        </div>
    </div>
""".format(timeframe), unsafe_allow_html=True)

# Real-time chart with lightweight-charts (full width)
with st.container():
    # Lightweight Charts panel with real-time TV signal markers
    ohlc = []
    base_df = df.copy() if 'df' in locals() else pd.DataFrame()
    if base_df is None or base_df.empty or not set(['timestamp','open','high','low','close']).issubset(base_df.columns):
        # Fallback: fetch OHLC from yfinance for display
        def _yf_params(tf: str, days: int = 7):
            tf = str(tf).lower()
            if tf == '1m': return ("1d","1m")
            if tf == '5m': return ("7d","5m")
            if tf == '15m': return ("30d","15m")
            if tf == '1h': return ("60d","60m")
            if tf == '4h': return ("730d","240m")
            return ("1y","1d")
        yf_symbol = to_yfinance_symbol(ex_name, symbol)
        p,i = _yf_params(str(timeframe))
        try:
            tmp = yf.download(yf_symbol, period=p, interval=i, progress=False)
            if not tmp.empty:
                base_df = tmp.reset_index().rename(columns={'Date':'timestamp','Datetime':'timestamp','Open':'open','High':'high','Low':'low','Close':'close'})
        except Exception:
            base_df = pd.DataFrame()

    if not base_df.empty:
        # time in seconds for lightweight-charts
        ohlc = [
            {
                'time': int(pd.Timestamp(ts).timestamp()),
                'open': float(o), 'high': float(h), 'low': float(l), 'close': float(c)
            }
            for ts, o, h, l, c in zip(base_df['timestamp'], base_df['open'], base_df['high'], base_df['low'], base_df['close'])
        ]
    lwc_data_json = json.dumps(ohlc)
    import base64 as _b64
    lwc_data_b64 = _b64.b64encode(lwc_data_json.encode('utf-8')).decode('ascii')

# Lightweight Charts disabled - fails in Streamlit sandboxed iframe
# Using Plotly chart below instead
# html(f"""
# <div id=\"lwc_container\" style=\"width:100%; height:600px;\"></div>
# ...
# """, height=610)
show_volume = False  # Volume indicator disabled as requested

# Create premium TradingView-style chart using chart_builder module
fig = create_premium_chart(df, symbol, show_volume=show_volume)
chart_config = get_chart_config()

# Update filename in config
chart_config['toImageButtonOptions']['filename'] = f'{symbol}_chart'

# Render Plotly chart
st.plotly_chart(fig, use_container_width=True, config=chart_config)

st.markdown("</div>", unsafe_allow_html=True)

# Enhanced Professional Technical Indicators Section
st.markdown("""
<div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); padding: 2rem; border-radius: 16px; 
            border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <h3 style="margin: 0; color: #fff; display: flex; align-items: center; gap: 0.75rem; font-size: 1.5rem; font-weight: 600;">
            📊 Real-Time Technical Indicators
        </h3>
        <div style="padding: 0.5rem 1rem; background: rgba(255, 255, 255, 0.1); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.2);">
            <span style="color: #fff; font-size: 0.9rem; font-weight: 600;">LIVE DATA</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Enhanced KPI Cards with smooth animations
k1, k2, k3, k4 = st.columns(4)

with k1:
    rsi_val = float(df['rsi'].iat[-1])
    rsi_color = "#ff4757" if rsi_val > 70 else "#00ff88" if rsi_val < 30 else "#ffa726"
    rsi_status = "OVERBOUGHT" if rsi_val > 70 else "OVERSOLD" if rsi_val < 30 else "NEUTRAL"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%); 
                padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); 
                text-align: center; transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);">
        <div style="font-size: 2.5rem; font-weight: 700; color: {rsi_color}; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);">
            {rsi_val:.1f}
        </div>
        <div style="color: #fff; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">RSI (14)</div>
        <div style="color: {rsi_color}; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
            {rsi_status}
        </div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    wt1_val = float(df['wt1'].iat[-1])
    wt1_color = "#00ff88" if wt1_val > df['wt2'].iat[-1] else "#ff4757"
    wt1_trend = "BULLISH" if wt1_val > df['wt2'].iat[-1] else "BEARISH"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%); 
                padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); 
                text-align: center; transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);">
        <div style="font-size: 2.5rem; font-weight: 700; color: {wt1_color}; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);">
            {wt1_val:.2f}
        </div>
        <div style="color: #fff; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">WaveTrend 1</div>
        <div style="color: {wt1_color}; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
            {wt1_trend}
        </div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    wt2_val = float(df['wt2'].iat[-1])
    wt2_color = "#00ff88" if wt2_val > 0 else "#ff4757"
    wt2_signal = "POSITIVE" if wt2_val > 0 else "NEGATIVE"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%); 
                padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); 
                text-align: center; transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);">
        <div style="font-size: 2.5rem; font-weight: 700; color: {wt2_color}; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);">
            {wt2_val:.2f}
        </div>
        <div style="color: #fff; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">WaveTrend 2</div>
        <div style="color: {wt2_color}; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
            {wt2_signal}
        </div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    chg_color = "#00ff88" if price_change_24h_pct >= 0 else "#ff4757"
    chg_symbol = "↗" if price_change_24h_pct >= 0 else "↘"
    chg_trend = "RISING" if price_change_24h_pct >= 0 else "FALLING"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%); 
                padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); 
                text-align: center; transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);">
        <div style="font-size: 2.5rem; font-weight: 700; color: {chg_color}; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);">
            {chg_symbol} {abs(price_change_24h_pct):.2f}%
        </div>
        <div style="color: #fff; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">24h Change</div>
        <div style="color: {chg_color}; font-size: 0.9rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
            {chg_trend}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Add additional technical indicators row
st.markdown("<br>", unsafe_allow_html=True)
k5, k6, k7, k8 = st.columns(4)

with k5:
    # Current Price
    current_price = float(df['close'].iat[-1])
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%); 
                padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); 
                text-align: center; transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);">
        <div style="font-size: 2rem; font-weight: 700; color: #00ff88; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);">
            ${current_price:.6f}
        </div>
        <div style="color: #fff; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">Current Price</div>
        <div style="color: #a0aec0; font-size: 0.9rem; font-weight: 500;">{symbol}</div>
    </div>
    """, unsafe_allow_html=True)

with k6:
    # High 24h
    high_24h = float(df['high'].tail(24).max()) if len(df) >= 24 else float(df['high'].max())
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%); 
                padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); 
                text-align: center; transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);">
        <div style="font-size: 2rem; font-weight: 700; color: #00ff88; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);">
            ${high_24h:.6f}
        </div>
        <div style="color: #fff; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">24h High</div>
        <div style="color: #a0aec0; font-size: 0.9rem; font-weight: 500;">MAXIMUM</div>
    </div>
    """, unsafe_allow_html=True)

with k7:
    # Low 24h
    low_24h = float(df['low'].tail(24).min()) if len(df) >= 24 else float(df['low'].min())
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%); 
                padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); 
                text-align: center; transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);">
        <div style="font-size: 2rem; font-weight: 700; color: #ff4757; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);">
            ${low_24h:.6f}
        </div>
        <div style="color: #fff; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">24h Low</div>
        <div style="color: #a0aec0; font-size: 0.9rem; font-weight: 500;">MINIMUM</div>
    </div>
    """, unsafe_allow_html=True)

with k8:
    # Volume 24h
    volume_24h = float(df['volume'].tail(24).sum()) if len(df) >= 24 and 'volume' in df.columns else 0
    volume_display = f"{volume_24h:,.0f}" if volume_24h > 0 else "N/A"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%); 
                padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); 
                text-align: center; transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);">
        <div style="font-size: 1.8rem; font-weight: 700; color: #ffa726; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);">
            {volume_display}
        </div>
        <div style="color: #fff; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">24h Volume</div>
        <div style="color: #a0aec0; font-size: 0.9rem; font-weight: 500;">TRADING</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Recent Data Table
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <h3 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
        📋 Recent Market Data
    </h3>
""", unsafe_allow_html=True)

# Style the dataframe
styled_df = df.tail(20).copy()
styled_df['timestamp'] = pd.to_datetime(styled_df['timestamp']).dt.strftime('%H:%M:%S')
styled_df = styled_df.round(6)

st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Trading Status Section
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <h3 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
        💼 Trading Status & Positions
    </h3>
""", unsafe_allow_html=True)

cpos, cords = st.columns([1, 2])
with cpos:
    if st.session_state['position'] is not None:
        p = st.session_state['position']
        pnl = (last_close - p['entry_price']) * p['qty']
        pnl_color = "#48bb78" if pnl >= 0 else "#f56565"
        bars_in_trade = len(df) - p['entry_idx'] if 'entry_idx' in p else 0
        
        st.markdown(f"""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color);">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                📈 Open Position
            </h4>
            <div style="display: grid; gap: 0.75rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Entry Price:</span>
                    <span style="color: var(--text-primary); font-weight: 600;">${p['entry_price']:.6f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Quantity:</span>
                    <span style="color: var(--text-primary); font-weight: 600;">{p['qty']:.6f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Unrealized P&L:</span>
                    <span style="color: {pnl_color}; font-weight: 700;">${pnl:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Bars in Trade:</span>
                    <span style="color: var(--text-primary); font-weight: 600;">{bars_in_trade}</span>
                </div>
                <hr style="border-color: var(--border-color); margin: 0.5rem 0;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Stop Loss:</span>
                    <span style="color: var(--accent-red); font-weight: 600;">${(p['entry_price']*(1-float(stop_loss_pct))):.6f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: var(--text-secondary);">Take Profit:</span>
                    <span style="color: var(--accent-green); font-weight: 600;">${(p['entry_price']*(1+float(take_profit_pct))):.6f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); text-align: center;">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                ⏳ No Open Position
            </h4>
            <p style="color: var(--text-secondary); margin: 0;">
                Waiting for next trading signal...
            </p>
        </div>
        """, unsafe_allow_html=True)

with cords:
    if st.session_state['trades']:
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color);">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                📋 Recent Trades
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        trades_df = pd.DataFrame(st.session_state['trades'])
        if not trades_df.empty:
            trades_df = trades_df.tail(10)  # Show only last 10 trades
            st.markdown(trades_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); text-align: center;">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                📊 No Trades Yet
            </h4>
            <p style="color: var(--text-secondary); margin: 0;">
                Start trading to see your trade history here.
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Indicator Sparklines Section
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <h3 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
        📈 Indicator Trends
    </h3>
""", unsafe_allow_html=True)

spr1, spr2, spr3 = st.columns(3)
with spr1:
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(
        x=df['timestamp'].tail(100), 
        y=df['rsi'].tail(100), 
        mode='lines', 
        line=dict(color="#4299e1", width=2),
        name="RSI"
    ))
    rsi_fig.update_layout(
        height=150, 
        margin=dict(l=10, r=10, t=20, b=10), 
        xaxis_visible=False, 
        yaxis_title="RSI",
        template='plotly_dark' if dark_theme else 'plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    rsi_fig.update_yaxes(range=[0, 100])
    st.plotly_chart(rsi_fig, use_container_width=True, config={'displaylogo': False, 'modeBarButtonsToRemove': ['select2d','lasso2d']})

with spr2:
    wt1_fig = go.Figure()
    wt1_fig.add_trace(go.Scatter(
        x=df['timestamp'].tail(100), 
        y=df['wt1'].tail(100), 
        mode='lines', 
        line=dict(color="#48bb78", width=2),
        name="WT1"
    ))
    wt1_fig.update_layout(
        height=150, 
        margin=dict(l=10, r=10, t=20, b=10), 
        xaxis_visible=False, 
        yaxis_title="WT1",
        template='plotly_dark' if dark_theme else 'plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(wt1_fig, use_container_width=True, config={'displaylogo': False, 'modeBarButtonsToRemove': ['select2d','lasso2d']})

with spr3:
    wt2_fig = go.Figure()
    wt2_fig.add_trace(go.Scatter(
        x=df['timestamp'].tail(100), 
        y=df['wt2'].tail(100), 
        mode='lines', 
        line=dict(color="#a0aec0", width=2),
        name="WT2"
    ))
    wt2_fig.update_layout(
        height=150, 
        margin=dict(l=10, r=10, t=20, b=10), 
        xaxis_visible=False, 
        yaxis_title="WT2",
        template='plotly_dark' if dark_theme else 'plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(wt2_fig, use_container_width=True, config={'displaylogo': False, 'modeBarButtonsToRemove': ['select2d','lasso2d']})

st.markdown("</div>", unsafe_allow_html=True)

latest_idx = len(df) - 1
latest_price = float(df['close'].iat[latest_idx]) if not pd.isna(df['close'].iat[latest_idx]) else 0.0
signal_now = bool(df['signal'].iat[latest_idx])
wt_cross_down_now = False
if latest_idx > 0:  # Prevent index out of bounds
    wt_cross_down_now = (df['wt1'].iat[latest_idx-1] >= df['wt2'].iat[latest_idx-1]) and (df['wt1'].iat[latest_idx] < df['wt2'].iat[latest_idx])

# Show latest signal badge with new trigger system
sig_badge = "No signal"
sig_color = "#8899aa"
signal_description = ""

if 'final_buy' in df.columns and 'final_sell' in df.columns:
    buy_signal_now = bool(df['final_buy'].iat[latest_idx])
    sell_signal_now = bool(df['final_sell'].iat[latest_idx])
    
    if buy_signal_now:
        # Determine which trigger fired
        if 'wt_buy' in df.columns and bool(df['wt_buy'].iat[latest_idx]):
            sig_badge = "WT Green Dot"
            signal_description = "Highest Priority"
            sig_color = "#00ff88"
        elif 'momentum_buy' in df.columns and bool(df['momentum_buy'].iat[latest_idx]):
            sig_badge = "Momentum BUY"
            signal_description = "Medium Priority"
            sig_color = "#22cc88"
        elif 'rsi_buy' in df.columns and bool(df['rsi_buy'].iat[latest_idx]):
            sig_badge = "RSI BUY"
            signal_description = "Low Priority"
            sig_color = "#88cc22"
        else:
            sig_badge = "BUY Signal"
            sig_color = "#22cc88"
    elif sell_signal_now:
        # Determine which trigger fired
        if 'wt_sell' in df.columns and bool(df['wt_sell'].iat[latest_idx]):
            sig_badge = "WT Red Dot"
            signal_description = "Highest Priority"
            sig_color = "#ff4444"
        elif 'momentum_sell' in df.columns and bool(df['momentum_sell'].iat[latest_idx]):
            sig_badge = "Momentum SELL"
            signal_description = "Medium Priority"
            sig_color = "#cc2222"
        elif 'rsi_sell' in df.columns and bool(df['rsi_sell'].iat[latest_idx]):
            sig_badge = "RSI SELL"
            signal_description = "Low Priority"
            sig_color = "#cc8822"
        else:
            sig_badge = "SELL Signal"
            sig_color = "#cc2222"
elif signal_now:
    # Fallback for other strategies
    sig_badge = "BUY signal"
    sig_color = "#22cc88"

# Trading execution logic (runs for all strategies when is_trading is True)
    if st.session_state['is_trading']:
        try:
            # Mode-specific trading logic
            paper_mode = st.session_state.get('paper_mode', True)
            if paper_mode:
                print(f"PAPER_TRADING: Processing simulated trades for {symbol}")
            else:
                print(f"REAL_TRADING: Processing trades for {symbol}")
            
            # Exit logic
            if st.session_state['position'] is not None:
                pos = st.session_state['position']
                entry_price = pos['entry_price']
                qty = pos['qty']
                stop_price = entry_price * (1 - float(stop_loss_pct))
                tp_price = entry_price * (1 + float(take_profit_pct))
                bars_in_trade = latest_idx - pos['entry_idx']
                should_exit = False
                if latest_price <= stop_price or latest_price >= tp_price:
                    should_exit = True
                if not should_exit and wt_cross_down_now:
                    should_exit = True
                if not should_exit and bars_in_trade >= int(max_bars_in_trade):
                    should_exit = True
                if should_exit:
                    side = 'sell' if qty > 0 else 'buy'
                    order = _exec.place_market_order(symbol, side, abs(qty))
                    pnl = (latest_price - entry_price) * qty
                    st.session_state['account']['cash'] += pnl
                    if st.session_state['trades']:
                        st.session_state['trades'][-1].update({
                            'exit_idx': latest_idx, 
                            'exit_price': latest_price,
                            'pnl': pnl
                        })
                    try:
                        log_trade('logs/trades.csv', {
                            'symbol': symbol,
                            'side': side,
                            'qty': abs(qty),
                            'price': latest_price,
                            'pnl': pnl,
                            'ts': int(time.time()*1000)
                        })
                    except Exception:
                        pass
                    st.session_state['position'] = None

            # Entry logic using new 3-tier trading trigger system
            if st.session_state['position'] is None and not pd.isna(latest_price) and latest_price > 0:
                # Check for buy signals from the new trigger system
                buy_signal = False
                sell_signal = False
                signal_type = "None"
                
                if strat_choice == 'auto' and 'final_buy' in df.columns and 'final_sell' in df.columns:
                    buy_signal = bool(df['final_buy'].iat[latest_idx])
                    sell_signal = bool(df['final_sell'].iat[latest_idx])
                    
                    # Determine signal type for logging
                    if 'wt_buy' in df.columns and bool(df['wt_buy'].iat[latest_idx]):
                        signal_type = "WT Green Dot"
                    elif 'wt_sell' in df.columns and bool(df['wt_sell'].iat[latest_idx]):
                        signal_type = "WT Red Dot"
                    elif 'momentum_buy' in df.columns and bool(df['momentum_buy'].iat[latest_idx]):
                        signal_type = "Momentum Buy"
                    elif 'momentum_sell' in df.columns and bool(df['momentum_sell'].iat[latest_idx]):
                        signal_type = "Momentum Sell"
                    elif 'rsi_buy' in df.columns and bool(df['rsi_buy'].iat[latest_idx]):
                        signal_type = "RSI Buy"
                    elif 'rsi_sell' in df.columns and bool(df['rsi_sell'].iat[latest_idx]):
                        signal_type = "RSI Sell"
                else:
                    # Fallback to old signal system for other strategies
                    buy_signal = signal_now
                    signal_type = f"{strat_choice} strategy"
                
                # Execute buy trade
                if buy_signal and position_mode in ['Long only', 'Long + Short']:
                        risk_usd = st.session_state['account']['cash'] * float(risk_per_trade)
                        qty = position_size_from_risk(st.session_state['account']['cash'], float(risk_per_trade), latest_price)
                        if qty > 0:
                            order = _exec.place_market_order(symbol, 'buy', qty)
                            st.session_state['position'] = {
                                'entry_price': latest_price, 
                                'qty': qty, 
                                'entry_idx': latest_idx,
                                'strategy': strat_choice,
                            'signal_type': signal_type,
                            'entry_rsi': float(df['rsi'].iat[latest_idx]),
                            'entry_wt1': float(df['wt1'].iat[latest_idx]),
                            'entry_wt2': float(df['wt2'].iat[latest_idx])
                            }
                            st.session_state['trades'].append({
                                'entry_idx': latest_idx, 
                                'entry_price': latest_price, 
                                'qty': qty,
                                'strategy': strat_choice,
                            'signal_type': signal_type,
                            'entry_rsi': float(df['rsi'].iat[latest_idx])
                            })
                            try:
                                log_trade('logs/trades.csv', {
                                    'symbol': symbol,
                                    'side': 'buy',
                                    'qty': qty,
                                    'price': latest_price,
                                    'strategy': strat_choice,
                                    'signal_type': signal_type,
                                    'rsi': float(df['rsi'].iat[latest_idx]),
                                    'ts': int(time.time()*1000)
                                })
                            except Exception:
                                pass
                
                # Execute sell trade (for short positions)
                elif sell_signal and position_mode == 'Long + Short':
                    risk_usd = st.session_state['account']['cash'] * float(risk_per_trade)
                    qty = position_size_from_risk(st.session_state['account']['cash'], float(risk_per_trade), latest_price)
                    if qty > 0:
                        order = _exec.place_market_order(symbol, 'sell', qty)
                        st.session_state['position'] = {
                            'entry_price': latest_price, 
                            'qty': -qty,  # Negative quantity for short position
                            'entry_idx': latest_idx,
                            'strategy': strat_choice,
                            'signal_type': signal_type,
                            'entry_rsi': float(df['rsi'].iat[latest_idx]),
                            'entry_wt1': float(df['wt1'].iat[latest_idx]),
                            'entry_wt2': float(df['wt2'].iat[latest_idx])
                        }
                        st.session_state['trades'].append({
                            'entry_idx': latest_idx, 
                            'entry_price': latest_price, 
                            'qty': -qty,
                            'strategy': strat_choice,
                            'signal_type': signal_type,
                            'entry_rsi': float(df['rsi'].iat[latest_idx])
                        })
                        try:
                            log_trade('logs/trades.csv', {
                                'symbol': symbol,
                                'side': 'sell',
                                'qty': qty,
                                'price': latest_price,
                                'strategy': strat_choice,
                                'signal_type': signal_type,
                                'rsi': float(df['rsi'].iat[latest_idx]),
                                'ts': int(time.time()*1000)
                            })
                        except Exception:
                            pass
                else:
                    # For other strategies, use the signal as is
                    risk_usd = st.session_state['account']['cash'] * float(risk_per_trade)
                    qty = position_size_from_risk(st.session_state['account']['cash'], float(risk_per_trade), latest_price)
                    if qty > 0:
                        order = _exec.place_market_order(symbol, 'buy', qty)
                        st.session_state['position'] = {
                            'entry_price': latest_price, 
                            'qty': qty, 
                            'entry_idx': latest_idx,
                            'strategy': strat_choice
                        }
                        st.session_state['trades'].append({
                            'entry_idx': latest_idx, 
                            'entry_price': latest_price, 
                            'qty': qty,
                            'strategy': strat_choice
                        })
                        try:
                            log_trade('logs/trades.csv', {
                                'symbol': symbol,
                                'side': 'buy',
                                'qty': qty,
                                'price': latest_price,
                                'strategy': strat_choice,
                                'ts': int(time.time()*1000)
                            })
                        except Exception:
                            pass

            # Equity tracking
            if st.session_state['position'] is not None:
                pos = st.session_state['position']
                unreal = (latest_price - pos['entry_price']) * pos['qty']
                equity_val = st.session_state['account']['cash'] + unreal
            else:
                equity_val = st.session_state['account']['cash']
            st.session_state['account']['equity'].append(float(equity_val))
            try:
                log_pnl('logs/equity.csv', float(equity_val))
            except Exception:
                pass

        except Exception as e:
            st.error(f"Trading Logic Error: {e}")
            st.session_state['is_trading'] = False  # Stop trading on error

# Right Sidebar - Enhanced Tabs
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-bottom: 1.5rem;">
    <h3 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
        📊 Market Analysis & Tools
    </h3>
""", unsafe_allow_html=True)

tabs = st.tabs(["🎯 Strategy", "💼 Account", "📋 Orders", "📈 Market", "🚨 Signals", "🔍 Arbitrage", "⚙️ Order Management", "📊 Comprehensive Metrics", "🧪 Advanced Backtester", "📡 TradingView Signals", "🚨 Error Log"]) 

with tabs[0]:
    # Get current strategy name
    current_strategy = strat_choice if 'strat_choice' in locals() else 'auto'
    strategy_name = {
        'auto': 'TradingView Webhook + RSI + WaveTrend (Auto)',
        'ema_crossover': 'EMA Crossover',
        'rsi_bbands': 'RSI + Bollinger Bands',
        'grid': 'Grid Trading'
    }.get(current_strategy, 'TradingView Webhook + RSI + WaveTrend (Auto)')
    
    # Calculate values first to avoid f-string format errors
    sl_display = f"{(stop_loss_pct * 100):.1f}%"
    tp_display = f"{(take_profit_pct * 100):.1f}%"
    max_bars_display = max_bars_in_trade
    rsi_threshold = rsi_oversold
    refresh_display = refresh_secs
    is_trading = 'is_trading' in st.session_state and st.session_state['is_trading']
    last_signal = 'BUY' if 'df' in locals() and len(df) > 0 and 'signal' in df.columns and bool(df['signal'].iat[-1]) else 'No Signal'
    
    st.markdown(f"""
    <div class="strategy-card">
        <div class="strategy-header">
            🎯 Active Strategy: {strategy_name}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Entry Conditions
    with st.container():
        st.markdown("""
        <div class="conditions-list">
            <h4>Entry Conditions</h4>
            <ul>
        """, unsafe_allow_html=True)
        
        if current_strategy == 'auto':
            st.markdown('<li>Priority 1: WaveTrend cross up (WT1 > WT2)</li>', unsafe_allow_html=True)
            st.markdown('<li>Priority 2: TradingView Webhook buy signal</li>', unsafe_allow_html=True)
            st.markdown('<li>Priority 3: RSI > 53 (Buy) or RSI < 47 (Sell)</li>', unsafe_allow_html=True)
        if current_strategy == 'rsi_bbands':
            st.markdown(f'<li>RSI below oversold threshold ({rsi_threshold})</li>', unsafe_allow_html=True)
        if current_strategy == 'ema_crossover':
            st.markdown('<li>EMA Fast crosses above EMA Slow</li>', unsafe_allow_html=True)
        if current_strategy == 'rsi_bbands':
            st.markdown('<li>Price below Bollinger Lower Band</li>', unsafe_allow_html=True)
        if current_strategy == 'grid':
            st.markdown('<li>Price crosses below grid level</li>', unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)
    
    # Exit Conditions
    with st.container():
        st.markdown(f"""
        <div class="conditions-list">
            <h4>Exit Conditions</h4>
            <ul>
                <li>Stop Loss: {sl_display}</li>
                <li>Take Profit: {tp_display}</li>
        """, unsafe_allow_html=True)
        
        if current_strategy == 'auto':
            st.markdown('<li>WaveTrend cross down</li>', unsafe_allow_html=True)
        
        st.markdown(f'<li>Max bars in trade: {max_bars_display}</li></ul></div>', unsafe_allow_html=True)
    
    # Strategy Status
    status_color = "var(--accent-green)" if is_trading else "var(--accent-red)"
    status_emoji = "🟢 LIVE TRADING" if is_trading else "🔴 STOPPED"
    
    st.markdown(f"""
    <div class="status-box">
        <div class="status-text" style="color: {status_color};">{status_emoji}</div>
        <div class="status-details">
            Last signal: {last_signal} • Next refresh: {refresh_display}s
        </div>
    </div>
    """, unsafe_allow_html=True)

with tabs[1]:
    # Account tab - Balance removed, now only shows in sidebar
    st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                border: 1px solid var(--border-color); text-align: center;">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">
            📊 Account Information
            </h4>
        <p style="color: var(--text-secondary); margin: 0;">
            Balance information is now displayed in the sidebar for easy access.
        </p>
        </div>
        """, unsafe_allow_html=True)

with tabs[2]:
    # Show real trading data if available, otherwise show simulated data
    if not paper and st.session_state['real_account_data'] and st.session_state['real_account_data'].get('trades'):
        # Real trading history
        real_trades = st.session_state['real_account_data']['trades']
        if real_trades:
            st.markdown("""
            <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                        border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                    📋 Real Trading History
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Display real trades
            for trade in real_trades[:10]:  # Show last 10 real trades
                symbol = trade.get('symbol', 'Unknown')
                side = trade.get('side', 'Unknown')
                qty = trade.get('qty', 0)
                price = trade.get('price', 0)
                timestamp = trade.get('timestamp', 0)
                
                # Format timestamp
                try:
                    if timestamp:
                        trade_time = pd.to_datetime(timestamp, unit='ms').strftime('%H:%M:%S')
                    else:
                        trade_time = 'Unknown'
                except:
                    trade_time = 'Unknown'
                
                st.markdown(f"""
                <div style="background: var(--card-bg); padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0; border-left: 4px solid var(--accent-blue);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: var(--text-primary); font-weight: 600;">{symbol}</span>
                        <span style="color: var(--text-secondary); font-size: 0.9rem;">{trade_time}</span>
                    </div>
                    <div style="color: var(--text-secondary); font-size: 0.9rem;">
                        {side} • Qty: {qty} • Price: ${float(price):,.4f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                        border: 1px solid var(--border-color); text-align: center;">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    📊 No Real Trades Yet
                </h4>
                <p style="color: var(--text-secondary); margin: 0;">
                    Start real trading to see your trade history here.
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Simulated trading history
        if st.session_state['trades']:
            st.markdown("""
            <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                        border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                    📋 Simulated Trade History
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            trades_df = pd.DataFrame(st.session_state['trades'])
            if not trades_df.empty:
                trades_df = trades_df.tail(20)  # Show last 20 trades
                st.markdown(trades_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                        border: 1px solid var(--border-color); text-align: center;">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    📊 No Trades Yet
                </h4>
                <p style="color: var(--text-secondary); margin: 0;">
                    Start trading to see your trade history here.
                </p>
            </div>
            """, unsafe_allow_html=True)

with tabs[3]:
    try:
        tk = _exec.fetch_ticker(symbol)
        last = tk.get('last') or tk.get('close') or 0.0
        high24 = tk.get('high') or 0.0
        low24 = tk.get('low') or 0.0
        base_volume = tk.get('baseVolume') or 0.0
        quote_volume = tk.get('quoteVolume') or 0.0
        market_cap = tk.get('info', {}).get('marketCap') if isinstance(tk.get('info'), dict) else None
        
        def fmt_m(x):
            try:
                x = float(x)
                return f"${x/1_000_000:,.2f}M"
            except Exception:
                return "N/A"
        
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color);">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                📈 Market Data
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        colm1, colm2 = st.columns(2)
        with colm1:
            st.metric("Last Price", f"${float(last):,.4f}")
            st.metric("24h Change", f"{price_change_24h_pct:+.2f}%", f"{price_change_24h:+.4f}")
            st.metric("24h High", f"${float(high24):,.4f}")
            st.metric("24h Low", f"${float(low24):,.4f}")
        with colm2:
            st.metric("Base Vol (24h)", f"{float(base_volume):,.0f}")
            st.metric("Quote Vol (24h)", f"{float(quote_volume):,.0f}")
            st.metric("Market Cap", fmt_m(market_cap) if market_cap else "N/A")
    except Exception as e:
        st.error(f"Unable to fetch market data: {e}")

with tabs[4]:
    # Use the new signal system if available
    if 'final_buy' in df.columns and 'final_sell' in df.columns:
        buy_signal_now = bool(df['final_buy'].iat[-1]) if len(df) > 0 else False
        sell_signal_now = bool(df['final_sell'].iat[-1]) if len(df) > 0 else False
        
        if buy_signal_now:
            # Determine which trigger fired
            if 'wt_buy' in df.columns and bool(df['wt_buy'].iat[-1]):
                sig_badge = "WT Green Dot"
                signal_description = "Highest Priority"
                sig_color = "#00ff88"
            elif 'momentum_buy' in df.columns and bool(df['momentum_buy'].iat[-1]):
                sig_badge = "Momentum BUY"
                signal_description = "Medium Priority"
                sig_color = "#22cc88"
            elif 'rsi_buy' in df.columns and bool(df['rsi_buy'].iat[-1]):
                sig_badge = "RSI BUY"
                signal_description = "Low Priority"
                sig_color = "#88cc22"
            else:
                sig_badge = "BUY Signal"
                sig_color = "#22cc88"
                signal_description = ""
        elif sell_signal_now:
            # Determine which trigger fired
            if 'wt_sell' in df.columns and bool(df['wt_sell'].iat[-1]):
                sig_badge = "WT Red Dot"
                signal_description = "Highest Priority"
                sig_color = "#ff4444"
            elif 'momentum_sell' in df.columns and bool(df['momentum_sell'].iat[-1]):
                sig_badge = "Momentum SELL"
                signal_description = "Medium Priority"
                sig_color = "#cc2222"
            elif 'rsi_sell' in df.columns and bool(df['rsi_sell'].iat[-1]):
                sig_badge = "RSI SELL"
                signal_description = "Low Priority"
                sig_color = "#cc8822"
            else:
                sig_badge = "SELL Signal"
                sig_color = "#cc2222"
                signal_description = ""
        else:
            sig_badge = "No Signal"
            sig_color = "#a0aec0"
            signal_description = ""
    else:
        # Fallback to old system
        signal_now = bool(df['signal'].iat[-1]) if len(df) > 0 else False
        sig_badge = "BUY Signal Active" if signal_now else "No Signal"
        sig_color = "#48bb78" if signal_now else "#a0aec0"
        signal_description = ""
    
    # Get current RSI and WT values for display
    current_rsi = float(df['rsi'].iat[-1]) if len(df) > 0 and 'rsi' in df.columns else 0.0
    current_wt1 = float(df['wt1'].iat[-1]) if len(df) > 0 and 'wt1' in df.columns else 0.0
    current_wt2 = float(df['wt2'].iat[-1]) if len(df) > 0 and 'wt2' in df.columns else 0.0
    
    # Determine signal strength indicator
    signal_strength = "🟢" if sig_badge.startswith("WT") else "🟡" if "Momentum" in sig_badge else "🔴" if "RSI" in sig_badge else "⚪"
    
    # Create professional signal display using Streamlit components
    st.markdown("### 📊 Trading Signal Analysis")
    
    # Signal strength indicator
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Current Status:** {sig_badge}")
    with col2:
        st.markdown(f"**Priority:** {signal_strength}")
    
    # Main signal info in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📈 Current Signal**")
        signal_html = f"<p style='color: #888; margin: 0.5rem 0 0 0; font-size: 0.9rem;'>{signal_description}</p>" if signal_description else ""
        st.markdown(f"<div style='padding: 1rem; background-color: #1e1e1e; border-radius: 8px; border-left: 4px solid {sig_color};'>"
                   f"<h3 style='color: {sig_color}; margin: 0;'>{sig_badge}</h3>"
                   f"{signal_html}"
                   f"</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("**⏰ Last Updated**")
        st.markdown(f"<div style='padding: 1rem; background-color: #1e1e1e; border-radius: 8px; border-left: 4px solid #4CAF50;'>"
                   f"<h3 style='color: #fff; margin: 0;'>{pd.Timestamp.now().strftime('%H:%M:%S')}</h3>"
                   f"<p style='color: #888; margin: 0.5rem 0 0 0; font-size: 0.9rem;'>{pd.Timestamp.now().strftime('%Y-%m-%d')}</p>"
                   f"</div>", unsafe_allow_html=True)
    
    # Technical indicators
    st.markdown("**📊 Technical Indicators**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rsi_color = '#4CAF50' if current_rsi > 50 else '#f44336'
        st.markdown(f"<div style='padding: 1rem; background-color: #1e1e1e; border-radius: 8px; text-align: center;'>"
                   f"<p style='color: #888; margin: 0; font-size: 0.8rem;'>RSI</p>"
                   f"<h2 style='color: {rsi_color}; margin: 0;'>{current_rsi:.1f}</h2>"
                   f"</div>", unsafe_allow_html=True)
    
    with col2:
        wt1_color = '#4CAF50' if current_wt1 > current_wt2 else '#f44336'
        st.markdown(f"<div style='padding: 1rem; background-color: #1e1e1e; border-radius: 8px; text-align: center;'>"
                   f"<p style='color: #888; margin: 0; font-size: 0.8rem;'>WT1</p>"
                   f"<h2 style='color: {wt1_color}; margin: 0;'>{current_wt1:.1f}</h2>"
                   f"</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"<div style='padding: 1rem; background-color: #1e1e1e; border-radius: 8px; text-align: center;'>"
                   f"<p style='color: #888; margin: 0; font-size: 0.8rem;'>WT2</p>"
                   f"<h2 style='color: #fff; margin: 0;'>{current_wt2:.1f}</h2>"
                   f"</div>", unsafe_allow_html=True)
    
    # Signal History Section
    st.markdown("---")
    st.markdown("### 📋 Recent Signal History")
    
    # Get recent signals from DataFrame
    if 'final_buy' in df.columns and 'final_sell' in df.columns:
        # Combine buy and sell signals with details
        signal_history = []
        
        # Process recent data (last 50 candles)
        recent_data = df.tail(50).copy()
        
        for idx, row in recent_data.iterrows():
            signal_info = None
            timestamp = row['timestamp']
            price = row['close']
            
            # Check which signal triggered
            if row.get('final_buy', False):
                if row.get('wt_buy', False):
                    signal_type = "WT Green Dot"
                    priority = "Highest"
                    color = "#00ff88"
                elif row.get('momentum_buy', False):
                    signal_type = "Momentum BUY"
                    priority = "Medium"
                    color = "#22cc88"
                elif row.get('rsi_buy', False):
                    signal_type = "RSI BUY"
                    priority = "Low"
                    color = "#88cc22"
                else:
                    signal_type = "BUY"
                    priority = "Standard"
                    color = "#22cc88"
                
                signal_info = {
                    'time': timestamp,
                    'signal': signal_type,
                    'type': 'BUY',
                    'price': price,
                    'priority': priority,
                    'color': color,
                    'rsi': row.get('rsi', 0),
                    'wt1': row.get('wt1', 0),
                    'wt2': row.get('wt2', 0)
                }
                
            elif row.get('final_sell', False):
                if row.get('wt_sell', False):
                    signal_type = "WT Red Dot"
                    priority = "Highest"
                    color = "#ff4444"
                elif row.get('momentum_sell', False):
                    signal_type = "Momentum SELL"
                    priority = "Medium"
                    color = "#cc2222"
                elif row.get('rsi_sell', False):
                    signal_type = "RSI SELL"
                    priority = "Low"
                    color = "#cc8822"
                else:
                    signal_type = "SELL"
                    priority = "Standard"
                    color = "#cc2222"
                
                signal_info = {
                    'time': timestamp,
                    'signal': signal_type,
                    'type': 'SELL',
                    'price': price,
                    'priority': priority,
                    'color': color,
                    'rsi': row.get('rsi', 0),
                    'wt1': row.get('wt1', 0),
                    'wt2': row.get('wt2', 0)
                }
            
            if signal_info:
                signal_history.append(signal_info)
        
        if signal_history:
            # Show last 10 signals
            for sig in signal_history[-10:]:
                time_str = sig['time'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(sig['time'], 'strftime') else str(sig['time'])
                
                st.markdown(f"""
                <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid {sig['color']};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: {sig['color']}; font-weight: 700; font-size: 1.1rem;">{sig['signal']}</span>
                        <span style="color: var(--text-secondary); font-size: 0.85rem;">{time_str}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; font-size: 0.85rem;">
                        <div>
                            <span style="color: var(--text-secondary);">Price:</span>
                            <span style="color: var(--text-primary); font-weight: 600;">${float(sig['price']):,.4f}</span>
                        </div>
                        <div>
                            <span style="color: var(--text-secondary);">Priority:</span>
                            <span style="color: var(--text-primary); font-weight: 600;">{sig['priority']}</span>
                        </div>
                        <div>
                            <span style="color: var(--text-secondary);">RSI:</span>
                            <span style="color: var(--text-primary); font-weight: 600;">{float(sig['rsi']):.1f}</span>
                        </div>
                        <div>
                            <span style="color: var(--text-secondary);">WT1/WT2:</span>
                            <span style="color: var(--text-primary); font-weight: 600;">{float(sig['wt1']):.1f}/{float(sig['wt2']):.1f}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No signals generated in recent history")
    else:
        st.info("Signal history not available")

with tabs[5]:
    if st.session_state['arb_running']:
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color);">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                🔍 Arbitrage Scanner
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # Build simple exchanges map for scanner
            import ccxt
            ex_map = {}
            ex_map['binance'] = ccxt.binance()
            ex_map['bybit'] = ccxt.bybit()
            ex_map['mexc'] = ccxt.mexc()
            
            scanner = ArbitrageEngine(ex_map, [symbol], threshold_bps=10.0)
            opps = scanner.run_once()
            
            if opps:
                for o in opps:
                    st.markdown(f"""
                    <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                                border: 1px solid var(--border-color); margin-bottom: 0.5rem;">
                        <div style="color: var(--accent-green); font-weight: 600; margin-bottom: 0.5rem;">
                            💰 Arbitrage Opportunity
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.9rem;">
                            <strong>{o['symbol']}</strong><br/>
                            Buy on: {o['buy_on']}<br/>
                            Sell on: {o['sell_on']}<br/>
                            Spread: <span style="color: var(--accent-green); font-weight: 600;">{o['spread']*100:.2f}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                            border: 1px solid var(--border-color); text-align: center;">
                    <div style="color: var(--text-secondary);">
                        🔍 No arbitrage opportunities found
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Arbitrage scanner error: {e}")
    else:
        st.markdown("""
        <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                    border: 1px solid var(--border-color); text-align: center;">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                🔍 Arbitrage Scanner
            </h4>
            <p style="color: var(--text-secondary); margin: 0;">
                Scanner is currently disabled. Enable it in the sidebar to start scanning for arbitrage opportunities.
            </p>
        </div>
        """, unsafe_allow_html=True)

with tabs[6]:
    # Order Management Tab
    st.markdown("""
    <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                border: 1px solid var(--border-color);">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            ⚙️ Order Management
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    if not paper and st.session_state['real_account_data'] and st.session_state['real_account_data'].get('orders'):
        # Real order management
        real_orders = st.session_state['real_account_data']['orders']
        if real_orders:
            st.markdown(f"**Open Orders ({len(real_orders)}):**")
            
            for order in real_orders:
                order_id = order.get('orderId', 'Unknown')
                symbol = order.get('symbol', 'Unknown')
                side = order.get('side', 'Unknown')
                qty = order.get('qty', 0)
                price = order.get('price', 0)
                status = order.get('orderStatus', 'Unknown')
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="background: var(--card-bg); padding: 0.75rem; border-radius: 6px; margin: 0.5rem 0;">
                        <div style="color: var(--text-primary); font-weight: 600;">{symbol} • {side}</div>
                        <div style="color: var(--text-secondary); font-size: 0.9rem;">
                            Qty: {qty} • Price: ${float(price):,.4f} • Status: {status}
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.8rem;">
                            ID: {order_id}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_{order_id}"):
                        with st.spinner("Canceling order..."):
                            try:
                                result = _exec.cancel_order(order_id, symbol)
                                if result.get('status') != 'error':
                                    st.success(f"Order {order_id} canceled!")
                                    # Refresh account data
                                    account_data = _exec.get_account_info()
                                    st.session_state['real_account_data'] = account_data
                                    st.rerun()
                                else:
                                    st.error(f"Failed to cancel order: {result.get('error', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Error canceling order: {e}")
                
                with col3:
                    if st.button("🔄 Refresh", key=f"refresh_{order_id}"):
                        with st.spinner("Refreshing order data..."):
                            try:
                                account_data = _exec.get_account_info()
                                st.session_state['real_account_data'] = account_data
                                st.success("Order data refreshed!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error refreshing data: {e}")
        else:
            st.markdown("""
            <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                        border: 1px solid var(--border-color); text-align: center;">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">📋 No Open Orders</h4>
                <p style="color: var(--text-secondary); margin: 0;">No orders to manage</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Paper trading or no real data
        if paper:
            st.markdown("""
            <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                        border: 1px solid var(--border-color); text-align: center;">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">📝 Paper Trading Mode</h4>
                <p style="color: var(--text-secondary); margin: 0;">Order management not available in paper trading mode</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                        border: 1px solid var(--border-color); text-align: center;">
                <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">🔐 Real Trading Required</h4>
                <p style="color: var(--text-secondary); margin: 0;">Enable real trading and fetch account data to manage orders</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Manual order placement (for advanced users)
    if not paper and st.session_state['account_validation'] and st.session_state['account_validation']['valid']:
        st.markdown("---")
        st.markdown("**Manual Order Placement:**")
        
        col1, col2 = st.columns(2)
        with col1:
            manual_symbol = st.text_input("Symbol", value=symbol, key="manual_symbol")
            manual_side = st.selectbox("Side", ["buy", "sell"], key="manual_side")
        with col2:
            manual_qty = st.number_input("Quantity", min_value=0.001, value=0.001, step=0.001, key="manual_qty")
            manual_leverage = st.number_input("Leverage", min_value=1, max_value=100, value=1, key="manual_leverage")
        
        if st.button("📤 Place Manual Order", key="place_manual_order"):
            if manual_symbol and manual_qty > 0:
                with st.spinner("Placing order..."):
                    try:
                        result = _exec.place_market_order(manual_symbol, manual_side, manual_qty, int(manual_leverage))
                        if result.get('status') != 'error':
                            st.success(f"Order placed successfully! ID: {result.get('id', 'Unknown')}")
                            # Refresh account data
                            account_data = _exec.get_account_info()
                            st.session_state['real_account_data'] = account_data
                            st.rerun()
                        else:
                            st.error(f"Failed to place order: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error placing order: {e}")
            else:
                st.error("Please fill in all required fields")

with tabs[7]:
    st.markdown('<div class="section-header">📊 Comprehensive Backtesting Metrics</div>', unsafe_allow_html=True)
    
    # Initialize metrics calculator
    metrics_calculator = ComprehensiveMetricsCalculator()

    # Enhanced Backtest Processing
    if st.session_state.get('enhanced_backtest_trigger'):
        st.session_state['enhanced_backtest_trigger'] = False
        params = st.session_state.get('enhanced_backtest_params', {})
        
        with st.spinner(f"Running enhanced backtest for {params.get('ticker', 'N/A')}..."):
            try:
                # Initialize enhanced backtester
                enhanced_bt = EnhancedBacktester()
                
                # Run enhanced backtest with new trading trigger system
                bt_results = enhanced_bt.run_enhanced_backtest(
                    symbol=params['ticker'],
                    timeframe=params['timeframe'],
                    start_date=params['start_date'],
                    end_date=params['end_date'],
                    initial_capital=10000.0,
                    risk_per_trade=0.02,
                    daily_loss_limit=0.05,
                    rsi_length=14,
                    rsi_oversold=params['rsi_sell_threshold'],
                    rsi_overbought=params['rsi_buy_threshold'],
                    wt_channel_length=10,
                    wt_average_length=21,
                    tp1_multiplier=1.5,
                    tp2_multiplier=2.0,
                    runner_multiplier=3.0,
                    data_source='auto'
                )
                
                # Store results in session state
                st.session_state['enhanced_backtest_results'] = bt_results
                st.session_state['trades'] = bt_results.get('trades', [])
                
                # Extract equity curve for metrics
                daily_summaries = bt_results.get('daily_summaries', [])
                if daily_summaries:
                    equity_curve = [ds['current_capital'] for ds in daily_summaries]
                    st.session_state.setdefault('account', {'equity': []})
                    st.session_state['account']['equity'] = equity_curve
                
                # Display quick summary
                metrics = bt_results.get('metrics', {})
                st.success(f"✅ Enhanced backtest completed!")
                st.info(f"**{params['ticker']}** ({params['timeframe']}) | "
                       f"Trades: {metrics.get('total_trades', 0)} | "
                       f"Win Rate: {metrics.get('win_rate', 0):.1%} | "
                       f"Return: {metrics.get('total_return', 0):.1%}")
                
            except Exception as e:
                st.error(f"Enhanced backtest error: {e}")
                import traceback
                st.error(f"Details: {traceback.format_exc()}")
    
    # Optional: run backtest on demand when triggered from sidebar
    if st.session_state.get('backtest_trigger'):
        st.session_state['backtest_trigger'] = False
        with st.spinner("Running backtest with current settings..."):
            try:
                # Prepare data and signals for backtest
                df_bt = df.copy() if 'df' in locals() else None
                if df_bt is not None and not df_bt.empty:
                    # Ensure a boolean entry signal column exists
                    if 'signal' not in df_bt.columns:
                        # Fallback: generate weighted signals if available
                        try:
                            from indicators.weighted_signals import generate_weighted_signals
                            df_bt['signal'] = generate_weighted_signals(df_bt).astype(bool)
                        except Exception:
                            df_bt['signal'] = False
                    # Run enhanced backtest if available, else core
                    try:
                        from backtester.enhanced_backtester import run_enhanced_backtest
                        bt_res = run_enhanced_backtest(
                            df=df_bt,
                            entry_col='signal',
                            initial_cap=float(st.session_state.get('initial_capital', 10000.0)),
                            risk_per_trade=float(st.session_state.get('risk_per_trade', 0.01)),
                            stop_loss_pct=float(st.session_state.get('stop_loss_pct', 0.03)),
                            take_profit_pct1=float(st.session_state.get('take_profit_pct1', 0.03)),
                            take_profit_pct2=float(st.session_state.get('take_profit_pct2', 0.06)),
                            max_bars_in_trade=int(st.session_state.get('max_bars_in_trade', 100)),
                            fee_rate=0.0004,
                            daily_breaker_active=bool(st.session_state.get('daily_breaker_active', False)),
                            daily_pnl_limit=float(st.session_state.get('daily_loss_limit', -0.05)),
                        )
                    except Exception:
                        from backtester.core import run_backtest as run_basic_backtest
                        bt_res = run_basic_backtest(df_bt, entry_col='signal')

                    # Persist into session for metrics tab
                    st.session_state['trades'] = bt_res.get('trades', [])
                    st.session_state.setdefault('account', {'equity': []})
                    st.session_state['account']['equity'] = bt_res.get('df', {}).get('equity', []) if isinstance(bt_res.get('df'), dict) else (bt_res.get('df')['equity'].tolist() if bt_res.get('df') is not None and 'equity' in bt_res.get('df').columns else st.session_state['account'].get('equity', []))
                    st.success("Backtest completed. Open '📊 Comprehensive Backtesting Metrics' tab.")
                else:
                    st.warning("No market data available to backtest. Load data first.")
            except Exception as e:
                st.error(f"Backtest error: {e}")
    
    # Check if we have trading data
    if 'trades' in st.session_state and st.session_state['trades']:
        trades = st.session_state['trades']
        account = st.session_state.get('account', {'equity': [10000]})
        equity_curve = pd.Series(account['equity'])
        
        # Calculate comprehensive metrics
        with st.spinner("Calculating comprehensive metrics..."):
            try:
                metrics = metrics_calculator.calculate_comprehensive_metrics(
                    equity_curve=equity_curve,
                    trades=trades,
                    initial_capital=initial_cap,
                    risk_free_rate=0.02
                )
                
                # Display metrics report
                st.markdown("### 📈 Performance Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Return", f"{metrics.total_return:.2%}")
                    st.metric("Win Rate", f"{metrics.win_rate:.2%}")
                
                with col2:
                    st.metric("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}")
                    st.metric("Max Drawdown", f"{metrics.max_drawdown:.2%}")
                
                with col3:
                    st.metric("Profit Factor", f"{metrics.profit_factor:.2f}")
                    st.metric("Total Trades", f"{metrics.total_trades}")
                
                with col4:
                    st.metric("Calmar Ratio", f"{metrics.calmar_ratio:.2f}")
                    st.metric("Recovery Factor", f"{metrics.recovery_factor:.2f}")
                
                # Detailed metrics
                st.markdown("### 📋 Detailed Metrics")
                
                # Generate and display comprehensive report
                report = metrics_calculator.generate_comprehensive_report(metrics)
                st.text(report)
                
                # Export functionality
                st.markdown("### 💾 Export Metrics")
                if st.button("📥 Export Metrics to CSV"):
                    filename = f"backtest_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    metrics_calculator.export_metrics_to_csv(metrics, filename)
                    st.success(f"Metrics exported to {filename}")
                
            except Exception as e:
                st.error(f"Error calculating metrics: {str(e)}")
    else:
        st.info("No trading data available. Run some trades to see comprehensive metrics.")
    
    # Multi-timeframe analysis results
    if enable_mtf and 'mtf_analyzer' in locals():
        st.markdown("### 🔄 Multi-Timeframe Analysis Results")
        
        mtf_summary = mtf_analyzer.get_timeframe_summary()
        
        st.markdown(f"**Primary Timeframe:** {mtf_summary['primary_timeframe']}")
        st.markdown(f"**Total Timeframes:** {mtf_summary['total_timeframes']}")
        st.markdown(f"**Enabled Timeframes:** {mtf_summary['enabled_timeframes']}")
        
        # Display timeframe configurations
        tf_df = pd.DataFrame(mtf_summary['timeframes'])
        st.markdown("**Timeframe Configuration:**")
        st.markdown(tf_df.to_html(escape=False, index=False), unsafe_allow_html=True)

with tabs[8]:
    # Advanced Backtester Tab
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(0, 150, 255, 0.1)); 
                padding: 1.5rem; border-radius: var(--border-radius); border: 2px solid var(--accent-green);">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            🧪 Advanced Backtester - Professional Trading Strategy Analysis
        </h4>
        <p style="margin: 0; color: var(--text-secondary); font-size: 0.9rem;">
            Comprehensive backtesting with 40+ metrics, multiple timeframes, and real exchange data
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Two columns layout
    col_config, col_results = st.columns([1, 2])
    
    with col_config:
        st.markdown("### ⚙️ Configuration")
        
        # Data Source Selection
        data_source = st.selectbox(
            "📊 Data Source",
            ["Exchange API", "Yahoo Finance", "CSV File"],
            index=1,
            help="Choose your data source for backtesting"
        )
        
        # Symbol Input
        if data_source == "CSV File":
            uploaded_file = st.file_uploader("Upload CSV", type=['csv'], help="CSV with columns: timestamp, open, high, low, close, volume")
            if uploaded_file:
                df_backtest = pd.read_csv(uploaded_file, parse_dates=['timestamp'])
                selected_symbol = "Custom"
            else:
                selected_symbol = None
                df_backtest = pd.DataFrame()
        else:
            selected_symbol = st.text_input(
                "🎯 Symbol",
                value="BTCUSDT" if data_source == "Exchange API" else "BTC-USD",
                help="Trading symbol (BTCUSDT, AAPL, etc.)"
            )
        
        # Exchange Selection (if using Exchange API)
        if data_source == "Exchange API":
            # Get sidebar exchange from session state
            sidebar_ex = st.session_state.get('selected_exchange', "binance")
            # Support ALL exchanges from sidebar
            exchange_options = ["binance", "bybit", "mexc", "alpaca", "coinbase", "kraken"]
            try:
                default_idx = exchange_options.index(sidebar_ex) if sidebar_ex in exchange_options else 0
            except:
                default_idx = 0
            exchange_name = st.selectbox(
                "Exchange",
                exchange_options,
                index=default_idx,
                help="Using same exchange from sidebar, can override here"
            )
        
        # Timeframe Selection
        timeframe_options = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '1w']
        selected_timeframe = st.selectbox(
            "⏰ Timeframe",
            timeframe_options,
            index=5  # Default to 1h
        )
        
        # Date Range
        st.markdown("**📅 Period**")
        col_start, col_end = st.columns(2)
        with col_start:
            start_days = st.number_input("Days Back", min_value=7, max_value=365, value=90, step=7)
        with col_end:
            end_date = st.date_input("End Date", value=datetime.now())
        
        start_date = end_date - timedelta(days=start_days)
        
        # Capital & Risk Settings
        st.markdown("### 💰 Capital & Risk")
        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=100.0,
            max_value=1000000.0,
            value=10000.0,
            step=1000.0
        )
        
        risk_per_trade = st.slider(
            "Risk Per Trade (%)",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5
        ) / 100
        
        # Stop Loss & Take Profit
        st.markdown("### 🎯 Risk Management")
        col_sl, col_tp = st.columns(2)
        with col_sl:
            stop_loss_pct = st.number_input("Stop Loss (%)", min_value=0.5, max_value=20.0, value=3.0, step=0.5) / 100
        with col_tp:
            take_profit_pct = st.number_input("Take Profit (%)", min_value=1.0, max_value=50.0, value=6.0, step=1.0) / 100
        
        # Commission/Fee
        fee_rate = st.number_input("Commission/Fee (%)", min_value=0.0, max_value=2.0, value=0.04, step=0.01) / 100
        
        # Signal Parameters
        st.markdown("### 📊 Signal Parameters")
        signal_type = st.selectbox(
            "Strategy",
            ["RSI + WaveTrend (Auto)", "EMA Crossover", "RSI + Bollinger Bands", "Custom Signals"],
            index=0
        )
        
        # RSI Settings
        if "RSI" in signal_type:
            col_rsi_len, col_rsi_ov = st.columns(2)
            with col_rsi_len:
                rsi_length = st.number_input("RSI Length", min_value=5, max_value=50, value=14, step=1)
            with col_rsi_ov:
                rsi_oversold_th = st.number_input("RSI Oversold", min_value=10, max_value=40, value=30, step=1)
        
        # WaveTrend Settings
        if "WaveTrend" in signal_type:
            col_wt_ch, col_wt_avg = st.columns(2)
            with col_wt_ch:
                wt_channel = st.number_input("WT Channel", min_value=5, max_value=30, value=10, step=1)
            with col_wt_avg:
                wt_average = st.number_input("WT Average", min_value=10, max_value=50, value=21, step=1)
        
        # Max Trade Duration
        max_bars_in_trade = st.number_input(
            "Max Trade Duration (bars)",
            min_value=10,
            max_value=500,
            value=100,
            step=10
        )
        
        # Run Button
        run_bt_button = st.button(
            "🚀 Run Backtest",
            type="primary",
            use_container_width=True,
            help="Start comprehensive backtesting analysis"
        )
    
    with col_results:
        st.markdown("### 📈 Results")
        
        # Results Display Area
        if run_bt_button:
            with st.spinner("Running comprehensive backtest analysis..."):
                try:
                    # Fetch data
                    if data_source == "Exchange API":
                        from executor.ccxt_executor import CCXTExecutor
                        executor = CCXTExecutor(exchange_name=exchange_name, paper=True)
                        
                        # Calculate appropriate limit based on timeframe
                        if 'h' in selected_timeframe:
                            limit = min(start_days * 24, 500)  # Max 500 candles
                        elif 'd' in selected_timeframe:
                            limit = min(start_days, 365)  # Max 365 days
                        elif 'w' in selected_timeframe:
                            limit = min(start_days // 7, 100)  # Max 100 weeks
                        else:
                            limit = 500  # Default for minutes
                        
                        df_backtest = executor.fetch_ohlcv_df(selected_symbol, selected_timeframe, limit=limit)
                        if df_backtest.empty:
                            st.error(f"Failed to fetch data from {exchange_name}. Check symbol '{selected_symbol}' and timeframe '{selected_timeframe}'")
                            executor.close()
                        else:
                            st.success(f"✓ Fetched {len(df_backtest)} candles from {exchange_name}")
                            executor.close()
                    elif data_source == "Yahoo Finance":
                        # Convert symbol format for yfinance
                        yf_symbol = selected_symbol.replace("USDT", "-USD") if "USDT" in selected_symbol else selected_symbol
                        period = "max" if start_days > 365 else f"{start_days}d"
                        
                        # Map timeframe to yfinance interval
                        tf_map = {
                            '1m': '1m', '3m': '2m', '5m': '5m', '15m': '15m', '30m': '30m',
                            '1h': '1h', '2h': '2h', '4h': '4h', '6h': '1h', '12h': '1h',
                            '1d': '1d', '1w': '1wk'
                        }
                        interval = tf_map.get(selected_timeframe, '1h')
                        
                        df_backtest = yf.download(yf_symbol, period=period, interval=interval, progress=False)
                        if not df_backtest.empty:
                            df_backtest = df_backtest.reset_index()
                            df_backtest.columns = [col if col != 'Datetime' else 'timestamp' for col in df_backtest.columns]
                            df_backtest['timestamp'] = pd.to_datetime(df_backtest['timestamp'])
                    
                    if df_backtest.empty:
                        st.error("No data available for backtesting")
                    else:
                        # Calculate indicators
                        df_backtest['rsi'] = rsi(df_backtest['close'], length=rsi_length if 'rsi_length' in locals() else 14)
                        
                        # WaveTrend calculation
                        if 'high' in df_backtest.columns and 'low' in df_backtest.columns:
                            hlc3 = (df_backtest['high'] + df_backtest['low'] + df_backtest['close']) / 3
                        else:
                            hlc3 = df_backtest['close']
                        
                        wt_result = wavetrend(hlc3, channel_length=wt_channel if 'wt_channel' in locals() else 10, 
                                             average_length=wt_average if 'wt_average' in locals() else 21)
                        df_backtest[['wt1', 'wt2']] = wt_result
                        
                        # Generate signals
                        from signals.engine import align_signals
                        df_backtest['signal'] = align_signals(
                            df_backtest,
                            rsi_col='rsi',
                            wt1_col='wt1',
                            wt2_col='wt2',
                            webhook_col=None,
                            rsi_oversold_threshold=rsi_oversold_th if 'rsi_oversold_th' in locals() else 30,
                            require_webhook=False
                        )
                        
                        # Run backtest
                        from backtester.core import run_backtest
                        bt_results = run_backtest(
                            df_backtest,
                            entry_col='signal',
                            initial_cap=initial_capital,
                            risk_per_trade=risk_per_trade,
                            stop_loss_pct=stop_loss_pct,
                            take_profit_pct=take_profit_pct,
                            max_bars_in_trade=max_bars_in_trade,
                            fee_rate=fee_rate
                        )
                        
                        # Display results
                        metrics = bt_results.get('metrics', {})
                        
                        # Key Metrics
                        st.success("✅ Backtest Complete!")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Return", f"{metrics.get('total_return', 0):.2%}")
                            st.metric("Win Rate", f"{metrics.get('win_rate', 0):.2%}")
                        with col2:
                            st.metric("Total Trades", f"{metrics.get('total_trades', 0)}")
                            st.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
                        with col3:
                            st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}")
                            st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0):.2%}")
                        with col4:
                            st.metric("Avg Win", f"${metrics.get('avg_win', 0):.2f}")
                            st.metric("Avg Loss", f"${metrics.get('avg_loss', 0):.2f}")
                        
                        # Equity Curve Chart
                        if 'equity_curve' in bt_results:
                            fig_equity = go.Figure()
                            fig_equity.add_trace(go.Scatter(
                                x=bt_results['equity_curve'].index,
                                y=bt_results['equity_curve'],
                                mode='lines',
                                name='Equity',
                                line=dict(color='#00ff88', width=2)
                            ))
                            fig_equity.update_layout(
                                title="Equity Curve",
                                xaxis_title="Time",
                                yaxis_title="Portfolio Value ($)",
                                template='plotly_dark',
                                height=300
                            )
                            st.plotly_chart(fig_equity, use_container_width=True)
                        
                        # Trade List
                        if 'trades' in bt_results and bt_results['trades']:
                            st.markdown("**📋 Recent Trades:**")
                            trades_df = pd.DataFrame(bt_results['trades'][-20:])  # Last 20 trades
                            if not trades_df.empty:
                                st.dataframe(trades_df, use_container_width=True, height=300)
                            
                except Exception as e:
                    st.error(f"Backtest error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        else:
            st.info("👈 Configure settings on the left and click 'Run Backtest' to start analysis")
            
            # Show sample metrics
            st.markdown("**📊 Sample Metrics Available:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                - Total Return
                - Win Rate  
                - Total Trades
                - Profit Factor
                - Expectancy
                """)
            with col2:
                st.markdown("""
                - Sharpe Ratio
                - Sortino Ratio
                - Calmar Ratio
                - Max Drawdown
                - Recovery Factor
                """)
            with col3:
                st.markdown("""
                - Average Win/Loss
                - Largest Win/Loss
                - Consecutive Wins/Losses
                - Trade Duration
                - Monthly Returns
                """)

with tabs[10]:
    # Error Log Tab
    st.markdown("""
    <div style="background: var(--secondary-bg); padding: 1.5rem; border-radius: var(--border-radius); 
                border: 1px solid var(--border-color);">
        <h4 style="margin: 0 0 1rem 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            🚨 Error Log & Diagnostics
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Error log controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("**Recent Errors:**")
    
    with col2:
        if st.button("🔄 Refresh Log", key="refresh_error_log"):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Log", key="clear_error_log"):
            error_handler.clear_errors()
            st.success("Error log cleared!")
            st.rerun()
    
    # Display recent errors
    recent_errors = error_handler.get_recent_errors(20)
    
    if recent_errors:
        st.markdown(f"**Showing {len(recent_errors)} recent errors:**")
        
        for error in reversed(recent_errors):  # Show newest first
            error_time = error['timestamp']
            error_type = error['type']
            error_message = error['message']
            error_id = error['id']
            
            # Color code by error type
            if "API" in error_type:
                color = "var(--accent-red)"
                icon = "🔌"
            elif "Validation" in error_type:
                color = "var(--accent-blue)"
                icon = "⚠️"
            elif "Trading" in error_type:
                color = "var(--accent-green)"
                icon = "📈"
            else:
                color = "var(--text-secondary)"
                icon = "❓"
            
            with st.expander(f"{icon} {error_type} - {error_time[:19]}", expanded=False):
                st.markdown(f"**Error ID:** `{error_id}`")
                st.markdown(f"**Message:** {error_message}")
                
                if error.get('context'):
                    st.markdown("**Context:**")
                    for key, value in error['context'].items():
                        st.markdown(f"• {key}: {value}")
                
                # Show traceback for debugging
                if st.checkbox("Show technical details", key=f"show_trace_{error_id}"):
                    st.code(error.get('traceback', 'No traceback available'), language='python')
    else:
        st.markdown("""
        <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; 
                    border: 1px solid var(--border-color); text-align: center;">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">✅ No Errors</h4>
            <p style="color: var(--text-secondary); margin: 0;">No errors have been logged recently</p>
        </div>
        """, unsafe_allow_html=True)
    
    # System diagnostics
    st.markdown("---")
    st.markdown("**System Diagnostics:**")
    
    # Check system status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Check if trading is active
        trading_status = "🟢 Active" if st.session_state.get('is_trading', False) else "🔴 Inactive"
        st.metric("Trading Status", trading_status)
    
    with col2:
        # Check account validation
        validation = st.session_state.get('account_validation')
        if validation and validation.get('valid'):
            validation_status = "🟢 Validated"
        elif validation:
            validation_status = "🔴 Failed"
        else:
            validation_status = "⚪ Not Checked"
        st.metric("Account Status", validation_status)
    
    with col3:
        # Check real account data
        real_data = st.session_state.get('real_account_data')
        if real_data and real_data.get('account_type') == 'real':
            data_status = "🟢 Real Data"
        elif real_data and real_data.get('account_type') == 'paper':
            data_status = "📝 Paper Data"
        else:
            data_status = "⚪ No Data"
        st.metric("Account Data", data_status)

st.markdown("</div>", unsafe_allow_html=True)

# Footer Section
st.markdown("""
<div style="background: var(--card-bg); padding: 1.5rem; border-radius: var(--border-radius); 
            border: 1px solid var(--border-color); margin-top: 2rem; text-align: center;">
    <div style="color: var(--text-secondary); font-size: 0.9rem;">
        <p style="margin: 0; font-size: 0.8rem;">
            Developed by <strong style="color: var(--accent-blue);">Mushfiqur Rahaman</strong> • 
            Multi-Exchange Trading Platform v2.0
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Auto-refresh logic
if st.session_state['is_trading']:
    time.sleep(int(refresh_secs))
    st.rerun()
