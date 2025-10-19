from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.password import get_password_hash


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID with address_resolver relationship"""
    result = await db.execute(
        select(User)
        .options(selectinload(User.address_resolver))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
    """Get user by phone"""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User)
        .options(selectinload(User.kyc_request))
        .where(User.phone == phone)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """Create new user"""
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        email=user.email,
        phone=user.phone,
        password_hash=hashed_password,
        default_currency=user.default_currency,
        terms_accepted=user.terms_accepted,
        role=UserRole.USER,
        is_active=True,
        kyc_verified=False,
        otp_enabled=False
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update user"""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user_last_login(db: AsyncSession, user_id: int) -> None:
    """Update user's last login timestamp"""
    db_user = await get_user_by_id(db, user_id)
    if db_user:
        db_user.last_login = datetime.utcnow()
        await db.commit()


async def update_user_pin(db: AsyncSession, user_id: int, hashed_pin: str) -> bool:
    """Update user's PIN"""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    db_user.pin_hash = hashed_pin
    await db.commit()
    return True


async def activate_user(db: AsyncSession, user_id: int) -> bool:
    """Activate user account"""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    db_user.is_active = True
    await db.commit()
    return True


async def deactivate_user(db: AsyncSession, user_id: int, ban_reason: str = None, ban_type: str = None) -> bool:
    """Deactivate user account with ban reason and type"""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return False
    db_user.is_active = False
    db_user.ban_reason = ban_reason
    db_user.ban_type = ban_type
    await db.commit()
    return db_user


async def update_kyc_status(db: AsyncSession, user_id: int, verified: bool) -> bool:
    """Update user's KYC verification status"""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    db_user.kyc_verified = verified
    await db.commit()
    return True


async def get_users_paginated(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    kyc_verified: Optional[bool] = None
) -> tuple[List[User], int]:
    """Get paginated list of users with filters"""
    query = select(User)
    count_query = select(func.count(User.id))
    
    # Apply filters
    conditions = []
    
    if search:
        search_condition = or_(
            User.email.ilike(f"%{search}%"),
            User.phone.ilike(f"%{search}%")
        )
        conditions.append(search_condition)
    
    if role:
        conditions.append(User.role == role)
    
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    
    if kyc_verified is not None:
        conditions.append(User.kyc_verified == kyc_verified)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count with timeout protection
    import asyncio
    try:
        count_task = asyncio.create_task(db.execute(count_query))
        count_result = await asyncio.wait_for(count_task, timeout=8.0)
        total_count = count_result.scalar()
    except asyncio.TimeoutError:
        print("WARNING: Count query timed out, using estimated count")
        total_count = 1000  # Fallback estimate
    
    # Get paginated results with timeout protection
    try:
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        result_task = asyncio.create_task(db.execute(query))
        result = await asyncio.wait_for(result_task, timeout=8.0)
        users = result.scalars().all()
    except asyncio.TimeoutError:
        print("WARNING: User query timed out, returning empty list")
        users = []
    
    return list(users), total_count


async def get_user_stats(db: AsyncSession) -> dict:
    """Get user statistics"""
    total_users = await db.execute(select(func.count(User.id)))
    active_users = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    kyc_pending = await db.execute(select(func.count(User.id)).where(User.kyc_verified == False))
    kyc_approved = await db.execute(select(func.count(User.id)).where(User.kyc_verified == True))
    
    return {
        "total_users": total_users.scalar(),
        "active_users": active_users.scalar(),
        "kyc_pending": kyc_pending.scalar(),
        "kyc_approved": kyc_approved.scalar(),
        "kyc_rejected": 0  # Will be calculated from KYC table
    }


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Delete user (soft delete by deactivating)"""
    return await deactivate_user(db, user_id)
