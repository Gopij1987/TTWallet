"""
Utilities for trade data processing and analysis
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import statistics


class TradeAnalyzer:
    """Analyze trade data for performance metrics"""
    
    @staticmethod
    def calculate_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics from trades"""
        
        if not trades:
            return {}
        
        pnl_values = [t.get('pnl', 0) for t in trades if 'pnl' in t]
        
        winning_trades = [p for p in pnl_values if p > 0]
        losing_trades = [p for p in pnl_values if p < 0]
        breakeven_trades = [p for p in pnl_values if p == 0]
        
        metrics = {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'breakeven_trades': len(breakeven_trades),
            'win_rate_pct': (len(winning_trades) / len(trades) * 100) if trades else 0,
            'total_pnl': sum(pnl_values),
            'avg_pnl_per_trade': sum(pnl_values) / len(pnl_values) if pnl_values else 0,
            'max_profit': max(pnl_values) if pnl_values else 0,
            'max_loss': min(pnl_values) if pnl_values else 0,
            'std_dev_pnl': statistics.stdev(pnl_values) if len(pnl_values) > 1 else 0,
            'avg_winning_trade': sum(winning_trades) / len(winning_trades) if winning_trades else 0,
            'avg_losing_trade': sum(losing_trades) / len(losing_trades) if losing_trades else 0,
            'profit_factor': abs(sum(winning_trades) / sum(losing_trades)) if losing_trades else float('inf'),
        }
        
        return metrics
    
    @staticmethod
    def filter_by_date_range(trades: List[Dict[str, Any]], 
                           start_date: datetime, 
                           end_date: datetime,
                           date_field: str = 'entry_date') -> List[Dict[str, Any]]:
        """Filter trades by date range"""
        
        filtered = []
        for trade in trades:
            trade_date_str = trade.get(date_field)
            if trade_date_str:
                try:
                    trade_date = datetime.fromisoformat(trade_date_str)
                    if start_date <= trade_date <= end_date:
                        filtered.append(trade)
                except ValueError:
                    pass
        
        return filtered
    
    @staticmethod
    def group_by_symbol(trades: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group trades by trading symbol"""
        
        grouped = {}
        for trade in trades:
            symbol = trade.get('symbol', 'UNKNOWN')
            if symbol not in grouped:
                grouped[symbol] = []
            grouped[symbol].append(trade)
        
        return grouped
    
    @staticmethod
    def metrics_by_symbol(trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate metrics for each trading symbol"""
        
        symbol_trades = TradeAnalyzer.group_by_symbol(trades)
        symbol_metrics = {}
        
        for symbol, symbol_trade_list in symbol_trades.items():
            symbol_metrics[symbol] = TradeAnalyzer.calculate_metrics(symbol_trade_list)
        
        return symbol_metrics
    
    @staticmethod
    def get_top_performers(trades: List[Dict[str, Any]], 
                          metric: str = 'pnl',
                          top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top performing trades"""
        
        sorted_trades = sorted(trades, key=lambda t: t.get(metric, 0), reverse=True)
        return sorted_trades[:top_n]
    
    @staticmethod
    def get_worst_performers(trades: List[Dict[str, Any]], 
                            metric: str = 'pnl',
                            bottom_n: int = 10) -> List[Dict[str, Any]]:
        """Get worst performing trades"""
        
        sorted_trades = sorted(trades, key=lambda t: t.get(metric, 0))
        return sorted_trades[:bottom_n]


class TradeReportGenerator:
    """Generate formatted reports from trade data"""
    
    @staticmethod
    def generate_text_report(metrics: Dict[str, Any]) -> str:
        """Generate a formatted text report"""
        
        report = f"""
{'='*70}
TRADE PERFORMANCE REPORT
{'='*70}

OVERVIEW
--------
Total Trades:           {metrics.get('total_trades', 0)}
Winning Trades:         {metrics.get('winning_trades', 0)}
Losing Trades:          {metrics.get('losing_trades', 0)}
Breakeven Trades:       {metrics.get('breakeven_trades', 0)}

PERFORMANCE
-----------
Win Rate:               {metrics.get('win_rate_pct', 0):.2f}%
Total P&L:              ${metrics.get('total_pnl', 0):,.2f}
Avg P&L per Trade:      ${metrics.get('avg_pnl_per_trade', 0):,.2f}
Std Dev P&L:            ${metrics.get('std_dev_pnl', 0):,.2f}

EXTREMES
--------
Max Profit:             ${metrics.get('max_profit', 0):,.2f}
Max Loss:               ${metrics.get('max_loss', 0):,.2f}
Avg Winning Trade:      ${metrics.get('avg_winning_trade', 0):,.2f}
Avg Losing Trade:       ${metrics.get('avg_losing_trade', 0):,.2f}
Profit Factor:          {metrics.get('profit_factor', 0):.2f}x

{'='*70}
"""
        return report
    
    @staticmethod
    def generate_csv_header() -> str:
        """Get CSV header for custom exports"""
        
        return "Date,Symbol,Entry,Exit,PnL,PnL%,Duration,Status\n"
    
    @staticmethod
    def print_metrics_table(metrics_by_symbol: Dict[str, Dict[str, Any]]):
        """Print metrics in table format"""
        
        print("\n" + "="*100)
        print(f"{'Symbol':<10} {'Trades':<8} {'Wins':<8} {'W/R %':<8} {'Total P&L':<15} {'Avg P&L':<15} {'PF':<8}")
        print("="*100)
        
        for symbol, metrics in sorted(metrics_by_symbol.items()):
            print(f"{symbol:<10} "
                  f"{metrics.get('total_trades', 0):<8} "
                  f"{metrics.get('winning_trades', 0):<8} "
                  f"{metrics.get('win_rate_pct', 0):<8.2f} "
                  f"${metrics.get('total_pnl', 0):<14,.2f} "
                  f"${metrics.get('avg_pnl_per_trade', 0):<14,.2f} "
                  f"{metrics.get('profit_factor', 0):<8.2f}")
        
        print("="*100 + "\n")


def calculate_sharpe_ratio(trades: List[Dict[str, Any]], 
                          risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe ratio for trades"""
    
    pnl_values = [t.get('pnl', 0) for t in trades if 'pnl' in t]
    
    if len(pnl_values) < 2:
        return 0
    
    mean_pnl = statistics.mean(pnl_values)
    std_pnl = statistics.stdev(pnl_values)
    
    if std_pnl == 0:
        return 0
    
    # Annualized (assuming 252 trading days)
    sharpe = ((mean_pnl * 252) - risk_free_rate) / (std_pnl * (252 ** 0.5))
    return sharpe


def calculate_max_drawdown(trades: List[Dict[str, Any]]) -> float:
    """Calculate maximum drawdown from trades"""
    
    if not trades:
        return 0
    
    cumulative_pnl = 0
    peak = 0
    max_drawdown_val = 0
    
    for trade in trades:
        pnl = trade.get('pnl', 0)
        cumulative_pnl += pnl
        
        if cumulative_pnl > peak:
            peak = cumulative_pnl
        
        drawdown = peak - cumulative_pnl
        if drawdown > max_drawdown_val:
            max_drawdown_val = drawdown
    
    return max_drawdown_val


if __name__ == "__main__":
    # Example usage
    sample_trades = [
        {'symbol': 'AAPL', 'pnl': 100, 'entry_price': 150},
        {'symbol': 'AAPL', 'pnl': -50, 'entry_price': 151},
        {'symbol': 'GOOGL', 'pnl': 200, 'entry_price': 140},
        {'symbol': 'GOOGL', 'pnl': -100, 'entry_price': 142},
        {'symbol': 'MSFT', 'pnl': 150, 'entry_price': 380},
    ]
    
    metrics = TradeAnalyzer.calculate_metrics(sample_trades)
    print(TradeReportGenerator.generate_text_report(metrics))
    
    metrics_by_sym = TradeAnalyzer.metrics_by_symbol(sample_trades)
    TradeReportGenerator.print_metrics_table(metrics_by_sym)
    
    print(f"Sharpe Ratio: {calculate_sharpe_ratio(sample_trades):.2f}")
    print(f"Max Drawdown: ${calculate_max_drawdown(sample_trades):,.2f}")
