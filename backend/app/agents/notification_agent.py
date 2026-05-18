import smtplib
from email.message import EmailMessage
import logging
import os

logger = logging.getLogger(__name__)

class NotificationAgent:
    """
    NotificationAgent
    Responsible for sending email notifications to users.
    Integrates with SMTP to deliver real emails or logs for dummy credentials.
    """
    def __init__(self):
        self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", 587))
        self.sender_email = os.environ.get("SMTP_EMAIL", "notify@pharmaagent.com")
        self.sender_password = os.environ.get("SMTP_PASSWORD", "dummy_pass")

    def send_order_confirmation(self, user_email: str, order_id: int, total_price: float):
        msg = EmailMessage()
        msg.set_content(f"Your order #{order_id} has been successfully placed. Total: ₹{total_price:.2f}.")
        msg["Subject"] = f"PharmaAgent AI - Order #{order_id} Confirmation"
        msg["From"] = self.sender_email
        msg["To"] = user_email
        
        logger.info(f"NotificationAgent: Simulating email to {user_email} for order #{order_id}")
        
        try:
            if self.sender_password != "dummy_pass":
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
                logger.info("NotificationAgent: Email sent successfully.")
            else:
                logger.info("NotificationAgent: Skipping real SMTP send (dummy credentials).")
        except Exception as e:
            logger.error(f"NotificationAgent: Failed to send email: {e}")
