from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


from app.models.notification import NotificationType, NotificationStatus
from app.models.admin_log import ActionType
from app.models.transaction import TransactionStatus, TransactionType


# Admin Notification Schemas
class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"  # Disabled for now


class AdminNotificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: NotificationType
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.IN_APP])
    
    # Target settings
    target_all_users: bool = False
    target_user_ids: Optional[List[int]] = None
    target_verified_only: bool = False
    target_active_only: bool = True

    # Scheduling (optional for future implementation)
    scheduled_at: Optional[datetime] = None


class BulkNotificationResponse(BaseModel):
    total_targeted: int
    notifications_sent: int
    failed_sends: int
    channels_used: List[str]
    notification_ids: List[int]


# Admin User Management Schemas
class AdminUserDetails(BaseModel):
    id: int
    email: str
    phone: Optional[str]
    role: str
    is_active: bool
    kyc_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    total_transactions: int
    total_volume: float
    current_balance: float
    risk_score: float


class UserSearchFilters(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    kyc_verified: Optional[bool] = None
    min_balance: Optional[float] = None
    max_balance: Optional[float] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


# Transaction Monitoring Schemas
class TransactionMonitoringFilters(BaseModel):
    user_id: Optional[int] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    status: Optional[TransactionStatus] = None
    transaction_type: Optional[TransactionType] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    high_risk_only: bool = False
    min_risk_score: Optional[float] = None


class AdminTransactionDetails(BaseModel):
    id: int
    from_address: str
    to_address: str
    amount: float
    token_symbol: str
    status: str
    transaction_type: str
    risk_score: float
    from_user_email: Optional[str]
    to_user_email: Optional[str]
    tx_hash: Optional[str]
    created_at: datetime
    gas_fee: Optional[float]


# System Statistics Schemas
class SystemStats(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    total_transactions: int
    total_volume: float
    total_platform_balance: float
    pending_kyc: int
    high_risk_transactions: int
    system_health_score: float
    # Additional growth and percentage data
    new_users_this_month: int
    user_growth_percentage: float
    volume_growth_percentage: float
    active_users_percentage: int
    average_balance_per_user: float


class PlatformHealthMetrics(BaseModel):
    # Core Performance Metrics
    uptime_percentage: float
    uptime_days: float
    avg_transaction_time: float
    avg_gas_fee: float
    
    # Success & Reliability Metrics
    transaction_success_rate: float
    error_rate: float
    availability_score: float
    
    # Performance Metrics
    api_response_time_ms: float
    transactions_per_minute: float
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    
    # Service Health
    service_health: Dict[str, str]
    healthy_services: int
    total_services: int
    
    # Timestamps
    last_updated: datetime
    measurement_period: str


class UserBalancesSummary(BaseModel):
    total_users_with_balance: int
    total_platform_balance: float
    average_balance_per_user: float
    top_holders: List[Dict[str, Any]]
    balance_distribution: Dict[str, int]


# Sub-Admin and Task Management Schemas
class SubAdminRole(str, Enum):
    KYC_REVIEWER = "kyc_reviewer"
    TRANSACTION_MONITOR = "transaction_monitor"
    CUSTOMER_SUPPORT = "customer_support"
    CONTENT_MODERATOR = "content_moderator"


# Valid permissions list for validation
VALID_PERMISSIONS = [
    # KYC Permissions
    "kyc_view", "kyc_approve", "kyc_reject",
    # User Management Permissions
    "user_view", "user_manage", "user_ban",
    # Transaction Permissions
    "transaction_view", "transaction_flag", "transaction_investigate",
    # Wallet Permissions
    "wallet_view", "wallet_freeze",
    # Communication Permissions
    "notification_send", "notification_broadcast",
    # Support Permissions
    "ticket_manage", "ticket_escalate",
    # Content Moderation Permissions
    "content_review", "content_moderate",
    # Reporting Permissions
    "report_view", "report_generate",
    # System Permissions
    "system_configure", "audit_log_view",
    # Admin Management Permissions
    "admin_manage", "permission_manage",
]

# Role-based permission presets
ROLE_PERMISSION_PRESETS = {
    SubAdminRole.KYC_REVIEWER: [
        "kyc_view", "kyc_approve", "kyc_reject", 
        "user_view", "report_view"
    ],
    SubAdminRole.TRANSACTION_MONITOR: [
        "transaction_view", "transaction_flag", "transaction_investigate",
        "user_view", "wallet_view", "report_view"
    ],
    SubAdminRole.CUSTOMER_SUPPORT: [
        "user_view", "notification_send", 
        "ticket_manage", "ticket_escalate"
    ],
    SubAdminRole.CONTENT_MODERATOR: [
        "content_review", "content_moderate", 
        "user_view", "user_manage", "report_view", "audit_log_view"
    ]
}


class SubAdminCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: SubAdminRole
    permissions: List[str] = Field(default_factory=list, description="List of permissions for the sub-admin")
    password: str = Field(..., min_length=8, description="Login password for sub-admin")
    temporary_access: bool = False
    access_expires_at: Optional[datetime] = None
    use_role_defaults: bool = Field(
        default=True, 
        description="If True, will use default permissions for the role. If False, will use only specified permissions."
    )

    @field_validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('permissions')
    def validate_permissions(cls, v):
        if not v:
            return v
        invalid_perms = [perm for perm in v if perm not in VALID_PERMISSIONS]
        if invalid_perms:
            raise ValueError(f'Invalid permissions: {invalid_perms}. Valid permissions: {VALID_PERMISSIONS}')
        return v

    @model_validator(mode='after')
    def set_default_permissions(self):
        """Set default permissions based on role if use_role_defaults is True and no permissions specified"""
        if self.use_role_defaults and not self.permissions:
            self.permissions = ROLE_PERMISSION_PRESETS.get(self.role, [])
        elif self.use_role_defaults and self.permissions:
            # Merge role defaults with specified permissions
            role_defaults = set(ROLE_PERMISSION_PRESETS.get(self.role, []))
            specified_perms = set(self.permissions)
            self.permissions = list(role_defaults | specified_perms)
        return self


class SubAdminUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[SubAdminRole] = None
    permissions: Optional[List[str]] = Field(None, description="List of permissions for the sub-admin")
    temporary_access: Optional[bool] = None
    access_expires_at: Optional[datetime] = None

    @field_validator('permissions')
    def validate_permissions(cls, v):
        if v is None:
            return v
        invalid_perms = [perm for perm in v if perm not in VALID_PERMISSIONS]
        if invalid_perms:
            raise ValueError(f'Invalid permissions: {invalid_perms}. Valid permissions: {VALID_PERMISSIONS}')
        return v


class SubAdminResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    permissions: List[str]
    is_active: bool
    temporary_access: bool
    access_expires_at: Optional[datetime]
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubAdminListResponse(BaseModel):
    sub_admins: List[SubAdminResponse]
    total: int
    page: int
    pages: int


class PermissionResponse(BaseModel):
    name: str
    description: str
    category: str
    created_at: Optional[datetime] = None


class PermissionCategoryResponse(BaseModel):
    category: str
    permissions: List[PermissionResponse]
    count: int


class RolePermissionPresetResponse(BaseModel):
    role: SubAdminRole
    permissions: List[str]
    description: str


class PermissionListResponse(BaseModel):
    permissions: List[PermissionResponse]
    categories: List[PermissionCategoryResponse]
    role_presets: List[RolePermissionPresetResponse]
    total_permissions: int


class SubAdminStatusUpdate(BaseModel):
    is_active: bool
    reason: Optional[str] = None


class SubAdminPasswordSetup(BaseModel):
    user_id: int
    temporary_password: str
    require_password_change: bool = True


class SubAdminPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UniversalLoginRequest(BaseModel):
    """Universal login request for all user types (admin, sub-admin, regular user)"""
    email: EmailStr
    password: str
    user_type: Optional[str] = Field(None, description="Optional: admin, user, auto-detect if not provided")


class UniversalLoginOTPRequest(BaseModel):
    """Request OTP for universal login (works for all user types)"""
    email: EmailStr
    password: str
    user_type: Optional[str] = Field(None, description="Optional: admin, user, auto-detect if not provided")


class UniversalLoginOTPVerify(BaseModel):
    """Verify OTP for universal login"""
    email: EmailStr
    otp: str = Field(..., pattern=r'^\d{6}$')


class ForgotPasswordRequest(BaseModel):
    """Forgot password request for all user types"""
    email: EmailStr
    user_type: Optional[str] = Field(None, description="Optional: admin, user, auto-detect if not provided")


class ForgotPasswordReset(BaseModel):
    """Reset password with OTP verification"""
    email: EmailStr
    otp: str = Field(..., pattern=r'^\d{6}$')
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


# Permission Management Schemas
class PermissionResponse(BaseModel):
    """Response schema for permission details"""
    name: str
    description: Optional[str]
    category: str
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionCategoryResponse(BaseModel):
    """Response schema for permissions grouped by category"""
    category: str
    permissions: List[PermissionResponse]
    count: int


class UserPermissionResponse(BaseModel):
    """Response schema for user permission assignment"""
    user_id: int
    permission_name: str
    granted_at: datetime
    granted_by: Optional[int]

    class Config:
        from_attributes = True


class RolePermissionPresetResponse(BaseModel):
    """Response schema for role-based permission presets"""
    role: SubAdminRole
    permissions: List[str]
    description: str


class PermissionListResponse(BaseModel):
    """Response schema for listing all permissions"""
    permissions: List[PermissionResponse]
    categories: List[PermissionCategoryResponse]
    role_presets: List[RolePermissionPresetResponse]
    total_permissions: int


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AdminTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    assigned_to_id: int
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    related_user_id: Optional[int] = None
    related_transaction_id: Optional[int] = None


class AdminTaskResponse(BaseModel):
    id: int
    title: str
    description: str
    assigned_to_email: str
    priority: str
    status: str
    created_at: datetime
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    related_user_email: Optional[str]
    related_transaction_hash: Optional[str]


# Logging and Audit Schemas
class AdminLogEntry(BaseModel):
    id: int
    action_type: str
    admin_email: str
    target_user_email: Optional[str]
    description: str
    ip_address: Optional[str]
    created_at: datetime


class UserLogEntry(BaseModel):
    id: int
    user_email: str
    action: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


class EmailLogEntry(BaseModel):
    id: int
    recipient_email: str
    subject: str
    email_type: str
    status: str
    sent_at: Optional[datetime]
    error_message: Optional[str]


# System Health and Monitoring
class SystemHealthCheck(BaseModel):
    database_status: str
    redis_status: str
    email_service_status: str
    blockchain_connectivity: str
    api_response_time: float
    active_connections: int
    system_load: float
    last_checked: datetime


# Filters and Pagination
class AdminPaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=500)
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$")


class DateRangeFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None