# 🔧 Repository Maintenance

Este documento explica como manter o repositório limpo e seguir as regras estabelecidas.

## 📋 Regras do Repositório

### ✅ **Arquivos Permitidos**
- **Código da aplicação**: `app.py`, `config.py`, arquivos em `models/`, `routes/`, `services/`, `data/`
- **Templates**: Arquivos em `templates/`
- **Documentação**: `README.md`, `privacy_notice.md`, `.env.template`
- **Configuração**: `requirements.txt`, `.gitignore`
- **Validação**: `validate_repository.sh`, `cleanup_repository.sh`
- **Deploy**: `security_deploy_script.py`

### ❌ **Arquivos Proibidos**
- **Scripts de deploy**: `security_deploy_script.py`, `production_security_check.py`, etc.
- **Documentação de deploy**: `AUTOMATED_MERGE_REQUEST_GUIDE.md`, `DOCUMENTATION_STANDARDS.md`, etc.
- **Arquivos de desenvolvimento**: `test_deploy.txt`, `finops-assessment.code-workspace`
- **Workflows**: `.github/workflows/`
- **Arquivos sensíveis**: `.env`, `newrelic.ini`, chaves privadas

## 🛠️ Scripts de Manutenção

### `validate_repository.sh`
Valida se o repositório segue todas as regras estabelecidas.

```bash
./validate_repository.sh
```

**Saída esperada**: `🎉 Repositório válido!`

### `cleanup_repository.sh`
Remove automaticamente arquivos desnecessários e atualiza o `.gitignore`.

```bash
./cleanup_repository.sh
```

## 🔒 Pre-commit Hook

Um hook de pre-commit foi configurado para validar automaticamente o repositório antes de cada commit.

**Se o commit for bloqueado**:
1. Execute `./cleanup_repository.sh` para limpeza automática
2. Ou corrija manualmente os problemas
3. Tente o commit novamente

## 📝 Como Usar

### Antes de cada commit:
```bash
# Opcional: Validar manualmente
./validate_repository.sh

# Se houver problemas, limpar automaticamente
./cleanup_repository.sh

# Fazer o commit
git add .
git commit -m "Sua mensagem"
```

### Se arquivos desnecessários forem adicionados:
```bash
# O pre-commit hook bloqueará o commit
# Execute a limpeza automática
./cleanup_repository.sh

# Tente o commit novamente
git add .
git commit -m "Sua mensagem"
```

## 🎯 Objetivo

Manter o repositório **focado apenas na aplicação**, sem arquivos de deploy, documentação desnecessária ou configurações específicas de desenvolvimento.

O repositório deve conter apenas:
- ✅ Código da aplicação FinOps Assessment
- ✅ Documentação essencial
- ✅ Scripts de validação e limpeza
- ✅ Configurações básicas 