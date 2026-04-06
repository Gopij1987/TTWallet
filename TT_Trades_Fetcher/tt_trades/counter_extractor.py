"""
Extract Trade Data from Counter Export JSON Files
Works with the existing exported JSON files instead of API calls
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict


class CounterExportExtractor:
    """Extract trade data from exported counter JSON files"""
    
    def __init__(self, exports_folder: str = None):
        """Initialize with path to counter_exports folder"""
        
        if exports_folder is None:
            # Default location relative to this script
            exports_folder = Path(__file__).parent.parent / "counter_exports"
        
        self.exports_folder = Path(exports_folder)
        
        if not self.exports_folder.exists():
            print(f"❌ Exports folder not found: {self.exports_folder}")
            return
        
        self.json_files = sorted(self.exports_folder.glob("counter_*.json"))
        print(f"✓ Found {len(self.json_files)} counter export files")
    
    def list_available_strategies(self) -> Dict[int, Dict[str, Any]]:
        """Get list of all strategies in the exported data"""
        
        strategies = {}
        
        for json_file in self.json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'data' in data and 'data' in data['data']:
                    strategy_data = data['data']['data']
                    strategy_id = strategy_data.get('id')
                    
                    if strategy_id and strategy_id not in strategies:
                        strategies[strategy_id] = {
                            'id': strategy_id,
                            'name': strategy_data.get('template', {}).get('name', 'N/A'),
                            'status': strategy_data.get('status', 'N/A'),
                            'sum_pnl': strategy_data.get('sum_of_pnl', 0),
                            'run_counter': strategy_data.get('run_counter', 0),
                            'source_file': json_file.name,
                        }
            except Exception as e:
                print(f"⚠️  Error reading {json_file.name}: {e}")
                continue
        
        return strategies
    
    def extract_strategy_data(self, strategy_id: int = None) -> Optional[Dict[str, Any]]:
        """Extract data for a specific strategy, or first available"""
        
        strategies = self.list_available_strategies()
        
        if not strategies:
            print("❌ No strategies found in exported data")
            return None
        
        # If no strategy_id specified, use first one
        if strategy_id is None:
            strategy_id = list(strategies.keys())[0]
            print(f"\n⚠️  No strategy ID specified, using first available: {strategy_id}")
        
        if strategy_id not in strategies:
            print(f"❌ Strategy {strategy_id} not found in exported data")
            print(f"\nAvailable strategies:")
            for sid, info in strategies.items():
                print(f"  - {sid}: {info['name']} (Status: {info['status']})")
            return None
        
        # Find and read the file for this strategy
        for json_file in self.json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'data' in data and 'data' in data['data']:
                    strategy_data = data['data']['data']
                    if strategy_data.get('id') == strategy_id:
                        return {
                            'strategy_id': strategy_id,
                            'strategy_data': strategy_data,
                            'source_file': json_file.name,
                        }
            except Exception as e:
                continue
        
        return None
    
    def extract_daily_pnl(self, strategy_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract daily P&L from run counter data"""
        
        daily_pnl = {}
        deployment_date = strategy_data.get('deployment_date', '2023-03-06')
        
        # Extract filtered_run_counter data
        run_counters = strategy_data.get('filtered_run_counter', [])
        
        for counter in run_counters:
            run_num = counter.get('run_counter', 0)
            pnl = counter.get('pnl', 0)
            
            # Create date key (assuming each run is one day)
            # This is approximate - actual trade dates would be better
            date_key = f"Run {run_num}"
            
            if date_key not in daily_pnl:
                daily_pnl[date_key] = {
                    'date': date_key,
                    'run_counter': run_num,
                    'pnl': pnl,
                }
        
        return daily_pnl
    
    def extract_positions(self, strategy_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract current positions/trades"""
        
        positions = []
        calc_positions = strategy_data.get('calculated_positions', [])
        
        for pos in calc_positions:
            trade = {
                'id': pos.get('id'),
                'symbol': pos.get('Instrument', pos.get('instrument', 'N/A')),
                'underlying': pos.get('underlying', 'N/A'),
                'option_type': pos.get('option_type', ''),
                'quantity': pos.get('quantity', 0),
                'price': pos.get('price', 0),
                'pnl': pos.get('pnl', 0),
                'ltp': pos.get('ltp', 0),
                'entry_value': pos.get('entry_value', 0),
                'exchange': pos.get('exchange', 'N/A'),
            }
            positions.append(trade)
        
        return positions
    
    def print_strategies(self):
        """Print all available strategies"""
        
        strategies = self.list_available_strategies()
        
        if not strategies:
            print("❌ No strategies found")
            return
        
        print("\n" + "="*100)
        print(f"{'Strategy ID':<15} {'Name':<50} {'Status':<15} {'Total P&L':<15}")
        print("="*100)
        
        for sid, info in sorted(strategies.items()):
            name = info['name'][:47] + "..." if len(info['name']) > 50 else info['name']
            print(f"{sid:<15} {name:<50} {info['status']:<15} ${info['sum_pnl']:<14,.2f}")
        
        print("="*100 + "\n")
    
    def print_strategy_details(self, strategy_id: int = None):
        """Print detailed information for a strategy"""
        
        data = self.extract_strategy_data(strategy_id)
        
        if not data:
            return
        
        strategy_data = data['strategy_data']
        strategy_id = data['strategy_id']
        
        print("\n" + "="*70)
        print(f"STRATEGY {strategy_id} - DETAILS")
        print("="*70)
        
        print(f"\nBasic Info:")
        print(f"  Source File: {data['source_file']}")
        print(f"  Status: {strategy_data.get('status')}")
        print(f"  Strategy Name: {strategy_data.get('template', {}).get('name')}")
        print(f"  Deployment Date: {strategy_data.get('deployment_date')}")
        print(f"  Run Counter: {strategy_data.get('run_counter')}")
        
        print(f"\nPerformance:")
        print(f"  Total P&L: ${strategy_data.get('sum_of_pnl'):,.2f}")
        print(f"  Capital Required: ${strategy_data.get('template', {}).get('capital_required', 0):,.2f}")
        print(f"  Max Multiple: {strategy_data.get('max_multiple')}")
        
        # Show positions
        positions = self.extract_positions(strategy_data)
        print(f"\nCurrent Positions: {len(positions)}")
        
        if positions:
            print("\n" + "="*120)
            print(f"{'Symbol':<30} {'Type':<8} {'Qty':<10} {'Entry':<12} {'LTP':<12} {'P&L':<15}")
            print("="*120)
            
            for pos in positions[:10]:  # Show first 10
                print(f"{pos['symbol']:<30} "
                      f"{pos.get('option_type', 'N/A'):<8} "
                      f"{pos['quantity']:<10.0f} "
                      f"${pos['price']:<11.2f} "
                      f"${pos['ltp']:<11.2f} "
                      f"${pos['pnl']:<14,.2f}")
            
            print("="*120 + "\n")
        
        # Show P&L by run
        print(f"\nP&L by Run (Recent 10):")
        daily_pnl = self.extract_daily_pnl(strategy_data)
        
        for date_key in sorted(list(daily_pnl.keys())[-10:]):
            pnl_data = daily_pnl[date_key]
            print(f"  {pnl_data['date']:<30}: ${pnl_data['pnl']:>12,.2f}")


def main():
    """Main execution"""
    
    print("="*70)
    print("TRADETRON COUNTER EXPORT EXTRACTOR")
    print("="*70)
    
    extractor = CounterExportExtractor()
    
    # List all strategies
    print("\n1️⃣  Available Strategies:")
    extractor.print_strategies()
    
    # Print details for first strategy (or specific ID if needed)
    print("\n2️⃣  Strategy Details:")
    extractor.print_strategy_details()  # Will use first available


if __name__ == "__main__":
    main()
