from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class EnginePredictRequest(BaseModel):
    symbol: str
    timeframe: str = "1H"

class EnginePredictResponse(BaseModel):
    symbol: str
    timeframe: str
    signal: str
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    reasons: List[str] = []
    models: Dict[str, float]
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "timeframe": "1H",
                "signal": "BUY",
                "confidence": 84.5,
                "entry_price": 67420.5,
                "stop_loss": 66500.0,
                "take_profit": 69000.0,
                "reasons": ["Bullish Engulfing", "Bouncing off Support"],
                "models": {
                    "trend_score": 20.0,
                    "momentum_score": 15.0,
                    "price_action_score": 25.0,
                    "fractal_score": 15.0,
                    "ai_score": 15.0
                }
            }
        }

class EngineScanRequest(BaseModel):
    pairs: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None

class EngineScanResponse(BaseModel):
    total_scanned: int
    actionable_signals: int
    signals: List[Dict[str, Any]]
    alerts_triggered: List[Dict[str, Any]]
