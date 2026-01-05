#!/usr/bin/env python3
"""Test the timestamp fix."""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from orca.data.collector import DataCollector
from orca.core.config import config

def test_data_loading():
    """Test that data loads correctly."""
    print("Testing data loading fix...")
    
    collector = DataCollector()
    
    # Try to load data
    symbol = config.data.symbols[0]
    timeframe = config.data.timeframes[0]
    
    print(f"Loading {symbol} {timeframe}...")
    data = collector._get_existing_data(symbol, timeframe)
    
    print(f"Data shape: {data.shape}")
    print(f"Index type: {type(data.index)}")
    print(f"Has NaT: {data.index.isna().any() if not data.empty else 'empty'}")
    
    if not data.empty:
        print(f"First row index: {data.index[0]}")
        print(f"Last row index: {data.index[-1]}")
        print(f"Date range: {data.index[0]} to {data.index[-1]}")
    
    return not data.empty and not data.index.isna().any()

if __name__ == "__main__":
    success = test_data_loading()
    if success:
        print("\n✅ Data loading fixed successfully!")
    else:
        print("\n❌ Data loading still has issues")