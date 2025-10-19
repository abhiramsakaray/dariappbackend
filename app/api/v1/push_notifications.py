from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.push_token import (
    PushTokenCreate,
    PushTokenDelete,
    PushTokenResponse,
    PushTokenListResponse
)
from app.crud import push_token as push_token_crud

router = APIRouter(prefix="/push", tags=["Push Notifications"])


@router.post("/register", response_model=dict, status_code=status.HTTP_200_OK)
async def register_push_token(
    token_data: PushTokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register or update a push notification token for the authenticated user.
    
    **Request Body:**
    - `expo_push_token`: Expo push token from device (must start with "ExponentPushToken[" or "ExpoPushToken[")
    - `device_type`: Device type - must be "ios" or "android"
    - `device_name`: Optional device model name (e.g., "iPhone 14", "Pixel 6")
    
    **Behavior:**
    - If token already exists for this user, it will be updated
    - If token is new, it will be created
    - Token is automatically marked as active
    - last_used_at timestamp is updated
    
    **Returns:**
    - Success message with token details
    """
    
    try:
        db_token = await push_token_crud.register_push_token(
            db, current_user.id, token_data
        )
        
        is_new = db_token.created_at == db_token.updated_at
        message = "Push token registered successfully" if is_new else "Push token updated successfully"
        
        return {
            "success": True,
            "message": message,
            "data": {
                "id": db_token.id,
                "user_id": db_token.user_id,
                "expo_push_token": db_token.expo_push_token,
                "device_type": db_token.device_type,
                "device_name": db_token.device_name,
                "is_active": db_token.is_active,
                "created_at": db_token.created_at
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register push token: {str(e)}"
        )


@router.delete("/unregister", response_model=dict, status_code=status.HTTP_200_OK)
async def unregister_push_token(
    token_data: PushTokenDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unregister (deactivate) a push notification token.
    
    **Use Case:**
    - Call this endpoint when user logs out
    - Call this when user disables notifications
    - Call this when switching devices
    
    **Request Body:**
    - `expo_push_token`: The token to unregister
    
    **Behavior:**
    - Token is marked as inactive (soft delete)
    - Token remains in database for audit purposes
    - User will no longer receive notifications on this device
    
    **Returns:**
    - Success message
    """
    
    success = await push_token_crud.unregister_push_token(
        db, current_user.id, token_data.expo_push_token
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push token not found or already inactive"
        )
    
    return {
        "success": True,
        "message": "Push token unregistered successfully"
    }


@router.get("/tokens", response_model=PushTokenListResponse)
async def get_user_push_tokens(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all push tokens for the authenticated user.
    
    **Query Parameters:**
    - `active_only`: If True, return only active tokens (default: True)
    
    **Returns:**
    - List of push tokens with device information
    - Ordered by last_used_at (most recent first)
    
    **Use Cases:**
    - View all devices where user is logged in
    - Manage notification settings per device
    - Debug notification issues
    """
    
    tokens = await push_token_crud.get_user_push_tokens(
        db, current_user.id, active_only=active_only
    )
    
    return PushTokenListResponse(
        success=True,
        data=tokens,
        total=len(tokens)
    )


@router.delete("/tokens/{token_id}", response_model=dict)
async def delete_push_token_by_id(
    token_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific push token by ID.
    
    **Path Parameters:**
    - `token_id`: The ID of the token to delete
    
    **Authorization:**
    - User can only delete their own tokens
    
    **Returns:**
    - Success message
    """
    
    # Get all user tokens
    tokens = await push_token_crud.get_user_push_tokens(
        db, current_user.id, active_only=False
    )
    
    # Find the token
    token_to_delete = next((t for t in tokens if t.id == token_id), None)
    
    if not token_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push token not found"
        )
    
    # Deactivate it
    await push_token_crud.unregister_push_token(
        db, current_user.id, token_to_delete.expo_push_token
    )
    
    return {
        "success": True,
        "message": "Push token deleted successfully"
    }


@router.post("/test", response_model=dict)
async def send_test_notification(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a test push notification to all user's active devices.
    
    **Use Case:**
    - Test if push notifications are working
    - Verify device registration
    - Debug notification delivery
    
    **Returns:**
    - Success/failure count
    """
    from app.services.expo_push_service import ExpoPushNotificationService
    
    # Get user's active tokens
    tokens = await push_token_crud.get_user_push_tokens(
        db, current_user.id, active_only=True
    )
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active push tokens found. Please register a device first."
        )
    
    service = ExpoPushNotificationService()
    success_count = 0
    failure_count = 0
    
    for token in tokens:
        result = await service.send_notification(
            expo_push_token=token.expo_push_token,
            title="Test Notification 🔔",
            body="This is a test notification from DARI Wallet!",
            data={
                "type": "test",
                "timestamp": str(token.last_used_at)
            },
            priority="high"
        )
        
        if result.get("error"):
            failure_count += 1
        else:
            success_count += 1
    
    return {
        "success": True,
        "message": f"Sent test notifications to {len(tokens)} device(s)",
        "results": {
            "total": len(tokens),
            "success": success_count,
            "failed": failure_count
        }
    }
