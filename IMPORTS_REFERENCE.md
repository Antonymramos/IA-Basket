# 🔗 MAPA DE IMPORTS - Como Usar Cada Componente

## Backend (API)

### Rodar o servidor
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### Imports
```python
from backend.oracle_api import app, ws_manager
from backend.gemini_knowledge import enrich_with_gemini

# app é a instância FastAPI
# ws_manager é o gerenciador WebSocket
```

---

## Core (Lógica)

### Oracle Detector
```python
from core.oracle_nba import AnalysisResult, detect_oracle_error

# Detector de erros (6-level hierarchy)
result = detect_oracle_error({
    "placar_real": {"H": 93, "A": 85},
    "placar_bet": {"H": 91, "A": 85},
    "tempo": "Q1 05:03"
})

print(result.tipo)        # e.g., "LINHA_OK_PLACAR_ATRASADO"
print(result.severidade)  # e.g., "CRITICA"
```

### Vision (OCR)
```python
from core.vision_bllsport import analyze_bllsport_frame

# Extrai placar/tempo de screenshot
result = analyze_bllsport_frame(
    frame_base64="data:image/png;base64,...",
    crop={"x": 100, "y": 50, "w": 400, "h": 100}
)

print(result.placar)      # {"Home": 93, "Away": 85}
print(result.tempo_video) # "Q1 05:03"
```

### NBA Official
```python
from core.nba_official import fetch_balldontlie_game

# Busca score oficial
score = await fetch_balldontlie_game(game_id=123)
# {"placar": {"Home": 93, "Away": 85}, "tempo": "5:03"}
```

---

## Integrations (Seu Código)

### Scrapers

#### BLLSport
```python
from integrations.scrapers.bllsport_scraper import BLLSportScraper

scraper = BLLSportScraper()
frame_b64 = await scraper.fetch_frame()    # base64 image
placar = await scraper.get_placar()        # {"home": 93, "away": 85}
```

#### Bet365
```python
from integrations.scrapers.bet365_scraper import Bet365Scraper

scraper = Bet365Scraper()
odds = await scraper.fetch_odds()          # {placar_geral, linhas}
linhas = await scraper.get_linhas_ativas() # [{"time": "Q1 05:03", ...}]
```

#### Flashscore (Fallback)
```python
from integrations.scrapers.flashscore_scraper import FlashscoreScraper

scraper = FlashscoreScraper()
score = await scraper.fetch_score()        # {home, away, tempo}
```

### APIs

#### BallDontLie (já existe)
```python
from core.nba_official import fetch_balldontlie_game

# Use a versão que já existe em core/
score = await fetch_balldontlie_game(game_id=123)
```

#### Gemini (já existe)
```python
from backend.gemini_knowledge import enrich_with_gemini

# Enrich oracle data com Gemini
enriched = await enrich_with_gemini(oracle_data)
```

### Executors

#### Dolphin Bot
```python
from integrations.executors.dolphin_macro import DolphinExecutor

executor = DolphinExecutor()
await executor.connect()
await executor.execute_macro([
    {"action": "click", "x": 500, "y": 300},
    {"action": "type", "text": "100"},
    {"action": "click", "x": 600, "y": 350}
])
```

#### Manual Executor
```python
from integrations.executors.manual_executor import ManualExecutor

executor = ManualExecutor(webhook_url="https://api.telegram.org/...")
await executor.notify_recommendation(oracle_data)
approved = await executor.get_approval(oracle_data)
```

---

## REST API Endpoints

### Status
```
GET /api/status
Response: {"status": "ok", "service": "oracle-nba", "prompt": {...}}
```

### Oracle Analysis
```
POST /api/oracle/analyze
Body: {"video_live": {...}, "bet365": {...}, "system": {...}}
Response: {JSON SaaS com diagnostico}
```

### Ingest (Tempo Real)
```
POST /api/oracle/ingest
Body: {"frame_base64": "...", "frame_crop": {...}, ...}
Response: {JSON SaaS} + Broadcast WebSocket
```

### Vision (OCR Isolado)
```
POST /api/oracle/vision/parse-frame
Body: {"frame_base64": "...", "crop": {...}}
Response: {"placar": {...}, "tempo_video": "...", "raw_text": "..."}
```

### Official Score
```
GET /api/oracle/nba/balldontlie/game?game_id=123
Response: {"placar": {...}, "tempo": "..."}
```

### Latest Result
```
GET /api/oracle/latest
Response: {"latest": {última análise JSON}}
```

### WebSocket
```
WS /ws/oracle
Recebe: JSON SaaS continuamente em tempo real
```

---

## Exemplo Completo: Pipeline

```python
import asyncio
import json
import httpx

async def main():
    # 1. BLLSport captura frame
    from integrations.scrapers.bllsport_scraper import BLLSportScraper
    scraper = BLLSportScraper()
    frame = await scraper.fetch_frame()
    
    # 2. POST para API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:8000/api/oracle/ingest",
            json={
                "frame_base64": frame,
                "frame_crop": {"x": 100, "y": 50, "w": 400, "h": 100},
                "bet365": {
                    "placar_geral": "91-85",
                    "tempo_bet": "Q1 05:03",
                    "linhas": []
                }
            }
        )
        
        # 3. Recebe análise
        result = response.json()
        
        # 4. Toma ação (se necessário)
        if result["diagnostico_saas"]["erro_detectado"]:
            print(f"⚠️ ERRO: {result['diagnostico_saas']['tipo']}")
            print(f"Severidade: {result['diagnostico_saas']['severidade']}")

asyncio.run(main())
```

---

## Testes

### Rodar testes
```bash
python -m pytest tests/
python -m pytest tests/test_oracle_api.py -v
```

### Testar endpoint
```bash
python test_oracle_api.py
```

---

## Estrutura de Pastas Para Imports

```python
# ✅ CORRETO - Imports relativos funcionam
from core.oracle_nba import detect_oracle_error
from integrations.scrapers.bllsport_scraper import BLLSportScraper
from backend.oracle_api import app

# ✅ CORRETO - De dentro da pasta
from . import BLLSportScraper  # em integrations/scrapers/

# ❌ ERRADO - Não use caminhos absolutos
from c:\...\core import ...
```

---

## Checklist: Tudo Pronto?

- [x] Backend rodando em `http://127.0.0.1:8000`
- [x] Docs da API em `http://127.0.0.1:8000/docs`
- [x] Core (oracle_nba, vision_bllsport, nba_official) importável
- [x] Integrations tem templates com `async def` e docstrings
- [x] WebSocket endpoint aberto em `/ws/oracle`
- [ ] BLLSport Scraper implementado
- [ ] Bet365 Scraper implementado
- [ ] Dolphin Executor implementado
- [ ] Manual Executor implementado

---

## 🚀 Quick Reference

```python
# Core
from core.oracle_nba import detect_oracle_error
from core.vision_bllsport import analyze_bllsport_frame
from core.nba_official import fetch_balldontlie_game

# Integrations (Você implementa)
from integrations.scrapers.bllsport_scraper import BLLSportScraper
from integrations.scrapers.bet365_scraper import Bet365Scraper
from integrations.executors.dolphin_macro import DolphinExecutor
from integrations.executors.manual_executor import ManualExecutor

# Backend
from backend.oracle_api import app, ws_manager

# Async
import asyncio
import httpx
import websockets
```

---

**Tudo que você precisa saber pra começar a integrar APIs! 🚀**
