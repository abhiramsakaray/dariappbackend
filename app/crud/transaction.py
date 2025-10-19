from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate


async def create_transaction(db: AsyncSession, transaction_data: TransactionCreate) -> Transaction:
    """Create a new transaction"""
    # Get token ID if not provided
    token_id = transaction_data.token_id
    if not token_id:
        from app.crud import token as token_crud
        token_obj = await token_crud.get_token_by_symbol(db, transaction_data.token)
        if not token_obj:
            raise ValueError(f"Token {transaction_data.token} not found")
        token_id = token_obj.id
    
    db_transaction = Transaction(
        from_user_id=transaction_data.from_user_id or transaction_data.user_id,
        to_user_id=transaction_data.to_user_id,
        from_address=transaction_data.from_address,
        to_address=transaction_data.to_address,
        amount=transaction_data.amount,
        token_id=token_id,
        tx_hash=transaction_data.transaction_hash,
        transaction_type=transaction_data.transaction_type,
        status=transaction_data.status or TransactionStatus.PENDING,
        gas_fee=transaction_data.fee,
        gas_used=transaction_data.gas_used
    )
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction


async def get_transaction_by_id(db: AsyncSession, transaction_id: int) -> Optional[Transaction]:
    """Get transaction by ID"""
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.token))
        .where(Transaction.id == transaction_id)
    )
    return result.scalar_one_or_none()


async def get_transaction_by_hash(db: AsyncSession, tx_hash: str) -> Optional[Transaction]:
    """Get transaction by hash"""
    result = await db.execute(
        select(Transaction).where(Transaction.transaction_hash == tx_hash)
    )
    return result.scalar_one_or_none()


async def get_user_transactions(
    db: AsyncSession, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[Transaction]:
    """Get all transactions for a user"""
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.token))
        .where(
            or_(
                Transaction.from_user_id == user_id,
                Transaction.to_user_id == user_id
            )
        )
        .order_by(desc(Transaction.created_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def update_transaction_status(
    db: AsyncSession, 
    transaction_id: int, 
    status: TransactionStatus,
    transaction_hash: Optional[str] = None
) -> Optional[Transaction]:
    """Update transaction status"""
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    db_transaction = result.scalar_one_or_none()
    
    if not db_transaction:
        return None
    
    db_transaction.status = status
    if transaction_hash:
        db_transaction.transaction_hash = transaction_hash
    if status == TransactionStatus.CONFIRMED:
        db_transaction.confirmed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction


async def update_transaction_receiver(
    db: AsyncSession, 
    transaction_id: int, 
    receiver_user_id: int
) -> Optional[Transaction]:
    """Update transaction receiver user ID"""
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    db_transaction = result.scalar_one_or_none()
    
    if not db_transaction:
        return None
    
    db_transaction.to_user_id = receiver_user_id
    
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction


async def get_pending_transactions(db: AsyncSession) -> List[Transaction]:
    """Get all pending transactions"""
    result = await db.execute(
        select(Transaction).where(Transaction.status == TransactionStatus.PENDING)
    )
    return result.scalars().all()


async def get_transactions_by_address(
    db: AsyncSession,
    address: str,
    skip: int = 0,
    limit: int = 100
) -> List[Transaction]:
    """Get transactions by from or to address"""
    result = await db.execute(
        select(Transaction)
        .where(
            or_(
                Transaction.from_address == address,
                Transaction.to_address == address
            )
        )
        .order_by(desc(Transaction.created_at))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
