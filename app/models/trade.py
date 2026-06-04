import uuid
import enum
from sqlalchemy import Column, String, Float, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TradeResult(str, enum.Enum):
    win = "win"
    loss = "loss"
    pending = "pending"


class Trade(Base):
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=False)
    result = Column(SAEnum(TradeResult), default=TradeResult.pending)
    pnl = Column(Float, nullable=True)           # profit/loss %
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="trades")
    signal = relationship("Signal", back_populates="trades")
