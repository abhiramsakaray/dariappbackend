from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransactionType(str, enum.Enum):
    SEND = "send"
    RECEIVE = "receive"
    INTERNAL = "internal"
    DEPOSIT = "deposit"  # Deposit via relayer


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Wallet and user references
    from_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=True)  # Can be null for external receives
    to_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=True)    # Can be null for external sends
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Transaction details
    from_address = Column(String(42), nullable=False)
    to_address = Column(String(42), nullable=False)
    amount = Column(Numeric(36, 18), nullable=False)
    gas_used = Column(Numeric(20, 0), nullable=True)
    gas_price = Column(Numeric(20, 0), nullable=True)
    gas_fee = Column(Numeric(36, 18), nullable=True)
    
    # Token and blockchain info
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    tx_hash = Column(String(66), nullable=True, unique=True, index=True)
    block_number = Column(Integer, nullable=True)
    block_hash = Column(String(66), nullable=True)
    
    # Transaction metadata
    transaction_type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    risk_score = Column(Numeric(3, 2), default=0.0, nullable=False)  # 0.00 to 1.00
    is_external = Column(Boolean, default=False, nullable=False)  # True for blockchain-synced transactions
    
    # Country tracking for international/domestic classification
    from_country = Column(String(2), nullable=True)  # ISO 3166-1 alpha-2 country code (e.g., 'US', 'IN')
    to_country = Column(String(2), nullable=True)  # ISO 3166-1 alpha-2 country code
    is_international = Column(Boolean, default=False, nullable=False)  # True if from_country != to_country
    
    # Fee breakdown
    platform_fee = Column(Numeric(36, 18), default=0, nullable=False)  # DARI platform fee
    total_fee = Column(Numeric(36, 18), default=0, nullable=False)  # Total fee (gas_fee + platform_fee)
    
    # Recipient information (for transaction details)
    recipient_name = Column(String(255), nullable=True)  # Receiver's name
    recipient_phone = Column(String(20), nullable=True)  # Receiver's phone (if sent via phone)
    transfer_method = Column(String(20), nullable=True)  # 'wallet', 'dari', or 'phone'
    
    # Additional information
    description = Column(Text, nullable=True)
    reference_id = Column(String(100), nullable=True)  # For internal reference
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    from_wallet = relationship("Wallet", foreign_keys=[from_wallet_id], back_populates="sent_transactions")
    to_wallet = relationship("Wallet", foreign_keys=[to_wallet_id], back_populates="received_transactions")
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="sent_transactions")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_transactions")
    token = relationship("Token", back_populates="transactions")
    notifications = relationship("Notification")

    def __repr__(self):
        return f"<Transaction(id={self.id}, from={self.from_address}, to={self.to_address}, amount={self.amount})>"
