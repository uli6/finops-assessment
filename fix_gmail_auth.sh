#!/bin/bash

# Gmail Authentication Fix Script
# This script helps fix common Gmail SMTP authentication issues

echo "=== Gmail Authentication Fix ==="
echo ""

echo "The error you're seeing indicates Gmail authentication issues."
echo "Here's how to fix it:"
echo ""

echo "1. ENABLE 2-FACTOR AUTHENTICATION:"
echo "   - Go to https://myaccount.google.com/"
echo "   - Security → 2-Step Verification"
echo "   - Enable 2-Factor Authentication"
echo ""

echo "2. GENERATE AN APP PASSWORD:"
echo "   - Go to https://myaccount.google.com/"
echo "   - Security → 2-Step Verification → App passwords"
echo "   - Select 'Mail' from the dropdown"
echo "   - Click 'Generate'"
echo "   - Copy the 16-character password (e.g., 'abcd efgh ijkl mnop')"
echo ""

echo "3. UPDATE YOUR EMAIL CONFIGURATION:"
echo ""

read -p "Enter your Gmail address: " gmail_address
read -s -p "Enter the 16-character app password: " app_password
echo ""
read -p "Enter your domain URL (e.g., https://your-domain.duckdns.org): " domain_url

echo ""
echo "=== Updating Configuration ==="

# Create new .env file
cat > .env << EOF
# Email Configuration
EMAIL_USER=$gmail_address
EMAIL_PASS=$app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
BASE_URL=$domain_url

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
AWS_ENV=1
EOF

echo "✅ Created new .env file"

# Export environment variables
export EMAIL_USER="$gmail_address"
export EMAIL_PASS="$app_password"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export BASE_URL="$domain_url"
export FLASK_ENV="production"
export AWS_ENV="1"

echo "✅ Exported environment variables"

# Update .bashrc
echo "" >> ~/.bashrc
echo "# FinOps Assessment Email Configuration (Updated)" >> ~/.bashrc
echo "export EMAIL_USER=\"$gmail_address\"" >> ~/.bashrc
echo "export EMAIL_PASS=\"$app_password\"" >> ~/.bashrc
echo "export SMTP_SERVER=\"smtp.gmail.com\"" >> ~/.bashrc
echo "export SMTP_PORT=\"587\"" >> ~/.bashrc
echo "export BASE_URL=\"$domain_url\"" >> ~/.bashrc
echo "export FLASK_ENV=\"production\"" >> ~/.bashrc
echo "export AWS_ENV=\"1\"" >> ~/.bashrc

echo "✅ Updated ~/.bashrc"

echo ""
echo "=== Testing Configuration ==="
echo "Restarting application..."

sudo systemctl restart finops-assessment

echo "✅ Application restarted"
echo ""
echo "=== Test Email Configuration ==="
echo "Run this command to test:"
echo "python3 test_email.py"
echo ""
echo "=== Common Issues & Solutions ==="
echo ""
echo "❌ Still getting authentication error?"
echo "   - Make sure 2FA is enabled on your Google account"
echo "   - Use the 16-character app password, not your regular password"
echo "   - Don't include spaces in the app password"
echo ""
echo "❌ Getting SSL/TLS errors?"
echo "   - Try port 587 with STARTTLS (current setting)"
echo "   - Or try port 465 with SSL"
echo ""
echo "❌ Getting connection refused?"
echo "   - Check your EC2 security group allows outbound traffic"
echo "   - Verify Gmail SMTP settings"
echo ""
echo "✅ Configuration complete! Test with: python3 test_email.py" 