
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from app.core.config import get_settings

settings = get_settings()

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM

    def generate_otp(self, length=6) -> str:
        """Generates a numeric OTP of given length."""
        return ''.join(random.choices(string.digits, k=length))

    def send_otp(self, to_email: str, otp: str) -> bool:
        """
        Sends an OTP to the specified email.
        If SMTP settings are missing, prints to console (Simulated Mode).
        """
        if not self.smtp_server or not self.password:
            print(f"\n[SIMULATED EMAIL] To: {to_email}")
            print(f"[SIMULATED EMAIL] Subject: Your Login OTP")
            print(f"[SIMULATED EMAIL] Body: Your One-Time Password is: {otp}\n")
            return True

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = to_email
            msg['Subject'] = "Resume Generator - Your Login OTP"

            body = f"""
            <html>
                <body>
                    <h2>Login Verification</h2>
                    <p>Your One-Time Password (OTP) is:</p>
                    <h1 style="color: #2563eb; letter-spacing: 5px;">{otp}</h1>
                    <p>This code will expire in 10 minutes.</p>
                </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

email_service = EmailService()
