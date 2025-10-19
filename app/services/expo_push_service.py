import httpx
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ExpoPushNotificationService:
    """Service for sending Expo push notifications"""
    
    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
    
    @staticmethod
    async def send_notification(
        expo_push_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        sound: str = "default",
        badge: Optional[int] = None,
        channel_id: str = "default",
        priority: str = "high"
    ) -> Dict[str, Any]:
        """
        Send a single push notification via Expo
        
        Args:
            expo_push_token: Expo push token for the device
            title: Notification title
            body: Notification body/message
            data: Additional data payload (optional)
            sound: Sound to play ('default' or None for silent)
            badge: Badge count to display (iOS)
            channel_id: Android notification channel ID
            priority: Notification priority ('default' or 'high')
            
        Returns:
            Response from Expo push service
        """
        
        payload = {
            "to": expo_push_token,
            "title": title,
            "body": body,
            "data": data or {},
            "sound": sound,
            "priority": priority,
            "channelId": channel_id,
        }
        
        if badge is not None:
            payload["badge"] = badge
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    ExpoPushNotificationService.EXPO_PUSH_URL,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip, deflate"
                    },
                    timeout=10.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✓ Push notification sent to {expo_push_token[:20]}...")
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"✗ Error sending push notification: {e}")
            return {"error": str(e), "success": False}
        except Exception as e:
            logger.error(f"✗ Unexpected error sending push notification: {e}")
            return {"error": str(e), "success": False}
    
    @staticmethod
    async def send_bulk_notifications(
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send multiple push notifications in one request
        
        Args:
            notifications: List of notification payloads
            
        Returns:
            Response from Expo push service with results for each notification
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    ExpoPushNotificationService.EXPO_PUSH_URL,
                    json=notifications,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip, deflate"
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✓ Sent {len(notifications)} bulk push notifications")
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"✗ Error sending bulk push notifications: {e}")
            return {"error": str(e), "success": False}
        except Exception as e:
            logger.error(f"✗ Unexpected error sending bulk push notifications: {e}")
            return {"error": str(e), "success": False}
    
    @staticmethod
    def handle_expo_error(response: Dict[str, Any]) -> Optional[str]:
        """
        Parse Expo push response and extract error code if present
        
        Returns:
            Error code if found, None otherwise
            Common codes: 'DeviceNotRegistered', 'MessageTooBig', 'MessageRateExceeded'
        """
        
        if "data" in response:
            data = response.get("data", [])
            if isinstance(data, list) and len(data) > 0:
                error_info = data[0]
                if error_info.get("status") == "error":
                    error_code = error_info.get("details", {}).get("error")
                    return error_code
        
        return None


# Convenience function for sending to multiple users
async def send_notification_to_users(
    db,
    user_ids: List[int],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, int]:
    """
    Send push notifications to multiple users
    
    Args:
        db: Database session
        user_ids: List of user IDs to notify
        title: Notification title
        body: Notification body
        data: Additional data payload
        **kwargs: Additional arguments for send_notification
        
    Returns:
        Dictionary with success/failure counts
    """
    from app.crud import push_token as push_token_crud
    
    service = ExpoPushNotificationService()
    success_count = 0
    failure_count = 0
    
    for user_id in user_ids:
        # Get all active tokens for user
        tokens = await push_token_crud.get_user_push_tokens(db, user_id, active_only=True)
        
        for token in tokens:
            result = await service.send_notification(
                expo_push_token=token.expo_push_token,
                title=title,
                body=body,
                data=data,
                **kwargs
            )
            
            if result.get("error"):
                failure_count += 1
                # Check if token is invalid
                error_code = service.handle_expo_error(result)
                if error_code == "DeviceNotRegistered":
                    await push_token_crud.deactivate_invalid_token(db, token.expo_push_token)
                    logger.info(f"Deactivated invalid token: {token.expo_push_token[:20]}...")
            else:
                success_count += 1
                # Update last_used_at
                await push_token_crud.update_token_last_used(db, token.expo_push_token)
    
    return {
        "success": success_count,
        "failed": failure_count,
        "total": success_count + failure_count
    }
