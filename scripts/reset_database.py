#!/usr/bin/env python3
"""
Reset the database and start fresh.
"""
import os
import sqlite3
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from orca.core.config import config

def reset_database():
    """Completely reset the database."""
    db_path = config.data.db_path
    
    print("=" * 60)
    print("🐋 ORCA - Database Reset")
    print("=" * 60)
    
    if db_path.exists():
        # Backup old database
        backup_path = db_path.parent / f"market.db.backup_{Path(db_path).stat().st_mtime}"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"📂 Backup created: {backup_path}")
        
        # Delete database
        db_path.unlink()
        print(f"🗑️  Database deleted: {db_path}")
    
    # Recreate directory structure
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE ohlcv (
        symbol TEXT,
        timeframe TEXT,
        timestamp INTEGER,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        PRIMARY KEY (symbol, timeframe, timestamp)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE metadata (
        symbol TEXT,
        timeframe TEXT,
        last_update INTEGER,
        PRIMARY KEY (symbol, timeframe)
    )
    """)
    
    # Create indices
    cursor.execute("""
    CREATE INDEX idx_ohlcv_symbol_timeframe ON ohlcv(symbol, timeframe)
    """)
    
    cursor.execute("""
    CREATE INDEX idx_ohlcv_timestamp ON ohlcv(timestamp)
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ New database created: {db_path}")
    print(f"📊 Size: 0 MB")
    
    print("\n" + "=" * 60)
    print("🎯 Next steps:")
    print("1. Run: python scripts/fetch_data.py")
    print("2. Run: python scripts/backtest_baseline.py")
    print("=" * 60)

if __name__ == "__main__":
    reset_database()