"""
AI Service for FinOps Assessment Platform
Handles OpenAI integration, maturity evaluation, and recommendation generation.
"""

import os
import re
import sqlite3
from functools import lru_cache
import openai

# Import data structures (will be moved to data/ later)
from data.capabilities import CAPABILITIES, LENSES, SCOPES


@lru_cache(maxsize=1)
def get_openai_client():
    """Get OpenAI client with caching"""
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
    return openai.OpenAI(api_key=api_key, base_url=base_url)


def evaluate_finops_maturity(capability_name, lens_name, answer_level, answer_details, scope_name):
    """
    Evaluate FinOps maturity based on the FinOps Foundation Assessment Guide
    """
    # Map answer levels to maturity scores
    level_mapping = {
        '0-20%': 0,
        '21-40%': 1,
        '41-60%': 2,
        '61-80%': 3,
        '81-100%': 4
    }
    
    # Get base score from level selection
    base_score = level_mapping.get(answer_level, 2)
    
    # FinOps Foundation maturity characteristics
    maturity_characteristics = {
        0: {
            'name': 'Crawl',
            'description': 'No capability or awareness',
            'characteristics': [
                'No processes, tools, or understanding',
                'Ad-hoc activities with no formal structure',
                'No dedicated resources or ownership',
                'Reactive approach to cost management'
            ]
        },
        1: {
            'name': 'Walk',
            'description': 'Basic awareness and ad-hoc activities',
            'characteristics': [
                'Limited understanding and inconsistent execution',
                'Some basic tools but no formal processes',
                'Occasional activities without systematic approach',
                'Basic cost visibility with manual processes'
            ]
        },
        2: {
            'name': 'Run',
            'description': 'Some processes in place',
            'characteristics': [
                'Inconsistent execution with basic tools',
                'Partial understanding and occasional success',
                'Some formal processes but not consistently applied',
                'Regular cost reviews with some automation'
            ]
        },
        3: {
            'name': 'Fly',
            'description': 'Well-defined processes',
            'characteristics': [
                'Consistent execution with good tools',
                'Strong understanding and regular success',
                'Formal processes with clear ownership',
                'Proactive cost optimization with good visibility'
            ]
        },
        4: {
            'name': 'Optimize',
            'description': 'Optimized and automated',
            'characteristics': [
                'Continuous improvement with advanced tools',
                'Expert level understanding and consistent excellence',
                'Automated processes with predictive capabilities',
                'Strategic cost management with predictive analytics'
            ]
        }
    }
    
    # Analyze the detailed response for additional insights
    details_lower = answer_details.lower()
    
    # Adjust score based on detailed response analysis
    score_adjustment = 0
    
    # Positive indicators
    positive_indicators = [
        'automated', 'automation', 'consistent', 'processes', 'formal', 'structured',
        'tools', 'platform', 'dashboard', 'monitoring', 'tracking', 'optimization',
        'governance', 'policies', 'standards', 'training', 'education', 'team',
        'ownership', 'responsibility', 'metrics', 'kpis', 'reporting', 'analysis'
    ]
    
    # Negative indicators
    negative_indicators = [
        'manual', 'ad-hoc', 'inconsistent', 'no process', 'no tools', 'no understanding',
        'limited', 'basic', 'occasional', 'reactive', 'no ownership', 'no responsibility',
        'no monitoring', 'no tracking', 'no optimization', 'no governance'
    ]
    
    positive_count = sum(1 for indicator in positive_indicators if indicator in details_lower)
    negative_count = sum(1 for indicator in negative_indicators if indicator in details_lower)
    
    # Adjust score based on indicators
    if positive_count > negative_count:
        score_adjustment = min(1, (positive_count - negative_count) / 3)
    elif negative_count > positive_count:
        score_adjustment = max(-1, -(negative_count - positive_count) / 3)
    
    final_score = max(0, min(4, base_score + score_adjustment))
    
    # Get maturity level info
    maturity_info = maturity_characteristics[int(final_score)]
    
    # Generate improvement suggestions based on current level
    improvement_suggestions = generate_improvement_suggestions(capability_name, lens_name, final_score, maturity_info)
    
    return {
        'score': final_score,
        'maturity_level': maturity_info['name'],
        'description': maturity_info['description'],
        'characteristics': maturity_info['characteristics'],
        'improvement_suggestions': improvement_suggestions,
        'confidence': 'High' if abs(score_adjustment) < 0.5 else 'Medium',
        'industry_comparison': get_industry_comparison(final_score, capability_name, lens_name),
        'risks': get_risks(final_score, capability_name, lens_name)
    }


def generate_improvement_suggestions(capability_name, lens_name, current_score, maturity_info):
    """Generate specific improvement suggestions based on current maturity level"""
    
    suggestions = {
        0: [
            "Establish basic awareness and understanding of FinOps principles",
            "Begin with simple cost visibility and basic reporting",
            "Identify key stakeholders and establish initial ownership",
            "Start with manual processes and basic tools"
        ],
        1: [
            "Develop formal processes and procedures",
            "Implement basic automation and tooling",
            "Establish regular review cycles and governance",
            "Begin training and education programs"
        ],
        2: [
            "Standardize processes across the organization",
            "Enhance automation and tool integration",
            "Implement comprehensive monitoring and alerting",
            "Develop advanced analytics and reporting capabilities"
        ],
        3: [
            "Optimize existing processes for efficiency",
            "Implement predictive analytics and forecasting",
            "Enhance cross-team collaboration and communication",
            "Develop advanced automation and AI capabilities"
        ],
        4: [
            "Focus on continuous improvement and innovation",
            "Implement advanced predictive and prescriptive analytics",
            "Develop strategic cost optimization strategies",
            "Establish industry leadership and best practices"
        ]
    }
    
    base_suggestions = suggestions.get(int(current_score), suggestions[2])
    
    # Add capability-specific suggestions
    capability_suggestions = get_capability_specific_suggestions(capability_name, lens_name, current_score)
    
    return base_suggestions + capability_suggestions


def get_capability_specific_suggestions(capability_name, lens_name, current_score):
    """Get specific suggestions based on capability and lens"""
    
    suggestions = {
        'data_ingestion': {
            'knowledge': [
                "Implement data governance and quality standards",
                "Establish data lineage and documentation processes",
                "Develop data validation and monitoring capabilities"
            ],
            'process': [
                "Standardize data ingestion workflows",
                "Implement automated data quality checks",
                "Establish data ownership and responsibility"
            ]
        },
        'allocation': {
            'knowledge': [
                "Develop comprehensive tagging strategies",
                "Establish cost allocation methodologies",
                "Implement chargeback and showback processes"
            ],
            'process': [
                "Standardize allocation rules and policies",
                "Implement automated allocation processes",
                "Establish allocation review and approval workflows"
            ]
        }
        # Add more capabilities as needed
    }
    
    capability_suggestions = suggestions.get(capability_name, {}).get(lens_name, [])
    
    # Filter suggestions based on current score
    if current_score < 2:
        return capability_suggestions[:2]  # Focus on basics
    elif current_score < 3:
        return capability_suggestions[:3]  # Add intermediate suggestions
    else:
        return capability_suggestions  # All suggestions for advanced levels


def get_industry_comparison(score, capability_name, lens_name):
    """Get industry comparison based on score and capability"""
    
    if score <= 1:
        return f"Below average for {capability_name} {lens_name} - 30% of organizations are at this level"
    elif score <= 2:
        return f"Average for {capability_name} {lens_name} - 55% of organizations are at this level"
    elif score <= 3:
        return f"Above average for {capability_name} {lens_name} - 15% of organizations reach this level"
    else:
        return f"Leading edge for {capability_name} {lens_name} - Top 5% of organizations achieve this level"


def get_risks(score, capability_name, lens_name):
    """Get potential risks based on current maturity level"""
    
    if score <= 1:
        return f"High risk of cost overruns and inefficiencies in {capability_name} {lens_name}. Lack of visibility and control may lead to significant financial impact."
    elif score <= 2:
        return f"Moderate risk in {capability_name} {lens_name}. Inconsistent processes may lead to missed optimization opportunities and increased costs."
    elif score <= 3:
        return f"Low risk in {capability_name} {lens_name}. Well-established processes provide good control and optimization capabilities."
    else:
        return f"Minimal risk in {capability_name} {lens_name}. Advanced capabilities provide excellent control and optimization."


def generate_recommendations(assessment_id, scope_id, domain, overall_percentage, lens_scores, database_path='finops_assessment.db'):
    """Generate concise, actionable recommendations using OpenAI API, based on lowest scores from Results Matrix."""
    try:
        # Get all responses for this assessment
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT capability_id, lens_id, answer, score, improvement_suggestions, evidence_files
            FROM responses 
            WHERE assessment_id = ?
            ORDER BY capability_id, lens_id
        ''', (assessment_id,))
        responses = cursor.fetchall()
        conn.close()
        
        # Build results matrix to find lowest scores
        results_matrix = {}
        lowest_scores = []
        
        for capability_id, lens_id, answer, score, improvement, evidence_files in responses:
            if not capability_id or not lens_id:
                continue
            if capability_id not in results_matrix:
                results_matrix[capability_id] = {}
            
            score_value = score or 0
            results_matrix[capability_id][lens_id] = {
                'score': score_value,
                'answer': answer,
                'improvement': improvement or 'No suggestions available'
            }
            
            # Get capability and lens names
            capability_name = next((c['name'] for c in CAPABILITIES if c['id'] == capability_id), capability_id)
            lens_name = next((l['name'] for l in LENSES if l['id'] == lens_id), lens_id)
            
            # Add to lowest scores list for sorting
            lowest_scores.append({
                'capability_id': capability_id,
                'capability_name': capability_name,
                'lens_id': lens_id,
                'lens_name': lens_name,
                'score': score_value,
                'answer': answer,
                'improvement': improvement or 'No suggestions available'
            })
        
        # Sort by score (ascending) to get lowest scores first
        lowest_scores.sort(key=lambda x: x['score'])
        
        # Take up to 5 lowest scores for recommendations
        target_recommendations = lowest_scores[:5]
        
        # Prepare summary for OpenAI
        assessment_summary = f"""
        Assessment Summary:
        - Scope: {next((s['name'] for s in SCOPES if s['id'] == scope_id), scope_id)}
        - Overall Score: {overall_percentage}%
        - Domain: {domain}
        """
        
        # Prepare lowest scores context for OpenAI
        lowest_scores_context = "\nLowest Scoring Areas (Focus for Recommendations):\n"
        for item in target_recommendations:
            lowest_scores_context += f"- {item['capability_name']} ({item['lens_name']}): Score {item['score']}/4\n"
            lowest_scores_context += f"  Answer: {item['answer'][:150]}{'...' if len(item['answer']) > 150 else ''}\n"
            lowest_scores_context += f"  Current Improvement: {item['improvement'][:150]}{'...' if len(item['improvement']) > 150 else ''}\n\n"
        
        # Updated prompt to focus on lowest scores with new structure
        prompt = f"""
        You are a FinOps expert. Based on the user's lowest scoring areas below, provide exactly {len(target_recommendations)} concise, actionable recommendations for FinOps maturity improvement. Focus on the areas with the lowest scores.

        CRITICAL: You must output ONLY the recommendations in this EXACT format, with NO extra text, headers, or explanations:

        Title: [Title of Recommendation]
        Description: [Brief description of the recommendation]
        Why it is important: [Explanation of why this matters for FinOps maturity]
        Recommendation: [Specific actionable steps to implement]

        Title: [Title of Recommendation]
        Description: [Brief description of the recommendation]
        Why it is important: [Explanation of why this matters for FinOps maturity]
        Recommendation: [Specific actionable steps to implement]

        Continue this format for all {len(target_recommendations)} recommendations. Do NOT include any introduction, summary, section headers, or extra text. Do NOT number the recommendations. Do NOT use any other labels or formatting.

        {assessment_summary}
        {lowest_scores_context}
        """
        
        # Call OpenAI API
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are a FinOps expert. You must output EXACTLY {len(target_recommendations)} recommendations in the specified format. Each recommendation must have: Title:, Description:, Why it is important:, and Recommendation:. Do NOT include any extra text, headers, explanations, or numbering. Only output the required fields in the exact order. Focus on the lowest scoring areas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.5
            )
            recommendations = response.choices[0].message.content
            if recommendations is None:
                recommendations = ''
            
            # Clean up the recommendations to ensure proper formatting
            # Remove any extra text at the beginning or end
            recommendations = re.sub(r'^(Executive Summary|Introduction|Conclusion|Summary|Here are|Based on|I\'ll provide).*?\n', '', recommendations, flags=re.DOTALL | re.IGNORECASE)
            recommendations = re.sub(r'\n\n+', '\n\n', recommendations)
            recommendations = recommendations.strip()
            
            # Ensure we have the proper structure
            if not re.search(r'Description:', recommendations):
                # If the AI didn't follow the format, create a fallback structure
                lines = recommendations.split('\n')
                formatted_recommendations = []
                current_recommendation = []
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('Description:') and not line.startswith('Why it is important:') and not line.startswith('Recommendation:'):
                        if current_recommendation:
                            formatted_recommendations.append('\n'.join(current_recommendation))
                            current_recommendation = []
                        current_recommendation.append(line)
                        current_recommendation.append('Description: Brief description of this recommendation')
                        current_recommendation.append('Why it is important: This will help improve your FinOps maturity')
                        current_recommendation.append('Recommendation: Implement specific steps to address this area')
                
                if current_recommendation:
                    formatted_recommendations.append('\n'.join(current_recommendation))
                
                recommendations = '\n\n'.join(formatted_recommendations)
                
        except Exception as e:
            print(f"OpenAI API error: {e}")
            recommendations = "Unable to generate recommendations at this time. Please try again later."
        
        # Store recommendations in database ONLY if successful
        if recommendations and "Unable to generate recommendations" not in recommendations:
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE assessments 
                SET recommendations = ?
                WHERE id = ?
            ''', (recommendations, assessment_id))
            conn.commit()
            conn.close()
        
        return recommendations
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return "Unable to generate recommendations at this time. Please try again later." 