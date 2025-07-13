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

# Comprehensive Question Bank for Each Capability and Lens
QUESTIONS = {
    # Domain 1: Understand Usage & Cost
    "data_ingestion": {
        "knowledge": [
            "What percentage of your team members can explain the key data sources required for effective FinOps practice?",
            "How well do stakeholders understand the difference between billing data, usage data, and metadata in your organization?"
        ],
        "process": [
            "How standardized are your data ingestion processes across different cloud providers?",
            "What percentage of your data ingestion processes have documented procedures and responsible owners?"
        ],
        "metrics": [
            "What percentage of your required data sources are successfully ingested and available for analysis?",
            "How do you measure the quality and completeness of your ingested data?"
        ],
        "adoption": [
            "What percentage of your teams regularly use centralized data ingestion processes rather than maintaining their own data silos?",
            "How consistently do teams follow established data ingestion standards?"
        ],
        "automation": [
            "What percentage of your data ingestion processes are automated?",
            "How automated is your data quality validation process?"
        ]
    },
    "allocation": {
        "knowledge": [
            "What percentage of your organization understands the importance of proper cost allocation for cloud resources?",
            "How well do teams understand the allocation methodologies being used in your organization?"
        ],
        "process": [
            "How consistently are allocation rules applied across all cloud resources?",
            "What percentage of your allocation processes have documented methodologies and approval workflows?"
        ],
        "metrics": [
            "What percentage of your cloud costs can be allocated to specific business units, projects, or services?",
            "What percentage of your cloud resources are properly tagged for cost allocation purposes?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in the cost allocation process?",
            "How widely are allocated costs used for decision-making across the organization?"
        ],
        "automation": [
            "What percentage of your cost allocation processes are automated?",
            "How automated is the validation and reconciliation of allocated costs?"
        ]
    },
    "reporting_analytics": {
        "knowledge": [
            "What percentage of your stakeholders can interpret and act on FinOps reports and analytics?",
            "How well do teams understand which metrics are most relevant for their specific roles and responsibilities?"
        ],
        "process": [
            "How standardized are your reporting processes across different stakeholder groups?",
            "What percentage of your reports have defined refresh schedules and delivery mechanisms?"
        ],
        "metrics": [
            "What percentage of your reports provide actionable insights rather than just raw data?",
            "How effectively do your analytics identify optimization opportunities?"
        ],
        "adoption": [
            "What percentage of your teams regularly use FinOps reports for decision-making?",
            "How consistently do stakeholders access and act on provided reports?"
        ],
        "automation": [
            "What percentage of your reports are generated automatically?",
            "How automated is the distribution and consumption of your reports?"
        ]
    },
    "anomaly_management": {
        "knowledge": [
            "What percentage of your organization understands what constitutes a cost anomaly and its potential impact?",
            "How well do teams understand their roles and responsibilities when anomalies are detected?"
        ],
        "process": [
            "How well-defined are your anomaly detection and response processes?",
            "What percentage of detected anomalies follow a standardized investigation and resolution workflow?"
        ],
        "metrics": [
            "What percentage of cost anomalies are detected within your target timeframe?",
            "How effectively do you measure the impact and resolution time of anomalies?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in anomaly monitoring and response?",
            "How consistently do teams respond to anomaly alerts within defined SLAs?"
        ],
        "automation": [
            "What percentage of your anomaly detection is automated?",
            "How automated are your anomaly notification and escalation processes?"
        ]
    },
    
    # Domain 2: Quantify Business Value
    "forecasting": {
        "knowledge": [
            "What percentage of your stakeholders understand the difference between trends, seasonal patterns, and growth forecasting?",
            "How well do teams understand the data requirements and limitations of different forecasting methodologies?"
        ],
        "process": [
            "How standardized are your forecasting methodologies across different business units and time horizons?",
            "What percentage of your forecasts have defined update cycles and review processes?"
        ],
        "metrics": [
            "What percentage of your forecasts achieve acceptable accuracy levels within your defined tolerance range?",
            "How effectively do you measure and improve forecast accuracy over time?"
        ],
        "adoption": [
            "What percentage of your business decisions incorporate cloud cost forecasts?",
            "How consistently do teams use forecasts for capacity planning and budget preparation?"
        ],
        "automation": [
            "What percentage of your forecasting processes are automated?",
            "How automated is the generation and distribution of forecast reports?"
        ]
    },
    "budgeting": {
        "knowledge": [
            "What percentage of your organization understands the relationship between cloud budgets and business objectives?",
            "How well do teams understand budget variance analysis and corrective actions?"
        ],
        "process": [
            "How standardized are your budget creation and approval processes across the organization?",
            "What percentage of your budgets have defined monitoring and alerting mechanisms?"
        ],
        "metrics": [
            "What percentage of your teams consistently stay within their allocated cloud budgets?",
            "How effectively do you track and analyze budget variance trends?"
        ],
        "adoption": [
            "What percentage of your cloud spending is covered by formal budget allocations?",
            "How consistently do teams use budget information for decision-making?"
        ],
        "automation": [
            "What percentage of your budget monitoring and alerting is automated?",
            "How automated is the budget variance reporting and analysis process?"
        ]
    },
    "benchmark": {
        "knowledge": [
            "What percentage of your organization understands the value and limitations of cloud cost benchmarking?",
            "How well do teams understand which benchmarks are most relevant for their specific use cases?"
        ],
        "process": [
            "How standardized are your benchmarking methodologies across different services and workloads?",
            "What percentage of your benchmarks have defined update cycles and review processes?"
        ],
        "metrics": [
            "What percentage of your cloud services have established benchmarks for cost and performance?",
            "How effectively do you measure the accuracy and relevance of your benchmarks?"
        ],
        "adoption": [
            "What percentage of your teams regularly use benchmarks for cost optimization decisions?",
            "How consistently do teams incorporate benchmark data into their planning and decision-making?"
        ],
        "automation": [
            "What percentage of your benchmark data collection and analysis is automated?",
            "How automated is the benchmark reporting and alerting process?"
        ]
    },
    "unit_economics": {
        "knowledge": [
            "What percentage of your organization understands the concept of unit economics in cloud cost management?",
            "How well do teams understand which unit metrics are most relevant for their specific services?"
        ],
        "process": [
            "How standardized are your unit economics calculations across different services and business units?",
            "What percentage of your unit economics have defined calculation methodologies and review processes?"
        ],
        "metrics": [
            "What percentage of your cloud services have established unit economics metrics?",
            "How effectively do you measure and track unit economics trends over time?"
        ],
        "adoption": [
            "What percentage of your teams regularly use unit economics for cost optimization decisions?",
            "How consistently do teams incorporate unit economics into their service design and optimization efforts?"
        ],
        "automation": [
            "What percentage of your unit economics calculations and reporting is automated?",
            "How automated is the unit economics monitoring and alerting process?"
        ]
    },
    
    # Domain 3: Optimize Usage & Cost
    "architecting_cloud": {
        "knowledge": [
            "What percentage of your teams understand cloud-native architecture principles and their cost implications?",
            "How well do teams understand the cost trade-offs between different architectural patterns?"
        ],
        "process": [
            "How standardized are your cloud architecture review processes across different projects?",
            "What percentage of your architecture decisions have documented cost impact analysis?"
        ],
        "metrics": [
            "What percentage of your cloud workloads follow cost-optimized architectural patterns?",
            "How effectively do you measure the cost impact of architectural decisions?"
        ],
        "adoption": [
            "What percentage of your teams regularly consider cost implications in their architectural decisions?",
            "How consistently do teams follow established cloud architecture best practices?"
        ],
        "automation": [
            "What percentage of your architecture review and approval processes are automated?",
            "How automated is the cost impact analysis for architectural changes?"
        ]
    },
    "rate_optimization": {
        "knowledge": [
            "What percentage of your organization understands the different pricing models and optimization opportunities?",
            "How well do teams understand the trade-offs between different pricing options?"
        ],
        "process": [
            "How standardized are your rate optimization processes across different cloud providers?",
            "What percentage of your rate optimization decisions have documented analysis and approval workflows?"
        ],
        "metrics": [
            "What percentage of your cloud spending uses optimized pricing models?",
            "How effectively do you measure the savings achieved through rate optimization?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in rate optimization initiatives?",
            "How consistently do teams use optimized pricing models for their workloads?"
        ],
        "automation": [
            "What percentage of your rate optimization analysis and decision-making is automated?",
            "How automated is the rate optimization monitoring and alerting process?"
        ]
    },
    "workload_optimization": {
        "knowledge": [
            "What percentage of your teams understand workload optimization techniques and their cost impact?",
            "How well do teams understand the performance vs. cost trade-offs for their specific workloads?"
        ],
        "process": [
            "How standardized are your workload optimization processes across different teams and services?",
            "What percentage of your workload optimization initiatives have documented methodologies and success criteria?"
        ],
        "metrics": [
            "What percentage of your cloud workloads have undergone optimization analysis?",
            "How effectively do you measure the cost savings achieved through workload optimization?"
        ],
        "adoption": [
            "What percentage of your teams regularly perform workload optimization analysis?",
            "How consistently do teams implement optimization recommendations?"
        ],
        "automation": [
            "What percentage of your workload optimization analysis and recommendations is automated?",
            "How automated is the workload optimization monitoring and alerting process?"
        ]
    },
    "cloud_sustainability": {
        "knowledge": [
            "What percentage of your organization understands the environmental impact of cloud computing?",
            "How well do teams understand sustainability optimization techniques and their cost implications?"
        ],
        "process": [
            "How standardized are your sustainability optimization processes across different teams and services?",
            "What percentage of your sustainability initiatives have documented methodologies and success criteria?"
        ],
        "metrics": [
            "What percentage of your cloud workloads have undergone sustainability optimization analysis?",
            "How effectively do you measure the environmental impact of your cloud operations?"
        ],
        "adoption": [
            "What percentage of your teams regularly consider sustainability in their cloud decisions?",
            "How consistently do teams implement sustainability optimization recommendations?"
        ],
        "automation": [
            "What percentage of your sustainability optimization analysis and recommendations is automated?",
            "How automated is the sustainability monitoring and reporting process?"
        ]
    },
    "licensing_saas": {
        "knowledge": [
            "What percentage of your organization understands the cost implications of software licensing and SaaS subscriptions?",
            "How well do teams understand the different licensing models and optimization opportunities?"
        ],
        "process": [
            "How standardized are your licensing and SaaS optimization processes across different teams?",
            "What percentage of your licensing decisions have documented analysis and approval workflows?"
        ],
        "metrics": [
            "What percentage of your software licensing and SaaS spending is optimized?",
            "How effectively do you measure the savings achieved through licensing optimization?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in licensing and SaaS optimization initiatives?",
            "How consistently do teams use optimized licensing models for their needs?"
        ],
        "automation": [
            "What percentage of your licensing optimization analysis and decision-making is automated?",
            "How automated is the licensing monitoring and renewal alerting process?"
        ]
    },
    
    # Domain 4: Manage the FinOps Practice
    "finops_practice_operations": {
        "knowledge": [
            "What percentage of your organization understands the FinOps practice and its value proposition?",
            "How well do teams understand their roles and responsibilities within the FinOps practice?"
        ],
        "process": [
            "How standardized are your FinOps practice operations across different teams and business units?",
            "What percentage of your FinOps processes have documented procedures and responsible owners?"
        ],
        "metrics": [
            "What percentage of your FinOps practice objectives are being met?",
            "How effectively do you measure the success and impact of your FinOps practice?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in the FinOps practice?",
            "How consistently do teams follow established FinOps processes and procedures?"
        ],
        "automation": [
            "What percentage of your FinOps practice operations are automated?",
            "How automated is the FinOps practice monitoring and reporting process?"
        ]
    },
    "policy_governance": {
        "knowledge": [
            "What percentage of your organization understands the FinOps policies and governance framework?",
            "How well do teams understand their compliance requirements and responsibilities?"
        ],
        "process": [
            "How standardized are your policy and governance processes across different teams and business units?",
            "What percentage of your policies have documented procedures and enforcement mechanisms?"
        ],
        "metrics": [
            "What percentage of your cloud operations comply with established FinOps policies?",
            "How effectively do you measure policy compliance and governance effectiveness?"
        ],
        "adoption": [
            "What percentage of your teams actively follow established FinOps policies?",
            "How consistently do teams adhere to governance requirements and procedures?"
        ],
        "automation": [
            "What percentage of your policy enforcement and governance processes are automated?",
            "How automated is the policy compliance monitoring and reporting process?"
        ]
    },
    "finops_assessment": {
        "knowledge": [
            "What percentage of your organization understands the value of regular FinOps assessments?",
            "How well do teams understand the assessment process and its benefits?"
        ],
        "process": [
            "How standardized are your FinOps assessment processes across different teams and business units?",
            "What percentage of your assessments have documented methodologies and success criteria?"
        ],
        "metrics": [
            "What percentage of your FinOps assessments achieve their objectives?",
            "How effectively do you measure the impact and value of your FinOps assessments?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in FinOps assessments?",
            "How consistently do teams use assessment results for improvement planning?"
        ],
        "automation": [
            "What percentage of your FinOps assessment processes are automated?",
            "How automated is the assessment reporting and follow-up process?"
        ]
    },
    "finops_tools_services": {
        "knowledge": [
            "What percentage of your organization understands the available FinOps tools and services?",
            "How well do teams understand how to effectively use these tools and services?"
        ],
        "process": [
            "How standardized are your FinOps tools and services usage across different teams?",
            "What percentage of your tools and services have documented procedures and responsible owners?"
        ],
        "metrics": [
            "What percentage of your FinOps tools and services are being used effectively?",
            "How effectively do you measure the value and impact of your FinOps tools and services?"
        ],
        "adoption": [
            "What percentage of your teams actively use available FinOps tools and services?",
            "How consistently do teams leverage tools and services for their FinOps activities?"
        ],
        "automation": [
            "What percentage of your FinOps tools and services operations are automated?",
            "How automated is the tools and services monitoring and optimization process?"
        ]
    },
    "finops_education_enablement": {
        "knowledge": [
            "What percentage of your organization has received FinOps education and training?",
            "How well do teams understand the FinOps concepts and practices relevant to their roles?"
        ],
        "process": [
            "How standardized are your FinOps education and enablement processes across different teams?",
            "What percentage of your education initiatives have documented curricula and success criteria?"
        ],
        "metrics": [
            "What percentage of your teams have completed required FinOps education and training?",
            "How effectively do you measure the impact and value of your FinOps education initiatives?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in FinOps education and enablement activities?",
            "How consistently do teams apply their FinOps education in their daily work?"
        ],
        "automation": [
            "What percentage of your FinOps education and enablement processes are automated?",
            "How automated is the education tracking and reporting process?"
        ]
    },
    "invoicing_chargeback": {
        "knowledge": [
            "What percentage of your organization understands the invoicing and chargeback processes?",
            "How well do teams understand their financial responsibilities and accountability?"
        ],
        "process": [
            "How standardized are your invoicing and chargeback processes across different teams and business units?",
            "What percentage of your invoicing and chargeback processes have documented procedures and responsible owners?"
        ],
        "metrics": [
            "What percentage of your cloud costs are properly invoiced and charged back?",
            "How effectively do you measure the accuracy and timeliness of your invoicing and chargeback processes?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in the invoicing and chargeback processes?",
            "How consistently do teams follow established invoicing and chargeback procedures?"
        ],
        "automation": [
            "What percentage of your invoicing and chargeback processes are automated?",
            "How automated is the invoicing and chargeback monitoring and reporting process?"
        ]
    },
    "onboarding_workloads": {
        "knowledge": [
            "What percentage of your organization understands the FinOps onboarding process for new workloads?",
            "How well do teams understand their responsibilities during the onboarding process?"
        ],
        "process": [
            "How standardized are your workload onboarding processes across different teams and business units?",
            "What percentage of your onboarding processes have documented procedures and success criteria?"
        ],
        "metrics": [
            "What percentage of your new workloads follow the established FinOps onboarding process?",
            "How effectively do you measure the success and efficiency of your onboarding processes?"
        ],
        "adoption": [
            "What percentage of your teams actively participate in the FinOps onboarding process?",
            "How consistently do teams follow established onboarding procedures?"
        ],
        "automation": [
            "What percentage of your workload onboarding processes are automated?",
            "How automated is the onboarding monitoring and reporting process?"
        ]
    },
    "intersecting_disciplines": {
        "knowledge": [
            "What percentage of your organization understands how FinOps intersects with other disciplines?",
            "How well do teams understand the collaboration requirements with other disciplines?"
        ],
        "process": [
            "How standardized are your cross-discipline collaboration processes?",
            "What percentage of your cross-discipline initiatives have documented procedures and success criteria?"
        ],
        "metrics": [
            "What percentage of your FinOps initiatives involve effective collaboration with other disciplines?",
            "How effectively do you measure the success and value of cross-discipline collaboration?"
        ],
        "adoption": [
            "What percentage of your teams actively collaborate with other disciplines on FinOps initiatives?",
            "How consistently do teams engage in cross-discipline collaboration?"
        ],
        "automation": [
            "What percentage of your cross-discipline collaboration processes are automated?",
            "How automated is the cross-discipline monitoring and reporting process?"
        ]
    }
}

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