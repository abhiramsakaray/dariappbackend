from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AddressResolver(Base):
    __tablename__ = "address_resolvers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    username = Column(String(50), nullable=False, unique=True, index=True)  # Only the part before @
    full_address = Column(String(100), nullable=False, unique=True, index=True)  # username@dari
    wallet_address = Column(String(42), nullable=False, index=True)  # Maps to actual wallet address
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="address_resolver")

    def __repr__(self):
        return f"<AddressResolver(id={self.id}, full_address='{self.full_address}', wallet_address='{self.wallet_address}')>"
