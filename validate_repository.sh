#!/bin/bash

# 🔍 Repository Validation Script
# Valida se o repositório segue as regras estabelecidas

echo "🔍 Validando repositório..."
echo "=================================="

ERRORS=0

# 1. Verificar arquivos de deploy
echo "📋 Verificando arquivos de deploy..."
DEPLOY_FILES=$(git ls-files 2>/dev/null | grep -E "(security_deploy_script|production_security_check|update_dependencies|deploy_newrelic|get_newrelic_info)" || true)

if [ ! -z "$DEPLOY_FILES" ]; then
    echo "❌ ERRO: Arquivos de deploy encontrados no repositório:"
    echo "$DEPLOY_FILES"
    echo "Execute: git rm --cached <arquivo>"
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
    echo "Execute: git rm --cached <arquivo>"
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
    echo "Execute: git rm --cached <arquivo>"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Nenhum arquivo sensível encontrado no repositório"
fi

# 4. Verificar arquivos de desenvolvimento
echo ""
echo "🛠️ Verificando arquivos de desenvolvimento..."
DEV_FILES=$(git ls-files 2>/dev/null | grep -E "(VERSION|test_deploy|\.db|__pycache__|venv/)" || true)

if [ ! -z "$DEV_FILES" ]; then
    echo "❌ ERRO: Arquivos de desenvolvimento encontrados no repositório:"
    echo "$DEV_FILES"
    echo "Execute: git rm --cached <arquivo>"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Nenhum arquivo de desenvolvimento encontrado no repositório"
fi

# 5. Verificar .gitignore
echo ""
echo "📝 Verificando .gitignore..."
if [ ! -f ".gitignore" ]; then
    echo "❌ ERRO: Arquivo .gitignore não encontrado"
    ERRORS=$((ERRORS + 1))
else
    # Verificar se arquivos de deploy estão no .gitignore
    if ! grep -q "security_deploy_script.py" .gitignore; then
        echo "❌ ERRO: security_deploy_script.py não está no .gitignore"
        ERRORS=$((ERRORS + 1))
    fi
    
    if ! grep -q "production_security_check.py" .gitignore; then
        echo "❌ ERRO: production_security_check.py não está no .gitignore"
        ERRORS=$((ERRORS + 1))
    fi
    
    if ! grep -q "update_dependencies.py" .gitignore; then
        echo "❌ ERRO: update_dependencies.py não está no .gitignore"
        ERRORS=$((ERRORS + 1))
    fi
    
    if ! grep -q "AUTOMATED_MERGE_REQUEST_GUIDE.md" .gitignore; then
        echo "❌ ERRO: AUTOMATED_MERGE_REQUEST_GUIDE.md não está no .gitignore"
        ERRORS=$((ERRORS + 1))
    fi
    
    if ! grep -q "DOCUMENTATION_STANDARDS.md" .gitignore; then
        echo "❌ ERRO: DOCUMENTATION_STANDARDS.md não está no .gitignore"
        ERRORS=$((ERRORS + 1))
    fi
    
    if [ $ERRORS -eq 0 ]; then
        echo "✅ .gitignore configurado corretamente"
    fi
fi

# 6. Verificar arquivos essenciais
echo ""
echo "✅ Verificando arquivos essenciais..."
ESSENTIAL_FILES=("app.py" "config.py" "requirements.txt" "README.md" "SECURITY.md")

for file in "${ESSENTIAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ ERRO: Arquivo essencial não encontrado: $file"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ $file encontrado"
    fi
done

# 7. Verificar diretórios essenciais
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
    echo "🔧 Para corrigir:"
    echo "1. Remova arquivos de deploy: git rm --cached <arquivo>"
    echo "2. Atualize .gitignore se necessário"
    echo "3. Execute este script novamente"
    exit 1
fi 