from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
from app.models.kyc import KYCStatus, DocumentType


class KYCBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    nationality: str = Field(..., min_length=2, max_length=100)
    
    address_line_1: str = Field(..., min_length=5, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(..., min_length=2, max_length=100)
    
    document_type: DocumentType
    document_number: str = Field(..., min_length=5, max_length=100)
    
    @field_validator('date_of_birth')
    def validate_age(cls, v):
        try:
            birth_date = datetime.strptime(v, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                raise ValueError('Must be at least 18 years old')
            if age > 120:
                raise ValueError('Invalid birth date')
            return v
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError('Invalid date format. Use YYYY-MM-DD')
            raise e


class KYCCreate(KYCBase):
    pass


class KYCUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    date_of_birth: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    nationality: Optional[str] = Field(None, min_length=2, max_length=100)
    
    address_line_1: Optional[str] = Field(None, min_length=5, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    
    document_type: Optional[DocumentType] = None
    document_number: Optional[str] = Field(None, min_length=5, max_length=100)


class KYCResponse(KYCBase):
    id: int
    user_id: int
    status: KYCStatus
    document_front_url: Optional[str] = None  # Maps to document_file_path
    document_back_url: Optional[str] = None   # Not used in current model
    selfie_url: Optional[str] = None          # Maps to selfie_file_path
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class KYCApproval(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None
    
    @field_validator('rejection_reason')
    def validate_rejection_reason(cls, v, info):
        if not info.data.get('approved') and not v:
            raise ValueError('Rejection reason is required when rejecting KYC')
        if info.data.get('approved') and v:
            raise ValueError('Rejection reason should not be provided when approving KYC')
        return v


class KYCStats(BaseModel):
    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    under_review_requests: int


class KYCStatusResponse(BaseModel):
    status: KYCStatus
    message: str
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class KYCReview(BaseModel):
    rejection_reason: str = Field(..., min_length=10, max_length=500)


class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    file_size: int
    upload_time: datetime
