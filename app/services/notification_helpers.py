"""
Notification Integration Helper

This module provides easy integration of push notifications into your existing endpoints.
Just call these functions after creating transactions, updating KYC, etc.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.services.expo_push_service import ExpoPushNotificationService
from app.crud import push_token as push_token_crud

logger = logging.getLogger(__name__)


async def notify_payment_received(
    db: AsyncSession,
    recipient_user_id: int,
    amount: str,
    token_symbol: str,
    sender_address: str,
    transaction_id: int
):
    """
    Send push notification when user receives a payment
    
    Usage:
        # In your transaction creation endpoint:
        await notify_payment_received(
            db=db,
            recipient_user_id=transaction.to_user_id,
            amount=str(transaction.amount),
            token_symbol=transaction.token_symbol,
            sender_address=sender_user.dari_address,
            transaction_id=transaction.id
        )
    """
    
    # Get all active tokens for recipient
    tokens = await push_token_crud.get_user_push_tokens(db, recipient_user_id, active_only=True)
    
    if not tokens:
        logger.info(f"No active push tokens for user {recipient_user_id}")
        return
    
    service = ExpoPushNotificationService()
    
    for token in tokens:
        await service.send_notification(
            expo_push_token=token.expo_push_token,
            title="Payment Received",
            body=f"You received {amount} {token_symbol} from {sender_address}",
            data={
                "type": "payment_received",
                "amount": amount,
                "token": token_symbol,
                "sender": sender_address,
                "transaction_id": str(transaction_id),
                "screen": "TransactionDetails"
            },
            badge=1,
            channel_id="payments",
            priority="high"
        )
    
    logger.info(f"✓ Payment notification sent to user {recipient_user_id} ({len(tokens)} devices)")


async def notify_payment_sent(
    db: AsyncSession,
    sender_user_id: int,
    amount: str,
    token_symbol: str,
    recipient_address: str,
    transaction_id: int,
    status: str = "pending"
):
    """
    Send push notification when user sends a payment
    
    Usage:
        await notify_payment_sent(
            db=db,
            sender_user_id=transaction.from_user_id,
            amount=str(transaction.amount),
            token_symbol=transaction.token_symbol,
            recipient_address=recipient_user.dari_address,
            transaction_id=transaction.id,
            status="complete"
        )
    """
    
    tokens = await push_token_crud.get_user_push_tokens(db, sender_user_id, active_only=True)
    
    if not tokens:
        return
    
    service = ExpoPushNotificationService()
    
    status_text = "sent successfully" if status == "complete" else "is pending"
    
    for token in tokens:
        await service.send_notification(
            expo_push_token=token.expo_push_token,
            title="Payment Sent",
            body=f"Your payment of {amount} {token_symbol} to {recipient_address} {status_text}",
            data={
                "type": "payment_sent",
                "amount": amount,
                "token": token_symbol,
                "recipient": recipient_address,
                "transaction_id": str(transaction_id),
                "status": status,
                "screen": "TransactionDetails"
            },
            channel_id="transactions"
        )
    
    logger.info(f"✓ Payment sent notification to user {sender_user_id}")


async def notify_transaction_status(
    db: AsyncSession,
    user_id: int,
    transaction_id: int,
    status: str,
    amount: str,
    token_symbol: str
):
    """
    Send notification when transaction status changes
    
    Usage:
        await notify_transaction_status(
            db=db,
            user_id=transaction.from_user_id,
            transaction_id=transaction.id,
            status="complete",
            amount=str(transaction.amount),
            token_symbol=transaction.token_symbol
        )
    """
    
    tokens = await push_token_crud.get_user_push_tokens(db, user_id, active_only=True)
    
    if not tokens:
        return
    
    service = ExpoPushNotificationService()
    
    status_messages = {
        "complete": f"Transaction Complete",
        "failed": f"Transaction Failed",
        "pending": f"Transaction Pending"
    }
    
    title = status_messages.get(status, "Transaction Update")
    body = f"Your transaction of {amount} {token_symbol} is {status}"
    
    for token in tokens:
        await service.send_notification(
            expo_push_token=token.expo_push_token,
            title=title,
            body=body,
            data={
                "type": "transaction_status",
                "transaction_id": str(transaction_id),
                "status": status,
                "amount": amount,
                "token": token_symbol,
                "screen": "TransactionDetails"
            },
            channel_id="transactions",
            priority="high" if status == "failed" else "default"
        )


async def notify_kyc_status(
    db: AsyncSession,
    user_id: int,
    status: str,
    reason: Optional[str] = None
):
    """
    Send notification when KYC status changes
    
    Usage:
        await notify_kyc_status(
            db=db,
            user_id=user.id,
            status="approved"
        )
    """
    
    tokens = await push_token_crud.get_user_push_tokens(db, user_id, active_only=True)
    
    if not tokens:
        return
    
    service = ExpoPushNotificationService()
    
    if status == "approved":
        title = "KYC Approved ✓"
        body = "Your identity verification has been approved!"
    elif status == "rejected":
        title = "KYC Review Required"
        body = f"Your verification needs review. {reason or 'Please check details.'}"
    else:
        title = "KYC Status Update"
        body = f"Your KYC status is now: {status}"
    
    for token in tokens:
        await service.send_notification(
            expo_push_token=token.expo_push_token,
            title=title,
            body=body,
            data={
                "type": f"kyc_{status}",
                "status": status,
                "reason": reason,
                "screen": "KYCStatus"
            },
            channel_id="security",
            priority="high"
        )


async def notify_deposit_complete(
    db: AsyncSession,
    user_id: int,
    amount: str,
    token_symbol: str,
    deposit_id: int
):
    """
    Send notification when deposit is complete
    
    Usage:
        await notify_deposit_complete(
            db=db,
            user_id=deposit.user_id,
            amount=str(deposit.amount),
            token_symbol=deposit.token_symbol,
            deposit_id=deposit.id
        )
    """
    
    tokens = await push_token_crud.get_user_push_tokens(db, user_id, active_only=True)
    
    if not tokens:
        return
    
    service = ExpoPushNotificationService()
    
    for token in tokens:
        await service.send_notification(
            expo_push_token=token.expo_push_token,
            title="Deposit Complete",
            body=f"Your deposit of {amount} {token_symbol} has been credited to your wallet",
            data={
                "type": "deposit_complete",
                "amount": amount,
                "token": token_symbol,
                "deposit_id": str(deposit_id),
                "screen": "DepositDetails"
            },
            badge=1,
            channel_id="transactions",
            priority="high"
        )


async def notify_withdrawal_complete(
    db: AsyncSession,
    user_id: int,
    amount: str,
    token_symbol: str,
    withdrawal_id: int
):
    """
    Send notification when withdrawal is complete
    """
    
    tokens = await push_token_crud.get_user_push_tokens(db, user_id, active_only=True)
    
    if not tokens:
        return
    
    service = ExpoPushNotificationService()
    
    for token in tokens:
        await service.send_notification(
            expo_push_token=token.expo_push_token,
            title="Withdrawal Complete",
            body=f"Your withdrawal of {amount} {token_symbol} has been processed",
            data={
                "type": "withdrawal_complete",
                "amount": amount,
                "token": token_symbol,
                "withdrawal_id": str(withdrawal_id),
                "screen": "WithdrawalDetails"
            },
            channel_id="transactions"
        )


async def notify_security_alert(
    db: AsyncSession,
    user_id: int,
    alert_type: str,
    message: str
):
    """
    Send security alert notification
    
    Usage:
        await notify_security_alert(
            db=db,
            user_id=user.id,
            alert_type="login_new_device",
            message="New login detected from Pixel 6"
        )
    """
    
    tokens = await push_token_crud.get_user_push_tokens(db, user_id, active_only=True)
    
    if not tokens:
        return
    
    service = ExpoPushNotificationService()
    
    for token in tokens:
        await service.send_notification(
            expo_push_token=token.expo_push_token,
            title="Security Alert",
            body=message,
            data={
                "type": "security_alert",
                "alert_type": alert_type,
                "screen": "Security"
            },
            channel_id="security",
            priority="high"
        )
