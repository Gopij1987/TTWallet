"""
Trade data extractor and formatter
Converts raw Tradetron API data into structured formats (CSV, JSON, etc.)
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tradetron_api import TradetronAPIClient

class TradeDataExtractor:
    """Extract and format trade data from Tradetron"""
    
    def __init__(self, client: Optional[TradetronAPIClient] = None):
        """Initialize extractor with API client"""
        self.client = client or TradetronAPIClient()
        self.extracted_data = {}
    
    def extract_all_trades(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Extract all trades with pagination"""
        
        print(f"\n📊 Extracting up to {limit} trades...")
        all_trades = []
        offset = 0
        batch_size = 100
        
        while offset < limit:
            trades = self.client.get_all_trades(limit=batch_size, offset=offset)
            
            if not trades:
                break
            
            all_trades.extend(trades)
            offset += batch_size
            
            print(f"  ✓ Extracted {len(all_trades)} trades ({offset})")
        
        self.extracted_data['trades'] = all_trades
        print(f"✓ Total trades extracted: {len(all_trades)}")
        return all_trades
    
    def extract_strategy_trades(self, strategy_id: int, limit: int = 1000) -> List[Dict[str, Any]]:
        """Extract trades for a specific strategy"""
        
        print(f"\n📊 Extracting trades for strategy {strategy_id}...")
        all_trades = []
        offset = 0
        batch_size = 100
        
        while offset < limit:
            trades = self.client.get_strategy_trades(strategy_id, limit=batch_size, offset=offset)
            
            if not trades:
                break
            
            all_trades.extend(trades)
            offset += batch_size
            
            print(f"  ✓ Extracted {len(all_trades)} trades")
        
        self.extracted_data[f'strategy_{strategy_id}_trades'] = all_trades
        return all_trades
    
    def extract_strategies(self) -> List[Dict[str, Any]]:
        """Extract all strategies"""
        
        print(f"\n📊 Extracting strategies...")
        strategies = self.client.get_strategies()
        
        if strategies:
            self.extracted_data['strategies'] = strategies
            print(f"✓ Extracted {len(strategies)} strategies")
        
        return strategies or []
    
    def export_to_json(self, filename: str, data: Any = None) -> bool:
        """Export data to JSON file"""
        
        if data is None:
            data = self.extracted_data
        
        try:
            path = Path(__file__).parent / filename
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            print(f"✓ Exported to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error exporting to {filename}: {e}")
            return False
    
    def export_trades_to_csv(self, filename: str, trades: List[Dict[str, Any]] = None) -> bool:
        """Export trades to CSV file"""
        
        if trades is None:
            trades = self.extracted_data.get('trades', [])
        
        if not trades:
            print("❌ No trades to export")
            return False
        
        try:
            path = Path(__file__).parent / filename
            
            # Get all unique keys from trades
            fieldnames = set()
            for trade in trades:
                fieldnames.update(trade.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(trades)
            
            print(f"✓ Exported {len(trades)} trades to {filename}")
            return True
        
        except Exception as e:
            print(f"❌ Error exporting to {filename}: {e}")
            return False
    
    def get_trade_summary(self, trades: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate summary statistics for trades"""
        
        if trades is None:
            trades = self.extracted_data.get('trades', [])
        
        if not trades:
            return {}
        
        # Calculate statistics
        total_trades = len(trades)
        
        pnl_values = []
        win_trades = 0
        loss_trades = 0
        
        for trade in trades:
            pnl = trade.get('pnl', 0)
            if isinstance(pnl, (int, float)):
                pnl_values.append(pnl)
                if pnl > 0:
                    win_trades += 1
                elif pnl < 0:
                    loss_trades += 0
        
        summary = {
            'total_trades': total_trades,
            'winning_trades': win_trades,
            'losing_trades': loss_trades,
            'total_pnl': sum(pnl_values) if pnl_values else 0,
            'average_pnl': sum(pnl_values) / len(pnl_values) if pnl_values else 0,
            'max_profit': max(pnl_values) if pnl_values else 0,
            'max_loss': min(pnl_values) if pnl_values else 0,
            'win_rate': (win_trades / total_trades * 100) if total_trades > 0 else 0,
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any] = None):
        """Print trade summary in a formatted way"""
        
        if summary is None:
            summary = self.get_trade_summary()
        
        if not summary:
            print("❌ No data to summarize")
            return
        
        print("\n" + "="*70)
        print("📈 TRADE SUMMARY")
        print("="*70)
        print(f"Total Trades:       {summary.get('total_trades', 0)}")
        print(f"Winning Trades:     {summary.get('winning_trades', 0)}")
        print(f"Losing Trades:      {summary.get('losing_trades', 0)}")
        print(f"Win Rate:           {summary.get('win_rate', 0):.2f}%")
        print(f"Total P&L:          ${summary.get('total_pnl', 0):,.2f}")
        print(f"Average P&L/Trade:  ${summary.get('average_pnl', 0):,.2f}")
        print(f"Max Profit:         ${summary.get('max_profit', 0):,.2f}")
        print(f"Max Loss:           ${summary.get('max_loss', 0):,.2f}")
        print("="*70)


def main():
    """Example usage of the trade data extractor"""
    
    print("="*70)
    print("Tradetron Trade Data Extractor")
    print("="*70)
    
    try:
        # Initialize extractor
        extractor = TradeDataExtractor()
        
        # Extract strategies
        strategies = extractor.extract_strategies()
        
        # Extract all trades
        trades = extractor.extract_all_trades(limit=1000)
        
        if trades:
            # Export to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extractor.export_to_json(f"trades_{timestamp}.json")
            
            # Export to CSV
            extractor.export_trades_to_csv(f"trades_{timestamp}.csv")
            
            # Print summary
            summary = extractor.get_trade_summary(trades)
            extractor.print_summary(summary)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
