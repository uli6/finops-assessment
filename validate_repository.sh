#!/bin/bash

# 🔍 Repository Validation Script
# Valida se o repositório segue as regras estabelecidas

echo "🔍 Validando repositório..."
echo "=================================="

ERRORS=0
FILES_TO_REMOVE=()

# 1. Verificar arquivos de deploy
echo "📋 Verificando arquivos de deploy..."
DEPLOY_FILES=$(git ls-files 2>/dev/null | grep -E "(security_deploy_script|production_security_check|update_dependencies|deploy_newrelic|get_newrelic_info)" || true)

if [ ! -z "$DEPLOY_FILES" ]; then
    echo "❌ ERRO: Arquivos de deploy encontrados no repositório:"
    echo "$DEPLOY_FILES"
    FILES_TO_REMOVE+=($DEPLOY_FILES)
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Nenhum arquivo de deploy encontrado no repositório"
fi

# 2. Verificar documentação de deploy
echo ""
echo "📚 Verificando documentação de deploy..."
DOC_FILES=$(git ls-files 2>/dev/null | grep -E "(AUTOMATED_MERGE_REQUEST_GUIDE|DOCUMENTATION_STANDARDS|DOCUMENTATION_GUARANTEES|REPOSITORY_CLEANUP_SUMMARY|REPOSITORY_RULES)" || true)

if [ ! -z "$DOC_FILES" ]; then
    echo "❌ ERRO: Documentação de deploy encontrada no repositório:"
    echo "$DOC_FILES"
    FILES_TO_REMOVE+=($DOC_FILES)
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Nenhuma documentação de deploy encontrada no repositório"
fi

# 3. Verificar arquivos sensíveis
echo ""
echo "🔒 Verificando arquivos sensíveis..."
SENSITIVE_FILES=$(git ls-files 2>/dev/null | grep -E "(\.env$|newrelic\.ini|\.key|\.pem|\.crt)" || true)

if [ ! -z "$SENSITIVE_FILES" ]; then
    echo "❌ ERRO: Arquivos sensíveis encontrados no repositório:"
    echo "$SENSITIVE_FILES"
    FILES_TO_REMOVE+=($SENSITIVE_FILES)
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Nenhum arquivo sensível encontrado no repositório"
fi

# 4. Verificar arquivos de desenvolvimento
echo ""
echo "🛠️ Verificando arquivos de desenvolvimento..."
DEV_FILES=$(git ls-files 2>/dev/null | grep -E "(VERSION|test_deploy|\.db|__pycache__|venv/|finops-assessment\.code-workspace)" || true)

if [ ! -z "$DEV_FILES" ]; then
    echo "❌ ERRO: Arquivos de desenvolvimento encontrados no repositório:"
    echo "$DEV_FILES"
    FILES_TO_REMOVE+=($DEV_FILES)
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Nenhum arquivo de desenvolvimento encontrado no repositório"
fi

# 5. Verificar arquivos de teste desnecessários
echo ""
echo "🧪 Verificando arquivos de teste..."
TEST_FILES=$(git ls-files 2>/dev/null | grep -E "(test_.*\.txt|test_.*\.py)" || true)

if [ ! -z "$TEST_FILES" ]; then
    echo "❌ ERRO: Arquivos de teste encontrados no repositório:"
    echo "$TEST_FILES"
    FILES_TO_REMOVE+=($TEST_FILES)
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Nenhum arquivo de teste encontrado no repositório"
fi

# 6. Verificar .gitignore (opcional)
echo ""
echo "📝 Verificando .gitignore..."
if [ ! -f ".gitignore" ]; then
    echo "⚠️ AVISO: Arquivo .gitignore não encontrado"
else
    # Verificar se arquivos de deploy estão no .gitignore (apenas avisos)
    REQUIRED_IGNORES=(
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
        ".env"
        "newrelic.ini"
    )
    
    GITIGNORE_WARNINGS=0
    for ignore in "${REQUIRED_IGNORES[@]}"; do
        if ! grep -q "$ignore" .gitignore; then
            echo "⚠️ AVISO: $ignore não está no .gitignore (mas não está no repositório)"
            GITIGNORE_WARNINGS=$((GITIGNORE_WARNINGS + 1))
        fi
    done
    
    if [ $GITIGNORE_WARNINGS -eq 0 ]; then
        echo "✅ .gitignore configurado corretamente"
    else
        echo "⚠️ $GITIGNORE_WARNINGS aviso(s) no .gitignore (não são erros críticos)"
    fi
fi

# 7. Verificar arquivos essenciais
echo ""
echo "✅ Verificando arquivos essenciais..."
ESSENTIAL_FILES=("app.py" "config.py" "requirements.txt" "README.md" ".env.template" "privacy_notice.md")

for file in "${ESSENTIAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ ERRO: Arquivo essencial não encontrado: $file"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ $file encontrado"
    fi
done

# 8. Verificar diretórios essenciais
echo ""
echo "📁 Verificando diretórios essenciais..."
ESSENTIAL_DIRS=("models" "routes" "services" "data" "templates")

for dir in "${ESSENTIAL_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "❌ ERRO: Diretório essencial não encontrado: $dir"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ $dir encontrado"
    fi
done

# Resultado final
echo ""
echo "=================================="
if [ $ERRORS -eq 0 ]; then
    echo "🎉 Repositório válido!"
    echo "✅ Todas as regras foram seguidas"
    exit 0
else
    echo "❌ Repositório inválido!"
    echo "❌ $ERRORS erro(s) encontrado(s)"
    echo ""
    
    # Mostrar arquivos que precisam ser removidos
    if [ ${#FILES_TO_REMOVE[@]} -gt 0 ]; then
        echo "🗑️ Arquivos que precisam ser removidos do repositório:"
        for file in "${FILES_TO_REMOVE[@]}"; do
            echo "   - $file"
        done
        echo ""
        echo "🔧 Para corrigir automaticamente, execute:"
        echo "   ./cleanup_repository.sh"
    fi
    
    echo "🔧 Para corrigir manualmente:"
    echo "1. Remova arquivos de deploy: git rm --cached <arquivo>"
    echo "2. Atualize .gitignore se necessário"
    echo "3. Execute este script novamente"
    exit 1
fi 