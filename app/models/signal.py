import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum as SAEnum, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SignalType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalStatus(str, enum.Enum):
    active = "active"
    closed = "closed"
    expired = "expired"


class Signal(Base):
    __tablename__ = "signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(SAEnum(SignalType), nullable=False)
    confidence = Column(Float, nullable=False)          # 0-100
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    risk_reward = Column(Float, nullable=False)
    timeframe = Column(String(10), nullable=False)       # 1H, 4H, 1D
    status = Column(SAEnum(SignalStatus), default=SignalStatus.active)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    trades = relationship("Trade", back_populates="signal")
