from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.trade import TradeResult


class TradeCreate(BaseModel):
    signal_id: UUID
    entry_price: float


class TradeClose(BaseModel):
    exit_price: float
    result: TradeResult


class TradeResponse(BaseModel):
    id: UUID
    signal_id: UUID
    result: TradeResult
    pnl: Optional[float]
    entry_price: Optional[float]
    exit_price: Optional[float]
    closed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TradeStats(BaseModel):
    total_trades: int
    wins: int
    losses: int
    pending: int
    accuracy_rate: float
    total_pnl: float


class NotificationCreate(BaseModel):
    title: str
    body: str
    type: str = "system"
    user_id: Optional[UUID] = None   # None = broadcast


class NotificationResponse(BaseModel):
    id: UUID
    title: str
    body: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    id: UUID
    plan: str
    status: str
    started_at: datetime
    expires_at: Optional[datetime]
    auto_renew: bool

    class Config:
        from_attributes = True


class AdminAnalytics(BaseModel):
    total_users: int
    active_users: int
    total_signals: int
    active_signals: int
    total_trades: int
    win_rate: float
    pro_subscribers: int
    elite_subscribers: int
