#!/usr/bin/env python3
"""
Gmail-specific test script to debug authentication issues
"""

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gmail_connection():
    """Test Gmail SMTP connection with detailed error reporting"""
    print("=== Gmail SMTP Connection Test ===")
    print()
    
    # Get configuration
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    
    print(f"Email User: {email_user}")
    print(f"Email Pass: {'*' * len(email_pass) if email_pass else 'Not set'}")
    print()
    
    if not email_user or not email_pass:
        print("❌ Email configuration incomplete!")
        return False
    
    # Test SMTP connection
    try:
        print("1. Testing SMTP connection...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        print("✅ Connected to smtp.gmail.com:587")
        
        print("2. Starting TLS...")
        server.starttls()
        print("✅ TLS started successfully")
        
        print("3. Attempting authentication...")
        server.login(email_user, email_pass)
        print("✅ Authentication successful!")
        
        print("4. Testing email send...")
        msg = MIMEText("This is a test email from FinOps Assessment", 'plain')
        msg['Subject'] = 'Gmail Test - FinOps Assessment'
        msg['From'] = email_user
        msg['To'] = email_user  # Send to yourself for testing
        
        server.send_message(msg)
        print("✅ Test email sent successfully!")
        
        server.quit()
        print()
        print("🎉 All tests passed! Your Gmail configuration is working correctly.")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print()
        print("This usually means:")
        print("1. You're using your regular password instead of an app password")
        print("2. 2-Factor Authentication is not enabled")
        print("3. The app password is incorrect")
        print()
        print("To fix this:")
        print("1. Enable 2-Factor Authentication on your Google account")
        print("2. Generate an App Password for 'Mail'")
        print("3. Use the 16-character app password (without spaces)")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("Check your internet connection and firewall settings")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_gmail_requirements():
    """Check if Gmail requirements are met"""
    print("=== Gmail Requirements Check ===")
    print()
    
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    
    print("Requirements:")
    print(f"✅ Email address set: {bool(email_user)}")
    print(f"✅ Password set: {bool(email_pass)}")
    
    if email_pass:
        print(f"✅ Password length: {len(email_pass)} characters")
        if len(email_pass) == 16 and ' ' in email_pass:
            print("⚠️  App password detected (contains spaces)")
        elif len(email_pass) == 16:
            print("✅ App password format looks correct")
        else:
            print("⚠️  Password length doesn't match app password format")
    
    print()
    print("Gmail Requirements:")
    print("1. ✅ 2-Factor Authentication enabled")
    print("2. ✅ App Password generated for 'Mail'")
    print("3. ✅ 16-character app password used")
    print("4. ✅ SMTP settings: smtp.gmail.com:587")
    print()

if __name__ == "__main__":
    check_gmail_requirements()
    test_gmail_connection() 