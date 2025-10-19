"""
Firebase Cloud Messaging (FCM) Service for push notifications
Supports both Legacy API (Server Key) and V1 API (Service Account)
"""
from typing import Optional, Dict, Any, List
import httpx
import json
import os
from pathlib import Path
from app.core.config import settings


class FirebaseService:
    """Service for sending push notifications via Firebase Cloud Messaging"""
    
    def __init__(self):
        # Legacy API (Server Key) - simpler but deprecated
        self.fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', None)
        self.fcm_legacy_url = "https://fcm.googleapis.com/fcm/send"
        
        # V1 API (Service Account) - recommended
        self.fcm_project_id = getattr(settings, 'FCM_PROJECT_ID', None)
        self.fcm_service_account_path = getattr(settings, 'FCM_SERVICE_ACCOUNT_PATH', None)
        self.fcm_v1_url = f"https://fcm.googleapis.com/v1/projects/{self.fcm_project_id}/messages:send" if self.fcm_project_id else None
        
        # Determine which API to use
        self.use_v1_api = self.fcm_project_id and self.fcm_service_account_path
        
        if self.use_v1_api:
            print("✓ FCM V1 API configured (Service Account)")
        elif self.fcm_server_key:
            print("⚠️  FCM Legacy API configured (Server Key) - Consider migrating to V1")
        else:
            print("ℹ️  FCM not configured - Push notifications disabled")
        
    def _get_access_token(self) -> Optional[str]:
        """
        Get OAuth2 access token for FCM V1 API using service account
        """
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
            
            credentials = service_account.Credentials.from_service_account_file(
                self.fcm_service_account_path,
                scopes=['https://www.googleapis.com/auth/firebase.messaging']
            )
            
            credentials.refresh(Request())
            return credentials.token
        except ImportError:
            print("✗ google-auth library not installed. Run: pip install google-auth")
            return None
        except Exception as e:
            print(f"✗ Error getting FCM access token: {e}")
            return None
    
    async def send_push_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None
    ) -> bool:
        """
        Send a push notification to a specific device
        Automatically uses V1 API if configured, otherwise falls back to Legacy API
        
        Args:
            device_token: FCM device token
            title: Notification title
            body: Notification body/message
            data: Additional data payload
            badge: Badge count for iOS
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not device_token:
            print("⚠️  No device token provided - skipping push notification")
            return False
        
        if self.use_v1_api:
            return await self._send_v1_notification(device_token, title, body, data, badge)
        elif self.fcm_server_key:
            return await self._send_legacy_notification(device_token, title, body, data, badge)
        else:
            print("⚠️  FCM not configured - skipping push notification")
            return False
    
    async def _send_v1_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None
    ) -> bool:
        """Send notification using FCM V1 API (Service Account)"""
        try:
            # Get OAuth2 access token
            access_token = self._get_access_token()
            if not access_token:
                print("✗ Failed to get FCM access token")
                return False
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare V1 API payload
            message = {
                "message": {
                    "token": device_token,
                    "notification": {
                        "title": title,
                        "body": body
                    },
                    "android": {
                        "priority": "high",
                        "notification": {
                            "sound": "default",
                            "notification_priority": "PRIORITY_HIGH"
                        }
                    },
                    "apns": {
                        "payload": {
                            "aps": {
                                "sound": "default",
                                "badge": badge or 1
                            }
                        }
                    }
                }
            }
            
            # Add custom data if provided
            if data:
                # Convert all values to strings for FCM
                message["message"]["data"] = {k: str(v) for k, v in data.items()}
            
            # Send request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_v1_url,
                    headers=headers,
                    json=message,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print(f"✓ Push notification sent (V1 API)")
                    return True
                else:
                    print(f"✗ FCM V1 failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"✗ Error sending V1 push notification: {e}")
            return False
    
    async def _send_legacy_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None
    ) -> bool:
        """Send notification using Legacy API (Server Key)"""
        try:
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare legacy API payload
            payload = {
                "to": device_token,
                "notification": {
                    "title": title,
                    "body": body,
                    "sound": "default",
                    "badge": badge or 1
                },
                "priority": "high"
            }
            
            # Add custom data if provided
            if data:
                payload["data"] = data
            
            # Send request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_legacy_url,
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", 0) > 0:
                        print(f"✓ Push notification sent (Legacy API)")
                        return True
                    else:
                        print(f"✗ FCM Legacy returned failure: {result}")
                        return False
                else:
                    print(f"✗ FCM Legacy failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"✗ Error sending Legacy push notification: {e}")
            return False
    
    async def send_push_to_multiple(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Send push notification to multiple devices
        
        Returns:
            Dict with 'success' and 'failed' counts
        """
        if not self.fcm_server_key:
            print("⚠️  FCM_SERVER_KEY not configured - skipping push notifications")
            return {"success": 0, "failed": 0}
        
        success_count = 0
        failed_count = 0
        
        for token in device_tokens:
            result = await self.send_push_notification(
                device_token=token,
                title=title,
                body=body,
                data=data,
                badge=badge
            )
            if result:
                success_count += 1
            else:
                failed_count += 1
        
        print(f"Push notifications: {success_count} sent, {failed_count} failed")
        return {"success": success_count, "failed": failed_count}
    
    async def send_transaction_notification(
        self,
        device_token: str,
        notification_type: str,
        amount: str,
        currency: str,
        from_to_display: str,
        transaction_id: Optional[int] = None,
        unread_count: int = 1
    ) -> bool:
        """
        Send a transaction-specific push notification
        
        Args:
            device_token: FCM device token
            notification_type: 'sent', 'received', 'confirmed', 'failed'
            amount: Amount with currency symbol
            currency: User's preferred currency
            from_to_display: DARI address or wallet address of sender/receiver
            transaction_id: ID of the transaction
            unread_count: Badge count for unread notifications
        """
        # Generate title and body based on type
        if notification_type == "sent":
            title = "Transaction Sent"
            body = f"You sent {amount} {currency} to {from_to_display}"
        elif notification_type == "received":
            title = "Payment Received"
            body = f"You received {amount} {currency} from {from_to_display}"
        elif notification_type == "confirmed":
            title = "Transaction Confirmed"
            body = f"Your transaction of {amount} {currency} has been confirmed"
        elif notification_type == "failed":
            title = "Transaction Failed"
            body = f"Your transaction of {amount} {currency} has failed"
        else:
            title = "Transaction Update"
            body = f"Transaction update for {amount} {currency}"
        
        # Prepare data payload
        data = {
            "type": "transaction",
            "notification_type": notification_type,
            "amount": amount,
            "currency": currency,
            "from_to": from_to_display
        }
        
        if transaction_id:
            data["transaction_id"] = str(transaction_id)
        
        return await self.send_push_notification(
            device_token=device_token,
            title=title,
            body=body,
            data=data,
            badge=unread_count
        )


# Global instance
firebase_service = FirebaseService()
