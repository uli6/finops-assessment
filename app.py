from flask import Flask
import secrets
import os
from models.database import init_db
from routes.auth import auth_bp
from routes.assessment import assessment_bp
from routes.admin import admin_bp
from routes.utils import utils_bp, markdown_filter
from config import DATABASE, UPLOAD_FOLDER, ENCRYPTION_KEY_FILE

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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
    app.run(debug=True)

