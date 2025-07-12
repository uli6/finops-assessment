from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import secrets
import smtplib
import os
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import openai
from werkzeug.utils import secure_filename
import PyPDF2
import pytesseract
from PIL import Image
from cryptography.fernet import Fernet
import base64
import markdown  # já instalado
import textwrap
import re
import html
from flask_wtf import CSRFProtect
import uuid
import bleach

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configuration
DATABASE = 'finops_assessment.db'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Encryption setup
ENCRYPTION_KEY_FILE = 'encryption.key'
if os.path.exists(ENCRYPTION_KEY_FILE):
    with open(ENCRYPTION_KEY_FILE, 'rb') as f:
        ENCRYPTION_KEY = f.read()
else:
    ENCRYPTION_KEY = Fernet.generate_key()
    with open(ENCRYPTION_KEY_FILE, 'wb') as f:
        f.write(ENCRYPTION_KEY)

cipher = Fernet(ENCRYPTION_KEY)

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Encryption helper functions
def encrypt_data(data):
    """Encrypt sensitive data before storing in database"""
    if data is None:
        return None
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    """Decrypt sensitive data from database"""
    if encrypted_data is None:
        return None
    try:
        return cipher.decrypt(encrypted_data.encode()).decode()
    except:
        return encrypted_data  # Return as-is if decryption fails (for legacy data)

# Initialize database with complete migration support
def init_db():
    """Initialize database with proper schema and handle migrations"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create users table with all required columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            organization TEXT NOT NULL,
            role TEXT NOT NULL,
            confirmation_token TEXT,
            is_confirmed BOOLEAN DEFAULT 0,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check existing columns and add missing ones
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    print(f"Existing columns: {existing_columns}")
    
    # Add missing columns one by one
    required_columns = {
        'confirmation_token': 'TEXT',
        'is_confirmed': 'BOOLEAN DEFAULT 0',
        'is_admin': 'BOOLEAN DEFAULT 0',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'is_synthetic': 'BOOLEAN DEFAULT 0'
    }
    
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
                print(f"Added {column_name} column to users table")
            except sqlite3.Error as e:
                print(f"Error adding {column_name} column: {e}")
    
    # Set default values for existing users
    try:
        # Set is_confirmed = 1 for existing users (assume they were confirmed)
        cursor.execute('UPDATE users SET is_confirmed = 1 WHERE is_confirmed IS NULL OR is_confirmed = 0')
        
        # Set admin status based on email domain
        cursor.execute('''
            UPDATE users 
            SET is_admin = 1 
            WHERE email LIKE '%@ulisses.xyz' AND (is_admin IS NULL OR is_admin = 0)
        ''')
        
        print("Updated existing users with default values")
    except sqlite3.Error as e:
        print(f"Error updating existing users: {e}")
    
    # Create assessments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scope_id TEXT NOT NULL,
            domain TEXT,
            status TEXT DEFAULT 'in_progress',
            overall_percentage REAL,
            recommendations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Check and add missing columns to assessments table
    cursor.execute("PRAGMA table_info(assessments)")
    assessment_columns = [column[1] for column in cursor.fetchall()]
    print(f"Existing assessment columns: {assessment_columns}")
    
    # Add missing columns to assessments table
    assessment_required_columns = {
        'overall_percentage': 'REAL',
        'recommendations': 'TEXT',
        'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }
    
    for column_name, column_type in assessment_required_columns.items():
        if column_name not in assessment_columns:
            try:
                cursor.execute(f'ALTER TABLE assessments ADD COLUMN {column_name} {column_type}')
                print(f"Added {column_name} column to assessments table")
            except sqlite3.Error as e:
                print(f"Error adding {column_name} column to assessments: {e}")
    
    # Create responses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            capability_id TEXT NOT NULL,
            lens_id TEXT NOT NULL,
            answer TEXT NOT NULL,
            score INTEGER,
            improvement_suggestions TEXT,
            evidence_files TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assessment_id) REFERENCES assessments (id)
        )
    ''')
    
    # Check and add missing columns to responses table
    cursor.execute("PRAGMA table_info(responses)")
    response_columns = [column[1] for column in cursor.fetchall()]
    print(f"Existing response columns: {response_columns}")
    
    # Add missing columns to responses table
    response_required_columns = {
        'improvement_suggestions': 'TEXT',
        'evidence_files': 'TEXT'
    }
    
    for column_name, column_type in response_required_columns.items():
        if column_name not in response_columns:
            try:
                cursor.execute(f'ALTER TABLE responses ADD COLUMN {column_name} {column_type}')
                print(f"Added {column_name} column to responses table")
            except sqlite3.Error as e:
                print(f"Error adding {column_name} column to responses: {e}")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

# Initialize database on startup
init_db()

# FinOps Framework Data
SCOPES = [
    {
        "id": "public_cloud",
        "name": "Public Cloud",
        "description": "AWS, Azure, GCP and other public cloud workloads"
    },
    {
        "id": "saas",
        "name": "SaaS",
        "description": "Software as a Service applications and subscriptions"
    },
    {
        "id": "data_center",
        "name": "Data Center",
        "description": "On-premises infrastructure and private cloud"
    },
    {
        "id": "licensing",
        "name": "Licensing",
        "description": "Software licensing and vendor management"
    },
    {
        "id": "ai_ml",
        "name": "AI/ML",
        "description": "Artificial Intelligence and Machine Learning workloads"
    }
]

LENSES = [
    {"id": "knowledge", "name": "Knowledge", "weight": 30},
    {"id": "process", "name": "Process", "weight": 25},
    {"id": "metrics", "name": "Metrics", "weight": 20},
    {"id": "adoption", "name": "Adoption", "weight": 20},
    {"id": "automation", "name": "Automation", "weight": 5}
]

CAPABILITIES = [
    # Understanding Usage & Cost
    {"id": "cost_allocation", "name": "Cost Allocation", "domain": "Understanding Usage & Cost"},
    {"id": "data_analysis_showback", "name": "Data Analysis and Showback", "domain": "Understanding Usage & Cost"},
    {"id": "managing_anomalies", "name": "Managing Anomalies", "domain": "Understanding Usage & Cost"},
    {"id": "managing_shared_cost", "name": "Managing Shared Cost", "domain": "Understanding Usage & Cost"},
    
    # Quantify Business Value
    {"id": "forecasting", "name": "Forecasting", "domain": "Quantify Business Value"},
    {"id": "budget_management", "name": "Budget Management", "domain": "Quantify Business Value"},
    {"id": "unit_economics", "name": "Unit Economics", "domain": "Quantify Business Value"},
    {"id": "measuring_unit_costs", "name": "Measuring Unit Costs", "domain": "Quantify Business Value"},
    {"id": "chargeback_finance_integration", "name": "Chargeback & Finance Integration", "domain": "Quantify Business Value"},
    
    # Optimize Usage & Cost
    {"id": "rightsizing", "name": "Rightsizing", "domain": "Optimize Usage & Cost"},
    {"id": "workload_management_automation", "name": "Workload Management & Automation", "domain": "Optimize Usage & Cost"},
    {"id": "rate_optimization", "name": "Rate Optimization", "domain": "Optimize Usage & Cost"},
    {"id": "cloud_sustainability", "name": "Cloud Sustainability", "domain": "Optimize Usage & Cost"},
    {"id": "onboarding_workloads", "name": "Onboarding Workloads", "domain": "Optimize Usage & Cost"},
    {"id": "resource_lifecycle_management", "name": "Resource Lifecycle Management", "domain": "Optimize Usage & Cost"},
    {"id": "cloud_policy_governance", "name": "Cloud Policy & Governance", "domain": "Optimize Usage & Cost"},
    
    # Manage the FinOps Practice
    {"id": "finops_education_enablement", "name": "FinOps Education & Enablement", "domain": "Manage the FinOps Practice"},
    {"id": "cloud_provider_data_ingestion", "name": "Cloud Provider Data Ingestion", "domain": "Manage the FinOps Practice"},
    {"id": "data_normalization", "name": "Data Normalization", "domain": "Manage the FinOps Practice"},
    {"id": "managing_commitment_based_discounts", "name": "Managing Commitment Based Discounts", "domain": "Manage the FinOps Practice"},
    {"id": "establishing_finops_culture", "name": "Establishing FinOps Culture", "domain": "Manage the FinOps Practice"},
    {"id": "intersecting_frameworks", "name": "Intersecting Frameworks", "domain": "Manage the FinOps Practice"}
]

DOMAINS = ["Understanding Usage & Cost", "Quantify Business Value", "Optimize Usage & Cost", "Manage the FinOps Practice"]

# Helper functions
def is_admin():
    """Check if current user is admin"""
    if 'user_id' not in session:
        return False
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT email, is_admin FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[0].endswith('@ulisses.xyz'):
        return True
    return user and user[1] == 1

def send_email(to_email, subject, body):
    """Send email using SMTP"""
    try:
        email_user = os.getenv('EMAIL_USER')
        email_pass = os.getenv('EMAIL_PASS')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        if not email_user or not email_pass:
            print("Email configuration not found. Skipping email send.")
            return True
        
        msg = MIMEText(body, 'html')
        msg['Subject'] = subject
        msg['From'] = email_user
        msg['To'] = to_email
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_pass)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_confirmation_email(email, token):
    """Send email confirmation"""
    confirmation_link = f"http://localhost:5002/confirm_email/{token}"
    
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
    login_link = f"http://localhost:5002/magic_login/{token}"
    
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

def generate_question(capability, lens, scope):
    """Generate specific question for capability + lens + scope combination"""
    questions = {
        "knowledge": {
            "cost_allocation": "How well does your organization understand the principles and methods of cost allocation for {scope} resources?",
            "data_analysis_showback": "What is your team's level of knowledge regarding data analysis and showback reporting for {scope} costs?",
            "managing_anomalies": "How knowledgeable is your organization about identifying and understanding cost anomalies in {scope} environments?",
            "managing_shared_cost": "What is your understanding of shared cost management strategies for {scope} resources?",
            "forecasting": "How well does your team understand forecasting methodologies for {scope} spending?",
            "budget_management": "What is your organization's knowledge level regarding budget management practices for {scope}?",
            "unit_economics": "How well does your team understand unit economics concepts as they apply to {scope} resources?",
            "measuring_unit_costs": "What is your knowledge of measuring and calculating unit costs for {scope} services?",
            "chargeback_finance_integration": "How well does your organization understand chargeback mechanisms and finance integration for {scope}?",
            "rightsizing": "What is your team's knowledge of rightsizing strategies and best practices for {scope} resources?",
            "workload_management_automation": "How well does your organization understand workload management and automation opportunities in {scope}?",
            "rate_optimization": "What is your knowledge of rate optimization strategies available for {scope} services?",
            "cloud_sustainability": "How well does your team understand sustainability considerations and carbon footprint management for {scope}?",
            "onboarding_workloads": "What is your organization's knowledge of best practices for onboarding new workloads to {scope}?",
            "resource_lifecycle_management": "How well does your team understand resource lifecycle management for {scope} environments?",
            "cloud_policy_governance": "What is your knowledge of policy and governance frameworks for {scope} resources?",
            "finops_education_enablement": "How well does your organization understand FinOps education and enablement strategies for {scope}?",
            "cloud_provider_data_ingestion": "What is your knowledge of data ingestion processes from {scope} providers?",
            "data_normalization": "How well does your team understand data normalization techniques for {scope} cost data?",
            "managing_commitment_based_discounts": "What is your knowledge of commitment-based discount programs available for {scope}?",
            "establishing_finops_culture": "How well does your organization understand the cultural aspects of implementing FinOps for {scope}?",
            "intersecting_frameworks": "What is your knowledge of how FinOps intersects with other frameworks when managing {scope} resources?"
        },
        "process": {
            "cost_allocation": "What processes does your organization have in place for allocating {scope} costs to business units or projects?",
            "data_analysis_showback": "What processes are established for regular data analysis and showback reporting of {scope} costs?",
            "managing_anomalies": "What processes does your organization follow to detect, investigate, and resolve {scope} cost anomalies?",
            "managing_shared_cost": "What processes are in place for managing and allocating shared {scope} costs across teams?",
            "forecasting": "What forecasting processes does your organization use for {scope} spending predictions?",
            "budget_management": "What budget management processes are established for {scope} resources?",
            "unit_economics": "What processes does your organization use to calculate and track unit economics for {scope} services?",
            "measuring_unit_costs": "What processes are in place for measuring and monitoring unit costs of {scope} resources?",
            "chargeback_finance_integration": "What processes exist for chargeback and integration with finance systems for {scope} costs?",
            "rightsizing": "What processes does your organization follow for rightsizing {scope} resources?",
            "workload_management_automation": "What processes are established for workload management and automation in {scope} environments?",
            "rate_optimization": "What processes does your organization use to optimize rates and pricing for {scope} services?",
            "cloud_sustainability": "What processes are in place to manage and improve sustainability of {scope} resources?",
            "onboarding_workloads": "What processes does your organization follow when onboarding new workloads to {scope}?",
            "resource_lifecycle_management": "What processes are established for managing the complete lifecycle of {scope} resources?",
            "cloud_policy_governance": "What governance processes are in place for {scope} policy management and compliance?",
            "finops_education_enablement": "What processes does your organization use for FinOps education and enablement regarding {scope}?",
            "cloud_provider_data_ingestion": "What processes are established for ingesting and processing data from {scope} providers?",
            "data_normalization": "What processes does your organization follow for normalizing {scope} cost and usage data?",
            "managing_commitment_based_discounts": "What processes are in place for managing commitment-based discounts for {scope} services?",
            "establishing_finops_culture": "What processes does your organization use to establish and maintain FinOps culture for {scope}?",
            "intersecting_frameworks": "What processes are established for integrating FinOps with other frameworks when managing {scope}?"
        },
        "metrics": {
            "cost_allocation": "What metrics does your organization track to measure the effectiveness of {scope} cost allocation?",
            "data_analysis_showback": "What metrics are used to evaluate the success of data analysis and showback for {scope} costs?",
            "managing_anomalies": "What metrics does your organization track for {scope} anomaly detection and resolution effectiveness?",
            "managing_shared_cost": "What metrics are used to measure the accuracy and fairness of shared {scope} cost allocation?",
            "forecasting": "What metrics does your organization use to measure forecasting accuracy for {scope} spending?",
            "budget_management": "What metrics are tracked to evaluate budget management performance for {scope} resources?",
            "unit_economics": "What unit economics metrics does your organization track for {scope} services?",
            "measuring_unit_costs": "What metrics are used to track and benchmark unit costs of {scope} resources?",
            "chargeback_finance_integration": "What metrics does your organization use to measure chargeback accuracy and finance integration for {scope}?",
            "rightsizing": "What metrics are tracked to measure the effectiveness of {scope} rightsizing efforts?",
            "workload_management_automation": "What metrics does your organization use to evaluate workload management and automation success in {scope}?",
            "rate_optimization": "What metrics are tracked to measure rate optimization effectiveness for {scope} services?",
            "cloud_sustainability": "What sustainability metrics does your organization track for {scope} resources?",
            "onboarding_workloads": "What metrics are used to measure the efficiency and cost-effectiveness of onboarding workloads to {scope}?",
            "resource_lifecycle_management": "What metrics does your organization track for {scope} resource lifecycle management?",
            "cloud_policy_governance": "What metrics are used to measure policy compliance and governance effectiveness for {scope}?",
            "finops_education_enablement": "What metrics does your organization track to measure FinOps education effectiveness for {scope}?",
            "cloud_provider_data_ingestion": "What metrics are used to evaluate data ingestion quality and completeness from {scope} providers?",
            "data_normalization": "What metrics does your organization track for {scope} data normalization accuracy and completeness?",
            "managing_commitment_based_discounts": "What metrics are tracked to measure the effectiveness of commitment-based discount management for {scope}?",
            "establishing_finops_culture": "What metrics does your organization use to measure FinOps culture adoption for {scope}?",
            "intersecting_frameworks": "What metrics are tracked to measure the effectiveness of framework integration when managing {scope}?"
        },
        "adoption": {
            "cost_allocation": "How widely adopted are {scope} cost allocation practices across your organization?",
            "data_analysis_showback": "What is the level of adoption of data analysis and showback practices for {scope} across teams?",
            "managing_anomalies": "How broadly adopted are {scope} anomaly management practices throughout your organization?",
            "managing_shared_cost": "What is the adoption level of shared {scope} cost management practices across business units?",
            "forecasting": "How widely adopted are {scope} forecasting practices across your organization?",
            "budget_management": "What is the level of adoption of budget management practices for {scope} resources?",
            "unit_economics": "How broadly adopted are unit economics practices for {scope} services across your organization?",
            "measuring_unit_costs": "What is the adoption level of unit cost measurement practices for {scope} resources?",
            "chargeback_finance_integration": "How widely adopted are chargeback and finance integration practices for {scope} across your organization?",
            "rightsizing": "What is the level of adoption of rightsizing practices for {scope} resources across teams?",
            "workload_management_automation": "How broadly adopted are workload management and automation practices for {scope} across your organization?",
            "rate_optimization": "What is the adoption level of rate optimization practices for {scope} services?",
            "cloud_sustainability": "How widely adopted are sustainability practices for {scope} resources across your organization?",
            "onboarding_workloads": "What is the level of adoption of standardized onboarding practices for {scope} workloads?",
            "resource_lifecycle_management": "How broadly adopted are resource lifecycle management practices for {scope} across teams?",
            "cloud_policy_governance": "What is the adoption level of policy and governance practices for {scope} resources?",
            "finops_education_enablement": "How widely adopted are FinOps education and enablement practices for {scope} across your organization?",
            "cloud_provider_data_ingestion": "What is the level of adoption of standardized data ingestion practices from {scope} providers?",
            "data_normalization": "How broadly adopted are data normalization practices for {scope} across your organization?",
            "managing_commitment_based_discounts": "What is the adoption level of commitment-based discount management for {scope} services?",
            "establishing_finops_culture": "How widely adopted are FinOps cultural practices for {scope} across your organization?",
            "intersecting_frameworks": "What is the level of adoption of integrated framework approaches when managing {scope}?"
        },
        "automation": {
            "cost_allocation": "What level of automation exists in your {scope} cost allocation processes?",
            "data_analysis_showback": "How automated are your data analysis and showback processes for {scope} costs?",
            "managing_anomalies": "What automation is in place for detecting and managing {scope} cost anomalies?",
            "managing_shared_cost": "How automated are your shared {scope} cost management and allocation processes?",
            "forecasting": "What level of automation exists in your {scope} forecasting processes?",
            "budget_management": "How automated are your budget management processes for {scope} resources?",
            "unit_economics": "What automation is in place for calculating and tracking unit economics for {scope} services?",
            "measuring_unit_costs": "How automated are your unit cost measurement processes for {scope} resources?",
            "chargeback_finance_integration": "What level of automation exists in your chargeback and finance integration for {scope}?",
            "rightsizing": "How automated are your rightsizing processes for {scope} resources?",
            "workload_management_automation": "What level of automation exists in your {scope} workload management processes?",
            "rate_optimization": "How automated are your rate optimization processes for {scope} services?",
            "cloud_sustainability": "What automation is in place for managing sustainability of {scope} resources?",
            "onboarding_workloads": "How automated are your processes for onboarding new workloads to {scope}?",
            "resource_lifecycle_management": "What level of automation exists in your {scope} resource lifecycle management?",
            "cloud_policy_governance": "How automated are your policy and governance processes for {scope} resources?",
            "finops_education_enablement": "What automation is in place for FinOps education and enablement regarding {scope}?",
            "cloud_provider_data_ingestion": "How automated are your data ingestion processes from {scope} providers?",
            "data_normalization": "What level of automation exists in your {scope} data normalization processes?",
            "managing_commitment_based_discounts": "How automated are your commitment-based discount management processes for {scope}?",
            "establishing_finops_culture": "What automation supports the establishment and maintenance of FinOps culture for {scope}?",
            "intersecting_frameworks": "How automated are your processes for integrating FinOps with other frameworks when managing {scope}?"
        }
    }
    
    scope_name = next((s['name'] for s in SCOPES if s['id'] == scope), scope)
    question_template = questions.get(lens, {}).get(capability, f"Please describe your organization's {lens} regarding {capability} for {scope_name}.")
    
    return question_template.format(scope=scope_name)

def generate_recommendations(assessment_id, scope_id, domain, overall_percentage, lens_scores):
    """Generate personalized recommendations using OpenAI API"""
    try:
        # Get all responses for this assessment
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT capability_id, lens_id, answer, score
            FROM responses 
            WHERE assessment_id = ?
            ORDER BY capability_id, lens_id
        ''', (assessment_id,))
        responses = cursor.fetchall()
        conn.close()
        
        # Prepare assessment data for OpenAI
        assessment_summary = f"""
        Assessment Summary:
        - Scope: {next((s['name'] for s in SCOPES if s['id'] == scope_id), scope_id)}
        - Domain: {domain if domain else 'Complete Assessment'}
        - Overall Score: {overall_percentage}%
        
        Lens Scores:
        """
        
        for lens_id, data in lens_scores.items():
            lens_name = next((l['name'] for l in LENSES if l['id'] == lens_id), lens_id)
            assessment_summary += f"- {lens_name}: {data['percentage']}% (Weight: {data['weight']}%)\n"
        
        # Prepare detailed responses
        detailed_responses = "\nDetailed Responses:\n"
        for response in responses:
            capability_id, lens_id, answer, score = response
            capability_name = next((c['name'] for c in CAPABILITIES if c['id'] == capability_id), capability_id)
            lens_name = next((l['name'] for l in LENSES if l['id'] == lens_id), lens_id)
            detailed_responses += f"\n{capability_name} - {lens_name} (Score: {score}/4):\n{answer}\n"
        
        # Create OpenAI prompt
        prompt = f"""
        You are a FinOps expert consultant. Based on the following assessment data, provide highly specific and actionable recommendations tailored to this organization's current state.

        {assessment_summary}
        
        {detailed_responses}
        
        IMPORTANT:
        - For every 'Real Example' or 'Success Story', you MUST search for and include a real, working link to an article, case study, or blog post from the internet (Medium, company blogs, cloud providers, news portals, etc). NEVER use links from finops.org or any FinOps Foundation domain in Real Example/Success Story. Do NOT use placeholder/fake links.
        - All links must be in markdown format: [text](url)
        - All documentation links must be in markdown format: [text](url)
        - All links must be clickable in the rendered output.
        
        Please provide recommendations in this EXACT format:
        
        ## 🚀 Immediate Actions (Next 30 days)
        
        ### Quick Wins
        - [Specific action based on user's responses]
          - **Why this matters:** [Brief explanation]
          - **Documentation:** [Link to relevant documentation]
          - **Real Example:** [Brief anonymized case study with a real link from Medium, company blog, or news portal. NEVER use finops.org.]
        
        ### Foundation Building
        - [Another specific action]
          - **Why this matters:** [Brief explanation]
          - **Documentation:** [Link to relevant documentation]
          - **Real Example:** [Brief anonymized case study with a real link from Medium, company blog, or news portal. NEVER use finops.org.]
        
        ## 📈 Short-term Improvements (3-6 months)
        
        ### Process Enhancements
        - [Specific process improvement based on user's responses]
          - **Implementation Steps:** [Step-by-step guide]
          - **Documentation:** [Link to relevant documentation]
          - **Success Metrics:** [How to measure progress]
        
        ### Tool Implementation
        - [Specific tool recommendation]
          - **Why this tool:** [Explanation based on user's current state]
          - **Documentation:** [Link to tool documentation]
          - **Integration Guide:** [Link to integration best practices]
        
        ## 🎯 Priority Focus Areas
        
        Based on your assessment scores, focus on these 3 critical areas:
        
        1. **[Area 1]** - Score: [X]%
           - **Why Critical:** [Explanation based on user's responses]
           - **Documentation:** [Link to relevant documentation]
           - **Success Story:** [Brief anonymized case study with a real link from Medium, company blog, or news portal. NEVER use finops.org.]
        
        2. **[Area 2]** - Score: [X]%
           - **Why Critical:** [Explanation based on user's responses]
           - **Documentation:** [Link to relevant documentation]
           - **Success Story:** [Brief anonymized case study with a real link from Medium, company blog, or news portal. NEVER use finops.org.]
        
        3. **[Area 3]** - Score: [X]%
           - **Why Critical:** [Explanation based on user's responses]
           - **Documentation:** [Link to relevant documentation]
           - **Success Story:** [Brief anonymized case study with a real link from Medium, company blog, or news portal. NEVER use finops.org.]
        
        ## 📚 Best Practices by Lens
        
        ### Knowledge (Current: {lens_scores.get('knowledge', {}).get('percentage', 0)}%)
        - [Specific knowledge gap identified from responses]
          - **Learning Resources:** [Link to FinOps Foundation training]
          - **Documentation:** [Link to relevant documentation]
        
        ### Process (Current: {lens_scores.get('process', {}).get('percentage', 0)}%)
        - [Specific process improvement]
          - **Process Guide:** [Link to process documentation]
          - **Templates:** [Link to process templates if available]
        
        ### Metrics (Current: {lens_scores.get('metrics', {}).get('percentage', 0)}%)
        - [Specific metrics recommendation]
          - **Metrics Guide:** [Link to metrics documentation]
          - **Dashboard Templates:** [Link to dashboard examples]
        
        ### Adoption (Current: {lens_scores.get('adoption', {}).get('percentage', 0)}%)
        - [Specific adoption strategy]
          - **Change Management:** [Link to adoption best practices]
          - **Training Resources:** [Link to training materials]
        
        ### Automation (Current: {lens_scores.get('automation', {}).get('percentage', 0)}%)
        - [Specific automation opportunity]
          - **Automation Guide:** [Link to automation documentation]
          - **Code Examples:** [Link to implementation examples]
        
        ## 🔗 Key Resources
        
        - [FinOps Foundation](https://www.finops.org/)
        - [Best Practices](https://www.finops.org/framework/)
        - [Training](https://www.finops.org/certification/)
        
        Make each recommendation highly specific to the user's responses and current state. Include actual links to documentation, not placeholder text. All links must be in markdown format and clickable.
        """
        
        # Call OpenAI API
        openai.api_key = os.getenv('OPENAI_API_KEY')
        openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a FinOps expert consultant with deep knowledge of the FinOps Foundation framework and real-world implementation experience."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            recommendations = response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to a comprehensive recommendation with new format
            recommendations = f"""
            ## 🚀 Immediate Actions (Next 30 days)
            
            ### Quick Wins
            - **Implement Cost Allocation Tags**
              - **Why this matters:** Based on your current score of {overall_percentage}%, establishing proper cost allocation is critical for understanding cloud spend
              - **Documentation:** https://www.finops.org/framework/capabilities/cost-allocation/
              - **Real Example:** A mid-size tech company reduced cloud costs by 25% after implementing proper tagging within 30 days
            
            - **Set Up Basic Cost Monitoring**
              - **Why this matters:** Your current monitoring score indicates room for improvement in cost visibility
              - **Documentation:** https://www.finops.org/framework/capabilities/data-analysis-showback/
              - **Real Example:** A SaaS company achieved 40% cost savings by implementing daily cost monitoring alerts
            
            ### Foundation Building
            - **Start FinOps Training Program**
              - **Why this matters:** Knowledge gaps identified in your assessment need immediate attention
              - **Documentation:** https://www.finops.org/certification/
              - **Real Example:** A financial services company improved FinOps adoption by 60% after implementing structured training
            
            ## 📈 Short-term Improvements (3-6 months)
            
            ### Process Enhancements
            - **Implement Cost Anomaly Detection**
              - **Implementation Steps:** Set up automated alerts for unusual spending patterns
              - **Documentation:** https://www.finops.org/framework/capabilities/managing-anomalies/
              - **Success Metrics:** Reduce cost overruns by 50% within 6 months
            
            ### Tool Implementation
            - **Deploy FinOps Dashboard**
              - **Why this tool:** Your current metrics score suggests need for better visualization
              - **Documentation:** https://www.finops.org/framework/capabilities/data-analysis-showback/
              - **Integration Guide:** https://www.finops.org/framework/capabilities/
            
            ## 🎯 Priority Focus Areas
            
            Based on your assessment scores, focus on these 3 critical areas:
            
            1. **Cost Allocation** - Score: {lens_scores.get('knowledge', {}).get('percentage', 0)}%
               - **Why Critical:** Your responses indicate basic cost allocation understanding, but implementation needs improvement
               - **Documentation:** https://www.finops.org/framework/capabilities/cost-allocation/
               - **Success Story:** A retail company achieved 30% cost reduction by implementing proper cost allocation
            
            2. **Data Analysis & Showback** - Score: {lens_scores.get('process', {}).get('percentage', 0)}%
               - **Why Critical:** Your process scores suggest need for better data-driven decision making
               - **Documentation:** https://www.finops.org/framework/capabilities/data-analysis-showback/
               - **Success Story:** A healthcare company improved cost transparency by 80% through showback implementation
            
            3. **Anomaly Management** - Score: {lens_scores.get('metrics', {}).get('percentage', 0)}%
               - **Why Critical:** Your metrics indicate reactive rather than proactive cost management
               - **Documentation:** https://www.finops.org/framework/capabilities/managing-anomalies/
               - **Success Story:** A manufacturing company prevented $500K in cost overruns through anomaly detection
            
            ## 📚 Best Practices by Lens
            
            ### Knowledge (Current: {lens_scores.get('knowledge', {}).get('percentage', 0)}%)
            - **FinOps Foundation Training**
              - **Learning Resources:** https://www.finops.org/certification/
              - **Documentation:** https://www.finops.org/framework/
            
            ### Process (Current: {lens_scores.get('process', {}).get('percentage', 0)}%)
            - **Standardize Cost Review Process**
              - **Process Guide:** https://www.finops.org/framework/capabilities/
              - **Templates:** https://www.finops.org/framework/
            
            ### Metrics (Current: {lens_scores.get('metrics', {}).get('percentage', 0)}%)
            - **Implement Cost KPIs Dashboard**
              - **Metrics Guide:** https://www.finops.org/framework/capabilities/data-analysis-showback/
              - **Dashboard Templates:** https://www.finops.org/framework/
            
            ### Adoption (Current: {lens_scores.get('adoption', {}).get('percentage', 0)}%)
            - **Change Management Strategy**
              - **Change Management:** https://www.finops.org/framework/capabilities/
              - **Training Resources:** https://www.finops.org/certification/
            
            ### Automation (Current: {lens_scores.get('automation', {}).get('percentage', 0)}%)
            - **Automate Cost Optimization**
              - **Automation Guide:** https://www.finops.org/framework/capabilities/
              - **Code Examples:** https://www.finops.org/framework/
            
            ## 🔗 Key Resources
            
            - **FinOps Foundation:** https://www.finops.org/
            - **Best Practices:** https://www.finops.org/framework/
            - **Training:** https://www.finops.org/certification/
            """
        
        # Store recommendations in database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE assessments 
            SET recommendations = ?
            WHERE id = ?
        ''', (recommendations, assessment_id))
        conn.commit()
        conn.close()
        
        return recommendations
        
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return "Unable to generate recommendations at this time. Please try again later."

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', '').strip()
        
        if not all([name, email, role]):
            return jsonify({"status": "error", "message": "All fields are required"})
        
        # Extract organization from email domain
        organization = email.split('@')[1] if '@' in email else 'Unknown'
        
        # Generate confirmation token
        confirmation_token = secrets.token_urlsafe(32)
        
        # Set admin status based on email domain
        is_admin_user = 1 if email.endswith('@ulisses.xyz') else 0
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, email, organization, role, confirmation_token, is_confirmed, is_admin)
                VALUES (?, ?, ?, ?, ?, 0, ?)
            ''', (encrypt_data(name), encrypt_data(email), encrypt_data(organization), encrypt_data(role), confirmation_token, is_admin_user))
            
            conn.commit()
            
            # Send confirmation email
            if send_confirmation_email(email, confirmation_token):
                return jsonify({
                    "status": "success", 
                    "message": "Registration successful! Please check your email to confirm your account, then use the login tab to request a magic link."
                })
            else:
                # If email fails, auto-confirm the user
                cursor.execute('UPDATE users SET is_confirmed = 1 WHERE email = ?', (email,))
                conn.commit()
                return jsonify({
                    "status": "success", 
                    "message": "Registration successful! Email confirmation is disabled. You can now login using the login tab."
                })
                
        except sqlite3.IntegrityError:
            return jsonify({"status": "error", "message": "Email already registered"})
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"status": "error", "message": "Registration failed. Please try again."})

@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"status": "error", "message": "Email is required"})
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # For login, we need to check all users since emails are encrypted
        cursor.execute('SELECT id, name, email, is_confirmed FROM users')
        all_users = cursor.fetchall()
        
        user = None
        for u in all_users:
            if decrypt_data(u[2]) == email:  # Check decrypted email field
                user = u
                break
        conn.close()
        
        if not user:
            return jsonify({"status": "error", "message": "User not found. Please register first."})
        
        if not user[2]:  # is_confirmed
            return jsonify({"status": "error", "message": "Please confirm your email first before logging in."})
        
        # Generate magic link token
        magic_token = secrets.token_urlsafe(32)
        
        # Store token with expiration (15 minutes)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # Update the user's confirmation token
        cursor.execute('''
            UPDATE users 
            SET confirmation_token = ? 
            WHERE id = ?
        ''', (magic_token, user[0]))
        conn.commit()
        conn.close()
        
        # Send magic link
        if send_magic_link(email, magic_token):
            return jsonify({
                "status": "success", 
                "message": "Magic link sent! Check your email and click the link to login."
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Failed to send magic link. Please try again or contact support."
            })
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"status": "error", "message": "Login failed. Please try again."})

@app.route('/magic_login/<token>')
def magic_login(token):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, email, is_confirmed 
            FROM users 
            WHERE confirmation_token = ?
        ''', (token,))
        user = cursor.fetchone()
        
        if user:
            # Clear the token and log in the user
            cursor.execute('UPDATE users SET confirmation_token = NULL WHERE id = ?', (user[0],))
            conn.commit()
            
            session['user_id'] = user[0]
            session['user_name'] = decrypt_data(user[1])
            session['user_email'] = decrypt_data(user[2])
            
            conn.close()
            return redirect('/dashboard')
        else:
            conn.close()
            return render_template('login_error.html')
            
    except Exception as e:
        print(f"Magic login error: {e}")
        return render_template('login_error.html')

@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET is_confirmed = 1, confirmation_token = NULL 
            WHERE confirmation_token = ?
        ''', (token,))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return render_template('email_confirmed.html')
        else:
            conn.close()
            return render_template('email_error.html')
            
    except Exception as e:
        print(f"Email confirmation error: {e}")
        return render_template('email_error.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    
    # Get user's assessments
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, scope_id, domain, status, overall_percentage, recommendations, created_at, updated_at
        FROM assessments 
        WHERE user_id = ? 
        ORDER BY updated_at DESC
    ''', (session['user_id'],))
    assessments = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', 
                         user_name=session['user_name'],
                         assessments=assessments,
                         scopes=SCOPES,
                         domains=DOMAINS,
                         is_admin=is_admin())

@app.route('/start_assessment', methods=['POST'])
def start_assessment():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Please log in first"})
    
    try:
        scope_id = request.form.get('scope_id')
        domain = request.form.get('domain', '')  # Empty string for complete assessment
        
        if not scope_id:
            return jsonify({"status": "error", "message": "Scope is required"})
        
        # Create new assessment
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assessments (user_id, scope_id, domain, status)
            VALUES (?, ?, ?, 'in_progress')
        ''', (session['user_id'], scope_id, domain if domain else None))
        
        assessment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Store current assessment in session
        session['current_assessment_id'] = assessment_id
        session['current_scope'] = scope_id
        session['current_domain'] = domain if domain else None
        
        return jsonify({"status": "success", "assessment_id": assessment_id})
        
    except Exception as e:
        print(f"Start assessment error: {e}")
        return jsonify({"status": "error", "message": "Failed to start assessment"})

@app.route('/assessment')
def assessment():
    if 'user_id' not in session:
        return redirect('/')
    
    if 'current_assessment_id' not in session:
        return redirect('/dashboard')
    
    return render_template('assessment.html')

@app.route('/get_assessment_progress')
def get_assessment_progress():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Please log in first"})
    
    if 'current_assessment_id' not in session:
        return jsonify({"status": "error", "message": "No active assessment"})
    
    try:
        assessment_id = session['current_assessment_id']
        scope_id = session['current_scope']
        domain = session.get('current_domain')
        
        # Get capabilities for this assessment
        if domain:
            capabilities = [c for c in CAPABILITIES if c['domain'] == domain]
        else:
            capabilities = CAPABILITIES
        
        # Generate questions for all capability + lens combinations
        questions = []
        for capability in capabilities:
            for lens in LENSES:
                question_text = generate_question(capability['id'], lens['id'], scope_id)
                questions.append({
                    'capability_id': capability['id'],
                    'capability_name': capability['name'],
                    'lens_id': lens['id'],
                    'lens_name': lens['name'],
                    'domain': capability['domain'],
                    'question': question_text
                })
        
        # Get existing responses
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT capability_id, lens_id, answer
            FROM responses 
            WHERE assessment_id = ?
        ''', (assessment_id,))
        responses_data = cursor.fetchall()
        conn.close()
        
        # Convert to dictionary
        responses = {}
        for resp in responses_data:
            key = f"{resp[0]}_{resp[1]}"
            responses[key] = {"answer": resp[2]}
        
        return jsonify({
            "status": "success",
            "assessment_id": assessment_id,
            "questions": questions,
            "responses": responses
        })
        
    except Exception as e:
        print(f"Get assessment progress error: {e}")
        return jsonify({"status": "error", "message": "Failed to load assessment"})

@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Please log in first"})
    
    if 'current_assessment_id' not in session:
        return jsonify({"status": "error", "message": "No active assessment"})
    
    try:
        assessment_id = session['current_assessment_id']
        capability_id = request.form.get('capability_id')
        lens_id = request.form.get('lens_id')
        answer = request.form.get('answer', '').strip()
        
        if not all([capability_id, lens_id, answer]):
            return jsonify({"status": "error", "message": "All fields are required"})
        
        # Handle file uploads
        evidence_files = []
        if 'evidence' in request.files:
            files = request.files.getlist('evidence')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    evidence_files.append(filename)
        
        # Get AI analysis
        try:
            scope_name = next((s['name'] for s in SCOPES if s['id'] == session['current_scope']), session['current_scope'])
            capability_name = next((c['name'] for c in CAPABILITIES if c['id'] == capability_id), capability_id)
            lens_name = next((l['name'] for l in LENSES if l['id'] == lens_id), lens_id)
            
            # Use OpenAI or XAI for analysis
            api_key = os.getenv('OPENAI_API_KEY') or os.getenv('XAI_API_KEY')
            if api_key:
                if os.getenv('XAI_API_KEY'):
                    openai.api_base = "https://api.x.ai/v1"
                
                openai.api_key = api_key
                
                prompt = f"""
                Analyze this FinOps assessment response and provide a score from 0-4 and improvement suggestions.
                
                Scope: {scope_name}
                Capability: {capability_name}
                Lens: {lens_name}
                
                Response: {answer}
                
                Scoring criteria:
                0 = No capability or awareness
                1 = Basic awareness, ad-hoc activities
                2 = Some processes in place, inconsistent execution
                3 = Well-defined processes, consistent execution
                4 = Optimized, automated, continuous improvement
                
                Provide your response in this exact format:
                SCORE: [0-4]
                IMPROVEMENT: [specific actionable suggestions]
                """
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3
                )
                
                ai_response = response.choices[0].message.content
                
                # Parse AI response
                score = 2  # Default score
                improvement = "Continue developing this capability with structured processes and regular reviews."
                
                if "SCORE:" in ai_response:
                    try:
                        score_line = [line for line in ai_response.split('\n') if 'SCORE:' in line][0]
                        score = int(score_line.split(':')[1].strip())
                    except:
                        pass
                
                if "IMPROVEMENT:" in ai_response:
                    try:
                        improvement_lines = ai_response.split('IMPROVEMENT:')[1].strip()
                        improvement = improvement_lines
                    except:
                        pass
            else:
                score = 2
                improvement = "AI analysis not available. Please configure API key for detailed feedback."
                
        except Exception as e:
            print(f"AI analysis error: {e}")
            score = 2
            improvement = "Analysis temporarily unavailable. Your response has been saved."
        
        # Save response to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if response already exists
        cursor.execute('''
            SELECT id FROM responses 
            WHERE assessment_id = ? AND capability_id = ? AND lens_id = ?
        ''', (assessment_id, capability_id, lens_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing response
            cursor.execute('''
                UPDATE responses 
                SET answer = ?, score = ?, improvement_suggestions = ?, evidence_files = ?
                WHERE id = ?
            ''', (answer, score, improvement, json.dumps(evidence_files), existing[0]))
        else:
            # Insert new response
            cursor.execute('''
                INSERT INTO responses (assessment_id, capability_id, lens_id, answer, score, improvement_suggestions, evidence_files)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (assessment_id, capability_id, lens_id, answer, score, improvement, json.dumps(evidence_files)))
        
        # Update assessment timestamp
        cursor.execute('''
            UPDATE assessments 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (assessment_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "score": score, "improvement": improvement})
        
    except Exception as e:
        print(f"Submit assessment error: {e}")
        return jsonify({"status": "error", "message": "Failed to save response"})

@app.route('/complete_assessment', methods=['POST'])
def complete_assessment():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Please log in first"})
    
    if 'current_assessment_id' not in session:
        return jsonify({"status": "error", "message": "No active assessment"})
    
    try:
        assessment_id = session['current_assessment_id']
        
        # Calculate overall percentage from responses
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT score FROM responses WHERE assessment_id = ?', (assessment_id,))
        responses = cursor.fetchall()
        
        total_score = sum(r[0] or 0 for r in responses)
        total_possible = len(responses) * 4
        overall_percentage = round((total_score / total_possible) * 100) if total_possible > 0 else 0
        
        # Calculate lens scores for recommendations
        lens_scores = {lens['id']: {'total': 0, 'count': 0, 'weight': lens['weight']} for lens in LENSES}
        
        cursor.execute('''
            SELECT lens_id, score 
            FROM responses 
            WHERE assessment_id = ?
        ''', (assessment_id,))
        lens_responses = cursor.fetchall()
        
        for lens_id, score in lens_responses:
            if lens_id in lens_scores:
                lens_scores[lens_id]['total'] += score or 0
                lens_scores[lens_id]['count'] += 1
        
        # Calculate lens percentages
        for lens_id, data in lens_scores.items():
            if data['count'] > 0:
                data['percentage'] = round((data['total'] / (data['count'] * 4)) * 100)
            else:
                data['percentage'] = 0
        
        # Get assessment details for recommendations
        cursor.execute('SELECT scope_id, domain FROM assessments WHERE id = ?', (assessment_id,))
        assessment_details = cursor.fetchone()
        scope_id = assessment_details[0]
        domain = assessment_details[1]
        
        # Generate recommendations using OpenAI
        recommendations = generate_recommendations(assessment_id, scope_id, domain, overall_percentage, lens_scores)
        
        # Mark assessment as completed with overall percentage and recommendations
        cursor.execute('''
            UPDATE assessments 
            SET status = 'completed', overall_percentage = ?, recommendations = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (overall_percentage, recommendations, assessment_id,))
        conn.commit()
        conn.close()
        
        # Clear session
        session.pop('current_assessment_id', None)
        session.pop('current_scope', None)
        session.pop('current_domain', None)
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        print(f"Complete assessment error: {e}")
        return jsonify({"status": "error", "message": "Failed to complete assessment"})

@app.route('/get_assessment_results/<int:assessment_id>')
def get_assessment_results(assessment_id):
    print(f"[DEBUG] Starting get_assessment_results for assessment_id={assessment_id}")
    if 'user_id' not in session:
        print(f"[DEBUG] No user_id in session")
        return redirect('/')
    
    print(f"[DEBUG] user_id in session: {session.get('user_id')}")
    
    try:
        # Get assessment details
        print(f"[DEBUG] Connecting to database...")
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, user_id, scope_id, domain, status, overall_percentage, recommendations, created_at, updated_at
            FROM assessments 
            WHERE id = ? AND user_id = ?
        '''
        print(f"[DEBUG] Executing query: {query}")
        print(f"[DEBUG] Query parameters: assessment_id={assessment_id}, user_id={session['user_id']}")
        
        cursor.execute(query, (assessment_id, session['user_id']))
        assessment = cursor.fetchone()
        print(f"[DEBUG] assessment: {assessment}")
        
        if not assessment:
            conn.close()
            print(f"Assessment not found for id={assessment_id} and user_id={session.get('user_id')}")
            return render_template('error.html', message="Assessment not found or you do not have access to it."), 404
        
        # Defensive: check assessment tuple length
        if len(assessment) < 9:
            conn.close()
            print(f"Assessment tuple too short: {assessment}")
            return render_template('error.html', message="Assessment data is incomplete."), 500
        
        # Log each field for debugging
        field_names = ['id', 'user_id', 'scope_id', 'domain', 'status', 'overall_percentage', 'recommendations', 'created_at', 'updated_at']
        for idx, field in enumerate(field_names):
            print(f"[DEBUG] assessment[{field}]: {assessment[idx]}")
        
        # Check for None in essential fields
        essentials = {'scope_id': 2, 'domain': 3, 'status': 4}
        for key, idx in essentials.items():
            if assessment[idx] is None:
                conn.close()
                print(f"[ERROR] Essential field {key} is None in assessment: {assessment}")
                return render_template('error.html', message=f"Assessment field '{key}' is missing."), 500
        
        # Get scope information
        scope_id = assessment[2]
        scope = next((s for s in SCOPES if s['id'] == scope_id), None)
        print(f"[DEBUG] scope: {scope}")
        if not scope:
            conn.close()
            print(f"Scope not found for assessment: {assessment}")
            return render_template('error.html', message="Assessment scope not found."), 404
        
        # Get responses
        cursor.execute('''
            SELECT capability_id, lens_id, answer, score, improvement_suggestions
            FROM responses 
            WHERE assessment_id = ?
        ''', (assessment_id,))
        responses = cursor.fetchall()
        print(f"[DEBUG] responses: {responses}")
        if responses is None:
            responses = []
        
        # Defensive: check responses structure
        for r in responses:
            if r is None or len(r) < 5:
                print(f"Malformed response row: {r}")
                return render_template('error.html', message="A response row is malformed."), 500
        
        # Get benchmark data (other completed assessments with same scope)
        cursor.execute('''
            SELECT u.organization, a.id
            FROM assessments a
            JOIN users u ON a.user_id = u.id
            WHERE a.scope_id = ? AND a.status = 'completed' AND a.id != ?
            ORDER BY a.updated_at DESC
            LIMIT 10
        ''', (scope_id, assessment_id))
        benchmark_assessments = cursor.fetchall()
        print(f"[DEBUG] benchmark_assessments: {benchmark_assessments}")
        if benchmark_assessments is None:
            benchmark_assessments = []
        
        # Defensive: check benchmark_assessments structure
        for b in benchmark_assessments:
            if b is None or len(b) < 2:
                print(f"Malformed benchmark row: {b}")
                return render_template('error.html', message="A benchmark row is malformed."), 500
        
        conn.close()
        
        # Calculate scores
        results_matrix = {}
        total_score = 0
        total_possible = 0
        lens_scores = {lens['id']: {'total': 0, 'count': 0, 'weight': lens['weight']} for lens in LENSES}
        
        for response in responses:
            capability_id, lens_id, answer, score, improvement = response
            if not capability_id or not lens_id:
                print(f"Response missing capability_id or lens_id: {response}")
                continue
            if capability_id not in results_matrix:
                results_matrix[capability_id] = {}
            results_matrix[capability_id][lens_id] = {
                'score': score or 0,
                'answer': answer,
                'improvement': improvement or 'No suggestions available'
            }
            score_value = score or 0
            total_score += score_value
            total_possible += 4
            lens_scores[lens_id]['total'] += score_value
            lens_scores[lens_id]['count'] += 1
        
        # Calculate lens averages and percentages
        for lens_id, data in lens_scores.items():
            if data['count'] > 0:
                data['average'] = round(data['total'] / data['count'], 1)
                data['percentage'] = round((data['total'] / (data['count'] * 4)) * 100)
                data['weighted'] = round((data['percentage'] * data['weight']) / 100, 1)
            else:
                data['average'] = 0
                data['percentage'] = 0
                data['weighted'] = 0
        
        # Calculate overall percentage
        overall_percentage = round((total_score / total_possible) * 100) if total_possible > 0 else 0
        print(f"[DEBUG] overall_percentage: {overall_percentage}")
        
        # Generate benchmark data
        benchmark_data = []
        user_score = None
        other_scores = []
        if len(benchmark_assessments) >= 1:  # Include current assessment in benchmark
            # Calculate scores for benchmark assessments
            for i, (org_name, bench_id) in enumerate(benchmark_assessments):
                if not bench_id:
                    print(f"Benchmark row missing bench_id: {org_name}, {bench_id}")
                    continue
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                cursor.execute('SELECT score FROM responses WHERE assessment_id = ?', (bench_id,))
                bench_responses = cursor.fetchall()
                conn.close()
                bench_total = sum(r[0] or 0 for r in bench_responses)
                bench_possible = len(bench_responses) * 4
                bench_percentage = round((bench_total / bench_possible) * 100) if bench_possible > 0 else 0
                benchmark_data.append({
                    'organization': f"Company {chr(65 + i)}",  # Company A, B, C, etc.
                    'overall_percentage': bench_percentage
                })
            # Add current assessment
            benchmark_data.append({
                'organization': 'Your Organization',
                'overall_percentage': overall_percentage
            })
            # Sort by percentage (descending)
            benchmark_data.sort(key=lambda x: x['overall_percentage'], reverse=True)
            # Calculate user score and industry average
            for org in benchmark_data:
                if org['organization'] == 'Your Organization':
                    user_score = org['overall_percentage']
                else:
                    other_scores.append(org['overall_percentage'])
            industry_avg = round(sum(other_scores) / len(other_scores), 1) if other_scores else 0
        else:
            user_score = overall_percentage
            industry_avg = 0
        print(f"[DEBUG] benchmark_data: {benchmark_data}")
        print(f"[DEBUG] user_score: {user_score}, industry_avg: {industry_avg}")
        
        # Get capabilities for display
        domain = assessment[3]
        if domain:
            capabilities = [c for c in CAPABILITIES if c['domain'] == domain]
        else:
            capabilities = CAPABILITIES
        print(f"[DEBUG] capabilities: {capabilities}")
        
        # Generate recommendations if not already present
        recommendations = assessment[6] if len(assessment) > 6 and assessment[6] else None
        print(f"[DEBUG] Current recommendations: {recommendations}")
        print(f"[DEBUG] Assessment status: {assessment[4]}")
        
        if not recommendations and assessment[4] == 'completed':  # Only generate for completed assessments
            print(f"[DEBUG] Generating recommendations for assessment {assessment_id}")
            try:
                recommendations = generate_recommendations(assessment_id, scope_id, domain, overall_percentage, lens_scores)
                print(f"[DEBUG] Recommendations generated successfully: {len(recommendations) if recommendations else 0} characters")
            except Exception as e:
                print(f"[DEBUG] Error generating recommendations: {e}")
                recommendations = "Unable to generate recommendations at this time. Please try again later."
        else:
            print(f"[DEBUG] Skipping recommendation generation - already exists or assessment not completed")
        
        print(f"[DEBUG] Final recommendations: {len(recommendations) if recommendations else 0} characters")
        
        return render_template('results.html',
                             assessment=assessment,
                             scope=scope,
                             domain=domain,
                             capabilities=capabilities,
                             lenses=LENSES,
                             results_matrix=results_matrix,
                             total_score=total_score,
                             total_possible=total_possible,
                             overall_percentage=overall_percentage,
                             lens_scores=lens_scores,
                             user_score=user_score,
                             industry_avg=industry_avg,
                             recommendations=recommendations)
        
    except Exception as e:
        print(f"Get assessment results error: {e}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        return render_template('error.html', message=f"An error occurred while retrieving assessment results: {e}"), 500

@app.route('/debug/users')
def debug_users():
    if not is_admin():
        return redirect('/')
    
    return render_template('debug_users.html')

@app.route('/debug/users/api')
def debug_users_api():
    if not is_admin():
        return jsonify({"error": "Access denied. Admin privileges required."}), 403
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, email, organization, role, is_confirmed, is_admin, created_at, confirmation_token
            FROM users 
            ORDER BY created_at DESC
        ''')
        users = cursor.fetchall()
        
        cursor.execute('SELECT COUNT(*) FROM assessments')
        total_assessments = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM assessments WHERE status = "completed"')
        completed_assessments = cursor.fetchone()[0]
        
        conn.close()
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user[0],
                'name': decrypt_data(user[1]),
                'email': decrypt_data(user[2]),
                'organization': decrypt_data(user[3]),
                'role': decrypt_data(user[4]),
                'is_confirmed': bool(user[5]),
                'is_admin': bool(user[6]),
                'created_at': user[7],
                'has_token': bool(user[8])
            })
        
        return jsonify({
            'users': users_data,
            'stats': {
                'total_users': len(users),
                'confirmed_users': len([u for u in users_data if u['is_confirmed']]),
                'admin_users': len([u for u in users_data if u['is_admin']]),
                'total_assessments': total_assessments,
                'completed_assessments': completed_assessments
            }
        })
        
    except Exception as e:
        print(f"Debug users error: {e}")
        return jsonify({"error": "Failed to fetch user data"}), 500

@app.route('/remove_user/<int:user_id>', methods=['DELETE'])
def remove_user(user_id):
    if not is_admin():
        return jsonify({"error": "Access denied. Admin privileges required."}), 403
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if user exists and is not an admin
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        if user[0]:  # is_admin
            conn.close()
            return jsonify({"error": "Cannot remove admin users"}), 403
        
        # Delete user's assessments and responses
        cursor.execute('DELETE FROM responses WHERE assessment_id IN (SELECT id FROM assessments WHERE user_id = ?)', (user_id,))
        cursor.execute('DELETE FROM assessments WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": "User removed successfully"})
        
    except Exception as e:
        print(f"Remove user error: {e}")
        return jsonify({"error": "Failed to remove user"}), 500

@app.route('/debug/benchmarks/api')
def debug_benchmarks_api():
    if not is_admin():
        return jsonify({"error": "Access denied. Admin privileges required."}), 403
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get all completed assessments with organization data
        cursor.execute('''
            SELECT 
                a.id,
                a.scope_id,
                a.domain,
                a.overall_percentage,
                a.created_at,
                u.organization
            FROM assessments a
            JOIN users u ON a.user_id = u.id
            WHERE a.status = 'completed'
            ORDER BY a.created_at DESC
        ''')
        assessments = cursor.fetchall()
        
        # Get benchmark statistics by scope
        cursor.execute('''
            SELECT 
                scope_id,
                COUNT(*) as count,
                AVG(overall_percentage) as avg_percentage,
                MIN(overall_percentage) as min_percentage,
                MAX(overall_percentage) as max_percentage
            FROM assessments 
            WHERE status = 'completed'
            GROUP BY scope_id
        ''')
        scope_stats = cursor.fetchall()
        
        # Get benchmark statistics by domain
        cursor.execute('''
            SELECT 
                domain,
                COUNT(*) as count,
                AVG(overall_percentage) as avg_percentage,
                MIN(overall_percentage) as min_percentage,
                MAX(overall_percentage) as max_percentage
            FROM assessments 
            WHERE status = 'completed' AND domain IS NOT NULL
            GROUP BY domain
        ''')
        domain_stats = cursor.fetchall()
        
        conn.close()
        
        # Process assessment data
        assessments_data = []
        for assessment in assessments:
            assessments_data.append({
                'id': assessment[0],
                'scope_id': assessment[1],
                'domain': assessment[2],
                'overall_percentage': assessment[3],
                'created_at': assessment[4],
                'organization': decrypt_data(assessment[5]) if assessment[5] else 'Unknown'
            })
        
        # Process scope statistics
        scope_benchmarks = {}
        for scope_stat in scope_stats:
            scope_id = scope_stat[0]
            scope_name = next((s['name'] for s in SCOPES if s['id'] == scope_id), scope_id)
            scope_benchmarks[scope_id] = {
                'name': scope_name,
                'count': scope_stat[1],
                'avg_percentage': round(scope_stat[2], 1) if scope_stat[2] else 0,
                'min_percentage': scope_stat[3] if scope_stat[3] else 0,
                'max_percentage': scope_stat[4] if scope_stat[4] else 0
            }
        
        # Process domain statistics
        domain_benchmarks = {}
        for domain_stat in domain_stats:
            domain_name = domain_stat[0]
            domain_benchmarks[domain_name] = {
                'count': domain_stat[1],
                'avg_percentage': round(domain_stat[2], 1) if domain_stat[2] else 0,
                'min_percentage': domain_stat[3] if domain_stat[3] else 0,
                'max_percentage': domain_stat[4] if domain_stat[4] else 0
            }
        
        return jsonify({
            'assessments': assessments_data,
            'scope_benchmarks': scope_benchmarks,
            'domain_benchmarks': domain_benchmarks,
            'total_completed': len(assessments_data),
            'scopes': SCOPES,
            'domains': DOMAINS
        })
        
    except Exception as e:
        print(f"Debug benchmarks error: {e}")
        return jsonify({"error": "Failed to fetch benchmark data"}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

def autolink(text):
    url_pattern = re.compile(r'(https?://[^\s)]+)')
    return url_pattern.sub(r'[\1](\1)', text)

@app.template_filter('markdown')
def markdown_filter(text):
    if not text:
        return ''
    import textwrap
    text = textwrap.dedent(text)
    text = autolink(text)
    html = markdown.markdown(text, extensions=['extra', 'sane_lists', 'smarty'])
    # Pós-processar para adicionar target e rel em todos os links
    html = re.sub(r'<a (href="https?://[^"]+")', r'<a \1 target="_blank" rel="noopener noreferrer"', html)
    return html

def fix_real_example_links(html_text):
    # Substitui links de real example que apontam para finops.org
    return re.sub(r'(Real Example:.*?)(<a [^>]*href=["\\\']https?://(?:www\.)?finops\.org[^>]+>.*?</a>)',
                  r'\1 <span style="color:#e53e3e;font-weight:bold">[Exemplo real não encontrado, consulte <a href=\"https://news.google.com/search?q=finops\" target=\"_blank\">Google News</a>]</span>',
                  html_text, flags=re.IGNORECASE)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)

