#!/usr/bin/env python3
"""
Test script to verify email configuration
Run this on your AWS EC2 instance to test email functionality
"""

import os
from dotenv import load_dotenv
from services.email_service import send_email

# Load environment variables
load_dotenv()

def test_email_config():
    """Test email configuration"""
    print("=== Email Configuration Test ===")
    print()
    
    # Check environment variables
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = os.getenv('SMTP_PORT', '587')
    base_url = os.getenv('BASE_URL')
    
    print("Environment Variables:")
    print(f"EMAIL_USER: {'✅ Set' if email_user else '❌ Not set'}")
    print(f"EMAIL_PASS: {'✅ Set' if email_pass else '❌ Not set'}")
    print(f"SMTP_SERVER: {smtp_server}")
    print(f"SMTP_PORT: {smtp_port}")
    print(f"BASE_URL: {base_url or '❌ Not set'}")
    print()
    
    if not email_user or not email_pass:
        print("❌ Email configuration incomplete!")
        print("Please run the setup_email_config.sh script to configure email settings.")
        return False
    
    # Test email sending
    print("Testing email functionality...")
    test_email = input("Enter a test email address: ").strip()
    
    if not test_email:
        print("❌ No email address provided")
        return False
    
    subject = "FinOps Assessment - Email Test"
    body = """
    <html>
    <body>
        <h2>Email Test Successful!</h2>
        <p>This is a test email from your FinOps Assessment platform.</p>
        <p>If you received this email, your email configuration is working correctly.</p>
        <br>
        <p>Best regards,<br>FinOps Assessment Team</p>
    </body>
    </html>
    """
    
    print(f"Sending test email to {test_email}...")
    
    try:
        result = send_email(test_email, subject, body)
        if result:
            print("✅ Test email sent successfully!")
            print("Please check your email inbox.")
            return True
        else:
            print("❌ Failed to send test email")
            return False
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        return False

if __name__ == "__main__":
    test_email_config() 