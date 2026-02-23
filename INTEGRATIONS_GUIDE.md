# 🎯 Guia Rápido - Onde Colocar as APIs

## 📍 Mapa de Diretórios

```
integrations/
├── scrapers/          ← EXTRAI dados (BLLSport, Bet365)
├── apis/              ← CONSOME APIs externas (BallDontLie, Gemini)
└── executors/         ← EXECUTA ações (Dolphin, Manual)
```

---

## 🔴 PRIORIDADE 1: BLLSport Scraper

**Arquivo:** `integrations/scrapers/bllsport_scraper.py`

**O que fazer:**
- Capturar frame/screenshot de BLLSport TV
- Extrair placar e tempo via OCR (`core/vision_bllsport.py`)
- Enviar para API

**Exemplo de uso:**
```python
from integrations.scrapers.bllsport_scraper import BLLSportScraper

scraper = BLLSportScraper()
frame = await scraper.fetch_frame()      # base64 image
score = await scraper.get_placar()        # {"home": 93, "away": 85}

# Depois enviar pra API:
response = await httpx.post(
    "http://127.0.0.1:8000/api/oracle/ingest",
    json={
        "frame_base64": frame,
        "frame_crop": {"x": 100, "y": 50, "w": 400, "h": 100}
    }
)
```

**Ferramentas recomendadas:**
- ✅ **Playwright** (melhor - headless browser)
- ⚠️ Selenium (mais lento)
- 🔥 FFmpeg (mais complexo)

---

## 🟠 PRIORIDADE 2: Bet365 Scraper

**Arquivo:** `integrations/scrapers/bet365_scraper.py`

**O que fazer:**
- Login em Bet365
- Navegar pro jogo NBA
- Extrair odds/linhas

**Exemplo:**
```python
from integrations.scrapers.bet365_scraper import Bet365Scraper

scraper = Bet365Scraper()
odds = await scraper.fetch_odds()

# Resultado:
# {
#    "placar_geral": {"home": 91, "away": 85},
#    "tempo_bet": "Q1 05:03",
#    "linhas": [
#        {"time": "Q1 05:03", "line": "+2.5", "odds": 1.40}
#    ]
# }

# Enviar pra API:
response = await httpx.post(
    "http://127.0.0.1:8000/api/oracle/ingest",
    json={"bet365": odds}
)
```

---

## 🟡 PRIORIDADE 3: Dolphin Executor

**Arquivo:** `integrations/executors/dolphin_macro.py`

**O que fazer:**
- Conectar ao Dolphin bot
- Executar cliques/ações recomendadas

**Exemplo:**
```python
from integrations.executors.dolphin_macro import DolphinExecutor

executor = DolphinExecutor()
await executor.connect()

# Executar aposta recomendada
await executor.execute_macro([
    {"action": "click", "x": 500, "y": 300},
    {"action": "type", "text": "100"},
    {"action": "click", "x": 600, "y": 350}
])
```

---

## 🟢 PRIORIDADE 4: Manual Executor

**Arquivo:** `integrations/executors/manual_executor.py`

**O que fazer:**
- Enviar notificação (Telegram/Discord)
- Aguardar aprovação manual

**Exemplo:**
```python
from integrations.executors.manual_executor import ManualExecutor

executor = ManualExecutor(webhook_url="https://api.telegram.org/...")
await executor.notify_recommendation(oracle_data)
```

---

## 🌐 APIs (Já Existe)

### BallDontLie (NBA Official)
**Arquivo:** `integrations/apis/balldontlie.py`

```python
from integrations.apis.balldontlie import fetch_balldontlie_game

score = await fetch_balldontlie_game(game_id=1)
# {"placar": {"home": 93, "away": 85}, "tempo": "5:03"}
```

### Gemini (Enrichment)
**Arquivo:** `backend/gemini_knowledge.py` (já existe, usar como referência)

```python
# Endpoint: POST /api/oracle/gemini-json
response = await httpx.post(
    "http://127.0.0.1:8000/api/oracle/gemini-json",
    json=oracle_data
)
```

---

## 📦 Dependências para Cada Integração

```bash
# BLLSport + Bet365 (Web Scraping)
pip install playwright selenium beautifulsoup4

# Browser automation
playwright install chromium

# APIs
pip install httpx requests

# Database (opcional)
pip install sqlalchemy

# Testing
pip install pytest pytest-asyncio
```

---

## 🔌 Como Conectar Scrapers à API

### Opção 1: Loop Contínuo (Background)
```python
# integrations/scrapers/bllsport_scraper.py

async def continuous_feed():
    scraper = BLLSportScraper()
    while True:
        frame = await scraper.fetch_frame()
        placar = await scraper.get_placar()
        
        # POST para API
        await send_to_oracle({
            "frame_base64": frame,
            "bet365": {  # Pega de outro scraper
                "placar_geral": "91-85"
            }
        })
        
        await asyncio.sleep(0.3)  # 3 FPS
```

### Opção 2: HTTP Webhook
```python
# Em backend/oracle_api.py:

@app.post("/api/integrations/scrapers/feed")
async def receive_scraper_feed(data: dict):
    """Recebe dados de scrapers externos."""
    
    # Processar e analisar
    result = await analyze_oracle(data)
    
    # Broadcast
    await ws_manager.broadcast(json.dumps(result))
    
    return {"status": "ok"}
```

---

## 👀 Exemplo Completo: BLLSport → API → WebSocket → Client

```python
# 1. BLLSPORT SCRAPER (Seu código)
from integrations.scrapers.bllsport_scraper import BLLSportScraper

async def scrape_bllsport():
    scraper = BLLSportScraper()
    while True:
        frame_b64 = await scraper.fetch_frame()
        
        # 2. POST para API
        resp = await httpx.post(
            "http://127.0.0.1:8000/api/oracle/ingest",
            json={
                "frame_base64": frame_b64,
                "frame_crop": {"x": 100, "y": 50, "w": 400, "h": 100},
                "bet365": {  # Você preenche com Bet365Scraper
                    "placar_geral": "91-85",
                    "tempo_bet": "Q1 05:03"
                }
            },
            timeout=5
        )
        
        result = resp.json()
        
        # 3. API faz OCR + atualiza
        # 4. WebSocket notifica clientes
        # 5. Cliente vê em tempo real
        
        await asyncio.sleep(0.3)
```

---

## 🧪 Testando

```bash
# Terminal 1: Rodar servidor
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Rodar seu scraper
python -m integrations.scrapers.bllsport_scraper

# Terminal 3 (Python REPL): Testar endpoint
import requests
resp = requests.post(
    "http://127.0.0.1:8000/api/oracle/ingest",
    json={"frame_base64": "...", "bet365": {...}}
)
print(resp.json())
```

---

## 📋 Checklist

- [ ] Criar `integrations/scrapers/bllsport_scraper.py`
  - [ ] Implementar `fetch_frame()`
  - [ ] Implementar `get_placar()`
  - [ ] Loop contínuo

- [ ] Criar `integrations/scrapers/bet365_scraper.py`
  - [ ] Implementar login
  - [ ] Implementar `fetch_odds()`
  - [ ] Extrair linhas ativas

- [ ] Criar `integrations/executors/dolphin_macro.py`
  - [ ] Conexão ao Dolphin
  - [ ] Execução de cliques

- [ ] Testes em `tests/`

---

**Pronto! Comece pelo BLLSport Scraper (Prioridade 🔴)**
