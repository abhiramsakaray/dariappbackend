from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class FileType(str, enum.Enum):
    KYC_DOCUMENT = "kyc_document"
    KYC_SELFIE = "kyc_selfie"


class UserFile(Base):
    __tablename__ = "user_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<UserFile(id={self.id}, user_id={self.user_id}, type='{self.file_type}', file='{self.filename}')>"
