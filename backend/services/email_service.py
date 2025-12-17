import os
import random
import string
from datetime import datetime, timedelta
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Email configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@minierp.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Mini ERP")

# OTP configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10

def generate_otp() -> str:
    """Generate a random 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))

def get_otp_expiry() -> datetime:
    """Get OTP expiry datetime (10 minutes from now)"""
    from datetime import timezone
    return datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

def is_otp_valid(otp_expires_at: Optional[datetime]) -> bool:
    """Check if OTP is still valid (not expired)"""
    from datetime import timezone
    if not otp_expires_at:
        return False
    # Handle both naive and aware datetimes
    now = datetime.now(timezone.utc)
    if otp_expires_at.tzinfo is None:
        # If naive, assume UTC
        otp_expires_at = otp_expires_at.replace(tzinfo=timezone.utc)
    return now < otp_expires_at

async def send_otp_email(to_email: str, otp_code: str, username: str) -> bool:
    """Send OTP verification email"""
    if not SMTP_USER or not SMTP_PASSWORD:
        # Dev mode - just print OTP
        print(f"[DEV MODE] OTP for {to_email}: {otp_code}")
        return True
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Your Mini ERP Verification Code: {otp_code}"
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg['To'] = to_email

        # Plain text version
        text = f"""
Hello {username},

Your verification code is: {otp_code}

This code will expire in {OTP_EXPIRY_MINUTES} minutes.

If you didn't request this, please ignore this email.

Best regards,
Mini ERP Team
"""

        # HTML version
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .code {{ font-size: 32px; font-weight: bold; color: #16a34a; letter-spacing: 5px; 
                 background: #f0fdf4; padding: 15px 25px; border-radius: 8px; 
                 display: inline-block; margin: 20px 0; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Email Verification</h2>
        <p>Hello <strong>{username}</strong>,</p>
        <p>Your verification code is:</p>
        <div class="code">{otp_code}</div>
        <p>This code will expire in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.</p>
        <p>If you didn't request this, please ignore this email.</p>
        <div class="footer">
            <p>Best regards,<br>Mini ERP Team</p>
        </div>
    </div>
</body>
</html>
"""

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())
        
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
