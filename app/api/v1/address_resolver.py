from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.crud import address_resolver as address_resolver_crud, wallet as wallet_crud
from app.schemas.address_resolver import (
    AddressResolverCreate,
    AddressResolverUpdate,
    AddressResolverResponse,
    AddressResolveRequest,
    AddressResolveResponse
)
from app.services.email_service import EmailService

router = APIRouter()


@router.post("/create", response_model=AddressResolverResponse)
async def create_user_address_resolver(
    address_data: AddressResolverCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> AddressResolverResponse:
    """Create DARI address for current user"""
    
    # Check if user already has an address resolver
    existing_resolver = await address_resolver_crud.get_address_resolver_by_user_id(db, current_user.id)
    if existing_resolver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a DARI address. Use update endpoint to modify it."
        )
    
    # Check if username is available
    username_taken = await address_resolver_crud.get_address_resolver_by_username(db, address_data.username)
    if username_taken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken. Please choose a different username."
        )
    
    # Get user's wallet address
    wallet = await wallet_crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have a wallet before creating DARI address"
        )
    
    # Create address resolver
    try:
        resolver = await address_resolver_crud.create_address_resolver(
            db, current_user.id, wallet.address, address_data
        )
        
        # Get KYC full_name if available
        from app.crud import kyc as kyc_crud
        kyc_request = await kyc_crud.get_kyc_by_user_id(db, current_user.id)
        full_name = kyc_request.full_name if kyc_request else current_user.full_name
        
        # Send email notification
        try:
            email_service = EmailService()
            await email_service.send_address_created_email(
                current_user.email,
                full_name or current_user.email.split('@')[0],  # Use full_name or email prefix
                resolver.full_address
            )
        except Exception as e:
            # Log error but don't fail the creation
            print(f"Failed to send address creation email: {e}")
        
        # Convert to dict and add full_name
        response_data = {
            "id": resolver.id,
            "username": resolver.username,
            "full_address": resolver.full_address,
            "wallet_address": resolver.wallet_address,
            "is_active": resolver.is_active,
            "created_at": resolver.created_at,
            "updated_at": resolver.updated_at,
            "full_name": full_name
        }
        
        return AddressResolverResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create DARI address: {str(e)}"
        )


@router.get("/my-address", response_model=AddressResolverResponse)
async def get_my_address_resolver(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> AddressResolverResponse:
    """Get current user's DARI address"""
    
    resolver = await address_resolver_crud.get_address_resolver_by_user_id(db, current_user.id)
    if not resolver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a DARI address"
        )
    
    # Get KYC full_name if available
    from app.crud import kyc as kyc_crud
    kyc_request = await kyc_crud.get_kyc_by_user_id(db, current_user.id)
    full_name = kyc_request.full_name if kyc_request else current_user.full_name
    
    # Convert to dict and add full_name
    response_data = {
        "id": resolver.id,
        "username": resolver.username,
        "full_address": resolver.full_address,
        "wallet_address": resolver.wallet_address,
        "is_active": resolver.is_active,
        "created_at": resolver.created_at,
        "updated_at": resolver.updated_at,
        "full_name": full_name
    }
    
    return AddressResolverResponse(**response_data)


@router.put("/update", response_model=AddressResolverResponse)
async def update_user_address_resolver(
    address_data: AddressResolverUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> AddressResolverResponse:
    """Update current user's DARI address"""
    
    # Check if user has an address resolver
    existing_resolver = await address_resolver_crud.get_address_resolver_by_user_id(db, current_user.id)
    if not existing_resolver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a DARI address. Create one first."
        )
    
    try:
        updated_resolver = await address_resolver_crud.update_address_resolver(
            db, current_user.id, address_data
        )
        
        if not updated_resolver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address resolver not found"
            )
        
        # Get KYC full_name if available
        from app.crud import kyc as kyc_crud
        kyc_request = await kyc_crud.get_kyc_by_user_id(db, current_user.id)
        full_name = kyc_request.full_name if kyc_request else current_user.full_name
        
        # Send email notification if username was changed
        if address_data.username and address_data.username != existing_resolver.username:
            try:
                email_service = EmailService()
                await email_service.send_address_updated_email(
                    current_user.email,
                    full_name or current_user.email.split('@')[0],  # Use full_name or email prefix
                    existing_resolver.full_address,
                    updated_resolver.full_address
                )
            except Exception as e:
                # Log error but don't fail the update
                print(f"Failed to send address update email: {e}")
        
        # Convert to dict and add full_name
        response_data = {
            "id": updated_resolver.id,
            "username": updated_resolver.username,
            "full_address": updated_resolver.full_address,
            "wallet_address": updated_resolver.wallet_address,
            "is_active": updated_resolver.is_active,
            "created_at": updated_resolver.created_at,
            "updated_at": updated_resolver.updated_at,
            "full_name": full_name
        }
        
        return AddressResolverResponse(**response_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update DARI address: {str(e)}"
        )


@router.post("/resolve", response_model=AddressResolveResponse)
async def resolve_address(
    resolve_request: AddressResolveRequest,
    db: AsyncSession = Depends(get_db)
) -> AddressResolveResponse:
    """Resolve DARI address to wallet address or vice versa"""
    
    result = await address_resolver_crud.resolve_address(db, resolve_request.address)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found or inactive"
        )
    
    return AddressResolveResponse(**result)


@router.get("/check-username/{username}")
async def check_username_availability(
    username: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Check if username is available"""
    
    # Validate username format
    import re
    if not re.match(r'^[a-zA-Z]+$', username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must contain only alphabetic characters"
        )
    
    if len(username) < 3 or len(username) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be between 3 and 50 characters"
        )
    
    is_available = await address_resolver_crud.is_username_available(db, username)
    
    return {
        "username": username,
        "available": is_available,
        "full_address": f"{username}@dari" if is_available else None
    }
    return {
        "username": username.lower(),
        "available": is_available,
        "full_address": f"{username.lower()}@dari"
    }
