import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from jinja2 import Environment, FileSystemLoader
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from sqlalchemy import select

from app.core.config import settings
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.admin import NotificationChannel, BulkNotificationResponse
from app.crud.admin import admin_crud
from app.core.database import get_db


class AdminNotificationService:
    """Service for handling admin notifications across multiple channels"""
    
    def __init__(self):
        self.subjects = {
            NotificationType.SECURITY_ALERT: "🔒 DARI Security Alert",
            NotificationType.KYC_UPDATE: "📋 DARI KYC Update",
            NotificationType.LOGIN_ALERT: "🔐 DARI Login Alert",
            NotificationType.TRANSACTION_SENT: "💸 DARI Transaction Sent",
            NotificationType.TRANSACTION_RECEIVED: "💰 DARI Transaction Received",
            NotificationType.TRANSACTION_CONFIRMED: "✅ DARI Transaction Confirmed",
            NotificationType.TRANSACTION_FAILED: "❌ DARI Transaction Failed",
            NotificationType.GENERAL: "📢 DARI Notification",
            NotificationType.ANNOUNCEMENT: "📣 DARI Announcement",
            NotificationType.SYSTEM_UPDATE: "🔄 DARI System Update",
            NotificationType.MAINTENANCE: "🛠️ DARI Maintenance Notice",
            NotificationType.ADMIN: "👨‍💼 DARI Admin Message",
            NotificationType.BROADCAST: "📢 DARI Broadcast",
            NotificationType.INFO: "ℹ️ DARI Information",
            NotificationType.NEWS: "📰 DARI News",
            NotificationType.UPDATE: "🔄 DARI Update"
        }
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'email')
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self.logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logo.png')

    async def send_bulk_notifications(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        channels: List[NotificationChannel],
        target_user_ids: List[int],
        admin_id: int
    ) -> BulkNotificationResponse:
        """Send bulk notifications across multiple channels"""
        results = {
            "total_targeted": len(target_user_ids),
            "notifications_sent": 0,
            "failed_sends": 0,
            "channels_used": [channel.value for channel in channels],
            "notification_ids": []
        }

        # Always create in-app notifications
        if NotificationChannel.IN_APP in channels:
            in_app_result = await self._send_in_app_notifications(
                title, message, notification_type, target_user_ids
            )
            results["notifications_sent"] += in_app_result["sent"]
            results["failed_sends"] += in_app_result["failed"]
            results["notification_ids"].extend(in_app_result["notification_ids"])
            
        # Send email notifications if requested
        if NotificationChannel.EMAIL in channels:
            email_result = await self._send_email_notifications(
                title, message, notification_type, target_user_ids, admin_id
            )
            results["notifications_sent"] += email_result["sent"]
            results["failed_sends"] += email_result["failed"]
            
        # SMS notifications (disabled for now)
        if NotificationChannel.SMS in channels:
            # SMS functionality disabled
            # TODO: Implement SMS service integration
            pass

        return BulkNotificationResponse(**results)

    async def _send_in_app_notifications(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        target_user_ids: List[int]
    ) -> Dict[str, Any]:
        """Send in-app notifications"""
        sent = 0
        failed = 0
        notification_ids = []

        async for db in get_db():
            try:
                notifications = await admin_crud.create_bulk_notifications(
                    db, title, message, notification_type, target_user_ids
                )
                sent = len(notifications)
                notification_ids = [n.id for n in notifications]
                
                # Log email sending attempts
                for notification in notifications:
                    try:
                        user_query = await db.execute(
                            select(User).where(User.id == notification.user_id)
                        )
                        user = user_query.scalar_one_or_none()
                        if user:
                            await admin_crud.log_email_sent(
                                db,
                                recipient_email=user.email,
                                subject=f"In-App: {title}",
                                email_type="in_app_notification",
                                status="sent",
                                user_id=user.id
                            )
                    except Exception as e:
                        print(f"Failed to log in-app notification: {e}")
                        
            except Exception as e:
                print(f"Failed to send in-app notifications: {e}")
                failed = len(target_user_ids)
            finally:
                await db.close()

        return {
            "sent": sent,
            "failed": failed,
            "notification_ids": notification_ids
        }

    async def _send_email_notifications(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        target_user_ids: List[int],
        admin_id: int
    ) -> Dict[str, Any]:
        """Send email notifications"""
        sent = 0
        failed = 0

        async for db in get_db():
            try:
                # Get user emails
                user_query = select(User.id, User.email, User.full_name).where(
                    User.id.in_(target_user_ids)
                )
                result = await db.execute(user_query)
                users = result.all()

                for user_id, email, full_name in users:
                    if email:
                        try:
                            success = await self._send_single_email(
                                email, full_name, title, message, notification_type
                            )

                            # Log email attempt
                            await admin_crud.log_email_sent(
                                db,
                                recipient_email=email,
                                subject=self.email_templates[notification_type]["subject"],
                                email_type="admin_notification",
                                status="sent" if success else "failed",
                                user_id=user_id,
                                admin_id=admin_id,
                                error_message=None if success else "SMTP error"
                            )

                            if success:
                                sent += 1
                            else:
                                failed += 1

                        except Exception as e:
                            print(f"Failed to send email to {email}: {e}")
                            failed += 1

                            # Log failed email
                            await admin_crud.log_email_sent(
                                db,
                                recipient_email=email,
                                subject=self.email_templates[notification_type]["subject"],
                                email_type="admin_notification",
                                status="failed",
                                user_id=user_id,
                                admin_id=admin_id,
                                error_message=str(e)
                            )
                    else:
                        failed += 1

            except Exception as e:
                print(f"Failed to process email notifications: {e}")
                failed = len(target_user_ids)
            finally:
                await db.close()

        return {"sent": sent, "failed": failed}

    async def _send_single_email(
        self,
        email: str,
        full_name: str,
        title: str,
        message: str,
        notification_type: NotificationType
    ) -> bool:
        """Send a single email notification"""
        try:
            # Render dari_base.html with Jinja2
            template = self.jinja_env.get_template('dari_base.html')
            year = datetime.now().year
            html = template.render(
                title=title,
                message=message,
                button_url=None,
                button_text=None,
                year=year
            )

            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USERNAME
            msg['To'] = email
            msg['Subject'] = self.subjects.get(notification_type, f"📢 DARI Notification: {title}")

            # Attach HTML body
            msg.attach(MIMEText(html, 'html'))

            # Attach logo as inline image
            if os.path.exists(self.logo_path):
                with open(self.logo_path, 'rb') as f:
                    logo_data = f.read()
                image = MIMEImage(logo_data)
                image.add_header('Content-ID', '<dari_logo>')
                image.add_header('Content-Disposition', 'inline', filename='logo.png')
                msg.attach(image)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")
            return False

    # All emails now use dari_base.html template with logo and consistent style

    def _kyc_update_template(self, name: str, title: str, message: str) -> str:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                <h1>📋 DARI KYC Update</h1>
                <p>Decentralized Address Resolver Interface</p>
            </div>

            <div style="padding: 30px; background-color: #f8f9fa;">
                <h2 style="color: #28a745;">KYC Update: {title}</h2>
                
                <p>Dear {name},</p>

                <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>📋 KYC Information:</strong><br>
                    {message}
                </div>

                <p>For any questions regarding your KYC status, please contact our support team.</p>
                <p>Best regards,<br>The DARI Compliance Team</p>
            </div>

            <div style="background-color: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px;">
                <p>This is an automated message from DARI. Please do not reply to this email.</p>
                <p>&copy; 2025 DARI - Decentralized Address Resolver Interface</p>
            </div>
        </body>
        </html>
        """

    def _login_alert_template(self, name: str, title: str, message: str) -> str:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                <h1>🔐 DARI Login Alert</h1>
                <p>Decentralized Address Resolver Interface</p>
            </div>

            <div style="padding: 30px; background-color: #f8f9fa;">
                <h2 style="color: #17a2b8;">Login Alert: {title}</h2>
                
                <p>Dear {name},</p>

                <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>🔐 Login Information:</strong><br>
                    {message}
                </div>

                <p>If this was not you, please secure your account immediately and contact support.</p>
                <p>Best regards,<br>The DARI Security Team</p>
            </div>

            <div style="background-color: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px;">
                <p>This is an automated security alert from DARI. Please do not reply to this email.</p>
                <p>&copy; 2025 DARI - Decentralized Address Resolver Interface</p>
            </div>
        </body>
        </html>
        """

    def _transaction_template(self, name: str, title: str, message: str) -> str:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                <h1>💰 DARI Transaction Update</h1>
                <p>Decentralized Address Resolver Interface</p>
            </div>

            <div style="padding: 30px; background-color: #f8f9fa;">
                <h2 style="color: #007bff;">Transaction: {title}</h2>
                
                <p>Dear {name},</p>

                <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>💰 Transaction Details:</strong><br>
                    {message}
                </div>

                <p>You can view full transaction details in your DARI dashboard.</p>
                <p>Best regards,<br>The DARI Team</p>
            </div>

            <div style="background-color: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px;">
                <p>This is an automated message from DARI. Please do not reply to this email.</p>
                <p>&copy; 2025 DARI - Decentralized Address Resolver Interface</p>
            </div>
        </body>
        </html>
        """

    def _default_template(self, name: str, title: str, message: str) -> str:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                <h1>📢 DARI Notification</h1>
                <p>Decentralized Address Resolver Interface</p>
            </div>

            <div style="padding: 30px; background-color: #f8f9fa;">
                <h2 style="color: #007bff;">{title}</h2>
                
                <p>Dear {name},</p>

                <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    {message}
                </div>

                <p>Best regards,<br>The DARI Team</p>
            </div>

            <div style="background-color: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px;">
                <p>This is an automated message from DARI. Please do not reply to this email.</p>
                <p>&copy; 2025 DARI - Decentralized Address Resolver Interface</p>
            </div>
        </body>
        </html>
        """


# Global instance
admin_notification_service = AdminNotificationService()