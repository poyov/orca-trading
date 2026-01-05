"""
Minimal data collector for cryptocurrency data.
Designed to run on a standard PC with limited storage.
"""
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

import ccxt
import pandas as pd
import numpy as np
from tqdm import tqdm

from orca.core.config import config

logger = logging.getLogger(__name__)

class DataCollector:
    """Minimal data collector for crypto data."""
    
    def __init__(self, exchange_name: str = None):
        """
        Initialize data collector.
        
        Args:
            exchange_name: Exchange name (default from config)
        """
        self.config = config
        self.exchange_name = exchange_name or self.config.data.exchange
        
        # Initialize CCXT exchange
        exchange_class = getattr(ccxt, self.exchange_name)
        self.exchange = exchange_class({
            'enableRateLimit': True,
            'rateLimit': 1000,  # Respect rate limits
            'options': {
                'defaultType': 'spot'
            }
        })
        
        # Database connection
        self.db_path = self.config.data.db_path
        self._init_database()
        
        logger.info(f"Initialized DataCollector for {self.exchange_name}")
    
    def _init_database(self):
        """Initialize SQLite database with minimal schema."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create OHLCV table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS ohlcv (
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
                
                # Create metadata table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    symbol TEXT,
                    timeframe TEXT,
                    last_update INTEGER,
                    PRIMARY KEY (symbol, timeframe)
                )
                """)
                
                # Create indices for faster queries
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timeframe 
                ON ohlcv(symbol, timeframe)
                """)
                
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ohlcv_timestamp 
                ON ohlcv(timestamp)
                """)
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str,
        days: int = None,
        force_update: bool = False
    ) -> pd.DataFrame:
        """
        Fetch historical data with smart updating.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Timeframe (e.g., "5m", "1h")
            days: Number of days to fetch (default from config)
            force_update: Force re-fetch even if data exists
            
        Returns:
            DataFrame with OHLCV data
        """
        # Use config value if days not specified
        if days is None:
            days = self.config.data.fetch_days
        
        logger.info(f"Fetching data for {symbol} {timeframe} ({days} days)")
        
        try:
            # Calculate start time
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # Convert to milliseconds
            since = int(start_time.timestamp() * 1000)
            
            # Check what we already have
            existing_data = self._get_existing_data(symbol, timeframe)
            
            # CORRECTION ICI : Vérifier si existing_data n'est pas vide
            if not existing_data.empty and not force_update:
                last_timestamp = existing_data.index.max()
                if pd.notna(last_timestamp):  # Vérifier que ce n'est pas NaT
                    last_timestamp_ms = int(last_timestamp.timestamp() * 1000)
                    if last_timestamp_ms > since:
                        since = last_timestamp_ms + 1  # Start from after last record
                        days_needed = (end_time - last_timestamp).days
                        logger.info(f"Resuming from existing data, fetching {days_needed} new days")
                else:
                    logger.warning(f"Last timestamp is NaT, fetching full {days} days")
            else:
                logger.info(f"No existing data or force update, fetching full {days} days")
            
            # Fetch data with progress bar
            all_ohlcv = []
            current_since = since
            
            with tqdm(total=days, desc=f"Fetching {symbol} {timeframe}") as pbar:
                while current_since < end_time.timestamp() * 1000:
                    try:
                        ohlcv = self.exchange.fetch_ohlcv(
                            symbol=symbol,
                            timeframe=timeframe,
                            since=current_since,
                            limit=1000  # Maximum per request
                        )
                        
                        if not ohlcv:
                            logger.warning(f"No more data available for {symbol} {timeframe}")
                            break
                        
                        df_batch = pd.DataFrame(
                            ohlcv,
                            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                        )
                        
                        df_batch['timestamp'] = pd.to_datetime(df_batch['timestamp'], unit='ms')
                        df_batch.set_index('timestamp', inplace=True)
                        
                        all_ohlcv.append(df_batch)
                        
                        # Update progress
                        batch_days = len(df_batch) * self._timeframe_to_minutes(timeframe) / (24 * 60)
                        pbar.update(min(batch_days, days - pbar.n))
                        
                        # Move to next batch
                        current_since = int(df_batch.index[-1].timestamp() * 1000) + 1
                        
                        # Rate limiting
                        time.sleep(self.exchange.rateLimit / 1000)
                        
                    except ccxt.NetworkError as e:
                        logger.warning(f"Network error: {e}, retrying in 5 seconds...")
                        time.sleep(5)
                    except ccxt.ExchangeError as e:
                        logger.error(f"Exchange error: {e}")
                        break
            
            if not all_ohlcv:
                logger.warning(f"No data fetched for {symbol} {timeframe}")
                return existing_data if not existing_data.empty else pd.DataFrame()
            
            # Combine all batches
            new_data = pd.concat(all_ohlcv)
            new_data = new_data[~new_data.index.duplicated(keep='first')]
            
            # Merge with existing data
            if not existing_data.empty:
                combined_data = pd.concat([existing_data, new_data])
                combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                combined_data.sort_index(inplace=True)
            else:
                combined_data = new_data
            
            # Remove duplicates and sort
            combined_data = combined_data[~combined_data.index.duplicated()]
            combined_data.sort_index(inplace=True)
            
            # Save to database
            self._save_to_database(symbol, timeframe, combined_data)
            
            logger.info(f"Fetched {len(combined_data)} candles for {symbol} {timeframe}")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} {timeframe}: {e}")
            import traceback
            logger.error(traceback.format_exc())  # Ajoute le stack trace pour debug
            return pd.DataFrame()
    
    def _get_existing_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Get existing data from database with proper timestamp handling."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT timestamp, open, high, low, close, volume
                FROM ohlcv
                WHERE symbol = ? AND timeframe = ?
                ORDER BY timestamp
                """
                
                # IMPORTANT: Ne pas utiliser parse_dates ici
                # On convertira manuellement après
                df = pd.read_sql_query(
                    query,
                    conn,
                    params=(symbol, timeframe)
                )
                
                if df.empty:
                    return pd.DataFrame()
                
                # Convertir les timestamps (millisecondes -> datetime)
                # Gérer les valeurs NULL/Nan
                df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
                df = df.dropna(subset=['timestamp'])
                
                if df.empty:
                    return pd.DataFrame()
                
                # Conversion avec unit='ms' pour millisecondes
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # Vérifier qu'il n'y a pas de NaT
                if df.index.isna().any():
                    logger.warning(f"Found NaT in index for {symbol} {timeframe}, removing")
                    df = df[df.index.notna()]
                
                return df
                
        except Exception as e:
            logger.warning(f"Could not load existing data: {e}")
            import traceback
            logger.warning(traceback.format_exc())
            return pd.DataFrame()
        
    def _save_to_database(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """Save data to SQLite database."""
        if data.empty:
            return
        
        try:
            # Clean data: remove any rows with NaT in index
            data_clean = data.copy()
            data_clean = data_clean[data_clean.index.notna()]
            
            if data_clean.empty:
                logger.warning(f"No valid timestamps for {symbol} {timeframe}, skipping save")
                return
            
            with sqlite3.connect(self.db_path) as conn:
                # Prepare data for insertion
                records = []
                for idx, row in data_clean.iterrows():
                    # Vérifier que l'index n'est pas NaT
                    if pd.isna(idx):
                        continue
                        
                    try:
                        timestamp_ms = int(idx.timestamp() * 1000)
                        records.append((
                            symbol,
                            timeframe,
                            timestamp_ms,
                            float(row['open']),
                            float(row['high']),
                            float(row['low']),
                            float(row['close']),
                            float(row['volume'])
                        ))
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Skipping invalid timestamp {idx}: {e}")
                        continue
                
                if not records:
                    logger.warning(f"No valid records to save for {symbol} {timeframe}")
                    return
                
                # Insert or replace
                cursor = conn.cursor()
                cursor.executemany("""
                INSERT OR REPLACE INTO ohlcv 
                (symbol, timeframe, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, records)
                
                # Update metadata with last valid timestamp
                last_timestamp = int(data_clean.index[-1].timestamp() * 1000)
                cursor.execute("""
                INSERT OR REPLACE INTO metadata (symbol, timeframe, last_update)
                VALUES (?, ?, ?)
                """, (symbol, timeframe, last_timestamp))
                
                conn.commit()
                
                logger.info(f"Saved {len(records)} records for {symbol} {timeframe}")
                
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes."""
        timeframe_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
        }
        return timeframe_map.get(timeframe, 60)
    
    def get_available_data(self) -> pd.DataFrame:
        """Get summary of available data in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT 
                    symbol,
                    timeframe,
                    MIN(timestamp) as first_date,
                    MAX(timestamp) as last_date,
                    COUNT(*) as candle_count
                FROM ohlcv
                GROUP BY symbol, timeframe
                ORDER BY symbol, timeframe
                """
                df = pd.read_sql_query(query, conn)
                
                if not df.empty:
                    df['first_date'] = pd.to_datetime(df['first_date'], unit='ms')
                    df['last_date'] = pd.to_datetime(df['last_date'], unit='ms')
                    df['days_available'] = (df['last_date'] - df['first_date']).dt.days
                
                return df
        except Exception as e:
            logger.error(f"Error getting available data: {e}")
            return pd.DataFrame()
    
    def cleanup_old_data(self, keep_days: int = 90):
        """Remove data older than keep_days to save space."""
        try:
            cutoff_time = int((datetime.now() - timedelta(days=keep_days)).timestamp() * 1000)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete old OHLCV data
                cursor.execute("""
                DELETE FROM ohlcv 
                WHERE timestamp < ?
                """, (cutoff_time,))
                
                rows_deleted = cursor.rowcount
                conn.commit()
                
                # Vacuum to reclaim space
                cursor.execute("VACUUM")
                
                logger.info(f"Cleaned up {rows_deleted} old records (older than {keep_days} days)")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")