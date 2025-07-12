#!/usr/bin/env python3
"""
Migration script to encrypt existing user data in the database.
This script should be run once to encrypt all existing user data.
"""

import sqlite3
import os
from cryptography.fernet import Fernet

# Database and encryption setup
DATABASE = 'finops_assessment.db'
ENCRYPTION_KEY_FILE = 'encryption.key'

def encrypt_data(data, cipher):
    """Encrypt sensitive data"""
    if data is None:
        return None
    return cipher.encrypt(data.encode()).decode()

def migrate_users():
    """Migrate existing user data to encrypted format"""
    
    # Check if encryption key exists
    if not os.path.exists(ENCRYPTION_KEY_FILE):
        print("❌ Encryption key not found. Please run the main application first to generate the key.")
        return False
    
    # Load encryption key
    with open(ENCRYPTION_KEY_FILE, 'rb') as f:
        encryption_key = f.read()
    
    cipher = Fernet(encryption_key)
    
    # Connect to database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Get all users
        cursor.execute('SELECT id, name, email, organization, role FROM users')
        users = cursor.fetchall()
        
        print(f"🔍 Found {len(users)} users to migrate...")
        
        migrated_count = 0
        
        for user in users:
            user_id, name, email, organization, role = user
            
            # Check if data is already encrypted (looks like base64)
            def is_encrypted(data):
                if not data:
                    return False
                try:
                    # Try to decode as base64 and decrypt
                    cipher.decrypt(data.encode())
                    return True
                except:
                    return False
            
            # Only encrypt if not already encrypted
            new_name = name if is_encrypted(name) else encrypt_data(name, cipher)
            new_email = email if is_encrypted(email) else encrypt_data(email, cipher)
            new_organization = organization if is_encrypted(organization) else encrypt_data(organization, cipher)
            new_role = role if is_encrypted(role) else encrypt_data(role, cipher)
            
            # Update user with encrypted data
            cursor.execute('''
                UPDATE users 
                SET name = ?, email = ?, organization = ?, role = ?
                WHERE id = ?
            ''', (new_name, new_email, new_organization, new_role, user_id))
            
            migrated_count += 1
            print(f"✅ Migrated user {user_id}")
        
        conn.commit()
        print(f"🎉 Successfully migrated {migrated_count} users!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("🔐 FinOps Assessment - Data Encryption Migration")
    print("=" * 50)
    
    if not os.path.exists(DATABASE):
        print("❌ Database not found. Please run the main application first.")
        exit(1)
    
    print("⚠️  This script will encrypt all existing user data.")
    print("⚠️  Make sure you have a backup of your database before proceeding.")
    
    response = input("Do you want to continue? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        exit(0)
    
    if migrate_users():
        print("\n✅ Migration completed successfully!")
        print("🔐 All user data is now encrypted.")
        print("🚀 You can now run the application with encryption enabled.")
    else:
        print("\n❌ Migration failed!")
        exit(1) 