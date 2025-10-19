from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import uuid

from app.core.database import Base


class NotificationType(str, Enum):
    TRANSACTION_SENT = "transaction_sent"
    TRANSACTION_RECEIVED = "transaction_received"
    TRANSACTION_CONFIRMED = "transaction_confirmed"
    TRANSACTION_FAILED = "transaction_failed"
    LOGIN_ALERT = "login_alert"
    KYC_UPDATE = "kyc_update"
    SECURITY_ALERT = "security_alert"
    GENERAL = "general"
    ANNOUNCEMENT = "announcement"
    SYSTEM_UPDATE = "system_update"
    MAINTENANCE = "maintenance"
    # Common aliases that frontends might use
    ADMIN = "admin"
    BROADCAST = "broadcast"
    INFO = "info"
    NEWS = "news"
    UPDATE = "update"


class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification details
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Extra data for the notification
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    
    # Status
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.UNREAD, nullable=False)
    
    # Related entities
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    transaction = relationship("Transaction", overlaps="notifications")
