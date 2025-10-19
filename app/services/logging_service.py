from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timedelta
import logging

# Simple logging service without database dependencies
logger = logging.getLogger(__name__)


async def log_login_attempt(
    db: AsyncSession,
    user_id: Optional[int],
    ip_address: str,
    user_agent: str,
    successful: bool,
    failure_reason: Optional[str] = None,
    location: Optional[str] = None
) -> None:
    """Log login attempt - simplified version without database logging"""
    try:
        # Log to application logger instead of database
        log_message = f"Login attempt - User ID: {user_id}, IP: {ip_address}, Success: {successful}"
        if failure_reason:
            log_message += f", Reason: {failure_reason}"
        
        if successful:
            logger.info(log_message)
        else:
            logger.warning(log_message)
        
        # Optional: Send email alerts for successful logins
        if user_id and successful:
            from app.crud import user as user_crud
            user = await user_crud.get_user_by_id(db, user_id)
            if user:
                from app.services.email_service import EmailService
                email_service = EmailService()
                
                # Send new login alert (optional)
                try:
                    await email_service.send_new_login_alert(
                        email=user.email,
                        user_name=user.email.split('@')[0],
                        ip_address=ip_address,
                        user_agent=user_agent,
                        location=location or "Unknown",
                        login_time=datetime.utcnow()
                    )
                except Exception as e:
                    logger.error(f"Failed to send login alert email: {e}")
        
    except Exception as e:
        logger.error(f"Error in log_login_attempt: {e}")
