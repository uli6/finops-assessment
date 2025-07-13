"""
Configuration settings for FinOps Assessment Platform
Centralizes all app configuration and environment variables.
"""

import os
import secrets

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Database Configuration
DATABASE = os.getenv('DATABASE', 'finops_assessment.db')

# File Upload Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Email Configuration
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

# Encryption Configuration
ENCRYPTION_KEY_FILE = os.getenv('ENCRYPTION_KEY_FILE', 'encryption.key')

# Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5002'))

# Public email domains (not allowed for registration)
PUBLIC_EMAIL_DOMAINS = [
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'aol.com', 
    'icloud.com', 'protonmail.com', 'mail.com', 'zoho.com', 'gmx.com', 
    'yandex.com', 'live.com', 'msn.com', 'me.com', 'pm.me', 'fastmail.com'
]

# Assessment Configuration
ASSESSMENT_TIMEOUT = 24 * 60 * 60  # 24 hours in seconds
MAGIC_LINK_TIMEOUT = 15 * 60  # 15 minutes in seconds 