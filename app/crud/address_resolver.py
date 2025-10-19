from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.models.address_resolver import AddressResolver
from app.schemas.address_resolver import AddressResolverCreate, AddressResolverUpdate


async def create_address_resolver(
    db: AsyncSession, 
    user_id: int, 
    wallet_address: str,
    address_data: AddressResolverCreate
) -> AddressResolver:
    """Create a new address resolver for a user"""
    full_address = f"{address_data.username}@dari"
    
    db_address_resolver = AddressResolver(
        user_id=user_id,
        username=address_data.username,
        full_address=full_address,
        wallet_address=wallet_address
    )
    
    db.add(db_address_resolver)
    await db.commit()
    await db.refresh(db_address_resolver)
    return db_address_resolver


async def get_address_resolver_by_user_id(db: AsyncSession, user_id: int) -> Optional[AddressResolver]:
    """Get address resolver by user ID"""
    result = await db.execute(
        select(AddressResolver).where(AddressResolver.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_address_resolver_by_username(db: AsyncSession, username: str) -> Optional[AddressResolver]:
    """Get address resolver by username"""
    result = await db.execute(
        select(AddressResolver).where(AddressResolver.username == username.lower())
    )
    return result.scalar_one_or_none()


async def get_address_resolver_by_full_address(db: AsyncSession, full_address: str) -> Optional[AddressResolver]:
    """Get address resolver by full address (username@dari)"""
    result = await db.execute(
        select(AddressResolver).where(AddressResolver.full_address == full_address.lower())
    )
    return result.scalar_one_or_none()


async def get_address_resolver_by_wallet_address(db: AsyncSession, wallet_address: str) -> Optional[AddressResolver]:
    """Get address resolver by wallet address"""
    from app.models.user import User
    result = await db.execute(
        select(AddressResolver)
        .options(
            selectinload(AddressResolver.user).selectinload(User.kyc_request)
        )
        .where(AddressResolver.wallet_address == wallet_address)
    )
    return result.scalar_one_or_none()


async def get_user_id_by_wallet_address(db: AsyncSession, wallet_address: str) -> Optional[int]:
    """Get user ID by wallet address"""
    resolver = await get_address_resolver_by_wallet_address(db, wallet_address)
    return resolver.user_id if resolver else None


async def get_user_by_wallet_address(db: AsyncSession, wallet_address: str):
    """Get user object by wallet address"""
    resolver = await get_address_resolver_by_wallet_address(db, wallet_address)
    return resolver.user if resolver else None


async def update_address_resolver(
    db: AsyncSession, 
    user_id: int, 
    address_data: AddressResolverUpdate
) -> Optional[AddressResolver]:
    """Update address resolver"""
    # First get the current resolver
    current_resolver = await get_address_resolver_by_user_id(db, user_id)
    if not current_resolver:
        return None
    
    # Check if new username is available
    if address_data.username and address_data.username != current_resolver.username:
        existing = await get_address_resolver_by_username(db, address_data.username)
        if existing:
            raise ValueError("Username already taken")
    
    # Update the resolver
    update_data = {}
    if address_data.username:
        update_data["username"] = address_data.username
        update_data["full_address"] = f"{address_data.username}@dari"
    
    if update_data:
        await db.execute(
            update(AddressResolver)
            .where(AddressResolver.user_id == user_id)
            .values(**update_data)
        )
        await db.commit()
        
        # Refresh and return updated resolver
        await db.refresh(current_resolver)
        return current_resolver
    
    return current_resolver


async def delete_address_resolver(db: AsyncSession, user_id: int) -> bool:
    """Delete address resolver"""
    result = await db.execute(
        delete(AddressResolver).where(AddressResolver.user_id == user_id)
    )
    await db.commit()
    return result.rowcount > 0


async def get_all_address_resolvers(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100
) -> List[AddressResolver]:
    """Get all address resolvers (admin only)"""
    result = await db.execute(
        select(AddressResolver)
        .offset(skip)
        .limit(limit)
        .order_by(AddressResolver.created_at.desc())
    )
    return result.scalars().all()


async def resolve_address(db: AsyncSession, address: str) -> Optional[dict]:
    """Resolve an address to wallet address and DARI address"""
    from app.models.user import User
    from app.models.kyc import KYCRequest
    
    # If it's a DARI address (contains @dari)
    if '@dari' in address.lower():
        resolver = await get_address_resolver_by_full_address(db, address)
        if resolver and resolver.is_active:
            # Get full_name from KYC or User
            result = await db.execute(
                select(User, KYCRequest)
                .outerjoin(KYCRequest, User.id == KYCRequest.user_id)
                .where(User.id == resolver.user_id)
            )
            user_data = result.first()
            full_name = None
            if user_data:
                user, kyc = user_data
                full_name = kyc.full_name if kyc else user.full_name
            
            return {
                "input_address": address,
                "wallet_address": resolver.wallet_address,
                "dari_address": resolver.full_address,
                "is_dari_address": True,
                "full_name": full_name
            }
        return None
    
    # If it's a wallet address (starts with 0x)
    elif address.startswith('0x') and len(address) == 42:
        resolver = await get_address_resolver_by_wallet_address(db, address)
        if resolver and resolver.is_active:
            # Get full_name from KYC or User
            result = await db.execute(
                select(User, KYCRequest)
                .outerjoin(KYCRequest, User.id == KYCRequest.user_id)
                .where(User.id == resolver.user_id)
            )
            user_data = result.first()
            full_name = None
            if user_data:
                user, kyc = user_data
                full_name = kyc.full_name if kyc else user.full_name
            
            return {
                "input_address": address,
                "wallet_address": address,
                "dari_address": resolver.full_address,
                "is_dari_address": False,
                "full_name": full_name
            }
        else:
            return {
                "input_address": address,
                "wallet_address": address,
                "dari_address": None,
                "is_dari_address": False,
                "full_name": None
            }
    
    return None


async def is_username_available(db: AsyncSession, username: str) -> bool:
    """Check if username is available"""
    resolver = await get_address_resolver_by_username(db, username)
    return resolver is None
