import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ResendEmailBackend(BaseEmailBackend):
    """
    Custom Django Email Backend for Resend HTTPS API.
    WHY: Railway blocks outbound SMTP ports (25, 465, 587).
         This backend sends email using HTTPS API on port 443, bypassing the block.
    """
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        api_key = getattr(settings, 'RESEND_API_KEY', '').strip()
        if not api_key:
            logger.error("Resend API Key is missing or empty in Django settings.")
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY is not configured.")
            return 0

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        sent_count = 0
        for message in email_messages:
            # Extract HTML alternative if present
            html_content = None
            alternatives = getattr(message, 'alternatives', None)
            if alternatives:
                for alt, mime in alternatives:
                    if mime == 'text/html':
                        html_content = alt
                        break

            # Resend API payload format
            payload = {
                "from": message.from_email,
                "to": message.to,
                "subject": message.subject,
                "text": message.body,
            }
            if html_content:
                payload["html"] = html_content

            try:
                response = requests.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                if response.status_code in [200, 201, 202]:
                    sent_count += 1
                else:
                    logger.error(f"Resend API error: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Failed to send email via Resend API: {str(e)}")
                if not self.fail_silently:
                    raise
        return sent_count
