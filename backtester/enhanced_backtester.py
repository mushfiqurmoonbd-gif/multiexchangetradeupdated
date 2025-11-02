import os
import sys
import types
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import requests

# Avoid curl_cffi/eventlet incompatibilities on some Python versions
# If curl_cffi is present, yfinance may try to use it; we force fallback to standard requests
os.environ.setdefault("YFINANCE_DISABLE_CURL_CFFI", "1")
# Provide a lightweight shim so yfinance imports succeed without eventlet/curl_cffi
try:
    import requests as _pyrequests
    _shim = types.ModuleType('curl_cffi')
    _shim.requests = _pyrequests
    sys.modules['curl_cffi'] = _shim
except Exception:
    pass

import yfinance as yf
from indicators.weighted_signals import WeightedSignalGenerator
from signals.trading_triggers import TradingTriggerEngine
from utils.advanced_risk import AdvancedRiskManager

class EnhancedBacktester:
    """
    Enhanced backtesting system with:
    - 15+ timeframes support
    - Historical data fetching
    - Crypto + Stock support
    - Multi-timeframe analysis
    """
    
    def __init__(self):
        self.supported_timeframes = [
            # Intraday timeframes
            '1m', '2m', '3m', '5m', '10m', '15m', '20m', '30m',
            # Hourly timeframes
            '1h', '2h', '3h', '4h', '6h', '8h', '12h',
            # Daily timeframes
            '1d', '2d', '3d', '5d',
            # Weekly timeframes
            '1w', '2w', '3w',
            # Monthly timeframes
            '1M', '2M', '3M', '6M',
            # Yearly timeframes
            '1y', '2y', '5y'
        ]
        
        self.supported_tickers = {
            'Crypto': [
                'BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'DOT-USD',
                'MATIC-USD', 'AVAX-USD', 'LINK-USD', 'UNI-USD', 'ATOM-USD'
            ],
            'Stocks': [
                'NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META',
                'NFLX', 'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'PYPL'
            ],
            'Forex': [
                'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X'
            ]
        }
        
        self.crypto_exchanges = ['binance', 'bybit', 'mexc', 'coinbase']
        self.stock_sources = ['alpaca', 'yfinance']
        
    def fetch_historical_data(self, 
                            symbol: str,
                            timeframe: str,
                            start_date: Union[str, datetime],
                            end_date: Union[str, datetime],
                            source: str = 'auto') -> pd.DataFrame:
        """
        Fetch historical data from various sources
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT', 'AAPL')
            timeframe: Timeframe string
            start_date: Start date
            end_date: End date
            source: Data source ('auto', 'yfinance', 'alpaca', 'binance', etc.)
            
        Returns:
            pd.DataFrame: Historical OHLCV data
        """
        if source == 'auto':
            source = self._detect_data_source(symbol)
        
        if source == 'yfinance':
            return self._fetch_yfinance_data(symbol, timeframe, start_date, end_date)
        elif source == 'alpaca':
            return self._fetch_alpaca_data(symbol, timeframe, start_date, end_date)
        elif source in self.crypto_exchanges:
            return self._fetch_crypto_data(symbol, timeframe, start_date, end_date, source)
        else:
            raise ValueError(f"Unsupported data source: {source}")
    
    def _detect_data_source(self, symbol: str) -> str:
        """
        Auto-detect data source based on symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            str: Detected data source
        """
        # Crypto symbols typically end with USDT, USD, BTC, ETH
        crypto_suffixes = ['USDT', 'USD', 'BTC', 'ETH', 'BNB', 'ADA', 'SOL']
        if any(symbol.endswith(suffix) for suffix in crypto_suffixes):
            return 'yfinance'  # Use yfinance for crypto as it's more reliable
        
        # Stock symbols are typically 1-5 characters
        if len(symbol) <= 5 and symbol.isalpha():
            return 'yfinance'  # Use yfinance for stocks
        
        return 'yfinance'  # Default to yfinance
    
    def _fetch_yfinance_data(self, symbol: str, timeframe: str, 
                            start_date: Union[str, datetime], 
                            end_date: Union[str, datetime]) -> pd.DataFrame:
        """
        Fetch data using yfinance
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            start_date: Start date
            end_date: End date
            
        Returns:
            pd.DataFrame: Historical data
        """
        # Convert timeframe to yfinance format
        yf_interval = self._convert_timeframe_to_yfinance(timeframe)
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval,
                auto_adjust=True,
                prepost=True
            )
            
            if df.empty:
                raise ValueError(f"No data found for {symbol}")
            
            # Standardize column names
            df.columns = df.columns.str.lower()
            df = df.rename(columns={
                'adj close': 'close',
                'adj_close': 'close'
            })
            
            # Add timestamp column
            df['timestamp'] = df.index
            df = df.reset_index(drop=True)
            
            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'volume':
                        df[col] = 0
                    else:
                        df[col] = df['close']
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            raise ValueError(f"Failed to fetch yfinance data for {symbol}: {str(e)}")
    
    def _convert_timeframe_to_yfinance(self, timeframe: str) -> str:
        """
        Convert timeframe to yfinance interval format
        
        Args:
            timeframe: Timeframe string
            
        Returns:
            str: yfinance interval
        """
        timeframe_map = {
            '1m': '1m', '2m': '2m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '12h': '12h',
            '1d': '1d', '5d': '5d', '1w': '1wk', '1M': '1mo', '3M': '3mo',
            '6M': '6mo', '1y': '1y', '2y': '2y', '5y': '5y'
        }
        
        return timeframe_map.get(timeframe, '1d')
    
    def _fetch_alpaca_data(self, symbol: str, timeframe: str,
                          start_date: Union[str, datetime],
                          end_date: Union[str, datetime]) -> pd.DataFrame:
        """
        Fetch data using Alpaca API
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            start_date: Start date
            end_date: End date
            
        Returns:
            pd.DataFrame: Historical data
        """
        # This would integrate with Alpaca API
        # For now, fallback to yfinance
        return self._fetch_yfinance_data(symbol, timeframe, start_date, end_date)
    
    def _fetch_crypto_data(self, symbol: str, timeframe: str,
                          start_date: Union[str, datetime],
                          end_date: Union[str, datetime],
                          exchange: str) -> pd.DataFrame:
        """
        Fetch crypto data from various exchanges
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            start_date: Start date
            end_date: End date
            exchange: Exchange name
            
        Returns:
            pd.DataFrame: Historical data
        """
        # This would integrate with exchange APIs
        # For now, fallback to yfinance
        return self._fetch_yfinance_data(symbol, timeframe, start_date, end_date)
    
    def run_enhanced_backtest(self,
                            symbol: str,
                            timeframe: str,
                            start_date: Union[str, datetime],
                            end_date: Union[str, datetime],
                            initial_capital: float = 10000.0,
                            risk_per_trade: float = 0.02,
                            daily_loss_limit: float = 0.05,
                            rsi_length: int = 14,
                            rsi_oversold: float = 30,
                            rsi_overbought: float = 70,
                            wt_channel_length: int = 10,
                            wt_average_length: int = 21,
                            momentum_lookback: int = 20,
                            tp1_multiplier: float = 1.5,
                            tp2_multiplier: float = 2.0,
                            runner_multiplier: float = 3.0,
                            data_source: str = 'auto') -> Dict[str, any]:
        """
        Run enhanced backtest with all features
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            start_date: Start date
            end_date: End date
            initial_capital: Initial capital
            risk_per_trade: Risk per trade
            daily_loss_limit: Daily loss limit
            rsi_length: RSI length
            rsi_oversold: RSI oversold level
            rsi_overbought: RSI overbought level
            wt_channel_length: WaveTrend channel length
            wt_average_length: WaveTrend average length
            momentum_lookback: Momentum lookback period
            tp1_multiplier: TP1 multiplier
            tp2_multiplier: TP2 multiplier
            runner_multiplier: Runner multiplier
            data_source: Data source
            
        Returns:
            Dict: Backtest results
        """
        # Validate timeframe
        if timeframe not in self.supported_timeframes:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {self.supported_timeframes}")
        
        # Fetch historical data
        df = self.fetch_historical_data(symbol, timeframe, start_date, end_date, data_source)
        
        if df.empty:
            raise ValueError("No data fetched for backtesting")
        
        # Initialize components
        trigger_engine = TradingTriggerEngine()
        risk_manager = AdvancedRiskManager(
            initial_capital=initial_capital,
            risk_per_trade=risk_per_trade,
            daily_loss_limit=daily_loss_limit
        )
        
        # Generate signals using the 3-tier hierarchy
        signals = trigger_engine.generate_combined_signals(
            df,
            wt_channel_length=wt_channel_length,
            wt_average_length=wt_average_length,
            momentum_lookback=20,  # Default momentum lookback
            rsi_length=rsi_length,
            rsi_buy_threshold=rsi_overbought,  # Use overbought as buy threshold
            rsi_sell_threshold=rsi_oversold,   # Use oversold as sell threshold
            show_intermediate=True
        )
        
        # Add signals to dataframe
        for signal_name, signal_data in signals.items():
            df[signal_name] = signal_data
        
        # Run backtest simulation (long+short)
        results = self._simulate_trading(
            df, risk_manager, tp1_multiplier, tp2_multiplier, runner_multiplier
        )
        
        # Calculate metrics
        metrics = self._calculate_enhanced_metrics(df, results)
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': start_date,
            'end_date': end_date,
            'data_source': data_source,
            'df': df,
            'signals': signals,
            'trades': results['trades'],
            'daily_summaries': results['daily_summaries'],
            'metrics': metrics,
            'risk_summary': results['risk_summary']
        }
    
    def _simulate_trading(self, df: pd.DataFrame, risk_manager: AdvancedRiskManager,
                         tp1_multiplier: float, tp2_multiplier: float, 
                         runner_multiplier: float) -> Dict[str, any]:
        """
        Simulate trading with advanced risk management
        
        Args:
            df: DataFrame with price data and signals
            risk_manager: Risk manager instance
            tp1_multiplier: TP1 multiplier
            tp2_multiplier: TP2 multiplier
            runner_multiplier: Runner multiplier
            
        Returns:
            Dict: Trading simulation results
        """
        trades = []
        daily_summaries = []
        current_date = None
        
        for idx, row in df.iterrows():
            current_price = row['close']
            current_timestamp = row['timestamp']
            
            # Check if new day
            if current_date != current_timestamp.date():
                if current_date is not None:
                    # Save daily summary
                    daily_summary = risk_manager.get_portfolio_summary()
                    daily_summary['date'] = current_date
                    daily_summaries.append(daily_summary)
                    
                    # Reset daily tracking
                    risk_manager.reset_daily_tracking()
                
                current_date = current_timestamp.date()
            
            # Update existing positions
            for position in risk_manager.positions[:]:  # Copy to avoid modification during iteration
                update_result = risk_manager.update_position(position['id'], current_price)
                
                if update_result['status'] in ['fully_closed', 'partially_closed']:
                    trades.append(update_result['trade'])
            
            # Check for new entry signals (long + short) using new trigger system
            if not risk_manager.is_daily_breaker_triggered():
                # Long entry - check for buy signals
                if 'final_buy' in df.columns and bool(row.get('final_buy', False)):
                    stop_loss_price = current_price * 0.98
                    position = risk_manager.open_position(
                        symbol='SYMBOL',
                        side='buy',
                        entry_price=current_price,
                        stop_loss_price=stop_loss_price,
                        tp1_multiplier=tp1_multiplier,
                        tp2_multiplier=tp2_multiplier,
                        runner_multiplier=runner_multiplier
                    )
                    if position:
                        trades.append({
                            'position_id': position['id'],
                            'symbol': position['symbol'],
                            'side': position['side'],
                            'entry_price': position['entry_price'],
                            'quantity': position['quantity'],
                            'timestamp': current_timestamp,
                            'action': 'open'
                        })
                # Short entry - check for sell signals
                if 'final_sell' in df.columns and bool(row.get('final_sell', False)):
                    stop_loss_price = current_price * 1.02  # SL above entry for shorts
                    position = risk_manager.open_position(
                        symbol='SYMBOL',
                        side='sell',
                        entry_price=current_price,
                        stop_loss_price=stop_loss_price,
                        tp1_multiplier=tp1_multiplier,
                        tp2_multiplier=tp2_multiplier,
                        runner_multiplier=runner_multiplier
                    )
                    if position:
                        trades.append({
                            'position_id': position['id'],
                            'symbol': position['symbol'],
                            'side': position['side'],
                            'entry_price': position['entry_price'],
                            'quantity': position['quantity'],
                            'timestamp': current_timestamp,
                            'action': 'open'
                        })
        
        # Final daily summary
        if current_date is not None:
            daily_summary = risk_manager.get_portfolio_summary()
            daily_summary['date'] = current_date
            daily_summaries.append(daily_summary)
        
        return {
            'trades': trades,
            'daily_summaries': daily_summaries,
            'risk_summary': risk_manager.get_portfolio_summary()
        }
    
    def _calculate_enhanced_metrics(self, df: pd.DataFrame, results: Dict[str, any]) -> Dict[str, float]:
        """
        Calculate enhanced backtesting metrics
        
        Args:
            df: Price data
            results: Trading results
            
        Returns:
            Dict: Enhanced metrics
        """
        trades = results['trades']
        daily_summaries = results['daily_summaries']
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'total_return': 0.0,
                'avg_trade_return': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0
            }
        
        # Basic trade metrics
        closed_trades = [t for t in trades if 'pnl' in t]
        if not closed_trades:
            return {'total_trades': len(trades), 'win_rate': 0.0}
        
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_profit = sum(t['pnl'] for t in winning_trades)
        total_loss = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Calculate returns
        if daily_summaries:
            equity_curve = [ds['current_capital'] for ds in daily_summaries]
            returns = np.diff(equity_curve) / equity_curve[:-1]
            
            # Sharpe ratio
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            
            # Max drawdown
            peak = np.maximum.accumulate(equity_curve)
            drawdown = (np.array(equity_curve) - peak) / peak
            max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
            
            # Total return
            total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0] if len(equity_curve) > 1 else 0
        else:
            sharpe_ratio = 0.0
            max_drawdown = 0.0
            total_return = 0.0
        
        # Trade statistics
        trade_returns = [t['pnl'] for t in closed_trades]
        avg_trade_return = np.mean(trade_returns) if trade_returns else 0
        best_trade = np.max(trade_returns) if trade_returns else 0
        worst_trade = np.min(trade_returns) if trade_returns else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_return': total_return,
            'avg_trade_return': avg_trade_return,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'total_profit': total_profit,
            'total_loss': total_loss
        }
    
    def get_supported_timeframes(self) -> List[str]:
        """
        Get list of supported timeframes
        
        Returns:
            List[str]: Supported timeframes
        """
        return self.supported_timeframes.copy()
    
    def get_supported_tickers(self) -> Dict[str, List[str]]:
        """
        Get dictionary of supported tickers by category
        
        Returns:
            Dict[str, List[str]]: Supported tickers by category
        """
        return self.supported_tickers.copy()
    
    def get_all_tickers(self) -> List[str]:
        """
        Get flat list of all supported tickers
        
        Returns:
            List[str]: All supported tickers
        """
        all_tickers = []
        for category, tickers in self.supported_tickers.items():
            all_tickers.extend(tickers)
        return all_tickers
    
    def validate_timeframe(self, timeframe: str) -> bool:
        """
        Validate if timeframe is supported
        
        Args:
            timeframe: Timeframe string
            
        Returns:
            bool: True if supported
        """
        return timeframe in self.supported_timeframes
    
    def validate_ticker(self, ticker: str) -> bool:
        """
        Validate if ticker is supported
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            bool: True if supported
        """
        all_tickers = self.get_all_tickers()
        return ticker in all_tickers
