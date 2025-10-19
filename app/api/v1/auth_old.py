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
    UserCreate, UserLogin, UserLoginResponse, UserResponse, 
    PasswordChange, PinCreate, PinVerify, OTPRequest, OTPVerify,
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

# --- Forgot Password: Request OTP ---
@router.post("/forgot-password/request-otp")
async def forgot_password_request_otp(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request OTP for password reset"""
    user = await user_crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is not active")
    # Reuse OTP logic
    success = await send_otp(data.email)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    return {"message": "OTP sent to email"}

# --- Forgot Password: Verify OTP and Reset Password ---
@router.post("/forgot-password/reset")
async def forgot_password_reset(
    data: ForgotPasswordVerify,
    db: AsyncSession = Depends(get_db)
):
    """Reset password using OTP"""
    user = await user_crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is not active")
    # Verify OTP
    is_valid = await verify_otp_code(data.email, data.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    # Set new password
    from app.core.security import get_password_hash
    user.password_hash = get_password_hash(data.new_password)
    await db.commit()
    return {"message": "Password reset successfully"}
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
    UserCreate, UserLogin, UserLoginResponse, UserResponse, 
    PasswordChange, PinCreate, PinVerify, OTPRequest, OTPVerify,
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

# --- Forgot Password: Request OTP ---
@router.post("/forgot-password/request-otp")
async def forgot_password_request_otp(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request OTP for password reset"""
    user = await user_crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is not active")
    # Reuse OTP logic
    success = await send_otp(data.email)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    return {"message": "OTP sent to email"}

# --- Forgot Password: Verify OTP and Reset Password ---
@router.post("/forgot-password/reset")
async def forgot_password_reset(
    data: ForgotPasswordVerify,
    db: AsyncSession = Depends(get_db)
):
    """Reset password using OTP"""
    user = await user_crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is not active")
    # Verify OTP
    is_valid = await verify_otp_code(data.email, data.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    # Set new password
    from app.core.security import get_password_hash
    user.password_hash = get_password_hash(data.new_password)
    await db.commit()
    return {"message": "Password reset successfully"}


@router.post("/register/request-otp")
async def request_registration_otp(
    registration_request: RegistrationOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """Step 1: Request OTP for registration"""
    
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
        "message": "OTP sent to your email. Please verify to complete registration.",
        "email": registration_request.email
    }


@router.post("/register/complete", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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
    
    return db_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, deprecated=True)
async def register(user: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """Register a new user (DEPRECATED - Use /register/request-otp and /register/complete instead)"""
    
    # Check if user already exists
    existing_user = await user_crud.get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_phone = await user_crud.get_user_by_phone(db, phone=user.phone)
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create user
    db_user = await user_crud.create_user(db, user=user)
    
    # Log the registration
    await log_login_attempt(
        db, db_user.id, request.client.host, 
        request.headers.get("user-agent", ""), True, "Registration"
    )
    
    return db_user


@router.post("/login", response_model=UserLoginResponse, deprecated=True)
async def login(
    user_credentials: UserLogin, 
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return tokens (DEPRECATED - Use /login/request-otp and /login/verify-otp for 2FA)"""
    
    # Get user by email
    user = await user_crud.get_user_by_email(db, email=user_credentials.email)
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        await log_login_attempt(
            db, None, request.client.host, 
            request.headers.get("user-agent", ""), False, "Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        await log_login_attempt(
            db, user.id, request.client.host, 
            request.headers.get("user-agent", ""), False, "Account deactivated"
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
    
    # Log successful login
    await log_login_attempt(
        db, user.id, request.client.host, 
        request.headers.get("user-agent", ""), True, "Successful login"
    )
    
    # Send login alert email with improved error handling
    try:
        from app.services.email_service import EmailService
        from datetime import datetime
        import traceback
        
        email_service = EmailService()
        await email_service.send_new_login_alert(
            email=user.email,
            user_name=user.email.split('@')[0],
            ip_address=request.client.host or "Unknown",
            user_agent=request.headers.get("user-agent", "Unknown"),
            location="Unknown",
            login_time=datetime.utcnow()
        )
        print(f"✅ Login alert sent successfully to {user.email}")
    except Exception as e:
        # Don't fail login if email fails - just log the error
        print(f"⚠️ Failed to send login alert to {user.email}: {str(e)}")
        print(f"Error details: {traceback.format_exc()}")
    
    # Send login notification email (non-blocking)
    try:
        from datetime import datetime
        import pytz
        import asyncio
        
        # Get current time in a readable format
        now = datetime.now(pytz.UTC)
        login_time = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Extract a friendly name from email (before @ symbol)
        user_name = user.email.split('@')[0].capitalize()
        
        # Send login notification asynchronously without blocking
        async def send_notification():
            try:
                from app.services.otp_service import send_email_notification
                
                subject = "🔐 New Login to Your DARI Wallet Account"
                
                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">🔐 DARI Wallet</h1>
                        <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Login Notification</p>
                    </div>
                    
                    <div style="background: #ffffff; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h2 style="color: #333; margin-top: 0;">Hello {user_name}!</h2>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <p style="margin: 0; font-size: 16px;">
                                <strong>We detected a new login to your DARI Wallet account.</strong>
                            </p>
                        </div>
                        
                        <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #1976d2;">📊 Login Details:</h3>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li><strong>Time:</strong> {login_time}</li>
                                <li><strong>IP Address:</strong> {request.client.host or "Unknown"}</li>
                                <li><strong>Device:</strong> {request.headers.get("user-agent", "Unknown Device")[:100]}</li>
                            </ul>
                        </div>
                        
                        <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                            <h3 style="margin-top: 0; color: #856404;">🛡️ Security Notice:</h3>
                            <p style="margin: 0;">
                                If this was you, no action is needed. If you don't recognize this login, please change your password immediately.
                            </p>
                        </div>
                        
                        <div style="text-align: center; border-top: 1px solid #eee; padding-top: 20px;">
                            <p style="color: #666; margin: 0;">
                                Best regards,<br>
                                <strong>DARI Wallet Security Team</strong>
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                await send_email_notification(user.email, subject, body, True)
            except Exception as e:
                print(f"Background email notification failed: {e}")
        
        # Fire and forget - don't wait for email to complete
        asyncio.create_task(send_notification())
        
    except Exception as e:
        # Don't fail login if email notification fails
        print(f"Failed to send login notification: {e}")
    
    return UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


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
    
    return {
        "message": "Credentials verified. OTP sent to your email for 2FA.",
        "email": login_request.email,
        "requires_otp": True,
        "otp_expires_in_minutes": settings.OTP_EXPIRE_MINUTES
    }


@router.post("/login/verify-otp", response_model=UserLoginResponse)
async def login_with_otp(
    login_data: LoginWithOTP,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Step 2: Complete login with OTP verification (2FA) - Only email and OTP required"""
    
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
        print(f"✅ 2FA Login alert sent successfully to {user.email}")
    except Exception as e:
        print(f"⚠️ Failed to send 2FA login alert to {user.email}: {str(e)}")
    
    return UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )


@router.post("/refresh", response_model=dict)
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
    
    # Create new access token
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    from app.core.security import get_password_hash
    new_password_hash = get_password_hash(password_data.new_password)
    
    current_user.password_hash = new_password_hash
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/set-pin")
async def set_pin(
    pin_data: PinCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set or update user PIN"""
    
    hashed_pin = hash_pin(pin_data.pin)
    success = await user_crud.update_user_pin(db, current_user.id, hashed_pin)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set PIN"
        )
    
    return {"message": "PIN set successfully"}


@router.post("/verify-pin")
async def verify_pin_endpoint(
    pin_data: PinVerify,
    current_user: User = Depends(get_current_user)
):
    """Verify user PIN"""
    
    if not current_user.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN not set"
        )
    
    if not verify_pin(pin_data.pin, current_user.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PIN"
        )
    
    return {"message": "PIN verified successfully"}


@router.post("/request-otp")
async def request_otp(otp_request: OTPRequest):
    """Request OTP for email verification"""
    
    if not settings.OTP_EMAIL_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP service is disabled"
        )
    
    success = await send_otp(otp_request.email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )
    
    return {"message": "OTP sent successfully"}


@router.post("/verify-otp")
async def verify_otp_endpoint(otp_data: OTPVerify):
    """Verify OTP code"""
    
    is_valid = await verify_otp_code(otp_data.email, otp_data.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    return {"message": "OTP verified successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user (client should discard tokens)"""
    # In a more sophisticated implementation, you might want to blacklist the token
    return {"message": "Logged out successfully"}


# ================================
# UNIVERSAL AUTHENTICATION SYSTEM
# ================================

@router.post("/universal/login/request-otp")
async def universal_login_request_otp(
    login_data: LoginOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Universal login with OTP - Request OTP for any user type (admin, sub-admin, regular user)"""
    
    # Find user by email
    user = await user_crud.get_user_by_email(db, login_data.email)
    if not user:
        # Log failed attempt
        await log_login_attempt(
            email=login_data.email,
            success=False,
            ip_address=request.client.host if request.client else None,
            failure_reason="User not found"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        await log_login_attempt(
            email=login_data.email,
            success=False,
            ip_address=request.client.host if request.client else None,
            failure_reason="Invalid password"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user is active
    if not user.is_active:
        await log_login_attempt(
            email=login_data.email,
            success=False,
            ip_address=request.client.host if request.client else None,
            failure_reason="Account disabled"
        )
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    # Send OTP
    success = await send_login_otp(login_data.email)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    
    return {
        "message": "OTP sent to email",
        "user_type": user.role.value,
        "email": user.email,
        "requires_otp": True
    }


@router.post("/universal/login/verify-otp", response_model=UserLoginResponse)
async def universal_login_verify_otp(
    otp_data: LoginWithOTP,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Universal login with OTP - Verify OTP and complete login for any user type"""
    
    # Verify OTP
    is_valid = await verify_login_otp(otp_data.email, otp_data.otp)
    if not is_valid:
        await log_login_attempt(
            email=otp_data.email,
            success=False,
            ip_address=request.client.host if request.client else None,
            failure_reason="Invalid OTP"
        )
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    
    # Get user
    user = await user_crud.get_user_by_email(db, otp_data.email)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Log successful login
    await log_login_attempt(
        email=user.email,
        success=True,
        ip_address=request.client.host if request.client else None,
        user_id=user.id
    )
    
    # Return response based on user type
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        role=user.role.value,
        is_active=user.is_active,
        kyc_verified=user.kyc_verified,
        default_currency=user.default_currency,
        created_at=user.created_at,
        full_name=user.full_name,
        last_login=user.last_login
    )
    
    return UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_response
    )


@router.post("/universal/forgot-password/request-otp")
async def universal_forgot_password_request_otp(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Universal forgot password - Request OTP for any user type (admin, sub-admin, regular user)"""
    
    user = await user_crud.get_user_by_email(db, data.email)
    if not user:
        # Don't reveal if user exists for security
        return {"message": "If the email exists, an OTP has been sent"}
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is disabled")
    
    # Send OTP
    success = await send_otp(data.email)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    
    return {
        "message": "If the email exists, an OTP has been sent",
        "user_type": user.role.value
    }


@router.post("/universal/forgot-password/reset")
async def universal_forgot_password_reset(
    data: ForgotPasswordVerify,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Universal forgot password - Reset password with OTP verification for any user type"""
    
    # Verify OTP
    is_valid = await verify_otp_code(data.email, data.otp)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    
    # Get user
    user = await user_crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is disabled")
    
    # Update password
    from app.core.password import get_password_hash
    user.password_hash = get_password_hash(data.new_password)
    await db.commit()
    
    # Log the password reset
    from app.crud.admin import admin_crud
    from app.models.admin_log import ActionType
    await admin_crud.log_admin_action(
        db,
        admin_id=user.id,  # Self-action
        action_type=ActionType.USER_UPDATE,
        description=f"Password reset via OTP for {user.role.value}: {user.email}",
        target_user_id=user.id,
        ip_address=request.client.host if request.client else None,
        details='{"action": "password_reset_via_otp"}'
    )
    
    return {
        "message": "Password reset successfully",
        "user_type": user.role.value,
        "email": user.email
    }


# ================================
# LEGACY LOGIN (with OTP upgrade)
# ================================

@router.post("/admin/login", response_model=UserLoginResponse)
async def admin_login(
    user_credentials: UserLogin,
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    """Admin login with automatic OTP verification requirement"""
    
    # Get user
    user = await user_crud.get_user_by_email(db, user_credentials.email)
    if not user:
        await log_login_attempt(
            email=user_credentials.email,
            success=False,
            ip_address=request.client.host if request.client else None,
            failure_reason="User not found"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user is admin/sub-admin
    if user.role not in ["admin", "superadmin", "support"]:
        await log_login_attempt(
            email=user_credentials.email,
            success=False,
            ip_address=request.client.host if request.client else None,
            failure_reason="Not an admin user"
        )
        raise HTTPException(status_code=403, detail="Access denied - Admin access required")
    
    # Verify password
    if not verify_password(user_credentials.password, user.password_hash):
        await log_login_attempt(
            email=user_credentials.email,
            success=False,
            ip_address=request.client.host if request.client else None,
            failure_reason="Invalid password"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user is active
    if not user.is_active:
        await log_login_attempt(
            email=user_credentials.email,
            success=False,
            ip_address=request.client.host if request.client else None,
            failure_reason="Account disabled"
        )
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    # For now, require OTP - redirect to OTP flow
    raise HTTPException(
        status_code=202,
        detail={
            "message": "OTP verification required",
            "next_step": "Use /universal/login/request-otp endpoint",
            "user_type": user.role.value
        }
    )
