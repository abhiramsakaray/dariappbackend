"""
Permission checking utilities for the DARI platform.
Provides functions for validating user permissions and role-based access control.
"""

from typing import List, Optional, Set
from functools import wraps
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
# from app.models.permission import Permission, UserPermission  # Admin functionality removed
# from app.schemas.admin import ROLE_PERMISSION_PRESETS, VALID_PERMISSIONS  # Admin functionality removed


def has_permission(user: User, permission: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user: User object
        permission: Permission name to check
        
    Returns:
        bool: True if user has the permission
    """
    if not user or not user.is_active:
        return False
    
    # Superadmin has all permissions
    if user.role == UserRole.SUPERADMIN:
        return True
    
    # Check JSON permissions field
    if isinstance(user.permissions, list):
        return permission in user.permissions
    
    return False


def check_permissions(user: User, required_permissions: List[str]) -> bool:
    """
    Check if user has all required permissions.
    
    Args:
        user: User object
        required_permissions: List of permission names to check
        
    Returns:
        bool: True if user has all required permissions
    """
    if not user or not user.is_active:
        return False
    
    # Superadmin has all permissions
    if user.role == UserRole.SUPERADMIN:
        return True
    
    return all(has_permission(user, perm) for perm in required_permissions)


def check_any_permission(user: User, permissions: List[str]) -> bool:
    """
    Check if user has any of the specified permissions.
    
    Args:
        user: User object
        permissions: List of permission names to check
        
    Returns:
        bool: True if user has at least one of the permissions
    """
    if not user or not user.is_active:
        return False
    
    # Superadmin has all permissions
    if user.role == UserRole.SUPERADMIN:
        return True
    
    return any(has_permission(user, perm) for perm in permissions)


def get_role_permissions(role: str) -> List[str]:
    """
    Get default permissions for a role.
    
    Args:
        role: Role name (SubAdminRole enum value)
        
    Returns:
        List[str]: List of permission names for the role
    """
    # Admin functionality removed - return empty list
    return []


def merge_permissions(base_permissions: List[str], additional_permissions: List[str]) -> List[str]:
    """
    Merge two permission lists, removing duplicates.
    
    Args:
        base_permissions: Base list of permissions
        additional_permissions: Additional permissions to merge
        
    Returns:
        List[str]: Merged and deduplicated permission list
    """
    return list(set(base_permissions + additional_permissions))


def validate_permissions(permissions: List[str]) -> tuple[bool, List[str]]:
    """
    Validate a list of permissions against valid permissions.
    
    Args:
        permissions: List of permission names to validate
        
    Returns:
        tuple: (is_valid, invalid_permissions)
    """
    if not permissions:
        return True, []
    
    invalid_perms = [perm for perm in permissions if perm not in VALID_PERMISSIONS]
    return len(invalid_perms) == 0, invalid_perms


async def sync_user_permissions(
    db: AsyncSession, 
    user: User, 
    permissions: List[str], 
    granted_by_id: Optional[int] = None
) -> None:
    """
    Synchronize user permissions in both JSON field and junction table.
    
    Args:
        db: Database session
        user: User object
        permissions: List of permissions to set
        granted_by_id: ID of user granting the permissions
    """
    # Validate permissions
    is_valid, invalid_perms = validate_permissions(permissions)
    if not is_valid:
        raise ValueError(f"Invalid permissions: {invalid_perms}")
    
    # Update JSON field
    user.permissions = permissions
    
    # Clear existing user permissions
    await db.execute(
        select(UserPermission).where(UserPermission.user_id == user.id)
    )
    result = await db.execute(
        select(UserPermission).where(UserPermission.user_id == user.id)
    )
    existing_permissions = result.scalars().all()
    
    for perm in existing_permissions:
        await db.delete(perm)
    
    # Add new permissions to junction table
    for permission_name in permissions:
        user_permission = UserPermission(
            user_id=user.id,
            permission_name=permission_name,
            granted_by=granted_by_id
        )
        db.add(user_permission)
    
    await db.commit()


async def get_user_permissions_detailed(db: AsyncSession, user_id: int) -> List[dict]:
    """
    Get detailed permission information for a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        List[dict]: List of permission details with metadata
    """
    query = (
        select(UserPermission, Permission)
        .join(Permission, UserPermission.permission_name == Permission.name)
        .where(UserPermission.user_id == user_id)
    )
    
    result = await db.execute(query)
    permissions_data = result.all()
    
    return [
        {
            "name": permission.name,
            "description": permission.description,
            "category": permission.category,
            "granted_at": user_permission.granted_at,
            "granted_by": user_permission.granted_by
        }
        for user_permission, permission in permissions_data
    ]


def require_permissions(*required_permissions: str):
    """
    Decorator for permission-based access control.
    
    Usage:
        @require_permissions('user_view', 'user_manage')
        async def some_endpoint(current_user: User = Depends(get_current_user)):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                # Try to find it in args (for positional arguments)
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not check_permissions(current_user, list(required_permissions)):
                missing_perms = [
                    perm for perm in required_permissions 
                    if not has_permission(current_user, perm)
                ]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Missing: {missing_perms}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """
    Decorator that requires user to have at least one of the specified permissions.
    
    Usage:
        @require_any_permission('user_view', 'admin_manage')
        async def some_endpoint(current_user: User = Depends(get_current_user)):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                # Try to find it in args
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not check_any_permission(current_user, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Need one of: {list(permissions)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PermissionChecker:
    """Permission checker class for complex permission logic"""
    
    def __init__(self, user: User):
        self.user = user
    
    def can(self, permission: str) -> bool:
        """Check if user can perform an action"""
        return has_permission(self.user, permission)
    
    def can_all(self, permissions: List[str]) -> bool:
        """Check if user can perform all actions"""
        return check_permissions(self.user, permissions)
    
    def can_any(self, permissions: List[str]) -> bool:
        """Check if user can perform any of the actions"""
        return check_any_permission(self.user, permissions)
    
    def is_admin(self) -> bool:
        """Check if user is admin or superadmin"""
        return self.user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    
    def is_superadmin(self) -> bool:
        """Check if user is superadmin"""
        return self.user.role == UserRole.SUPERADMIN
    
    def can_manage_user(self, target_user: User) -> bool:
        """Check if user can manage another user"""
        # Superadmin can manage anyone
        if self.is_superadmin():
            return True
        
        # Admin can manage non-superadmin users
        if self.is_admin() and target_user.role != UserRole.SUPERADMIN:
            return True
        
        # Sub-admin with user management permission can manage regular users
        if (self.can('user_manage') and 
            target_user.role == UserRole.USER):
            return True
        
        return False