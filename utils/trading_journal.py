#!/usr/bin/env python3
"""
Trading Journal System
Tracks and analyzes all trading activity with detailed records
"""

import os
import csv
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path


class TradingJournal:
    """
    Trading journal for recording and analyzing trade history
    
    Features:
    - Trade logging with full details
    - PnL tracking
    - Performance analytics
    - Strategy performance breakdown
    - CSV export
    - Trade notes and tags
    """
    
    def __init__(self, journal_file: str = "logs/trading_journal.csv"):
        """
        Initialize trading journal
        
        Args:
            journal_file: Path to journal CSV file
        """
        self.journal_file = journal_file
        self._ensure_journal_exists()
    
    def _ensure_journal_exists(self):
        """Create journal file and directory if they don't exist"""
        # Create logs directory if needed
        os.makedirs(os.path.dirname(self.journal_file), exist_ok=True)
        
        # Create CSV with headers if doesn't exist
        if not os.path.exists(self.journal_file):
            with open(self.journal_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'trade_id', 'exchange', 'symbol', 'strategy',
                    'action', 'order_type', 'entry_price', 'exit_price',
                    'quantity', 'position_size_usd', 'pnl', 'pnl_percent',
                    'fees', 'net_pnl', 'win_loss', 'holding_time',
                    'stop_loss', 'take_profit', 'notes', 'tags',
                    'entry_time', 'exit_time', 'market_conditions'
                ])
    
    def log_trade(self, 
                  trade_id: str,
                  exchange: str,
                  symbol: str,
                  strategy: str,
                  action: str,
                  order_type: str = 'market',
                  entry_price: float = 0.0,
                  exit_price: float = 0.0,
                  quantity: float = 0.0,
                  pnl: float = 0.0,
                  fees: float = 0.0,
                  stop_loss: float = 0.0,
                  take_profit: float = 0.0,
                  notes: str = "",
                  tags: List[str] = None,
                  entry_time: Optional[datetime] = None,
                  exit_time: Optional[datetime] = None,
                  market_conditions: str = "") -> bool:
        """
        Log a trade to the journal
        
        Args:
            trade_id: Unique trade identifier
            exchange: Exchange name
            symbol: Trading pair
            strategy: Strategy used
            action: 'buy', 'sell', 'long', 'short', 'close'
            order_type: 'market', 'limit', 'stop_limit'
            entry_price: Entry price
            exit_price: Exit price (0 if still open)
            quantity: Trade quantity
            pnl: Profit/loss
            fees: Trading fees
            stop_loss: Stop-loss price
            take_profit: Take-profit price
            notes: Trade notes
            tags: List of tags
            entry_time: Entry timestamp
            exit_time: Exit timestamp
            market_conditions: Market conditions description
            
        Returns:
            bool: Success status
        """
        try:
            # Calculate metrics
            position_size_usd = entry_price * quantity
            
            if exit_price > 0 and entry_price > 0:
                # Closed position
                pnl_percent = ((exit_price - entry_price) / entry_price) * 100
                if action.lower() in ['sell', 'short']:
                    pnl_percent = -pnl_percent
                
                net_pnl = pnl - fees
                win_loss = 'win' if net_pnl > 0 else 'loss' if net_pnl < 0 else 'breakeven'
                
                # Calculate holding time
                if entry_time and exit_time:
                    holding_time = str(exit_time - entry_time)
                else:
                    holding_time = ""
            else:
                # Open position
                pnl_percent = 0.0
                net_pnl = -fees
                win_loss = 'open'
                holding_time = ""
            
            # Format timestamps
            timestamp = datetime.now().isoformat()
            entry_time_str = entry_time.isoformat() if entry_time else timestamp
            exit_time_str = exit_time.isoformat() if exit_time else ""
            
            # Format tags
            tags_str = ','.join(tags) if tags else ""
            
            # Write to CSV
            with open(self.journal_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, trade_id, exchange, symbol, strategy,
                    action, order_type, entry_price, exit_price,
                    quantity, position_size_usd, pnl, pnl_percent,
                    fees, net_pnl, win_loss, holding_time,
                    stop_loss, take_profit, notes, tags_str,
                    entry_time_str, exit_time_str, market_conditions
                ])
            
            return True
            
        except Exception as e:
            print(f"Error logging trade: {e}")
            return False
    
    def log_signal(self, symbol: str, signal_type: str, strategy: str,
                   confidence: float, price: float, notes: str = "") -> bool:
        """
        Log a trading signal (even if not executed)
        
        Args:
            symbol: Trading pair
            signal_type: 'buy' or 'sell'
            strategy: Strategy name
            confidence: Signal confidence (0-100)
            price: Price at signal
            notes: Additional notes
            
        Returns:
            bool: Success status
        """
        signal_file = "logs/signals_journal.csv"
        
        # Create signals file if needed
        if not os.path.exists(signal_file):
            os.makedirs(os.path.dirname(signal_file), exist_ok=True)
            with open(signal_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'symbol', 'signal_type', 'strategy',
                    'confidence', 'price', 'executed', 'notes'
                ])
        
        try:
            with open(signal_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    symbol, signal_type, strategy,
                    confidence, price, 'no', notes
                ])
            return True
        except Exception as e:
            print(f"Error logging signal: {e}")
            return False
    
    def get_trade_stats(self) -> Dict[str, Any]:
        """
        Get trading statistics
        
        Returns:
            Dict with stats
        """
        try:
            df = pd.read_csv(self.journal_file)
            
            if len(df) == 0:
                return {'error': 'No trades in journal'}
            
            # Filter closed trades
            closed_trades = df[df['win_loss'].isin(['win', 'loss', 'breakeven'])]
            
            if len(closed_trades) == 0:
                return {
                    'total_trades': 0,
                    'open_positions': len(df[df['win_loss'] == 'open']),
                    'message': 'No closed trades yet'
                }
            
            # Calculate stats
            total_trades = len(closed_trades)
            winning_trades = len(closed_trades[closed_trades['win_loss'] == 'win'])
            losing_trades = len(closed_trades[closed_trades['win_loss'] == 'loss'])
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = closed_trades['net_pnl'].sum()
            avg_win = closed_trades[closed_trades['win_loss'] == 'win']['net_pnl'].mean() if winning_trades > 0 else 0
            avg_loss = closed_trades[closed_trades['win_loss'] == 'loss']['net_pnl'].mean() if losing_trades > 0 else 0
            
            # Best and worst trades
            best_trade = closed_trades.loc[closed_trades['net_pnl'].idxmax()] if len(closed_trades) > 0 else None
            worst_trade = closed_trades.loc[closed_trades['net_pnl'].idxmin()] if len(closed_trades) > 0 else None
            
            # Strategy breakdown
            strategy_stats = closed_trades.groupby('strategy').agg({
                'net_pnl': ['sum', 'mean', 'count']
            }).round(2)
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
                'best_trade': {
                    'symbol': best_trade['symbol'],
                    'pnl': round(best_trade['net_pnl'], 2),
                    'strategy': best_trade['strategy']
                } if best_trade is not None else None,
                'worst_trade': {
                    'symbol': worst_trade['symbol'],
                    'pnl': round(worst_trade['net_pnl'], 2),
                    'strategy': worst_trade['strategy']
                } if worst_trade is not None else None,
                'open_positions': len(df[df['win_loss'] == 'open']),
                'strategy_breakdown': strategy_stats.to_dict() if len(strategy_stats) > 0 else {}
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """
        Get recent trades
        
        Args:
            limit: Number of trades to return
            
        Returns:
            List of trade dicts
        """
        try:
            df = pd.read_csv(self.journal_file)
            recent = df.tail(limit)
            return recent.to_dict('records')
        except Exception as e:
            print(f"Error getting recent trades: {e}")
            return []
    
    def export_to_excel(self, output_file: str = "logs/trading_journal.xlsx"):
        """
        Export journal to Excel with multiple sheets
        
        Args:
            output_file: Output Excel file path
        """
        try:
            df = pd.read_csv(self.journal_file)
            
            # Create Excel writer
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # All trades sheet
                df.to_excel(writer, sheet_name='All Trades', index=False)
                
                # Closed trades only
                closed = df[df['win_loss'].isin(['win', 'loss', 'breakeven'])]
                closed.to_excel(writer, sheet_name='Closed Trades', index=False)
                
                # Winning trades
                wins = df[df['win_loss'] == 'win']
                wins.to_excel(writer, sheet_name='Winning Trades', index=False)
                
                # Losing trades
                losses = df[df['win_loss'] == 'loss']
                losses.to_excel(writer, sheet_name='Losing Trades', index=False)
                
                # Strategy performance
                if len(closed) > 0:
                    strategy_perf = closed.groupby('strategy').agg({
                        'net_pnl': ['sum', 'mean', 'count'],
                        'win_loss': lambda x: (x == 'win').sum()
                    }).round(2)
                    strategy_perf.to_excel(writer, sheet_name='Strategy Performance')
            
            print(f"Journal exported to {output_file}")
            return True
            
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
    
    def generate_report(self) -> str:
        """
        Generate a text report of trading performance
        
        Returns:
            str: Formatted report
        """
        stats = self.get_trade_stats()
        
        if 'error' in stats:
            return f"Error generating report: {stats['error']}"
        
        report = f"""
{'=' * 60}
TRADING JOURNAL REPORT
{'=' * 60}

OVERALL STATISTICS:
------------------
Total Trades: {stats.get('total_trades', 0)}
Winning Trades: {stats.get('winning_trades', 0)} ✓
Losing Trades: {stats.get('losing_trades', 0)} ✗
Win Rate: {stats.get('win_rate', 0):.2f}%
Open Positions: {stats.get('open_positions', 0)}

PERFORMANCE:
-----------
Total PnL: ${stats.get('total_pnl', 0):,.2f}
Average Win: ${stats.get('avg_win', 0):,.2f}
Average Loss: ${stats.get('avg_loss', 0):,.2f}
Profit Factor: {stats.get('profit_factor', 0):.2f}

BEST TRADE:
----------
"""
        if stats.get('best_trade'):
            report += f"Symbol: {stats['best_trade']['symbol']}\n"
            report += f"PnL: ${stats['best_trade']['pnl']:,.2f}\n"
            report += f"Strategy: {stats['best_trade']['strategy']}\n"
        
        report += "\nWORST TRADE:\n-----------\n"
        if stats.get('worst_trade'):
            report += f"Symbol: {stats['worst_trade']['symbol']}\n"
            report += f"PnL: ${stats['worst_trade']['pnl']:,.2f}\n"
            report += f"Strategy: {stats['worst_trade']['strategy']}\n"
        
        report += "\n" + "=" * 60
        report += f"\nReport Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "=" * 60
        
        return report


# Example usage
if __name__ == "__main__":
    print("=== Trading Journal System ===\n")
    
    # Create journal
    journal = TradingJournal()
    
    # Example: Log a trade
    journal.log_trade(
        trade_id="TRADE_001",
        exchange="Binance",
        symbol="BTC/USDT",
        strategy="EMA Crossover",
        action="buy",
        order_type="market",
        entry_price=95000.0,
        exit_price=97000.0,
        quantity=0.001,
        pnl=2.0,
        fees=0.1,
        stop_loss=93000.0,
        take_profit=98000.0,
        notes="Strong uptrend, good entry",
        tags=["swing", "crypto"],
        entry_time=datetime(2025, 10, 29, 10, 0),
        exit_time=datetime(2025, 10, 29, 15, 30),
        market_conditions="Bullish"
    )
    
    print("✓ Sample trade logged\n")
    
    # Get stats
    print("Getting trade statistics...\n")
    stats = journal.get_trade_stats()
    print(json.dumps(stats, indent=2))
    
    # Generate report
    print("\n" + journal.generate_report())
    
    # Export to Excel
    journal.export_to_excel()
    print("\n✓ Journal exported to Excel")

