#!/usr/bin/env python3
"""
Simple baseline backtesting for Orca.
FULLY CORRECTED VERSION
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from orca.data.collector import DataCollector
from orca.core.config import config

class BaselineBacktester:
    """Simple backtester for baseline strategies."""
    
    def __init__(self, initial_balance: float = None, commission: float = None):
        # Use config values if not specified
        self.initial_balance = initial_balance or config.trading.initial_balance
        self.commission = commission or config.trading.commission
        self.collector = DataCollector()
        # CORRECTION: Get fetch_days from config.data
        self.fetch_days = config.data.fetch_days if hasattr(config.data, 'fetch_days') else 30
    
    def buy_and_hold(self, symbol: str, timeframe: str) -> dict:
        """Buy and hold strategy (baseline)."""
        # Use fetch_days from config
        data = self.collector.fetch_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            days=self.fetch_days
        )
        
        # Clean data: remove any NaT in index
        if not data.empty:
            data = data[data.index.notna()]
        
        if data.empty or len(data) < 2:
            return {"error": f"Insufficient data: {len(data)} candles"}
        
        # Calculate returns
        initial_price = data['close'].iloc[0]
        final_price = data['close'].iloc[-1]
        
        # Buy at first candle, sell at last
        shares = self.initial_balance / initial_price
        final_value = shares * final_price
        
        # Apply commission (buy and sell)
        final_value *= (1 - self.commission) ** 2
        
        total_return = (final_value - self.initial_balance) / self.initial_balance
        
        # Calculate actual days for annualization
        actual_days = (data.index[-1] - data.index[0]).days
        if actual_days == 0:
            actual_days = 1  # Avoid division by zero
        
        annualized_return = (1 + total_return) ** (365/actual_days) - 1
        
        return {
            "strategy": "buy_and_hold",
            "initial_balance": self.initial_balance,
            "final_value": final_value,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "start_date": data.index[0],
            "end_date": data.index[-1],
            "actual_days": actual_days,
            "config_days": self.fetch_days,
            "candles": len(data)
        }
    
    def random_trader(self, symbol: str, timeframe: str, trade_prob: float = 0.05) -> dict:
        """Random trading strategy (for comparison)."""
        # Use fetch_days from config
        data = self.collector.fetch_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            days=self.fetch_days
        )
        
        # Clean data: remove any NaT in index
        if not data.empty:
            data = data[data.index.notna()]
        
        if data.empty or len(data) < 2:
            return {"error": f"Insufficient data: {len(data)} candles"}
        
        cash = self.initial_balance
        position = 0
        trades = []
        
        for i in range(1, len(data)):
            current_price = data['close'].iloc[i]
            
            # Random decision
            if np.random.random() < trade_prob:
                if position == 0:  # Buy
                    # Use all cash
                    shares = cash / current_price
                    cost = shares * current_price * (1 + self.commission)
                    
                    if cost <= cash:
                        position = shares
                        cash -= cost
                        trades.append({
                            'date': data.index[i],
                            'action': 'buy',
                            'price': current_price,
                            'shares': shares
                        })
                
                elif position > 0:  # Sell
                    proceeds = position * current_price * (1 - self.commission)
                    cash += proceeds
                    trades.append({
                        'date': data.index[i],
                        'action': 'sell',
                        'price': current_price,
                        'shares': position
                    })
                    position = 0
        
        # Close final position if any
        if position > 0:
            final_price = data['close'].iloc[-1]
            cash += position * final_price * (1 - self.commission)
        
        total_return = (cash - self.initial_balance) / self.initial_balance
        
        # Calculate actual days for annualization
        actual_days = (data.index[-1] - data.index[0]).days
        if actual_days == 0:
            actual_days = 1
        
        annualized_return = (1 + total_return) ** (365/actual_days) - 1
        
        return {
            "strategy": "random_trader",
            "initial_balance": self.initial_balance,
            "final_value": cash,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "trade_count": len(trades),
            "start_date": data.index[0],
            "end_date": data.index[-1],
            "actual_days": actual_days,
            "config_days": self.fetch_days,
            "candles": len(data)
        }
    
    def print_results(self, results: dict):
        """Print backtest results nicely."""
        print("\n" + "=" * 60)
        print(f"📊 BACKTEST RESULTS: {results['strategy'].upper()}")
        print("=" * 60)
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        print(f"📅 Period: {results['start_date'].date()} to {results['end_date'].date()}")
        print(f"📈 Config Days: {results['config_days']}")
        print(f"📈 Actual Trading Days: {results['actual_days']}")
        print(f"🕯️  Candles: {results.get('candles', 'N/A')}")
        print(f"💰 Initial Balance: ${results['initial_balance']:,.2f}")
        print(f"💰 Final Value: ${results['final_value']:,.2f}")
        print(f"🎯 Total Return: {results['total_return'] * 100:.2f}%")
        print(f"📊 Annualized Return: {results['annualized_return'] * 100:.2f}%")
        
        if 'trade_count' in results:
            print(f"🔄 Trades Executed: {results['trade_count']}")
        
        print("=" * 60)

def main():
    """Run baseline backtests."""
    print("=" * 60)
    print("🐋 ORCA - Baseline Backtesting (FINAL)")
    print("=" * 60)
    
    # Initialize backtester with config values
    backtester = BaselineBacktester()
    
    # Get configuration
    symbol = config.data.symbols[0]
    timeframe = config.data.timeframes[0]
    
    # Get fetch_days safely
    fetch_days = config.data.fetch_days if hasattr(config.data, 'fetch_days') else 30
    
    print(f"\nConfiguration:")
    print(f"  Symbol: {symbol}")
    print(f"  Timeframe: {timeframe}")
    print(f"  Fetch Days: {fetch_days}")
    print(f"  Commission: {config.trading.commission * 100}%")
    print(f"  Initial Balance: ${config.trading.initial_balance:,.2f}")
    
    print("\n" + "-" * 40)
    print("1. Buy & Hold Strategy")
    print("-" * 40)
    bh_results = backtester.buy_and_hold(symbol, timeframe)
    backtester.print_results(bh_results)
    
    print("\n" + "-" * 40)
    print("2. Random Trader (for comparison)")
    print("-" * 40)
    random_results = backtester.random_trader(symbol, timeframe, trade_prob=0.05)
    backtester.print_results(random_results)
    
    # Compare
    print("\n" + "=" * 60)
    print("🏆 COMPARISON")
    print("=" * 60)
    
    if "error" not in bh_results and "error" not in random_results:
        bh_return = bh_results['total_return'] * 100
        random_return = random_results['total_return'] * 100
        
        print(f"Buy & Hold Return: {bh_return:.2f}%")
        print(f"Random Trader Return: {random_return:.2f}%")
        
        if bh_return > random_return:
            print(f"\n✅ Buy & Hold outperformed Random Trader by {bh_return - random_return:.2f}%")
        else:
            print(f"\n⚠️  Random Trader outperformed Buy & Hold by {random_return - bh_return:.2f}%")
    
    print("\n" + "=" * 60)
    print("🎉 PHASE 1 COMPLETE!")
    print("\nNext: Phase 2 - Building our first RL agent!")
    print("=" * 60)

if __name__ == "__main__":
    main()