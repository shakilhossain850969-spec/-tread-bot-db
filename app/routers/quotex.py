from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app.services.quotex_service import quotex_service

router = APIRouter(
    prefix="/quotex",
    tags=["Quotex Trading API"]
)

logger = logging.getLogger(__name__)

class TradeRequest(BaseModel):
    symbol: str
    amount: float
    direction: str  # "CALL" or "PUT"
    duration: int = 60

@router.get("/status")
async def get_status():
    """Check if Quotex WebSocket is connected."""
    return {
        "is_connected": quotex_service.is_connected,
        "is_demo": quotex_service.is_demo
    }

@router.get("/balance")
async def get_balance():
    """Get the current account balance."""
    bal = await quotex_service.get_balance()
    return {"balance": bal}

@router.get("/assets")
async def get_assets():
    """Get all currently open assets with their payouts."""
    assets = await quotex_service.get_open_assets()
    return {"assets": assets}

@router.get("/candles/{symbol}")
async def get_candles(symbol: str, timeframe: str = "1m", count: int = 100):
    """Get live OHLC candles for a specific asset."""
    candles = await quotex_service.get_candles(symbol, timeframe, count)
    if candles is None:
        raise HTTPException(status_code=503, detail="Quotex service not connected or failed to fetch candles.")
    return {"symbol": symbol, "timeframe": timeframe, "candles": candles}

@router.post("/trade")
async def place_trade(req: TradeRequest):
    """Place a live trade on the Quotex platform."""
    if not quotex_service.is_connected:
        raise HTTPException(status_code=503, detail="Quotex service is not connected.")
    
    if req.direction.upper() not in ["CALL", "PUT"]:
        raise HTTPException(status_code=400, detail="Direction must be CALL or PUT.")
        
    result = await quotex_service.place_order(
        symbol=req.symbol,
        amount=req.amount,
        direction=req.direction.upper(),
        duration=req.duration
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return result
