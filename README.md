# Oracle NBA API - Documentação

## 📋 Resumo

Sistema em tempo real baseado no **prompt principal** (`prompts/ORACLE_PROMPT_PRINCIPAL.txt`) que detecta divergências entre:
- **BLLSport** (transmissão ao vivo) → OCR → placar/tempo
- **Bet365** (via Dolphin/scraping) → placar/linhas
- **NBA oficial** (balldontlie opcional) → validação

JSON rígido **SaaS** é gerado a cada ingestão (150ms) com:
- Diagnóstico (erro/tipo/severidade)
- Comando para executor (não executa macro/clique aqui — apenas recomenda)
- Broadcast WebSocket para 1000+ clientes

---

## 🚀 Instalação & Rodagem

### 1. Dependências

```bash
pip install -r requirements.txt
```

Se usar OCR (pytesseract), instale o Tesseract no Windows:
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Instale em `C:\Program Files\Tesseract-OCR`

### 2. Variáveis de Ambiente

```bash
cp .env.example .env
# Edite .env com suas chaves:
# GEMINI_API_KEY=seu_key_aqui
# BALLDONTLIE_API_KEY=opcional
```

### 3. Rodar o Backend

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Servidor sobe em: `http://127.0.0.1:8000`

---

## 📡 Endpoints

### Status & Debug

#### `GET /api/status`
```json
{
  "status": "ok",
  "timestamp": "2026-02-23T17:05:48-03:00",
  "service": "oracle-nba",
  "prompt": {
    "sha256": "...",
    "chars": 2841,
    "updated_at": "2026-02-23T..."
  }
}
```

#### `GET /api/debug/routes`
Lista todas as rotas carregadas (para diagnóstico).

---

### Oráculo

#### `POST /api/oracle/analyze`
Análise síncrona (sem guardar nem broadcast).

**Request:**
```json
{
  "video_live": {
    "placar": {"Home": 93, "Away": 85},
    "tempo": "Q1 05:03"
  },
  "bet365": {
    "placar_geral": {"Home": 91, "Away": 85},
    "tempo_bet": "Q1 05:03",
    "linhas": ["Q05:03 R$L Mag 2pts 1.40 ✓REGISTROU"]
  },
  "system": {
    "status_stream": "OK",
    "latencia_ms": 1300
  }
}
```

**Response:**
```json
{
  "timestamp": "2026-02-23T17:05:48-03:00",
  "server_metrics": {
    "status_stream": "OK",
    "confianca_ia": 0.97,
    "latencia_processamento_ms": 1300
  },
  "analise_live": {
    "placar_real": {"H": 93, "A": 85},
    "tempo_video": "Q1 05:03",
    "evento": ""
  },
  "diagnostico_saas": {
    "erro_detectado": true,
    "tipo": "LINHA_OK_PLACAR_ATRASADO",
    "detalhes_tecnicos": "Linha confirmada na Bet365 mas placar geral atrasado. Bet=91-85 vs Verdade=93-85.",
    "severidade": "CRITICA"
  },
  "comando_cliente": {
    "executar": false,
    "urgencia": "IMEDIATA",
    "macro_steps": []
  },
  "notificacao_dashboard": "ALERTA: DIVERGENCIA DETECTADA"
}
```

---

#### `POST /api/oracle/ingest` (TEMPO REAL)
Análise + broadcast via WebSocket + salva como `/api/oracle/latest`.

**Request (mesmo que analyze, mas com opção de frame_base64):**
```json
{
  "frame_base64": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "frame_crop": {
    "x": 100,
    "y": 50,
    "w": 400,
    "h": 100
  },
  "bet365": {...},
  "system": {...}
}
```

**Response:** Mesmo que `/api/oracle/analyze` + broadcast automático.

---

#### `GET /api/oracle/latest`
Ultimo JSON de ingestão (útil para clientes que conectam depois).

```json
{
  "status": "ok",
  "timestamp": "2026-02-23T17:05:48-03:00",
  "latest": { /* JSON completo do Oráculo */ }
}
```

---

#### `GET /api/oracle/prompt?include_text=true`
Retorna o prompt principal (com SHA256 para validação).

---

### Visão (OCR - BLLSport)

#### `POST /api/oracle/vision/parse-frame`
OCR isolado do frame (só placar/tempo, sem análise completa).

**Request:**
```json
{
  "frame_base64": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "crop": {
    "x": 100,
    "y": 50,
    "w": 400,
    "h": 100
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-02-23T17:05:48-03:00",
  "placar": {"Home": 93, "Away": 85},
  "tempo_video": "Q1 05:03",
  "raw_text": "93 85 Q1 05:03",
  "error": null
}
```

---

### Oficial (NBA)

#### `GET /api/oracle/nba/balldontlie/game?game_id=1`
Busca score oficial por game_id (opcional, via balldontlie).

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-02-23T17:05:48-03:00",
  "provider": "balldontlie",
  "placar": {"Home": 93, "Away": 85},
  "tempo": null,
  "error": null
}
```

---

### WebSocket (Broadcast Tempo Real)

#### `WS /ws/oracle`
Conecta e recebe JSON do Oráculo em streaming (1000+ clientes suportados).

**Cliente Python:**
```python
import asyncio
import json
import websockets

async def listen():
    async with websockets.connect("ws://127.0.0.1:8000/ws/oracle") as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"Erro: {data['diagnostico_saas']['erro_detectado']}")
            print(f"Tipo: {data['diagnostico_saas']['tipo']}")

asyncio.run(listen())
```

**Cliente JavaScript:**
```javascript
const ws = new WebSocket("ws://127.0.0.1:8000/ws/oracle");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Oráculo:", data);
};
```

---

## 📊 Exemplo Completo (Pipeline)

1. **Captura frame da bllsport → base64**
2. **POST /api/oracle/ingest**
   - OCR extrai placar/tempo
   - Combina com Bet365 + oficial
   - Detecta erro (LINHA_OK_PLACAR_ATRASADO)
   - Broadcast para todos os clientes WebSocket
   - Salva como `latest`
3. **Cliente recebe JSON rígido** (urgencia/tipo/detalhes)
4. **Executor externo** (seu script/macro) consome JSON e toma ação
   - ✅ Pode clicar no Dolphin (recomendação SaaS)
   - ✅ Can place bet via API legítima (se autorizado)
   - ❌ NÃO bypass CAPTCHA/ToS (fora do escopo)

---

## 🔍 Hierarquia de Erros (Prioridade)

| Tipo | Severidade | Descrição |
|------|------------|----|
| LINHA_OK_PLACAR_ATRASADO | CRITICA | Linha confirmada mas placar geral atrasado (seu caso raro!) |
| 3PTS_REGISTRADO_2PTS | ALTA | 3 pontos registrou como 2 |
| LANCE_LIVRE_DELAY | ALTA | Lance livre visível + tempo Bet parado |
| DELAY_GERAL | MEDIA/ALTA | Relogio Bet atrasa >3s |
| TEMPO_DESYNC | MEDIA | Desync entre fontes |
| PLACAR_ATRASADO | MEDIA/ALTA | Placar geral atrasado |
| OK | BAIXA | Sem erro crítico |

---

## 🛠️ Troubleshooting

### OCR retorna erro "Tesseract not found"
Instale: https://github.com/UB-Mannheim/tesseract/wiki

### Port 8000 já em uso
Use outra porta:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

### WebSocket desconecta sozinho
Normal (timeout/keep-alive). Cliente reconecta automaticamente.

### Gemini timeout
Aumentar timeout em `backend/oracle_api.py` ou usar outro modelo.

---

## 📁 Estrutura

```
c:\Users\anton\OneDrive\Desktop\IA Basket\IA-Basket\
├── prompts/
│   └── ORACLE_PROMPT_PRINCIPAL.txt          # Seu prompt (2841 chars)
├── core/
│   ├── oracle_nba.py                        # Detector (regras + JSON)
│   ├── vision_bllsport.py                   # OCR do frame
│   └── nba_official.py                      # Validação oficial
├── backend/
│   ├── main.py                              # Entrypoint
│   ├── oracle_api.py                        # API + WebSocket
│   └── gemini_knowledge.py                  # Gemini integration
├── .env                                      # Variáveis (ignore no git)
├── .env.example                              # Template
├── requirements.txt                          # Deps
└── README.md                                 # Este arquivo
```

---

## 📞 Próximas Etapas

1. **Mande uma print do placar/relógio da bllsport** → Eu ajusto OCR com crop exato
2. **Configure .env** com sua chave Gemini (opcional balldontlie)
3. **Rode o servidor** e teste os endpoints
4. **Conecte seu executor** (script/macro Dolphin) ao `/ws/oracle` ou `/api/oracle/latest`

---

## ⚖️ Aviso Legal

Este sistema detecta divergências e gera recomendações **apenas**. Não executa macro, cliques ou apostas automaticamente. Qualquer ação de aposta deve seguir a lei e ToS da plataforma.

---

**Desenvolvido com base no "Oracle NBA prompt" (Feb 2026)**
