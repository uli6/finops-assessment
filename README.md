
# FinOps Assessment Platform

A privacy-focused FinOps Maturity Assessment platform that helps organizations evaluate their FinOps practices across different domains and capabilities.

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/uli6)

## 🌟 Features

### Privacy-First Design
- **No personal data storage** - Only email hashes are stored, no plaintext emails or names
- **Anonymous assessments** - Company names are anonymized and encrypted
- **Domain-based company counting** - Users with same email domain count as single company
- **Secure magic link authentication** - No passwords, only secure email-based login

### Assessment Framework
- **Multi-domain assessments**: Understanding Usage & Cost, Quantify Business Value, Optimize Usage & Cost, Manage the FinOps Practice
- **Comprehensive capabilities**: 20+ FinOps capabilities across 4 domains
- **Multi-lens evaluation**: Knowledge, Process, Metrics, Adoption, Automation
- **AI-powered analysis**: ChatGPT analyzes text responses for maturity evaluation
- **Evidence-based scoring**: AI considers detailed responses for accurate assessments
- **Professional PDF export**: Comprehensive assessment reports with anonymized data
- **Excel XLSX export**: Results matrix in spreadsheet format for data analysis

### User Experience
- **Email confirmation required** - Users only saved after confirming email
- **Confirmation landing page** - After confirming your email, you are greeted with a dedicated page announcing successful confirmation, login instructions, and a button to access the login page
- **Magic link authentication** - Secure, passwordless login
- **Real-time progress tracking** - Save and resume assessments
- **AI-powered recommendations** - Personalized improvement suggestions
- **Dashboard analytics** - Company benchmarks and progress tracking
- **Responsive design** - Works on desktop and mobile
- **Interactive results matrix** - Click scores for detailed responses and suggestions

### Export & Reporting
- **PDF Reports**: Professional, comprehensive reports with all assessment data
- **Excel Export**: Results matrix in XLSX format with color-coded scores
- **Print-friendly**: Browser print functionality for quick sharing
- **Multi-format support**: PDF, Excel, and print options

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Email configuration (Gmail recommended)
- OpenAI API key (for AI recommendations)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd finops-assessment
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up email configuration**
   ```bash
   export EMAIL_USER="your-email@gmail.com"
   export EMAIL_PASS="your-app-password"
   export SMTP_SERVER="smtp.gmail.com"
   export SMTP_PORT="587"
   ```

   For Gmail setup:
   - Enable 2-Factor Authentication
   - Generate App Password
   - Use the 16-character app password as EMAIL_PASS

5. **Set up OpenAI API key**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   - Open http://localhost:5002
   - Register with your corporate email
   - Confirm your email address
   - Start your FinOps assessment

## 📧 Email Configuration

The platform requires email configuration for user registration and login. For Gmail setup:
1. Enable 2-Factor Authentication
2. Generate App Password
3. Use the 16-character app password as EMAIL_PASS

### Supported Email Providers
- **Gmail** (recommended)
- **Outlook/Hotmail**
- **Yahoo**
- **Corporate email domains**

## 🔒 Security Features

### Privacy Protection
- **Email hashing**: Only SHA-256 hashes of emails are stored
- **Company anonymization**: Organization names are encrypted and anonymized
- **No personal data**: No names, plaintext emails, or personal information stored
- **Domain-based privacy**: Users from same domain counted as single company

### Authentication
- **Magic link login**: Secure, time-limited login links
- **Email confirmation**: Required before account activation
- **Session security**: Secure session management
- **CSRF protection**: Built-in CSRF protection

### Data Protection
- **XSS protection**: Input sanitization and output encoding
- **SQL injection protection**: Parameterized queries
- **Encryption**: Sensitive data encrypted at rest

## 📊 Assessment Framework

### Domains
- **Understanding Usage & Cost**: Visibility and cost allocation
- **Quantify Business Value**: Business value measurement and optimization
- **Optimize Usage & Cost**: Resource optimization and cost management
- **Manage the FinOps Practice**: Governance and organizational practices

### Capabilities
Each domain contains multiple FinOps capabilities:
- **Forecasting**: Cost and usage prediction
- **Budgeting**: Financial planning and budget management
- **Benchmark**: Performance comparison and analysis
- **Unit Economics**: Cost per unit analysis
- **And more**: 20+ capabilities across all domains

### Lenses
- **Knowledge** (30% weight): Understanding and awareness
- **Process** (25% weight): Established procedures
- **Metrics** (20% weight): Measurement and tracking
- **Adoption** (20% weight): Organizational adoption
- **Automation** (5% weight): Automated processes

## 🛠️ Technical Stack

### Backend
- **Flask**: Web framework with modular architecture
- **SQLite**: Database with automatic migrations
- **Cryptography**: Data encryption and security
- **WeasyPrint**: Professional PDF generation
- **OpenPyXL**: Excel XLSX file generation
- **OpenAI**: AI-powered analysis and recommendations

### Frontend
- **HTML/CSS/JavaScript**: Responsive design
- **Chart.js**: Interactive dashboard charts
- **Markdown**: Rich text formatting
- **Modern UI**: Clean, professional interface

### Security
- **Flask-WTF**: CSRF protection
- **Bleach**: HTML sanitization
- **Secure headers**: Security hardening

## 📁 Project Structure

```
finops-assessment/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── privacy_notice.md     # Privacy policy
├── finops_assessment.db  # SQLite database

├── routes/               # Modular route handlers
│   ├── auth.py          # Authentication routes
│   ├── assessment.py    # Assessment routes
│   ├── dashboard.py     # Dashboard routes
│   └── utils.py         # Utility routes (PDF/XLSX export)

├── services/            # Business logic
│   ├── assessment.py    # Assessment processing
│   ├── auth.py          # Authentication services
│   └── email.py         # Email services

├── models/              # Data models
│   ├── user.py          # User model
│   ├── assessment.py    # Assessment model
│   └── response.py      # Response model

├── data/                # Static data
│   ├── capabilities.py  # FinOps capabilities
│   └── questions.py     # Assessment questions

├── templates/           # HTML templates
│   ├── login.html       # Login/registration page
│   ├── dashboard.html   # User dashboard
│   ├── assessment.html  # Assessment interface
│   ├── results.html     # Assessment results
│   ├── pdf_report.html  # PDF export template
│   └── settings.html    # Account settings

└── uploads/            # File uploads
    └── *.pdf          # Uploaded documents
```

## 🔧 Configuration

### Environment Variables
- `EMAIL_USER`: Email address for sending
- `EMAIL_PASS`: Email password/app password
- `SMTP_SERVER`: SMTP server (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP port (default: 587)
- `OPENAI_API_KEY`: OpenAI API key for AI recommendations

### Database
The application automatically creates and migrates the SQLite database on startup. No manual database setup required.

## 📈 Usage

### Registration Flow
1. **Register** with corporate email address
2. **Confirm email** via confirmation link
3. **After confirmation, you are taken to a landing page announcing your email is confirmed, with clear instructions and a button to access the login page.**
4. **Login** with magic link
5. **Start assessment** for your chosen domain

### Assessment Process
1. **Select domain** (Understanding Usage & Cost, Quantify Business Value, etc.)
2. **Answer questions** for each capability and lens
3. **Get AI-powered insights** based on your responses
4. **View recommendations** for improvement
5. **Export results** in PDF or Excel format

### Dashboard Features
- **Company benchmarks**: Compare your scores to industry averages
- **Domain-specific charts**: Visual progress tracking per domain
- **Assessment history**: Track all completed assessments
- **Privacy-focused analytics**: Anonymous benchmarking
- **Statistics overview**: User and assessment counts

### Results & Export Features
- **Interactive matrix**: Click scores for detailed responses
- **PDF reports**: Professional, comprehensive assessment reports
- **Excel export**: Results matrix in XLSX format with color coding
- **Print functionality**: Browser-based printing
- **Benchmark comparisons**: Industry average comparisons
- **AI recommendations**: Personalized improvement suggestions

### Privacy Features
- **Anonymous company names**: Company A, Company B, etc.
- **Encrypted organization data**: All sensitive data encrypted
- **No personal tracking**: No names or personal info stored
- **Domain-based analytics**: Company counting by email domain
- **AI-powered insights**: Personalized recommendations without data retention

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
1. Set up proper email configuration
2. Configure production database (PostgreSQL recommended)
3. Set up reverse proxy (nginx)
4. Use WSGI server (gunicorn)
5. Configure SSL/TLS certificates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 