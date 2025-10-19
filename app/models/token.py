from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    symbol = Column(String(10), nullable=False, unique=True, index=True)
    contract_address = Column(String(42), nullable=False, unique=True, index=True)
    decimals = Column(Integer, default=18, nullable=False)
    logo_url = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Price information
    current_price_usd = Column(Numeric(20, 8), default=0, nullable=False)
    last_price_update = Column(DateTime(timezone=True), nullable=True)
    
    # Supported fiat currencies for conversion
    coingecko_id = Column(String(100), nullable=True)  # For price fetching
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    token_balances = relationship("TokenBalance", back_populates="token")
    transactions = relationship("Transaction", back_populates="token")

    def __repr__(self):
        return f"<Token(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"


class TokenBalance(Base):
    __tablename__ = "token_balances"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    
    balance = Column(Numeric(36, 18), default=0, nullable=False)  # Support very large numbers
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    wallet = relationship("Wallet", back_populates="token_balances")
    token = relationship("Token", back_populates="token_balances")

    def __repr__(self):
        return f"<TokenBalance(wallet_id={self.wallet_id}, token_id={self.token_id}, balance={self.balance})>"


class FiatCurrency(Base):
    __tablename__ = "fiat_currencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), nullable=False, unique=True, index=True)  # USD, EUR, INR, etc.
    name = Column(String(100), nullable=False)
    symbol = Column(String(10), nullable=False)  # $, €, ₹, etc.
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<FiatCurrency(code='{self.code}', name='{self.name}')>"
