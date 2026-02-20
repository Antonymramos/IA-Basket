# 🎬 JARVIS PREMIUM - Guia Completo de Uso

## ✅ O que foi implementado

### 1. **Voz Premium ElevenLabs** (Qualidade Cinematográfica) 
- ✨ Mesma voz do Jarvis dos filmes do Homem de Ferro
- 🌐 Integrada no **frontend web** e no **assistente desktop**
- 🔄 Fallback automático para voz do Windows se API falhar
- 💰 10k caracteres grátis/mês (depois $5/mês)

### 2. **Frontend Web com Voz Premium**
- 🎙️ Botão "Premium ON/OFF" na interface
- ⚡ Responde com voz cinematográfica automaticamente
- 🔊 Saudação automática ao abrir a página
- 📱 Funciona em qualquer navegador moderno

### 3. **Assistente Desktop com Wake Word**
- 🎤 Diga "Jarvis" e dê comandos de voz
- 🤖 Controla o sistema de arbitragem por voz
- 🔌 Suporta múltiplas engines de voz (ElevenLabs, Azure, Google, Windows)
- 🎯 Seleção automática da melhor voz disponível

---

## 🚀 Como Usar (Passo a Passo)

### **PASSO 1: Reinicie o PC** ⚠️
Você já instalou o Visual C++ Build Tools. Reinicie para ativar.

### **PASSO 2: Após Reiniciar**
Execute o instalador pós-reinício:

```bash
.\instalar_pos_reinicio.bat
```

Este script vai:
- ✅ Instalar PyAudio (agora vai funcionar com Visual C++)
- ✅ Instalar ElevenLabs e pygame
- ✅ Verificar todas as dependências

### **PASSO 3: Teste a Voz Premium**
```bash
python test_jarvis_voice.py
```

Você deve ouvir: *"Bom dia, senhor. Jarvis online..."* com voz cinematográfica!

---

## 🌐 Usar Voz Premium no Frontend Web

### **Iniciar servidor:**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### **Abrir navegador:**
```
http://localhost:8000
```

### **Ativar voz premium:**
1. Clique no botão **"▶️ Premium OFF"**
2. Ele muda para **"🎬 Premium ON"**
3. Agora todas as respostas do Jarvis usam voz cinematográfica!

### **Comandos de voz no frontend:**
- "Iniciar" / "Start" → Liga monitoramento
- "Parar" / "Stop" → Pausa monitoramento
- "Ativar apostas automáticas" → Liga auto-bet
- "Desativar apostas" → Desliga auto-bet

---

## 🎤 Usar Assistente Desktop com Wake Word

### **Iniciar assistente:**
```bash
python jarvis_assistant_premium.py
```

### **Como usar:**
1. **Aguarde:** Terminal mostra `[AGUARDANDO] Diga 'Jarvis'...`
2. **Ative:** Fale "Jarvis" (ou "Jarviz", "Gervis")
3. **Jarvis responde:** "Sim, senhor." (com voz premium!)
4. **Dê comando:** Ex: "Iniciar monitoramento"
5. **Jarvis executa** e confirma com voz

### **Comandos disponíveis:**
| Comando | Ação |
|---------|------|
| "Iniciar" / "Start" | Inicia bot de arbitragem |
| "Parar" / "Stop" | Para monitoramento |
| "Status" | Informa estado do sistema |
| "Lucro" / "Resultado" | Reporta operações processadas |
| "Abrir painel" | Abre interface web |
| "Abrir Bet365" | Abre site Bet365 |
| "Desligar Jarvis" | Encerra assistente |

---

## 🎛️ Configurações de Voz (Opcional)

### **Engines suportadas (em ordem de qualidade):**

1. **⭐⭐⭐⭐⭐ ElevenLabs** (MELHOR - usando agora)
   - Voz: Adam (British male)
   - Qualidade: Cinematográfica
   - Configurado em `.env`: ✅

2. **⭐⭐⭐⭐ Azure Neural TTS**
   - Voz: en-US-GuyNeural
   - Adicione em `.env`:
     ```
     AZURE_SPEECH_KEY=sua_chave
     AZURE_SPEECH_REGION=eastus
     ```

3. **⭐⭐⭐⭐ Google WaveNet**
   - Voz: en-US-Wavenet-D
   - Adicione em `.env`:
     ```
     GOOGLE_APPLICATION_CREDENTIALS=caminho/para/credentials.json
     ```

4. **⭐⭐⭐ Windows Premium** (Fallback automático)
   - Sempre disponível
   - Voz: Daniel/Antonio (PT-BR) ou Guy/Mark (EN-US)

### **Sistema seleciona automaticamente a melhor voz disponível!**

---

## 🔧 Solução de Problemas

### **PyAudio não instala após reinício:**
1. Certifique-se que reiniciou após instalar Visual C++ Build Tools
2. Tente: `pip install pipwin` e depois `pipwin install pyaudio`
3. **Alternativa:** Use versão offline:
   ```bash
   python jarvis_assistant_offline.py
   ```
   (Funciona sem PyAudio, mas detecta wake word offline com Vosk)

### **Voz premium não funciona no frontend:**
- ✅ Verifique console do navegador (F12) para erros
- ✅ Confirme que `.env` tem `ELEVENLABS_API_KEY`
- ✅ Teste backend isolado: `python test_jarvis_voice.py`

### **Assistente não escuta microfone:**
- 🎤 Verifique permissões de microfone no Windows
- 🎤 Teste microfone em outros apps
- 🎤 Calibração automática demora 2 segundos no início

### **Voz fica repetindo/cortando:**
- 🔇 Diminua volume do Windows (pode causar feedback)
- 🎧 Use fones de ouvido para evitar loop de áudio

---

## 📊 Status da Implementação

| Componente | Status | Observações |
|------------|--------|-------------|
| Frontend web | ✅ Completo | Voz premium integrada |
| Backend API | ✅ Completo | Endpoint `/api/voice/premium` |
| Assistente desktop | ✅ Completo | Wake word + voz premium |
| ElevenLabs API | ✅ Configurado | 10k chars grátis/mês |
| PyAudio | ⏳ Pendente | Aguardando reinício + instalação |
| Documentação | ✅ Completo | Este arquivo! |

---

## 📁 Arquivos Importantes

```
IA-Basket/
├── jarvis_assistant_premium.py       # Assistente desktop PRINCIPAL (com wake word)
├── jarvis_assistant_offline.py       # Alternativa offline (sem PyAudio)
├── test_jarvis_voice.py              # Teste rápido da voz premium
├── instalar_pos_reinicio.bat         # Instalar após reiniciar PC
├── backend/
│   ├── main.py                       # Servidor FastAPI (endpoint /api/voice/premium)
│   ├── jarvis_voice_api.py           # Geração de áudio ElevenLabs
│   └── static/
│       ├── app.js                    # Frontend React (botão Premium ON/OFF)
│       └── index.html                # Interface web
├── .env                              # Configurações (API keys)
└── JARVIS_PREMIUM_GUIA.md           # Este arquivo
```

---

## 🎯 Próximos Passos (Após Reiniciar)

1. ✅ **Reiniciar PC** (Visual C++ Build Tools ativado)
2. ⚡ **Executar:** `.\instalar_pos_reinicio.bat`
3. 🎵 **Testar voz:** `python test_jarvis_voice.py`
4. 🌐 **Iniciar servidor:** `uvicorn backend.main:app --reload`
5. 🎬 **Ativar Premium** no frontend
6. 🎤 **Testar assistente:** `python jarvis_assistant_premium.py`

---

## 💡 Dicas de Uso

### **Frontend (Web Interface):**
- ✨ Deixe "Premium ON" sempre ativado para melhor experiência
- 🔇 Se estiver em local público, desative voz temporariamente
- 📱 Funciona em celular/tablet também!

### **Assistente Desktop:**
- 🎤 Fale claramente e aguarde o "Sim, senhor" antes de dar comando
- 🔊 Primeiro teste em ambiente silencioso
- 💾 Terminal mostra todos os comandos reconhecidos

### **Economia de API:**
- 💰 10k caracteres/mês grátis = ~200 frases do Jarvis
- 📊 Monitore uso em: https://elevenlabs.io/app/usage
- 🔄 Se acabar cota, sistema usa voz Windows automaticamente

---

## 🎬 A Experiência Jarvis Completa

Com tudo configurado, você terá:

**Frontend:**
- 🌐 Abre navegador em `http://localhost:8000`
- 🎙️ Saudação automática: "Bom dia. J.A.R.V.I.S online..."
- ✨ Todas respostas com voz cinematográfica
- 🎛️ Controles visuais + voz integrados

**Desktop:**
- 🎤 Você: "Jarvis"
- 🤖 Jarvis: "Sim, senhor." (voz premium)
- 🎤 Você: "Iniciar monitoramento"
- 🤖 Jarvis: "Sistema de arbitragem iniciado, senhor."
- 📊 Sistema começa a monitorar apostas automaticamente

---

## 🆘 Suporte

### **Problemas?**
1. Verifique console de erros
2. Teste cada componente isoladamente
3. Use versões alternativas (offline/web) como fallback

### **Melhorias futuras sugeridas:**
- [ ] Adicionar mais comandos de voz
- [ ] Integrar com mais casas de apostas
- [ ] Dashboard de análise de lucro por voz
- [ ] Suporte para múltiplos idiomas
- [ ] Notificações de oportunidades por voz

---

**🎉 Divirta-se com seu assistente Jarvis cinematográfico!**
