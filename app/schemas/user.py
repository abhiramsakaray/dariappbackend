
from pydantic import BaseModel, Field, field_validator, validator, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole

# Forgot Password Schemas
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordVerify(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserBase(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
    default_currency: str = Field(default="USD", max_length=3)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    terms_accepted: bool = Field(default=True)
    
    @field_validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?1?\d{9,15}$')
    default_currency: Optional[str] = Field(None, max_length=3)


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    kyc_verified: bool
    terms_accepted: bool
    otp_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('new_password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class PinCreate(BaseModel):
    pin: str = Field(..., pattern=r'^\d{4,6}$')


class PinVerify(BaseModel):
    pin: str = Field(..., pattern=r'^\d{4,6}$')


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str = Field(..., pattern=r'^\d{6}$')


class RegistrationOTPRequest(BaseModel):
    """Request OTP for registration"""
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')


class RegistrationComplete(BaseModel):
    """Complete registration with OTP verification"""
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    password: str = Field(..., min_length=8, max_length=128)
    otp: str = Field(..., pattern=r'^\d{6}$')
    default_currency: str = Field("USD", max_length=3)
    terms_accepted: bool = Field(..., description="Must accept terms and conditions")
    
    @validator('terms_accepted')
    def validate_terms_accepted(cls, v):
        if not v:
            raise ValueError('Terms and conditions must be accepted')
        return v


class LoginWithOTP(BaseModel):
    """Complete login with OTP verification (no need to re-enter password)"""
    email: EmailStr
    otp: str = Field(..., pattern=r'^\d{6}$')
    
    # Optional push notification registration (auto-register on login)
    expo_push_token: Optional[str] = None
    device_type: Optional[str] = Field(None, pattern=r'^(ios|android)$')
    device_name: Optional[str] = None


class LoginOTPRequest(BaseModel):
    """Request OTP for login (2FA)"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserStats(BaseModel):
    total_users: int
    active_users: int
    kyc_pending: int
    kyc_approved: int
    kyc_rejected: int


class CheckPhonesRequest(BaseModel):
    """Request to check which phone numbers are DARI users"""
    phones: list[str] = Field(..., min_length=1, description="List of phone numbers to check")


class DariUserInfo(BaseModel):
    """Information about a DARI user"""
    phone: str
    full_name: Optional[str] = None
    dari_address: Optional[str] = None
    full_address: Optional[str] = None


class CheckPhonesResponse(BaseModel):
    """Response with DARI users found"""
    dari_users: list[DariUserInfo]
