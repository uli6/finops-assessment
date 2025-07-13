from flask import Flask
import secrets
import os
import logging
from dotenv import load_dotenv
from models.database import init_db
from routes.auth import auth_bp
from routes.assessment import assessment_bp
from routes.admin import admin_bp
from routes.utils import utils_bp, markdown_filter
from config import DATABASE, UPLOAD_FOLDER, ENCRYPTION_KEY_FILE
from flask_talisman import Talisman

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set security headers with Flask-Talisman (permissive CSP for now)
Talisman(app, content_security_policy=None)

# Set secret key securely
if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('AWS_ENV') == '1':
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        logging.warning('WARNING: Running in production without a secure SECRET_KEY! Set SECRET_KEY env variable.')
        secret_key = secrets.token_hex(32)
    app.secret_key = secret_key
else:
    app.secret_key = secrets.token_hex(32)

# Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Environment-based session cookie security
if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('AWS_ENV') == '1':
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
else:
    # Local/dev: allow HTTP for easier testing
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
init_db()

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(assessment_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(utils_bp)

# Register template filters
app.template_filter('markdown')(markdown_filter)

if __name__ == '__main__':
    app.run(debug=True, port=5002)

