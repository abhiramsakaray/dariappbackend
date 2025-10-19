from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"
    SUPPORT = "support"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    pin_hash = Column(String(255), nullable=True)

    full_name = Column(String(255), nullable=True)  # Added to support notifications and user display

    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    default_currency = Column(String(3), default="USD", nullable=False)
    
    # FCM device token for push notifications
    fcm_device_token = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    kyc_verified = Column(Boolean, default=False, nullable=False)
    terms_accepted = Column(Boolean, default=False, nullable=False)

    ban_reason = Column(String(255), nullable=True)
    ban_type = Column(String(20), nullable=True)  # 'temporary' or 'permanent'

    otp_secret = Column(String(255), nullable=True)
    otp_enabled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Permissions stored as JSON array for quick access
    permissions = Column(JSON, default=list, nullable=True)
    
    # Relationships (using lazy string references to avoid circular imports)
    kyc_request = relationship("KYCRequest", foreign_keys="KYCRequest.user_id", back_populates="user", uselist=False)
    # wallet = relationship("Wallet", back_populates="user", uselist=False)
    address_resolver = relationship("AddressResolver", back_populates="user", uselist=False)
    # login_logs = relationship("LoginLog", back_populates="user")
    sent_transactions = relationship("Transaction", foreign_keys="Transaction.from_user_id", back_populates="from_user")
    received_transactions = relationship("Transaction", foreign_keys="Transaction.to_user_id", back_populates="to_user")
    payment_methods = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan")
    push_tokens = relationship("PushToken", back_populates="user", cascade="all, delete-orphan")
    # notifications = relationship("Notification", back_populates="user")
    # activity_logs = relationship("UserActivityLog", back_populates="user")
    # user_permissions = relationship("UserPermission", foreign_keys="UserPermission.user_id", back_populates="user")  # Admin functionality removed

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
