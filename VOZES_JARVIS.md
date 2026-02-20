# JARVIS - Guia de Vozes Premium

## 🎯 Opções de Voz (da melhor para mais básica)

### **OPÇÃO 1: ElevenLabs (MELHOR QUALIDADE - Voz do filme!)** ⭐⭐⭐⭐⭐

**Voz IGUAL ao Jarvis do filme Iron Man.**

**Configuração:**
1. Crie conta gratuita: https://elevenlabs.io/
2. Pegue sua API key no dashboard
3. Adicione ao `.env`:
   ```
   ELEVENLABS_API_KEY=sua-chave-aqui
   ```
4. Use voz pré-configurada "British Male - Professional"

**Custo:**
- Grátis: 10.000 caracteres/mês (~20 min de fala)
- Pago: $5/mês para 30.000 caracteres

**Qualidade:** 🎬 **Igual ao filme!**

---

### **OPÇÃO 2: Azure TTS (EXCELENTE - Vozes Microsoft Premium)** ⭐⭐⭐⭐

**Vozes neurais premium da Microsoft.**

**Configuração:**
1. Conta Azure (grátis): https://azure.microsoft.com/free/
2. Crie recurso "Speech Service"
3. Adicione ao `.env`:
   ```
   AZURE_SPEECH_KEY=sua-chave
   AZURE_SPEECH_REGION=eastus
   ```
4. Use voz: `en-US-GuyNeural` (grave masculina)

**Custo:**
- Grátis: 500.000 caracteres/mês
- Pago: $1 por milhão de caracteres

**Qualidade:** 🎙️ **Muito natural!**

---

### **OPÇÃO 3: Google Cloud TTS (ÓTIMA)** ⭐⭐⭐⭐

**Vozes WaveNet do Google.**

**Configuração:**
1. Conta Google Cloud: https://cloud.google.com/text-to-speech
2. Ative API Text-to-Speech
3. Baixe JSON de credenciais
4. Configure:
   ```bash
   set GOOGLE_APPLICATION_CREDENTIALS=caminho\para\credenciais.json
   ```
5. Use voz: `en-US-Wavenet-D` (masculina grave)

**Custo:**
- Grátis: $300 crédito inicial
- Pago: ~$4 por milhão de caracteres

**Qualidade:** 🌟 **Natural++**

---

### **OPÇÃO 4: Vozes Premium Windows (MELHOR OFFLINE)** ⭐⭐⭐

**Vozes nativas do Windows 11.**

**Instalação:**
1. Windows Settings > Time & Language > Speech
2. Add voices > Baixe:
   - **PT-BR**: `Daniel` ou `Antonio` (masculinas)
   - **EN-US**: `Guy` ou `Mark` (graves)
3. Ajuste código para usar a nova voz

**Custo:** Grátis ✅

**Qualidade:** 🔊 **Boa para uso offline**

---

### **OPÇÃO 5: Coqui TTS (Clone de Voz Local)** ⭐⭐⭐

**Clone a voz EXATA do Jarvis com amostra de áudio.**

**Como:**
1. Baixe clipe de áudio do Jarvis (YouTube)
2. Use Coqui TTS para clonar
3. Roda localmente (sem custos)

**Complexidade:** Alta (requer GPU idealmente)

---

## 🚀 RECOMENDAÇÃO

Para **operação profissional** de arbitragem:

**Use ElevenLabs** (opção 1):
- Voz PERFEITA sem esforço
- 10k caracteres = ~200 frases/dia (suficiente)
- Se passar do limite, volta para Windows automaticamente

**Fallback:** Azure TTS (500k grátis/mês)

---

## ⚙️ Como Configurar

Criei versão DEFINITIVA que suporta TODAS as opções acima com fallback automático:

Execute após instalar Visual C++ Build Tools:
```bash
python jarvis_assistant_premium.py
```

Ordem de prioridade automática:
1. ElevenLabs (se API key existe)
2. Azure TTS (se configurado)
3. Google Cloud TTS (se configurado)
4. Windows Premium (se instalada)
5. Windows padrão (fallback final)

---

**Próximo passo:** Vou criar o código agora!
