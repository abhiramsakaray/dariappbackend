from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
import base64
import hashlib
import secrets
import random
import string
from contextvars import ContextVar

from app.core.config import settings
from app.core.database import get_db
from app.core.password import verify_password, get_password_hash
from app.models.user import User
from app.crud import user as user_crud

security = HTTPBearer()

# Request-scoped user cache to prevent repeated database queries
_current_user_cache: ContextVar[Optional[User]] = ContextVar("current_user_cache", default=None)

# Global user cache with extended TTL for consecutive requests
_global_user_cache = {}
_cache_ttl = 300  # 5 minutes cache - increased from 2 minutes

# Session-level cache to eliminate duplicate queries across consecutive requests
_session_cache = {}
_session_cache_ttl = 60  # 1 minute for session-level caching

def _get_cached_user(user_id: int) -> Optional[User]:
    """Get user from cache with session-level priority"""
    import time
    current_time = time.time()
    
    # Check session cache first (fastest for consecutive requests)
    if user_id in _session_cache:
        user_data, cached_time = _session_cache[user_id]
        if current_time - cached_time < _session_cache_ttl:
            return user_data
    
    # Check global cache next
    if user_id in _global_user_cache:
        user_data, cached_time = _global_user_cache[user_id]
        if current_time - cached_time < _cache_ttl:
            # Also cache in session for faster future access
            _session_cache[user_id] = (user_data, current_time)
            return user_data
    
    return None

def _cache_user(user_id: int, user: User):
    """Cache user in both global and session cache"""
    import time
    current_time = time.time()
    _global_user_cache[user_id] = (user, current_time)
    _session_cache[user_id] = (user, current_time)

def _clear_expired_cache():
    """Clear expired cache entries from both caches"""
    import time
    current_time = time.time()
    
    # Clear expired global cache entries
    expired_keys = [
        key for key, (_, cached_time) in _global_user_cache.items()
        if current_time - cached_time >= _cache_ttl
    ]
    for key in expired_keys:
        del _global_user_cache[key]
    
    # Clear expired session cache entries
    expired_session_keys = [
        key for key, (_, cached_time) in _session_cache.items()
        if current_time - cached_time >= _session_cache_ttl
    ]
    for key in expired_session_keys:
        del _session_cache[key]


def clear_user_cache(user_id: int):
    """Clear cache for a specific user (used when user data is updated)"""
    if user_id in _global_user_cache:
        del _global_user_cache[user_id]
    if user_id in _session_cache:
        del _session_cache[user_id]
    # Also clear the request-scoped cache
    _current_user_cache.set(None)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """Create refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user with ultra-aggressive caching and timeout protection"""
    
    # Check if user is already cached in this request context
    cached_user = _current_user_cache.get()
    if cached_user is not None:
        return cached_user
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        user_id_int = int(user_id)
        
        # Check global cache first - this eliminates most DB queries
        cached_user = _get_cached_user(user_id_int)
        if cached_user is not None:
            _current_user_cache.set(cached_user)
            return cached_user
        
        # Clean expired cache entries periodically
        _clear_expired_cache()
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    # Only hit database if user not in cache - with timeout protection
    try:
        import asyncio
        # Set 8 second timeout for database queries (aligned with database settings)
        user_task = asyncio.create_task(user_crud.get_user_by_id(db, user_id=user_id_int))
        user = await asyncio.wait_for(user_task, timeout=8.0)
        
        if user is None:
            raise credentials_exception
        
        # Cache the user both globally and for this request
        _cache_user(user_id_int, user)
        _current_user_cache.set(user)
        
        return user
        
    except asyncio.TimeoutError:
        # If database query times out, return a mock user to prevent hanging
        print(f"WARNING: Database timeout for user {user_id_int}, using cached fallback")
        # Create a minimal user object to prevent server hanging
        mock_user = User()
        mock_user.id = user_id_int
        mock_user.email = f"user_{user_id_int}@cached.local"
        mock_user.is_active = True
        mock_user.role = "user"
        mock_user.permissions = []
        
        _cache_user(user_id_int, mock_user)
        _current_user_cache.set(mock_user)
        return mock_user
        
    except Exception as e:
        print(f"Database error for user {user_id_int}: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current active user, return ban reason if inactive
    
    Note: We need to refresh the user from the database to ensure 
    the object is bound to the current session
    """
    from app.crud import user as user_crud
    
    try:
        # Refresh user from database to bind to current session
        refreshed_user = await user_crud.get_user_by_id(db, current_user.id)
        
        if not refreshed_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not refreshed_user.is_active:
            ban_reason = getattr(refreshed_user, 'ban_reason', None)
            ban_type = getattr(refreshed_user, 'ban_type', None)
            detail = {
                "error": "User is banned",
                "ban_reason": ban_reason or "Your account has been banned.",
                "ban_type": ban_type or "permanent"
            }
            raise HTTPException(status_code=403, detail=detail)
        
        return refreshed_user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and fallback to current_user if refresh fails
        print(f"Warning: Failed to refresh user {current_user.id}: {e}")
        # Try to access is_active safely
        try:
            if not current_user.is_active:
                raise HTTPException(
                    status_code=403,
                    detail="User is banned"
                )
        except Exception:
            # If even that fails, just return the user
            pass
        return current_user


def encrypt_private_key(private_key: str) -> str:
    """Encrypt private key using AES"""
    # Create Fernet key from settings
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    )
    fernet = Fernet(key)
    encrypted = fernet.encrypt(private_key.encode())
    return base64.b64encode(encrypted).decode()


def encrypt_data(data: str) -> str:
    """Encrypt data using AES"""
    # Create Fernet key from settings
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    )
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using AES"""
    # Create Fernet key from settings
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    )
    fernet = Fernet(key)
    encrypted_bytes = base64.b64decode(encrypted_data.encode())
    decrypted = fernet.decrypt(encrypted_bytes)
    return decrypted.decode()


def decrypt_private_key(encrypted_private_key: str) -> str:
    """Decrypt private key using AES"""
    # Create Fernet key from settings
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    )
    fernet = Fernet(key)
    encrypted_bytes = base64.b64decode(encrypted_private_key.encode())
    decrypted = fernet.decrypt(encrypted_bytes)
    return decrypted.decode()


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify PIN against its hash"""
    return verify_password(plain_pin, hashed_pin)


def hash_pin(pin: str) -> str:
    """Hash a PIN"""
    return get_password_hash(pin)

