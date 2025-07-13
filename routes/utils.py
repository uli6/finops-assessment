from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file
import sqlite3
import json
import markdown
import html
from datetime import datetime
from models.database import get_db_connection
from services.ai_service import evaluate_finops_maturity
from config import DATABASE

utils_bp = Blueprint('utils', __name__)

@utils_bp.route('/test_openai')
def test_openai():
    """Test OpenAI API connection"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Test with a simple evaluation
        result = evaluate_finops_maturity("Data Ingestion", "Knowledge", "Good understanding", "", "complete")
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@utils_bp.route('/reprocess_response/<int:assessment_id>/<capability_id>/<lens_id>')
def reprocess_response(assessment_id, capability_id, lens_id):
    """Reprocess a specific response with AI"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify assessment belongs to user
    cursor.execute('SELECT user_id FROM assessments WHERE id = ?', (assessment_id,))
    assessment = cursor.fetchone()
    
    if not assessment or assessment[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Assessment not found'}), 404
    
    # Get the response
    cursor.execute('''
        SELECT answer FROM responses 
        WHERE assessment_id = ? AND capability_id = ? AND lens_id = ?
    ''', (assessment_id, capability_id, lens_id))
    response = cursor.fetchone()
    
    if not response:
        conn.close()
        return jsonify({'error': 'Response not found'}), 404
    
    answer = response[0]
    
    # Get capability and lens names
    from data.capabilities import CAPABILITIES, LENSES
    
    capability = next((c for c in CAPABILITIES if c['id'] == capability_id), None)
    lens = next((l for l in LENSES if l['id'] == lens_id), None)
    
    if not capability or not lens:
        conn.close()
        return jsonify({'error': 'Invalid capability or lens'}), 400
    
    try:
        # Reprocess with AI
        evaluation = evaluate_finops_maturity(capability['name'], lens['name'], answer, '', 'complete')
        score = evaluation['score']
        improvement_suggestions = evaluation['improvement_suggestions']
        
        # Update the response
        cursor.execute('''
            UPDATE responses 
            SET score = ?, improvement_suggestions = ?
            WHERE assessment_id = ? AND capability_id = ? AND lens_id = ?
        ''', (score, improvement_suggestions, assessment_id, capability_id, lens_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'score': score, 
            'improvement_suggestions': improvement_suggestions
        })
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Failed to reprocess: {str(e)}'}), 500

@utils_bp.route('/my_responses')
def my_responses():
    """View all user responses"""
    if 'user_id' not in session:
        return redirect(url_for('auth.index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all user's responses with assessment details
    cursor.execute('''
        SELECT 
            r.assessment_id,
            a.domain,
            r.capability_id,
            r.lens_id,
            r.answer,
            r.score,
            r.improvement_suggestions,
            r.created_at
        FROM responses r
        JOIN assessments a ON r.assessment_id = a.id
        WHERE a.user_id = ?
        ORDER BY r.created_at DESC
    ''', (session['user_id'],))
    responses = cursor.fetchall()
    
    conn.close()
    
    return render_template('my_responses.html', responses=responses)

@utils_bp.route('/settings')
def settings():
    """User settings page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.index'))
    
    return render_template('settings.html')

@utils_bp.route('/delete_account', methods=['DELETE'])
def delete_account():
    """Delete user account and all data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Delete all user data
        cursor.execute('DELETE FROM responses WHERE assessment_id IN (SELECT id FROM assessments WHERE user_id = ?)', (session['user_id'],))
        cursor.execute('DELETE FROM assessments WHERE user_id = ?', (session['user_id'],))
        cursor.execute('DELETE FROM users WHERE id = ?', (session['user_id'],))
        
        conn.commit()
        conn.close()
        
        session.clear()
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Failed to delete account: {str(e)}'}), 500

@utils_bp.route('/export_pdf/<int:assessment_id>')
def export_pdf(assessment_id):
    """Export assessment results as PDF"""
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
            parsed = json.loads(recommendations)
            if isinstance(parsed, list):
                return parsed
        except:
            pass
        
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
    
    # Generate HTML for PDF
    html_content = render_template('pdf_report.html',
                                 assessment_id=assessment_id,
                                 domain=domain,
                                 overall_percentage=overall_percentage,
                                 recommendations=parsed_recommendations,
                                 responses=responses,
                                 created_at=created_at)
    
    try:
        from weasyprint import HTML
        pdf = HTML(string=html_content).write_pdf()
        
        from io import BytesIO
        pdf_buffer = BytesIO(pdf) if pdf else BytesIO()
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'finops_assessment_{assessment_id}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate PDF: {str(e)}'}), 500

# Utility functions
def markdown_filter(text):
    """Convert markdown to HTML"""
    if not text:
        return ""
    
    # Fix URL links
    def fix_url_links(md):
        # Replace [https://...](https://...) with just the URL as a clickable link
        import re
        pattern = r'\[(https?://[^\]]+)\]\(https?://[^)]+\)'
        return re.sub(pattern, r'\1', md)
    
    # Convert markdown to HTML
    html_text = markdown.markdown(fix_url_links(text), extensions=['fenced_code', 'tables'])
    
    # Fix real example links
    def fix_real_example_links(html_text):
        # Replace links that point to finops.org
        import re
        pattern = r'<a href="https://www\.finops\.org[^"]*">([^<]+)</a>'
        return re.sub(pattern, r'\1', html_text)
    
    return fix_real_example_links(html_text) 