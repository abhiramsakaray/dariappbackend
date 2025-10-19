from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from typing import Optional, List
from datetime import datetime

from app.models.push_token import PushToken
from app.schemas.push_token import PushTokenCreate


async def get_user_push_tokens(db: AsyncSession, user_id: int, active_only: bool = True) -> List[PushToken]:
    """Get all push tokens for a user"""
    query = select(PushToken).where(PushToken.user_id == user_id)
    
    if active_only:
        query = query.where(PushToken.is_active == True)
    
    result = await db.execute(query.order_by(PushToken.last_used_at.desc()))
    return result.scalars().all()


async def get_push_token_by_token(db: AsyncSession, expo_push_token: str) -> Optional[PushToken]:
    """Get a push token by its token string"""
    result = await db.execute(
        select(PushToken).where(PushToken.expo_push_token == expo_push_token)
    )
    return result.scalar_one_or_none()


async def register_push_token(
    db: AsyncSession,
    user_id: int,
    token_data: PushTokenCreate
) -> PushToken:
    """Register or update a push token"""
    
    # Check if token already exists for this user
    existing_token = await db.execute(
        select(PushToken).where(
            and_(
                PushToken.user_id == user_id,
                PushToken.expo_push_token == token_data.expo_push_token
            )
        )
    )
    existing_token = existing_token.scalar_one_or_none()
    
    if existing_token:
        # Update existing token
        existing_token.device_type = token_data.device_type
        existing_token.device_name = token_data.device_name
        existing_token.is_active = True
        existing_token.last_used_at = datetime.utcnow()
        existing_token.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(existing_token)
        return existing_token
    
    # Create new token
    new_token = PushToken(
        user_id=user_id,
        expo_push_token=token_data.expo_push_token,
        device_type=token_data.device_type,
        device_name=token_data.device_name,
        is_active=True
    )
    
    db.add(new_token)
    await db.commit()
    await db.refresh(new_token)
    
    return new_token


async def unregister_push_token(
    db: AsyncSession,
    user_id: int,
    expo_push_token: str
) -> bool:
    """Unregister (deactivate) a push token"""
    
    result = await db.execute(
        select(PushToken).where(
            and_(
                PushToken.user_id == user_id,
                PushToken.expo_push_token == expo_push_token
            )
        )
    )
    token = result.scalar_one_or_none()
    
    if not token:
        return False
    
    # Soft delete - mark as inactive
    token.is_active = False
    token.updated_at = datetime.utcnow()
    
    await db.commit()
    return True


async def deactivate_invalid_token(db: AsyncSession, expo_push_token: str) -> None:
    """Deactivate a token that's been reported as invalid by Expo"""
    
    await db.execute(
        update(PushToken)
        .where(PushToken.expo_push_token == expo_push_token)
        .values(is_active=False, updated_at=datetime.utcnow())
    )
    await db.commit()


async def update_token_last_used(db: AsyncSession, expo_push_token: str) -> None:
    """Update the last_used_at timestamp for a token"""
    
    await db.execute(
        update(PushToken)
        .where(PushToken.expo_push_token == expo_push_token)
        .values(last_used_at=datetime.utcnow())
    )
    await db.commit()


async def cleanup_inactive_tokens(db: AsyncSession, days_inactive: int = 90) -> int:
    """
    Clean up tokens that haven't been used in X days
    Returns number of tokens deleted
    """
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
    
    result = await db.execute(
        select(PushToken).where(
            and_(
                PushToken.is_active == False,
                PushToken.updated_at < cutoff_date
            )
        )
    )
    tokens_to_delete = result.scalars().all()
    
    for token in tokens_to_delete:
        await db.delete(token)
    
    await db.commit()
    return len(tokens_to_delete)
