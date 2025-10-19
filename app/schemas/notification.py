from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.notification import NotificationType, NotificationStatus


class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    extra_data: Optional[Dict[str, Any]] = None
    transaction_id: Optional[int] = None


class NotificationUpdate(BaseModel):
    status: Optional[NotificationStatus] = None


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: NotificationType
    title: str
    message: str
    extra_data: Optional[Dict[str, Any]] = None
    status: NotificationStatus
    transaction_id: Optional[int] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total_count: int
    unread_count: int
    page: int
    per_page: int
    total_pages: int


class TransactionNotificationData(BaseModel):
    """Data structure for transaction notification metadata"""
    transaction_hash: str
    amount: str
    token_symbol: str
    amount_in_user_currency: Optional[str] = None
    user_currency: Optional[str] = None
    sender_dari_address: Optional[str] = None
    receiver_dari_address: Optional[str] = None
    sender_wallet_address: Optional[str] = None
    receiver_wallet_address: Optional[str] = None
    transaction_time: str  # ISO format string
