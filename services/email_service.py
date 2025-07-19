"""
Email Service for FinOps Assessment Platform
Handles all email-related functionality including confirmation and magic link emails.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email, subject, body):
    """Send email using SMTP or development mode"""
    try:
        email_user = os.getenv('EMAIL_USER')
        email_pass = os.getenv('EMAIL_PASS')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Development mode: if no email credentials, just log the email
        if not email_user or not email_pass:
            print("=" * 60)
            print("📧 DEVELOPMENT MODE - EMAIL NOT SENT")
            print("=" * 60)
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print("Body:")
            print(body)
            print("=" * 60)
            print("💡 To enable real email sending:")
            print("1. Copy env.example to .env")
            print("2. Configure EMAIL_USER and EMAIL_PASS")
            print("3. For Gmail, use App Password (not regular password)")
            print("=" * 60)
            return True  # Return True to not break the flow
        
        msg = MIMEText(body, 'html')
        msg['Subject'] = subject
        msg['From'] = email_user
        msg['To'] = to_email
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_pass)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def send_confirmation_email(email, token):
    """Send email confirmation"""
    # Get base URL from environment or default to localhost
    base_url = os.getenv('BASE_URL', 'http://localhost:5002')
    confirmation_link = f"{base_url}/confirm_email/{token}"
    
    subject = "Confirm Your FinOps Assessment Account"
    body = f"""
    <html>
    <body>
        <h2>Welcome to FinOps Assessment!</h2>
        <p>Thank you for registering. Please click the link below to confirm your email address:</p>
        <p><a href="{confirmation_link}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">Confirm Email</a></p>
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <p>{confirmation_link}</p>
        <p>This link will expire in 24 hours.</p>
        <br>
        <p>Best regards,<br>FinOps Assessment Team</p>
    </body>
    </html>
    """
    
    return send_email(email, subject, body)


def send_magic_link(email, token):
    """Send magic login link"""
    # Get base URL from environment or default to localhost
    base_url = os.getenv('BASE_URL', 'http://localhost:5002')
    login_link = f"{base_url}/magic_login/{token}"
    
    subject = "Your FinOps Assessment Login Link"
    body = f"""
    <html>
    <body>
        <h2>FinOps Assessment Login</h2>
        <p>Click the link below to log in to your account:</p>
        <p><a href="{login_link}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">Login to Account</a></p>
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <p>{login_link}</p>
        <p>This link will expire in 15 minutes for security.</p>
        <br>
        <p>Best regards,<br>FinOps Assessment Team</p>
    </body>
    </html>
    """
    
    return send_email(email, subject, body) 