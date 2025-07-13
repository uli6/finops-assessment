from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from models.database import get_db_connection
from config import DATABASE

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard/stats')
def dashboard_stats():
    """Get dashboard statistics"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user's assessments by domain
    cursor.execute('''
        SELECT domain, overall_percentage
        FROM assessments 
        WHERE user_id = ? AND status = 'completed'
        ORDER BY created_at DESC
    ''', (session['user_id'],))
    user_assessments = cursor.fetchall()
    
    # Get industry benchmarks by domain
    cursor.execute('''
        SELECT domain, AVG(overall_percentage) as avg_score, COUNT(*) as count
        FROM assessments 
        WHERE status = 'completed'
        GROUP BY domain
    ''')
    industry_benchmarks = cursor.fetchall()
    
    conn.close()
    
    # Process data for charts
    domains = ["Understand Usage & Cost", "Quantify Business Value", "Optimize Usage & Cost", "Manage the FinOps Practice"]
    
    user_scores = {}
    for domain, score in user_assessments:
        user_scores[domain] = score
    
    industry_scores = {}
    for domain, avg_score, count in industry_benchmarks:
        industry_scores[domain] = avg_score if avg_score else 0
    
    chart_data = {
        'labels': domains,
        'user_scores': [user_scores.get(domain, 0) for domain in domains],
        'industry_scores': [industry_scores.get(domain, 0) for domain in domains]
    }
    
    return jsonify(chart_data)

@admin_bp.route('/company_benchmarks')
def company_benchmarks():
    """Get company benchmarks data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user's company hash
    cursor.execute('SELECT company_hash FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    company_hash = user[0]
    
    # Get user's latest assessment per domain
    cursor.execute('''
        SELECT domain, overall_percentage
        FROM assessments 
        WHERE user_id = ? AND status = 'completed'
        AND (domain, created_at) IN (
            SELECT domain, MAX(created_at)
            FROM assessments 
            WHERE user_id = ? AND status = 'completed'
            GROUP BY domain
        )
    ''', (session['user_id'], session['user_id']))
    user_scores = dict(cursor.fetchall())
    
    # Get industry averages per domain
    cursor.execute('''
        SELECT domain, AVG(overall_percentage) as avg_score
        FROM assessments 
        WHERE status = 'completed'
        GROUP BY domain
    ''')
    industry_scores = dict(cursor.fetchall())
    
    conn.close()
    
    # Prepare data for all domains
    domains = ["Understand Usage & Cost", "Quantify Business Value", "Optimize Usage & Cost", "Manage the FinOps Practice"]
    
    chart_data = {
        'labels': domains,
        'user_scores': [user_scores.get(domain, 0) for domain in domains],
        'industry_scores': [industry_scores.get(domain, 0) for domain in domains]
    }
    
    return jsonify(chart_data) 