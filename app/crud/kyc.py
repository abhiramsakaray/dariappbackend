from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.models.kyc import KYCRequest, KYCStatus
from app.schemas.kyc import KYCCreate, KYCUpdate


async def get_kyc_by_user_id(db: AsyncSession, user_id: int) -> Optional[KYCRequest]:
    """Get KYC request by user ID"""
    result = await db.execute(
        select(KYCRequest).where(KYCRequest.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_kyc_by_id(db: AsyncSession, kyc_id: int) -> Optional[KYCRequest]:
    """Get KYC request by ID"""
    result = await db.execute(
        select(KYCRequest).where(KYCRequest.id == kyc_id)
    )
    return result.scalar_one_or_none()


async def create_kyc_request(db: AsyncSession, kyc_data: KYCCreate, user_id: int) -> KYCRequest:
    """Create a new KYC request"""
    db_kyc = KYCRequest(
        user_id=user_id,
        full_name=kyc_data.full_name,
        date_of_birth=kyc_data.date_of_birth,
        nationality=kyc_data.nationality,
        address_line_1=kyc_data.address_line_1,
        address_line_2=kyc_data.address_line_2,
        city=kyc_data.city,
        state=kyc_data.state,
        postal_code=kyc_data.postal_code,
        country=kyc_data.country,
        document_type=kyc_data.document_type,
        document_number=kyc_data.document_number,
        status=KYCStatus.PENDING
    )
    db.add(db_kyc)
    await db.commit()
    await db.refresh(db_kyc)
    return db_kyc


async def create_kyc_request_with_files(
    db: AsyncSession, 
    kyc_data: KYCCreate, 
    user_id: int,
    document_file_path: str,
    selfie_file_path: str
) -> KYCRequest:
    """Create KYC request with uploaded file paths"""
    db_kyc = KYCRequest(
        user_id=user_id,
        full_name=kyc_data.full_name,
        date_of_birth=kyc_data.date_of_birth,
        nationality=kyc_data.nationality,
        address_line_1=kyc_data.address_line_1,
        address_line_2=kyc_data.address_line_2,
        city=kyc_data.city,
        state=kyc_data.state,
        postal_code=kyc_data.postal_code,
        country=kyc_data.country,
        document_type=kyc_data.document_type,
        document_number=kyc_data.document_number,
        document_file_path=document_file_path,
        selfie_file_path=selfie_file_path,
        status=KYCStatus.PENDING
    )
    db.add(db_kyc)
    await db.commit()
    await db.refresh(db_kyc)
    return db_kyc


async def update_kyc_request(db: AsyncSession, kyc_id: int, kyc_data: KYCUpdate) -> Optional[KYCRequest]:
    """Update KYC request"""
    result = await db.execute(
        select(KYCRequest).where(KYCRequest.id == kyc_id)
    )
    db_kyc = result.scalar_one_or_none()
    
    if not db_kyc:
        return None
    
    update_data = kyc_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_kyc, field, value)
    
    await db.commit()
    await db.refresh(db_kyc)
    return db_kyc


async def approve_kyc(db: AsyncSession, kyc_id: int, reviewer_id: int) -> Optional[KYCRequest]:
    """Approve KYC request"""
    result = await db.execute(
        select(KYCRequest).where(KYCRequest.id == kyc_id)
    )
    db_kyc = result.scalar_one_or_none()
    
    if not db_kyc:
        return None
    
    # Update KYC request status
    db_kyc.status = KYCStatus.APPROVED
    db_kyc.reviewed_by = reviewer_id
    db_kyc.reviewed_at = datetime.utcnow()
    db_kyc.rejection_reason = None
    
    # Update user's kyc_verified status
    from app.models.user import User
    user_result = await db.execute(
        select(User).where(User.id == db_kyc.user_id)
    )
    user = user_result.scalar_one_or_none()
    if user:
        user.kyc_verified = True
    
    await db.commit()
    await db.refresh(db_kyc)
    
    # 🆕 Automatically create wallet and DARI address after KYC approval
    if user:
        try:
            from app.crud import wallet as wallet_crud
            from app.crud import address_resolver as address_crud
            
            # Check if user already has a wallet
            existing_wallet = await wallet_crud.get_user_wallet(db, user.id)
            
            if not existing_wallet:
                print(f"🏦 Creating wallet for user {user.id} after KYC approval...")
                
                # Create wallet
                new_wallet = await wallet_crud.create_wallet(db, user.id)
                print(f"✅ Wallet created: {new_wallet.address}")
                
                # Generate DARI address from email (username@dari)
                email_username = user.email.split('@')[0]  # Get username part before @
                dari_address = f"{email_username}@dari"
                
                # Check if DARI address already exists
                existing_address = await address_crud.get_address_by_dari_address(db, dari_address)
                
                if not existing_address:
                    # Create DARI address
                    await address_crud.create_address(
                        db=db,
                        user_id=user.id,
                        wallet_address=new_wallet.address,
                        dari_address=dari_address,
                        full_name=db_kyc.full_name  # Use KYC verified name
                    )
                    print(f"✅ DARI address created: {dari_address}")
                else:
                    # If address exists, use a unique variation
                    counter = 1
                    while existing_address:
                        dari_address = f"{email_username}{counter}@dari"
                        existing_address = await address_crud.get_address_by_dari_address(db, dari_address)
                        counter += 1
                    
                    await address_crud.create_address(
                        db=db,
                        user_id=user.id,
                        wallet_address=new_wallet.address,
                        dari_address=dari_address,
                        full_name=db_kyc.full_name
                    )
                    print(f"✅ DARI address created: {dari_address} (unique variation)")
                
                await db.commit()
                print(f"🎉 Wallet and DARI address setup complete for user {user.id}")
            else:
                print(f"ℹ️ User {user.id} already has a wallet")
                
        except Exception as e:
            print(f"⚠️ Failed to create wallet/address after KYC approval: {e}")
            # Don't fail KYC approval if wallet creation fails
            await db.rollback()
            await db.commit()  # Commit the KYC approval
    
    # 🆕 Send Expo push notification for KYC approval
    try:
        from app.services.notification_helpers import notify_kyc_status
        await notify_kyc_status(db, db_kyc.user_id, "approved", None)
    except Exception as e:
        print(f"⚠️ Failed to send KYC approval notification: {e}")
    
    return db_kyc


async def reject_kyc(db: AsyncSession, kyc_id: int, reviewer_id: int, reason: str) -> Optional[KYCRequest]:
    """Reject KYC request"""
    result = await db.execute(
        select(KYCRequest).where(KYCRequest.id == kyc_id)
    )
    db_kyc = result.scalar_one_or_none()
    
    if not db_kyc:
        return None
    
    # Update KYC request status
    db_kyc.status = KYCStatus.REJECTED
    db_kyc.reviewed_by = reviewer_id
    db_kyc.reviewed_at = datetime.utcnow()
    db_kyc.rejection_reason = reason
    
    # Update user's kyc_verified status
    from app.models.user import User
    user_result = await db.execute(
        select(User).where(User.id == db_kyc.user_id)
    )
    user = user_result.scalar_one_or_none()
    if user:
        user.kyc_verified = False
    
    await db.commit()
    await db.refresh(db_kyc)
    
    # 🆕 Send Expo push notification for KYC rejection
    try:
        from app.services.notification_helpers import notify_kyc_status
        await notify_kyc_status(db, db_kyc.user_id, "rejected", reason)
    except Exception as e:
        print(f"⚠️ Failed to send KYC rejection notification: {e}")
    
    return db_kyc


async def get_pending_kyc_requests(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all pending KYC requests"""
    result = await db.execute(
        select(KYCRequest)
        .where(KYCRequest.status == KYCStatus.PENDING)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
