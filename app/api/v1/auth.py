from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta, datetime
import asyncio

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    verify_password, create_access_token, create_refresh_token, 
    verify_token, get_current_user, get_current_active_user, hash_pin, verify_pin
)
from app.schemas.user import (
    UserCreate, UserLoginResponse, UserResponse, 
    PinCreate, PinVerify,
    RefreshTokenRequest, RegistrationOTPRequest, RegistrationComplete,
    LoginWithOTP, LoginOTPRequest, ForgotPasswordRequest, ForgotPasswordVerify
)
from app.crud import user as user_crud
from app.services.otp_service import (
    send_otp, verify_otp_code, store_registration_data, 
    verify_registration_otp, send_login_otp, verify_login_otp
)
from app.services.logging_service import log_login_attempt
from app.models.user import User


router = APIRouter()
security = HTTPBearer()


# ================================
# 1. REGISTRATION ENDPOINTS
# ================================

@router.post("/register/request-otp")
async def request_registration_otp(
    registration_request: RegistrationOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """Step 1: Request OTP for new user registration"""
    
    # Check if email already exists
    existing_user = await user_crud.get_user_by_email(db, email=registration_request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone already exists
    existing_phone = await user_crud.get_user_by_phone(db, phone=registration_request.phone)
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Store registration data temporarily and send OTP
    registration_data = {
        "email": registration_request.email,
        "phone": registration_request.phone
    }
    
    otp_sent = await store_registration_data(registration_request.email, registration_data)
    
    if not otp_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again."
        )
    
    return {
        "success": True,
        "message": "OTP sent successfully",
        "data": {
            "otp_expires_at": (datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)).isoformat() + "Z",
            "otp_length": 6
        }
    }


@router.post("/register/complete", status_code=status.HTTP_201_CREATED)
async def complete_registration(
    registration_data: RegistrationComplete,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Step 2: Complete registration with OTP verification"""
    
    # Verify OTP and get stored registration data
    stored_data = await verify_registration_otp(registration_data.email, registration_data.otp)
    
    if not stored_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Verify that the data matches
    if (stored_data["email"] != registration_data.email or 
        stored_data["phone"] != registration_data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration data mismatch"
        )
    
    # Double-check if user still doesn't exist (race condition protection)
    existing_user = await user_crud.get_user_by_email(db, email=registration_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create the user
    user_create = UserCreate(
        email=registration_data.email,
        phone=registration_data.phone,
        password=registration_data.password,
        default_currency=registration_data.default_currency,
        terms_accepted=registration_data.terms_accepted
    )
    
    db_user = await user_crud.create_user(db, user=user_create)
    
    # Log the registration
    await log_login_attempt(
        db, db_user.id, request.client.host,
        request.headers.get("user-agent", ""), True, "Registration with OTP"
    )
    
    # Create tokens for auto-login after registration
    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
    
    return {
        "success": True,
        "message": "Registration successful",
        "data": {
            "user": {
                "id": db_user.id,
                "email": db_user.email,
                "phone": db_user.phone,
                "role": db_user.role,
                "is_active": db_user.is_active,
                "kyc_verified": db_user.kyc_verified,
                "terms_accepted": db_user.terms_accepted,
                "otp_enabled": db_user.otp_enabled,
                "created_at": db_user.created_at,
                "default_currency": db_user.default_currency
            },
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        }
    }


# ================================
# 2. LOGIN ENDPOINTS
# ================================

@router.post("/login/request-otp")
async def request_login_otp(
    login_request: LoginOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Step 1: Verify credentials and send OTP for 2FA login"""
    
    # Get user by email
    user = await user_crud.get_user_by_email(db, email=login_request.email)
    
    if not user or not verify_password(login_request.password, user.password_hash):
        await log_login_attempt(
            db, None, request.client.host,
            request.headers.get("user-agent", ""), False, "Invalid credentials - OTP request"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        await log_login_attempt(
            db, user.id, request.client.host,
            request.headers.get("user-agent", ""), False, "Account deactivated - OTP request"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Send OTP to email for 2FA
    otp_sent = await send_login_otp(login_request.email, user.id)
    
    if not otp_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again."
        )
    
    # Mask email and phone for privacy
    email_parts = user.email.split('@')
    masked_email = f"{email_parts[0][:1]}***@{email_parts[1]}"
    masked_phone = f"{user.phone[:3]}****{user.phone[-4:]}" if user.phone else None
    
    return {
        "success": True,
        "message": "OTP sent successfully",
        "data": {
            "otp_expires_at": (datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)).isoformat() + "Z",
            "masked_phone": masked_phone,
            "masked_email": masked_email
        }
    }


@router.post("/login/verify-otp")
async def login_with_otp(
    login_data: LoginWithOTP,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Step 2: Complete login with OTP verification (2FA)"""
    
    # Verify OTP and get user_id from verified session
    user_id = await verify_login_otp(login_data.email, login_data.otp)
    
    if not user_id:
        await log_login_attempt(
            db, None, request.client.host,
            request.headers.get("user-agent", ""), False, "Invalid OTP"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Get user by ID (already verified in step 1)
    user = await user_crud.get_user_by_id(db, user_id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        await log_login_attempt(
            db, user.id, request.client.host,
            request.headers.get("user-agent", ""), False, "Account deactivated - OTP verification"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Update last login
    await user_crud.update_user_last_login(db, user.id)
    
    # Log successful login with 2FA
    await log_login_attempt(
        db, user.id, request.client.host,
        request.headers.get("user-agent", ""), True, "Successful login with 2FA"
    )
    
    # 🆕 Auto-register push notification token if provided
    if login_data.expo_push_token and login_data.device_type:
        try:
            from app.crud import push_token as push_token_crud
            from app.schemas.push_token import PushTokenCreate
            
            push_token_create = PushTokenCreate(
                expo_push_token=login_data.expo_push_token,
                device_type=login_data.device_type,
                device_name=login_data.device_name or "Unknown Device"
            )
            
            await push_token_crud.register_push_token(db, user.id, push_token_create)
            print(f"✅ Auto-registered push token for user {user.id}")
        except Exception as e:
            # Don't fail login if push token registration fails
            print(f"⚠️ Failed to auto-register push token: {str(e)}")
    
    # Send login notification (non-blocking)
    try:
        from app.services.email_service import EmailService
        from datetime import datetime
        
        email_service = EmailService()
        await email_service.send_new_login_alert(
            email=user.email,
            user_name=user.email.split('@')[0],
            ip_address=request.client.host or "Unknown",
            user_agent=request.headers.get("user-agent", "Unknown"),
            location="Unknown",
            login_time=datetime.utcnow()
        )
    except Exception as e:
        print(f"⚠️ Failed to send login alert: {str(e)}")
    
    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
                "kyc_verified": user.kyc_verified,
                "terms_accepted": user.terms_accepted,
                "otp_enabled": user.otp_enabled,
                "created_at": user.created_at,
                "last_login": user.last_login
            },
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        }
    }


# ================================
# 3. TOKEN MANAGEMENT
# ================================

@router.post("/refresh")
async def refresh_token(token_request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    
    payload = verify_token(token_request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new access token and refresh token
    access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    
    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    }


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
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


@router.post("/logout")
async def logout(
    token_request: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Logout user (invalidate refresh token)"""
    # In production, add refresh token to blacklist in Redis
    # For now, client should discard tokens
    return {
        "success": True,
        "message": "Logged out successfully"
    }


# ================================
# 4. PIN MANAGEMENT
# ================================

@router.post("/set-pin")
async def set_pin(
    pin_data: PinCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set or update user PIN for transaction authentication"""
    
    # Validate PIN format (should be done in schema too)
    if len(pin_data.pin) < 4 or len(pin_data.pin) > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN must be 4-6 digits"
        )
    
    # Check for sequential or repeating PINs
    pin_str = str(pin_data.pin)
    if pin_str in ['1234', '4321', '0000', '1111', '2222', '3333', '4444', '5555', '6666', '7777', '8888', '9999']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN cannot be sequential or repeating"
        )
    
    hashed_pin = hash_pin(pin_data.pin)
    success = await user_crud.update_user_pin(db, current_user.id, hashed_pin)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set PIN"
        )
    
    # Clear user cache so next request gets fresh data with updated PIN
    from app.core.security import clear_user_cache
    clear_user_cache(current_user.id)
    
    return {
        "success": True,
        "message": "PIN set successfully"
    }


@router.post("/verify-pin")
async def verify_pin_endpoint(
    pin_data: PinVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify user PIN for transaction authentication"""
    
    # Refresh user from database to avoid detached instance error
    from app.crud import user as user_crud
    refreshed_user = await user_crud.get_user_by_id(db, current_user.id)
    
    if not refreshed_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not refreshed_user.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN not set"
        )
    
    if not verify_pin(pin_data.pin, refreshed_user.pin_hash):
        # Track failed attempts (implement in production)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PIN"
        )
    
    return {
        "success": True,
        "message": "PIN verified",
        "data": {
            "verified": True
        }
    }


# ================================
# 5. PASSWORD RESET
# ================================

@router.post("/forgot-password/request-otp")
async def forgot_password_request_otp(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request OTP for password reset"""
    
    user = await user_crud.get_user_by_email(db, data.email)
    if not user:
        # Don't reveal if email exists (security best practice)
        return {
            "success": True,
            "message": "Password reset OTP sent",
            "data": {
                "otp_expires_at": (datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)).isoformat() + "Z"
            }
        }
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not active"
        )
    
    # Send OTP
    success = await send_otp(data.email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )
    
    return {
        "success": True,
        "message": "Password reset OTP sent",
        "data": {
            "otp_expires_at": (datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)).isoformat() + "Z"
        }
    }


@router.post("/forgot-password/reset")
async def forgot_password_reset(
    data: ForgotPasswordVerify,
    db: AsyncSession = Depends(get_db)
):
    """Reset password using OTP verification"""
    
    user = await user_crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not active"
        )
    
    # Verify OTP
    is_valid = await verify_otp_code(data.email, data.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Update password
    from app.core.security import get_password_hash
    user.password_hash = get_password_hash(data.new_password)
    await db.commit()
    
    # Invalidate all existing sessions (implement token blacklist in production)
    
    # Send password changed notification
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        # Send email notification about password change
    except Exception as e:
        print(f"⚠️ Failed to send password change notification: {str(e)}")
    
    return {
        "success": True,
        "message": "Password reset successful"
    }
