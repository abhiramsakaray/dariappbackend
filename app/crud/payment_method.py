from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from typing import Optional, List
from fastapi import HTTPException, status

from app.models.payment_method import PaymentMethod, PaymentMethodType
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodUpdate


async def get_payment_methods(db: AsyncSession, user_id: int) -> List[PaymentMethod]:
    """Get all payment methods for a user"""
    result = await db.execute(
        select(PaymentMethod)
        .where(PaymentMethod.user_id == user_id)
        .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
    )
    return result.scalars().all()


async def get_payment_method_by_id(db: AsyncSession, payment_method_id: int, user_id: int) -> Optional[PaymentMethod]:
    """Get a specific payment method by ID"""
    result = await db.execute(
        select(PaymentMethod)
        .where(
            and_(
                PaymentMethod.id == payment_method_id,
                PaymentMethod.user_id == user_id
            )
        )
    )
    return result.scalar_one_or_none()


async def create_payment_method(
    db: AsyncSession, 
    user_id: int, 
    payment_method: PaymentMethodCreate
) -> PaymentMethod:
    """Create a new payment method"""
    
    # Check if this is the user's first payment method
    existing_methods = await get_payment_methods(db, user_id)
    is_first_method = len(existing_methods) == 0
    
    # Create new payment method
    db_payment_method = PaymentMethod(
        user_id=user_id,
        type=PaymentMethodType(payment_method.type),
        name=payment_method.name,
        details=payment_method.details,
        is_default=is_first_method  # Auto-set as default if first method
    )
    
    db.add(db_payment_method)
    await db.commit()
    await db.refresh(db_payment_method)
    
    return db_payment_method


async def update_payment_method(
    db: AsyncSession,
    payment_method_id: int,
    user_id: int,
    payment_method_update: PaymentMethodUpdate
) -> Optional[PaymentMethod]:
    """Update a payment method"""
    
    # Get existing payment method
    db_payment_method = await get_payment_method_by_id(db, payment_method_id, user_id)
    if not db_payment_method:
        return None
    
    # Update fields
    update_data = payment_method_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_payment_method, field, value)
    
    await db.commit()
    await db.refresh(db_payment_method)
    
    return db_payment_method


async def delete_payment_method(
    db: AsyncSession,
    payment_method_id: int,
    user_id: int
) -> bool:
    """Delete a payment method"""
    
    # Get the payment method to delete
    db_payment_method = await get_payment_method_by_id(db, payment_method_id, user_id)
    if not db_payment_method:
        return False
    
    # Check if this is the only payment method
    all_methods = await get_payment_methods(db, user_id)
    if len(all_methods) == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the only payment method. Add another payment method first."
        )
    
    was_default = db_payment_method.is_default
    
    # Delete the payment method
    await db.delete(db_payment_method)
    
    # If deleted method was default, set another as default
    if was_default:
        remaining_methods = await get_payment_methods(db, user_id)
        if remaining_methods:
            remaining_methods[0].is_default = True
    
    await db.commit()
    return True


async def set_default_payment_method(
    db: AsyncSession,
    payment_method_id: int,
    user_id: int
) -> Optional[PaymentMethod]:
    """Set a payment method as default"""
    
    # Get the payment method to set as default
    db_payment_method = await get_payment_method_by_id(db, payment_method_id, user_id)
    if not db_payment_method:
        return None
    
    # Remove default from all other payment methods
    await db.execute(
        update(PaymentMethod)
        .where(PaymentMethod.user_id == user_id)
        .values(is_default=False)
    )
    
    # Set this one as default
    db_payment_method.is_default = True
    
    await db.commit()
    await db.refresh(db_payment_method)
    
    return db_payment_method


async def count_payment_methods(db: AsyncSession, user_id: int) -> int:
    """Count total payment methods for a user"""
    result = await db.execute(
        select(PaymentMethod)
        .where(PaymentMethod.user_id == user_id)
    )
    return len(result.scalars().all())
