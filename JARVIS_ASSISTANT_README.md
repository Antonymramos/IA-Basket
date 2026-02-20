# JARVIS Desktop Assistant - Guia Completo

Assistente de voz desktop para operação multi-conta do sistema Hoops Jarvis.

---

## 🎯 **Para Que Serve**

O JARVIS Desktop é um copiloto de voz para gerenciar múltiplas contas de apostas simultaneamente:

- **Controle mãos-livres** do sistema enquanto opera várias telas
- **Abertura automática** de múltiplas contas em abas separadas
- **Consultas rápidas** de status, lucro, apostas sem tirar mãos do mouse
- **Automação de setup** para iniciar sessões multi-conta
- **Respostas inteligentes** via GPT-4o-mini para perguntas complexas

---

## 📋 **Instalação Rápida**

### **Opção 1: Script Automático (RECOMENDADO)**

```bash
install_jarvis_assistant.bat
```

### **Opção 2: Manual**

```bash
# 1. Ative o ambiente virtual
.venv\Scripts\activate

# 2. Instale dependências
pip install SpeechRecognition pyttsx3 python-dotenv openai pywhatkit requests

# 3. Instale PyAudio (essencial para microfone)
pip install pipwin
pipwin install pyaudio

# 4. Configure OpenAI (opcional, para respostas inteligentes)
# Edite .env e adicione:
OPENAI_API_KEY=sk-sua-chave-aqui
```

---

## 🚀 **Como Usar**

### **1. Inicie o Sistema Principal**

```bash
python -m uvicorn backend.main:app --reload
```

### **2. Execute o Assistente Desktop**

```bash
python jarvis_assistant.py
```

### **3. Fale "Jarvis" + Comando**

Exemplos:
- **"Jarvis, inicie o bot"**
- **"Jarvis, qual o status do sistema?"**
- **"Jarvis, abra a Bet365 conta 2"** (abre em nova aba)
- **"Jarvis, qual o lucro hoje?"**
- **"Jarvis, abra o painel de controle"**

---

## 📝 **Comandos Disponíveis**

### **Controle do Sistema**
- `"Jarvis, inicie o bot"` → Inicia monitoramento
- `"Jarvis, pare o bot"` → Para análise
- `"Jarvis, ative aposta automática"` → Liga auto-bet
- `"Jarvis, desative aposta automática"` → Desliga auto-bet

### **Consultas e Status**
- `"Jarvis, qual o status?"` → Status running/parado + auto-bet
- `"Jarvis, qual o lucro hoje?"` → Total de apostas + bloqueadas
- `"Jarvis, quantas apostas foram feitas?"` → Contador total

### **Abrir Aplicativos/Sites**
- `"Jarvis, abra o painel"` → Abre localhost:8000
- `"Jarvis, abra a Bet365"` → Abre Bet365 principal
- `"Jarvis, abra a Bet365 conta 2"` → Nova aba Bet365
- `"Jarvis, abra o Chrome"` → Abre navegador
- `"Jarvis, abra o VS Code"` → Abre editor

### **Utilidades**
- `"Jarvis, que horas são?"` → Hora atual
- `"Jarvis, que dia é hoje?"` → Data atual
- `"Jarvis, [qualquer pergunta]"` → Resposta via GPT (se configurado)

### **Encerrar**
- `"Jarvis, desligar assistente"` → Fecha o assistente
- **Ctrl+C** → Fecha via teclado

---

## 🔧 **Configuração da Voz**

### **Voz Masculina PT-BR no Windows**

O sistema busca automaticamente a melhor voz disponível:
1. Voz PT-BR (Daniel, Antonio)
2. Voz masculina em inglês
3. Voz padrão do sistema

### **Ajustar Voz Manualmente**

Ao iniciar, o assistente lista todas as vozes:
```
=== VOZES DISPONÍVEIS ===
0: Microsoft Daniel - Portuguese (Brazil)
1: Microsoft Maria - Portuguese (Brazil)
2: Microsoft David - English (US)
...
```

Edite `jarvis_assistant.py` linha ~35 e force o índice desejado:
```python
self.engine.setProperty('voice', voices[0].id)  # Use o índice da lista
```

### **Parâmetros de Voz**

```python
self.engine.setProperty('rate', 140)    # Velocidade (100-200)
self.engine.setProperty('volume', 0.9)  # Volume (0.0-1.0)
```

---

## ⚙️ **Integração com OpenAI GPT (Opcional)**

Para respostas inteligentes a perguntas complexas:

1. Obtenha API key em: https://platform.openai.com/api-keys
2. Adicione ao arquivo `.env`:
   ```
   OPENAI_API_KEY=sk-proj-...
   ```
3. Reinicie o assistente

**Exemplos com GPT:**
- "Jarvis, explique como funciona o delay learning"
- "Jarvis, qual a melhor estratégia para odds baixas?"
- "Jarvis, por que a última aposta foi bloqueada?"

---

## 🎙️ **Calibração do Microfone**

### **Microfone Não Detecta Comandos**

1. **Windows**: Configurações > Privacidade > Microfone > Permitir apps
2. **Teste de áudio**: `python -m speech_recognition` e fale
3. **Ajuste sensibilidade** no código (`adjust_for_ambient_noise` linha ~55)

### **Muitos Falsos Positivos**

Edite `jarvis_assistant.py` linha ~68:
```python
# Aumenta timeout para evitar ruídos
audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=2)
```

---

## 🌟 **Workflow Multi-Conta Recomendado**

### **Setup de Sessão de 4 Contas**

1. **Inicie o assistente**: `python jarvis_assistant.py`
2. **Configure navegador**:
   - "Jarvis, abra a Bet365" (conta 1)
   - "Jarvis, abra a Bet365 conta 2"
   - "Jarvis, abra a Bet365 conta 3"
   - "Jarvis, abra o painel de controle"
3. **Organize janelas** manualmente em grade
4. **Inicie bot**: "Jarvis, inicie o bot"
5. **Monitore**: Pergunte status sem parar de operar

### **Durante Operação**

- Use assistente para consultas rápidas
- Mantenha mãos livres para apostas manuais rápidas
- Peça para abrir novas abas conforme necessário

---

## 🐛 **Troubleshooting**

### **Erro: "No module named 'pyaudio'"**
```bash
pip install pipwin
pipwin install pyaudio
```

### **Erro: "Could not understand audio"**
- Fale mais próximo do microfone
- Reduza ruído ambiente
- Verifique permissões do microfone no Windows

### **Jarvis não responde a wake word**
- Pronuncie claramente: "**Jár-vis**"
- Aumente volume do microfone
- Reduza `timeout` no código (linha 68)

### **API não conecta**
- Verifique se sistema principal está rodando: `http://localhost:8000`
- Confirme porta 8000 não está bloqueada

---

## 📊 **Próximas Melhorias Planejadas**

- [ ] Comando "organizar janelas em grade N×N"
- [ ] Abertura de múltiplas contas com perfis Chrome nomeados
- [ ] Histórico de conversas persistente
- [ ] Integração com notificações Telegram
- [ ] Comando "rotacionar contas" automático
- [ ] Wake word detection offline (Porcupine/Snowboy)

---

## 🔒 **Segurança**

- **Nunca compartilhe** seu arquivo `.env` (contém API keys)
- **Cuidado** com comandos de "desligar PC" em produção
- **Use perfis diferentes** do Chrome para cada conta Bet365

---

**Última atualização:** 2026-02-19  
**Versão:** 1.0.0  
**Responsável:** Hoops Jarvis Team
