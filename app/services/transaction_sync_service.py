from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
import asyncio

from app.services.blockchain_service import get_blockchain_transactions
from app.crud.transaction import create_transaction
from app.crud.wallet import get_wallet_by_address
from app.crud.user import get_user_by_id
from app.crud.token import get_token_by_symbol
from app.models.transaction import TransactionType, TransactionStatus
from app.schemas.transaction import TransactionCreate


class TransactionSyncService:
    """Service for syncing blockchain transactions with database"""
    
    async def sync_user_transactions(
        self,
        db: AsyncSession,
        user_id: int,
        wallet_address: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Sync blockchain transactions for a user's wallet"""
        try:
            print(f"🔄 Syncing transactions for user {user_id}, wallet: {wallet_address}")
            
            # Fetch transactions from blockchain
            blockchain_result = await get_blockchain_transactions(wallet_address, limit)
            
            if not blockchain_result.get("success"):
                print(f"⚠️ Blockchain API failed: {blockchain_result.get('error', 'Unknown error')}")
                return {
                    "success": True,  # Don't fail sync for API issues
                    "error": f"API unavailable: {blockchain_result.get('error', 'Unknown error')}",
                    "synced_count": 0,
                    "skipped_count": 0,
                    "api_failed": True
                }
            
            blockchain_transactions = blockchain_result.get("transactions", [])
            
            if not blockchain_transactions:
                print("ℹ️ No blockchain transactions found (API may be down or wallet has no transactions)")
                return {
                    "success": True,
                    "message": "No transactions found to sync",
                    "synced_count": 0,
                    "skipped_count": 0,
                    "total_blockchain_transactions": 0
                }
            
            synced_count = 0
            skipped_count = 0
            
            for tx_data in blockchain_transactions:
                try:
                    # Check if transaction already exists in database
                    existing_tx = await self._check_transaction_exists(db, tx_data['hash'])
                    if existing_tx:
                        skipped_count += 1
                        continue
                    
                    # Determine transaction direction and type
                    is_incoming = tx_data['to_address'].lower() == wallet_address.lower()
                    is_outgoing = tx_data['from_address'].lower() == wallet_address.lower()
                    
                    if not (is_incoming or is_outgoing):
                        continue  # Skip transactions not related to this wallet
                    
                    # Get token information
                    token = await get_token_by_symbol(db, tx_data['token_symbol'])
                    if not token:
                        print(f"⚠️ Token {tx_data['token_symbol']} not found in database, skipping")
                        continue
                    
                    # Calculate amount in human-readable format
                    amount_wei = int(tx_data['value'])
                    amount = Decimal(amount_wei) / Decimal(10 ** tx_data['token_decimals'])
                    
                    # Calculate fees
                    gas_used = int(tx_data.get('gas_used', 0))
                    gas_price = int(tx_data.get('gas_price', 0))
                    fee_wei = gas_used * gas_price
                    fee = Decimal(fee_wei) / Decimal(10 ** 18)  # Gas fees are in MATIC (18 decimals)
                    
                    # Determine user IDs for from/to
                    from_user_id = None
                    to_user_id = None
                    
                    if is_outgoing:
                        from_user_id = user_id
                        # Try to find the recipient user
                        to_wallet = await get_wallet_by_address(db, tx_data['to_address'])
                        if to_wallet:
                            to_user_id = to_wallet.user_id
                    
                    if is_incoming:
                        to_user_id = user_id
                        # Try to find the sender user
                        from_wallet = await get_wallet_by_address(db, tx_data['from_address'])
                        if from_wallet:
                            from_user_id = from_wallet.user_id
                    
                    # Create transaction record
                    transaction_data = TransactionCreate(
                        from_address=tx_data['from_address'],
                        to_address=tx_data['to_address'],
                        amount=amount,
                        token_id=token.id,
                        transaction_type=TransactionType.SEND if is_outgoing else TransactionType.RECEIVE,
                        status=TransactionStatus.CONFIRMED if tx_data['status'] == '1' else TransactionStatus.FAILED,
                        transaction_hash=tx_data['hash'],
                        fee=fee,
                        gas_used=str(gas_used),
                        from_user_id=from_user_id,
                        to_user_id=to_user_id,
                        is_external=True  # Mark as external (from blockchain sync)
                    )
                    
                    # Create transaction in database
                    await create_transaction(db, transaction_data)
                    synced_count += 1
                    
                    print(f"✅ Synced transaction: {tx_data['hash'][:10]}... ({tx_data['token_symbol']})")
                    
                except Exception as e:
                    print(f"❌ Error syncing transaction {tx_data.get('hash', 'unknown')}: {e}")
                    continue
            
            print(f"🎉 Sync complete: {synced_count} new transactions, {skipped_count} already existed")
            
            return {
                "success": True,
                "synced_count": synced_count,
                "skipped_count": skipped_count,
                "total_blockchain_transactions": len(blockchain_transactions)
            }
            
        except Exception as e:
            print(f"❌ Error syncing user transactions: {e}")
            return {
                "success": False,
                "error": str(e),
                "synced_count": 0
            }
    
    async def _check_transaction_exists(self, db: AsyncSession, tx_hash: str) -> bool:
        """Check if a transaction already exists in the database"""
        from sqlalchemy import select
        from app.models.transaction import Transaction
        
        try:
            result = await db.execute(
                select(Transaction).where(Transaction.transaction_hash == tx_hash)
            )
            return result.scalar_one_or_none() is not None
        except Exception:
            return False


# Create service instance
transaction_sync_service = TransactionSyncService()
