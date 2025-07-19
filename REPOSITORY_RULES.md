# 📋 Repository Rules - Regras Obrigatórias

## 🚨 **REGRAS CRÍTICAS - SEMPRE SEGUIR**

### **✅ ARQUIVOS QUE DEVEM estar no Repositório**

#### **Aplicação Principal**
- `app.py` - Aplicação Flask principal
- `config.py` - Configurações da aplicação
- `requirements.txt` - Dependências Python
- `README.md` - Documentação principal do projeto
- `SECURITY.md` - Política de segurança

#### **Diretórios da Aplicação**
- `models/` - Modelos de dados
- `routes/` - Rotas da aplicação
- `services/` - Serviços da aplicação
- `data/` - Dados da aplicação
- `templates/` - Templates HTML
- `uploads/` - Diretório de uploads

#### **Configuração**
- `.gitignore` - Configuração do Git
- `privacy_notice.md` - Aviso de privacidade

### **❌ ARQUIVOS QUE NUNCA DEVEM estar no Repositório**

#### **Scripts de Deploy e Desenvolvimento**
- `security_deploy_script.py`
- `production_security_check.py`
- `update_dependencies.py`
- `deploy_newrelic.py`
- `get_newrelic_info.py`

#### **Documentação de Deploy**
- `AUTOMATED_MERGE_REQUEST_GUIDE.md`
- `DOCUMENTATION_STANDARDS.md`
- `DOCUMENTATION_GUARANTEES.md`
- `REPOSITORY_CLEANUP_SUMMARY.md`
- `REPOSITORY_RULES.md` (este arquivo)

#### **Arquivos de Desenvolvimento**
- `VERSION`
- `test_deploy.txt`
- `finops_assessment.db`
- `__pycache__/`
- `venv/`

#### **Arquivos Sensíveis**
- `.env`
- `newrelic.ini`
- `*.key`, `*.pem`, `*.crt`

---

## 🔄 **Processo de Validação**

### **Antes de Qualquer Commit**

#### **1. Verificar .gitignore**
```bash
# Verificar se arquivos de deploy estão no .gitignore
grep -E "(security_deploy_script|production_security_check|update_dependencies)" .gitignore

# Verificar se documentação de deploy está no .gitignore
grep -E "(AUTOMATED_MERGE_REQUEST_GUIDE|DOCUMENTATION_STANDARDS|DOCUMENTATION_GUARANTEES)" .gitignore
```

#### **2. Verificar Arquivos no Repositório**
```bash
# Listar arquivos que estão sendo trackeados
git ls-files | grep -E "(security_deploy_script|production_security_check|update_dependencies)"

# Se retornar algo, REMOVER imediatamente
git rm --cached <arquivo>
```

#### **3. Verificar Referências**
```bash
# Verificar se há referências a arquivos de deploy no README
grep -E "(AUTOMATED_MERGE_REQUEST_GUIDE|DOCUMENTATION_STANDARDS)" README.md

# Se encontrar, REMOVER a referência
```

### **Checklist Obrigatório**

#### **✅ Antes de Commitar**
- [ ] Arquivos de deploy estão no .gitignore
- [ ] Documentação de deploy está no .gitignore
- [ ] Nenhum arquivo de deploy está sendo trackeado
- [ ] README.md não referencia arquivos de deploy
- [ ] Apenas arquivos da aplicação estão no repositório

#### **✅ Após Commitar**
- [ ] Verificar se arquivos sensíveis não foram commitados
- [ ] Confirmar que apenas código da aplicação está no repositório
- [ ] Testar se a aplicação funciona normalmente

---

## 🛡️ **Sistema de Proteção**

### **1. .gitignore Atualizado**
O `.gitignore` deve SEMPRE conter:

```gitignore
# Scripts de deploy e desenvolvimento
security_deploy_script.py
production_security_check.py
update_dependencies.py
deploy_newrelic.py
get_newrelic_info.py
VERSION

# Documentação de deploy
AUTOMATED_MERGE_REQUEST_GUIDE.md
DOCUMENTATION_STANDARDS.md
DOCUMENTATION_GUARANTEES.md
REPOSITORY_CLEANUP_SUMMARY.md
REPOSITORY_RULES.md

# Arquivos sensíveis
.env
newrelic.ini
*.key
*.pem
*.crt

# Desenvolvimento
*.db
__pycache__/
venv/
test_*.py
```

### **2. Validação Automática**
Criar script de validação:

```bash
#!/bin/bash
# validate_repository.sh

echo "🔍 Validando repositório..."

# Verificar arquivos de deploy
DEPLOY_FILES=$(git ls-files | grep -E "(security_deploy_script|production_security_check|update_dependencies)")

if [ ! -z "$DEPLOY_FILES" ]; then
    echo "❌ ERRO: Arquivos de deploy encontrados no repositório:"
    echo "$DEPLOY_FILES"
    echo "Execute: git rm --cached <arquivo>"
    exit 1
fi

# Verificar documentação de deploy
DOC_FILES=$(git ls-files | grep -E "(AUTOMATED_MERGE_REQUEST_GUIDE|DOCUMENTATION_STANDARDS|DOCUMENTATION_GUARANTEES)")

if [ ! -z "$DOC_FILES" ]; then
    echo "❌ ERRO: Documentação de deploy encontrada no repositório:"
    echo "$DOC_FILES"
    echo "Execute: git rm --cached <arquivo>"
    exit 1
fi

echo "✅ Repositório válido!"
```

### **3. Pre-commit Hook**
Criar `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Executar validação
./validate_repository.sh

if [ $? -ne 0 ]; then
    echo "❌ Commit bloqueado - Repositório inválido"
    exit 1
fi

echo "✅ Commit permitido"
```

---

## 📚 **Documentação de Deploy**

### **Arquivos de Deploy (NÃO no repositório)**
- `AUTOMATED_MERGE_REQUEST_GUIDE.md` - Guia de merge requests
- `DOCUMENTATION_STANDARDS.md` - Padrões de documentação
- `DOCUMENTATION_GUARANTEES.md` - Garantias de documentação
- `REPOSITORY_CLEANUP_SUMMARY.md` - Resumo de limpeza
- `REPOSITORY_RULES.md` - Este arquivo

### **Como Usar**
1. **Desenvolvimento**: Arquivos ficam no ambiente local
2. **Deploy**: Scripts executados localmente
3. **Repositório**: Apenas código da aplicação
4. **Produção**: Aplicação deployada sem arquivos de desenvolvimento

---

## 🚨 **Ações Imediatas se Violado**

### **Se Arquivos de Deploy Forem Commitados**
```bash
# 1. Remover do tracking
git rm --cached security_deploy_script.py
git rm --cached production_security_check.py
git rm --cached update_dependencies.py

# 2. Adicionar ao .gitignore
echo "security_deploy_script.py" >> .gitignore
echo "production_security_check.py" >> .gitignore
echo "update_dependencies.py" >> .gitignore

# 3. Commit das correções
git add .gitignore
git commit -m "🔧 Remove arquivos de deploy do repositório"
```

### **Se Documentação de Deploy For Commitada**
```bash
# 1. Remover do tracking
git rm --cached AUTOMATED_MERGE_REQUEST_GUIDE.md
git rm --cached DOCUMENTATION_STANDARDS.md
git rm --cached DOCUMENTATION_GUARANTEES.md

# 2. Adicionar ao .gitignore
echo "AUTOMATED_MERGE_REQUEST_GUIDE.md" >> .gitignore
echo "DOCUMENTATION_STANDARDS.md" >> .gitignore
echo "DOCUMENTATION_GUARANTEES.md" >> .gitignore

# 3. Commit das correções
git add .gitignore
git commit -m "🔧 Remove documentação de deploy do repositório"
```

---

## 📞 **Responsabilidade**

### **Quem Deve Seguir**
- ✅ **Todos os desenvolvedores**
- ✅ **Todos os commits**
- ✅ **Todos os merges**
- ✅ **Todos os deploys**

### **Consequências de Violação**
- ❌ **Commit rejeitado**
- ❌ **Deploy bloqueado**
- ❌ **Repositório inválido**
- ❌ **Segurança comprometida**

---

## 🎯 **Objetivo**

### **Repositório Limpo**
- ✅ Apenas código da aplicação
- ✅ Documentação essencial
- ✅ Configurações seguras
- ✅ Fácil manutenção

### **Deploy Seguro**
- ✅ Scripts isolados
- ✅ Configurações protegidas
- ✅ Processo automatizado
- ✅ Qualidade garantida

---

## 📋 **Resumo das Regras**

### **✅ SEMPRE Incluir**
- Código da aplicação
- README.md e SECURITY.md
- Configurações essenciais
- Documentação do usuário

### **❌ NUNCA Incluir**
- Scripts de deploy
- Documentação de deploy
- Arquivos sensíveis
- Arquivos de desenvolvimento

---

**🚨 IMPORTANTE: Estas regras são OBRIGATÓRIAS e devem ser seguidas SEMPRE!**

*Última atualização: 2025-07-19* 