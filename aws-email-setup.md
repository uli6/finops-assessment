# AWS Email Configuration Setup Guide

This guide will help you configure email functionality for your FinOps Assessment platform on AWS EC2.

## Problem
You're seeing the error: `Email configuration not found. Skipping email send.`

This happens because the email environment variables are not set on your AWS EC2 instance.

## Solution

### Step 1: Upload Updated Files
First, upload the updated files to your EC2 instance:

```bash
# From your local machine, upload the updated files
scp -i your-key.pem services/email_service.py ubuntu@your-ec2-ip:/home/ubuntu/finops-assessment/services/
scp -i your-key.pem app.py ubuntu@your-ec2-ip:/home/ubuntu/finops-assessment/
scp -i your-key.pem setup_email_config.sh ubuntu@your-ec2-ip:/home/ubuntu/finops-assessment/
scp -i your-key.pem test_email.py ubuntu@your-ec2-ip:/home/ubuntu/finops-assessment/
```

### Step 2: SSH into Your EC2 Instance
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### Step 3: Navigate to Your Application Directory
```bash
cd /home/ubuntu/finops-assessment
```

### Step 4: Make the Setup Script Executable
```bash
chmod +x setup_email_config.sh
```

### Step 5: Run the Email Configuration Script
```bash
./setup_email_config.sh
```

This script will:
- Prompt you for email configuration details
- Create a `.env` file with your settings
- Export environment variables for the current session
- Add environment variables to `~/.bashrc` for persistence

### Step 6: Configure Email Provider (Gmail Example)

#### For Gmail:
1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Use the 16-character password as `EMAIL_PASS`

#### For Other Email Providers:
- **Outlook/Hotmail**: Use `smtp-mail.outlook.com` port 587
- **Yahoo**: Use `smtp.mail.yahoo.com` port 587
- **Corporate email**: Check with your IT department for SMTP settings

### Step 7: Set Your Domain URL
When prompted for `BASE_URL`, enter your DuckDNS domain:
```
https://your-domain.duckdns.org
```

### Step 8: Restart Your Application
```bash
sudo systemctl restart finops-assessment
```

### Step 9: Test Email Configuration
```bash
python3 test_email.py
```

This will:
- Check if environment variables are set correctly
- Send a test email to verify functionality

### Step 10: Check Application Logs
```bash
sudo journalctl -u finops-assessment -f
```

## Environment Variables Explained

| Variable | Description | Example |
|----------|-------------|---------|
| `EMAIL_USER` | Your email address | `your-app@gmail.com` |
| `EMAIL_PASS` | Email password/app password | `abcd efgh ijkl mnop` |
| `SMTP_SERVER` | SMTP server address | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port number | `587` |
| `BASE_URL` | Your domain URL | `https://your-domain.duckdns.org` |

## Troubleshooting

### Common Issues:

1. **"Email configuration not found"**
   - Environment variables not set
   - Run `./setup_email_config.sh` again

2. **"Authentication failed"**
   - Wrong email/password
   - For Gmail: Use app password, not regular password
   - Check 2FA is enabled

3. **"Connection refused"**
   - Wrong SMTP server/port
   - Check firewall settings
   - Verify email provider settings

4. **"SSL/TLS error"**
   - Try port 587 with STARTTLS
   - Or port 465 with SSL

### Manual Environment Variable Setup

If the script doesn't work, set variables manually:

```bash
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASS="your-app-password"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export BASE_URL="https://your-domain.duckdns.org"
export FLASK_ENV="production"
export AWS_ENV="1"
```

### Check Current Environment Variables
```bash
env | grep -E "(EMAIL|SMTP|BASE_URL)"
```

## Security Notes

1. **Never commit `.env` files** to version control
2. **Use app passwords** instead of regular passwords
3. **Enable 2FA** on your email account
4. **Use HTTPS** for your domain URL

## Testing Email Functionality

1. **Register a new user** on your website
2. **Check email inbox** for confirmation link
3. **Click the confirmation link**
4. **Try logging in** with magic link

## Support

If you continue to have issues:

1. Check the application logs: `sudo journalctl -u finops-assessment -f`
2. Test email manually: `python3 test_email.py`
3. Verify environment variables: `env | grep EMAIL`
4. Restart the application: `sudo systemctl restart finops-assessment` 