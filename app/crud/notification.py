from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
import json

from app.models.notification import Notification, NotificationStatus, NotificationType
from app.schemas.notification import NotificationCreate, NotificationUpdate


class NotificationCRUD:
    """CRUD operations for notifications"""
    
    async def create_notification(
        self, 
        db: AsyncSession, 
        notification_data: NotificationCreate
    ) -> Notification:
        """Create a new notification"""
        extra_data_json = None
        if notification_data.extra_data:
            extra_data_json = json.dumps(notification_data.extra_data)
        
        db_notification = Notification(
            user_id=notification_data.user_id,
            type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            extra_data=extra_data_json,
            transaction_id=notification_data.transaction_id,
            status=NotificationStatus.UNREAD
        )
        
        db.add(db_notification)
        await db.commit()
        await db.refresh(db_notification)
        return db_notification
    
    async def get_notification_by_id(
        self, 
        db: AsyncSession, 
        notification_id: int
    ) -> Optional[Notification]:
        """Get notification by ID"""
        result = await db.execute(
            select(Notification)
            .options(selectinload(Notification.transaction))
            .where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get user notifications with pagination"""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.status == NotificationStatus.UNREAD)
        
        query = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_user_notifications_count(
        self,
        db: AsyncSession,
        user_id: int,
        unread_only: bool = False
    ) -> int:
        """Get count of user notifications"""
        query = select(func.count(Notification.id)).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.status == NotificationStatus.UNREAD)
        
        result = await db.execute(query)
        return result.scalar()
    
    async def mark_as_read(
        self,
        db: AsyncSession,
        notification_id: int,
        user_id: int
    ) -> Optional[Notification]:
        """Mark notification as read"""
        # First check if notification exists and belongs to user
        notification = await self.get_notification_by_id(db, notification_id)
        if not notification or notification.user_id != user_id:
            return None
        
        await db.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(
                status=NotificationStatus.READ,
                read_at=func.now()
            )
        )
        await db.commit()
        
        # Return updated notification
        return await self.get_notification_by_id(db, notification_id)
    
    async def mark_all_as_read(
        self,
        db: AsyncSession,
        user_id: int
    ) -> int:
        """Mark all user notifications as read. Returns count of updated notifications."""
        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.UNREAD
            )
            .values(
                status=NotificationStatus.READ,
                read_at=func.now()
            )
        )
        await db.commit()
        return result.rowcount
    
    async def delete_notification(
        self,
        db: AsyncSession,
        notification_id: int,
        user_id: int
    ) -> bool:
        """Delete a notification. Returns True if deleted, False if not found."""
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            return False
        
        await db.delete(notification)
        await db.commit()
        return True


# Create instance to use
notification_crud = NotificationCRUD()
