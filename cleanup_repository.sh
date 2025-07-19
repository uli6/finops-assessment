#!/bin/bash

# 🧹 Repository Cleanup Script
# Remove automaticamente arquivos desnecessários do repositório

echo "🧹 Iniciando limpeza do repositório..."
echo "=================================="

# Lista de arquivos que devem ser removidos
FILES_TO_REMOVE=(
    "security_deploy_script.py"
    "production_security_check.py"
    "update_dependencies.py"
    "deploy_newrelic.py"
    "get_newrelic_info.py"
    "AUTOMATED_MERGE_REQUEST_GUIDE.md"
    "DOCUMENTATION_STANDARDS.md"
    "DOCUMENTATION_GUARANTEES.md"
    "REPOSITORY_CLEANUP_SUMMARY.md"
    "REPOSITORY_RULES.md"
    "test_deploy.txt"
    "finops-assessment.code-workspace"
    "SECURITY.md"
    ".github/workflows/deploy-production.yml"
    ".github/workflows/test.yml"
    ".github/workflows/release.yml"
)

# Lista de padrões de arquivos que devem ser removidos
PATTERNS_TO_REMOVE=(
    "test_*.txt"
    "test_*.py"
    "*.db"
    "__pycache__"
    "venv/"
    ".env"
    "newrelic.ini"
)

echo "🗑️ Removendo arquivos específicos..."
for file in "${FILES_TO_REMOVE[@]}"; do
    if git ls-files | grep -q "$file"; then
        echo "   Removendo: $file"
        git rm --cached "$file" 2>/dev/null || true
    fi
done

echo ""
echo "🗑️ Removendo arquivos por padrão..."
for pattern in "${PATTERNS_TO_REMOVE[@]}"; do
    if [[ "$pattern" == *"*"* ]]; then
        # Para padrões com wildcard
        files=$(git ls-files | grep -E "$pattern" || true)
        if [ ! -z "$files" ]; then
            echo "   Removendo padrão: $pattern"
            echo "$files" | xargs -I {} git rm --cached {} 2>/dev/null || true
        fi
    else
        # Para arquivos/diretórios específicos
        if git ls-files | grep -q "$pattern"; then
            echo "   Removendo: $pattern"
            git rm --cached -r "$pattern" 2>/dev/null || true
        fi
    fi
done

echo ""
echo "📝 Atualizando .gitignore..."
# Garantir que todos os arquivos removidos estejam no .gitignore
for file in "${FILES_TO_REMOVE[@]}"; do
    if ! grep -q "$file" .gitignore 2>/dev/null; then
        echo "$file" >> .gitignore
        echo "   Adicionado ao .gitignore: $file"
    fi
done

# Adicionar padrões ao .gitignore se não existirem
GITIGNORE_PATTERNS=(
    "# Deployment scripts"
    "security_deploy_script.py"
    "production_security_check.py"
    "update_dependencies.py"
    "deploy_newrelic.py"
    "get_newrelic_info.py"
    ""
    "# Documentation files"
    "AUTOMATED_MERGE_REQUEST_GUIDE.md"
    "DOCUMENTATION_STANDARDS.md"
    "DOCUMENTATION_GUARANTEES.md"
    "REPOSITORY_CLEANUP_SUMMARY.md"
    "REPOSITORY_RULES.md"
    "SECURITY.md"
    ""
    "# Development files"
    "test_deploy.txt"
    "test_*.txt"
    "test_*.py"
    "finops-assessment.code-workspace"
    "*.db"
    "__pycache__/"
    "venv/"
    ""
    "# Sensitive files"
    ".env"
    "newrelic.ini"
    "*.key"
    "*.pem"
    "*.crt"
    ""
    "# GitHub workflows"
    ".github/workflows/"
)

# Verificar se os padrões já estão no .gitignore
for pattern in "${GITIGNORE_PATTERNS[@]}"; do
    if [[ "$pattern" != "" && "$pattern" != "#"* ]]; then
        if ! grep -q "$pattern" .gitignore 2>/dev/null; then
            echo "$pattern" >> .gitignore
            echo "   Adicionado ao .gitignore: $pattern"
        fi
    fi
done

echo ""
echo "✅ Limpeza concluída!"
echo ""
echo "📋 Status atual:"
git status --porcelain

echo ""
echo "🔍 Para verificar se tudo está correto, execute:"
echo "   ./validate_repository.sh"
echo ""
echo "💾 Para fazer commit das mudanças:"
echo "   git add ."
echo "   git commit -m 'Cleanup: Remove unnecessary files from repository'" 