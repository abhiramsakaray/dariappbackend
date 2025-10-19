from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class WalletBase(BaseModel):
    address: str = Field(..., pattern=r'^0x[a-fA-F0-9]{40}$')


class WalletCreate(BaseModel):
    address: str = Field(..., pattern=r'^0x[a-fA-F0-9]{40}$')
    encrypted_private_key: str


class WalletUpdate(BaseModel):
    chain: Optional[str] = None


class WalletResponse(BaseModel):
    id: int
    address: str
    chain: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenBalanceResponse(BaseModel):
    token_id: int
    token_symbol: str
    token_name: str
    balance: Decimal
    balance_formatted: str
    fiat_value: Optional[Decimal] = None
    fiat_currency: str
    
    class Config:
        from_attributes = True


class WalletBalanceResponse(BaseModel):
    wallet: WalletResponse
    balances: list[TokenBalanceResponse]
    total_fiat_value: Decimal
    fiat_currency: str
    last_updated: datetime


class WalletStatsResponse(BaseModel):
    total_wallets: int
    active_wallets: int
    total_value_usd: Decimal
    average_balance_usd: Decimal


class QRCodeResponse(BaseModel):
    qr_code_data: str
    qr_code_image: str  # Base64 encoded image
    address: str
