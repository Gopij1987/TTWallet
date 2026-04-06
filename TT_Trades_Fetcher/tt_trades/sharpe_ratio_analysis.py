"""
Sharpe Ratio Analysis for Trading Strategy
Calculates daily returns, volatility, and Sharpe ratio
"""

import json
from pathlib import Path
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime


class SharpeRatioAnalyzer:
    """Analyze Sharpe ratio and performance metrics for a strategy"""
    
    def __init__(self, strategy_json_path: str):
        """Initialize with strategy JSON file"""
        self.strategy_path = Path(strategy_json_path)
        self.strategy_data = self._load_strategy()
        
    def _load_strategy(self) -> Dict:
        """Load strategy JSON"""
        with open(self.strategy_path, 'r') as f:
            return json.load(f)
    
    def extract_pnl_values(self) -> Tuple[List[float], List[int]]:
        """Extract PnL values and run counters from daily analysis"""
        daily_pnl = self.strategy_data.get('daily_pnl_analysis', {})
        
        pnl_values = []
        run_counters = []
        
        # Sort by run counter (descending - most recent first, then reverse for chronological)
        sorted_runs = sorted(
            daily_pnl.items(),
            key=lambda x: x[1].get('run_counter', 0),
            reverse=True
        )
        sorted_runs.reverse()  # Now in chronological order (oldest first)
        
        for run_key, run_data in sorted_runs:
            pnl = run_data.get('pnl', 0)
            run_counter = run_data.get('run_counter', 0)
            pnl_values.append(float(pnl))
            run_counters.append(run_counter)
        
        return pnl_values, run_counters
    
    def calculate_returns(self, pnl_values: List[float], capital: float) -> np.ndarray:
        """Calculate daily returns as percentage of capital"""
        returns = np.array([pnl / capital for pnl in pnl_values])
        return returns
    
    def calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe Ratio
        
        Sharpe Ratio = (Mean Return - Risk-Free Rate) / Std Dev of Returns
        
        For daily calculations, we use:
        - Daily risk-free rate ≈ 0 (or annual rate / 252)
        - Standard deviation of daily returns
        """
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)  # Sample std dev
        
        if std_return == 0:
            return 0.0
        
        sharpe = (mean_return - risk_free_rate) / std_return
        return sharpe
    
    def calculate_annualized_sharpe(self, sharpe_daily: float, trading_days: int = 252) -> float:
        """Convert daily Sharpe ratio to annualized"""
        return sharpe_daily * np.sqrt(trading_days)
    
    def analyze(self) -> Dict:
        """Perform complete Sharpe ratio analysis"""
        # Get basic strategy info
        strategy_id = self.strategy_data.get('strategy_id')
        strategy_name = self.strategy_data.get('strategy_name')
        capital_required = self.strategy_data.get('capital_required')
        total_pnl = self.strategy_data.get('total_pnl')
        
        # Extract PnL values
        pnl_values, run_counters = self.extract_pnl_values()
        num_days = len(pnl_values)
        
        # Calculate returns
        returns = self.calculate_returns(pnl_values, capital_required)
        
        # Calculate metrics
        mean_daily_return = np.mean(returns)
        std_daily_return = np.std(returns, ddof=1)
        min_daily_return = np.min(returns)
        max_daily_return = np.max(returns)
        
        # Sharpe Ratio (daily and annualized)
        sharpe_daily = self.calculate_sharpe_ratio(returns)
        sharpe_annual = self.calculate_annualized_sharpe(sharpe_daily)
        
        # Win rate
        winning_days = len([r for r in returns if r > 0])
        win_rate = (winning_days / num_days * 100) if num_days > 0 else 0
        
        # Cumulative returns
        cumulative_return = np.sum(returns)
        
        # Drawdown analysis
        cumulative_pnl = np.cumsum(pnl_values)
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = cumulative_pnl - running_max
        max_drawdown = np.min(drawdown)
        max_drawdown_pct = (max_drawdown / capital_required * 100) if capital_required > 0 else 0
        
        # Profit factor
        gross_profit = sum([p for p in pnl_values if p > 0])
        gross_loss = abs(sum([p for p in pnl_values if p < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Return on Capital
        roc = (total_pnl / capital_required * 100) if capital_required > 0 else 0
        
        return {
            'strategy_id': strategy_id,
            'strategy_name': strategy_name,
            'extraction_date': self.strategy_data.get('extraction_date'),
            'status': self.strategy_data.get('status'),
            
            # Capital & PnL
            'capital_required': capital_required,
            'total_pnl': total_pnl,
            'roi_percent': roc,
            
            # Returns Analysis
            'num_trading_days': num_days,
            'mean_daily_return': mean_daily_return,
            'mean_daily_return_percent': mean_daily_return * 100,
            'std_daily_return': std_daily_return,
            'std_daily_return_percent': std_daily_return * 100,
            'min_daily_return_percent': min_daily_return * 100,
            'max_daily_return_percent': max_daily_return * 100,
            'cumulative_return_percent': cumulative_return * 100,
            
            # Sharpe Ratio
            'sharpe_ratio_daily': sharpe_daily,
            'sharpe_ratio_annualized': sharpe_annual,
            
            # Win/Loss
            'winning_days': winning_days,
            'losing_days': num_days - winning_days,
            'win_rate_percent': win_rate,
            'profit_factor': profit_factor,
            
            # Drawdown
            'max_drawdown': max_drawdown,
            'max_drawdown_percent': max_drawdown_pct,
            
            # Run details
            'first_run': int(run_counters[0]),
            'last_run': int(run_counters[-1]),
            'total_runs': num_days,
        }


def print_analysis(analysis: Dict):
    """Print analysis in a readable format"""
    print("\n" + "="*70)
    print("SHARPE RATIO ANALYSIS - TRADING STRATEGY")
    print("="*70)
    
    print(f"\nStrategy: {analysis['strategy_name']} (ID: {analysis['strategy_id']})")
    print(f"Status: {analysis['status']}")
    print(f"Extracted: {analysis['extraction_date']}")
    
    print("\n" + "-"*70)
    print("CAPITAL & PnL SUMMARY")
    print("-"*70)
    print(f"Capital Required:           ₹{analysis['capital_required']:,.2f}")
    print(f"Total P&L:                  ₹{analysis['total_pnl']:,.2f}")
    print(f"Return on Capital (ROC):    {analysis['roi_percent']:.2f}%")
    
    print("\n" + "-"*70)
    print("RETURNS ANALYSIS")
    print("-"*70)
    print(f"Trading Days (Runs):        {analysis['num_trading_days']}")
    print(f"Run Range:                  {analysis['first_run']} to {analysis['last_run']}")
    print(f"Mean Daily Return:          {analysis['mean_daily_return_percent']:.4f}%")
    print(f"Std Dev (Daily):            {analysis['std_daily_return_percent']:.4f}%")
    print(f"Min Daily Return:           {analysis['min_daily_return_percent']:.4f}%")
    print(f"Max Daily Return:           {analysis['max_daily_return_percent']:.4f}%")
    print(f"Cumulative Return:          {analysis['cumulative_return_percent']:.2f}%")
    
    print("\n" + "-"*70)
    print("⭐ SHARPE RATIO")
    print("-"*70)
    print(f"Daily Sharpe Ratio:         {analysis['sharpe_ratio_daily']:.4f}")
    print(f"Annualized Sharpe Ratio:    {analysis['sharpe_ratio_annualized']:.4f}")
    
    print("\n" + "-"*70)
    print("PERFORMANCE METRICS")
    print("-"*70)
    print(f"Winning Days:               {analysis['winning_days']} / {analysis['num_trading_days']}")
    print(f"Win Rate:                   {analysis['win_rate_percent']:.2f}%")
    print(f"Profit Factor:              {analysis['profit_factor']:.4f}")
    print(f"Max Drawdown:               ₹{analysis['max_drawdown']:,.2f}")
    print(f"Max Drawdown %:             {analysis['max_drawdown_percent']:.2f}%")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    import sys
    
    # Default strategy file
    strategy_file = Path(__file__).parent / "strategy_7147483_complete_20260308_210353.json"
    
    # Check if a different file was provided
    if len(sys.argv) > 1:
        strategy_file = Path(sys.argv[1])
    
    if not strategy_file.exists():
        print(f"Error: Strategy file not found: {strategy_file}")
        sys.exit(1)
    
    analyzer = SharpeRatioAnalyzer(str(strategy_file))
    analysis = analyzer.analyze()
    print_analysis(analysis)
    
    # Also print JSON for easy parsing
    print("\n[JSON OUTPUT]")
    print(json.dumps(analysis, indent=2))
