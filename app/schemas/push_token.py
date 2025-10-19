from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class PushTokenCreate(BaseModel):
    """Schema for creating/registering a push token"""
    expo_push_token: str = Field(..., description="Expo push token from device")
    device_type: str = Field(..., description="Device type: 'ios' or 'android'")
    device_name: Optional[str] = Field(None, max_length=100, description="Device model name (e.g., 'iPhone 14', 'Pixel 6')")
    
    @validator('expo_push_token')
    def validate_expo_token(cls, v):
        if not v.startswith(("ExponentPushToken[", "ExpoPushToken[")):
            raise ValueError('Invalid Expo push token format. Must start with "ExponentPushToken[" or "ExpoPushToken["')
        if not v.endswith("]"):
            raise ValueError('Invalid Expo push token format. Must end with "]"')
        return v
    
    @validator('device_type')
    def validate_device_type(cls, v):
        if v.lower() not in ['ios', 'android']:
            raise ValueError('Device type must be "ios" or "android"')
        return v.lower()


class PushTokenDelete(BaseModel):
    """Schema for deleting/unregistering a push token"""
    expo_push_token: str = Field(..., description="Expo push token to unregister")


class PushTokenResponse(BaseModel):
    """Schema for push token response"""
    id: int
    user_id: int
    expo_push_token: str
    device_type: str
    device_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_used_at: datetime
    
    class Config:
        from_attributes = True


class PushTokenListResponse(BaseModel):
    """Schema for list of push tokens"""
    success: bool = True
    data: list[PushTokenResponse]
    total: int


class PushNotificationPayload(BaseModel):
    """Schema for sending a push notification"""
    title: str = Field(..., max_length=200, description="Notification title")
    body: str = Field(..., max_length=500, description="Notification body")
    data: Optional[dict] = Field(None, description="Additional data payload")
    sound: Optional[str] = Field("default", description="Sound to play")
    badge: Optional[int] = Field(None, description="Badge count")
    channel_id: str = Field("default", description="Android notification channel")
    priority: str = Field("high", description="Notification priority: 'default' or 'high'")
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['default', 'high']:
            raise ValueError('Priority must be "default" or "high"')
        return v
