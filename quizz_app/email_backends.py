import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.core.mail.backends.base import BaseEmailBackend
import logging

class SendGridEmailBackend(BaseEmailBackend):
    """
    Sends email via SendGrid Web API (HTTPS). Works on Render even if SMTP is blocked.
    """
    def send_messages(self, email_messages):
        api_key = os.environ.get("SENDGRID_API_KEY")
        if not api_key:
            # Fail loudly in logs (so you know why nothing sends)
            raise RuntimeError("SENDGRID_API_KEY is missing")

        sg = SendGridAPIClient(api_key)
        sent = 0

        for msg in email_messages:
            # Django passes EmailMultiAlternatives sometimes
            to_emails = msg.to
            if not to_emails:
                continue

            # Prefer HTML alternative if it exists
            html_content = None
            if hasattr(msg, "alternatives"):
                for content, mimetype in msg.alternatives:
                    if mimetype == "text/html":
                        html_content = content
                        break

            mail = Mail(
                from_email=msg.from_email,
                to_emails=to_emails,
                subject=msg.subject,
                plain_text_content=msg.body,
                html_content=html_content
            )

            # SendGrid API call
            sg.send(mail)
            sent += 1

        return sent
logger = logging.getLogger("quizfy.mail")
logger.info("Sending password reset email to %s", to_emails)