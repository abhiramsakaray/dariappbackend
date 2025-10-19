from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class TokenBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., min_length=1, max_length=10)
    contract_address: str = Field(..., pattern=r'^0x[a-fA-F0-9]{40}$')
    decimals: int = Field(default=18, ge=0, le=18)
    coingecko_id: Optional[str] = Field(None, max_length=100)


class TokenCreate(TokenBase):
    pass


class TokenUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    is_active: Optional[bool] = None
    coingecko_id: Optional[str] = Field(None, max_length=100)


class TokenResponse(TokenBase):
    id: int
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenPriceResponse(BaseModel):
    token_id: int
    symbol: str
    name: str
    price_usd: Decimal
    price_change_24h: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    last_updated: str


class FiatCurrencyBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=3)
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., min_length=1, max_length=10)


class FiatCurrencyCreate(FiatCurrencyBase):
    pass


class FiatCurrencyResponse(FiatCurrencyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CurrencyConversionResponse(BaseModel):
    amount: Decimal
    from_currency: str
    to_currency: str
    exchange_rate: Decimal
    converted_amount: Decimal
    timestamp: datetime


class SupportedTokensResponse(BaseModel):
    tokens: List[TokenResponse]
    total_count: int
