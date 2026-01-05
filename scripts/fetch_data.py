#!/usr/bin/env python3
"""
New fetch script that handles errors gracefully.
"""
import sys
from pathlib import Path
import sqlite3
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from orca.core.config import config
import ccxt

def fetch_fresh_data():
    """Fetch fresh data ignoring existing database."""
    print("=" * 60)
    print("🐋 ORCA - Fresh Data Fetch (Ignore Existing)")
    print("=" * 60)
    
    # Create fresh database
    db_path = config.data.db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize exchange
    exchange = ccxt.binance({'enableRateLimit': True})
    
    for symbol in config.data.symbols:
        print(f"\n📊 Symbol: {symbol}")
        
        for timeframe in config.data.timeframes:
            print(f"  Timeframe: {timeframe}")
            
            try:
                # Fetch fresh data
                ohlcv = exchange.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=1000  # Just get recent data
                )
                
                if not ohlcv:
                    print(f"    ❌ No data")
                    continue
                
                # Create DataFrame
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Save to database
                with sqlite3.connect(db_path) as conn:
                    for _, row in df.iterrows():
                        conn.execute("""
                        INSERT OR REPLACE INTO ohlcv 
                        (symbol, timeframe, timestamp, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            symbol, timeframe,
                            int(row['timestamp'].timestamp() * 1000),
                            float(row['open']), float(row['high']),
                            float(row['low']), float(row['close']),
                            float(row['volume'])
                        ))
                
                print(f"    ✅ {len(df)} candles saved")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
    
    print("\n✅ Fresh data fetch complete!")

if __name__ == "__main__":
    fetch_fresh_data()