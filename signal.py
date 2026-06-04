from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.signal import SignalType, SignalStatus


class RawCandle(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

class RawSignalRequest(BaseModel):
    symbol: str
    timeframe: str
    candles: List[RawCandle]

class SignalCreate(BaseModel):
    symbol: str
    signal_type: SignalType
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    timeframe: str
    notes: Optional[str] = None

    @validator("confidence")
    def confidence_range(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Confidence must be between 0 and 100")
        return v

    @validator("stop_loss")
    def validate_stop_loss(cls, v, values):
        if "signal_type" in values and values["signal_type"] == SignalType.BUY:
            if "entry_price" in values and v >= values["entry_price"]:
                raise ValueError("Stop loss must be below entry price for BUY signals")
        return v

    def compute_risk_reward(self) -> float:
        reward = abs(self.take_profit - self.entry_price)
        risk = abs(self.entry_price - self.stop_loss)
        return round(reward / risk, 2) if risk > 0 else 0


class SignalUpdate(BaseModel):
    signal_type: Optional[SignalType] = None
    confidence: Optional[float] = None
    status: Optional[SignalStatus] = None
    notes: Optional[str] = None


class SignalResponse(BaseModel):
    id: UUID
    symbol: str
    signal_type: SignalType
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    timeframe: str
    status: SignalStatus
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SignalListResponse(BaseModel):
    signals: List[SignalResponse]
    total: int
    page: int
    page_size: int
