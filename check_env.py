#!/usr/bin/env python3
"""
Environment Variables Check Script
Verifies that .env file is being loaded correctly.
"""

import os
from dotenv import load_dotenv

def check_environment():
    """Check environment variables"""
    print("🔍 Environment Variables Check")
    print("=" * 50)
    
    # Load .env file
    load_dotenv()
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("❌ .env file not found")
        return
    
    # Check email variables
    email_vars = {
        'EMAIL_USER': os.getenv('EMAIL_USER'),
        'EMAIL_PASS': os.getenv('EMAIL_PASS'),
        'SMTP_SERVER': os.getenv('SMTP_SERVER'),
        'SMTP_PORT': os.getenv('SMTP_PORT')
    }
    
    print("\n📧 Email Configuration:")
    print("-" * 30)
    
    all_set = True
    for var, value in email_vars.items():
        if value:
            # Mask password for security
            if var == 'EMAIL_PASS':
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '****'
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    print(f"\n📋 Summary:")
    if all_set:
        print("✅ All email variables are configured")
        print("💡 Real email sending should be enabled")
    else:
        print("❌ Some email variables are missing")
        print("💡 Application will run in development mode")
    
    # Check other important variables
    print(f"\n🔧 Other Variables:")
    print("-" * 30)
    
    other_vars = {
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'FLASK_DEBUG': os.getenv('FLASK_DEBUG'),
        'BASE_URL': os.getenv('BASE_URL'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }
    
    for var, value in other_vars.items():
        if value:
            if var == 'SECRET_KEY':
                masked_value = value[:8] + '...' if len(value) > 8 else '****'
                print(f"✅ {var}: {masked_value}")
            elif var == 'OPENAI_API_KEY':
                masked_value = value[:8] + '...' if len(value) > 8 else '****'
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: Not set")

if __name__ == '__main__':
    check_environment() 