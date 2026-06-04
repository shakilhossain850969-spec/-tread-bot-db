import uuid
import enum
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class NotificationType(str, enum.Enum):
    signal = "signal"
    system = "system"
    alert = "alert"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # null = broadcast
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    type = Column(SAEnum(NotificationType), default=NotificationType.system)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")
