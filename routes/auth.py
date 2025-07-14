from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import secrets
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from models.database import get_db_connection
from services.email_service import send_confirmation_email, send_magic_link
from services.encryption_service import encryption_service
from config import DATABASE

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle user registration"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    company_role = data.get('company_role', '').strip()
    
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email is required'}), 400
    
    # Hash email for privacy
    email_hash = encryption_service.hash_email(email)
    company_hash = encryption_service.hash_company(email.split('@')[1])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute('SELECT id FROM users WHERE email_hash = ?', (email_hash,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        conn.close()
        return jsonify({'error': 'Email already registered'}), 400
    
    # Generate confirmation token
    token = secrets.token_urlsafe(32)
    
    # Create user (unconfirmed)
    cursor.execute('''
        INSERT INTO users (email_hash, company_hash, confirmation_token, is_confirmed, created_at, company_role)
        VALUES (?, ?, ?, 0, ?, ?)
    ''', (email_hash, company_hash, token, datetime.now(), company_role))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Send confirmation email
    try:
        send_confirmation_email(email, token)
        return jsonify({'message': 'Registration successful! Please check your email to confirm your account.'}), 200
    except Exception as e:
        # If email fails, delete the user
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'error': 'Failed to send confirmation email. Please try again.'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login with magic link"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email is required'}), 400
    
    email_hash = encryption_service.hash_email(email)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists and is confirmed
    cursor.execute('SELECT id, is_confirmed FROM users WHERE email_hash = ?', (email_hash,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Email not registered. Please register first.'}), 400
    
    if not user[1]:  # is_confirmed
        conn.close()
        return jsonify({'error': 'Please confirm your email before logging in.'}), 400
    
    # Generate magic link token
    token = secrets.token_urlsafe(32)
    
    # Update user with new token
    cursor.execute('UPDATE users SET confirmation_token = ? WHERE id = ?', (token, user[0]))
    conn.commit()
    conn.close()
    
    # Send magic link
    try:
        send_magic_link(email, token)
        return jsonify({'message': 'Magic link sent! Please check your email.'}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to send magic link. Please try again.'}), 500

@auth_bp.route('/magic_login/<token>')
def magic_login(token):
    """Handle magic link login"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find user by token
    cursor.execute('SELECT id FROM users WHERE confirmation_token = ? AND is_confirmed = 1', (token,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return render_template('login.html', error='Invalid or expired magic link')
    
    # Clear token and set session
    cursor.execute('UPDATE users SET confirmation_token = NULL WHERE id = ?', (user[0],))
    conn.commit()
    conn.close()
    
    session['user_id'] = user[0]
    return redirect(url_for('assessment.dashboard'))

@auth_bp.route('/confirm_email/<token>')
def confirm_email(token):
    """Confirm user email"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find user by token
    cursor.execute('SELECT id FROM users WHERE confirmation_token = ?', (token,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return render_template('login.html', error='Invalid or expired confirmation link')
    
    # Confirm user
    cursor.execute('UPDATE users SET is_confirmed = 1, confirmation_token = NULL WHERE id = ?', (user[0],))
    conn.commit()
    conn.close()
    
    return render_template('email_confirmed.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('auth.index')) 