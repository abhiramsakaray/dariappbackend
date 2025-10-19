from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import math
import json

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.crud.notification import notification_crud
from app.schemas.notification import (
    NotificationResponse, 
    NotificationListResponse, 
    NotificationUpdate
)


router = APIRouter()


def parse_extra_data(extra_data):
    """Parse extra_data from JSON string to dict"""
    if extra_data is None:
        return None
    if isinstance(extra_data, dict):
        return extra_data
    if isinstance(extra_data, str):
        try:
            return json.loads(extra_data)
        except (json.JSONDecodeError, ValueError):
            return None
    return None


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationListResponse:
    """Get user notifications with pagination"""
    
    # Calculate offset
    skip = (page - 1) * per_page
    
    # Get notifications
    notifications = await notification_crud.get_user_notifications(
        db, current_user.id, skip, per_page, unread_only
    )
    
    # Get total count
    total_count = await notification_crud.get_user_notifications_count(
        db, current_user.id, unread_only
    )
    
    # Get unread count
    unread_count = await notification_crud.get_user_notifications_count(
        db, current_user.id, unread_only=True
    )
    
    # Calculate total pages
    total_pages = math.ceil(total_count / per_page)
    
    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                type=notification.type,
                title=notification.title,
                message=notification.message,
                extra_data=parse_extra_data(notification.extra_data),
                status=notification.status,
                transaction_id=notification.transaction_id,
                created_at=notification.created_at,
                read_at=notification.read_at
            )
            for notification in notifications
        ],
        total_count=total_count,
        unread_count=unread_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/unread/count")
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get count of unread notifications"""
    
    unread_count = await notification_crud.get_user_notifications_count(
        db, current_user.id, unread_only=True
    )
    
    return {"unread_count": unread_count}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationResponse:
    """Mark a specific notification as read"""
    
    notification = await notification_crud.mark_as_read(
        db, notification_id, current_user.id
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        type=notification.type,
        title=notification.title,
        message=notification.message,
        extra_data=parse_extra_data(notification.extra_data),
        status=notification.status,
        transaction_id=notification.transaction_id,
        created_at=notification.created_at,
        read_at=notification.read_at
    )


@router.patch("/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Mark all notifications as read"""
    
    updated_count = await notification_crud.mark_all_as_read(
        db, current_user.id
    )
    
    return {
        "message": f"Marked {updated_count} notifications as read",
        "updated_count": updated_count
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a notification"""
    
    deleted = await notification_crud.delete_notification(
        db, notification_id, current_user.id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {
        "success": True,
        "message": "Notification deleted"
    }
