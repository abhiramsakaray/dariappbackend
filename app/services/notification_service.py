from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import json

from app.crud.notification import notification_crud
from app.crud.user import get_user_by_id
from app.crud.address_resolver import get_address_resolver_by_wallet_address
from app.services.currency_service import currency_service
from app.services.email_service import email_service
from app.services.firebase_service import firebase_service
from app.models.notification import NotificationType
from app.models.transaction import Transaction, TransactionType
from app.schemas.notification import NotificationCreate, TransactionNotificationData


class NotificationService:
    """Service for handling notifications"""
    
    def _format_amount(self, amount: Decimal, decimals: int = 6) -> str:
        """Format amount to remove unnecessary trailing zeros"""
        # Convert to float and format with specified decimals
        formatted = f"{float(amount):.{decimals}f}"
        # Remove trailing zeros and decimal point if not needed
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        return formatted
    
    async def create_transaction_notification(
        self,
        db: AsyncSession,
        user_id: int,
        transaction: Transaction,
        notification_type: NotificationType,
        amount_in_user_currency: Optional[str] = None,
        user_currency: str = "USD"
    ) -> None:
        """Create a transaction notification for a user"""
        
        try:
            print(f"📧 Creating notification for user {user_id}, type: {notification_type}")
            
            # Get user details for default currency
            user = await get_user_by_id(db, user_id)
            if not user:
                print(f"❌ User {user_id} not found")
                return
            
            # Get DARI addresses if available
            sender_dari_address = None
            receiver_dari_address = None
            
            # Check if sender has DARI address
            if transaction.from_address:
                sender_resolver = await get_address_resolver_by_wallet_address(db, transaction.from_address)
                if sender_resolver:
                    sender_dari_address = sender_resolver.full_address
            
            # Check if receiver has DARI address
            if transaction.to_address:
                receiver_resolver = await get_address_resolver_by_wallet_address(db, transaction.to_address)
                if receiver_resolver:
                    receiver_dari_address = receiver_resolver.full_address
            
            # Convert amount to user's preferred currency if not provided
            if not amount_in_user_currency and user.default_currency != "USD":
                try:
                    # Get token price in USD first
                    token = transaction.token
                    if token and token.coingecko_id:
                        from app.services.price_service import price_service
                        token_price_usd = await price_service.get_token_price(token.coingecko_id, "usd")
                        
                        if token_price_usd:
                            usd_value = float(transaction.amount) * float(token_price_usd)
                            
                            # Convert USD to user's currency
                            converted_amount = await currency_service.convert_amount(
                                Decimal(str(usd_value)),
                                "USD",
                                user.default_currency
                            )
                            
                            if converted_amount:
                                amount_in_user_currency = f"{float(converted_amount):.2f}"
                
                except Exception as e:
                    print(f"❌ Error converting currency for notification: {e}")
                    amount_in_user_currency = None
            
            # Format the amount properly (remove unnecessary decimals)
            formatted_amount = self._format_amount(transaction.amount)
            
            # Prepare notification metadata
            notification_metadata = TransactionNotificationData(
                transaction_hash=transaction.tx_hash or "",
                amount=formatted_amount,
                token_symbol=transaction.token.symbol if transaction.token else "UNKNOWN",
                amount_in_user_currency=amount_in_user_currency,
                user_currency=user.default_currency,
                sender_dari_address=sender_dari_address,
                receiver_dari_address=receiver_dari_address,
                sender_wallet_address=transaction.from_address,
                receiver_wallet_address=transaction.to_address,
                transaction_time=transaction.created_at.isoformat() if transaction.created_at else datetime.now().isoformat()
            ).dict()
            
            # Generate notification title and message based on type
            title, message = self._generate_notification_content(
                notification_type,
                transaction,
                notification_metadata
            )
            
            # Create notification
            notification_data = NotificationCreate(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                extra_data=notification_metadata,
                transaction_id=transaction.id
            )
            
            await notification_crud.create_notification(db, notification_data)
            print(f"✅ In-app notification created successfully")
            
            # Send push notification via Firebase
            await self._send_push_notification(user, notification_type, title, message, notification_metadata)
            
            # Send email notification
            await self._send_email_notification(user, notification_type, notification_metadata)
            
        except Exception as e:
            print(f"❌ Error creating transaction notification: {e}")
    
    def _generate_notification_content(
        self,
        notification_type: NotificationType,
        transaction: Transaction,
        metadata: Dict[str, Any]
    ) -> tuple[str, str]:
        """Generate notification title and message"""
        
        amount = metadata.get("amount", "0")
        token_symbol = metadata.get("token_symbol", "UNKNOWN")
        amount_in_user_currency = metadata.get("amount_in_user_currency")
        user_currency = metadata.get("user_currency", "USD")
        sender_dari = metadata.get("sender_dari_address")
        receiver_dari = metadata.get("receiver_dari_address")
        sender_wallet = metadata.get("sender_wallet_address", "")
        receiver_wallet = metadata.get("receiver_wallet_address", "")
        transaction_hash = metadata.get("transaction_hash", "")
        
        # Format amount display
        amount_display = f"{amount} {token_symbol}"
        if amount_in_user_currency and user_currency != "USD":
            amount_display += f" (≈ {amount_in_user_currency} {user_currency})"
        
        # Show amount in user's default currency only (not USDC)
        # If user currency is USD, show token amount, otherwise show converted amount
        if user_currency != "USD" and amount_in_user_currency:
            primary_amount_display = f"{amount_in_user_currency} {user_currency}"
            secondary_amount_display = f"{amount} {token_symbol}"
        else:
            primary_amount_display = f"{amount} {token_symbol}"
            secondary_amount_display = None
        
        if notification_type == NotificationType.TRANSACTION_SENT:
            title = "Transaction Sent"
            
            # Use DARI address if available, otherwise wallet address
            to_display = receiver_dari if receiver_dari else f"{receiver_wallet[:8]}...{receiver_wallet[-6:]}"
            
            message = f"You sent {primary_amount_display} to {to_display}"
            if secondary_amount_display:
                message += f" ({secondary_amount_display})"
            if transaction_hash:
                message += f"\n\nTransaction Hash: {transaction_hash}"
        
        elif notification_type == NotificationType.TRANSACTION_RECEIVED:
            title = "Payment Received"
            
            # Use DARI address if available, otherwise wallet address  
            from_display = sender_dari if sender_dari else f"{sender_wallet[:8]}...{sender_wallet[-6:]}"
            
            message = f"You received {primary_amount_display} from {from_display}"
            if secondary_amount_display:
                message += f" ({secondary_amount_display})"
            if transaction_hash:
                message += f"\n\nTransaction Hash: {transaction_hash}"
        
        elif notification_type == NotificationType.TRANSACTION_CONFIRMED:
            title = "Transaction Confirmed"
            message = f"Your transaction of {primary_amount_display} has been confirmed on the blockchain"
            if secondary_amount_display:
                message += f" ({secondary_amount_display})"
            if transaction_hash:
                message += f"\n\nTransaction Hash: {transaction_hash}"
        
        elif notification_type == NotificationType.TRANSACTION_FAILED:
            title = "Transaction Failed"
            message = f"Your transaction of {primary_amount_display} has failed"
            if secondary_amount_display:
                message += f" ({secondary_amount_display})"
            if transaction_hash:
                message += f"\n\nTransaction Hash: {transaction_hash}"
        
        else:
            title = "Transaction Update"
            message = f"Transaction update for {primary_amount_display}"
        
        return title, message
    
    async def _send_push_notification(
        self,
        user,
        notification_type: NotificationType,
        title: str,
        message: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Send push notification via Firebase Cloud Messaging"""
        try:
            # Check if user has FCM device token
            if not hasattr(user, 'fcm_device_token') or not user.fcm_device_token:
                print(f"ℹ️  User {user.id} has no FCM device token - skipping push notification")
                return
            
            print(f"📱 Sending push notification to user {user.id}")
            
            # Get unread notification count for badge
            from app.crud.notification import notification_crud
            # We'll use a simple count, you can get actual unread count from DB if needed
            unread_count = 1
            
            # Determine notification type for Firebase
            if notification_type == NotificationType.TRANSACTION_SENT:
                fcm_type = "sent"
            elif notification_type == NotificationType.TRANSACTION_RECEIVED:
                fcm_type = "received"
            elif notification_type == NotificationType.TRANSACTION_CONFIRMED:
                fcm_type = "confirmed"
            elif notification_type == NotificationType.TRANSACTION_FAILED:
                fcm_type = "failed"
            else:
                fcm_type = "update"
            
            # Extract relevant info
            amount = metadata.get("amount", "0")
            user_currency = metadata.get("user_currency", "USD")
            amount_in_user_currency = metadata.get("amount_in_user_currency")
            token_symbol = metadata.get("token_symbol", "")
            
            # Use user's currency amount if available
            if user_currency != "USD" and amount_in_user_currency:
                display_amount = amount_in_user_currency
                display_currency = user_currency
            else:
                display_amount = amount
                display_currency = token_symbol
            
            # Get from/to display
            sender_dari = metadata.get("sender_dari_address")
            receiver_dari = metadata.get("receiver_dari_address")
            sender_wallet = metadata.get("sender_wallet_address", "")
            receiver_wallet = metadata.get("receiver_wallet_address", "")
            
            if fcm_type == "sent":
                from_to_display = receiver_dari if receiver_dari else f"{receiver_wallet[:8]}...{receiver_wallet[-6:]}"
            else:
                from_to_display = sender_dari if sender_dari else f"{sender_wallet[:8]}...{sender_wallet[-6:]}"
            
            # Send via Firebase
            await firebase_service.send_transaction_notification(
                device_token=user.fcm_device_token,
                notification_type=fcm_type,
                amount=display_amount,
                currency=display_currency,
                from_to_display=from_to_display,
                transaction_id=metadata.get("transaction_id"),
                unread_count=unread_count
            )
            
            print(f"✓ Push notification sent to user {user.id}")
            
        except Exception as e:
            print(f"✗ Error sending push notification: {e}")
    
    async def _send_email_notification(
        self,
        user,
        notification_type: NotificationType,
        metadata: Dict[str, Any]
    ) -> None:
        """Send email notification to user"""
        try:
            print(f"📧 Sending email notification to {user.email}")
            
            amount = metadata.get("amount", "0")
            token_symbol = metadata.get("token_symbol", "UNKNOWN")
            amount_in_user_currency = metadata.get("amount_in_user_currency")
            user_currency = metadata.get("user_currency", "USD")
            transaction_hash = metadata.get("transaction_hash", "")
            sender_dari = metadata.get("sender_dari_address")
            receiver_dari = metadata.get("receiver_dari_address")
            sender_wallet = metadata.get("sender_wallet_address", "")
            receiver_wallet = metadata.get("receiver_wallet_address", "")
            
            if notification_type == NotificationType.TRANSACTION_SENT:
                to_display = receiver_dari if receiver_dari else f"{receiver_wallet[:8]}...{receiver_wallet[-6:]}"
                await email_service.send_transaction_sent_email(
                    email=user.email,
                    name=user.email.split('@')[0].title(),
                    amount=amount,
                    token=token_symbol,
                    to_address=to_display,
                    transaction_hash=transaction_hash,
                    amount_in_user_currency=amount_in_user_currency,
                    user_currency=user_currency
                )
            elif notification_type == NotificationType.TRANSACTION_RECEIVED:
                from_display = sender_dari if sender_dari else f"{sender_wallet[:8]}...{sender_wallet[-6:]}"
                await email_service.send_transaction_received_email(
                    email=user.email,
                    name=user.email.split('@')[0].title(),
                    amount=amount,
                    token=token_symbol,
                    from_address=from_display,
                    transaction_hash=transaction_hash,
                    amount_in_user_currency=amount_in_user_currency,
                    user_currency=user_currency
                )
            elif notification_type == NotificationType.TRANSACTION_CONFIRMED:
                # For confirmed transactions, we'll send a generic sent email since there's no specific confirmed email method
                print(f"📧 Transaction confirmed - skipping email (no specific email template available)")
                
            elif notification_type == NotificationType.TRANSACTION_FAILED:
                to_display = receiver_dari if receiver_dari else f"{receiver_wallet[:8]}...{receiver_wallet[-6:]}"
                await email_service.send_transaction_failed_email(
                    email=user.email,
                    name=user.email.split('@')[0].title(),
                    amount=amount,
                    token=token_symbol,
                    to_address=to_display,
                    error_message="Transaction failed on blockchain"
                )
            
            print(f"✅ Email notification sent successfully to {user.email}")
            
        except Exception as e:
            print(f"❌ Error sending email notification: {e}")
    
    async def notify_transaction_sent(
        self,
        db: AsyncSession,
        transaction: Transaction
    ) -> None:
        """Notify sender when transaction is sent"""
        if transaction.from_user_id:
            await self.create_transaction_notification(
                db,
                transaction.from_user_id,
                transaction,
                NotificationType.TRANSACTION_SENT
            )
    
    async def notify_transaction_received(
        self,
        db: AsyncSession,
        transaction: Transaction
    ) -> None:
        """Notify receiver when transaction is received"""
        if transaction.to_user_id:
            await self.create_transaction_notification(
                db,
                transaction.to_user_id,
                transaction,
                NotificationType.TRANSACTION_RECEIVED
            )
    
    async def notify_transaction_confirmed(
        self,
        db: AsyncSession,
        transaction: Transaction
    ) -> None:
        """Notify both parties when transaction is confirmed"""
        # Notify sender about confirmation
        if transaction.from_user_id:
            await self.create_transaction_notification(
                db,
                transaction.from_user_id,
                transaction,
                NotificationType.TRANSACTION_CONFIRMED
            )
        
        # Notify receiver about confirmation (only if they are a DARI user)
        if transaction.to_user_id:
            await self.create_transaction_notification(
                db,
                transaction.to_user_id,
                transaction,
                NotificationType.TRANSACTION_CONFIRMED
            )
    
    async def notify_transaction_failed(
        self,
        db: AsyncSession,
        transaction: Transaction
    ) -> None:
        """Notify sender when transaction fails"""
        if transaction.from_user_id:
            await self.create_transaction_notification(
                db,
                transaction.from_user_id,
                transaction,
                NotificationType.TRANSACTION_FAILED
            )


# Create service instance
notification_service = NotificationService()
