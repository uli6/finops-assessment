"""
FinOps Framework Data
Contains all the capabilities, lenses, scopes, and questions for the assessment.
"""

# FinOps Framework Scopes
SCOPES = [
    {
        "id": "public_cloud",
        "name": "Public Cloud",
        "description": "AWS, Azure, GCP and other public cloud workloads"
    },
    {
        "id": "saas",
        "name": "SaaS",
        "description": "Software as a Service applications and subscriptions"
    },
    {
        "id": "data_center",
        "name": "Data Center",
        "description": "On-premises infrastructure and private cloud"
    },
    {
        "id": "licensing",
        "name": "Licensing",
        "description": "Software licensing and vendor management"
    },
    {
        "id": "ai_ml",
        "name": "AI/ML",
        "description": "Artificial Intelligence and Machine Learning workloads"
    }
]

# FinOps Assessment Lenses
LENSES = [
    {"id": "knowledge", "name": "Knowledge", "weight": 30},
    {"id": "process", "name": "Process", "weight": 25},
    {"id": "metrics", "name": "Metrics", "weight": 20},
    {"id": "adoption", "name": "Adoption", "weight": 20},
    {"id": "automation", "name": "Automation", "weight": 5}
]

# Updated FinOps Framework with 4 Domains and Detailed Capabilities
CAPABILITIES = [
    # Domain 1: Understand Usage & Cost
    {"id": "data_ingestion", "name": "Data Ingestion", "domain": "Understand Usage & Cost"},
    {"id": "allocation", "name": "Allocation", "domain": "Understand Usage & Cost"},
    {"id": "reporting_analytics", "name": "Reporting & Analytics", "domain": "Understand Usage & Cost"},
    {"id": "anomaly_management", "name": "Anomaly Management", "domain": "Understand Usage & Cost"},
    
    # Domain 2: Quantify Business Value
    {"id": "forecasting", "name": "Forecasting", "domain": "Quantify Business Value"},
    {"id": "budgeting", "name": "Budgeting", "domain": "Quantify Business Value"},
    {"id": "benchmark", "name": "Benchmark", "domain": "Quantify Business Value"},
    {"id": "unit_economics", "name": "Unit Economics", "domain": "Quantify Business Value"},
    
    # Domain 3: Optimize Usage & Cost
    {"id": "architecting_cloud", "name": "Architecting for Cloud", "domain": "Optimize Usage & Cost"},
    {"id": "rate_optimization", "name": "Rate Optimization", "domain": "Optimize Usage & Cost"},
    {"id": "workload_optimization", "name": "Workload Optimization", "domain": "Optimize Usage & Cost"},
    {"id": "cloud_sustainability", "name": "Cloud Sustainability", "domain": "Optimize Usage & Cost"},
    {"id": "licensing_saas", "name": "Licensing & SaaS", "domain": "Optimize Usage & Cost"},
    
    # Domain 4: Manage the FinOps Practice
    {"id": "finops_practice_operations", "name": "FinOps Practice Operations", "domain": "Manage the FinOps Practice"},
    {"id": "policy_governance", "name": "Policy & Governance", "domain": "Manage the FinOps Practice"},
    {"id": "finops_assessment", "name": "FinOps Assessment", "domain": "Manage the FinOps Practice"},
    {"id": "finops_tools_services", "name": "FinOps Tools & Services", "domain": "Manage the FinOps Practice"},
    {"id": "finops_education_enablement", "name": "FinOps Education & Enablement", "domain": "Manage the FinOps Practice"},
    {"id": "invoicing_chargeback", "name": "Invoicing & Chargeback", "domain": "Manage the FinOps Practice"},
    {"id": "onboarding_workloads", "name": "Onboarding Workloads", "domain": "Manage the FinOps Practice"},
    {"id": "intersecting_disciplines", "name": "Intersecting Disciplines", "domain": "Manage the FinOps Practice"}
]

# Domains list
DOMAINS = ["Understand Usage & Cost", "Quantify Business Value", "Optimize Usage & Cost", "Manage the FinOps Practice"]

# Answer options for different question types
ANSWER_OPTIONS = {
    "percentage_questions": [
        "0-20%",
        "21-40%", 
        "41-60%",
        "61-80%",
        "81-100%"
    ],
    "understanding_questions": [
        "No understanding",
        "Basic awareness",
        "Moderate understanding", 
        "Good understanding",
        "Expert level understanding"
    ],
    "standardization_questions": [
        "Not standardized",
        "Some standardization",
        "Mostly standardized",
        "Well standardized",
        "Fully standardized and documented"
    ],
    "consistency_questions": [
        "No consistency",
        "Low consistency",
        "Moderate consistency",
        "Good consistency", 
        "High consistency"
    ],
    "measurement_questions": [
        "No measurement",
        "Basic measurement",
        "Moderate measurement",
        "Good measurement",
        "Comprehensive measurement"
    ],
    "effectiveness_questions": [
        "Not effective",
        "Somewhat effective",
        "Moderately effective",
        "Effective",
        "Highly effective"
    ],
    "automation_questions": [
        "0-20%",
        "21-40%",
        "41-60%", 
        "61-80%",
        "81-100%"
    ]
} 