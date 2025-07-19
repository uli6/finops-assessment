# 🚀 Instruções para Deploy Manual em Produção

## 📋 **Processo de Deploy**

### **1. Pré-requisitos**
- ✅ Script de segurança executado com sucesso
- ✅ Código enviado para repositório privado: `https://github.com/uli6/finops-assessment-deploy`
- ✅ Acesso ao servidor de produção
- ✅ Credenciais configuradas

### **2. Deploy no Servidor de Produção**

#### **A. Acesse o Servidor**
```bash
ssh usuario@seu-servidor-producao
cd /caminho/para/finops-assessment
```

#### **B. Atualize o Código**
```bash
# Verifique o status atual
git status

# Faça backup do código atual (opcional)
git stash

# Atualize do repositório privado
git pull origin main

# Verifique as mudanças
git log --oneline -5
```

#### **C. Verifique Configurações**
```bash
# Verifique variáveis de ambiente
cat .env

# Execute verificação de segurança
python3 production_security_check.py

# Verifique dependências
python3 update_dependencies.py
```

#### **D. Reinicie a Aplicação**
```bash
# Se usando systemd
sudo systemctl restart finops-assessment

# Se usando supervisor
sudo supervisorctl restart finops-assessment

# Se executando manualmente
pkill -f "python.*app.py"
nohup python3 app.py > app.log 2>&1 &
```

### **3. Verificações Pós-Deploy**

#### **A. Verifique se a Aplicação Está Rodando**
```bash
# Verifique processos
ps aux | grep python

# Verifique logs
tail -f app.log
tail -f security.log

# Teste a aplicação
curl -I http://localhost:5002
```

#### **B. Teste Funcionalidades**
- ✅ Acesse a aplicação no navegador
- ✅ Teste login com magic link
- ✅ Execute uma avaliação de teste
- ✅ Verifique geração de relatórios
- ✅ Teste upload de arquivos

#### **C. Verifique Segurança**
```bash
# Verifique headers de segurança
curl -I -H "Host: seu-dominio.com" http://localhost:5002

# Verifique rate limiting
for i in {1..10}; do curl http://localhost:5002; done

# Verifique logs de segurança
grep "SECURITY_EVENT" security.log
```

### **4. Monitoramento**

#### **A. Logs Importantes**
```bash
# Log da aplicação
tail -f app.log

# Log de segurança
tail -f security.log

# Log do sistema
tail -f /var/log/syslog | grep finops
```

#### **B. Métricas de Performance**
```bash
# Uso de CPU e memória
htop

# Uso de disco
df -h

# Conexões de rede
netstat -tulpn | grep :5002
```

### **5. Rollback (se necessário)**

#### **A. Reverta para Versão Anterior**
```bash
# Liste commits recentes
git log --oneline -10

# Reverta para commit anterior
git reset --hard HEAD~1

# Ou para commit específico
git reset --hard <commit-hash>

# Reinicie aplicação
sudo systemctl restart finops-assessment
```

#### **B. Verifique Rollback**
```bash
# Verifique versão
git log --oneline -1

# Teste aplicação
curl -I http://localhost:5002
```

## 🔒 **Configurações de Segurança**

### **Variáveis de Ambiente de Produção**
```bash
FLASK_ENV=production
AWS_ENV=1
SECRET_KEY=sua-chave-secreta-muito-longa
HOST=127.0.0.1
PORT=5002
```

### **Firewall**
```bash
# Permita apenas porta 5002
sudo ufw allow 5002/tcp

# Bloqueie acesso direto (use proxy reverso)
sudo ufw deny 5002/tcp
```

### **Proxy Reverso (Nginx)**
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📞 **Suporte**

### **Em Caso de Problemas:**
1. Verifique logs: `tail -f app.log security.log`
2. Execute verificação: `python3 production_security_check.py`
3. Verifique status: `sudo systemctl status finops-assessment`
4. Consulte documentação: `PRODUCTION_DEPLOYMENT_GUIDE.md`

### **Contatos:**
- **Email**: security@example.com
- **Documentação**: `README.md`
- **Logs**: `security.log`, `app.log`

---

**Status**: ✅ **Instruções prontas para deploy manual**

**Última atualização**: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """ 