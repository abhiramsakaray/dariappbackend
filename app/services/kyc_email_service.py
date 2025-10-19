import smtplib
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings


class KYCEmailService:
    """Service for sending KYC-related email notifications"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def _send_email_sync(self, to_email: str, subject: str, message: str) -> bool:
        """Send email synchronously"""
        try:
            # Create email message
            email_text = f"""\
From: {self.from_email}
To: {to_email}
Subject: {subject}
Content-Type: text/html; charset=utf-8

{message}
"""
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_email, [to_email], email_text.encode('utf-8'))
            
            return True
        except Exception as e:
            print(f"Failed to send KYC email to {to_email}: {e}")
            return False
    
    async def send_email_async(self, to_email: str, subject: str, message: str) -> bool:
        """Send email asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._send_email_sync, 
            to_email, 
            subject, 
            message
        )
    
    async def send_kyc_approved_email(self, user_email: str, user_name: str) -> bool:
        """Send KYC approval notification"""
        subject = "🎉 KYC Verification Approved - DARI Wallet"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>KYC Approved</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #28a745;">🎉 KYC Verification Approved!</h1>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <p>Dear {user_name},</p>
                    
                    <p><strong>Congratulations!</strong> Your KYC (Know Your Customer) verification has been successfully approved.</p>
                    
                    <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0;">✅ What's Next?</h3>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>You can now create your crypto wallet</li>
                            <li>Start sending and receiving USDC, USDT, and MATIC</li>
                            <li>Access all DARI Wallet features</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 20px;">
                        <a href="http://localhost:8000/docs" 
                           style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Access Your Wallet
                        </a>
                    </p>
                </div>
                
                <div style="border-top: 1px solid #dee2e6; padding-top: 20px; text-align: center; color: #6c757d; font-size: 12px;">
                    <p>This is an automated message from DARI Wallet.<br>
                    If you have any questions, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        KYC Verification Approved - DARI Wallet
        
        Dear {user_name},
        
        Congratulations! Your KYC (Know Your Customer) verification has been successfully approved.
        
        What's Next?
        - You can now create your crypto wallet
        - Start sending and receiving USDC, USDT, and MATIC
        - Access all DARI Wallet features
        
        Visit: http://localhost:8000/docs
        
        This is an automated message from DARI Wallet.
        If you have any questions, please contact our support team.
        """
        
        return await self.send_email_async(user_email, subject, html_content)
    
    async def send_kyc_rejected_email(self, user_email: str, user_name: str, rejection_reason: str) -> bool:
        """Send KYC rejection notification"""
        subject = "❌ KYC Verification Update - DARI Wallet"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>KYC Update Required</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #dc3545;">📋 KYC Verification Update Required</h1>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <p>Dear {user_name},</p>
                    
                    <p>Thank you for submitting your KYC verification documents. After careful review, we need some additional information to complete your verification.</p>
                    
                    <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0;">📝 Reason for Update Request:</h3>
                        <p style="margin: 0; font-weight: bold;">{rejection_reason}</p>
                    </div>
                    
                    <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0;">🔄 Next Steps:</h3>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Review the feedback provided above</li>
                            <li>Update your documents accordingly</li>
                            <li>Resubmit your KYC application</li>
                            <li>Our team will review it within 24-48 hours</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 20px;">
                        <a href="http://localhost:8000/docs" 
                           style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Update KYC Documents
                        </a>
                    </p>
                </div>
                
                <div style="border-top: 1px solid #dee2e6; padding-top: 20px; text-align: center; color: #6c757d; font-size: 12px;">
                    <p>This is an automated message from DARI Wallet.<br>
                    If you have any questions, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        KYC Verification Update Required - DARI Wallet
        
        Dear {user_name},
        
        Thank you for submitting your KYC verification documents. After careful review, we need some additional information to complete your verification.
        
        Reason for Update Request:
        {rejection_reason}
        
        Next Steps:
        - Review the feedback provided above
        - Update your documents accordingly
        - Resubmit your KYC application
        - Our team will review it within 24-48 hours
        
        Visit: http://localhost:8000/docs
        
        This is an automated message from DARI Wallet.
        If you have any questions, please contact our support team.
        """
        
        return await self.send_email_async(user_email, subject, html_content)


# Global instance
kyc_email_service = KYCEmailService()
