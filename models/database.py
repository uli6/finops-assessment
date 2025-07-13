"""
Database Model for FinOps Assessment Platform
Handles database initialization, migrations, and connection management.
"""

import sqlite3
import os
from config import DATABASE


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


def get_db_connection():
    """Get a database connection"""
    return sqlite3.connect(DATABASE)


def close_db_connection(conn):
    """Close a database connection"""
    if conn:
        conn.close() 