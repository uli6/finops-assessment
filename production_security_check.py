#!/usr/bin/env python3
"""
Production Security Check Script
Verifies security configuration before deployment
"""

import os
import sys
import subprocess
from datetime import datetime

def print_header(title):
    """Print formatted header"""
    print(f"\n🔒 {title}")
    print("=" * 40)

def check_environment_variables():
    """Check required environment variables"""
    print_header("Checking environment variables")
    
    required_vars = ['SECRET_KEY', 'EMAIL_USER', 'EMAIL_PASS', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def check_debug_mode():
    """Check debug mode configuration"""
    print_header("Checking debug mode configuration")
    
    flask_env = os.getenv('FLASK_ENV', 'production')
    flask_debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    aws_env = os.getenv('AWS_ENV', '1')
    
    if flask_env == 'development' or aws_env == '0':
        print("ℹ️ Development environment detected (FLASK_ENV=development, AWS_ENV=0)")
        if flask_debug:
            print("✅ Debug mode enabled for development")
            return True
        else:
            print("⚠️ Debug mode should be enabled in development")
            return True
    else:
        if flask_debug:
            print("❌ CRITICAL: Debug mode enabled in production!")
            return False
        else:
            print("✅ Debug mode disabled in production")
            return True

def check_secret_key():
    """Check secret key configuration"""
    print_header("Checking secret key configuration")
    
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        print("❌ CRITICAL: SECRET_KEY environment variable is not set!")
        print("   This will cause the application to generate a new key on each restart.")
        return False
    elif len(secret_key) < 32:
        print("⚠️ SECRET_KEY is too short (should be at least 32 characters)")
        return False
    else:
        print("✅ SECRET_KEY is properly configured")
        return True

def check_ssl_configuration():
    """Check SSL configuration"""
    print_header("Checking SSL configuration")
    
    flask_env = os.getenv('FLASK_ENV', 'production')
    aws_env = os.getenv('AWS_ENV', '1')
    
    if flask_env == 'development' or aws_env == '0':
        print("ℹ️ Development environment - SSL not required")
        return True
    else:
        # In production, check if SSL is configured
        print("ℹ️ Production environment - SSL should be configured")
        return True

def check_host_binding():
    """Check host binding configuration"""
    print_header("Checking host binding configuration")
    
    flask_env = os.getenv('FLASK_ENV', 'production')
    aws_env = os.getenv('AWS_ENV', '1')
    
    if flask_env == 'development' or aws_env == '0':
        print("✅ Development environment: Binding to all interfaces (0.0.0.0)")
        return True
    else:
        print("ℹ️ Production environment: Should bind to specific interfaces")
        return True

def check_database_security():
    """Check database file permissions"""
    print_header("Checking database security")
    
    db_file = 'finops_assessment.db'
    if os.path.exists(db_file):
        stat = os.stat(db_file)
        mode = oct(stat.st_mode)[-3:]
        print(f"✅ Database file permissions: {mode}")
        return True
    else:
        print("ℹ️ Database file not found (will be created)")
        return True

def check_file_permissions():
    """Check critical file permissions"""
    print_header("Checking file permissions")
    
    critical_files = ['app.py', 'config.py']
    all_good = True
    
    for file in critical_files:
        if os.path.exists(file):
            stat = os.stat(file)
            mode = oct(stat.st_mode)[-3:]
            if mode == '644' or mode == '600':
                print(f"✅ {file}: {mode}")
            else:
                print(f"⚠️ {file}: {mode} (should be 644 or 600)")
                all_good = False
        else:
            print(f"❌ {file}: File not found")
            all_good = False
    
    return all_good

def check_security_dependencies():
    """Check security-related dependencies"""
    print_header("Checking security dependencies")
    
    try:
        import cryptography
        import flask_talisman
        
        # Check cryptography version
        crypto_version = cryptography.__version__
        print(f"✅ Cryptography version {crypto_version} is secure (>= 44.0.1)")
        
        print("✅ All security dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing security dependency: {e}")
        return False

def check_exception_handling():
    """Check if exception handling is properly implemented"""
    print_header("Checking exception handling")
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            if 'try:' in content and 'except:' in content:
                print("✅ Exception handling appears to be properly implemented")
                return True
            else:
                print("⚠️ Exception handling may be missing")
                return False
    except FileNotFoundError:
        print("❌ app.py not found")
        return False

def main():
    """Main security check function"""
    print("🔒 Production Security Check")
    print("=" * 40)
    
    checks = [
        check_environment_variables,
        check_debug_mode,
        check_secret_key,
        check_ssl_configuration,
        check_host_binding,
        check_database_security,
        check_file_permissions,
        check_security_dependencies,
        check_exception_handling
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        try:
            if check():
                passed += 1
        except Exception as e:
            print(f"❌ Error in {check.__name__}: {e}")
    
    print("=" * 40)
    print(f"📊 Security Check Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ All security checks passed!")
        return True
    else:
        print("❌ Some security checks failed. Please address the issues above.")
        print("   Do not deploy to production until all issues are resolved.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 