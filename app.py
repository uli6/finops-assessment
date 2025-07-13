from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
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
from weasyprint import HTML, CSS
from io import BytesIO
import hashlib
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from functools import lru_cache

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

def hash_company(domain):
    return hashlib.sha256(domain.strip().lower().encode()).hexdigest()

# Initialize database with complete migration support
def init_db():
    """Initialize database with proper schema and handle migrations"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create users table with all required columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_hash TEXT UNIQUE NOT NULL,
            company_hash TEXT,
            confirmation_token TEXT,
            is_confirmed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check existing columns and add missing ones
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    print(f"Existing columns: {existing_columns}")
    
    # Add missing columns one by one
    required_columns = {
        'company_hash': 'TEXT',
        'confirmation_token': 'TEXT',
        'is_confirmed': 'BOOLEAN DEFAULT 0',
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

# Updated FinOps Framework with 4 Domains and Detailed Capabilities
CAPABILITIES = [
    # Domain 1: Understand Usage & Cost
    {"id": "data_ingestion", "name": "Data Ingestion", "domain": "Understand Usage & Cost"},
    {"id": "allocation", "name": "Allocation", "domain": "Understand Usage & Cost"},
    {"id": "reporting_analytics", "name": "Reporting & Analytics", "domain": "Understand Usage & Cost"},
    {"id": "anomaly_management", "name": "Anomaly Management", "domain": "Understand Usage & Cost"},
    
    # Domain 2: Quantify Business Value
    {"id": "forecasting", "name": "Forecasting", "domain": "Quantify Business Value"},
    {"id": "budgeting", "name": "Budgeting", "domain": "Quantify Business Value"},
    {"id": "benchmark", "name": "Benchmark", "domain": "Quantify Business Value"},
    {"id": "unit_economics", "name": "Unit Economics", "domain": "Quantify Business Value"},
    
    # Domain 3: Optimize Usage & Cost
    {"id": "architecting_cloud", "name": "Architecting for Cloud", "domain": "Optimize Usage & Cost"},
    {"id": "rate_optimization", "name": "Rate Optimization", "domain": "Optimize Usage & Cost"},
    {"id": "workload_optimization", "name": "Workload Optimization", "domain": "Optimize Usage & Cost"},
    {"id": "cloud_sustainability", "name": "Cloud Sustainability", "domain": "Optimize Usage & Cost"},
    {"id": "licensing_saas", "name": "Licensing & SaaS", "domain": "Optimize Usage & Cost"},
    
    # Domain 4: Manage the FinOps Practice
    {"id": "finops_practice_operations", "name": "FinOps Practice Operations", "domain": "Manage the FinOps Practice"},
    {"id": "policy_governance", "name": "Policy & Governance", "domain": "Manage the FinOps Practice"},
    {"id": "finops_assessment", "name": "FinOps Assessment", "domain": "Manage the FinOps Practice"},
    {"id": "finops_tools_services", "name": "FinOps Tools & Services", "domain": "Manage the FinOps Practice"},
    {"id": "finops_education_enablement", "name": "FinOps Education & Enablement", "domain": "Manage the FinOps Practice"},
    {"id": "invoicing_chargeback", "name": "Invoicing & Chargeback", "domain": "Manage the FinOps Practice"},
    {"id": "onboarding_workloads", "name": "Onboarding Workloads", "domain": "Manage the FinOps Practice"},
    {"id": "intersecting_disciplines", "name": "Intersecting Disciplines", "domain": "Manage the FinOps Practice"}
]

DOMAINS = ["Understand Usage & Cost", "Quantify Business Value", "Optimize Usage & Cost", "Manage the FinOps Practice"]

# Comprehensive Question Bank for Each Capability and Lens
QUESTIONS = {
    # Domain 1: Understand Usage & Cost
    "data_ingestion": {
        "knowledge": [
            "What percentage of your team members can explain the key data sources required for effective FinOps practice?",
            "How well do stakeholders understand the difference between billing data, usage data, and metadata in your organization?"
        ],
        "process": [
            "How standardized are your data ingestion processes across different cloud providers?",
            "What percentage of your data ingestion processes have documented procedures and responsible owners?"
        ],
        "metrics": [
            "What percentage of your required data sources are successfully ingested and available for analysis?",
            "How do you measure the quality and completeness of your ingested data?"
        ],
        "adoption": [
            "What percentage of your teams regularly use centralized data ingestion processes rather than maintaining their own data silos?",
            "How consistently do teams follow established data ingestion standards?"
        ],
        "automation": [
            "What percentage of your data ingestion processes are automated?",
            "How automated is your data quality validation process?"
        ]
    },
    "allocation": {
        "knowledge": [
            "What percentage of your organization understands the importance of proper cost allocation for cloud resources?",
            "How well do teams understand the allocation methodologies being used in your organization?"
        ],
        "process": [
            "How consistently are allocation rules applied across all cloud resources?",
            "What percentage of your allocation processes have documented methodologies and approval workflows?"
        ],
        "metrics": [
            "What percentage of your cloud costs can be allocated to specific business units, projects, or services?",
            "What percentage of your cloud resources are properly tagged for cost allocation purposes?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in the cost allocation process?",
            "How widely are allocated costs used for decision-making across the organization?"
        ],
        "automation": [
            "What percentage of your cost allocation processes are automated?",
            "How automated is the validation and reconciliation of allocated costs?"
        ]
    },
    "reporting_analytics": {
        "knowledge": [
            "What percentage of your stakeholders can interpret and act on FinOps reports and analytics?",
            "How well do teams understand which metrics are most relevant for their specific roles and responsibilities?"
        ],
        "process": [
            "How standardized are your reporting processes across different stakeholder groups?",
            "What percentage of your reports have defined refresh schedules and delivery mechanisms?"
        ],
        "metrics": [
            "What percentage of your reports provide actionable insights rather than just raw data?",
            "How effectively do your analytics identify optimization opportunities?"
        ],
        "adoption": [
            "What percentage of your teams regularly use FinOps reports for decision-making?",
            "How consistently do stakeholders access and act on provided reports?"
        ],
        "automation": [
            "What percentage of your reports are generated automatically?",
            "How automated is the distribution and consumption of your reports?"
        ]
    },
    "anomaly_management": {
        "knowledge": [
            "What percentage of your organization understands what constitutes a cost anomaly and its potential impact?",
            "How well do teams understand their roles and responsibilities when anomalies are detected?"
        ],
        "process": [
            "How well-defined are your anomaly detection and response processes?",
            "What percentage of detected anomalies follow a standardized investigation and resolution workflow?"
        ],
        "metrics": [
            "What percentage of cost anomalies are detected within your target timeframe?",
            "How effectively do you measure the impact and resolution time of anomalies?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in anomaly monitoring and response?",
            "How consistently do teams respond to anomaly alerts within defined SLAs?"
        ],
        "automation": [
            "What percentage of your anomaly detection is automated?",
            "How automated are your anomaly notification and escalation processes?"
        ]
    },
    
    # Domain 2: Quantify Business Value
    "forecasting": {
        "knowledge": [
            "What percentage of your stakeholders understand the difference between trends, seasonal patterns, and growth forecasting?",
            "How well do teams understand the data requirements and limitations of different forecasting methodologies?"
        ],
        "process": [
            "How standardized are your forecasting methodologies across different business units and time horizons?",
            "What percentage of your forecasts have defined update cycles and review processes?"
        ],
        "metrics": [
            "What percentage of your forecasts achieve acceptable accuracy levels within your defined tolerance range?",
            "How effectively do you measure and improve forecast accuracy over time?"
        ],
        "adoption": [
            "What percentage of your business decisions incorporate cloud cost forecasts?",
            "How consistently do teams use forecasts for capacity planning and budget preparation?"
        ],
        "automation": [
            "What percentage of your forecasting processes are automated?",
            "How automated is the generation and distribution of forecast reports?"
        ]
    },
    "budgeting": {
        "knowledge": [
            "What percentage of your organization understands the relationship between cloud budgets and business objectives?",
            "How well do teams understand budget variance analysis and corrective actions?"
        ],
        "process": [
            "How standardized are your budget creation and approval processes across the organization?",
            "What percentage of your budgets have defined monitoring and alerting mechanisms?"
        ],
        "metrics": [
            "What percentage of your teams consistently stay within their allocated cloud budgets?",
            "How effectively do you track and analyze budget variance trends?"
        ],
        "adoption": [
            "What percentage of your cloud spending is covered by formal budget allocations?",
            "How consistently do teams use budget information for spending decisions?"
        ],
        "automation": [
            "What percentage of your budget monitoring and alerting is automated?",
            "How automated are your budget approval and modification workflows?"
        ]
    },
    "benchmark": {
        "knowledge": [
            "What percentage of your organization understands relevant benchmarking metrics for cloud efficiency?",
            "How well do teams understand how to interpret benchmark data and identify improvement opportunities?"
        ],
        "process": [
            "How standardized are your benchmarking processes and methodologies?",
            "What percentage of your benchmarking activities follow defined data collection and analysis procedures?"
        ],
        "metrics": [
            "What percentage of your key cloud metrics are regularly benchmarked against relevant standards?",
            "How effectively do you track improvement progress based on benchmark comparisons?"
        ],
        "adoption": [
            "What percentage of your teams regularly use benchmark data for performance evaluation and goal setting?",
            "How consistently do teams incorporate benchmark insights into their optimization strategies?"
        ],
        "automation": [
            "What percentage of your benchmarking data collection and analysis is automated?",
            "How automated is the generation and distribution of benchmark reports?"
        ]
    },
    "unit_economics": {
        "knowledge": [
            "What percentage of your organization understands how cloud costs relate to business unit economics?",
            "How well do teams understand the metrics that drive unit cost calculations in your business model?"
        ],
        "process": [
            "How standardized are your unit economics calculation methodologies across different products or services?",
            "What percentage of your unit economics analyses include cloud cost components?"
        ],
        "metrics": [
            "What percentage of your products or services have defined and tracked unit cost metrics?",
            "How effectively do you measure the impact of cloud optimization on unit economics?"
        ],
        "adoption": [
            "What percentage of your business decisions consider unit economics including cloud costs?",
            "How consistently do product teams use unit economics for pricing and investment decisions?"
        ],
        "automation": [
            "What percentage of your unit economics calculations are automated?",
            "How automated is the tracking and reporting of unit cost trends?"
        ]
    },
    
    # Domain 3: Optimize Usage & Cost
    "architecting_cloud": {
        "knowledge": [
            "What percentage of your architects and developers understand cloud-native design patterns for cost optimization?",
            "How well do teams understand the cost implications of different architectural decisions?"
        ],
        "process": [
            "How standardized are your architecture review processes for cost and sustainability considerations?",
            "What percentage of your architectural decisions include formal cost impact assessments?"
        ],
        "metrics": [
            "What percentage of your applications follow cloud-native architectural best practices for cost efficiency?",
            "How effectively do you measure the cost efficiency of different architectural patterns in your environment?"
        ],
        "adoption": [
            "What percentage of your teams consistently apply cloud-native architectural principles in new development?",
            "How consistently do teams refactor existing applications using cost-optimized architectural patterns?"
        ],
        "automation": [
            "What percentage of your architectural compliance checks are automated?",
            "How automated is the enforcement of cost-optimized architectural standards?"
        ]
    },
    "rate_optimization": {
        "knowledge": [
            "What percentage of your teams understand the different pricing models available across your cloud providers?",
            "How well do stakeholders understand when and how to apply different commitment types (Reserved Instances, Savings Plans, etc.)?"
        ],
        "process": [
            "How standardized are your rate optimization analysis and decision-making processes?",
            "What percentage of your rate optimization opportunities are evaluated using defined criteria and approval workflows?"
        ],
        "metrics": [
            "What percentage of your eligible workloads are covered by cost-effective rate optimization strategies?",
            "How effectively do you measure and track the savings achieved through rate optimization?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in rate optimization planning and implementation?",
            "How consistently do teams follow rate optimization recommendations and guidelines?"
        ],
        "automation": [
            "What percentage of your rate optimization analysis and monitoring is automated?",
            "How automated is the implementation and management of rate optimization commitments?"
        ]
    },
    "workload_optimization": {
        "knowledge": [
            "What percentage of your development teams understand cloud-native optimization principles and best practices?",
            "How well do teams understand the relationship between application architecture and cloud costs?"
        ],
        "process": [
            "How standardized are your workload optimization assessment and implementation processes?",
            "What percentage of your workloads undergo regular optimization reviews using defined criteria?"
        ],
        "metrics": [
            "What percentage of your workloads are rightsized according to actual usage patterns?",
            "How effectively do you measure workload efficiency and optimization impact?"
        ],
        "adoption": [
            "What percentage of your development teams actively implement workload optimization practices?",
            "How consistently do teams incorporate optimization considerations into their development lifecycle?"
        ],
        "automation": [
            "What percentage of your workload optimization recommendations are generated automatically?",
            "How automated is the implementation of workload optimization changes?"
        ]
    },
    "cloud_sustainability": {
        "knowledge": [
            "What percentage of your organization understands the relationship between cloud usage patterns and environmental impact?",
            "How well do teams understand sustainable cloud practices and their implementation?"
        ],
        "process": [
            "How standardized are your sustainability assessment and optimization processes?",
            "What percentage of your cloud optimization decisions include sustainability impact considerations?"
        ],
        "metrics": [
            "What percentage of your cloud resources are optimized for both cost and carbon efficiency?",
            "How effectively do you measure and track the environmental impact of your cloud usage?"
        ],
        "adoption": [
            "What percentage of your teams actively consider sustainability in their cloud usage decisions?",
            "How consistently do teams implement sustainable cloud practices in their daily operations?"
        ],
        "automation": [
            "What percentage of your sustainability monitoring and reporting is automated?",
            "How automated are your sustainable cloud optimization implementations?"
        ]
    },
    "licensing_saas": {
        "knowledge": [
            "What percentage of your organization understands the cost implications of different software licensing models in cloud environments?",
            "How well do teams understand SaaS optimization strategies and vendor management best practices?"
        ],
        "process": [
            "How standardized are your software licensing and SaaS procurement processes?",
            "What percentage of your software licenses and SaaS subscriptions undergo regular utilization and optimization reviews?"
        ],
        "metrics": [
            "What percentage of your software licenses are optimally utilized according to actual usage patterns?",
            "How effectively do you measure and track software licensing costs and optimization opportunities?"
        ],
        "adoption": [
            "What percentage of your teams actively manage and optimize their software licensing and SaaS usage?",
            "How consistently do teams follow established software procurement and optimization guidelines?"
        ],
        "automation": [
            "What percentage of your software license monitoring and optimization is automated?",
            "How automated are your software procurement and license management workflows?"
        ]
    },
    
    # Domain 4: Manage the FinOps Practice
    "finops_practice_operations": {
        "knowledge": [
            "What percentage of your organization understands the role and value of the FinOps practice?",
            "How well do stakeholders understand their roles and responsibilities within the FinOps operating model?"
        ],
        "process": [
            "How well-defined and documented are your FinOps operating procedures and workflows?",
            "What percentage of your FinOps activities follow standardized operating procedures?"
        ],
        "metrics": [
            "What percentage of your FinOps practice objectives have defined success metrics and KPIs?",
            "How effectively do you measure the maturity and effectiveness of your FinOps practice?"
        ],
        "adoption": [
            "What percentage of your organization actively participates in and supports the FinOps practice?",
            "How consistently do teams engage with FinOps processes and follow established practices?"
        ],
        "automation": [
            "What percentage of your FinOps operational tasks are automated?",
            "How automated are your FinOps practice monitoring and reporting processes?"
        ]
    },
    "policy_governance": {
        "knowledge": [
            "What percentage of your organization understands the cloud governance policies and their rationale?",
            "How well do teams understand compliance requirements and governance procedures?"
        ],
        "process": [
            "How comprehensive and well-documented are your cloud governance policies and procedures?",
            "What percentage of your governance policies have defined enforcement mechanisms and compliance monitoring?"
        ],
        "metrics": [
            "What percentage of your cloud resources comply with established governance policies?",
            "How effectively do you measure and track policy compliance and governance effectiveness?"
        ],
        "adoption": [
            "What percentage of your teams consistently follow established governance policies and procedures?",
            "How consistently do teams incorporate governance considerations into their cloud usage decisions?"
        ],
        "automation": [
            "What percentage of your governance policy enforcement is automated?",
            "How automated are your compliance monitoring and violation remediation processes?"
        ]
    },
    "finops_assessment": {
        "knowledge": [
            "What percentage of your organization understands the value and methodology of FinOps maturity assessments?",
            "How well do stakeholders understand how to interpret assessment results and develop improvement plans?"
        ],
        "process": [
            "How systematically and regularly do you conduct FinOps maturity assessments?",
            "What percentage of your assessment results lead to documented improvement plans and actions?"
        ],
        "metrics": [
            "What percentage of your FinOps capabilities have been formally assessed for maturity?",
            "How effectively do you track improvement progress following assessment recommendations?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in and support FinOps assessments?",
            "How consistently do teams implement assessment recommendations and improvement initiatives?"
        ],
        "automation": [
            "What percentage of your assessment data collection and analysis is automated?",
            "How automated are your assessment reporting and improvement tracking processes?"
        ]
    },
    "finops_tools_services": {
        "knowledge": [
            "What percentage of your organization understands the available FinOps tools and their appropriate use cases?",
            "How well do teams understand how to effectively integrate and utilize FinOps tools in their workflows?"
        ],
        "process": [
            "How standardized are your FinOps tool selection, implementation, and management processes?",
            "What percentage of your FinOps tools have defined integration, maintenance, and upgrade procedures?"
        ],
        "metrics": [
            "What percentage of your FinOps requirements are adequately supported by your current tool portfolio?",
            "How effectively do you measure tool utilization, performance, and ROI?"
        ],
        "adoption": [
            "What percentage of your teams consistently use standardized FinOps tools for their cloud management activities?",
            "How consistently do teams leverage tool capabilities to their full potential?"
        ],
        "automation": [
            "What percentage of your FinOps tool management and maintenance activities are automated?",
            "How automated are your tool integration and data synchronization processes?"
        ]
    },
    "finops_education_enablement": {
        "knowledge": [
            "What percentage of your organization has received formal FinOps training appropriate to their role?",
            "How well do different stakeholder groups understand FinOps concepts relevant to their responsibilities?"
        ],
        "process": [
            "How structured and comprehensive is your FinOps education and training program?",
            "What percentage of your training programs include regular updates and continuous learning opportunities?"
        ],
        "metrics": [
            "What percentage of your staff demonstrate measurable improvement in FinOps knowledge and skills after training?",
            "How effectively do you measure the impact of FinOps education on organizational performance?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in available FinOps education and training opportunities?",
            "How consistently do teams apply learned FinOps concepts in their daily work?"
        ],
        "automation": [
            "What percentage of your training delivery and tracking is automated or technology-enabled?",
            "How automated are your learning assessment and certification processes?"
        ]
    },
    "invoicing_chargeback": {
        "knowledge": [
            "What percentage of your organization understands chargeback principles and their business value?",
            "How well do teams understand the invoicing processes and their responsibilities in cost accountability?"
        ],
        "process": [
            "How standardized and comprehensive are your chargeback and invoicing processes?",
            "What percentage of your cloud costs are subject to formal chargeback or showback processes?"
        ],
        "metrics": [
            "What percentage of your invoices and chargebacks are accurate and delivered on time?",
            "How effectively do you measure the impact of chargeback processes on cost accountability and optimization?"
        ],
        "adoption": [
            "What percentage of your business units actively use chargeback information for budget planning and cost management?",
            "How consistently do teams respond to and act on chargeback reports and invoices?"
        ],
        "automation": [
            "What percentage of your invoicing and chargeback processes are automated?",
            "How automated are your chargeback calculation, validation, and distribution processes?"
        ]
    },
    "onboarding_workloads": {
        "knowledge": [
            "What percentage of your teams understand the importance of cost considerations during workload onboarding?",
            "How well do teams understand the onboarding requirements for cost visibility, tagging, and governance?"
        ],
        "process": [
            "How standardized and comprehensive are your workload onboarding processes?",
            "What percentage of new workloads complete all required onboarding steps before going live?"
        ],
        "metrics": [
            "What percentage of newly onboarded workloads are immediately visible in your cost management systems?",
            "How effectively do you measure onboarding compliance and time-to-visibility for new workloads?"
        ],
        "adoption": [
            "What percentage of your development teams consistently follow established onboarding procedures?",
            "How consistently do teams incorporate FinOps requirements into their workload migration and deployment processes?"
        ],
        "automation": [
            "What percentage of your workload onboarding processes are automated?",
            "How automated are your onboarding compliance checks and validation processes?"
        ]
    },
    "intersecting_disciplines": {
        "knowledge": [
            "What percentage of your organization understands how FinOps intersects with other disciplines like Security, DevOps, and ITAM?",
            "How well do teams understand collaboration patterns and shared responsibilities across disciplines?"
        ],
        "process": [
            "How well-established are your cross-functional collaboration processes and governance structures?",
            "What percentage of your projects include formal collaboration with intersecting disciplines from the planning stage?"
        ],
        "metrics": [
            "What percentage of your cross-functional initiatives achieve their intended outcomes and objectives?",
            "How effectively do you measure collaboration effectiveness and shared value creation across disciplines?"
        ],
        "adoption": [
            "What percentage of your teams actively collaborate with intersecting disciplines on cloud-related initiatives?",
            "How consistently do teams incorporate input from intersecting disciplines in their decision-making processes?"
        ],
        "automation": [
            "What percentage of your cross-functional processes and communications are supported by automation?",
            "How automated are your shared workflows and data exchanges between disciplines?"
        ]
    }
}

# Answer options for all questions
ANSWER_OPTIONS = {
    "percentage_questions": [
        "0-20%",
        "21-40%", 
        "41-60%",
        "61-80%",
        "81-100%"
    ],
    "understanding_questions": [
        "No understanding",
        "Basic awareness",
        "Good understanding",
        "Comprehensive understanding",
        "Expert level understanding"
    ],
    "standardization_questions": [
        "No standardization",
        "Ad-hoc processes",
        "Some standardization",
        "Mostly standardized",
        "Fully standardized and documented"
    ],
    "consistency_questions": [
        "No consistency",
        "Occasional adherence",
        "Moderate consistency",
        "High consistency",
        "Full compliance with standards"
    ],
    "measurement_questions": [
        "No measurement",
        "Basic tracking",
        "Moderate measurement",
        "Comprehensive metrics",
        "Advanced analytics with trends"
    ],
    "effectiveness_questions": [
        "Not effective",
        "Slightly effective",
        "Moderately effective",
        "Highly effective",
        "Extremely effective with predictive capabilities"
    ],
    "automation_questions": [
        "Fully manual",
        "Basic automation",
        "Moderate automation",
        "Highly automated",
        "Fully automated with intelligent capabilities"
    ]
}

# Helper functions
def send_email(to_email, subject, body):
    """Send email using SMTP"""
    try:
        email_user = os.getenv('EMAIL_USER')
        email_pass = os.getenv('EMAIL_PASS')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        if not email_user or not email_pass:
            print("Email configuration not found. Skipping email send.")
            return False
        
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
    """Generate specific question for capability + lens + scope combination using the new question structure"""
    
    # Get the questions for this capability and lens
    capability_questions = QUESTIONS.get(capability, {})
    lens_questions = capability_questions.get(lens, [])
    
    # Get scope name for context
    scope_name = next((s['name'] for s in SCOPES if s['id'] == scope), scope)
    
    # If we have specific questions for this capability and lens, randomly select one
    if lens_questions:
        import random
        # Randomly select one question from the available questions for this capability+lens
        question_text = random.choice(lens_questions)
        return question_text
    
    # Fallback to a generic question if no specific question is found
    capability_name = next((c['name'] for c in CAPABILITIES if c['id'] == capability), capability)
    lens_name = next((l['name'] for l in LENSES if l['id'] == lens), lens)
    
    return f"Please describe your organization's {lens_name.lower()} regarding {capability_name} for {scope_name}."

def get_answer_options(question_text):
    """Determine appropriate answer options based on question content"""
    question_lower = question_text.lower()
    
    if "percentage" in question_lower or "what percentage" in question_lower:
        return ANSWER_OPTIONS["percentage_questions"]
    elif "understanding" in question_lower or "how well" in question_lower or "understand" in question_lower:
        return ANSWER_OPTIONS["understanding_questions"]
    elif "standardized" in question_lower or "standardization" in question_lower:
        return ANSWER_OPTIONS["standardization_questions"]
    elif "consistency" in question_lower or "consistently" in question_lower:
        return ANSWER_OPTIONS["consistency_questions"]
    elif "measure" in question_lower or "measurement" in question_lower or "track" in question_lower:
        return ANSWER_OPTIONS["measurement_questions"]
    elif "effective" in question_lower or "effectiveness" in question_lower:
        return ANSWER_OPTIONS["effectiveness_questions"]
    elif "automated" in question_lower or "automation" in question_lower:
        return ANSWER_OPTIONS["automation_questions"]
    else:
        # Default to percentage questions
        return ANSWER_OPTIONS["percentage_questions"]

# Helper to get OpenAI client
@lru_cache(maxsize=1)
def get_openai_client():
    import openai
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
    return openai.OpenAI(api_key=api_key, base_url=base_url)

def evaluate_finops_maturity(capability_name, lens_name, answer_level, answer_details, scope_name):
    """
    Evaluate FinOps maturity based on the FinOps Foundation Assessment Guide
    """
    # Map answer levels to maturity scores
    level_mapping = {
        '0-20%': 0,
        '21-40%': 1,
        '41-60%': 2,
        '61-80%': 3,
        '81-100%': 4
    }
    
    # Get base score from level selection
    base_score = level_mapping.get(answer_level, 2)
    
    # FinOps Foundation maturity characteristics
    maturity_characteristics = {
        0: {
            'name': 'Crawl',
            'description': 'No capability or awareness',
            'characteristics': [
                'No processes, tools, or understanding',
                'Ad-hoc activities with no formal structure',
                'No dedicated resources or ownership',
                'Reactive approach to cost management'
            ]
        },
        1: {
            'name': 'Walk',
            'description': 'Basic awareness and ad-hoc activities',
            'characteristics': [
                'Limited understanding and inconsistent execution',
                'Some basic tools but no formal processes',
                'Occasional activities without systematic approach',
                'Basic cost visibility with manual processes'
            ]
        },
        2: {
            'name': 'Run',
            'description': 'Some processes in place',
            'characteristics': [
                'Inconsistent execution with basic tools',
                'Partial understanding and occasional success',
                'Some formal processes but not consistently applied',
                'Regular cost reviews with some automation'
            ]
        },
        3: {
            'name': 'Fly',
            'description': 'Well-defined processes',
            'characteristics': [
                'Consistent execution with good tools',
                'Strong understanding and regular success',
                'Formal processes with clear ownership',
                'Proactive cost optimization with good visibility'
            ]
        },
        4: {
            'name': 'Optimize',
            'description': 'Optimized and automated',
            'characteristics': [
                'Continuous improvement with advanced tools',
                'Expert level understanding and consistent excellence',
                'Automated processes with predictive capabilities',
                'Strategic cost management with predictive analytics'
            ]
        }
    }
    
    # Analyze the detailed response for additional insights
    details_lower = answer_details.lower()
    
    # Adjust score based on detailed response analysis
    score_adjustment = 0
    
    # Positive indicators
    positive_indicators = [
        'automated', 'automation', 'consistent', 'processes', 'formal', 'structured',
        'tools', 'platform', 'dashboard', 'monitoring', 'tracking', 'optimization',
        'governance', 'policies', 'standards', 'training', 'education', 'team',
        'ownership', 'responsibility', 'metrics', 'kpis', 'reporting', 'analysis'
    ]
    
    # Negative indicators
    negative_indicators = [
        'manual', 'ad-hoc', 'inconsistent', 'no process', 'no tools', 'no understanding',
        'limited', 'basic', 'occasional', 'reactive', 'no ownership', 'no responsibility',
        'no monitoring', 'no tracking', 'no optimization', 'no governance'
    ]
    
    positive_count = sum(1 for indicator in positive_indicators if indicator in details_lower)
    negative_count = sum(1 for indicator in negative_indicators if indicator in details_lower)
    
    # Adjust score based on indicators
    if positive_count > negative_count:
        score_adjustment = min(1, (positive_count - negative_count) / 3)
    elif negative_count > positive_count:
        score_adjustment = max(-1, -(negative_count - positive_count) / 3)
    
    final_score = max(0, min(4, base_score + score_adjustment))
    
    # Get maturity level info
    maturity_info = maturity_characteristics[int(final_score)]
    
    # Generate improvement suggestions based on current level
    improvement_suggestions = generate_improvement_suggestions(capability_name, lens_name, final_score, maturity_info)
    
    return {
        'score': final_score,
        'maturity_level': maturity_info['name'],
        'description': maturity_info['description'],
        'characteristics': maturity_info['characteristics'],
        'improvement_suggestions': improvement_suggestions,
        'confidence': 'High' if abs(score_adjustment) < 0.5 else 'Medium',
        'industry_comparison': get_industry_comparison(final_score, capability_name, lens_name),
        'risks': get_risks(final_score, capability_name, lens_name)
    }

def generate_improvement_suggestions(capability_name, lens_name, current_score, maturity_info):
    """Generate specific improvement suggestions based on current maturity level"""
    
    suggestions = {
        0: [
            "Establish basic awareness and understanding of FinOps principles",
            "Begin with simple cost visibility and basic reporting",
            "Identify key stakeholders and establish initial ownership",
            "Start with manual processes and basic tools"
        ],
        1: [
            "Develop formal processes and procedures",
            "Implement basic automation and tooling",
            "Establish regular review cycles and governance",
            "Begin training and education programs"
        ],
        2: [
            "Standardize processes across the organization",
            "Enhance automation and tool integration",
            "Implement comprehensive monitoring and alerting",
            "Develop advanced analytics and reporting capabilities"
        ],
        3: [
            "Optimize existing processes for efficiency",
            "Implement predictive analytics and forecasting",
            "Enhance cross-team collaboration and communication",
            "Develop advanced automation and AI capabilities"
        ],
        4: [
            "Focus on continuous improvement and innovation",
            "Implement advanced predictive and prescriptive analytics",
            "Develop strategic cost optimization strategies",
            "Establish industry leadership and best practices"
        ]
    }
    
    base_suggestions = suggestions.get(int(current_score), suggestions[2])
    
    # Add capability-specific suggestions
    capability_suggestions = get_capability_specific_suggestions(capability_name, lens_name, current_score)
    
    return base_suggestions + capability_suggestions

def get_capability_specific_suggestions(capability_name, lens_name, current_score):
    """Get specific suggestions based on capability and lens"""
    
    suggestions = {
        'data_ingestion': {
            'knowledge': [
                "Implement data governance and quality standards",
                "Establish data lineage and documentation processes",
                "Develop data validation and monitoring capabilities"
            ],
            'process': [
                "Standardize data ingestion workflows",
                "Implement automated data quality checks",
                "Establish data ownership and responsibility"
            ]
        },
        'allocation': {
            'knowledge': [
                "Develop comprehensive tagging strategies",
                "Establish cost allocation methodologies",
                "Implement chargeback and showback processes"
            ],
            'process': [
                "Standardize allocation rules and policies",
                "Implement automated allocation processes",
                "Establish allocation review and approval workflows"
            ]
        }
        # Add more capabilities as needed
    }
    
    capability_suggestions = suggestions.get(capability_name, {}).get(lens_name, [])
    
    # Filter suggestions based on current score
    if current_score < 2:
        return capability_suggestions[:2]  # Focus on basics
    elif current_score < 3:
        return capability_suggestions[:3]  # Add intermediate suggestions
    else:
        return capability_suggestions  # All suggestions for advanced levels

def get_industry_comparison(score, capability_name, lens_name):
    """Get industry comparison based on score and capability"""
    
    if score <= 1:
        return f"Below average for {capability_name} {lens_name} - 30% of organizations are at this level"
    elif score <= 2:
        return f"Average for {capability_name} {lens_name} - 55% of organizations are at this level"
    elif score <= 3:
        return f"Above average for {capability_name} {lens_name} - 15% of organizations reach this level"
    else:
        return f"Leading edge for {capability_name} {lens_name} - Top 5% of organizations achieve this level"

def get_risks(score, capability_name, lens_name):
    """Get potential risks based on current maturity level"""
    
    if score <= 1:
        return f"High risk of cost overruns and inefficiencies in {capability_name} {lens_name}. Lack of visibility and control may lead to significant financial impact."
    elif score <= 2:
        return f"Moderate risk in {capability_name} {lens_name}. Inconsistent processes may lead to missed optimization opportunities and increased costs."
    elif score <= 3:
        return f"Low risk in {capability_name} {lens_name}. Well-established processes provide good control and optimization capabilities."
    else:
        return f"Minimal risk in {capability_name} {lens_name}. Advanced capabilities provide excellent control and optimization."

def generate_recommendations(assessment_id, scope_id, domain, overall_percentage, lens_scores):
    """Generate concise, actionable recommendations using OpenAI API, based on lowest scores from Results Matrix."""
    try:
        # Get all responses for this assessment
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT capability_id, lens_id, answer, score, improvement_suggestions, evidence_files
            FROM responses 
            WHERE assessment_id = ?
            ORDER BY capability_id, lens_id
        ''', (assessment_id,))
        responses = cursor.fetchall()
        conn.close()
        
        # Build results matrix to find lowest scores
        results_matrix = {}
        lowest_scores = []
        
        for capability_id, lens_id, answer, score, improvement, evidence_files in responses:
            if not capability_id or not lens_id:
                continue
            if capability_id not in results_matrix:
                results_matrix[capability_id] = {}
            
            score_value = score or 0
            results_matrix[capability_id][lens_id] = {
                'score': score_value,
                'answer': answer,
                'improvement': improvement or 'No suggestions available'
            }
            
            # Get capability and lens names
            capability_name = next((c['name'] for c in CAPABILITIES if c['id'] == capability_id), capability_id)
            lens_name = next((l['name'] for l in LENSES if l['id'] == lens_id), lens_id)
            
            # Add to lowest scores list for sorting
            lowest_scores.append({
                'capability_id': capability_id,
                'capability_name': capability_name,
                'lens_id': lens_id,
                'lens_name': lens_name,
                'score': score_value,
                'answer': answer,
                'improvement': improvement or 'No suggestions available'
            })
        
        # Sort by score (ascending) to get lowest scores first
        lowest_scores.sort(key=lambda x: x['score'])
        
        # Take up to 5 lowest scores for recommendations
        target_recommendations = lowest_scores[:5]
        
        # Prepare summary for OpenAI
        assessment_summary = f"""
        Assessment Summary:
        - Scope: {next((s['name'] for s in SCOPES if s['id'] == scope_id), scope_id)}
        - Overall Score: {overall_percentage}%
        - Domain: {domain}
        """
        
        # Prepare lowest scores context for OpenAI
        lowest_scores_context = "\nLowest Scoring Areas (Focus for Recommendations):\n"
        for item in target_recommendations:
            lowest_scores_context += f"- {item['capability_name']} ({item['lens_name']}): Score {item['score']}/4\n"
            lowest_scores_context += f"  Answer: {item['answer'][:150]}{'...' if len(item['answer']) > 150 else ''}\n"
            lowest_scores_context += f"  Current Improvement: {item['improvement'][:150]}{'...' if len(item['improvement']) > 150 else ''}\n\n"
        
        # Updated prompt to focus on lowest scores with new structure
        prompt = f"""
        You are a FinOps expert. Based on the user's lowest scoring areas below, provide exactly {len(target_recommendations)} concise, actionable recommendations for FinOps maturity improvement. Focus on the areas with the lowest scores.

        CRITICAL: You must output ONLY the recommendations in this EXACT format, with NO extra text, headers, or explanations:

        Title: [Title of Recommendation]
        Description: [Brief description of the recommendation]
        Why it is important: [Explanation of why this matters for FinOps maturity]
        Recommendation: [Specific actionable steps to implement]

        Title: [Title of Recommendation]
        Description: [Brief description of the recommendation]
        Why it is important: [Explanation of why this matters for FinOps maturity]
        Recommendation: [Specific actionable steps to implement]

        Continue this format for all {len(target_recommendations)} recommendations. Do NOT include any introduction, summary, section headers, or extra text. Do NOT number the recommendations. Do NOT use any other labels or formatting.

        {assessment_summary}
        {lowest_scores_context}
        """
        
        # Call OpenAI API
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are a FinOps expert. You must output EXACTLY {len(target_recommendations)} recommendations in the specified format. Each recommendation must have: Title:, Description:, Why it is important:, and Recommendation:. Do NOT include any extra text, headers, explanations, or numbering. Only output the required fields in the exact order. Focus on the lowest scoring areas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.5
            )
            recommendations = response.choices[0].message.content
            if recommendations is None:
                recommendations = ''
            
            # Clean up the recommendations to ensure proper formatting
            import re
            
            # Remove any extra text at the beginning or end
            recommendations = re.sub(r'^(Executive Summary|Introduction|Conclusion|Summary|Here are|Based on|I\'ll provide).*?\n', '', recommendations, flags=re.DOTALL | re.IGNORECASE)
            recommendations = re.sub(r'\n\n+', '\n\n', recommendations)
            recommendations = recommendations.strip()
            
            # Ensure we have the proper structure
            if not re.search(r'Description:', recommendations):
                # If the AI didn't follow the format, create a fallback structure
                lines = recommendations.split('\n')
                formatted_recommendations = []
                current_recommendation = []
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('Description:') and not line.startswith('Why it is important:') and not line.startswith('Recommendation:'):
                        if current_recommendation:
                            formatted_recommendations.append('\n'.join(current_recommendation))
                            current_recommendation = []
                        current_recommendation.append(line)
                        current_recommendation.append('Description: Brief description of this recommendation')
                        current_recommendation.append('Why it is important: This will help improve your FinOps maturity')
                        current_recommendation.append('Recommendation: Implement specific steps to address this area')
                
                if current_recommendation:
                    formatted_recommendations.append('\n'.join(current_recommendation))
                
                recommendations = '\n\n'.join(formatted_recommendations)
                
        except Exception as e:
            print(f"OpenAI API error: {e}")
            recommendations = "Unable to generate recommendations at this time. Please try again later."
        
        # Store recommendations in database ONLY if successful
        if recommendations and "Unable to generate recommendations" not in recommendations:
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

# Token serializer for email confirmation
serializer = URLSafeTimedSerializer(app.secret_key or 'fallback-secret-key')

@app.route('/register', methods=['POST'])
def register():
    try:
        email = request.form.get('email', '').strip().lower()
        if not email:
            return jsonify({"status": "error", "message": "Email is required"})
        public_domains = [
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'aol.com', 'icloud.com', 'protonmail.com',
            'mail.com', 'zoho.com', 'gmx.com', 'yandex.com', 'live.com', 'msn.com', 'me.com', 'pm.me', 'fastmail.com'
        ]
        domain = email.split('@')[1] if '@' in email else ''
        if domain in public_domains:
            return jsonify({"status": "error", "message": "Please use your corporate email address to register."})
        email_hash = hash_email(email)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM users WHERE email_hash = ?', (email_hash,))
            if cursor.fetchone():
                return jsonify({"status": "error", "message": "Email already registered"})
        finally:
            conn.close()
        # Generate signed token with email and domain
        token = serializer.dumps({'email': email, 'domain': domain})
        if send_confirmation_email(email, token):
            return jsonify({
                "status": "success", 
                "message": "Registration successful! Please check your email to confirm your account, then use the login tab to request a magic link."
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send confirmation email. Please try again."
            })
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"status": "error", "message": "Registration failed. Please try again."})

@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('email', '').strip().lower()
        if not email:
            return jsonify({"status": "error", "message": "Email is required"})
        email_hash = hash_email(email)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, is_confirmed FROM users WHERE email_hash = ?', (email_hash,))
        user = cursor.fetchone()
        conn.close()
        if not user:
            return jsonify({"status": "error", "message": "User not found. Please register first."})
        if not user[1]:
            return jsonify({"status": "error", "message": "Please confirm your email first before logging in."})
        # Generate magic link token
        magic_token = secrets.token_urlsafe(32)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET confirmation_token = ? WHERE id = ?', (magic_token, user[0]))
        conn.commit()
        conn.close()
        if send_magic_link(email, magic_token):
            return jsonify({"status": "success", "message": "Magic link sent! Check your email and click the link to login."})
        else:
            return jsonify({"status": "error", "message": "Failed to send magic link. Please try again or contact support."})
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"status": "error", "message": "Login failed. Please try again."})

@app.route('/magic_login/<token>')
def magic_login(token):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, email_hash, is_confirmed FROM users WHERE confirmation_token = ?', (token,))
        user = cursor.fetchone()
        if user:
            cursor.execute('UPDATE users SET confirmation_token = NULL WHERE id = ?', (user[0],))
            conn.commit()
            session['user_id'] = user[0]
            session['user_hash'] = user[1]
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
        # Decode token and check expiry (24h)
        try:
            data = serializer.loads(token, max_age=86400)
            email = data['email']
            domain = data['domain']
        except SignatureExpired:
            return render_template('email_error.html', message="Confirmation link expired.")
        except BadSignature:
            return render_template('email_error.html', message="Invalid confirmation link.")
        email_hash = hash_email(email)
        company_hash = hash_company(domain) if domain else None
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, is_confirmed FROM users WHERE email_hash = ?', (email_hash,))
        user = cursor.fetchone()
        if user:
            if user[1]:
                conn.close()
                return render_template('email_confirmed.html')
            else:
                cursor.execute('UPDATE users SET is_confirmed = 1, confirmation_token = NULL WHERE id = ?', (user[0],))
                conn.commit()
                conn.close()
                return render_template('email_confirmed.html')
        # Insert new confirmed user
        cursor.execute('''
            INSERT INTO users (email_hash, company_hash, is_confirmed, confirmation_token)
            VALUES (?, ?, 1, NULL)
        ''', (email_hash, company_hash))
        conn.commit()
        conn.close()
        return render_template('email_confirmed.html')
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
                         assessments=assessments,
                         scopes=SCOPES,
                         domains=DOMAINS)

@app.route('/start_assessment', methods=['POST'])
def start_assessment():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Please log in first"})
    
    try:
        domain = request.form.get('domain', '')  # Empty string for complete assessment
        scope_id = request.form.get('scope_id', 'public_cloud')  # Default to public cloud
        
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
    print(f"Assessment route called. Session: {session}")
    if 'user_id' not in session:
        return redirect('/')
    
    if 'current_assessment_id' not in session:
        return redirect('/dashboard')
    
    return render_template('assessment.html')

@app.route('/get_assessment_progress')
def get_assessment_progress():
    print(f"get_assessment_progress called. Session: {session}")
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
                answer_options = get_answer_options(question_text)
                questions.append({
                    'capability_id': capability['id'],
                    'capability_name': capability['name'],
                    'lens_id': lens['id'],
                    'lens_name': lens['name'],
                    'domain': capability['domain'],
                    'question': question_text,
                    'answer_options': answer_options
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
        answer_level = request.form.get('answer_level', '').strip()
        answer_details = request.form.get('answer_details', '').strip()
        
        if not all([capability_id, lens_id, answer_level]):
            return jsonify({"status": "error", "message": "Capability, lens, and maturity level are required"})
        # answer_details is now optional
        
        # Combine level and details for storage
        answer = f"Level: {answer_level}\nDetails: {answer_details}"
        
                # Default score - will be processed with AI later
        score = 2
        improvement = "Will be analyzed when assessment is completed"
        
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
                SET answer = ?, score = ?, improvement_suggestions = ?
                WHERE id = ?
            ''', (answer, score, improvement, existing[0]))
        else:
            # Insert new response
            cursor.execute('''
                INSERT INTO responses (assessment_id, capability_id, lens_id, answer, score, improvement_suggestions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (assessment_id, capability_id, lens_id, answer, score, improvement))
        
        # Update assessment timestamp
        cursor.execute('''
            UPDATE assessments 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (assessment_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": "Response saved successfully"
        })
        
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
        
        # Process all responses with AI analysis
        cursor.execute('''
            SELECT capability_id, lens_id, answer, id
            FROM responses 
            WHERE assessment_id = ?
        ''', (assessment_id,))
        responses = cursor.fetchall()
        
        scope_name = next((s['name'] for s in SCOPES if s['id'] == scope_id), scope_id)
        
        # Process each response with AI
        for capability_id, lens_id, answer, response_id in responses:
            try:
                capability_name = next((c['name'] for c in CAPABILITIES if c['id'] == capability_id), capability_id)
                lens_name = next((l['name'] for l in LENSES if l['id'] == lens_id), lens_id)
                
                # Parse answer to get level and details
                answer_lines = answer.split('\n')
                answer_level = ""
                answer_details = ""
                
                for line in answer_lines:
                    if line.startswith('Level: '):
                        answer_level = line.replace('Level: ', '').strip()
                    elif line.startswith('Details: '):
                        answer_details = line.replace('Details: ', '').strip()
                
                # Use the FinOps maturity evaluation function
                evaluation_result = evaluate_finops_maturity(capability_name, lens_name, answer_level, answer_details, scope_name)
                
                score = evaluation_result['score']
                improvement = "\n".join(evaluation_result['improvement_suggestions'])
                
                # Update the response with AI analysis
                cursor.execute('''
                    UPDATE responses 
                    SET score = ?, improvement_suggestions = ?
                    WHERE id = ?
                ''', (score, improvement, response_id))
                
            except Exception as e:
                print(f"AI processing error for response {response_id}: {e}")
                # Keep default score if AI processing fails
                continue
        
        # Recalculate overall percentage after AI processing
        cursor.execute('SELECT score FROM responses WHERE assessment_id = ?', (assessment_id,))
        updated_responses = cursor.fetchall()
        
        total_score = sum(r[0] or 0 for r in updated_responses)
        total_possible = len(updated_responses) * 4
        overall_percentage = round((total_score / total_possible) * 100) if total_possible > 0 else 0
        
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
        
        # Get domain and user company hash for benchmark filtering
        domain = assessment[3]
        cursor.execute('SELECT company_hash FROM users WHERE id = ?', (session['user_id'],))
        user_result = cursor.fetchone()
        user_company_hash = user_result[0] if user_result else None
        
        # Get benchmark data (other completed assessments with same domain and different companies)
        cursor.execute('''
            SELECT u.company_hash, a.id
            FROM assessments a
            JOIN users u ON a.user_id = u.id
            WHERE a.domain = ? AND a.status = 'completed' AND a.id != ? AND u.company_hash != ?
            ORDER BY a.updated_at DESC
            LIMIT 10
        ''', (domain, assessment_id, user_company_hash))
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
        
        should_generate = (
            assessment[4] == 'completed' and (
                not recommendations or
                "Unable to generate recommendations" in recommendations
            )
        )

        if should_generate:
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
        
        def parse_recommendations(recommendations):
            import re
            blocks = re.split(r'(?:^|\n)Title:', recommendations)
            parsed = []
            for block in blocks:
                block = block.strip()
                if not block:
                    continue
                title_match = re.search(r'^(.*?)(?:\n|$)', block)
                desc_match = re.search(r'Description:(.*?)(?:\n|$)', block, re.DOTALL)
                why_match = re.search(r'Why (?:it matters|it is important):(.*?)(?:\n|$)', block, re.DOTALL)
                rec_match = re.search(r'Recommendation:(.*)', block, re.DOTALL)
                # Only add if all fields are present
                if title_match and desc_match and why_match and rec_match:
                    parsed.append({
                        'title': title_match.group(1).strip(),
                        'description': desc_match.group(1).strip(),
                        'why': why_match.group(1).strip(),
                        'recommendation': rec_match.group(1).strip(),
                    })
            return parsed
        parsed_recommendations = parse_recommendations(recommendations) if recommendations else []
        
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
                             recommendations=recommendations,
                             parsed_recommendations=parsed_recommendations,
                             benchmark_data=benchmark_data)
        
    except Exception as e:
        print(f"Get assessment results error: {e}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        return render_template('error.html', message=f"An error occurred while retrieving assessment results: {e}"), 500

@app.route('/export_pdf/<int:assessment_id>')
def export_pdf(assessment_id):
    """Export assessment results as PDF"""
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        # Get assessment details (reuse logic from get_assessment_results)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, user_id, scope_id, domain, status, overall_percentage, recommendations, created_at, updated_at
            FROM assessments 
            WHERE id = ? AND user_id = ?
        '''
        
        cursor.execute(query, (assessment_id, session['user_id']))
        assessment = cursor.fetchone()
        
        if not assessment:
            conn.close()
            return render_template('error.html', message="Assessment not found or you do not have access to it."), 404
        
        # Get scope information
        scope_id = assessment[2]
        scope = next((s for s in SCOPES if s['id'] == scope_id), None)
        if not scope:
            conn.close()
            return render_template('error.html', message="Assessment scope not found."), 404
        
        # Get responses
        cursor.execute('''
            SELECT capability_id, lens_id, answer, score, improvement_suggestions
            FROM responses 
            WHERE assessment_id = ?
        ''', (assessment_id,))
        responses = cursor.fetchall()
        
        # Get user information (privacy-focused - no personal data stored)
        cursor.execute('SELECT company_hash FROM users WHERE id = ?', (session['user_id'],))
        user_info = cursor.fetchone()
        user_name = "Anonymous User"  # No personal data stored
        organization = f"Company {chr(65 + (hash(user_info[0]) % 26))}" if user_info and user_info[0] else "Unknown Organization"
        
        # Get domain for benchmark filtering
        domain = assessment[3]
        user_company_hash = user_info[0] if user_info else None
        
        # Get benchmark data (other completed assessments with same domain and different companies)
        cursor.execute('''
            SELECT u.company_hash, a.id
            FROM assessments a
            JOIN users u ON a.user_id = u.id
            WHERE a.domain = ? AND a.status = 'completed' AND a.id != ? AND u.company_hash != ?
            ORDER BY a.updated_at DESC
            LIMIT 10
        ''', (domain, assessment_id, user_company_hash))
        benchmark_assessments = cursor.fetchall()
        if benchmark_assessments is None:
            benchmark_assessments = []
        conn.close()
        
        # Calculate scores (reuse logic from get_assessment_results)
        results_matrix = {}
        total_score = 0
        total_possible = 0
        for response in responses:
            capability_id, lens_id, answer, score, improvement = response
            if not capability_id or not lens_id:
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
        
        # Calculate overall percentage
        overall_percentage = round((total_score / total_possible) * 100) if total_possible > 0 else 0
        
        # Generate benchmark data
        benchmark_data = []
        user_score = None
        other_scores = []
        if len(benchmark_assessments) >= 1:
            for i, (org_name, bench_id) in enumerate(benchmark_assessments):
                if not bench_id:
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
                    'organization': f"Company {chr(65 + i)}",
                    'overall_percentage': bench_percentage
                })
            benchmark_data.append({
                'organization': 'Your Organization',
                'overall_percentage': overall_percentage
            })
            benchmark_data.sort(key=lambda x: x['overall_percentage'], reverse=True)
            for org in benchmark_data:
                if org['organization'] == 'Your Organization':
                    user_score = org['overall_percentage']
                else:
                    other_scores.append(org['overall_percentage'])
            industry_avg = round(sum(other_scores) / len(other_scores), 1) if other_scores else 0
        else:
            user_score = overall_percentage
            industry_avg = 0
        
        # Get capabilities for display
        domain = assessment[3]
        if domain:
            capabilities = [c for c in CAPABILITIES if c['domain'] == domain]
        else:
            capabilities = CAPABILITIES
        
        # Get recommendations
        recommendations = assessment[6] if len(assessment) > 6 and assessment[6] else None
        
        # Generate PDF content
        html_content = render_template('pdf_results.html',
                                     assessment=assessment,
                                     scope=scope,
                                     domain=domain,
                                     capabilities=capabilities,
                                     results_matrix=results_matrix,
                                     total_score=total_score,
                                     total_possible=total_possible,
                                     overall_percentage=overall_percentage,
                                     user_name=user_name,
                                     organization=organization,
                                     recommendations=recommendations,
                                     parsed_recommendations=parsed_recommendations,
                                     benchmark_data=benchmark_data,
                                     user_score=user_score,
                                     industry_avg=industry_avg,
                                     lenses=LENSES)
        
        # Convert HTML to PDF
        pdf = HTML(string=html_content).write_pdf()
        
        # Create BytesIO object and return as file
        pdf_buffer = BytesIO(pdf if pdf else b'')
        pdf_buffer.seek(0)
        
        filename = f"finops_assessment_{assessment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"PDF export error: {e}")
        import traceback
        print(f"[DEBUG] PDF export traceback: {traceback.format_exc()}")
        return render_template('error.html', message=f"An error occurred while generating PDF: {e}"), 500

def get_company_mapping(users):
    """Return a mapping of email domain to anonymized company name (Company A, B, ...)."""
    domains = []
    domain_to_company = {}
    for user in users:
        email = user[2]  # decrypted email
        domain = email.split('@')[1].lower() if '@' in email else 'unknown'
        if domain not in domains:
            domains.append(domain)
        idx = domains.index(domain)
        domain_to_company[domain] = f"Company {chr(65 + (idx % 26))}"
    return domain_to_company

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT created_at FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return redirect('/')
        
        return render_template('settings.html', user_created_at=user[0][:10] if user[0] else 'Unknown')
        
    except Exception as e:
        print(f"Settings error: {e}")
        return redirect('/')

@app.route('/delete_account', methods=['DELETE'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Please log in first"}), 401
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({"status": "error", "message": "User not found"}), 404
        
        # Delete user's assessments and responses
        cursor.execute('DELETE FROM responses WHERE assessment_id IN (SELECT id FROM assessments WHERE user_id = ?)', (session['user_id'],))
        cursor.execute('DELETE FROM assessments WHERE user_id = ?', (session['user_id'],))
        cursor.execute('DELETE FROM users WHERE id = ?', (session['user_id'],))
        
        conn.commit()
        conn.close()
        
        # Clear session
        session.clear()
        
        return jsonify({"status": "success", "message": "Account deleted successfully"})
        
    except Exception as e:
        print(f"Delete account error: {e}")
        return jsonify({"status": "error", "message": "Failed to delete account"}), 500

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
    # Fix [https://...](https://...) to just the URL as a clickable link
    import re
    def fix_url_links(md):
        # Replace [https://...](https://...) with just the URL as a clickable link
        return re.sub(r'\[https?://([^\]]+)\]\((https?://[^)]+)\)', r'\2', md)
    text = fix_url_links(text)
    html = markdown.markdown(text, extensions=['extra', 'sane_lists', 'smarty'])
    # Pós-processar para adicionar target e rel em todos os links
    html = re.sub(r'<a (href="https?://[^"]+")', r'<a \1 target="_blank" rel="noopener noreferrer"', html)
    return html

def fix_real_example_links(html_text):
    # Substitui links de real example que apontam para finops.org
    return re.sub(r'(Real Example:.*?)(<a [^>]*href=["\\\']https?://(?:www\.)?finops\.org[^>]+>.*?</a>)',
                  r'\1 <span style="color:#e53e3e;font-weight:bold">[Exemplo real não encontrado, consulte <a href=\"https://news.google.com/search?q=finops\" target=\"_blank\">Google News</a>]</span>',
                  html_text, flags=re.IGNORECASE)

@app.route('/dashboard/stats')
def dashboard_stats():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        cursor.execute('SELECT COUNT(DISTINCT company_hash) FROM users WHERE company_hash IS NOT NULL')
        total_companies = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM assessments')
        total_assessments = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM assessments WHERE status = "completed"')
        completed_assessments = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM assessments WHERE status = "in_progress"')
        in_progress_assessments = cursor.fetchone()[0]
        conn.close()
        return jsonify({
            'stats': {
                'total_users': len(users),
                'total_companies': total_companies,
                'in_progress_assessments': in_progress_assessments,
                'completed_assessments': completed_assessments
            }
        })
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return jsonify({"error": "Failed to fetch stats"}), 500

def hash_email(email):
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()

@app.route('/set_current_assessment/<int:assessment_id>')
def set_current_assessment(assessment_id):
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        # Verify the assessment belongs to the current user
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT scope_id, domain FROM assessments 
            WHERE id = ? AND user_id = ?
        ''', (assessment_id, session['user_id']))
        assessment = cursor.fetchone()
        conn.close()
        
        if not assessment:
            return redirect('/dashboard')
        
        # Set current assessment in session
        session['current_assessment_id'] = assessment_id
        session['current_scope'] = assessment[0]
        session['current_domain'] = assessment[1]
        
        return redirect('/assessment')
        
    except Exception as e:
        print(f"Set current assessment error: {e}")
        return redirect('/dashboard')

@app.route('/test_openai')
def test_openai():
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello!"}],
            max_tokens=5,
            temperature=0.1
        )
        test_message = response.choices[0].message.content
        return jsonify({'status': 'success', 'message': test_message})
    except Exception as e:
        import traceback
        return jsonify({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/reprocess_response/<int:assessment_id>/<capability_id>/<lens_id>')
def reprocess_response(assessment_id, capability_id, lens_id):
    """Reprocess an existing response with AI analysis"""
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Please log in first"})
    
    try:
        # Get the existing response
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT answer, score, improvement_suggestions
            FROM responses 
            WHERE assessment_id = ? AND capability_id = ? AND lens_id = ?
        ''', (assessment_id, capability_id, lens_id))
        response = cursor.fetchone()
        
        if not response:
            conn.close()
            return jsonify({"status": "error", "message": "Response not found"})
        
        answer = response[0]
        old_score = response[1]
        old_improvement = response[2]
        
        # Get assessment and scope details
        cursor.execute('SELECT scope_id, domain FROM assessments WHERE id = ?', (assessment_id,))
        assessment = cursor.fetchone()
        scope_id = assessment[0]
        domain = assessment[1]
        
        conn.close()
        
        # Get names for context
        scope_name = next((s['name'] for s in SCOPES if s['id'] == scope_id), scope_id)
        capability_name = next((c['name'] for c in CAPABILITIES if c['id'] == capability_id), capability_id)
        lens_name = next((l['name'] for l in LENSES if l['id'] == lens_id), lens_id)
        
        # Reprocess with AI
        try:
            api_key = os.getenv('OPENAI_API_KEY') or os.getenv('XAI_API_KEY')
            if api_key:
                if os.getenv('XAI_API_KEY'):
                    client = openai.OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
                else:
                    client = get_openai_client()
                
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
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3
                )
                
                ai_response = response.choices[0].message.content
                
                # Parse AI response
                score = 2  # Default score
                improvement = "Continue developing this capability with structured processes and regular reviews."
                
                if ai_response and "SCORE:" in ai_response:
                    try:
                        score_line = [line for line in ai_response.split('\n') if 'SCORE:' in line][0]
                        score = int(score_line.split(':')[1].strip())
                    except:
                        pass
                
                if ai_response and "IMPROVEMENT:" in ai_response:
                    try:
                        improvement_lines = ai_response.split('IMPROVEMENT:')[1].strip()
                        improvement = improvement_lines
                    except:
                        pass
                
                # Update the response in database
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE responses 
                    SET score = ?, improvement_suggestions = ?
                    WHERE assessment_id = ? AND capability_id = ? AND lens_id = ?
                ''', (score, improvement, assessment_id, capability_id, lens_id))
                conn.commit()
                conn.close()
                
                return jsonify({
                    "status": "success", 
                    "message": "Response reprocessed successfully",
                    "old_score": old_score,
                    "new_score": score,
                    "old_improvement": old_improvement,
                    "new_improvement": improvement
                })
            else:
                return jsonify({"status": "error", "message": "OpenAI API key not configured"})
                
        except Exception as e:
            print(f"AI reprocessing error: {e}")
            return jsonify({"status": "error", "message": f"AI analysis failed: {str(e)}"})
        
    except Exception as e:
        print(f"Reprocess response error: {e}")
        return jsonify({"status": "error", "message": "Failed to reprocess response"})

@app.route('/my_responses')
def my_responses():
    """Show all responses for the current user with their IDs"""
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Please log in first"})
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.assessment_id, r.capability_id, r.lens_id, r.answer, r.score, r.improvement_suggestions
            FROM responses r
            JOIN assessments a ON r.assessment_id = a.id
            WHERE a.user_id = ?
            ORDER BY r.assessment_id, r.capability_id, r.lens_id
        ''', (session['user_id'],))
        responses = cursor.fetchall()
        conn.close()
        
        result = []
        for resp in responses:
            assessment_id, capability_id, lens_id, answer, score, improvement = resp
            
            # Get names for display
            capability_name = next((c['name'] for c in CAPABILITIES if c['id'] == capability_id), capability_id)
            lens_name = next((l['name'] for l in LENSES if l['id'] == lens_id), lens_id)
            
            result.append({
                'assessment_id': assessment_id,
                'capability_id': capability_id,
                'capability_name': capability_name,
                'lens_id': lens_id,
                'lens_name': lens_name,
                'answer_preview': answer[:100] + '...' if len(answer) > 100 else answer,
                'score': score,
                'improvement_preview': improvement[:100] + '...' if improvement and len(improvement) > 100 else improvement,
                'reprocess_url': f'/reprocess_response/{assessment_id}/{capability_id}/{lens_id}'
            })
        
        return jsonify({
            "status": "success",
            "responses": result
        })
        
    except Exception as e:
        print(f"My responses error: {e}")
        return jsonify({"status": "error", "message": "Failed to get responses"})

@app.route('/company_benchmarks')
def company_benchmarks():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Get user's company hash
    cursor.execute('SELECT company_hash FROM users WHERE id = ?', (session['user_id'],))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    company_hash = user_row[0]
    # For each domain, get the latest assessment for this company
    result = {'company': {}, 'industry': {}}
    for domain in DOMAINS:
        # Latest assessment for this company and domain
        cursor.execute('''
            SELECT a.overall_percentage, a.updated_at
            FROM assessments a
            JOIN users u ON a.user_id = u.id
            WHERE u.company_hash = ? AND a.domain = ? AND a.status = 'completed'
            ORDER BY a.updated_at DESC LIMIT 1
        ''', (company_hash, domain))
        row = cursor.fetchone()
        if row:
            result['company'][domain] = {'overall_percentage': row[0], 'updated_at': row[1]}
        else:
            result['company'][domain] = None
        # Industry average for this domain (excluding this company)
        cursor.execute('''
            SELECT a.overall_percentage
            FROM assessments a
            JOIN users u ON a.user_id = u.id
            WHERE u.company_hash != ? AND a.domain = ? AND a.status = 'completed'
        ''', (company_hash, domain))
        industry_scores = [r[0] for r in cursor.fetchall() if r[0] is not None]
        if industry_scores:
            avg = round(sum(industry_scores) / len(industry_scores), 1)
            result['industry'][domain] = {'average': avg, 'count': len(industry_scores)}
        else:
            result['industry'][domain] = None
    conn.close()
    return jsonify({'status': 'success', 'data': result})



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)

