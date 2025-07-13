#!/usr/bin/env python3
"""
Test script to verify modularization is working correctly
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported successfully"""
    try:
        # Test configuration
        from config import DATABASE, SECRET_KEY
        print("✅ Config imported successfully")
        
        # Test data
        from data.capabilities import CAPABILITIES, LENSES, SCOPES
        print("✅ Data modules imported successfully")
        
        # Test services
        from services.email_service import send_email, send_confirmation_email
        from services.encryption_service import encryption_service
        from services.ai_service import get_openai_client, evaluate_finops_maturity
        print("✅ Services imported successfully")
        
        # Test models
        from models.database import init_db, get_db_connection
        print("✅ Models imported successfully")
        
        print("\n🎉 All modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_data_structures():
    """Test that data structures are properly defined"""
    try:
        from data.capabilities import CAPABILITIES, LENSES, SCOPES, DOMAINS
        
        print(f"📊 Data structures:")
        print(f"   - Capabilities: {len(CAPABILITIES)}")
        print(f"   - Lenses: {len(LENSES)}")
        print(f"   - Scopes: {len(SCOPES)}")
        print(f"   - Domains: {len(DOMAINS)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data structure error: {e}")
        return False

def test_services():
    """Test that services can be instantiated"""
    try:
        from services.encryption_service import encryption_service
        
        # Test encryption service
        test_data = "test@example.com"
        encrypted = encryption_service.encrypt_data(test_data)
        decrypted = encryption_service.decrypt_data(encrypted)
        
        print(f"🔐 Encryption test: {test_data} -> {encrypted[:20]}... -> {decrypted}")
        
        # Test hashing
        hashed_email = encryption_service.hash_email(test_data)
        hashed_company = encryption_service.hash_company("example.com")
        
        print(f"🔒 Hashing test: {test_data} -> {hashed_email[:20]}...")
        print(f"🔒 Company hash: example.com -> {hashed_company[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Service test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing FinOps Assessment Platform Modularization")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Data Structures Test", test_data_structures),
        ("Services Test", test_services)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Modularization is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1) 