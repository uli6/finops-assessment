# 🚀 FinOps Maturity Assessment Platform

A comprehensive, enterprise-grade platform for conducting FinOps maturity assessments with advanced security, user management, and detailed analytics.

![FinOps Assessment](https://img.shields.io/badge/FinOps-Maturity%20Assessment-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Flask](https://img.shields.io/badge/Flask-2.0+-lightgrey)
![Security](https://img.shields.io/badge/Security-Encrypted%20Data-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Table of Contents

- [Overview](#-overview)
- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [🔧 Configuration](#-configuration)
- [🔐 Security](#-security)
- [👥 User Management](#-user-management)
- [📊 Assessment Framework](#-assessment-framework)
- [🔍 API Reference](#-api-reference)
- [🧪 Testing](#-testing)
- [📈 Deployment](#-deployment)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## 🎯 Overview

The FinOps Maturity Assessment Platform is a sophisticated web application designed to evaluate and track FinOps maturity across organizations. Built with Flask and featuring enterprise-grade security, it provides comprehensive assessments across multiple domains and lenses of the FinOps Framework.

### Key Capabilities

- **🔐 End-to-End Encryption**: All sensitive user data is encrypted at rest
- **👥 Advanced User Management**: Admin controls with user removal capabilities
- **📊 Comprehensive Assessments**: 110+ questions across 5 FinOps lenses
- **🎯 Multi-Scope Support**: Public Cloud, SaaS, Data Center, Licensing, AI/ML
- **📈 Detailed Analytics**: Maturity scoring with benchmark comparisons
- **🔗 Magic Link Authentication**: Passwordless, secure login system

## ✨ Features

### 🔐 Security & Privacy
- **AES-256 Encryption**: All user data encrypted at rest
- **Automatic Key Management**: Secure encryption key generation and storage
- **Magic Link Authentication**: No passwords, secure email-based login
- **Admin Access Control**: Role-based permissions with domain restrictions

### 👥 User Management
- **Organization Inference**: Automatically extracted from email domains
- **Admin Dashboard**: Complete user management interface
- **User Removal**: Safe deletion with cascade protection
- **Status Tracking**: Confirmed, pending, and admin user states

### 📊 Assessment Framework
- **5 FinOps Lenses**: Knowledge, Process, Metrics, Adoption, Automation
- **4 Assessment Domains**: Understanding Usage & Cost, Quantify Business Value, Optimize Usage & Cost, Manage the FinOps Practice
- **Multiple Scopes**: Public Cloud, SaaS, Data Center, Licensing, AI/ML
- **Detailed Scoring**: Weighted scoring with improvement suggestions

### 📈 Analytics & Reporting
- **Maturity Scoring**: Comprehensive evaluation across all capabilities
- **Benchmark Comparisons**: Anonymous peer organization comparisons
- **Progress Tracking**: Real-time assessment completion status
- **Detailed Reports**: PDF generation with actionable insights

## 🏗️ Architecture

```
finops-assessment/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── finops_assessment.db  # SQLite database (encrypted)
├── encryption.key        # AES-256 encryption key
├── templates/            # HTML templates
│   ├── index.html       # Landing page
│   ├── login.html       # Authentication
│   ├── dashboard.html   # User dashboard
│   ├── assessment.html  # Assessment interface
│   ├── results.html     # Results display
│   └── debug_users.html # Admin user management
├── uploads/             # File uploads
└── migrate_encryption.py # Data migration script
```

### Technology Stack

- **Backend**: Flask (Python 3.8+)
- **Database**: SQLite with encryption
- **Security**: Cryptography (Fernet/AES-256)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Email**: SMTP with HTML templates
- **File Processing**: PyPDF2, Pytesseract, Pillow

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- SMTP server access (for email functionality)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd finops-assessment
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file (optional):

```env
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### 5. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5002`

## 📦 Installation

### Detailed Setup Instructions

1. **System Requirements**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3 python3-pip python3-venv
   
   # macOS
   brew install python3
   
   # Windows
   # Download Python from python.org
   ```

2. **Database Initialization**
   ```bash
   # The database is automatically created on first run
   python app.py
   ```

3. **Encryption Setup**
   ```bash
   # Encryption key is automatically generated
   # No manual setup required
   ```

4. **Email Configuration** (Optional)
   ```bash
   # For Gmail, enable 2FA and generate app password
   # Add credentials to .env file
   ```

### Migration from Previous Versions

If you have existing data, run the migration script:

```bash
python migrate_encryption.py
```

This will encrypt all existing user data while preserving functionality.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EMAIL_USER` | SMTP username | None |
| `EMAIL_PASS` | SMTP password | None |
| `SMTP_SERVER` | SMTP server | smtp.gmail.com |
| `SMTP_PORT` | SMTP port | 587 |

### Database Configuration

The application uses SQLite with automatic encryption:

- **Database File**: `finops_assessment.db`
- **Encryption**: AES-256 (Fernet)
- **Key Storage**: `encryption.key`

### Admin Configuration

Admin users are automatically assigned based on email domain:

- **Admin Domain**: `@ulisses.xyz`
- **Permissions**: User management, system access
- **Security**: Cannot be removed by other admins

## 🔐 Security

### Data Encryption

All sensitive user data is encrypted using AES-256:

```python
# Automatic encryption of user data
encrypted_name = cipher.encrypt(name.encode()).decode()
encrypted_email = cipher.encrypt(email.encode()).decode()
```

### Authentication

- **Magic Link System**: No passwords stored
- **Token Expiration**: 15-minute validity
- **Session Management**: Secure Flask sessions
- **CSRF Protection**: Built-in Flask security

### Access Control

- **Admin Verification**: Domain-based admin assignment
- **Route Protection**: Admin-only endpoints
- **User Removal**: Safe deletion with confirmation

## 👥 User Management

### User Registration

1. **Automatic Organization Detection**
   ```python
   # Organization extracted from email domain
   organization = email.split('@')[1]  # user@company.com → company.com
   ```

2. **Email Confirmation**
   - Confirmation link sent via email
   - 24-hour validity period
   - Automatic account activation

### Admin Features

Access the admin panel at `/debug/users`:

- **User Statistics**: Total users, confirmed users, assessments
- **User Management**: View all users with decrypted data
- **User Removal**: Delete non-admin users
- **Status Monitoring**: Confirmed, pending, admin status

### User Roles

| Role | Permissions | Access |
|------|-------------|--------|
| **Regular User** | Create assessments, view results | Dashboard, assessments |
| **Admin** | User management, system access | All features + admin panel |

## 📊 Assessment Framework

### FinOps Lenses

The assessment evaluates across 5 key lenses:

| Lens | Weight | Description |
|------|--------|-------------|
| **Knowledge** | 30% | Understanding and awareness |
| **Process** | 25% | Operational procedures |
| **Metrics** | 20% | Measurement and reporting |
| **Adoption** | 20% | Implementation and usage |
| **Automation** | 5% | Automated processes |

### Assessment Scopes

| Scope | Description | Use Case |
|-------|-------------|----------|
| **Public Cloud** | AWS, Azure, GCP workloads | Cloud-native organizations |
| **SaaS** | Software subscriptions | SaaS-heavy environments |
| **Data Center** | On-premises infrastructure | Hybrid environments |
| **Licensing** | Software licensing | Enterprise software |
| **AI/ML** | AI/ML workloads | Data science teams |

### Assessment Domains

1. **Understanding Usage & Cost**
   - Cost Allocation
   - Data Analysis and Showback
   - Managing Anomalies
   - Managing Shared Cost

2. **Quantify Business Value**
   - Forecasting
   - Budget Management
   - Unit Economics
   - Measuring Unit Costs
   - Chargeback & Finance Integration

3. **Optimize Usage & Cost**
   - Rightsizing
   - Workload Management & Automation
   - Rate Optimization
   - Cloud Sustainability
   - Onboarding Workloads
   - Resource Lifecycle Management
   - Cloud Policy & Governance

4. **Manage the FinOps Practice**
   - FinOps Education & Enablement
   - Cloud Provider Data Ingestion
   - Data Normalization
   - Managing Commitment Based Discounts
   - Establishing FinOps Culture
   - Intersecting Frameworks

## 🔍 API Reference

### Authentication Endpoints

```http
POST /register
Content-Type: application/x-www-form-urlencoded

name=John%20Doe&email=john@company.com&role=FinOps%20Practitioner
```

```http
POST /login
Content-Type: application/x-www-form-urlencoded

email=john@company.com
```

```http
GET /magic_login/{token}
```

### Assessment Endpoints

```http
POST /start_assessment
Content-Type: application/x-www-form-urlencoded

scope_id=public_cloud&domain=Understanding%20Usage%20%26%20Cost
```

```http
POST /submit_assessment
Content-Type: application/x-www-form-urlencoded

capability_id=cost_allocation&lens_id=knowledge&answer=Detailed%20response...
```

### Admin Endpoints

```http
GET /debug/users
Authorization: Admin required
```

```http
GET /debug/users/api
Authorization: Admin required
```

```http
DELETE /remove_user/{user_id}
Authorization: Admin required
```

### Response Formats

**Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {...}
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Error description"
}
```

## 🧪 Testing

### Manual Testing

1. **User Registration**
   ```bash
   # Test registration with different email domains
   curl -X POST http://localhost:5002/register \
     -d "name=Test User&email=test@company.com&role=FinOps Practitioner"
   ```

2. **Admin Access**
   ```bash
   # Register with admin domain
   curl -X POST http://localhost:5002/register \
     -d "name=Admin User&email=admin@ulisses.xyz&role=Admin"
   ```

3. **User Removal**
   ```bash
   # Remove user (admin only)
   curl -X DELETE http://localhost:5002/remove_user/1
   ```

### Automated Testing

```bash
# Run tests (if test suite is implemented)
python -m pytest tests/

# Run with coverage
python -m pytest --cov=app tests/
```

## 📈 Deployment

### Production Deployment

1. **WSGI Server Setup**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5002 app:app
   ```

2. **Reverse Proxy (Nginx)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5002;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **SSL Certificate**
   ```bash
   # Using Let's Encrypt
   sudo certbot --nginx -d your-domain.com
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5002

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5002", "app:app"]
```

### Environment Variables

```bash
# Production environment
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
export DATABASE_URL=sqlite:///finops_assessment.db
```

## 🤝 Contributing

### Development Setup

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/finops-assessment.git
   cd finops-assessment
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make Changes**
   - Follow PEP 8 style guidelines
   - Add tests for new features
   - Update documentation

4. **Submit Pull Request**
   ```bash
   git commit -m "Add amazing feature"
   git push origin feature/amazing-feature
   ```

### Code Style

- **Python**: PEP 8 compliant
- **JavaScript**: ES6+ with consistent formatting
- **HTML/CSS**: Semantic markup with responsive design
- **Documentation**: Comprehensive docstrings and comments

### Testing Guidelines

- Unit tests for all new functions
- Integration tests for API endpoints
- Security tests for authentication flows
- Performance tests for database operations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### License Summary

- ✅ **Commercial Use**: Allowed
- ✅ **Modification**: Allowed  
- ✅ **Distribution**: Allowed
- ✅ **Private Use**: Allowed
- ❌ **Liability**: Limited
- ❌ **Warranty**: None

## 🙏 Acknowledgments

- **FinOps Foundation**: For the comprehensive FinOps Framework
- **Flask Community**: For the excellent web framework
- **Cryptography Team**: For the robust encryption library
- **Open Source Contributors**: For the supporting libraries

## 📞 Support

### Getting Help

- **Documentation**: This README and inline code comments
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas

### Contact Information

- **Maintainer**: [Your Name](mailto:contact@ulisses.xyz)
- **Project URL**: [https://github.com/your-username/finops-assessment](https://github.com/your-username/finops-assessment)

---

<div align="center">

**Made with ❤️ for the FinOps community**

[![FinOps Foundation](https://img.shields.io/badge/FinOps-Foundation-blue)](https://www.finops.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-lightgrey)](https://flask.palletsprojects.com/)

</div> 