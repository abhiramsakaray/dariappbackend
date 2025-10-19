from sqlalchemy.orm import selectinload
from app.models.wallet import Wallet
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
async def get_user_wallets(db: AsyncSession, user_id: int) -> List[Wallet]:
    """Get all wallets for a specific user"""
    result = await db.execute(
        select(Wallet)
        .options(selectinload(Wallet.token_balances))
        .where(Wallet.user_id == user_id)
    )
    return result.scalars().all()
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime

from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletUpdate


async def get_wallet_by_user_id(db: AsyncSession, user_id: int) -> Optional[Wallet]:
    """Get wallet by user ID"""
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_wallet_by_address(db: AsyncSession, address: str) -> Optional[Wallet]:
    """Get wallet by address"""
    result = await db.execute(
        select(Wallet).where(Wallet.address == address)
    )
    return result.scalar_one_or_none()


async def create_wallet(db: AsyncSession, wallet_data: WalletCreate, user_id: int) -> Wallet:
    """Create a new wallet"""
    db_wallet = Wallet(
        user_id=user_id,
        address=wallet_data.address,
        encrypted_private_key=wallet_data.encrypted_private_key,
        chain="polygon"
    )
    db.add(db_wallet)
    await db.commit()
    await db.refresh(db_wallet)
    return db_wallet


async def update_wallet(db: AsyncSession, wallet_id: int, wallet_data: WalletUpdate) -> Optional[Wallet]:
    """Update wallet"""
    result = await db.execute(
        select(Wallet).where(Wallet.id == wallet_id)
    )
    db_wallet = result.scalar_one_or_none()
    
    if not db_wallet:
        return None
    
    update_data = wallet_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_wallet, field, value)
    
    await db.commit()
    await db.refresh(db_wallet)
    return db_wallet


async def deactivate_wallet(db: AsyncSession, wallet_id: int) -> Optional[Wallet]:
    """Deactivate wallet"""
    result = await db.execute(
        select(Wallet).where(Wallet.id == wallet_id)
    )
    db_wallet = result.scalar_one_or_none()
    
    if not db_wallet:
        return None
    
    # TODO: Add is_active field to Wallet model if wallet deactivation is needed
    # db_wallet.is_active = False
    await db.commit()
    await db.refresh(db_wallet)
    return db_wallet


async def get_all_wallets(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Wallet]:
    """Get all wallets (admin only)"""
    result = await db.execute(
        select(Wallet)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_active_wallets_count(db: AsyncSession) -> int:
    """Get count of wallets belonging to active users"""
    from app.models.user import User
    result = await db.execute(
        select(Wallet).join(User).where(User.is_active == True)
    )
    return len(result.scalars().all())
