from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from decimal import Decimal
import asyncio

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.crud import token as token_crud
from app.schemas.token import TokenResponse, TokenPriceResponse
from app.services.blockchain_service import get_token_prices

router = APIRouter()


@router.get("/", response_model=List[TokenResponse])
async def get_supported_tokens(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[TokenResponse]:
    """Get supported tokens"""
    tokens = await token_crud.get_active_tokens(db)
    
    return [
        TokenResponse(
            id=token.id,
            name=token.name,
            symbol=token.symbol,
            contract_address=token.contract_address,
            decimals=token.decimals,
            logo_url=token.logo_url,
            is_active=token.is_active,
            created_at=token.created_at
        )
        for token in tokens
    ]


@router.get("/prices", response_model=List[TokenPriceResponse])
async def get_token_prices_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[TokenPriceResponse]:
    """Get current token prices"""
    try:
        # Get supported tokens
        tokens = await token_crud.get_active_tokens(db)
        
        # Get prices from blockchain service
        prices = await get_token_prices()
        
        # Combine token info with prices
        result = []
        for token in tokens:
            symbol_lower = token.symbol.lower()
            price_info = prices.get(symbol_lower, {})
            
            # Convert timestamp to ISO string if it's an integer
            last_updated = price_info.get('last_updated_at', '')
            if isinstance(last_updated, (int, float)):
                from datetime import datetime
                last_updated = datetime.fromtimestamp(last_updated).isoformat() + "Z"
            
            result.append(TokenPriceResponse(
                token_id=token.id,
                symbol=token.symbol,
                name=token.name,
                price_usd=Decimal(str(price_info.get('usd', 0))),
                price_change_24h=Decimal(str(price_info.get('usd_24h_change', 0))),
                market_cap=Decimal(str(price_info.get('usd_market_cap', 0))),
                last_updated=last_updated if last_updated else datetime.utcnow().isoformat() + "Z"
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch token prices: {str(e)}"
        )
