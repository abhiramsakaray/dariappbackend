import redis
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import string

from app.core.config import settings

# Import SendGrid service
try:
    from app.services.sendgrid_service import send_otp_email_sendgrid, send_notification_email_sendgrid
    SENDGRID_AVAILABLE = True
except ImportError:
    print("⚠️  SendGrid not available - install: pip install sendgrid")
    SENDGRID_AVAILABLE = False

# Redis client for OTP storage - with fallback
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
    REDIS_AVAILABLE = True
    print("✅ Redis connected for OTP storage")
except Exception as e:
    print(f"⚠️  Redis not available for OTP storage: {e}")
    print("💡 Using in-memory fallback (development only)")
    redis_client = None
    REDIS_AVAILABLE = False

# In-memory fallback for OTP storage (development only)
_otp_memory_store = {}


def _cleanup_expired_otps():
    """Clean up expired OTPs from memory storage"""
    current_time = datetime.now()
    expired_keys = [
        key for key, value in _otp_memory_store.items()
        if value['expires_at'] < current_time
    ]
    for key in expired_keys:
        del _otp_memory_store[key]


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


async def send_email_otp(email: str, otp: str) -> bool:
    """Send OTP via email - Uses SendGrid if available, falls back to SMTP"""
    
    # Try SendGrid first (recommended for cloud deployment)
    if settings.USE_SENDGRID and SENDGRID_AVAILABLE and settings.SENDGRID_API_KEY:
        try:
            print(f"📧 Attempting to send OTP via SendGrid to {email}...")
            result = await send_otp_email_sendgrid(email, otp)
            if result:
                return True
            else:
                print("⚠️  SendGrid failed, falling back to SMTP...")
        except Exception as e:
            print(f"⚠️  SendGrid error: {e}, falling back to SMTP...")
    
    # Fallback to SMTP (for local development or if SendGrid fails)
    try:
        print(f"📧 Attempting to send OTP via SMTP to {email}...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = "DARI - Your OTP Code"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>DARI Verification</h2>
            <p>Your OTP code is: <strong>{otp}</strong></p>
            <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
            <p>Do not share this code with anyone.</p>
            <br>
            <p>Best regards,<br>DARI Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Use SSL or TLS based on configuration
        if settings.SMTP_USE_SSL:
            # Port 465 - SSL
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
        else:
            # Port 587 - TLS (STARTTLS)
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
            if settings.SMTP_USE_TLS:
                server.starttls()
        
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.FROM_EMAIL, email, text)
        server.quit()
        
        print(f"✅ OTP sent successfully via SMTP to {email}")
        return True
    except TimeoutError as e:
        print(f"❌ Timeout sending email OTP: {e}")
        return False
    except Exception as e:
        print(f"❌ Error sending email OTP: {e}")
        return False


async def send_sms_otp(phone: str, otp: str) -> bool:
    """Send OTP via SMS (Twilio)"""
    try:
        if not settings.OTP_SMS_ENABLED:
            return False
            
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=f"Your DARI OTP code is: {otp}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes.",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )
        
        return True
    except Exception as e:
        print(f"Error sending SMS OTP: {e}")
        return False


async def send_otp(email: str, phone: Optional[str] = None) -> bool:
    """Send OTP to email and/or phone"""
    otp = generate_otp()
    
    # Store OTP with expiration
    otp_key = f"otp:{email}"
    if REDIS_AVAILABLE:
        redis_client.setex(
            otp_key, 
            timedelta(minutes=settings.OTP_EXPIRE_MINUTES), 
            otp
        )
    else:
        # Use in-memory storage as fallback
        expiry_time = datetime.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        _otp_memory_store[otp_key] = {
            'otp': otp,
            'expires_at': expiry_time
        }
        # Clean up expired OTPs from memory
        _cleanup_expired_otps()
    
    # Send via email
    email_sent = False
    if settings.OTP_EMAIL_ENABLED:
        email_sent = await send_email_otp(email, otp)
    
    # Send via SMS if phone provided
    sms_sent = False
    if phone and settings.OTP_SMS_ENABLED:
        sms_sent = await send_sms_otp(phone, otp)
    
    return email_sent or sms_sent


async def verify_otp_code(email: str, otp: str) -> bool:
    """Verify OTP code"""
    try:
        otp_key = f"otp:{email}"
        stored_otp = None
        
        if REDIS_AVAILABLE:
            stored_otp = redis_client.get(otp_key)
        else:
            # Use in-memory storage
            _cleanup_expired_otps()
            if otp_key in _otp_memory_store:
                stored_data = _otp_memory_store[otp_key]
                if stored_data['expires_at'] > datetime.now():
                    stored_otp = stored_data['otp']
                else:
                    # Expired, remove it
                    del _otp_memory_store[otp_key]
        
        if not stored_otp:
            return False
        
        if stored_otp == otp:
            # Delete OTP after successful verification
            if REDIS_AVAILABLE:
                redis_client.delete(otp_key)
            else:
                _otp_memory_store.pop(otp_key, None)
            return True
        
        return False
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        return False


async def store_registration_data(email: str, registration_data: Dict[str, Any]) -> bool:
    """Store registration data temporarily with OTP"""
    try:
        otp = generate_otp()
        
        # Store registration data with OTP
        reg_key = f"registration:{email}"
        data_to_store = {
            'registration_data': registration_data,
            'otp': otp,
            'expires_at': (datetime.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)).isoformat()
        }
        
        if REDIS_AVAILABLE:
            redis_client.setex(
                reg_key,
                timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
                json.dumps(data_to_store)
            )
        else:
            # Use in-memory storage as fallback
            expiry_time = datetime.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
            _otp_memory_store[reg_key] = {
                'data': data_to_store,
                'expires_at': expiry_time
            }
            _cleanup_expired_otps()
        
        # Send OTP via email
        if settings.OTP_EMAIL_ENABLED:
            email_sent = await send_email_otp(email, otp)
            return email_sent
        
        return False
    except Exception as e:
        print(f"Error storing registration data: {e}")
        return False


async def verify_registration_otp(email: str, otp: str) -> Optional[Dict[str, Any]]:
    """Verify registration OTP and return stored registration data"""
    try:
        reg_key = f"registration:{email}"
        
        if REDIS_AVAILABLE:
            stored_data = redis_client.get(reg_key)
            if stored_data:
                data = json.loads(stored_data)
                if data['otp'] == otp:
                    # Delete the registration data after successful verification
                    redis_client.delete(reg_key)
                    return data['registration_data']
        else:
            # Memory storage fallback
            _cleanup_expired_otps()
            if reg_key in _otp_memory_store:
                stored_entry = _otp_memory_store[reg_key]
                data = stored_entry['data']
                if data['otp'] == otp:
                    # Delete the registration data after successful verification
                    del _otp_memory_store[reg_key]
                    return data['registration_data']
        
        return None
    except Exception as e:
        print(f"Error verifying registration OTP: {e}")
        return None


async def send_login_otp(email: str, user_id: int) -> bool:
    """Send OTP for login (2FA) and store verified session"""
    try:
        otp = generate_otp()
        
        # Store OTP for login with user session data
        login_otp_key = f"login_otp:{email}"
        login_session_data = {
            "otp": otp,
            "user_id": user_id,
            "verified_at": datetime.now().isoformat()
        }
        
        if REDIS_AVAILABLE:
            redis_client.setex(
                login_otp_key,
                timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
                json.dumps(login_session_data)
            )
        else:
            # Use in-memory storage as fallback
            expiry_time = datetime.now() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
            _otp_memory_store[login_otp_key] = {
                'data': login_session_data,
                'expires_at': expiry_time
            }
            _cleanup_expired_otps()
        
        # Send via email
        if settings.OTP_EMAIL_ENABLED:
            email_sent = await send_email_otp(email, otp)
            return email_sent
        
        return False
    except Exception as e:
        print(f"Error sending login OTP: {e}")
        return False


async def verify_login_otp(email: str, otp: str) -> Optional[int]:
    """Verify login OTP and return user_id if valid"""
    try:
        login_otp_key = f"login_otp:{email}"
        
        if REDIS_AVAILABLE:
            stored_data = redis_client.get(login_otp_key)
            if stored_data:
                session_data = json.loads(stored_data)
                if session_data["otp"] == otp:
                    # Delete OTP after successful verification
                    redis_client.delete(login_otp_key)
                    return session_data["user_id"]
        else:
            # Memory storage fallback
            _cleanup_expired_otps()
            if login_otp_key in _otp_memory_store:
                stored_entry = _otp_memory_store[login_otp_key]
                session_data = stored_entry['data']
                if session_data["otp"] == otp:
                    # Delete OTP after successful verification
                    del _otp_memory_store[login_otp_key]
                    return session_data["user_id"]
        
        return None
    except Exception as e:
        print(f"Error verifying login OTP: {e}")
        return None


async def send_email_notification(
    to_email: str, 
    subject: str, 
    body: str, 
    is_html: bool = True
) -> bool:
    """Send email notification - Uses SendGrid if available, falls back to SMTP"""
    
    # Try SendGrid first (recommended for cloud deployment)
    if settings.USE_SENDGRID and SENDGRID_AVAILABLE and settings.SENDGRID_API_KEY:
        try:
            print(f"📧 Attempting to send notification via SendGrid to {to_email}...")
            result = await send_notification_email_sendgrid(to_email, subject, body)
            if result:
                return True
            else:
                print("⚠️  SendGrid failed, falling back to SMTP...")
        except Exception as e:
            print(f"⚠️  SendGrid error: {e}, falling back to SMTP...")
    
    # Fallback to SMTP
    try:
        print(f"📧 Attempting to send notification via SMTP to {to_email}...")
        
        # Run the synchronous SMTP operations in a thread
        def _send_email():
            msg = MIMEMultipart()
            msg['From'] = settings.FROM_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            # Use SSL or TLS based on configuration
            if settings.SMTP_USE_SSL:
                # Port 465 - SSL
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
            else:
                # Port 587 - TLS (STARTTLS)
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
                if settings.SMTP_USE_TLS:
                    server.starttls()
            
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(settings.FROM_EMAIL, to_email, text)
            server.quit()
            return True
        
        # Execute in thread to avoid blocking the async event loop with 30 second timeout
        import asyncio
        result = await asyncio.wait_for(asyncio.to_thread(_send_email), timeout=30.0)
        print(f"✅ Email sent successfully to {to_email}")
        return result
    except asyncio.TimeoutError:
        print(f"❌ Timeout sending email notification to {to_email}")
        return False
    except Exception as e:
        print(f"❌ Error sending email notification: {e}")
        return False


async def send_kyc_approval_notification(email: str, name: str) -> bool:
    """Send KYC approval notification"""
    subject = "DARI - KYC Approved"
    body = f"""
    <html>
    <body>
        <h2>Congratulations {name}!</h2>
        <p>Your KYC verification has been approved.</p>
        <p>Your wallet has been created and you can now start using DARI.</p>
        <br>
        <p>Best regards,<br>DARI Team</p>
    </body>
    </html>
    """
    return await send_email_notification(email, subject, body)


async def send_kyc_rejection_notification(email: str, name: str, reason: str) -> bool:
    """Send KYC rejection notification"""
    subject = "DARI - KYC Verification Required"
    body = f"""
    <html>
    <body>
        <h2>Hello {name},</h2>
        <p>Unfortunately, we could not verify your KYC submission.</p>
        <p><strong>Reason:</strong> {reason}</p>
        <p>Please resubmit your KYC with the correct information.</p>
        <br>
        <p>Best regards,<br>DARI Team</p>
    </body>
    </html>
    """
    return await send_email_notification(email, subject, body)