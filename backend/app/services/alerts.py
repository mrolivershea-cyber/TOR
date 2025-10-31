"""
Alert Service - Email and Telegram notifications
"""
import logging
import aiosmtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertService:
    """Service for sending alerts via email and Telegram"""
    
    async def send_alert(self, subject: str, message: str, severity: str = "info"):
        """Send alert through all enabled channels"""
        if settings.ALERT_EMAIL_ENABLED:
            await self.send_email_alert(subject, message)
        
        if settings.ALERT_TELEGRAM_ENABLED:
            await self.send_telegram_alert(subject, message, severity)
    
    async def send_email_alert(self, subject: str, message: str):
        """Send alert via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.ALERT_EMAIL_FROM
            msg['To'] = settings.ALERT_EMAIL_TO
            msg['Subject'] = f"[{settings.APP_NAME}] {subject}"
            
            body = f"""
            <html>
            <body>
            <h2>{subject}</h2>
            <p>{message}</p>
            <hr>
            <p><small>Sent from {settings.APP_NAME}</small></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            async with aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=settings.SMTP_TLS
            ) as smtp:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                await smtp.send_message(msg)
            
            logger.info(f"Email alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def send_telegram_alert(self, subject: str, message: str, severity: str = "info"):
        """Send alert via Telegram"""
        try:
            # Emoji based on severity
            emoji_map = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "critical": "🚨"
            }
            emoji = emoji_map.get(severity, "ℹ️")
            
            text = f"{emoji} *{subject}*\n\n{message}\n\n_From {settings.APP_NAME}_"
            
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": settings.TELEGRAM_CHAT_ID,
                        "text": text,
                        "parse_mode": "Markdown"
                    }
                )
                response.raise_for_status()
            
            logger.info(f"Telegram alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    async def alert_nodes_down(self, down_count: int, total_count: int):
        """Alert when too many nodes are down"""
        percentage = (down_count / total_count) * 100 if total_count > 0 else 0
        
        if percentage >= (settings.ALERT_NODE_DOWN_THRESHOLD * 100):
            await self.send_alert(
                "High Node Failure Rate",
                f"{down_count} out of {total_count} Tor nodes are down ({percentage:.1f}%)",
                severity="error"
            )
    
    async def alert_tls_expiry(self, days_remaining: int):
        """Alert when TLS certificate is expiring"""
        if days_remaining <= settings.ALERT_TLS_EXPIRY_DAYS:
            await self.send_alert(
                "TLS Certificate Expiring Soon",
                f"TLS certificate will expire in {days_remaining} days",
                severity="warning"
            )
    
    async def alert_brute_force(self, ip: str, username: str, attempts: int):
        """Alert on brute force attempts"""
        await self.send_alert(
            "Brute Force Detected",
            f"Multiple failed login attempts detected from IP {ip} for user {username} ({attempts} attempts)",
            severity="warning"
        )
