from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models.user_file import DocumentType


class UserFileBase(BaseModel):
    file_name: str
    original_name: str
    file_path: str
    file_size: int
    content_type: str
    document_type: DocumentType


class UserFileCreate(UserFileBase):
    pass


class UserFileResponse(UserFileBase):
    id: int
    user_id: int
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    message: str
    file_id: int
    filename: str
    document_type: DocumentType
    file_size: int


class KYCFilesStatus(BaseModel):
    has_document: bool
    has_selfie: bool
    all_required_files: bool
    document_count: int
    selfie_count: int
    documents: list[UserFileResponse] = []
    selfies: list[UserFileResponse] = []
