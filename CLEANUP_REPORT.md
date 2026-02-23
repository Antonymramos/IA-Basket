# ✨ Projeto Limpo - Status Final

## 🗑️ O que foi DELETADO

- ❌ `auto_bootstrap.ps1` (Jarvis legacy)
- ❌ `auto_relogin.ps1` (Jarvis legacy)
- ❌ `start_chrome_cdp.*` (Chrome legacy)
- ❌ COMANDOS_TESTE.md (docs antigo)
- ❌ TESTE_PRE_DEPLOY.md (docs antigo)
- ❌ test_bet365_scraper.py (teste antigo)
- ❌ test_dolphin.py (teste antigo)
- ❌ app.py (API antiga)
- ❌ action_layer/ (Jarvis)
- ❌ data_ingestion/ (pipeline antigo)
- ❌ tools/ (Jarvis)
- ❌ docs/ (docs antigo)
- ❌ vosk-model-small-pt-0.3/ (voice engine)
- ❌ config.json / config.example.json
- ❌ backend/static/ (front-end)
- ❌ backend/dolphin_endpoints.txt (docs antigo)
- ❌ 11 arquivos em core/ (antigos)

**Total: ~50MB limpos ✨**

---

## 📁 O QUE FICOU (Essencial)

### Núcleo (Core)
```
✅ core/
   ├── oracle_nba.py         (Detector de erros - 306 linhas)
   ├── vision_bllsport.py    (OCR - 112 linhas)
   ├── nba_official.py       (BallDontLie - 65 linhas)
   └── __init__.py
```

### Backend (API)
```
✅ backend/
   ├── main.py               (Entrypoint)
   ├── oracle_api.py         (40+ endpoints)
   ├── gemini_knowledge.py   (Gemini integration)
   └── __init__.py
```

### Integrações (TODO - Você implementa)
```
✅ integrations/
   ├── scrapers/
   │   ├── bllsport_scraper.py      (BLLSport → frame/placar)
   │   ├── bet365_scraper.py        (Bet365 → odds/linhas)
   │   ├── flashscore_scraper.py    (Fallback)
   │   └── __init__.py
   ├── apis/
   │   ├── balldontlie.py           (NBA Official ← JÁ EXISTE)
   │   ├── gemini.py                (Google Gemini endpoint)
   │   ├── youtube.py               (YouTube fallback - future)
   │   └── __init__.py
   ├── executors/
   │   ├── dolphin_macro.py         (Dolphin bot - TODO)
   │   ├── manual_executor.py       (Manual UI - TODO)
   │   └── __init__.py
   └── __init__.py
```

### Testes
```
✅ tests/
   ├── test_oracle_api.py    (Já existe)
   └── __init__.py
```

### Docs
```
✅ README.md                 (Principal)
✅ BACKEND_STATUS.md         (Checklist)
✅ ARCHITECTURE.md           (Este projeto - estrutura)
✅ prompts/                  (Contexto Gemini)
✅ data/                     (local DB/cache)
```

---

## 🎯 PRÓXIMAS ETAPAS

### 1. **BLLSport Scraper** (Prioridade 🔴)
📁 `integrations/scrapers/bllsport_scraper.py`

**O que fazer:**
- [ ] Escolher: Playwright vs Selenium vs FFmpeg
- [ ] Capturar screenshot/frame de BLLSport
- [ ] Converter pra base64
- [ ] Enviar para `/backend/oracle_api.py → POST /api/oracle/ingest`

**Dica:** Comece com Playwright (mais fácil)
```bash
pip install playwright
playwright install chromium
```

---

### 2. **Bet365 Scraper** (Prioridade 🟠)
📁 `integrations/scrapers/bet365_scraper.py`

**O que fazer:**
- [ ] Login em Bet365 (pode usar CDP)
- [ ] Navegar pro jogo NBA ativo
- [ ] Extrair odds/linhas da página
- [ ] Enviar para `/backend/oracle_api.py → POST /api/oracle/ingest`

---

### 3. **Dolphin Executor** (Prioridade 🟡)
📁 `integrations/executors/dolphin_macro.py`

**O que fazer:**
- [ ] Instalar Dolphin bot
- [ ] Implementar conexão (TCP/WebSocket)
- [ ] Enviar comandos de clique
- [ ] Chamar via `POST /api/oracle/execute/dolphin`

---

### 4. **Manual Executor** (Prioridade 🟡)
📁 `integrations/executors/manual_executor.py`

**O que fazer:**
- [ ] Notificação (Telegram/Discord/Email)
- [ ] Dashboard com aprovação manual
- [ ] Webhook pra confirmar aposta

---

## 🔗 Como os Pieces se Conectam

```
1️⃣  BLLSportScraper
    ↓ (frame_base64 + placar)
    
2️⃣  POST /api/oracle/ingest
    ↓ (com bet365 data)
    
3️⃣  Oracle Analyzer
    ↓ (detecta erro + recomendação)
    
4️⃣  JSON SaaS + WebSocket Broadcast
    ↓ (para 1000+ clientes)
    
5️⃣  DolphinExecutor OU ManualExecutor
    ↓ (executa ação)
    
6️⃣  Volta pra Bet365 (novo loop)
```

---

## 💡 Estrutura de um Scraper (Exemplo)

```python
# integrations/scrapers/bllsport_scraper.py

from integrations.scrapers import BLLSportScraper
from core.vision_bllsport import analyze_bllsport_frame

async def main():
    scraper = BLLSportScraper()
    
    # Loop contínuo
    while True:
        # 1. Captura frame
        frame_base64 = await scraper.fetch_frame()
        
        # 2. Extrai placar via OCR
        result = analyze_bllsport_frame(frame_base64)
        
        # 3. Envia pra API
        response = await send_to_oracle({
            "frame_base64": frame_base64,
            "frame_crop": {"x": 100, "y": 50, "w": 400, "h": 100}
        })
        
        print(f"Placar: {result.placar}")
        print(f"Tempo: {result.tempo_video}")
        
        await asyncio.sleep(0.3)
```

---

## 📊 Estrutura Final (Limpa)

```
IA-Basket/
├── backend/              ← Coração (API FastAPI)
├── core/                 ← Lógica (OCR + Detection)
├── integrations/         ← APIs/Scrapers (SEU CÓDIGO AQUI ↓)
│   ├── scrapers/         ← BLLSport, Bet365, Flashscore
│   ├── apis/             ← BallDontLie, Gemini, YouTube
│   └── executors/        ← Dolphin, Manual
├── tests/                ← Unit tests
├── prompts/              ← Contexto Gemini
├── data/                 ← Cache/DB local
├── .env                  ← Variáveis (IGNORE no git)
├── .env.example          ← Template
├── README.md             ← Docs
├── ARCHITECTURE.md       ← Este arquivo
├── BACKEND_STATUS.md     ← Checklist
└── requirements.txt      ← Deps
```

---

## ✅ Checklist Setup

- [x] Backend (FastAPI) — **PRONTO**
- [x] Oracle Detector (6-level) — **PRONTO**
- [x] OCR Vision (BLLSport) — **PRONTO**
- [x] WebSocket Broadcast — **PRONTO**
- [x] Estrutura Limpa — **PRONTO**
- [ ] BLLSport Scraper — **TODO**
- [ ] Bet365 Scraper — **TODO**
- [ ] Dolphin Executor — **TODO**
- [ ] Manual Executor — **TODO**

---

## 🚀 Quick Start

```bash
# 1. Ativar venv
cd "c:\Users\anton\OneDrive\Desktop\IA Basket\IA-Basket"
.\.venv\Scripts\Activate.ps1

# 2. Instalar deps (se não tiver)
pip install -r requirements.txt

# 3. Rodar servidor
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 4. Testar API
python test_oracle_api.py

# 5. Acessar docs
# http://127.0.0.1:8000/docs
```

---

**Status: 🟢 PRONTO PARA INTEGRAÇÃO**

Próxima ação: Escolher qual scraper você quer implementar primeiro (BLLSport ou Bet365)?
