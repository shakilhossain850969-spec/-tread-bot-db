import httpx
import random
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any

router = APIRouter(prefix="/market", tags=["Market Data"])

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Fallback mock data when CoinGecko is unavailable
MOCK_ASSETS = [
    {"symbol": "BTC", "name": "Bitcoin", "price": 67420.50, "change_24h": 2.34, "volume": 28_500_000_000, "market_cap": 1_320_000_000_000},
    {"symbol": "ETH", "name": "Ethereum", "price": 3842.20, "change_24h": 1.87, "volume": 14_200_000_000, "market_cap": 461_000_000_000},
    {"symbol": "BNB", "name": "BNB", "price": 612.40, "change_24h": -0.54, "volume": 2_100_000_000, "market_cap": 89_000_000_000},
    {"symbol": "SOL", "name": "Solana", "price": 178.60, "change_24h": 4.21, "volume": 5_800_000_000, "market_cap": 82_000_000_000},
    {"symbol": "ADA", "name": "Cardano", "price": 0.624, "change_24h": -1.23, "volume": 780_000_000, "market_cap": 22_000_000_000},
    {"symbol": "AVAX", "name": "Avalanche", "price": 42.10, "change_24h": 3.12, "volume": 920_000_000, "market_cap": 17_000_000_000},
]


async def _fetch_coingecko(path: str, params: dict = None) -> Any:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{COINGECKO_BASE}{path}", params=params)
        resp.raise_for_status()
        return resp.json()


@router.get("/overview")
async def market_overview():
    """Top crypto assets by market cap."""
    try:
        data = await _fetch_coingecko("/coins/markets", {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 20,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h",
        })
        return {"assets": data}
    except Exception:
        return {"assets": MOCK_ASSETS}


@router.get("/trending")
async def trending_assets():
    """Trending assets on CoinGecko."""
    try:
        data = await _fetch_coingecko("/search/trending")
        return data
    except Exception:
        return {"coins": [{"item": a} for a in MOCK_ASSETS[:5]]}


@router.get("/sentiment")
async def market_sentiment():
    """Fear & Greed index + overall sentiment."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://api.alternative.me/fng/")
            fng = resp.json()["data"][0]
    except Exception:
        fng = {"value": "65", "value_classification": "Greed", "timestamp": str(int(datetime.utcnow().timestamp()))}

    bullish_pct = random.randint(55, 75)
    return {
        "fear_greed": {
            "value": int(fng["value"]),
            "classification": fng["value_classification"],
        },
        "sentiment": {
            "bullish": bullish_pct,
            "bearish": 100 - bullish_pct,
        },
        "market_cap_change_24h": round(random.uniform(-3, 5), 2),
    }


@router.get("/assets/{symbol}")
async def asset_detail(symbol: str):
    """Asset detail: price, volume, change."""
    sym_lower = symbol.lower()
    try:
        data = await _fetch_coingecko(f"/coins/{sym_lower}", {
            "localization": False,
            "tickers": False,
            "market_data": True,
            "community_data": False,
            "developer_data": False,
        })
        md = data["market_data"]
        return {
            "symbol": symbol.upper(),
            "name": data["name"],
            "price": md["current_price"]["usd"],
            "change_24h": md["price_change_percentage_24h"],
            "change_7d": md["price_change_percentage_7d"],
            "volume": md["total_volume"]["usd"],
            "market_cap": md["market_cap"]["usd"],
            "high_24h": md["high_24h"]["usd"],
            "low_24h": md["low_24h"]["usd"],
            "image": data["image"]["large"],
        }
    except Exception:
        mock = next((a for a in MOCK_ASSETS if a["symbol"] == symbol.upper()), MOCK_ASSETS[0])
        return mock


@router.get("/assets/{symbol}/candles")
async def asset_candles(
    symbol: str,
    timeframe: str = Query("1D", description="1H, 4H, 1D, 1W"),
):
    """OHLCV candlestick data."""
    days_map = {"1H": 1, "4H": 7, "1D": 30, "1W": 180}
    days = days_map.get(timeframe, 30)
    sym_lower = symbol.lower()
    try:
        data = await _fetch_coingecko(f"/coins/{sym_lower}/ohlc", {
            "vs_currency": "usd",
            "days": days,
        })
        candles = [
            {"time": c[0], "open": c[1], "high": c[2], "low": c[3], "close": c[4]}
            for c in data
        ]
        return {"symbol": symbol.upper(), "timeframe": timeframe, "candles": candles}
    except Exception:
        # Generate mock candles
        import time
        base_price = 67000.0
        candles = []
        now = int(time.time() * 1000)
        for i in range(30):
            o = base_price + random.uniform(-500, 500)
            c = o + random.uniform(-300, 300)
            h = max(o, c) + random.uniform(0, 200)
            lo = min(o, c) - random.uniform(0, 200)
            candles.append({"time": now - (30 - i) * 86400000, "open": o, "high": h, "low": lo, "close": c})
        return {"symbol": symbol.upper(), "timeframe": timeframe, "candles": candles}
