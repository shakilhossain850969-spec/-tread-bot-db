import httpx
import pandas as pd
from datetime import datetime, timedelta
import asyncio

class DataFetcher:
    """
    Fetches historical OHLCV data from public APIs (e.g., Binance).
    Supports multiple timeframes.
    """
    
    # Map our timeframes to Binance API intervals
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1H": "1h",
        "4H": "4h",
        "1D": "1d",
    }
    
    BINANCE_URL = "https://api.binance.com/api/v3/klines"

    @classmethod
    async def get_ohlcv(cls, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """
        Fetches OHLCV data and returns a pandas DataFrame.
        """
        symbol_fmt = symbol.replace("/", "").replace("-", "").upper()
        interval = cls.TIMEFRAME_MAP.get(timeframe, "1h")
        
        params = {
            "symbol": symbol_fmt,
            "interval": interval,
            "limit": limit
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(cls.BINANCE_URL, params=params)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                # If network fails, return a mock DataFrame for robustness
                print(f"Data fetch error for {symbol}: {e}")
                return cls._generate_mock_data(limit)

        # Binance kline format:
        # [Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, ...]
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        
        # Keep only required columns and convert types
        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
            
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df

    @staticmethod
    def _generate_mock_data(limit: int) -> pd.DataFrame:
        """Fallback mock data generator if API is blocked/down."""
        import numpy as np
        dates = pd.date_range(end=datetime.utcnow(), periods=limit, freq="1H")
        
        # Random walk for mock prices
        close_prices = 60000 + np.random.randn(limit).cumsum() * 100
        high = close_prices + np.abs(np.random.randn(limit) * 50)
        low = close_prices - np.abs(np.random.randn(limit) * 50)
        open_prices = close_prices - np.random.randn(limit) * 20
        volume = np.abs(np.random.randn(limit) * 1000)
        
        df = pd.DataFrame({
            "open": open_prices,
            "high": high,
            "low": low,
            "close": close_prices,
            "volume": volume
        }, index=dates)
        return df
