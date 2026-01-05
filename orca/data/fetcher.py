import sqlite3
import pandas as pd
import ccxt
from loguru import logger
import time
from datetime import datetime, timedelta
import os

class DataFetcher:
    def __init__(self, db_path="data/market_data.db"):
        self.db_path = db_path
        self.exchange = ccxt.binance()
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Table for OHLCV data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ohlcv (
                symbol TEXT,
                timestamp INTEGER,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (symbol, timestamp)
            )
        """)
        # Table for fetched symbols and time ranges
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbol_info (
                symbol TEXT PRIMARY KEY,
                first_timestamp INTEGER,
                last_timestamp INTEGER,
                timeframe TEXT
            )
        """)
        conn.commit()
        conn.close()

    def fetch_ohlcv(self, symbol, timeframe='5m', since=None, limit=1000):
        """Fetch OHLCV data from exchange."""
        try:
            data = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['symbol'] = symbol
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def store_ohlcv(self, df):
        """Store OHLCV data in the database."""
        if df.empty:
            return
        conn = sqlite3.connect(self.db_path)
        try:
            df.to_sql('ohlcv', conn, if_exists='append', index=False, method='multi')
        except sqlite3.IntegrityError:
            # Duplicate data, we can ignore or update
            pass
        finally:
            conn.close()

    def update_symbol_info(self, symbol, timeframe, first_ts, last_ts):
        """Update the symbol info table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO symbol_info (symbol, first_timestamp, last_timestamp, timeframe)
            VALUES (?, ?, ?, ?)
        """, (symbol, first_ts, last_ts, timeframe))
        conn.commit()
        conn.close()

    def get_last_timestamp(self, symbol):
        """Get the last timestamp for a symbol from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT last_timestamp FROM symbol_info WHERE symbol=?", (symbol,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        return None

    def download_historical_data(self, symbol, timeframe='5m', start_date="2023-01-01", end_date=None):
        """Download historical data from start_date to end_date (or now)."""
        since = int(pd.Timestamp(start_date).timestamp() * 1000)
        if end_date:
            end_timestamp = int(pd.Timestamp(end_date).timestamp() * 1000)
        else:
            end_timestamp = int(time.time() * 1000)

        all_data = []
        while since < end_timestamp:
            logger.info(f"Fetching data for {symbol} from {pd.Timestamp(since, unit='ms')}")
            df = self.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
            if df.empty:
                break
            since = df['timestamp'].iloc[-1] + 1
            all_data.append(df)
            time.sleep(self.exchange.rateLimit / 1000)  # Respect rate limit

        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            # Filter to only up to end_timestamp
            final_df = final_df[final_df['timestamp'] <= end_timestamp]
            # Store in database
            self.store_ohlcv(final_df)
            # Update symbol info
            first_ts = final_df['timestamp'].iloc[0]
            last_ts = final_df['timestamp'].iloc[-1]
            self.update_symbol_info(symbol, timeframe, first_ts, last_ts)
            logger.success(f"Downloaded {len(final_df)} rows for {symbol}")
        else:
            logger.warning(f"No data downloaded for {symbol}")

if __name__ == "__main__":
    fetcher = DataFetcher()
    # Example: download BTC/USDT 5min data from 2023-01-01 to now
    fetcher.download_historical_data("BTC/USDT", timeframe="5m", start_date="2023-01-01")