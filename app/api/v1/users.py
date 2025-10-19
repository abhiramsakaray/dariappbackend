from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.schemas.user import UserResponse, UserUpdate, CheckPhonesRequest, CheckPhonesResponse, DariUserInfo
from app.crud import user as user_crud
from app.models.user import User
from app.models.address_resolver import AddressResolver

router = APIRouter()


class FCMTokenUpdate(BaseModel):
    """Schema for updating FCM device token"""
    fcm_device_token: str


@router.get("/profile")
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "phone": current_user.phone,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "kyc_verified": current_user.kyc_verified,
            "terms_accepted": current_user.terms_accepted,
            "otp_enabled": current_user.otp_enabled,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login
        }
    }


@router.put("/profile")
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    
    # Only check for duplicate email if a new email is provided and it's different from the current user's email
    if user_update.email is not None and user_update.email != current_user.email:
        existing_user = await user_crud.get_user_by_email(db, email=user_update.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Only check for duplicate phone if a new phone is provided and it's different from the current user's phone
    if user_update.phone is not None and user_update.phone != current_user.phone:
        existing_phone = await user_crud.get_user_by_phone(db, phone=user_update.phone)
        if existing_phone and existing_phone.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )

    updated_user = await user_crud.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "success": True,
        "message": "Profile updated successfully",
        "data": {
            "id": updated_user.id,
            "email": updated_user.email,
            "phone": updated_user.phone,
            "role": updated_user.role,
            "is_active": updated_user.is_active,
            "kyc_verified": updated_user.kyc_verified,
            "terms_accepted": updated_user.terms_accepted,
            "otp_enabled": updated_user.otp_enabled,
            "created_at": updated_user.created_at,
            "last_login": updated_user.last_login
        }
    }


@router.get("/pin-status")
async def get_pin_status(current_user: User = Depends(get_current_active_user)):
    """Check if user has set up a PIN"""
    return {
        "success": True,
        "data": {
            "pin_set": bool(current_user.pin_hash)
        }
    }


@router.post("/check-phones", response_model=CheckPhonesResponse)
async def check_phones(
    request: CheckPhonesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Check which phone numbers from the provided list are registered DARI users.
    Returns user information including phone, full_name, and DARI address.
    
    Request body:
    {
      "phones": ["+917207276059", "+919876543210", ...]
    }
    
    Response:
    {
      "dari_users": [
        {
          "phone": "+917207276059",
          "full_name": "Abhiram Sakaray",
          "dari_address": "abhi@dari",
          "full_address": "abhi@dari"
        }
      ]
    }
    """
    dari_users = []
    
    # Query users and their address resolvers for the provided phone numbers
    result = await db.execute(
        select(User, AddressResolver)
        .outerjoin(AddressResolver, User.id == AddressResolver.user_id)
        .where(User.phone.in_(request.phones))
        .where(User.is_active == True)
    )
    
    users_with_addresses = result.all()
    
    for user, address_resolver in users_with_addresses:
        dari_user = DariUserInfo(
            phone=user.phone,
            full_name=user.full_name,
            dari_address=address_resolver.username + "@dari" if address_resolver else None,
            full_address=address_resolver.full_address if address_resolver else None
        )
        dari_users.append(dari_user)
    
    return CheckPhonesResponse(dari_users=dari_users)


@router.post("/fcm-token")
async def update_fcm_token(
    token_data: FCMTokenUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Register or update the user's FCM device token for push notifications
    
    Request body:
    {
      "fcm_device_token": "firebase_device_token_string"
    }
    """
    try:
        # Update user's FCM token
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(fcm_device_token=token_data.fcm_device_token)
        )
        await db.commit()
        
        return {
            "success": True,
            "message": "FCM device token updated successfully"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update FCM token: {str(e)}"
        )


@router.delete("/fcm-token")
async def remove_fcm_token(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove the user's FCM device token (e.g., on logout)
    """
    try:
        # Clear user's FCM token
        await db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(fcm_device_token=None)
        )
        await db.commit()
        
        return {
            "success": True,
            "message": "FCM device token removed successfully"
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove FCM token: {str(e)}"
        )
