"""
Daily Trade Summary Extractor
Extracts: Date, Trade Details, Daily P&L, Capital Used, Multiplier, Strategy ID
"""

import json
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tradetron_api import TradetronAPIClient
from trade_extractor import TradeDataExtractor


class DailyTradeSummaryExtractor:
    """Extract daily trade summaries with specific metrics"""
    
    def __init__(self):
        self.client = TradetronAPIClient()
        self.extractor = TradeDataExtractor()
    
    def extract_daily_summary(self, trades: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract daily summaries with:
        - Date
        - Trade Details
        - Daily P&L
        - Capital Used
        - Multiplier Used
        - Strategy ID
        """
        
        daily_data = defaultdict(list)
        
        for trade in trades:
            # Extract date (from entry_date or created_at)
            trade_date_str = trade.get('entry_date') or trade.get('created_at') or trade.get('date')
            
            if not trade_date_str:
                continue
            
            # Parse date
            try:
                if isinstance(trade_date_str, str):
                    # Try different date formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%d-%m-%Y', '%m/%d/%Y']:
                        try:
                            trade_date = datetime.strptime(trade_date_str[:10], '%Y-%m-%d')
                            break
                        except ValueError:
                            continue
                    else:
                        trade_date = datetime.fromisoformat(trade_date_str.split('T')[0])
                else:
                    trade_date = trade_date_str
            except Exception as e:
                print(f"⚠️  Could not parse date for trade: {trade_date_str}")
                continue
            
            # Format date key
            date_key = trade_date.strftime('%Y-%m-%d')
            
            # Extract required fields
            summary = {
                'date': date_key,
                'trade_id': trade.get('id', 'N/A'),
                'symbol': trade.get('symbol', 'N/A'),
                'entry_price': trade.get('entry_price', 0),
                'exit_price': trade.get('exit_price', 0),
                'quantity': trade.get('quantity', 0),
                'entry_time': trade.get('entry_time', trade.get('entry_date', 'N/A')),
                'exit_time': trade.get('exit_time', trade.get('exit_date', 'N/A')),
                'pnl': trade.get('pnl', 0),
                'pnl_percentage': trade.get('pnl_percentage', trade.get('pnl_pct', 0)),
                'capital_used': self._calculate_capital_used(trade),
                'multiplier': trade.get('multiplier', trade.get('leverage', 1)),
                'strategy_id': trade.get('strategy_id', 'N/A'),
                'strategy_name': trade.get('strategy_name', 'N/A'),
                'trade_status': trade.get('status', 'completed'),
                'duration_minutes': self._calculate_duration(trade),
            }
            
            daily_data[date_key].append(summary)
        
        return dict(daily_data)
    
    def _calculate_capital_used(self, trade: Dict[str, Any]) -> float:
        """Calculate capital used in trade"""
        
        # Try different ways to calculate
        if 'capital_used' in trade:
            return float(trade['capital_used'])
        
        if 'margin_used' in trade:
            return float(trade['margin_used'])
        
        # Calculate from entry_price * quantity
        entry_price = float(trade.get('entry_price', 0))
        quantity = float(trade.get('quantity', 0))
        
        if entry_price > 0 and quantity > 0:
            return entry_price * quantity
        
        return 0
    
    def _calculate_duration(self, trade: Dict[str, Any]) -> int:
        """Calculate trade duration in minutes"""
        
        try:
            entry_str = trade.get('entry_time') or trade.get('entry_date')
            exit_str = trade.get('exit_time') or trade.get('exit_date')
            
            if entry_str and exit_str:
                entry = datetime.fromisoformat(entry_str.replace('Z', '+00:00'))
                exit_dt = datetime.fromisoformat(exit_str.replace('Z', '+00:00'))
                duration = (exit_dt - entry).total_seconds() / 60
                return int(duration)
        except Exception:
            pass
        
        return 0
    
    def get_daily_pnl(self, daily_summary: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """Calculate daily P&L summary"""
        
        daily_pnl = {}
        
        for date_key, trades in daily_summary.items():
            total_pnl = sum([t['pnl'] for t in trades])
            winning_trades = len([t for t in trades if t['pnl'] > 0])
            losing_trades = len([t for t in trades if t['pnl'] < 0])
            
            total_capital = sum([t['capital_used'] for t in trades])
            
            daily_pnl[date_key] = {
                'date': date_key,
                'total_trades': len(trades),
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_pnl': total_pnl,
                'avg_pnl_per_trade': total_pnl / len(trades) if trades else 0,
                'total_capital_used': total_capital,
                'avg_capital_per_trade': total_capital / len(trades) if trades else 0,
                'daily_return_pct': (total_pnl / total_capital * 100) if total_capital > 0 else 0,
            }
        
        return daily_pnl
    
    def export_daily_summary(self, daily_summary: Dict[str, List[Dict[str, Any]]], 
                            filename: str = None) -> bool:
        """Export daily summary to JSON"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daily_summary_{timestamp}.json"
        
        try:
            path = Path(__file__).parent / filename
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(daily_summary, f, indent=2, default=str)
            
            print(f"✓ Exported daily summary to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error exporting: {e}")
            return False
    
    def export_daily_pnl_csv(self, daily_pnl: Dict[str, Dict[str, Any]], 
                            filename: str = None) -> bool:
        """Export daily P&L summary to CSV"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daily_pnl_{timestamp}.csv"
        
        if not daily_pnl:
            print("❌ No data to export")
            return False
        
        try:
            import csv
            path = Path(__file__).parent / filename
            
            with open(path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'Date', 'Total Trades', 'Winning', 'Losing', 
                    'Total P&L', 'Avg P&L', 'Total Capital', 'Return %'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for date_key, pnl_data in sorted(daily_pnl.items()):
                    writer.writerow({
                        'Date': pnl_data['date'],
                        'Total Trades': pnl_data['total_trades'],
                        'Winning': pnl_data['winning_trades'],
                        'Losing': pnl_data['losing_trades'],
                        'Total P&L': f"${pnl_data['total_pnl']:,.2f}",
                        'Avg P&L': f"${pnl_data['avg_pnl_per_trade']:,.2f}",
                        'Total Capital': f"${pnl_data['total_capital_used']:,.2f}",
                        'Return %': f"{pnl_data['daily_return_pct']:.2f}%",
                    })
            
            print(f"✓ Exported daily P&L to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error exporting: {e}")
            return False
    
    def print_daily_summary(self, daily_pnl: Dict[str, Dict[str, Any]]):
        """Print daily summary in formatted table"""
        
        print("\n" + "="*110)
        print(f"{'Date':<12} {'Trades':<8} {'W/L':<12} {'Total P&L':<15} {'Avg P&L':<15} {'Capital':<15} {'Return %':<10}")
        print("="*110)
        
        for date_key in sorted(daily_pnl.keys()):
            pnl = daily_pnl[date_key]
            w_l = f"{pnl['winning_trades']}/{pnl['losing_trades']}"
            
            print(f"{pnl['date']:<12} "
                  f"{pnl['total_trades']:<8} "
                  f"{w_l:<12} "
                  f"${pnl['total_pnl']:<14,.2f} "
                  f"${pnl['avg_pnl_per_trade']:<14,.2f} "
                  f"${pnl['total_capital_used']:<14,.2f} "
                  f"{pnl['daily_return_pct']:<10.2f}%")
        
        print("="*110 + "\n")
    
    def print_trade_details(self, daily_summary: Dict[str, List[Dict[str, Any]]], 
                          date: str = None):
        """Print detailed trade information for a specific date"""
        
        if date and date in daily_summary:
            trades = daily_summary[date]
        else:
            # Print all
            trades = []
            for trade_list in daily_summary.values():
                trades.extend(trade_list)
        
        if not trades:
            print("No trades found")
            return
        
        print("\n" + "="*140)
        print(f"{'Date':<12} {'Symbol':<8} {'Entry':<10} {'Exit':<10} {'Qty':<8} {'Capital':<12} {'Mult':<6} {'P&L':<12} {'Strategy ID':<15}")
        print("="*140)
        
        for trade in trades:
            print(f"{trade['date']:<12} "
                  f"{trade['symbol']:<8} "
                  f"${trade['entry_price']:<9.2f} "
                  f"${trade['exit_price']:<9.2f} "
                  f"{trade['quantity']:<8.2f} "
                  f"${trade['capital_used']:<11,.0f} "
                  f"{trade['multiplier']:<6.1f} "
                  f"${trade['pnl']:<11,.2f} "
                  f"{str(trade['strategy_id']):<15}")
        
        print("="*140 + "\n")


def main():
    """Extract daily trade summaries"""
    
    print("="*70)
    print("Daily Trade Summary Extractor")
    print("="*70)
    
    try:
        # Initialize
        extractor = DailyTradeSummaryExtractor()
        
        # Extract all trades
        print("\n📊 Extracting trades...")
        trade_extractor = TradeDataExtractor()
        trades = trade_extractor.extract_all_trades(limit=10000)
        
        if not trades:
            print("❌ No trades found")
            return False
        
        # Generate daily summary
        print("\n📈 Processing daily summaries...")
        daily_summary = extractor.extract_daily_summary(trades)
        
        # Get daily P&L
        daily_pnl = extractor.get_daily_pnl(daily_summary)
        
        # Print summary
        print(f"\n✓ Generated summary for {len(daily_summary)} days")
        extractor.print_daily_summary(daily_pnl)
        
        # Print detailed trades
        print("\n📋 Detailed Trade Information:")
        extractor.print_trade_details(daily_summary)
        
        # Export
        print("\n💾 Exporting data...")
        extractor.export_daily_summary(daily_summary)
        extractor.export_daily_pnl_csv(daily_pnl)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
