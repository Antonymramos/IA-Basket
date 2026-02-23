# 📚 DOCUMENTAÇÃO ORACLE NBA - INDEX

## Documentos Criados (Consultar quando necessário)

### 🚀 **COMECE_AGORA.md** ← LEIA PRIMEIRO!
**Para:** Entender o próximo passo prático
- Status atual em percentual
- 3 opções (BLLSport / Dolphin / Fallbacks)
- Comandos exatos para começar HOJE
- O que você precisa fornecer

**Quando usar:** Você quer saber "e agora, o que faço?" 

---

### 📋 **ROADMAP_COMPLETO.md**
**Para:** Planejamento completo do projeto (38 horas restantes)
- ✅ O que já está pronto
- ❌ O que falta (com prioridades)
- 📅 Timeline recomendada (5 semanas)
- 🏗️ Estrutura esperada

**Quando usar:** Você quer visão geral de tudo + timing

---

### ✅ **CHECKLIST_PROMPT_COMPLIANCE.md**
**Para:** Mapear seu prompt principal vs código
- Tabela: Requisito Prompt → Arquivo → Status
- JSON de output esperado (conforme seu prompt)
- Fluxo visual do sistema
- Checklist pré-produção

**Quando usar:** "Estou implementando X, por onde começo?"

---

### 🤖 **DOLPHIN_MACRO_GUIDE.md**
**Para:** Implementação profunda do macro Dolphin (o coração)
- Setup Windows Dolphin Anty
- Código completo DolphinAPI + DolphinExecutor
- Handlers para CAPTCHA / bloqueios / fallbacks
- Testes unitários

**Quando usar:** Você está implementando automação de apostas

---

### 📄 **ORACLE_PROMPT_PRINCIPAL.txt** (original)
**Para:** Referência do seu spec original
- 149 linhas com tudo que você quer
- Padrão lucrativo (seu caso real)
- JSON schema rígido
- Regras NBA 100% técnicas

**Quando usar:** Dúvida sobre o que o sistema deve fazer

---

## 📊 Arquivos Existentes (Referência)

### Backend
- `backend/oracle_api.py` - API principal (40+ endpoints)
- `backend/gemini_knowledge.py` - Inteligência Gemini
- `backend/main.py` - Entry point

### Core Oracle
- `core/oracle_nba.py` - Detector de erros 6-level
- `core/vision_bllsport.py` - OCR placar/tempo
- `core/nba_official.py` - Validação balldontlie

### Integrations (70% Templates)
- `integrations/scrapers/bllsport_scraper.py` - 🟥 FAZER (4-6h)
- `integrations/scrapers/bet365_scraper.py` - 🟥 FAZER (8-10h)
- `integrations/scrapers/flashscore_scraper.py` - 🟥 Fallback
- `integrations/executors/dolphin_macro.py` - 🟥 FAZER (20-30h)
- `integrations/executors/manual_executor.py` - 🟥 FAZER (3-4h)

### Testes (Templates)
- `tests/test_scrapers.py` - 🟥 Atualizar
- `tests/test_macro.py` - 🟥 Criar

### Documentação
- `QUICK_START.md` - Setup inicial
- `ARCHITECTURE.md` - Visão geral
- `IMPORTS_REFERENCE.md` - Dependências
- `CLEANUP_REPORT.md` - O que foi removido

---

## 🎯 ROADMAP VISUAL

```
20 DIAS = 100% PRONTO

┌─ BLLSport Scraper (4-6h)          ← Hoje ou amanhã
│  └─ Você manda screenshot
│
├─ Bet365 Scraper (8-10h)           ← Dia 2-3
│  └─ Teste com conta real ($1)
│
├─ Dolphin Macro (20-30h)           ← Dias 3-7
│  ├─ Setup TCP/CDP
│  ├─ Click/type/wait
│  └─ CAPTCHA handlers
│
├─ Fallbacks + YouTube/ESPN (6-8h)  ← Dias 5-6
│  └─ 4 fontes alternativas
│
└─ Métricas + Dashboard (5-8h)      ← Dias 6-7
   └─ EV/hora + hit_rate + streak

─────────────────────────────────────
Total: ~38h de implementação = 5 dias (8h/dia) ou 7 dias (relaxado)
```

---

## 📞 FLUXO DE COMUNICAÇÃO

### Quando você tem uma dúvida:

1. **"Por onde começo?"** → Leia `COMECE_AGORA.md`

2. **"O que preciso implementar?"** → Veja `ROADMAP_COMPLETO.md`

3. **"Estou em [componente], o que fazer?"**
   - BLLSport? → Leia `COMECE_AGORA.md` (Opção 1)
   - Dolphin? → Leia `DOLPHIN_MACRO_GUIDE.md`
   - Compliance? → Leia `CHECKLIST_PROMPT_COMPLIANCE.md`

4. **"O sistema está funcionando?"**
   ```bash
   # Rodar no terminal:
   python -m uvicorn backend.main:app --reload --port 8000
   # Ir para: http://127.0.0.1:8000/docs
   ```

5. **"Preciso do JSON esperado"** → `CHECKLIST_PROMPT_COMPLIANCE.md`

---

## 🚀 PRÓXIMO PASSO

### Você deve fazer UMA destas coisas:

### ✅ A) BLLSport Scraper (RECOMENDADO)
- Abra `COMECE_AGORA.md` seção "OPÇÃO 1"
- Tire screenshot do bllsport
- Implemente `get_live_frame()`
- Me envie screenshot + coordenadas para calibração OCR

### ✅ B) Entender Dolphin
- Abra `DOLPHIN_MACRO_GUIDE.md`
- Instale Dolphin (se não tiver)
- Crie profiles 1 e 2
- Teste conexão TCP

### ✅ C) Setup Fallbacks
- Abra `COMECE_AGORA.md` seção "OPÇÃO 3"
- Implemente YouTube API
- Teste com livestream NBA real

### ✅ D) Estudar Arquitetura
- Leia `CHECKLIST_PROMPT_COMPLIANCE.md`
- Entenda o fluxo de dados
- Compare com seu prompt original

---

## 🔧 COMANDOS RÁPIDOS

```bash
# Setup inicial
cd c:\Users\anton\OneDrive\Desktop\IA\ Basket\IA-Basket
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Rodar backend
python -m uvicorn backend.main:app --reload --port 8000

# Testar um endpoint
curl -X POST http://127.0.0.1:8000/api/oracle/analyze \
  -H "Content-Type: application/json" \
  -d '{"frame_base64":"data:image/png;base64,...", "diagnosticos":[]}'

# Ver documentação interativa
# Ir a: http://127.0.0.1:8000/docs

# Rodar testes
pytest tests/ -v

# Fazer commit
git add -A
git commit -m "feat: implementar bllsport scraper"
git push origin main
```

---

## 📊 PROGRESSO TRACKING

### Backend
- ✅ FastAPI (100%)
- ✅ WebSocket (100%)
- ✅ OCR (100%)
- ✅ Error detection (100%)
- ✅ Gemini (100%)
- ✅ JSON SaaS (100%)

### Scrapers
- 🟥 BLLSport (0% - começar agora)
- 🟥 Bet365 (0%)
- 🟥 YouTube/ESPN (0%)
- 🟥 Flashscore (0%)

### Automation
- 🟥 Dolphin (0% - 20-30h)
- 🟥 Manual executor (0% - 3-4h)

### Infrastructure
- 🟥 Métricas (0% - 5-8h)
- 🟥 Dashboard (0% - 3-4h)
- 🟥 Tests (0% - 4-5h)

---

## 💡 TIPS

1. **Sempre rode backend pronto:** `python -m uvicorn backend.main:app`
2. **Sempre committee:** `git add -A && git commit -m "feat: ..."`
3. **Sempre teste:** `pytest tests/ -v` antes de fazer commit
4. **Sempre abra issues:** Se algo quebrar, use GitHub Issues
5. **Sempre documente:** Add docstrings nos seus scripts

---

## ❓ FAQ RÁPIDO

**P: Por onde começo mesmo?**
R: `COMECE_AGORA.md` + escolher Opção A/B/C/D

**P: Quanto tempo vai levar?**
R: 5-7 dias (8h/dia) para 100% pronto

**P: E se Dolphin não funcionar?**
R: Fallback automático para manual executor (email/Telegram)

**P: O sistema já está testado?**
R: Backend sim (100%). Scrapers não (faltam).

**P: Posso começar com Dolphin?**
R: Pode, mas recomendo BLLSport primeiro (feedback rápido)

**P: Como faço deploy?**
R: Depois que tudo pronto, iremos para Docker + AWS/contrato

**P: E se o OCR não reconhecer?**
R: Fallback para Flashscore API (fallback n°4 do prompt)

---

## 🎯 META FINAL

```
┌─────────────────────────────────────────────────┐
│ Sistema 100% Automático Oracle NBA              │
│                                                  │
│ Input:  bllsport frame + Bet365 odds            │
│ Processo: Detecta LINHA_OK_PLACAR_ATRASADO     │
│ Action: Macro Dolphin clica + coloca aposta     │
│ Output: JSON SaaS + "+R$20 EV" + 94% acurácia   │
│                                                  │
│ 24/7 • Invisível • Windows 11 • -400ms latência │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

**Escolha uma opção de `COMECE_AGORA.md` e comece agora! 🚀**

Qual você quer fazer primeiro?
