from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import re
from app.models.transaction import TransactionStatus, TransactionType


class TransactionBase(BaseModel):
    from_address: str
    to_address: str = Field(..., pattern=r'^0x[a-fA-F0-9]{40}$')
    amount: Decimal = Field(..., gt=0)
    token: str = Field(..., max_length=10)
    transaction_type: TransactionType
    fee: Optional[Decimal] = None
    gas_used: Optional[int] = None


class TransactionCreate(TransactionBase):
    user_id: Optional[int] = None  # Can be None for external transactions
    transaction_hash: Optional[str] = None
    token_id: Optional[int] = None  # Alternative to token symbol
    from_user_id: Optional[int] = None
    to_user_id: Optional[int] = None
    status: Optional[TransactionStatus] = None


class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    transaction_hash: Optional[str] = None
    fee: Optional[Decimal] = None
    gas_used: Optional[int] = None


class TransactionResponse(BaseModel):
    id: int
    from_address: Optional[str] = None  # Hidden by default for privacy
    to_address: Optional[str] = None    # Hidden by default for privacy
    amount: Decimal
    token: str
    transaction_hash: Optional[str] = None
    transaction_type: TransactionType
    status: TransactionStatus
    
    # Fee details
    gas_fee: Optional[Decimal] = None
    platform_fee: Optional[Decimal] = None
    total_fee: Optional[Decimal] = None
    gas_used: Optional[int] = None
    
    # Country and international tracking
    from_country: Optional[str] = None
    to_country: Optional[str] = None
    is_international: Optional[bool] = None
    
    # Recipient details
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    transfer_method: Optional[str] = None
    
    # Privacy-friendly display fields
    from_user_display: Optional[str] = None  # e.g., "abhi@dari" or "+91 98765 43210"
    to_user_display: Optional[str] = None    # e.g., "admin@dari" or "+1 234 567 8900"
    payment_method: Optional[str] = None      # e.g., "DARI Address", "Phone Number", "Wallet Address"
    
    # Direction indicator for user
    direction: Optional[str] = None  # "sent", "received", or "self"
    
    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total_count: int
    page: int
    per_page: int
    total_pages: int


class TransactionStatsResponse(BaseModel):
    total_transactions: int
    pending_transactions: int
    confirmed_transactions: int
    failed_transactions: int
    total_volume_usd: Decimal
    average_transaction_value_usd: Decimal


class TransactionReceiptResponse(BaseModel):
    transaction: TransactionResponse
    receipt_id: str
    generated_at: datetime
    pdf_url: Optional[str] = None


class TransactionFilter(BaseModel):
    status: Optional[TransactionStatus] = None
    transaction_type: Optional[TransactionType] = None
    token_symbol: Optional[str] = None


class TransactionSend(BaseModel):
    to_address: str = Field(..., min_length=1, description="Can be wallet address (0x...), DARI username (username@dari), or phone number (+1234567890)")
    amount: Decimal = Field(..., gt=0)
    token: str = Field(..., pattern=r'^(USDC|MATIC)$')  # Removed USDT
    pin: str = Field(..., pattern=r'^\d{4,6}$')
    transfer_method: Optional[str] = Field(default="auto", pattern=r'^(auto|wallet|dari|phone)$', description="Transfer method: auto (detect), wallet (0x address), dari (username@dari), or phone (phone number)")
    
    # Optional recipient details (for frontend to pass)
    recipient_name: Optional[str] = Field(None, max_length=255, description="Recipient's name (optional)")
    recipient_country: Optional[str] = Field(None, pattern=r'^[A-Z]{2}$', description="Recipient's country code (ISO 3166-1 alpha-2, e.g., 'US', 'IN')")
    sender_country: Optional[str] = Field(None, pattern=r'^[A-Z]{2}$', description="Sender's country code (ISO 3166-1 alpha-2)")
    
    @field_validator('to_address')
    def validate_to_address(cls, v):
        # Check if it's a DARI address (username@dari)
        if '@dari' in v.lower():
            username = v.lower().split('@dari')[0]
            if not re.match(r'^[a-zA-Z]+$', username):
                raise ValueError('DARI username must contain only alphabetic characters')
            if len(username) < 3 or len(username) > 50:
                raise ValueError('DARI username must be between 3 and 50 characters')
        # Check if it's a wallet address (0x...)
        elif v.startswith('0x') and len(v) == 42:
            try:
                int(v[2:], 16)
            except ValueError:
                raise ValueError('Invalid wallet address format')
        # Check if it's a phone number (starts with +)
        elif v.startswith('+'):
            if not re.match(r'^\+?1?\d{9,15}$', v):
                raise ValueError('Invalid phone number format. Use E.164 format (e.g., +1234567890)')
        else:
            raise ValueError('Address must be a wallet address (0x...), DARI address (username@dari), or phone number (+1234567890)')
        return v
    
    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > Decimal('1000000'):  # Max 1M tokens
            raise ValueError('Amount too large')
        return v


class TransactionQuery(BaseModel):
    """Query parameters for transaction listing"""
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class GasEstimationRequest(BaseModel):
    to_address: str = Field(..., min_length=1, description="Can be wallet address (0x...), DARI username (username@dari), or phone number (+1234567890)")
    amount: Decimal = Field(..., gt=0)
    token: str = Field(..., pattern=r'^(USDC|USDT|MATIC)$')
    
    @field_validator('to_address')
    def validate_to_address(cls, v):
        # Check if it's a DARI address (username@dari)
        if '@dari' in v.lower():
            username = v.lower().split('@dari')[0]
            if not re.match(r'^[a-zA-Z]+$', username):
                raise ValueError('DARI username must contain only alphabetic characters')
            if len(username) < 3 or len(username) > 50:
                raise ValueError('DARI username must be between 3 and 50 characters')
        # Check if it's a wallet address (0x...)
        elif v.startswith('0x') and len(v) == 42:
            try:
                int(v[2:], 16)
            except ValueError:
                raise ValueError('Invalid wallet address format')
        # Check if it's a phone number (starts with +)
        elif v.startswith('+'):
            if not re.match(r'^\+?1?\d{9,15}$', v):
                raise ValueError('Invalid phone number format. Use E.164 format (e.g., +1234567890)')
        else:
            raise ValueError('Address must be a wallet address (0x...), DARI address (username@dari), or phone number (+1234567890)')
        return v
    
    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > Decimal('1000000'):  # Max 1M tokens
            raise ValueError('Amount too large')
        return v


class GasEstimationResponse(BaseModel):
    gas_estimate: int
    gas_price: int
    gas_price_gwei: float
    gas_fee_wei: int
    gas_fee_matic: float
    total_cost_usd: float
    total_cost_user_currency: Optional[float] = None
    user_currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    token: str
    amount: Decimal
    to_address: str
    error: Optional[str] = None
    is_estimate: Optional[bool] = False
    
    class Config:
        from_attributes = True


class FeeEstimationRequest(BaseModel):
    """Request schema for fee estimation"""
    amount: Decimal = Field(..., gt=0)
    token: str = Field(..., pattern=r'^(USDC|MATIC)$')
    recipient_identifier: Optional[str] = Field(None, min_length=1, description="Recipient identifier: wallet address (0x...), DARI address (username@dari), or phone number (+1234567890)")
    sender_country: Optional[str] = Field(None, pattern=r'^[A-Z]{2}$', description="Sender's country code (ISO 3166-1 alpha-2)")
    recipient_country: Optional[str] = Field(None, pattern=r'^[A-Z]{2}$', description="Recipient's country code (ISO 3166-1 alpha-2)")
    
    @field_validator('recipient_identifier')
    def validate_recipient_identifier(cls, v):
        if v is None:
            return v
        
        # Check if it's a DARI address (username@dari)
        if '@dari' in v.lower():
            username = v.lower().split('@dari')[0]
            if not re.match(r'^[a-zA-Z]+$', username):
                raise ValueError('DARI username must contain only alphabetic characters')
            if len(username) < 3 or len(username) > 50:
                raise ValueError('DARI username must be between 3 and 50 characters')
        # Check if it's a wallet address (0x...)
        elif v.startswith('0x') and len(v) == 42:
            try:
                int(v[2:], 16)
            except ValueError:
                raise ValueError('Invalid wallet address format')
        # Check if it's a phone number (starts with +)
        elif v.startswith('+'):
            if not re.match(r'^\+?1?\d{9,15}$', v):
                raise ValueError('Invalid phone number format. Use E.164 format (e.g., +1234567890)')
        else:
            raise ValueError('Recipient must be a wallet address (0x...), DARI address (username@dari), or phone number (+1234567890)')
        
        return v
    
    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > Decimal('1000000'):  # Max 1M tokens
            raise ValueError('Amount too large')
        return v


class FeeEstimationResponse(BaseModel):
    """Response schema for fee estimation"""
    amount: Decimal
    token: str
    gas_fee: Decimal  # What user pays for gas (0 in gasless mode)
    platform_fee: Decimal
    total_fee: Decimal  # Total user pays
    gas_fee_usd: Decimal
    platform_fee_usd: Decimal
    total_fee_usd: Decimal
    is_international: bool
    from_country: Optional[str] = None
    to_country: Optional[str] = None
    estimated_gas: int
    gas_price_gwei: Decimal
    amount_to_send: Decimal
    total_cost: Decimal
    gasless_mode: Optional[bool] = True  # Whether DARI is covering gas fees
    dari_gas_subsidy: Optional[Decimal] = None  # How much DARI is subsidizing
    
    # Recipient information (if provided)
    recipient_identifier: Optional[str] = None  # The input identifier
    recipient_wallet_address: Optional[str] = None  # Resolved wallet address
    recipient_name: Optional[str] = None  # Recipient's name
    recipient_type: Optional[str] = None  # 'wallet', 'dari', or 'phone'
    
    class Config:
        from_attributes = True
