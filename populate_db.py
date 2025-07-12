#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados sintéticos
para criar um ambiente mais realista para benchmarking.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os

# Configuração
DATABASE = 'finops_assessment.db'
ENCRYPTION_KEY_FILE = 'encryption.key'

# Carregar chave de criptografia
if os.path.exists(ENCRYPTION_KEY_FILE):
    with open(ENCRYPTION_KEY_FILE, 'rb') as f:
        ENCRYPTION_KEY = f.read()
else:
    ENCRYPTION_KEY = Fernet.generate_key()
    with open(ENCRYPTION_KEY_FILE, 'wb') as f:
        f.write(ENCRYPTION_KEY)

cipher = Fernet(ENCRYPTION_KEY)

def encrypt_data(data):
    """Criptografar dados sensíveis"""
    if data is None:
        return None
    return cipher.encrypt(data.encode()).decode()

# Dados sintéticos
ORGANIZATIONS = [
    "TechCorp Solutions",
    "CloudFirst Inc",
    "Digital Dynamics",
    "Innovation Labs",
    "Future Systems",
    "SmartTech Group",
    "Cloud Masters",
    "DataFlow Corp",
    "NextGen Tech",
    "Elite Solutions"
]

DOMAINS = [
    "Understanding Usage & Cost",
    "Quantify Business Value", 
    "Optimize Usage & Cost",
    "Manage the FinOps Practice"
]

SCOPES = [
    {"id": "public_cloud", "name": "Public Cloud"},
    {"id": "saas", "name": "SaaS"},
    {"id": "data_center", "name": "Data Center"},
    {"id": "licensing", "name": "Licensing"},
    {"id": "ai_ml", "name": "AI/ML"}
]

CAPABILITIES = [
    {"id": "cost_allocation", "name": "Cost Allocation", "domain": "Understanding Usage & Cost"},
    {"id": "data_analysis_showback", "name": "Data Analysis and Showback", "domain": "Understanding Usage & Cost"},
    {"id": "managing_anomalies", "name": "Managing Anomalies", "domain": "Understanding Usage & Cost"},
    {"id": "managing_shared_cost", "name": "Managing Shared Cost", "domain": "Understanding Usage & Cost"},
    {"id": "forecasting", "name": "Forecasting", "domain": "Quantify Business Value"},
    {"id": "budget_management", "name": "Budget Management", "domain": "Quantify Business Value"},
    {"id": "unit_economics", "name": "Unit Economics", "domain": "Quantify Business Value"},
    {"id": "measuring_unit_costs", "name": "Measuring Unit Costs", "domain": "Quantify Business Value"},
    {"id": "chargeback_finance_integration", "name": "Chargeback & Finance Integration", "domain": "Quantify Business Value"},
    {"id": "rightsizing", "name": "Rightsizing", "domain": "Optimize Usage & Cost"},
    {"id": "workload_management_automation", "name": "Workload Management & Automation", "domain": "Optimize Usage & Cost"},
    {"id": "rate_optimization", "name": "Rate Optimization", "domain": "Optimize Usage & Cost"},
    {"id": "cloud_sustainability", "name": "Cloud Sustainability", "domain": "Optimize Usage & Cost"},
    {"id": "onboarding_workloads", "name": "Onboarding Workloads", "domain": "Optimize Usage & Cost"},
    {"id": "resource_lifecycle_management", "name": "Resource Lifecycle Management", "domain": "Optimize Usage & Cost"},
    {"id": "cloud_policy_governance", "name": "Cloud Policy & Governance", "domain": "Optimize Usage & Cost"},
    {"id": "finops_education_enablement", "name": "FinOps Education & Enablement", "domain": "Manage the FinOps Practice"},
    {"id": "cloud_provider_data_ingestion", "name": "Cloud Provider Data Ingestion", "domain": "Manage the FinOps Practice"},
    {"id": "data_normalization", "name": "Data Normalization", "domain": "Manage the FinOps Practice"},
    {"id": "managing_commitment_based_discounts", "name": "Managing Commitment Based Discounts", "domain": "Manage the FinOps Practice"},
    {"id": "establishing_finops_culture", "name": "Establishing FinOps Culture", "domain": "Manage the FinOps Practice"},
    {"id": "intersecting_frameworks", "name": "Intersecting Frameworks", "domain": "Manage the FinOps Practice"}
]

LENSES = [
    {"id": "knowledge", "name": "Knowledge", "weight": 30},
    {"id": "process", "name": "Process", "weight": 25},
    {"id": "metrics", "name": "Metrics", "weight": 20},
    {"id": "adoption", "name": "Adoption", "weight": 20},
    {"id": "automation", "name": "Automation", "weight": 5}
]

ANSWERS = [
    "Not implemented",
    "Basic implementation", 
    "Well implemented",
    "Very well implemented",
    "Fully optimized"
]

def create_synthetic_users():
    """Criar usuários sintéticos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Verificar se já existem usuários sintéticos
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_synthetic = 1')
    existing_count = cursor.fetchone()[0]
    print(f"Usuários sintéticos existentes: {existing_count}")
    
    if existing_count > 0:
        print(f"Já existem {existing_count} usuários sintéticos. Pulando criação de usuários.")
        conn.close()
        return
    
    print("Criando usuários sintéticos...")
    
    for i in range(1, 21):  # 20 usuários sintéticos
        name = f"User {i}"
        email = f"user{i}@synthetic.com"
        organization = random.choice(ORGANIZATIONS)
        role = random.choice(["FinOps Engineer", "Cloud Architect", "DevOps Engineer", "Finance Manager", "CTO"])
        
        encrypted_name = encrypt_data(name)
        encrypted_email = encrypt_data(email)
        encrypted_org = encrypt_data(organization)
        encrypted_role = encrypt_data(role)
        
        print(f"Criando usuário {i}: {email} - {organization}")
        
        cursor.execute('''
            INSERT INTO users (name, email, organization, role, is_confirmed, is_admin, is_synthetic, created_at)
            VALUES (?, ?, ?, ?, 1, 0, 1, ?)
        ''', (
            encrypted_name,
            encrypted_email, 
            encrypted_org,
            encrypted_role,
            datetime.now() - timedelta(days=random.randint(1, 365))
        ))
    
    conn.commit()
    
    # Verificar se foram criados
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_synthetic = 1')
    new_count = cursor.fetchone()[0]
    print(f"Usuários criados: {new_count}")
    
    conn.close()
    print("✅ Usuários sintéticos criados!")

def create_synthetic_assessments():
    """Criar assessments sintéticos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Verificar se já existem assessments sintéticos
    cursor.execute('''
        SELECT COUNT(*) FROM assessments a 
        JOIN users u ON a.user_id = u.id 
        WHERE u.is_synthetic = 1
    ''')
    existing_count = cursor.fetchone()[0]
    print(f"Assessments sintéticos existentes: {existing_count}")
    
    if existing_count > 0:
        print(f"Já existem {existing_count} assessments sintéticos. Pulando criação de assessments.")
        conn.close()
        return
    
    print("Criando assessments sintéticos...")
    
    # Pegar IDs dos usuários sintéticos
    cursor.execute('SELECT id FROM users WHERE is_synthetic = 1')
    user_ids = [row[0] for row in cursor.fetchall()]
    print(f"IDs dos usuários sintéticos: {user_ids}")
    
    if not user_ids:
        print("❌ Nenhum usuário sintético encontrado!")
        conn.close()
        return
    
    for user_id in user_ids:
        # Criar 1-3 assessments por usuário
        num_assessments = random.randint(1, 3)
        print(f"Criando {num_assessments} assessments para usuário {user_id}")
        
        for _ in range(num_assessments):
            scope = random.choice(SCOPES)
            domain = random.choice(DOMAINS) if random.random() > 0.3 else None  # 30% chance de assessment completo
            
            print(f"  - Assessment: {scope['name']} - {domain or 'Complete'}")
            
            # Criar assessment
            cursor.execute('''
                INSERT INTO assessments (user_id, scope_id, domain, status, created_at, updated_at)
                VALUES (?, ?, ?, 'completed', ?, ?)
            ''', (
                user_id,
                scope['id'],
                domain,
                datetime.now() - timedelta(days=random.randint(1, 180)),
                datetime.now() - timedelta(days=random.randint(1, 30))
            ))
            
            assessment_id = cursor.lastrowid
            print(f"    Assessment ID: {assessment_id}")
            
            # Criar respostas para este assessment
            create_synthetic_responses(cursor, assessment_id, domain)
            
            # Calcular e atualizar overall_percentage
            update_assessment_score(cursor, assessment_id)
    
    conn.commit()
    
    # Verificar se foram criados
    cursor.execute('''
        SELECT COUNT(*) FROM assessments a 
        JOIN users u ON a.user_id = u.id 
        WHERE u.is_synthetic = 1
    ''')
    new_count = cursor.fetchone()[0]
    print(f"Assessments criados: {new_count}")
    
    conn.close()
    print("✅ Assessments sintéticos criados!")

def create_synthetic_responses(cursor, assessment_id, domain):
    """Criar respostas sintéticas para um assessment"""
    # Determinar quais capabilities usar
    if domain:
        capabilities = [c for c in CAPABILITIES if c['domain'] == domain]
    else:
        capabilities = CAPABILITIES
    
    # Criar respostas para cada capability + lens
    for capability in capabilities:
        for lens in LENSES:
            # Gerar score baseado em distribuição realística
            score = generate_realistic_score()
            answer = ANSWERS[score] if score < len(ANSWERS) else "Well implemented"
            
            cursor.execute('''
                INSERT INTO responses (assessment_id, capability_id, lens_id, answer, score, improvement_suggestions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                assessment_id,
                capability['id'],
                lens['id'],
                answer,
                score,
                generate_improvement_suggestion(capability, lens, score)
            ))

def generate_realistic_score():
    """Gerar score realístico baseado em distribuição normal"""
    # Distribuição: 0-1 (20%), 2 (30%), 3 (35%), 4 (15%)
    rand = random.random()
    if rand < 0.20:
        return random.choice([0, 1])
    elif rand < 0.50:
        return 2
    elif rand < 0.85:
        return 3
    else:
        return 4

def generate_improvement_suggestion(capability, lens, score):
    """Gerar sugestão de melhoria baseada no score"""
    if score >= 3:
        return f"Great progress on {capability['name']} {lens['name'].lower()}! Consider advanced optimization techniques."
    elif score == 2:
        return f"Good foundation for {capability['name']} {lens['name'].lower()}. Focus on process standardization and automation."
    else:
        return f"Start with basic {capability['name']} {lens['name'].lower()} implementation. Build foundational processes first."

def update_assessment_score(cursor, assessment_id):
    """Calcular e atualizar overall_percentage do assessment"""
    cursor.execute('SELECT score FROM responses WHERE assessment_id = ?', (assessment_id,))
    scores = cursor.fetchall()
    
    if scores:
        total_score = sum(score[0] or 0 for score in scores)
        total_possible = len(scores) * 4
        overall_percentage = round((total_score / total_possible) * 100) if total_possible > 0 else 0
        
        cursor.execute('''
            UPDATE assessments 
            SET overall_percentage = ? 
            WHERE id = ?
        ''', (overall_percentage, assessment_id))

def main():
    """Função principal"""
    print("🚀 Iniciando população do banco de dados com dados sintéticos...")
    
    try:
        # Criar usuários sintéticos
        create_synthetic_users()
        
        # Criar assessments sintéticos
        create_synthetic_assessments()
        
        # Mostrar estatísticas
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_synthetic = 1')
        synthetic_users = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM assessments a 
            JOIN users u ON a.user_id = u.id 
            WHERE u.is_synthetic = 1
        ''')
        synthetic_assessments = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM responses r
            JOIN assessments a ON r.assessment_id = a.id
            JOIN users u ON a.user_id = u.id
            WHERE u.is_synthetic = 1
        ''')
        synthetic_responses = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n📊 Estatísticas dos dados sintéticos:")
        print(f"   👥 Usuários: {synthetic_users}")
        print(f"   📋 Assessments: {synthetic_assessments}")
        print(f"   💬 Respostas: {synthetic_responses}")
        print(f"   📈 Média de respostas por assessment: {synthetic_responses // synthetic_assessments if synthetic_assessments > 0 else 0}")
        
        print("\n✅ População do banco de dados concluída!")
        print("💡 Agora você pode ver dados de benchmarking mais realistas!")
        
    except Exception as e:
        print(f"❌ Erro durante a população: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 