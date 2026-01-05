#!/usr/bin/env python3
"""
Debug script to check database issues.
"""
import sys
import sqlite3
import pandas as pd
from pathlib import Path
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from orca.core.config import config

def check_database():
    """Check database for issues."""
    print("=" * 60)
    print("🐋 ORCA - Database Debug")
    print("=" * 60)
    
    db_path = config.data.db_path
    print(f"Database: {db_path}")
    print(f"Exists: {db_path.exists()}")
    
    if not db_path.exists():
        print("❌ Database doesn't exist!")
        return
    
    # Check size
    size_mb = db_path.stat().st_size / 1024 / 1024
    print(f"Size: {size_mb:.2f} MB")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Check tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📊 Tables: {[t[0] for t in tables]}")
        
        # Check ohlcv table
        print("\n🔍 Checking OHLCV table...")
        df = pd.read_sql_query("SELECT * FROM ohlcv LIMIT 10", conn)
        print(f"First 10 rows:")
        print(df)
        
        # Check for NaT/NULL
        print("\n🔍 Checking for invalid data...")
        cursor.execute("SELECT COUNT(*) FROM ohlcv WHERE timestamp IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"NULL timestamps: {null_count}")
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM ohlcv")
        min_ts, max_ts = cursor.fetchone()
        print(f"Timestamp range: {min_ts} to {max_ts}")
        
        # Convert to datetime to check
        if min_ts and max_ts:
            min_dt = pd.to_datetime(min_ts, unit='ms')
            max_dt = pd.to_datetime(max_ts, unit='ms')
            print(f"Date range: {min_dt} to {max_dt}")
        
        # Check metadata table
        print("\n🔍 Checking metadata table...")
        df_meta = pd.read_sql_query("SELECT * FROM metadata", conn)
        print(df_meta)
        
        # Test loading data properly
        print("\n🔍 Testing data loading (FIXED VERSION)...")
        query = """
        SELECT timestamp, open, high, low, close, volume 
        FROM ohlcv 
        WHERE symbol = 'BTC/USDT' AND timeframe = '5m'
        ORDER BY timestamp 
        LIMIT 5
        """
        # CORRECTION: Ne pas utiliser parse_dates
        df_test = pd.read_sql_query(query, conn)

        # Convertir manuellement
        df_test['timestamp'] = pd.to_datetime(df_test['timestamp'], unit='ms')
        print("Test load (first 5 rows) - FIXED:")
        print(df_test)
        
        # Check index
        if not df_test.empty:
            df_test.set_index('timestamp', inplace=True)
            print("\n🔍 Checking index...")
            print(f"Index type: {type(df_test.index)}")
            print(f"Has NaT: {df_test.index.isna().any()}")
            if df_test.index.isna().any():
                print(f"NaT positions: {np.where(df_test.index.isna())}")
        
        conn.close()
        
        print("\n✅ Database check complete!")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()