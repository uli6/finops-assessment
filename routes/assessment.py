from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file
import sqlite3
import json
import random
from datetime import datetime
from models.database import get_db_connection
from services.ai_service import evaluate_finops_maturity, generate_recommendations
from data.capabilities import CAPABILITIES, LENSES, DOMAINS, QUESTIONS, ANSWER_OPTIONS
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
    
    # Get domain-specific benchmarks for dashboard
    cursor.execute('''
        SELECT 
            a.domain,
            AVG(a.overall_percentage) as avg_score,
            COUNT(DISTINCT u.company_hash) as unique_companies
        FROM assessments a
        JOIN users u ON a.user_id = u.id
        WHERE a.status = 'completed'
        GROUP BY a.domain
        HAVING COUNT(DISTINCT u.company_hash) >= 1
    ''')
    benchmarks = cursor.fetchall()
    
    # Get dashboard statistics
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_confirmed = 1')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT company_hash) FROM users WHERE is_confirmed = 1')
    total_companies = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM assessments WHERE status = "in_progress"')
    assessments_in_progress = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM assessments WHERE status = "completed"')
    assessments_completed = cursor.fetchone()[0]
    
    # Create benchmark data for template
    benchmark_data = {}
    for domain, avg_score, unique_companies in benchmarks:
        benchmark_data[domain] = {
            'avg_score': round(avg_score, 1),
            'unique_companies': unique_companies
        }
    
    conn.close()
    
    return render_template('dashboard.html', 
                         assessments=assessments,
                         domains=DOMAINS,
                         benchmark_data=benchmark_data,
                         total_users=total_users,
                         total_companies=total_companies,
                         assessments_in_progress=assessments_in_progress,
                         assessments_completed=assessments_completed)

@assessment_bp.route('/start_assessment', methods=['POST'])
def start_assessment():
    """Start a new assessment"""
    print("=== START ASSESSMENT ROUTE CALLED ===")
    print("Session user_id:", session.get('user_id'))
    print("Request form data:", request.form)
    
    if 'user_id' not in session:
        print("ERROR: Not authenticated")
        return jsonify({'error': 'Not authenticated'}), 401
    
    domain = request.form.get('domain')
    print("Domain received:", domain)
    
    if domain is None:
        print("ERROR: Domain is required")
        return jsonify({'error': 'Domain is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create new assessment
    cursor.execute('''
        INSERT INTO assessments (user_id, scope_id, domain, status, created_at, updated_at)
        VALUES (?, ?, ?, 'in_progress', ?, ?)
    ''', (session['user_id'], 'complete', domain, datetime.now(), datetime.now()))
    
    assessment_id = cursor.lastrowid
    print("Created assessment with ID:", assessment_id)
    conn.commit()
    conn.close()
    
    print("Returning success response")
    return jsonify({'status': 'success', 'assessment_id': assessment_id, 'redirect': url_for('assessment.assessment')})

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
                        questions.append({
                            'capability_id': capability['id'],
                            'lens_id': lens['id'],
                            'capability_name': capability['name'],
                            'lens_name': lens['name'],
                            'question': lens_questions[0],
                            'answer': responses[question_key]['answer'],
                            'score': responses[question_key]['score'],
                            'answered': True,
                            'answer_options': ANSWER_OPTIONS["percentage_questions"],
                            'domain': capability['domain'] if domain == 'Complete Assessment' else domain
                        })
                    else:
                        questions.append({
                            'capability_id': capability['id'],
                            'lens_id': lens['id'],
                            'capability_name': capability['name'],
                            'lens_name': lens['name'],
                            'question': lens_questions[0],
                            'answered': False,
                            'answer_options': ANSWER_OPTIONS["percentage_questions"],
                            'domain': capability['domain'] if domain == 'Complete Assessment' else domain
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
    
    assessment_id = request.form.get('assessment_id')
    capability_id = request.form.get('capability_id')
    lens_id = request.form.get('lens_id')
    answer = request.form.get('answer')
    
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
        if isinstance(improvement_suggestions, list):
            improvement_suggestions = "\n".join(improvement_suggestions)
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
    
    return jsonify({'status': 'success', 'score': score})

@assessment_bp.route('/complete_assessment', methods=['POST'])
def complete_assessment():
    """Complete assessment and generate recommendations"""
    assessment_id = request.form.get('assessment_id')
    if not assessment_id:
        return jsonify({'status': 'error', 'message': 'Missing assessment_id'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify assessment belongs to user
    cursor.execute('SELECT domain FROM assessments WHERE id = ? AND user_id = ?', (assessment_id, session['user_id']))
    assessment = cursor.fetchone()
    
    if not assessment:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Assessment not found'}), 404
    
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
        return jsonify({'status': 'error', 'message': 'No responses found for assessment'}), 400
    
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
        'status': 'success',
        'overall_percentage': overall_percentage,
        'redirect': url_for('assessment.get_assessment_results', assessment_id=assessment_id)
    })

@assessment_bp.route('/get_assessment_results/<int:assessment_id>')
def get_assessment_results(assessment_id):
    """Get assessment results"""
    if 'user_id' not in session:
        return redirect(url_for('auth.index'))
    
    raw_average = 0
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
    
    # Get responses (only the latest response per capability_id + lens_id combination)
    cursor.execute('''
        SELECT capability_id, lens_id, answer, score, improvement_suggestions
        FROM responses r1
        WHERE assessment_id = ? 
        AND id = (
            SELECT MAX(id) 
            FROM responses r2 
            WHERE r2.assessment_id = r1.assessment_id 
            AND r2.capability_id = r1.capability_id 
            AND r2.lens_id = r1.lens_id
        )
        ORDER BY capability_id, lens_id
    ''', (assessment_id,))
    responses = cursor.fetchall()

    # --- Ensure recommendations are generated if missing or invalid ---
    def is_invalid_recommendations(recommendations):
        if not recommendations:
            return True
        if 'Unable to generate recommendations' in recommendations:
            return True
        if recommendations.strip() == '':
            return True
        return False

    if is_invalid_recommendations(recommendations):
        # Calculate overall percentage if needed
        total_score = sum(response[3] for response in responses) if responses else 0
        total_questions = len(responses) if responses else 0
        overall_pct = (total_score / total_questions) if total_questions > 0 else 0
        lens_scores = {f"{r[0]}_{r[1]}": r[3] for r in responses}
        from services.ai_service import generate_recommendations
        recommendations = generate_recommendations(assessment_id, scope_id, domain, overall_pct, lens_scores)
        # Save to DB
        cursor.execute('''
            UPDATE assessments SET recommendations = ? WHERE id = ?
        ''', (recommendations, assessment_id))
        conn.commit()

    # Calculate domain-specific benchmarks
    if domain == 'Complete Assessment':
        # For complete assessments, calculate benchmarks by domain using actual response scores
        domain_benchmarks = {}
        all_domains = ["Understand Usage & Cost", "Quantify Business Value", "Optimize Usage & Cost", "Manage the FinOps Practice"]
        
        for domain_name in all_domains:
            # Get all responses for this domain from domain-specific assessments
            cursor.execute('''
                SELECT r.score, u.company_hash, r.capability_id
                FROM assessments a
                JOIN users u ON a.user_id = u.id
                JOIN responses r ON a.id = r.assessment_id
                WHERE a.domain = ? AND a.status = 'completed'
            ''', (domain_name,))
            all_responses = cursor.fetchall()
            
            # Filter responses for this specific domain using Python data
            domain_responses = []
            for score, company_hash, capability_id in all_responses:
                capability = next((cap for cap in CAPABILITIES if cap['id'] == capability_id), None)
                if capability and capability['domain'] == domain_name:
                    domain_responses.append((score, company_hash))
            
            # Calculate average score for this domain
            if domain_responses:
                total_score = sum(response[0] for response in domain_responses)
                total_responses = len(domain_responses)
                avg_score = total_score / total_responses
                unique_companies = len(set(response[1] for response in domain_responses))
            else:
                avg_score = 0
                unique_companies = 0
            
            domain_benchmarks[domain_name] = {
                'avg_score': avg_score,
                'unique_companies': unique_companies,
                'has_data': unique_companies >= 1
            }
        
        # Calculate overall benchmark for complete assessment (any domains with data)
        valid_domains = [d for d in domain_benchmarks.values() if d['has_data']]
        if valid_domains:
            overall_avg = sum(d['avg_score'] for d in valid_domains) / len(valid_domains)
            total_companies = sum(d['unique_companies'] for d in valid_domains)
            has_benchmark_data = True
        else:
            overall_avg = 0
            total_companies = 0
            has_benchmark_data = False
        
        benchmark = (overall_avg, total_companies)
        industry_avg = overall_avg
    else:
        # For domain-specific assessments, get data from both domain-specific assessments AND complete assessments
        # First, get domain-specific assessment data using actual response scores
        cursor.execute('''
            SELECT r.score, u.company_hash
            FROM assessments a
            JOIN users u ON a.user_id = u.id
            JOIN responses r ON a.id = r.assessment_id
            WHERE a.domain = ? AND a.status = 'completed'
        ''', (domain,))
        domain_specific_responses = cursor.fetchall()
        
        # Calculate average score for domain-specific assessments
        domain_specific_avg = 0
        domain_specific_companies = 0
        if domain_specific_responses:
            total_score = sum(response[0] for response in domain_specific_responses)
            total_responses = len(domain_specific_responses)
            domain_specific_avg = total_score / total_responses
            domain_specific_companies = len(set(response[1] for response in domain_specific_responses))
        
        domain_specific_benchmark = (domain_specific_avg, domain_specific_companies)
        
        # Then, get domain data from complete assessments by analyzing responses
        # We need to calculate domain-specific scores from complete assessments
        cursor.execute('''
            SELECT 
                a.id,
                a.overall_percentage,
                u.company_hash,
                r.capability_id,
                r.score
            FROM assessments a
            JOIN users u ON a.user_id = u.id
            JOIN responses r ON a.id = r.assessment_id
            WHERE a.domain = 'Complete Assessment' 
            AND a.status = 'completed'
        ''')
        complete_assessment_responses = cursor.fetchall()
        
        # Calculate domain-specific scores from complete assessments
        complete_assessment_domain_scores = {}
        for assessment_id, overall_percentage, company_hash, capability_id, score in complete_assessment_responses:
            # Find the capability's domain from the Python data
            capability = next((cap for cap in CAPABILITIES if cap['id'] == capability_id), None)
            if capability and capability['domain'] == domain:
                if company_hash not in complete_assessment_domain_scores:
                    complete_assessment_domain_scores[company_hash] = {'total_score': 0, 'count': 0}
                complete_assessment_domain_scores[company_hash]['total_score'] += score
                complete_assessment_domain_scores[company_hash]['count'] += 1
        
        # Calculate average domain score from complete assessments
        complete_assessment_avg = 0
        complete_assessment_companies = 0
        if complete_assessment_domain_scores:
            domain_scores = []
            for company_hash, data in complete_assessment_domain_scores.items():
                if data['count'] > 0:
                    avg_score = data['total_score'] / data['count']
                    domain_scores.append(avg_score)
                    complete_assessment_companies += 1
            
            if domain_scores:
                complete_assessment_avg = sum(domain_scores) / len(domain_scores)
        
        complete_assessment_benchmark = (complete_assessment_avg, complete_assessment_companies)
        
        # Combine the data
        total_companies = 0
        total_score = 0
        company_count = 0
        
        if domain_specific_benchmark and domain_specific_benchmark[1] > 0:
            total_score += domain_specific_benchmark[0] * domain_specific_benchmark[1]
            total_companies += domain_specific_benchmark[1]
            company_count += 1
        
        if complete_assessment_benchmark and complete_assessment_benchmark[1] > 0:
            total_score += complete_assessment_benchmark[0] * complete_assessment_benchmark[1]
            total_companies += complete_assessment_benchmark[1]
            company_count += 1
        
        if total_companies > 0:
            industry_avg = total_score / total_companies
            has_benchmark_data = True
        else:
            industry_avg = 0
            has_benchmark_data = False
        
        benchmark = (industry_avg, total_companies)
        domain_benchmarks = None
    
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
    
    # Calculate total possible questions and points based on actual assessment scope
    # For complete assessment: 21 capabilities × 5 lenses = 105 questions
    # For domain-specific: varies by domain
    if domain == 'Complete Assessment':
        total_questions = 105  # 21 capabilities × 5 lenses
        total_possible_points = 105 * 4  # 105 questions × 4 points max each = 420 points
    else:
        # Count capabilities for this domain
        domain_capabilities = [cap for cap in CAPABILITIES if cap['domain'] == domain]
        total_questions = len(domain_capabilities) * 5  # 5 lenses per capability
        total_possible_points = total_questions * 4  # questions × 4 points max each
    
    # Calculate total score from responses
    total_score = sum(response[3] for response in responses) if responses else 0
    
    # Calculate correct overall percentage
    correct_overall_percentage = (total_score / total_possible_points) * 100 if total_possible_points > 0 else 0
    
    # Calculate domain-specific scores for complete assessments
    domain_scores = {}
    if domain == 'Complete Assessment' and responses:
        total_score = sum(response[3] for response in responses)
        total_questions = len(responses)
        user_score = (total_score / total_questions) if total_questions > 0 else 0
        # Cálculo dos scores por domínio:
        domain_scores = {}
        for response in responses:
            capability_id = response[0]
            score = response[3]
            capability = next((cap for cap in CAPABILITIES if cap['id'] == capability_id), None)
            if capability:
                cap_domain = capability['domain']
                if cap_domain not in domain_scores:
                    domain_scores[cap_domain] = {'total_score': 0, 'count': 0}
                domain_scores[cap_domain]['total_score'] += score
                domain_scores[cap_domain]['count'] += 1
        for domain_name in domain_scores:
            if domain_scores[domain_name]['count'] > 0:
                domain_scores[domain_name]['average'] = domain_scores[domain_name]['total_score'] / domain_scores[domain_name]['count']
            else:
                domain_scores[domain_name]['average'] = 0
        # domain_benchmarks já deve estar sendo calculado como antes, usando média 0-4
    else:
        # For domain-specific assessments, use average score per question
        user_score = (total_score / total_questions) if total_questions > 0 else 0
        # Calculate raw average for domain-specific assessments
        if responses:
            all_scores = [response[3] for response in responses]
            raw_average = sum(all_scores) / len(all_scores)
        else:
            raw_average = 0
    
    # Create results matrix for JavaScript visualization
    results_matrix = {}
    
    # Organize responses by capability_id and lens_id
    for response in responses:
        capability_id = response[0]
        lens_id = response[1]
        answer = response[2]
        score = response[3]
        improvement_suggestions = response[4]
        
        if capability_id not in results_matrix:
            results_matrix[capability_id] = {}
        
        results_matrix[capability_id][lens_id] = {
            'answer': answer,
            'score': score,
            'improvement_suggestions': improvement_suggestions
        }
    
    # Calculate unique questions answered (each response represents one question)
    unique_questions_answered = len(responses) if responses else 0
    
    # Add additional metadata
    results_matrix['metadata'] = {
        'domain': domain,
        'overall_percentage': overall_percentage,
        'industry_avg': industry_avg,
        'total_score': total_score,
        'total_possible_points': total_possible_points,
        'total_questions': total_questions,
        'responses_count': unique_questions_answered,
        'has_benchmark_data': has_benchmark_data,
        'unique_companies_for_benchmark': benchmark[1] if benchmark else 0
    }
    
    # Get capabilities and lenses for the domain
    if domain == 'Complete Assessment':
        # For complete assessments, get all capabilities
        domain_capabilities = CAPABILITIES
    else:
        # For domain-specific assessments, get capabilities for the specific domain
        domain_capabilities = [cap for cap in CAPABILITIES if cap['domain'] == domain]
    lenses = LENSES

    print("responses:", responses)
    print("user_score:", user_score)
    print("raw_average:", raw_average)
    print("total_score:", total_score)
    print("total_questions:", total_questions)
    print("assessment_id:", assessment_id)
    
    return render_template('results.html', 
                         assessment_id=assessment_id,
                         domain=domain,
                         status=status,
                         overall_percentage=correct_overall_percentage,
                         parsed_recommendations=parsed_recommendations,
                         responses=responses,
                         benchmark=benchmark,
                         created_at=created_at,
                         updated_at=updated_at,
                         total_possible_points=total_possible_points,
                         total_questions=total_questions,
                         total_score=total_score,
                         industry_avg=industry_avg,
                         user_score=user_score,
                         has_benchmark_data=has_benchmark_data,
                         results_matrix=results_matrix,
                         capabilities=domain_capabilities,
                         lenses=lenses,
                         assessment=[assessment_id, domain, status, correct_overall_percentage, created_at, updated_at],
                         domain_benchmarks=domain_benchmarks,
                         domain_scores=domain_scores,
                         unique_questions_answered=unique_questions_answered,
                         raw_average=raw_average)

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