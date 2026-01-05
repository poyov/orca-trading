from orca.data.fetcher import DataFetcher

if __name__ == "__main__":
    fetcher = DataFetcher()
    # Télécharge les données pour BTC/USDT et ETH/USDT en 5min, 1h et 1j
    pairs = ["BTC/USDT", "ETH/USDT"]
    timeframes = ["5m", "1h", "1d"]
    for pair in pairs:
        for tf in timeframes:
            print(f"Downloading {pair} {tf}")
            fetcher.download_historical_data(pair, timeframe=tf, start_date="2023-01-01")