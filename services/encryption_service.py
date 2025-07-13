"""
Encryption Service for FinOps Assessment Platform
Handles data encryption and hashing for privacy protection.
"""

import os
import hashlib
from cryptography.fernet import Fernet


class EncryptionService:
    """Service for handling data encryption and hashing"""
    
    def __init__(self):
        self.encryption_key_file = 'encryption.key'
        self.cipher = self._initialize_cipher()
    
    def _initialize_cipher(self):
        """Initialize the encryption cipher"""
        if os.path.exists(self.encryption_key_file):
            with open(self.encryption_key_file, 'rb') as f:
                encryption_key = f.read()
        else:
            encryption_key = Fernet.generate_key()
            with open(self.encryption_key_file, 'wb') as f:
                f.write(encryption_key)
        
        return Fernet(encryption_key)
    
    def encrypt_data(self, data):
        """Encrypt sensitive data before storing in database"""
        if data is None:
            return None
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data from database"""
        if encrypted_data is None:
            return None
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except:
            return encrypted_data  # Return as-is if decryption fails (for legacy data)
    
    def hash_company(self, domain):
        """Hash company domain for privacy"""
        return hashlib.sha256(domain.strip().lower().encode()).hexdigest()
    
    def hash_email(self, email):
        """Hash email address for privacy"""
        return hashlib.sha256(email.strip().lower().encode()).hexdigest()


# Global instance
encryption_service = EncryptionService() 