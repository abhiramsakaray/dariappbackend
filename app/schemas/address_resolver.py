from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class AddressResolverBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z]+$')

    @field_validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z]+$', v):
            raise ValueError('Username must contain only alphabetic characters')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be at most 50 characters long')
        return v.lower()  # Convert to lowercase for consistency


class AddressResolverCreate(AddressResolverBase):
    pass


class AddressResolverUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r'^[a-zA-Z]+$')

    @field_validator('username')
    def validate_username(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z]+$', v):
                raise ValueError('Username must contain only alphabetic characters')
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if len(v) > 50:
                raise ValueError('Username must be at most 50 characters long')
            return v.lower()  # Convert to lowercase for consistency
        return v


class AddressResolverResponse(BaseModel):
    id: int
    username: str
    full_address: str
    wallet_address: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    full_name: Optional[str] = None  # From KYC data

    class Config:
        from_attributes = True


class AddressResolveRequest(BaseModel):
    address: str = Field(..., min_length=1)

    @field_validator('address')
    def validate_address(cls, v):
        # Check if it's a DARI address (username@dari) or a wallet address (0x...)
        if '@dari' in v:
            username = v.split('@dari')[0]
            if not re.match(r'^[a-zA-Z]+$', username):
                raise ValueError('DARI username must contain only alphabetic characters')
        elif v.startswith('0x') and len(v) == 42:
            # It's a wallet address, which is also valid
            pass
        else:
            raise ValueError('Address must be either a DARI address (username@dari) or a valid wallet address (0x...)')
        return v


class AddressResolveResponse(BaseModel):
    input_address: str
    wallet_address: str
    dari_address: Optional[str] = None
    is_dari_address: bool
    full_name: Optional[str] = None  # From KYC data
