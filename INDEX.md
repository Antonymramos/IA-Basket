# 📖 INDEX - Guia de Navegação

**Bem-vindo ao Oracle NBA!** Aqui está tudo que você precisa saber.

---

## 🚀 COMECE AQUI

### Se você é novo no projeto:
1. 📖 [QUICK_START.md](QUICK_START.md) - **LEIA PRIMEIRO** (5 min)
2. 📐 [ARCHITECTURE.md](ARCHITECTURE.md) - Entenda a estrutura (10 min)
3. 🔗 [INTEGRATIONS_GUIDE.md](INTEGRATIONS_GUIDE.md) - Como integrar APIs (15 min)

### Se você quer ver status:
- ✅ [BACKEND_STATUS.md](BACKEND_STATUS.md) - O que já existe
- 🗑️ [CLEANUP_REPORT.md](CLEANUP_REPORT.md) - O que foi deletado

---

## 📁 ESTRUTURA DO PROJETO

```
IA-Basket/
│
├── 🟢 backend/              (FastAPI - PRONTO)
│   ├── main.py              Entrypoint
│   ├── oracle_api.py        40+ endpoints + WebSocket
│   └── gemini_knowledge.py  Gemini integration
│
├── 🟢 core/                 (Lógica - PRONTO)
│   ├── oracle_nba.py        Detector de erros (6-level)
│   ├── vision_bllsport.py   OCR placar/tempo
│   └── nba_official.py      BallDontLie API
│
├── 🟡 integrations/         (SEU CÓDIGO AQUI)
│   ├── scrapers/            Extrair dados
│   │   ├── bllsport_scraper.py    → BLLSport (Prioridade 🔴)
│   │   ├── bet365_scraper.py      → Bet365 (Prioridade 🟠)
│   │   └── flashscore_scraper.py  → Flashscore (fallback)
│   │
│   ├── apis/                Consumir APIs externas
│   │   ├── balldontlie.py   (JÁ EXISTE)
│   │   ├── gemini.py        (future)
│   │   └── youtube.py       (future)
│   │
│   └── executors/           Executar ações
│       ├── dolphin_macro.py      → Bot clicker (Prioridade 🟡)
│       └── manual_executor.py    → UI manual (Prioridade 🟡)
│
├── 📊 tests/                (Unit tests)
│   └── test_oracle_api.py   (JÁ EXISTE)
│
├── 📝 prompts/              (Contexto Gemini)
│   └── ORACLE_PROMPT_PRINCIPAL.txt
│
└── 💾 data/                 (Cache/DB local)
```

---

## 🎯 PRIORIDADES DE IMPLEMENTAÇÃO

### 🔴 CRÍTICA: BLLSport Scraper
**Arquivo:** `integrations/scrapers/bllsport_scraper.py`

**O que fazer:**
- Implementar `fetch_frame()` → capturar frame de BLLSport
- Implementar `get_placar()` → extrair placar via OCR

**Deps:** Playwright ou Selenium

**Docs:** Ver [QUICK_START.md - #1](QUICK_START.md)

---

### 🟠 ALTA: Bet365 Scraper
**Arquivo:** `integrations/scrapers/bet365_scraper.py`

**O que fazer:**
- Implementar `fetch_odds()` → extrair odds/linhas
- Implementar `get_linhas_ativas()` → linhas registradas

**Deps:** Selenium + CDP

**Docs:** Ver [QUICK_START.md - #2](QUICK_START.md)

---

### 🟡 MÉDIA: Dolphin & Manual Executors
**Arquivos:** 
- `integrations/executors/dolphin_macro.py`
- `integrations/executors/manual_executor.py`

**Docs:** Ver [QUICK_START.md - #3 e #4](QUICK_START.md)

---

## 📚 DOCUMENTAÇÃO DETALHADA

| Documento | Conteúdo | Tempo |
|-----------|----------|-------|
| [README.md](README.md) | Docs principal + exemplos | 15 min |
| [QUICK_START.md](QUICK_START.md) | Como começar (SUPER SIMPLES) | 5 min |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Estrutura técnica completa | 10 min |
| [INTEGRATIONS_GUIDE.md](INTEGRATIONS_GUIDE.md) | Guia detalhado de APIs | 15 min |
| [BACKEND_STATUS.md](BACKEND_STATUS.md) | Status final do backend | 5 min |
| [CLEANUP_REPORT.md](CLEANUP_REPORT.md) | O que foi deletado e por quê | 5 min |
| [INDEX.md](INDEX.md) | Este arquivo (navegação) | 3 min |

---

## 🔧 COMANDOS RÁPIDOS

### Rodar o servidor
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### Acessar docs da API
```
http://127.0.0.1:8000/docs
```

### Testar endpoints
```bash
python test_oracle_api.py
```

### Ativar venv
```bash
.\.venv\Scripts\Activate.ps1
```

---

## 🎮 EXEMPLOS PRÁTICOS

### Exemplo 1: Testar OCR (core/)
```python
from core.vision_bllsport import analyze_bllsport_frame

result = analyze_bllsport_frame(frame_base64="data:image/png;base64,...")
print(f"Placar: {result.placar}")  # {"Home": 93, "Away": 85}
print(f"Tempo: {result.tempo_video}")  # "Q1 05:03"
```

### Exemplo 2: Chamar Oracle API
```bash
curl -X POST http://127.0.0.1:8000/api/oracle/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "frame_base64": "data:image/png;base64,...",
    "bet365": {"placar_geral": "91-85", "tempo_bet": "Q1 05:03"}
  }'
```

### Exemplo 3: Conectar WebSocket
```python
import websockets
import json

async def listen():
    async with websockets.connect("ws://127.0.0.1:8000/ws/oracle") as ws:
        async for msg in ws:
            data = json.loads(msg)
            print(f"Erro: {data['diagnostico_saas']['tipo']}")

asyncio.run(listen())
```

---

## 🔗 FLUXO COMPLETO

```
1️⃣  BLLSport Scraper extraí frame
     ↓
2️⃣  OCR extrai placar/tempo
     ↓
3️⃣  POST /api/oracle/ingest
     ↓
4️⃣  Oracle analyzer detecta erro
     ↓
5️⃣  JSON broadcast via WebSocket
     ↓
6️⃣  Dolphin/Manual executor toma ação
```

---

## ✅ CHECKLIST

### Backend (PRONTO ✅)
- [x] FastAPI + uvicorn
- [x] 40+ endpoints
- [x] WebSocket broadcast
- [x] Error detection (6-level)
- [x] OCR pipeline
- [x] Gemini integration

### Integrations (TODO)
- [ ] BLLSport Scraper (🔴 CRÍTICA)
- [ ] Bet365 Scraper (🟠 ALTA)
- [ ] Dolphin Executor (🟡 MÉDIA)
- [ ] Manual Executor (🟡 MÉDIA)

### Tests & Docs (PRONTO ✅)
- [x] Documentação completa
- [x] Code templates
- [x] API examples

---

## 🆘 SUPORTE

### Dúvidas sobre estrutura?
→ Ver [ARCHITECTURE.md](ARCHITECTURE.md)

### Como começo a implementar?
→ Ver [QUICK_START.md](QUICK_START.md)

### Detalhes técnicos de API?
→ Ver [INTEGRATIONS_GUIDE.md](INTEGRATIONS_GUIDE.md)

### O que mudou?
→ Ver [CLEANUP_REPORT.md](CLEANUP_REPORT.md)

---

## 📞 ENDPOINTS PRINCIPAIS

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/status` | Status do servidor |
| POST | `/api/oracle/analyze` | Análise síncrona |
| POST | `/api/oracle/ingest` | Análise + broadcast |
| GET | `/api/oracle/latest` | Último resultado |
| WS | `/ws/oracle` | WebSocket broadcast |
| POST | `/api/oracle/vision/parse-frame` | OCR isolado |
| GET | `/api/oracle/nba/balldontlie/game` | Score oficial |

**Faz docs: http://127.0.0.1:8000/docs**

---

## 🚀 PRÓXIMA AÇÃO

1. 📖 Leia [QUICK_START.md](QUICK_START.md)
2. 🎯 Escolha: BLLSport ou Bet365 (comece pelo BLLSport!)
3. 💻 Abra o arquivo em `integrations/scrapers/`
4. ✍️ Implemente os `TODO`s
5. ✅ Teste com `python test_oracle_api.py`

---

**Status: 🟢 PRONTO PARA INTEGRAÇÃO**

Projeto limpo, documentado, escalável.
Você está pronto para começar! 🚀
