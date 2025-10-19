from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_active_user, decrypt_data, verify_pin
from app.models.user import User
from app.models.transaction import TransactionType, TransactionStatus
from app.crud import wallet as wallet_crud, transaction as transaction_crud, address_resolver as address_resolver_crud, user as user_crud
from app.schemas.transaction import (
    TransactionCreate, 
    TransactionResponse, 
    TransactionSend,
    GasEstimationRequest,
    GasEstimationResponse,
    FeeEstimationRequest,
    FeeEstimationResponse
)
from app.services.blockchain_service import (
    send_token_transaction,
    send_matic_transaction,
    send_token_transaction_with_relayer_fallback,
    estimate_token_transfer_gas,
    estimate_matic_transfer_gas,
    USDC_CONTRACT,
    USDT_CONTRACT
)
from app.services.currency_service import currency_service
from app.services.notification_service import notification_service
from app.services.notification_helpers import notify_payment_received, notify_payment_sent
from app.services.fee_service import fee_service
from app.crud import token as token_crud

router = APIRouter()


@router.post("/estimate-gas", response_model=GasEstimationResponse)
async def estimate_gas_fee(
    gas_request: GasEstimationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> GasEstimationResponse:
    """Estimate gas fee for a transaction before sending
    
    Supports:
    - Wallet address (0x...)
    - DARI address (username@dari)
    - Phone number (+1234567890)
    """
    
    # Get user's wallet
    wallet = await wallet_crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Resolve recipient address
    recipient_wallet = gas_request.to_address
    recipient_id = gas_request.to_address
    
    # Resolve DARI address
    if '@dari' in recipient_id.lower():
        resolved = await address_resolver_crud.resolve_address(db, recipient_id)
        if not resolved:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DARI address not found or inactive"
            )
        recipient_wallet = resolved["wallet_address"]
    
    # Resolve phone number
    elif recipient_id.startswith('+'):
        recipient_user = await user_crud.get_user_by_phone(db, recipient_id)
        if not recipient_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user found with this phone number"
            )
        
        # Get recipient's wallet
        recipient_wallet_obj = await wallet_crud.get_wallet_by_user_id(db, recipient_user.id)
        if not recipient_wallet_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient has no wallet"
            )
        recipient_wallet = recipient_wallet_obj.address
    
    # Direct wallet address - use as is
    elif recipient_id.startswith('0x') and len(recipient_id) == 42:
        recipient_wallet = recipient_id
    
    try:
        # Determine token and contract address
        token_symbol = gas_request.token.upper()
        
        if token_symbol == "MATIC":
            # Estimate gas for MATIC transfer
            gas_info = await estimate_matic_transfer_gas(
                from_address=wallet.address,
                to_address=recipient_wallet,
                amount=float(gas_request.amount)
            )
        elif token_symbol in ["USDC", "USDT"]:
            # Get contract address
            if token_symbol == "USDC":
                contract_address = USDC_CONTRACT
                decimals = 6
            else:  # USDT
                contract_address = USDT_CONTRACT
                decimals = 6
            
            # Estimate gas for token transfer
            gas_info = await estimate_token_transfer_gas(
                from_address=wallet.address,
                to_address=recipient_wallet,
                amount=float(gas_request.amount),
                token_contract=contract_address,
                decimals=decimals
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported token: {token_symbol}"
            )
        
        # Get user's default currency and convert USD amount
        user_currency = current_user.default_currency
        total_cost_user_currency = None
        exchange_rate = None
        
        if user_currency and user_currency != "USD":
            try:
                converted_amount = await currency_service.convert_amount(
                    Decimal(str(gas_info["total_cost_usd"])),
                    "USD",
                    user_currency
                )
                if converted_amount is not None:
                    total_cost_user_currency = float(converted_amount)
                    rate = await currency_service.get_exchange_rate("USD", user_currency)
                    if rate:
                        exchange_rate = float(rate)
            except Exception as e:
                # Log error but don't fail the estimation
                print(f"Currency conversion error: {e}")
        
        return GasEstimationResponse(
            gas_estimate=gas_info["gas_estimate"],
            gas_price=gas_info["gas_price"],
            gas_price_gwei=gas_info["gas_price_gwei"],
            gas_fee_wei=gas_info["gas_fee_wei"],
            gas_fee_matic=gas_info["gas_fee_matic"],
            total_cost_usd=gas_info["total_cost_usd"],
            total_cost_user_currency=total_cost_user_currency,
            user_currency=user_currency,
            exchange_rate=exchange_rate,
            token=token_symbol,
            amount=gas_request.amount,
            to_address=recipient_wallet,
            error=gas_info.get("error"),
            is_estimate=gas_info.get("is_estimate", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate gas fee: {str(e)}"
        )


@router.post("/estimate-fee", response_model=FeeEstimationResponse)
async def estimate_transaction_fee(
    fee_request: FeeEstimationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> FeeEstimationResponse:
    """Estimate complete transaction fee including platform and gas fees
    
    Supports:
    - Amount only (no recipient)
    - DARI address (username@dari)
    - Phone number (+1234567890)
    - Wallet address (0x...)
    """
    
    try:
        # Get token price
        token_obj = await token_crud.get_token_by_symbol(db, fee_request.token)
        if not token_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token {fee_request.token} not found"
            )
        
        token_price_usd = Decimal(str(token_obj.current_price_usd)) if token_obj.current_price_usd else Decimal("1.0")
        
        # Resolve recipient information if provided
        recipient_wallet = None
        recipient_name = None
        recipient_type = None
        recipient_user = None
        recipient_country_code = None
        
        if fee_request.recipient_identifier:
            recipient_id = fee_request.recipient_identifier
            
            # Resolve DARI address
            if '@dari' in recipient_id.lower():
                resolved = await address_resolver_crud.resolve_address(db, recipient_id)
                if not resolved:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="DARI address not found or inactive"
                    )
                recipient_wallet = resolved["wallet_address"]
                recipient_type = "dari"
                
                # Get recipient user info
                recipient_user = await address_resolver_crud.get_user_by_wallet_address(db, recipient_wallet)
                if recipient_user:
                    recipient_name = recipient_user.full_name
                    # Try to get country from KYC
                    if recipient_user.kyc_request and recipient_user.kyc_request.country:
                        recipient_country_code = recipient_user.kyc_request.country
            
            # Resolve phone number
            elif recipient_id.startswith('+'):
                recipient_user = await user_crud.get_user_by_phone(db, recipient_id)
                if not recipient_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No user found with this phone number"
                    )
                
                # Get recipient's wallet
                recipient_wallet_obj = await wallet_crud.get_wallet_by_user_id(db, recipient_user.id)
                if recipient_wallet_obj:
                    recipient_wallet = recipient_wallet_obj.address
                
                recipient_type = "phone"
                recipient_name = recipient_user.full_name
                
                # Try to get country from KYC
                if recipient_user.kyc_request and recipient_user.kyc_request.country:
                    recipient_country_code = recipient_user.kyc_request.country
            
            # Direct wallet address
            elif recipient_id.startswith('0x') and len(recipient_id) == 42:
                recipient_wallet = recipient_id
                recipient_type = "wallet"
                
                # Try to find user info
                recipient_user = await address_resolver_crud.get_user_by_wallet_address(db, recipient_wallet)
                if recipient_user:
                    recipient_name = recipient_user.full_name
                    # Try to get country from KYC
                    if recipient_user.kyc_request and recipient_user.kyc_request.country:
                        recipient_country_code = recipient_user.kyc_request.country
        
        # Get country codes
        sender_country = fee_request.sender_country
        if not sender_country and current_user.kyc_request and current_user.kyc_request.country:
            sender_country = current_user.kyc_request.country
            
        recipient_country = fee_request.recipient_country or recipient_country_code
        
        # Determine if international
        is_international = fee_service.is_international_transaction(sender_country, recipient_country)
        
        # Calculate fees
        fee_breakdown = fee_service.calculate_total_fee(
            amount=fee_request.amount,
            token=fee_request.token,
            is_international=is_international,
            token_price_usd=token_price_usd
        )
        
        return FeeEstimationResponse(
            amount=fee_request.amount,
            token=fee_request.token,
            gas_fee=fee_breakdown["gas_fee"],  # 0 in gasless mode
            platform_fee=fee_breakdown["platform_fee"],
            total_fee=fee_breakdown["total_fee"],
            gas_fee_usd=fee_breakdown["fee_breakdown"]["user_gas_fee_usd"],  # What user pays
            platform_fee_usd=fee_breakdown["fee_breakdown"]["platform_fee_usd"],
            total_fee_usd=fee_breakdown["fee_breakdown"]["total_fee_usd"],
            is_international=is_international,
            from_country=sender_country,
            to_country=recipient_country,
            estimated_gas=int(fee_breakdown["estimated_gas"]),
            gas_price_gwei=fee_breakdown["gas_price_gwei"],
            amount_to_send=fee_request.amount,
            total_cost=fee_request.amount + fee_breakdown["total_fee"],
            gasless_mode=fee_breakdown.get("gasless_mode", True),
            dari_gas_subsidy=fee_breakdown["fee_breakdown"].get("dari_subsidy_usd", Decimal("0")),
            # Recipient information
            recipient_identifier=fee_request.recipient_identifier,
            recipient_wallet_address=recipient_wallet,
            recipient_name=recipient_name,
            recipient_type=recipient_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate fee: {str(e)}"
        )


@router.post("/send", response_model=TransactionResponse)
async def send_transaction(
    transaction_data: TransactionSend,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionResponse:
    """Send transaction"""
    # Check if user has set up a PIN
    if not current_user.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN is required for transactions. Please set up your PIN first using the /auth/set-pin endpoint."
        )
    
    # Verify PIN
    if not verify_pin(transaction_data.pin, current_user.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PIN"
        )
    
    # Get user's wallet
    wallet = await wallet_crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Resolve destination address (DARI address, phone number, or wallet address)
    destination_wallet_address = transaction_data.to_address
    transfer_method_used = transaction_data.transfer_method or "auto"
    recipient_user_obj = None
    recipient_name = transaction_data.recipient_name
    recipient_phone = None
    
    # Resolve DARI address to wallet address
    if '@dari' in transaction_data.to_address.lower():
        resolved = await address_resolver_crud.resolve_address(db, transaction_data.to_address)
        if not resolved:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DARI address not found or inactive"
            )
        destination_wallet_address = resolved["wallet_address"]
        transfer_method_used = "dari"
        
        # Get recipient user info
        recipient_user_obj = await address_resolver_crud.get_user_by_wallet_address(db, destination_wallet_address)
        if recipient_user_obj:
            recipient_name = recipient_name or recipient_user_obj.full_name
            recipient_phone = recipient_user_obj.phone
        
        # Prevent self-transactions using DARI address
        if destination_wallet_address.lower() == wallet.address.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send transaction to your own wallet"
            )
    
    # Resolve phone number to wallet address
    elif transaction_data.to_address.startswith('+'):
        # Find user by phone number
        recipient_user = await user_crud.get_user_by_phone(db, transaction_data.to_address)
        if not recipient_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user found with this phone number"
            )
        
        # Get recipient's wallet
        recipient_wallet = await wallet_crud.get_wallet_by_user_id(db, recipient_user.id)
        if not recipient_wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient does not have a wallet"
            )
        
        destination_wallet_address = recipient_wallet.address
        transfer_method_used = "phone"
        recipient_user_obj = recipient_user
        recipient_name = recipient_name or recipient_user.full_name
        recipient_phone = recipient_user.phone
        
        # Prevent self-transactions using phone number
        if recipient_user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send transaction to your own wallet"
            )
    
    # Direct wallet address
    elif destination_wallet_address.lower() == wallet.address.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send transaction to your own wallet"
        )
    else:
        transfer_method_used = "wallet"
        # Try to find recipient user info for wallet address
        recipient_user_obj = await address_resolver_crud.get_user_by_wallet_address(db, destination_wallet_address)
        if recipient_user_obj:
            recipient_name = recipient_name or recipient_user_obj.full_name
            recipient_phone = recipient_user_obj.phone
    
    # Get country codes and determine if international
    sender_country = transaction_data.sender_country or current_user.country_code
    recipient_country = transaction_data.recipient_country
    
    # Try to get recipient country from their profile if not provided
    if not recipient_country and recipient_user_obj:
        recipient_country = recipient_user_obj.country_code
    
    # Determine if international transaction
    is_international = fee_service.is_international_transaction(sender_country, recipient_country)
    
    # Get token price for fee calculation
    token_obj = await token_crud.get_token_by_symbol(db, transaction_data.token)
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token {transaction_data.token} not found"
        )
    
    token_price_usd = Decimal(str(token_obj.current_price_usd)) if token_obj.current_price_usd else Decimal("1.0")
    
    # Calculate fees
    fee_breakdown = fee_service.calculate_total_fee(
        amount=Decimal(str(transaction_data.amount)),
        token=transaction_data.token,
        is_international=is_international,
        token_price_usd=token_price_usd
    )
    
    # Decrypt private key
    try:
        private_key = decrypt_data(wallet.encrypted_private_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to access wallet"
        )
    
    # Create transaction record
    try:
        transaction_create = TransactionCreate(
            user_id=current_user.id,
            from_address=wallet.address,
            to_address=destination_wallet_address,  # Use resolved wallet address
            amount=transaction_data.amount,
            token=transaction_data.token,
            transaction_type=TransactionType.SEND,
            fee=fee_breakdown["gas_fee"],  # Gas fee only for blockchain
            gas_used=int(fee_breakdown["estimated_gas"])
        )
        
        db_transaction = await transaction_crud.create_transaction(db, transaction_create)
        
        # Update transaction with additional fee and country information
        db_transaction.platform_fee = fee_breakdown["platform_fee"]
        db_transaction.total_fee = fee_breakdown["total_fee"]
        db_transaction.from_country = sender_country
        db_transaction.to_country = recipient_country
        db_transaction.is_international = is_international
        db_transaction.recipient_name = recipient_name
        db_transaction.recipient_phone = recipient_phone
        db_transaction.transfer_method = transfer_method_used
        
        await db.commit()
        await db.refresh(db_transaction)
        
        # Reload transaction with token relationship for response
        db_transaction = await transaction_crud.get_transaction_by_id(db, db_transaction.id)
        
        # Find receiver's user ID for notifications
        receiver_user_id = await address_resolver_crud.get_user_id_by_wallet_address(
            db, destination_wallet_address
        )
        
        # Set receiver user ID if found
        if receiver_user_id:
            await transaction_crud.update_transaction_receiver(db, db_transaction.id, receiver_user_id)
            db_transaction.to_user_id = receiver_user_id
        
        # NOTE: Notifications will be sent AFTER blockchain confirmation
        # Not sending notify_transaction_sent here - wait for blockchain success
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction creation failed: {str(e)}"
        )
    
    # Send transaction based on token type
    try:
        # Import settings to check if gasless is enabled
        from app.core.config import settings
        
        if transaction_data.token == "MATIC":
            result = await send_matic_transaction(
                wallet.address,
                destination_wallet_address,  # Use resolved wallet address
                float(transaction_data.amount),
                private_key
            )
        elif transaction_data.token == "USDC":
            # Use gasless transactions if enabled
            if settings.ENABLE_GASLESS and settings.RELAYER_PRIVATE_KEY:
                result = await send_token_transaction_with_relayer_fallback(
                    wallet.address,
                    destination_wallet_address,
                    float(transaction_data.amount),
                    USDC_CONTRACT,
                    private_key,
                    settings.RELAYER_PRIVATE_KEY,
                    6
                )
            else:
                result = await send_token_transaction(
                    wallet.address,
                    destination_wallet_address,
                    float(transaction_data.amount),
                    USDC_CONTRACT,
                    private_key,
                    6
                )
        elif transaction_data.token == "USDT":
            # Use gasless transactions if enabled
            if settings.ENABLE_GASLESS and settings.RELAYER_PRIVATE_KEY:
                result = await send_token_transaction_with_relayer_fallback(
                    wallet.address,
                    destination_wallet_address,
                    float(transaction_data.amount),
                    USDT_CONTRACT,
                    private_key,
                    settings.RELAYER_PRIVATE_KEY,
                    6
                )
            else:
                result = await send_token_transaction(
                    wallet.address,
                    destination_wallet_address,  # Use resolved wallet address
                    float(transaction_data.amount),
                    USDT_CONTRACT,
                    private_key,
                    6
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported token"
            )
        
        if result["success"]:
            # Update transaction with hash and success status
            await transaction_crud.update_transaction_status(
                db,
                db_transaction.id,
                TransactionStatus.CONFIRMED,
                result["transaction_hash"]
            )
            
            # Refresh transaction object
            db_transaction = await transaction_crud.get_transaction_by_id(db, db_transaction.id)
            
            # ✅ NOW send all notifications AFTER blockchain confirmation
            # 1. Notify sender that transaction was sent successfully
            await notification_service.notify_transaction_sent(db, db_transaction)
            
            # 2. Send confirmation notifications to both sender and receiver
            await notification_service.notify_transaction_confirmed(db, db_transaction)
            
            # 3. Send received notification to receiver if they are a DARI user
            if db_transaction.to_user_id:
                await notification_service.notify_transaction_received(db, db_transaction)
            
            # 🆕 4. Send EXPO PUSH NOTIFICATIONS (non-blocking, won't fail transaction)
            try:
                # Notify recipient (Expo Push)
                if db_transaction.to_user_id:
                    await notify_payment_received(
                        db=db,
                        recipient_user_id=db_transaction.to_user_id,
                        amount=str(db_transaction.amount),
                        token_symbol=db_transaction.token.symbol,
                        sender_address=wallet.address,
                        transaction_id=db_transaction.id
                    )
                
                # Notify sender (Expo Push)
                await notify_payment_sent(
                    db=db,
                    sender_user_id=current_user.id,
                    amount=str(db_transaction.amount),
                    token_symbol=db_transaction.token.symbol,
                    recipient_address=destination_wallet_address,
                    transaction_id=db_transaction.id,
                    status="complete"
                )
            except Exception as e:
                # Don't fail transaction if Expo notification fails
                print(f"⚠️ Expo notification error: {e}")
            
            return TransactionResponse(
                id=db_transaction.id,
                from_address=db_transaction.from_address,
                to_address=db_transaction.to_address,
                amount=db_transaction.amount,
                token=db_transaction.token.symbol,
                transaction_hash=result["transaction_hash"],
                transaction_type=db_transaction.transaction_type,
                status=TransactionStatus.CONFIRMED,
                created_at=db_transaction.created_at,
                gas_fee=db_transaction.gas_fee or Decimal("0"),
                platform_fee=db_transaction.platform_fee or Decimal("0"),
                total_fee=db_transaction.total_fee or Decimal("0"),
                from_country=db_transaction.from_country,
                to_country=db_transaction.to_country,
                is_international=db_transaction.is_international or False,
                recipient_name=db_transaction.recipient_name,
                recipient_phone=db_transaction.recipient_phone,
                transfer_method=db_transaction.transfer_method
            )
        else:
            # Update transaction with failed status
            await transaction_crud.update_transaction_status(
                db,
                db_transaction.id,
                TransactionStatus.FAILED
            )
            
            # Refresh transaction object and send failure notification
            db_transaction = await transaction_crud.get_transaction_by_id(db, db_transaction.id)
            await notification_service.notify_transaction_failed(db, db_transaction)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transaction failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        # Update transaction with failed status
        await transaction_crud.update_transaction_status(
            db,
            db_transaction.id,
            TransactionStatus.FAILED
        )
        
        # Refresh transaction object and send failure notification
        db_transaction = await transaction_crud.get_transaction_by_id(db, db_transaction.id)
        await notification_service.notify_transaction_failed(db, db_transaction)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send transaction: {str(e)}"
        )


# OLD ENDPOINT REMOVED - Replaced with privacy-friendly version below (line ~823)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionResponse:
    """Get specific transaction"""
    transaction = await transaction_crud.get_transaction_by_id(db, transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Ensure user owns this transaction
    if transaction.from_user_id != current_user.id and transaction.to_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build privacy-friendly response
    return await _build_transaction_response(transaction, current_user.id, db)


async def _build_transaction_response(
    transaction: Any,
    current_user_id: int,
    db: AsyncSession
) -> TransactionResponse:
    """Build privacy-friendly transaction response
    
    - Hides wallet addresses (shows DARI address or phone instead)
    - Shows payment method (DARI Address, Phone Number, Wallet Address)
    - Indicates direction (sent/received/self)
    - Filters out relayer gas fee transactions
    """
    from app.core.config import settings
    
    # Determine direction
    if transaction.from_user_id == current_user_id and transaction.to_user_id == current_user_id:
        direction = "self"
    elif transaction.from_user_id == current_user_id:
        direction = "sent"
    else:
        direction = "received"
    
    # Get user display names
    from_user_display = None
    to_user_display = None
    payment_method = None
    
    # Get sender info
    if transaction.from_user_id:
        from_user = await user_crud.get_user_by_id(db, transaction.from_user_id)
        if from_user:
            # Prefer DARI address (from address_resolver)
            if hasattr(from_user, 'address_resolver') and from_user.address_resolver:
                from_user_display = from_user.address_resolver.full_address
                if direction == "received":
                    payment_method = "DARI Address"
            elif from_user.phone:
                # Format phone nicely
                from_user_display = from_user.phone
                if direction == "received":
                    payment_method = "Phone Number"
            elif from_user.full_name:
                # Use full name if available
                from_user_display = from_user.full_name
                if direction == "received":
                    payment_method = "Name"
    
    # Get receiver info
    if transaction.to_user_id:
        to_user = await user_crud.get_user_by_id(db, transaction.to_user_id)
        if to_user:
            # Prefer DARI address (from address_resolver)
            if hasattr(to_user, 'address_resolver') and to_user.address_resolver:
                to_user_display = to_user.address_resolver.full_address
                if direction == "sent":
                    payment_method = "DARI Address"
            elif to_user.phone:
                # Format phone nicely
                to_user_display = to_user.phone
                if direction == "sent":
                    payment_method = "Phone Number"
            elif to_user.full_name:
                # Use full name if available
                to_user_display = to_user.full_name
                if direction == "sent":
                    payment_method = "Name"
    
    # Fallback to wallet address (masked for privacy)
    if not from_user_display and transaction.from_address:
        # Better masking: show first 6 and last 4 characters only
        addr = transaction.from_address
        from_user_display = f"{addr[:6]}...{addr[-4:]}"
    
    if not to_user_display and transaction.to_address:
        # Better masking: show first 6 and last 4 characters only  
        addr = transaction.to_address
        to_user_display = f"{addr[:6]}...{addr[-4:]}"
    
    # If still no display name, use "Unknown"
    if not from_user_display:
        from_user_display = "Unknown"
    if not to_user_display:
        to_user_display = "Unknown"
    
    if not payment_method:
        payment_method = "Wallet Address"
    
    return TransactionResponse(
        id=transaction.id,
        from_address=None,  # Hidden for privacy
        to_address=None,    # Hidden for privacy
        amount=transaction.amount,
        token=transaction.token.symbol if transaction.token else "UNKNOWN",
        transaction_hash=transaction.tx_hash,
        transaction_type=transaction.transaction_type,
        status=transaction.status,
        gas_fee=transaction.gas_fee,
        platform_fee=transaction.platform_fee,
        total_fee=transaction.total_fee,
        gas_used=transaction.gas_used,
        from_country=transaction.from_country,
        to_country=transaction.to_country,
        is_international=transaction.is_international,
        recipient_name=transaction.recipient_name,
        recipient_phone=transaction.recipient_phone,
        transfer_method=transaction.transfer_method,
        from_user_display=from_user_display,
        to_user_display=to_user_display,
        payment_method=payment_method,
        direction=direction,
        created_at=transaction.created_at,
        completed_at=transaction.confirmed_at
    )


@router.get("/", response_model=List[TransactionResponse])
async def get_transaction_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
) -> List[TransactionResponse]:
    """Get user's transaction history
    
    Privacy features:
    - Hides wallet addresses (shows DARI address or phone instead)
    - Shows payment method used
    - Filters out relayer gas fee transactions
    - Indicates transaction direction (sent/received/self)
    """
    from app.core.config import settings
    
    # Get user's wallet
    wallet = await wallet_crud.get_wallet_by_user_id(db, current_user.id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Get user's transactions from database
    all_transactions = await transaction_crud.get_user_transactions(
        db, current_user.id, skip=offset, limit=limit * 2  # Get extra to account for filtering
    )
    
    # Filter out relayer gas fee transactions
    relayer_address = settings.RELAYER_ADDRESS.lower() if settings.RELAYER_ADDRESS else ""
    
    filtered_transactions = []
    for transaction in all_transactions:
        # Skip transactions from relayer (gas fee transactions)
        if relayer_address and transaction.from_address and transaction.from_address.lower() == relayer_address:
            # This is a gas fee transaction from relayer, skip it
            continue
        
        # Skip small MATIC transactions TO user (these are gas fees from relayer)
        if (transaction.token and transaction.token.symbol == "MATIC" and 
            transaction.to_user_id == current_user.id and
            transaction.amount and float(transaction.amount) < 0.01):  # Gas fees are typically < 0.01 MATIC
            # This is likely a gas fee transaction, skip it
            continue
        
        # Skip MATIC transactions from relayer to user
        if (relayer_address and transaction.token and transaction.token.symbol == "MATIC" and 
            transaction.from_address and transaction.from_address.lower() == relayer_address and
            transaction.to_user_id == current_user.id):
            continue
        
        filtered_transactions.append(transaction)
        
        # Stop when we have enough
        if len(filtered_transactions) >= limit:
            break
    
    # Build privacy-friendly responses
    responses = []
    for transaction in filtered_transactions:
        response = await _build_transaction_response(transaction, current_user.id, db)
        responses.append(response)
    
    return responses


@router.get("/relayer/status")
async def get_relayer_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get relayer wallet status for gasless transactions
    
    Returns:
    - Relayer address
    - Current MATIC balance
    - Estimated transactions remaining
    - Average gas cost per transaction
    - Status (funded/low/empty)
    """
    from app.services.blockchain_service import get_relayer_status
    
    try:
        status_data = await get_relayer_status()
        return status_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get relayer status: {str(e)}"
        )
