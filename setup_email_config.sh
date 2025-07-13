#!/bin/bash

# Email Configuration Setup Script for FinOps Assessment Platform
# Run this script on your AWS EC2 instance to configure email settings

echo "=== FinOps Assessment Email Configuration Setup ==="
echo ""

# Check if running on AWS
if [ -f /sys/hypervisor/uuid ] && [ "$(head -c 3 /sys/hypervisor/uuid)" = "ec2" ]; then
    echo "✅ Detected AWS EC2 environment"
else
    echo "⚠️  Not running on AWS EC2 - this script is designed for AWS deployment"
fi

echo ""
echo "This script will help you configure email settings for your FinOps Assessment platform."
echo ""

# Get current environment variables
echo "Current email configuration:"
echo "EMAIL_USER: ${EMAIL_USER:-'Not set'}"
echo "EMAIL_PASS: ${EMAIL_PASS:-'Not set'}"
echo "SMTP_SERVER: ${SMTP_SERVER:-'smtp.gmail.com'}"
echo "SMTP_PORT: ${SMTP_PORT:-'587'}"
echo "BASE_URL: ${BASE_URL:-'Not set'}"
echo ""

# Prompt for email configuration
echo "Please provide your email configuration:"
echo ""

read -p "Enter your email address (e.g., your-app@gmail.com): " email_user
read -s -p "Enter your email password/app password: " email_pass
echo ""
read -p "Enter SMTP server (default: smtp.gmail.com): " smtp_server
smtp_server=${smtp_server:-smtp.gmail.com}
read -p "Enter SMTP port (default: 587): " smtp_port
smtp_port=${smtp_port:-587}
read -p "Enter your domain URL (e.g., https://your-domain.duckdns.org): " base_url

echo ""
echo "=== Configuration Summary ==="
echo "Email: $email_user"
echo "SMTP Server: $smtp_server"
echo "SMTP Port: $smtp_port"
echo "Base URL: $base_url"
echo ""

read -p "Is this correct? (y/n): " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    echo ""
    echo "Setting up environment variables..."
    
    # Create .env file
    cat > .env << EOF
# Email Configuration
EMAIL_USER=$email_user
EMAIL_PASS=$email_pass
SMTP_SERVER=$smtp_server
SMTP_PORT=$smtp_port
BASE_URL=$base_url

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
AWS_ENV=1
EOF

    echo "✅ Created .env file with email configuration"
    
    # Export environment variables for current session
    export EMAIL_USER="$email_user"
    export EMAIL_PASS="$email_pass"
    export SMTP_SERVER="$smtp_server"
    export SMTP_PORT="$smtp_port"
    export BASE_URL="$base_url"
    export FLASK_ENV="production"
    export AWS_ENV="1"
    
    echo "✅ Environment variables exported for current session"
    
    # Add to .bashrc for persistence
    echo "" >> ~/.bashrc
    echo "# FinOps Assessment Email Configuration" >> ~/.bashrc
    echo "export EMAIL_USER=\"$email_user\"" >> ~/.bashrc
    echo "export EMAIL_PASS=\"$email_pass\"" >> ~/.bashrc
    echo "export SMTP_SERVER=\"$smtp_server\"" >> ~/.bashrc
    echo "export SMTP_PORT=\"$smtp_port\"" >> ~/.bashrc
    echo "export BASE_URL=\"$base_url\"" >> ~/.bashrc
    echo "export FLASK_ENV=\"production\"" >> ~/.bashrc
    echo "export AWS_ENV=\"1\"" >> ~/.bashrc
    
    echo "✅ Added environment variables to ~/.bashrc for persistence"
    
    echo ""
    echo "=== Next Steps ==="
    echo "1. Restart your Flask application:"
    echo "   sudo systemctl restart finops-assessment"
    echo ""
    echo "2. Check the application logs:"
    echo "   sudo journalctl -u finops-assessment -f"
    echo ""
    echo "3. Test email functionality by registering a new user"
    echo ""
    echo "=== Gmail Setup Instructions ==="
    echo "If using Gmail, make sure to:"
    echo "1. Enable 2-Factor Authentication"
    echo "2. Generate an App Password"
    echo "3. Use the 16-character app password as EMAIL_PASS"
    echo ""
    
else
    echo "Configuration cancelled."
fi 