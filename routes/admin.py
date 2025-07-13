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
    """Get company benchmark data for charts (maturity as percentage 0-100)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    from data.capabilities import DOMAINS, CAPABILITIES

    # Helper: get capability ids for each domain
    domain_capabilities = {d: [c['id'] for c in CAPABILITIES if c['domain'] == d] for d in DOMAINS}
    domain_total_questions = {d: len(domain_capabilities[d]) * 5 for d in DOMAINS}  # 5 lenses per capability
    domain_total_points = {d: domain_total_questions[d] * 4 for d in DOMAINS}

    # Get user's company_hash
    cursor.execute('SELECT company_hash FROM users WHERE id = ?', (session['user_id'],))
    user_row = cursor.fetchone()
    user_company_hash = user_row[0] if user_row else None

    # Company maturity (%) per domain
    company_scores = []
    for domain in DOMAINS:
        # Find the most recent completed assessment (domain-specific or complete) for this company with responses for this domain
        cursor.execute('''
            SELECT a.id, a.domain, a.created_at
            FROM assessments a
            JOIN users u ON a.user_id = u.id
            WHERE u.company_hash = ? AND a.status = 'completed' AND (a.domain = ? OR a.domain = 'Complete Assessment')
            ORDER BY a.created_at DESC
            LIMIT 1
        ''', (user_company_hash, domain))
        row = cursor.fetchone()
        if row:
            assessment_id = row[0]
            # Get all responses for this assessment and domain
            cursor.execute('''
                SELECT r.score, r.capability_id
                FROM responses r
                WHERE r.assessment_id = ?
            ''', (assessment_id,))
            responses = cursor.fetchall()
            # Filter responses for this domain
            scores = [score for score, capability_id in responses if capability_id in domain_capabilities[domain]]
            total_points = domain_total_points[domain]
            maturity_pct = round((sum(scores) / total_points) * 100, 1) if scores and total_points > 0 else None
            company_scores.append(maturity_pct)
        else:
            company_scores.append(None)

    # Industry maturity (%) per domain (exclude user's company)
    industry_scores = []
    for domain in DOMAINS:
        # For each company, get the most recent completed assessment (domain-specific or complete) for this domain
        cursor.execute('''
            SELECT u.company_hash, MAX(a.created_at)
            FROM assessments a
            JOIN users u ON a.user_id = u.id
            WHERE (a.domain = ? OR a.domain = 'Complete Assessment') AND a.status = 'completed' AND u.company_hash != ?
            GROUP BY u.company_hash
        ''', (domain, user_company_hash))
        company_latest_dates = cursor.fetchall()
        domain_percentages = []
        for company_hash, latest_date in company_latest_dates:
            # Get the assessment id
            cursor.execute('''
                SELECT a.id FROM assessments a
                JOIN users u ON a.user_id = u.id
                WHERE u.company_hash = ? AND a.created_at = ? AND a.status = 'completed' AND (a.domain = ? OR a.domain = 'Complete Assessment')
                LIMIT 1
            ''', (company_hash, latest_date, domain))
            assessment_row = cursor.fetchone()
            if assessment_row:
                assessment_id = assessment_row[0]
                cursor.execute('''
                    SELECT r.score, r.capability_id
                    FROM responses r
                    WHERE r.assessment_id = ?
                ''', (assessment_id,))
                responses = cursor.fetchall()
                scores = [score for score, capability_id in responses if capability_id in domain_capabilities[domain]]
                total_points = domain_total_points[domain]
                maturity_pct = (sum(scores) / total_points) * 100 if scores and total_points > 0 else None
                if maturity_pct is not None:
                    domain_percentages.append(maturity_pct)
        avg_score = round(sum(domain_percentages) / len(domain_percentages), 1) if domain_percentages else None
        industry_scores.append(avg_score)

    conn.close()

    return jsonify({
        'domains': DOMAINS,
        'company_scores': company_scores,
        'industry_avgs': industry_scores
    }) 