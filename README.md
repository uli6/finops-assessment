# 🛡️ FinOps Assessment Platform

Uma plataforma segura e moderna para avaliação de maturidade FinOps, construída com Flask e foco em segurança.

## 🔒 Segurança

### ✅ **Recursos de Segurança Implementados**

- **Rate Limiting**: Proteção contra ataques de força bruta e spam
- **Headers de Segurança**: XSS, clickjacking, MIME sniffing protection
- **Autenticação Segura**: Magic links com expiração e validação
- **Criptografia**: Dependências atualizadas (cryptography >= 44.0.1)
- **Logging de Segurança**: Monitoramento de atividades suspeitas
- **Validação de Entrada**: Sanitização e validação robusta
- **Sessões Seguras**: Cookies HttpOnly, Secure, SameSite
- **Debug Mode Seguro**: Automaticamente desabilitado em produção
- **Binding Seguro**: Localhost apenas em produção

### 🚨 **Aviso de Segurança**

Este é um repositório público (open-source). **NUNCA** commite:
- Chaves de API ou secrets
- Arquivos de configuração com dados sensíveis
- Logs de produção
- Bancos de dados
- Arquivos de ambiente (.env)

## 🚀 Instalação

### Pré-requisitos
- Python 3.9+
- pip
- Git

### Configuração

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/finops-assessment.git
cd finops-assessment
```

2. **Configure o ambiente virtual:**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite .env com suas configurações
```

5. **Configure o New Relic (opcional):**
```bash
cp newrelic.ini.template newrelic.ini
# Edite newrelic.ini com sua license key
```

## 🔧 Desenvolvimento

### Verificação de Segurança
```bash
python production_security_check.py
```

### Atualização de Dependências
```bash
python update_dependencies.py
```

### Executar em Desenvolvimento
```bash
FLASK_ENV=development python app.py
```

## 🚀 Deploy em Produção

### Verificação Pré-Deploy
```bash
# Executar script de segurança e deploy
python security_deploy_script.py
```

### Configuração de Produção
1. Configure as variáveis de ambiente de produção
2. Execute `python production_security_check.py`
3. Siga o guia em `PRODUCTION_DEPLOYMENT_GUIDE.md`

### Docker
```bash
docker build -t finops-assessment .
docker run -p 5002:5002 finops-assessment
```

## 📊 Funcionalidades

- **Avaliação FinOps**: Questionário abrangente de maturidade
- **Benchmarks**: Comparação com dados da indústria
- **Recomendações IA**: Sugestões personalizadas baseadas em IA
- **Relatórios**: Geração de relatórios detalhados
- **Dashboard**: Visualização de progresso e resultados

## 🔧 Tecnologias

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Banco de Dados**: SQLite
- **IA**: OpenAI GPT
- **Segurança**: Flask-Talisman, cryptography
- **Monitoramento**: New Relic

## 📝 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Diretrizes de Contribuição

- ✅ Siga as boas práticas de segurança
- ✅ Execute os testes de segurança antes do commit
- ✅ Mantenha a documentação atualizada
- ✅ Use commits descritivos
- ❌ NUNCA commite dados sensíveis

## 🆘 Suporte

Para problemas de segurança:
1. **NÃO** abra issues públicos com dados sensíveis
2. Entre em contato diretamente com os mantenedores
3. Use o email de segurança: security@example.com

Para outros problemas:
- Abra uma issue no GitHub
- Inclua logs relevantes (sem dados sensíveis)
- Descreva os passos para reproduzir

## 📈 Roadmap

- [ ] Autenticação OAuth2
- [ ] Integração com provedores cloud
- [ ] API REST completa
- [ ] Dashboard avançado
- [ ] Relatórios em tempo real

---

**⚠️ Importante**: Este é um repositório público. Mantenha a segurança em mente ao contribuir.
