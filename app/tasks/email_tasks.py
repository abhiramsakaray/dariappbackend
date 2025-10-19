from celery import Celery
import redis
from app.celery_app import celery_app
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


@celery_app.task
def send_email_notification_task(to_email: str, subject: str, body: str, is_html: bool = True):
    """Celery task to send email notification"""
    import asyncio
    from app.services.otp_service import send_email_notification
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            send_email_notification(to_email, subject, body, is_html)
        )
        return result
    finally:
        loop.close()


@celery_app.task
def send_kyc_approval_notification_task(email: str, name: str):
    """Celery task to send KYC approval notification"""
    import asyncio
    from app.services.otp_service import send_kyc_approval_notification
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            send_kyc_approval_notification(email, name)
        )
        return result
    finally:
        loop.close()


@celery_app.task
def send_kyc_rejection_notification_task(email: str, name: str, reason: str):
    """Celery task to send KYC rejection notification"""
    import asyncio
    from app.services.otp_service import send_kyc_rejection_notification
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            send_kyc_rejection_notification(email, name, reason)
        )
        return result
    finally:
        loop.close()


@celery_app.task
def cleanup_expired_otps():
    """Clean up expired OTP codes from Redis"""
    try:
        # Get all OTP keys
        otp_keys = redis_client.keys("otp:*")
        cleaned_count = 0
        
        for key in otp_keys:
            ttl = redis_client.ttl(key)
            if ttl == -1:  # No expiration set (shouldn't happen)
                redis_client.delete(key)
                cleaned_count += 1
            elif ttl == -2:  # Key doesn't exist (already expired)
                cleaned_count += 1
        
        print(f"Cleaned up {cleaned_count} expired OTP keys")
        return cleaned_count
    except Exception as e:
        print(f"Error cleaning up OTPs: {e}")
        return 0


@celery_app.task
def send_login_notification_task(email: str, name: str, login_time: str, ip_address: str, user_agent: str):
    """Celery task to send login notification"""
    import asyncio
    from app.services.otp_service import send_email_notification
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        subject = "🔐 New Login to Your DARI Wallet Account"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🔐 DARI Wallet</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Login Notification</p>
            </div>
            
            <div style="background: #ffffff; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-top: 0;">Hello {name}!</h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 16px;">
                        <strong>We detected a new login to your DARI Wallet account.</strong>
                    </p>
                </div>
                
                <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1976d2;">📊 Login Details:</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li><strong>Time:</strong> {login_time}</li>
                        <li><strong>IP Address:</strong> {ip_address}</li>
                        <li><strong>Device:</strong> {user_agent[:100]}{'...' if len(user_agent) > 100 else ''}</li>
                    </ul>
                </div>
                
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <h3 style="margin-top: 0; color: #856404;">🛡️ Security Notice:</h3>
                    <p style="margin: 0;">
                        If this was you, no action is needed. If you don't recognize this login, please:
                    </p>
                    <ul style="margin: 10px 0 0 20px; padding-left: 0;">
                        <li>Change your password immediately</li>
                        <li>Contact our support team</li>
                        <li>Review your account activity</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; font-size: 14px;">
                        This is an automated security notification. Please do not reply to this email.
                    </p>
                </div>
                
                <div style="text-align: center; border-top: 1px solid #eee; padding-top: 20px;">
                    <p style="color: #666; margin: 0;">
                        Best regards,<br>
                        <strong>DARI Wallet Security Team</strong>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        result = loop.run_until_complete(
            send_email_notification(email, subject, body, True)
        )
        return result
    finally:
        loop.close()
