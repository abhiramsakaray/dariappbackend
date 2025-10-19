from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    address = Column(String(42), nullable=False, unique=True, index=True)  # Ethereum address format
    encrypted_private_key = Column(Text, nullable=False)
    chain = Column(String(20), default="polygon", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    token_balances = relationship("TokenBalance", back_populates="wallet")
    sent_transactions = relationship("Transaction", foreign_keys="Transaction.from_wallet_id", back_populates="from_wallet")
    received_transactions = relationship("Transaction", foreign_keys="Transaction.to_wallet_id", back_populates="to_wallet")

    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, address='{self.address}')>"
