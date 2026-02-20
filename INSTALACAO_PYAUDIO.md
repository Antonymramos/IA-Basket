# JARVIS - Guia de Instalação Completo

## ❌ Problema: PyAudio no Python 3.14

PyAudio requer compilação no Windows e Python 3.14 não tem wheels pré-compilados.

---

## ✅ Soluções Práticas (em ordem de prioridade)

### **OPÇÃO 1: Usar Assistente Web (RECOMENDADO)** ✅

**Já está funcionando!** Comandos por texto + respostas em voz PT-BR.

```bash
# Execute agora:
.venv\Scripts\python.exe jarvis_assistant_web.py

# Comandos disponíveis:
> status
> iniciar
> parar
> lucro
> sair
```

**Vantagens:**
- ✅ Funciona agora sem instalar nada
- ✅ Voz PT-BR funcionando (Maria)
- ✅ Integrado com API do sistema
- ✅ Sem dependências problemáticas

---

### **OPÇÃO 2: Usar Frontend Web com Voz** ✅

O **painel web já tem reconhecimento de voz!**

1. Abra: `http://localhost:8000`
2. Seção "Controles" > "Falar comando"
3. Clique e fale comandos!

**Vantagens:**
- ✅ Wake-free (clique e fale)
- ✅ Integração visual com logs
- ✅ Voz Jarvis já configurada
- ✅ Funciona em qualquer navegador

---

### **OPÇÃO 3: Instalar Visual C++ Build Tools** ⚙️

**Só se REALMENTE quiser wake word "Jarvis" desktop.**

1. Baixe: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Instale "C++ Build Tools" (8GB!)
3. Execute:
   ```bash
   .venv\Scripts\python.exe -m pip install PyAudio
   ```
4. Execute:
   ```bash
   python jarvis_assistant.py
   ```

**Desvantagens:**
- ❌ Download de 8GB
- ❌ Instalação demorada
- ❌ Complexo para manter

---

### **OPÇÃO 4: Downgrade para Python 3.11** 🔄

Python 3.11 tem PyAudio wheel pronto.

1. Desinstale Python 3.14
2. Instale Python 3.11: https://www.python.org/downloads/release/python-3117/
3. Recrie ambiente:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   pip install PyAudio
   ```
4. Execute:
   ```bash
   python jarvis_assistant.py
   ```

**Desvantagens:**
- ❌ Perde benefícios do Python 3.14
- ❌ Precisa reconfigurar tudo

---

## 🎯 Minha Recomendação

**Use OPÇÃO 1 ou OPÇÃO 2** (assistente web ou frontend web).

### Por quê?

1. **Funciona AGORA** sem instalações complexas
2. **Mesmo resultado prático**: controle por voz + feedback sonoro
3. **Visual + Áudio**: melhor que só voz
4. **Mais rápido**: clique → fale vs "Jarvis... [espera] ... comando"
5. **Confiável**: navegador lida com microfone automaticamente

---

## 🚀 Workflow Recomendado Multi-Conta

### Setup:
```
Terminal 1: python -m uvicorn backend.main:app --reload
Terminal 2: .venv\Scripts\python.exe jarvis_assistant_web.py
Navegador:  http://localhost:8000 (painel visual)
```

### Durante Operação:
- **Painel web**: Ver logs, status, iniciar/parar
- **Assistente web terminal**: Consultas rápidas ("status", "lucro")
- **Voz no navegador**: Comandos complexos quando necessário

---

## 📊 Comparação

| Recurso | Desktop PyAudio | Web Terminal | Frontend Web |
|---------|----------------|--------------|--------------|
| Wake word | ✅ "Jarvis" | ❌ | ❌ Clique |
| Instalação | ❌ Complexa | ✅ Pronta | ✅ Pronta |
| Voz resposta | ✅ | ✅ | ✅ |
| Multi-conta | ✅ | ✅ | ✅ |
| Visual | ❌ | ❌ | ✅ Logs/Stats |
| Latência | ~2-4s | <0.1s | ~1s |

---

## ⚡ Quick Start (AGORA)

```bash
# Terminal 1 - Sistema principal
python -m uvicorn backend.main:app --reload

# Terminal 2 - Assistente de voz
.venv\Scripts\python.exe jarvis_assistant_web.py

# Navegador
http://localhost:8000
```

Pronto! Sistema completo funcionando.

---

**Criado:** 2026-02-19  
**Versão:** 2.0 (Web-first approach)
