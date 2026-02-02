"""
Custom SendGrid email backend with debug logging
"""
import logging
from sendgrid_backend import SendgridBackend as OriginalSendgridBackend

logger = logging.getLogger(__name__)


class SendgridBackend(OriginalSendgridBackend):
    """SendGrid backend with detailed logging"""
    
    def send_messages(self, email_messages):
        """Send messages and log the results"""
        if not email_messages:
            return 0
        
        logger.info(f"[SENDGRID] Attempting to send {len(email_messages)} message(s)")
        
        for msg in email_messages:
            logger.info(f"[SENDGRID] Subject: {msg.subject}")
            logger.info(f"[SENDGRID] From: {msg.from_email}")
            logger.info(f"[SENDGRID] To: {msg.to}")
        
        try:
            result = super().send_messages(email_messages)
            logger.info(f"[SENDGRID] Successfully sent {result} message(s)")
            return result
        except Exception as e:
            logger.error(f"[SENDGRID] Error: {type(e).__name__}: {e}")
            raise
