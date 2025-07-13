from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file
import sqlite3
import json
import random
from datetime import datetime
from models.database import get_db_connection
from services.ai_service import evaluate_finops_maturity, generate_recommendations
from data.capabilities import CAPABILITIES, SCOPES, DOMAINS, QUESTIONS, LENSES
from config import DATABASE

assessment_bp = Blueprint('assessment', __name__)

@assessment_bp.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('auth.index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user's assessments
    cursor.execute('''
        SELECT id, scope_id, domain, status, overall_percentage, created_at, updated_at
        FROM assessments 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],))
    assessments = cursor.fetchall()
    
    # Get company benchmarks
    cursor.execute('''
        SELECT domain, AVG(overall_percentage) as avg_score, COUNT(*) as count
        FROM assessments 
        WHERE status = 'completed' 
        GROUP BY domain
    ''')
    benchmarks = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', assessments=assessments, benchmarks=benchmarks)

@assessment_bp.route('/start_assessment', methods=['POST'])
def start_assessment():
    """Start a new assessment"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    domain = data.get('domain')
    
    if not domain:
        return jsonify({'error': 'Domain is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create new assessment
    cursor.execute('''
        INSERT INTO assessments (user_id, scope_id, domain, status, created_at, updated_at)
        VALUES (?, ?, ?, 'in_progress', ?, ?)
    ''', (session['user_id'], 'complete', domain, datetime.now(), datetime.now()))
    
    assessment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'assessment_id': assessment_id, 'redirect': url_for('assessment.assessment')})

@assessment_bp.route('/assessment')
def assessment():
    """Assessment page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.index'))
    
    return render_template('assessment.html')

@assessment_bp.route('/get_assessment_progress')
def get_assessment_progress():
    """Get current assessment progress"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current assessment
    cursor.execute('''
        SELECT id, scope_id, domain, status 
        FROM assessments 
        WHERE user_id = ? AND status = 'in_progress'
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (session['user_id'],))
    assessment = cursor.fetchone()
    
    if not assessment:
        conn.close()
        return jsonify({'error': 'No active assessment found'}), 404
    
    assessment_id, scope_id, domain, status = assessment
    
    # Get existing responses
    cursor.execute('''
        SELECT capability_id, lens_id, answer, score
        FROM responses 
        WHERE assessment_id = ?
    ''', (assessment_id,))
    responses = {f"{row[0]}_{row[1]}": {'answer': row[2], 'score': row[3]} for row in cursor.fetchall()}
    
    conn.close()
    
    # Generate questions for the domain
    questions = []
    total_questions = 0
    
    for capability in CAPABILITIES:
        if domain == 'Complete Assessment' or domain == capability['domain']:
            capability_questions = QUESTIONS.get(capability['id'], {})
            for lens in LENSES:
                lens_questions = capability_questions.get(lens['id'], [])
                if lens_questions:
                    total_questions += 1
                    question_key = f"{capability['id']}_{lens['id']}"
                    
                    if question_key in responses:
                        # Question already answered
                        questions.append({
                            'capability_id': capability['id'],
                            'lens_id': lens['id'],
                            'capability_name': capability['name'],
                            'lens_name': lens['name'],
                            'question': lens_questions[0],  # Use first question for now
                            'answer': responses[question_key]['answer'],
                            'score': responses[question_key]['score'],
                            'answered': True
                        })
                    else:
                        # Question not answered yet
                        questions.append({
                            'capability_id': capability['id'],
                            'lens_id': lens['id'],
                            'capability_name': capability['name'],
                            'lens_name': lens['name'],
                            'question': lens_questions[0],  # Use first question for now
                            'answered': False
                        })
    
    return jsonify({
        'assessment_id': assessment_id,
        'domain': domain,
        'status': status,
        'questions': questions,
        'total_questions': total_questions,
        'answered_questions': len([q for q in questions if q['answered']])
    })

@assessment_bp.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    """Submit assessment response"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    assessment_id = data.get('assessment_id')
    capability_id = data.get('capability_id')
    lens_id = data.get('lens_id')
    answer = data.get('answer')
    
    if not all([assessment_id, capability_id, lens_id, answer]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify assessment belongs to user
    cursor.execute('SELECT domain FROM assessments WHERE id = ? AND user_id = ?', (assessment_id, session['user_id']))
    assessment = cursor.fetchone()
    
    if not assessment:
        conn.close()
        return jsonify({'error': 'Assessment not found'}), 404
    
    domain = assessment[0]
    
    # Get capability and lens info
    capability = next((c for c in CAPABILITIES if c['id'] == capability_id), None)
    lens = next((l for l in LENSES if l['id'] == lens_id), None)
    
    if not capability or not lens:
        conn.close()
        return jsonify({'error': 'Invalid capability or lens'}), 400
    
    # Evaluate maturity
    try:
        evaluation = evaluate_finops_maturity(capability['name'], lens['name'], answer, '', 'complete')
        score = evaluation['score']
        improvement_suggestions = evaluation['improvement_suggestions']
    except Exception as e:
        score = 0
        improvement_suggestions = "Unable to evaluate at this time."
    
    # Save response
    cursor.execute('''
        INSERT OR REPLACE INTO responses 
        (assessment_id, capability_id, lens_id, answer, score, improvement_suggestions, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (assessment_id, capability_id, lens_id, answer, score, improvement_suggestions, datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'score': score})

@assessment_bp.route('/complete_assessment', methods=['POST'])
def complete_assessment():
    """Complete assessment and generate recommendations"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    assessment_id = data.get('assessment_id')
    
    if not assessment_id:
        return jsonify({'error': 'Assessment ID required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify assessment belongs to user
    cursor.execute('SELECT domain FROM assessments WHERE id = ? AND user_id = ?', (assessment_id, session['user_id']))
    assessment = cursor.fetchone()
    
    if not assessment:
        conn.close()
        return jsonify({'error': 'Assessment not found'}), 404
    
    domain = assessment[0]
    
    # Get all responses for this assessment
    cursor.execute('''
        SELECT capability_id, lens_id, score
        FROM responses 
        WHERE assessment_id = ?
    ''', (assessment_id,))
    responses = cursor.fetchall()
    
    if not responses:
        conn.close()
        return jsonify({'error': 'No responses found for assessment'}), 400
    
    # Calculate overall percentage
    total_score = sum(response[2] for response in responses)
    overall_percentage = (total_score / len(responses)) if responses else 0
    
    # Generate recommendations
    try:
        lens_scores = {f"{r[0]}_{r[1]}": r[2] for r in responses}
        recommendations = generate_recommendations(assessment_id, 'complete', domain, overall_percentage, lens_scores)
    except Exception as e:
        recommendations = "Unable to generate recommendations at this time."
    
    # Update assessment
    cursor.execute('''
        UPDATE assessments 
        SET status = 'completed', overall_percentage = ?, recommendations = ?, updated_at = ?
        WHERE id = ?
    ''', (overall_percentage, recommendations, datetime.now(), assessment_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'overall_percentage': overall_percentage,
        'redirect': url_for('assessment.get_assessment_results', assessment_id=assessment_id)
    })

@assessment_bp.route('/get_assessment_results/<int:assessment_id>')
def get_assessment_results(assessment_id):
    """Get assessment results"""
    if 'user_id' not in session:
        return redirect(url_for('auth.index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get assessment details
    cursor.execute('''
        SELECT scope_id, domain, status, overall_percentage, recommendations, created_at, updated_at
        FROM assessments 
        WHERE id = ? AND user_id = ?
    ''', (assessment_id, session['user_id']))
    assessment = cursor.fetchone()
    
    if not assessment:
        conn.close()
        return render_template('dashboard.html', error='Assessment not found')
    
    scope_id, domain, status, overall_percentage, recommendations, created_at, updated_at = assessment
    
    # Get responses
    cursor.execute('''
        SELECT capability_id, lens_id, answer, score, improvement_suggestions
        FROM responses 
        WHERE assessment_id = ?
        ORDER BY capability_id, lens_id
    ''', (assessment_id,))
    responses = cursor.fetchall()
    
    conn.close()
    
    # Parse recommendations
    def parse_recommendations(recommendations):
        if not recommendations:
            return []
        
        try:
            # Try to parse as JSON first
            parsed = json.loads(recommendations)
            if isinstance(parsed, list):
                return parsed
        except:
            pass
        
        # Fallback: parse as text
        recommendations_list = []
        current_rec = {}
        lines = recommendations.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Title:'):
                if current_rec:
                    recommendations_list.append(current_rec)
                current_rec = {'title': line[6:].strip()}
            elif line.startswith('Description:'):
                current_rec['description'] = line[12:].strip()
            elif line.startswith('Why it matters:'):
                current_rec['why_matters'] = line[15:].strip()
            elif line.startswith('Recommendation:'):
                current_rec['recommendation'] = line[15:].strip()
        
        if current_rec:
            recommendations_list.append(current_rec)
        
        return recommendations_list
    
    parsed_recommendations = parse_recommendations(recommendations)
    
    # Get domain-specific benchmarks
    cursor = conn.cursor()
    cursor.execute('''
        SELECT AVG(overall_percentage) as avg_score, COUNT(*) as count
        FROM assessments 
        WHERE domain = ? AND status = 'completed' AND id != ?
    ''', (domain, assessment_id))
    benchmark = cursor.fetchone()
    conn.close()
    
    return render_template('results.html', 
                         assessment_id=assessment_id,
                         domain=domain,
                         overall_percentage=overall_percentage,
                         recommendations=parsed_recommendations,
                         responses=responses,
                         benchmark=benchmark,
                         created_at=created_at)

@assessment_bp.route('/set_current_assessment/<int:assessment_id>')
def set_current_assessment(assessment_id):
    """Set current assessment for session"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify assessment belongs to user
    cursor.execute('SELECT id FROM assessments WHERE id = ? AND user_id = ?', (assessment_id, session['user_id']))
    assessment = cursor.fetchone()
    
    if not assessment:
        conn.close()
        return jsonify({'error': 'Assessment not found'}), 404
    
    conn.close()
    
    session['current_assessment_id'] = assessment_id
    return jsonify({'success': True}) 