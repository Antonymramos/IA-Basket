# 🚀 GUIA COMPLETO - JARVIS com VOZ PREMIUM

## ✅ CHECKLIST DE INSTALAÇÃO

### **PASSO 1: Instalar Visual C++ Build Tools** ⚙️

1. **Download** (~6GB):
   - Link direto: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Ou busque: "Microsoft C++ Build Tools download"

2. **Instalação** (~15 minutos):
   - Execute o instalador
   - Marque: **"Desktop development with C++"**
   - Clique em "Install"
   - Aguarde conclusão
   - **REINICIE o computador** (importante!)

3. **Verificação**:
   ```bash
   # Após reiniciar, teste:
   .\install_jarvis_premium.bat
   ```

---

### **PASSO 2: Configurar Voz Premium** 🎙️

#### **OPÇÃO A: ElevenLabs (RECOMENDADO - Voz do filme!)** ⭐⭐⭐⭐⭐

**Grátis: 10.000 caracteres/mês**

1. Crie conta: https://elevenlabs.io/sign-up
2. Vá em: Settings > API Keys
3. Copie sua chave
4. Edite `.env` e adicione:
   ```
   ELEVENLABS_API_KEY=sua-chave-aqui
   ```

**Vozes recomendadas:**
- `Adam` (British Male - Jarvis clássico) - ID: `pNInz6obpgDQGcFmaJgB`
- `Antoni` (British Male - Formal) - ID: `ErXwobaYiN019PkySvjV`

Para trocar voz:
```
ELEVENLABS_VOICE_ID=ErXwobaYiN019PkySvjV
```

**Custos:**
- Grátis: 10k chars/mês (~200 frases)
- Starter: $5/mês = 30k chars
- Creator: $22/mês = 100k chars + clone de voz

---

#### **OPÇÃO B: Azure TTS (Excelente qualidade)** ⭐⭐⭐⭐

**Grátis: 500.000 caracteres/mês**

1. Crie conta: https://azure.microsoft.com/free/ (cartão requerido mas não cobra)
2. Portal Azure > Create Resource > "Speech Services"
3. Preencha:
   - Resource name: `jarvis-tts`
   - Region: `East US`
   - Pricing tier: `Free F0`
4. Após criar, vá em "Keys and Endpoint"
5. Copie `KEY 1` e `REGION`
6. Edite `.env`:
   ```
   AZURE_SPEECH_KEY=sua-chave-aqui
   AZURE_SPEECH_REGION=eastus
   ```

**Vozes masculinas graves:**
- `en-US-GuyNeural` (grave americano)
- `en-GB-RyanNeural` (britânico formal)

---

#### **OPÇÃO C: Windows Premium Voices** ⭐⭐⭐

**Grátis - Offline**

1. Windows Settings (Win + I)
2. Time & Language > **Speech**
3. **Manage voices** > Add voices
4. Baixe:
   - **PT-BR**: `Microsoft Daniel` ou `Antonio`
   - **EN-US**: `Microsoft Guy` ou `Mark`
   - **EN-GB**: `George` (britânico)

5. O código já detecta automaticamente!

---

### **PASSO 3: Execute!** 🎬

```bash
# Com Visual C++ Build Tools instalado:
python jarvis_assistant_premium.py
```

**Primeiro uso:**
- Vai listar todas vozes disponíveis
- Seleciona automaticamente a melhor
- Calibra microfone (fique em silêncio 2 segundos)

**Comandos:**
1. Fale: **"Jarvis"**
2. Aguarde: "Sim, senhor"
3. Fale comando:
   - "Iniciar"
   - "Qual o status"
   - "Qual o lucro hoje"
   - "Abra o painel"
   - "Abra a Bet365"
   - "Desligar Jarvis" (para encerrar)

---

## 🎯 COMPARAÇÃO DE VOZES

| Engine | Qualidade | Latência | Custo/mês | Offline |
|--------|-----------|----------|-----------|---------|
| **ElevenLabs** | 🎬 Filme! | ~1s | Grátis* | ❌ |
| **Azure Neural** | 🌟 Excelente | ~0.5s | Grátis** | ❌ |
| **Google WaveNet** | 🌟 Excelente | ~0.7s | $300 crédito | ❌ |
| **Windows Premium** | 🔊 Boa | <0.1s | Grátis | ✅ |
| **Windows Padrão** | 🔉 OK | <0.1s | Grátis | ✅ |

\* 10k chars/mês  
\** 500k chars/mês

---

## 🎙️ VÍDEO DE REFERÊNCIA - VOZ JARVIS MCU

Para comparar, ouça o Jarvis original:
- YouTube: "Jarvis voice compilation"
- Tom: Britânico formal, grave, pausado
- Características: Respeitoso, preciso, eficiente

**Mais próximo:**
1. ElevenLabs - voz "Adam" com stability=0.5
2. Azure - `en-GB-RyanNeural`
3. Windows - voz "George" (se disponível)

---

## ⚡ QUICK START (após Build Tools instalado)

```bash
# 1. Instale tudo automaticamente
.\install_jarvis_premium.bat

# 2. [OPCIONAL] Configure ElevenLabs
# Edite .env e adicione sua API key

# 3. Execute
python jarvis_assistant_premium.py

# 4. Fale
"Jarvis"
[aguarda]
"Qual o status"
```

---

## 🐛 TROUBLESHOOTING

### **Erro: "Microsoft Visual C++ 14.0 required"**
- Instale Visual C++ Build Tools primeiro
- Reinicie o PC
- Execute novamente

### **Voz robótica/ruim no Windows**
- Baixe vozes premium no Windows Settings
- Ou configure ElevenLabs/Azure

### **Microfone não detecta "Jarvis"**
- Fale mais perto do microfone
- Pronuncie claramente: "Jár-vis"
- Aumente volume do microfone em Settings

### **"Não compreendi"**
- Fale pausadamente após "Sim, senhor"
- Aguarde 1 segundo antes de falar
- Reduza ruído ambiente

---

## 📊 CONSUMO ESTIMADO

**Uso moderado (4h/dia operando):**
- ~50 comandos/dia
- ~100 palavras/resposta
- ~5.000 caracteres/dia
- **ElevenLabs grátis:** dura 2 dias
- **Azure grátis:** dura 100+ dias

**Solução:** Sistema usa fallback automático quando quota acaba!

---

## 🔥 DICA PRO

Para máxima qualidade SEM custo:
1. Configure ElevenLabs para comandos importantes
2. Windows para confirmações simples
3. Edite código para escolher engine por tipo de mensagem

---

**Última atualização:** 2026-02-19  
**Versão:** Premium 1.0
