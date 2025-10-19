from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.crud import wallet as wallet_crud
from app.services.blockchain_service import USDC_CONTRACT, POLYGON_CHAIN_ID

router = APIRouter()


@router.get("/info")
async def get_deposit_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get deposit information for user's wallet
    
    Returns:
    - User's wallet address (where to deposit tokens)
    - USDC contract address
    - Network details (Polygon)
    - Chain ID
    
    **Usage:**
    1. Get deposit info from this endpoint
    2. Send USDC/MATIC directly to user's wallet address
    3. User can track balance via /api/v1/wallets/balance
    """
    
    # Get user's wallet
    user_wallet = await wallet_crud.get_wallet_by_user_id(db, current_user.id)
    if not user_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found. Please create a wallet first."
        )
    
    # Get network info
    network_name = "Polygon Amoy Testnet" if settings.USE_TESTNET else "Polygon Mainnet"
    explorer_url = "https://amoy.polygonscan.com" if settings.USE_TESTNET else "https://polygonscan.com"
    
    return {
        "wallet_address": user_wallet.address,
        "network": network_name,
        "chain_id": POLYGON_CHAIN_ID,
        "explorer_url": f"{explorer_url}/address/{user_wallet.address}",
        "tokens": [
            {
                "symbol": "USDC",
                "name": "USD Coin",
                "contract_address": USDC_CONTRACT,
                "decimals": 6,
                "type": "ERC-20",
                "deposit_instructions": f"Send USDC to {user_wallet.address} on {network_name}"
            },
            {
                "symbol": "MATIC",
                "name": "Polygon",
                "is_native": True,
                "decimals": 18,
                "type": "Native",
                "deposit_instructions": f"Send MATIC to {user_wallet.address} on {network_name}"
            }
        ],
        "qr_data": {
            "address": user_wallet.address,
            "network": network_name,
            "chain_id": POLYGON_CHAIN_ID
        },
        "instructions": [
            f"1. Send USDC or MATIC to: {user_wallet.address}",
            f"2. Network: {network_name}",
            "3. Check balance at: GET /api/v1/wallets/balance",
            f"4. View on explorer: {explorer_url}/address/{user_wallet.address}"
        ]
    }
