from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import re


class BankDetails(BaseModel):
    """Bank account details"""
    bank_name: str = Field(..., min_length=2, max_length=100)
    account_number: str = Field(..., min_length=9, max_length=18)
    ifsc_code: str = Field(..., min_length=11, max_length=11)
    account_holder_name: str = Field(..., min_length=2, max_length=100)

    @validator('account_number')
    def validate_account_number(cls, v):
        if not v.isdigit():
            raise ValueError('Account number must contain only digits')
        if len(v) < 9 or len(v) > 18:
            raise ValueError('Account number must be between 9 and 18 digits')
        return v

    @validator('ifsc_code')
    def validate_ifsc_code(cls, v):
        # IFSC format: XXXX0XXXXXX (4 letters, 1 zero, 6 alphanumeric)
        pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
        if not re.match(pattern, v.upper()):
            raise ValueError('Invalid IFSC code format. Must be like ABCD0123456')
        return v.upper()


class UPIDetails(BaseModel):
    """UPI payment details"""
    upi_name: str = Field(..., min_length=2, max_length=100, description="UPI provider name (e.g., PayTM, Google Pay)")
    upi_id: str = Field(..., min_length=5, max_length=100, description="UPI ID (e.g., user@paytm)")

    @validator('upi_id')
    def validate_upi_id(cls, v):
        # UPI ID format: username@provider
        pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+$'
        if not re.match(pattern, v):
            raise ValueError('Invalid UPI ID format. Must be like username@provider')
        return v.lower()


class PaymentMethodBase(BaseModel):
    """Base payment method schema"""
    type: str = Field(..., description="Payment method type: 'bank' or 'upi'")
    name: str = Field(..., min_length=2, max_length=100, description="Display name for the payment method")
    details: Dict[str, Any] = Field(..., description="Payment method details (bank or UPI)")

    @validator('type')
    def validate_type(cls, v):
        if v not in ['bank', 'upi']:
            raise ValueError('Type must be either "bank" or "upi"')
        return v


class PaymentMethodCreate(PaymentMethodBase):
    """Schema for creating a new payment method"""
    
    @validator('details')
    def validate_details(cls, v, values):
        payment_type = values.get('type')
        
        if payment_type == 'bank':
            try:
                BankDetails(**v)
            except Exception as e:
                raise ValueError(f'Invalid bank details: {str(e)}')
        elif payment_type == 'upi':
            try:
                UPIDetails(**v)
            except Exception as e:
                raise ValueError(f'Invalid UPI details: {str(e)}')
        
        return v


class PaymentMethodUpdate(BaseModel):
    """Schema for updating a payment method"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    details: Optional[Dict[str, Any]] = None

    @validator('details')
    def validate_details(cls, v):
        if v is not None:
            # Basic validation - type should be determined from existing record
            if 'bank_name' in v:
                try:
                    BankDetails(**v)
                except Exception as e:
                    raise ValueError(f'Invalid bank details: {str(e)}')
            elif 'upi_id' in v:
                try:
                    UPIDetails(**v)
                except Exception as e:
                    raise ValueError(f'Invalid UPI details: {str(e)}')
        return v


class PaymentMethodResponse(BaseModel):
    """Schema for payment method response"""
    id: int
    user_id: int
    type: str
    name: str
    details: Dict[str, Any]
    is_default: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentMethodListResponse(BaseModel):
    """Schema for list of payment methods"""
    payment_methods: list[PaymentMethodResponse]
    total: int


class PaymentMethodSetDefaultRequest(BaseModel):
    """Schema for setting default payment method"""
    pass  # No body needed, ID is in path
