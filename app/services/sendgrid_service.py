"""
SendGrid Email Service
Uses SendGrid API to send emails (no SMTP ports required)
Perfect for cloud deployment where SMTP ports are blocked
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.core.config import settings
import asyncio
from typing import Optional


async def send_email_via_sendgrid(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: Optional[str] = None
) -> bool:
    """
    Send email using SendGrid API
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        from_email: Sender email (optional, uses FROM_EMAIL from config)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        if not settings.SENDGRID_API_KEY:
            print("⚠️  SendGrid API key not configured")
            return False
        
        # Use provided from_email or default from settings
        sender = from_email or settings.FROM_EMAIL
        
        # Create SendGrid message
        message = Mail(
            from_email=Email(sender),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        # Send email in thread to avoid blocking
        def _send():
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            return response.status_code in [200, 202]  # 202 = Accepted
        
        result = await asyncio.to_thread(_send)
        
        if result:
            print(f"✅ Email sent successfully to {to_email} via SendGrid")
        else:
            print(f"❌ SendGrid returned unexpected status")
            
        return result
        
    except Exception as e:
        print(f"❌ Error sending email via SendGrid: {e}")
        return False


async def send_otp_email_sendgrid(email: str, otp: str) -> bool:
    """Send OTP email using SendGrid"""
    subject = "DARI - Your OTP Code"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #333; margin-bottom: 20px;">DARI Wallet Verification</h2>
            <p style="color: #666; font-size: 16px;">Your OTP code is:</p>
            <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <span style="font-size: 32px; font-weight: bold; color: #4CAF50; letter-spacing: 5px;">{otp}</span>
            </div>
            <p style="color: #666; font-size: 14px;">This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">
                <strong>Security Note:</strong> Do not share this code with anyone. DARI staff will never ask for your OTP.
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 12px;">
                Best regards,<br>
                <strong>DARI Wallet Team</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    return await send_email_via_sendgrid(email, subject, html_content)


async def send_notification_email_sendgrid(
    to_email: str,
    subject: str,
    html_content: str
) -> bool:
    """Send notification email using SendGrid"""
    return await send_email_via_sendgrid(to_email, subject, html_content)
