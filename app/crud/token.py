from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from app.models.token import Token, TokenBalance, FiatCurrency
from app.schemas.token import TokenCreate, TokenUpdate


async def get_token_by_id(db: AsyncSession, token_id: int) -> Optional[Token]:
    """Get token by ID"""
    result = await db.execute(select(Token).where(Token.id == token_id))
    return result.scalar_one_or_none()


async def get_token_by_symbol(db: AsyncSession, symbol: str) -> Optional[Token]:
    """Get token by symbol"""
    result = await db.execute(select(Token).where(Token.symbol == symbol.upper()))
    return result.scalar_one_or_none()


async def get_token_by_contract(db: AsyncSession, contract_address: str) -> Optional[Token]:
    """Get token by contract address"""
    result = await db.execute(select(Token).where(Token.contract_address == contract_address.lower()))
    return result.scalar_one_or_none()


async def create_token(db: AsyncSession, token: TokenCreate) -> Token:
    """Create new token"""
    db_token = Token(
        name=token.name,
        symbol=token.symbol.upper(),
        contract_address=token.contract_address.lower(),
        decimals=token.decimals,
        coingecko_id=token.coingecko_id,
        is_active=True,
        current_price_usd=Decimal('0'),
    )
    
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def update_token(db: AsyncSession, token_id: int, token_update: TokenUpdate) -> Optional[Token]:
    """Update token"""
    db_token = await get_token_by_id(db, token_id)
    if not db_token:
        return None
    
    update_data = token_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "symbol" and value:
            value = value.upper()
        setattr(db_token, field, value)
    
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def update_token_price(db: AsyncSession, token_id: int, price_usd: Decimal) -> bool:
    """Update token price"""
    db_token = await get_token_by_id(db, token_id)
    if not db_token:
        return False
    
    db_token.current_price_usd = price_usd
    db_token.last_price_update = datetime.utcnow()
    await db.commit()
    return True


async def get_active_tokens(db: AsyncSession) -> List[Token]:
    """Get all active tokens"""
    result = await db.execute(
        select(Token)
        .where(Token.is_active == True)
        .order_by(Token.symbol)
    )
    return list(result.scalars().all())


async def get_tokens_with_coingecko_id(db: AsyncSession) -> List[Token]:
    """Get all tokens that have coingecko_id for price updates"""
    result = await db.execute(
        select(Token)
        .where(
            and_(
                Token.is_active == True,
                Token.coingecko_id.isnot(None),
                Token.coingecko_id != ""
            )
        )
    )
    return list(result.scalars().all())


async def get_wallet_token_balance(
    db: AsyncSession, 
    wallet_id: int, 
    token_id: int
) -> Optional[TokenBalance]:
    """Get specific token balance for wallet"""
    result = await db.execute(
        select(TokenBalance)
        .where(
            and_(
                TokenBalance.wallet_id == wallet_id,
                TokenBalance.token_id == token_id
            )
        )
    )
    return result.scalar_one_or_none()


async def update_token_balance(
    db: AsyncSession,
    wallet_id: int,
    token_id: int,
    balance: Decimal
) -> TokenBalance:
    """Update or create token balance"""
    db_balance = await get_wallet_token_balance(db, wallet_id, token_id)
    
    if db_balance:
        db_balance.balance = balance
    else:
        db_balance = TokenBalance(
            wallet_id=wallet_id,
            token_id=token_id,
            balance=balance
        )
        db.add(db_balance)
    
    await db.commit()
    await db.refresh(db_balance)
    return db_balance


async def get_wallet_balances(db: AsyncSession, wallet_id: int) -> List[TokenBalance]:
    """Get all token balances for a wallet"""
    result = await db.execute(
        select(TokenBalance)
        .where(TokenBalance.wallet_id == wallet_id)
        .options(selectinload(TokenBalance.token))
    )
    return list(result.scalars().all())


# Fiat Currency CRUD
async def get_fiat_currency_by_code(db: AsyncSession, code: str) -> Optional[FiatCurrency]:
    """Get fiat currency by code"""
    result = await db.execute(select(FiatCurrency).where(FiatCurrency.code == code.upper()))
    return result.scalar_one_or_none()


async def get_active_fiat_currencies(db: AsyncSession) -> List[FiatCurrency]:
    """Get all active fiat currencies"""
    result = await db.execute(
        select(FiatCurrency)
        .where(FiatCurrency.is_active == True)
        .order_by(FiatCurrency.code)
    )
    return list(result.scalars().all())


async def seed_default_data(db: AsyncSession) -> None:
    """Seed default tokens and fiat currencies"""
    try:
        # Seed USDC and USDT tokens
        from app.core.config import settings
        
        # Check if tokens already exist
        usdc = await get_token_by_symbol(db, "USDC")
        if not usdc:
            usdc_create = TokenCreate(
                name="USD Coin",
                symbol="USDC",
                contract_address=settings.USDC_TESTNET_CONTRACT_ADDRESS if settings.USE_TESTNET else settings.USDC_CONTRACT_ADDRESS,
                decimals=6,
                coingecko_id="usd-coin"
            )
            await create_token(db, usdc_create)
        
        usdt = await get_token_by_symbol(db, "USDT")
        if not usdt:
            usdt_create = TokenCreate(
                name="Tether USD",
                symbol="USDT",
                contract_address=settings.USDT_TESTNET_CONTRACT_ADDRESS if settings.USE_TESTNET else settings.USDT_CONTRACT_ADDRESS,
                decimals=6,
                coingecko_id="tether"
            )
            await create_token(db, usdt_create)
        
        # Seed fiat currencies
        fiat_currencies = [
            {"code": "USD", "name": "US Dollar", "symbol": "$"},
            {"code": "EUR", "name": "Euro", "symbol": "€"},
            {"code": "GBP", "name": "British Pound", "symbol": "£"},
            {"code": "INR", "name": "Indian Rupee", "symbol": "₹"},
            {"code": "JPY", "name": "Japanese Yen", "symbol": "¥"},
        ]
        
        for fiat_data in fiat_currencies:
            existing = await get_fiat_currency_by_code(db, fiat_data["code"])
            if not existing:
                fiat = FiatCurrency(**fiat_data, is_active=True)
                db.add(fiat)
        
        await db.commit()
        print("Default tokens and fiat currencies seeded successfully")
        
    except Exception as e:
        print(f"Error seeding default data: {e}")
        await db.rollback()
