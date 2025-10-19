from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from web3 import Web3
from eth_account import Account

from app.core.database import get_db
from app.core.security import get_current_active_user, encrypt_data
from app.models.user import User
from app.models.kyc import KYCStatus
from app.crud import kyc as kyc_crud, wallet as wallet_crud
from app.schemas.wallet import WalletCreate, WalletResponse
from app.services.blockchain_service import get_balances
from app.services.fiat_service import get_fiat_conversion_rate

router = APIRouter()


@router.post("/create", response_model=WalletResponse)
async def create_wallet(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> WalletResponse:
    """Create a new wallet for the user (only after KYC approval)"""
    # Check if user already has a wallet
    existing_wallet = await wallet_crud.get_wallet_by_user_id(db, current_user.id)
    if existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a wallet"
        )
    
    # Check KYC status
    kyc_request = await kyc_crud.get_kyc_by_user_id(db, current_user.id)
    if not kyc_request or kyc_request.status != KYCStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC must be approved before wallet creation"
        )
    
    # Generate new Ethereum account
    account = Account.create()
    private_key = account.key.hex()
    address = account.address
    
    # Encrypt private key
    encrypted_private_key = encrypt_data(private_key)
    
    # Create wallet in database
    wallet_data = WalletCreate(
        address=address,
        encrypted_private_key=encrypted_private_key
    )
    
    db_wallet = await wallet_crud.create_wallet(db, wallet_data, current_user.id)
    
    return WalletResponse(
        id=db_wallet.id,
        address=db_wallet.address,
        chain=db_wallet.chain,
        created_at=db_wallet.created_at
    )


@router.get("/balance")
async def get_wallet_balance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get wallet balance"""
    # Get user's wallet
    wallet = await wallet_crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found. Please create a wallet first."
        )
    
    # Get balances from blockchain
    try:
        balances = await get_balances(wallet.address)
        user_currency = current_user.default_currency or "USD"
        # Get USD to user currency conversion rate
        async def get_rate():
            # Use USD as base for conversion
            url = f"https://api.coingecko.com/api/v3/simple/price?ids=usd&vs_currencies={user_currency.lower()}"
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data.get("usd", {}).get(user_currency.lower(), 1.0))
            return 1.0
        rate = await get_rate()
        total_fiat = balances.get("total_usd", 0) * rate
        # Only USDC and MATIC are supported
        return {
            "address": wallet.address,
            "balances": {
                "USDC": balances.get("USDC", 0),
                "MATIC": balances.get("MATIC", 0),
            },
            "total": total_fiat,
            "currency": user_currency
        }
    except Exception as e:
        # Fallback to zero balances if blockchain service fails
        return {
            "address": wallet.address,
            "balances": {
                "USDC": 0,
                "MATIC": 0,
            },
            "total": 0,
            "currency": current_user.default_currency or "USD",
            "error": "Unable to fetch live balances"
        }


@router.get("/", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> WalletResponse:
    """Get user wallet"""
    wallet = await wallet_crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found. Please create a wallet first."
        )
    
    return WalletResponse(
        id=wallet.id,
        address=wallet.address,
        chain=wallet.chain,
        created_at=wallet.created_at
    )