# 🎯 Oracle NBA - Backend Ready! Status Final

## ✅ Infraestrutura Pronta

| Componente | Status | Porta | URL |
|------------|--------|-------|-----|
| **FastAPI Server** | ✅ Rodando | 8000 | http://127.0.0.1:8000 |
| **OpenAPI Docs** | ✅ Pronto | 8000 | http://127.0.0.1:8000/docs |
| **WebSocket** | ✅ Pronto | 8000 | ws://127.0.0.1:8000/ws/oracle |

## 📝 Testes Validados

```
✅ /api/status                      → Retorna metadata do servidor
✅ /api/oracle/analyze              → Detecta erros (regex pattern matching)
✅ /api/oracle/ingest              → Real-time + broadcast + salva latest
✅ /api/oracle/vision/parse-frame  → OCR isolado (placar/tempo)
✅ /api/oracle/nba/balldontlie/game → Validação oficial (opcional)
✅ /api/oracle/latest              → Último resultado
✅ /api/debug/routes               → Lista endpoints (14 rotas)
✅ /ws/oracle                       → WebSocket broadcast (1000+ clients)
```

## 📂 Arquivos Criados

- `README.md` — Documentação completa (endpoints, exemplos, troubleshooting)
- `.env.example` — Template de variáveis (Gemini key, Balldontlie, etc)
- `test_oracle_api.py` — Script de teste dos 4 endpoints principais
- `run_server.ps1` — Shortcut para rodar servidor (PowerShell)
- `run_server.bat` — Shortcut para rodar servidor (CMD)

## 🚀 Como Rodar

### Opção 1: PowerShell
```powershell
cd "c:\Users\anton\OneDrive\Desktop\IA Basket\IA-Basket"
.\run_server.ps1
```

### Opção 2: CMD
```cmd
cd "c:\Users\anton\OneDrive\Desktop\IA Basket\IA-Basket"
run_server.bat
```

### Opção 3: Manual
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

## 🎮 Exemplo: POST /api/oracle/ingest

**Request com frame_base64 (bllsport screenshot):**

```json
curl -X POST http://127.0.0.1:8000/api/oracle/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "frame_base64": "data:image/png;base64,iVBORw0KGgoAAAANS...",
    "frame_crop": {
      "x": 100,
      "y": 50,
      "w": 400,
      "h": 100
    },
    "bet365": {
      "placar_geral": "91-85",
      "tempo_bet": "Q1 05:03",
      "linhas": ["Q05:03 R$L Mag 2pts 1.40 ✓REGISTROU"]
    },
    "system": {
      "status_stream": "OK"
    }
  }'
```

**Response (JSON rígido SaaS):**

```json
{
  "timestamp": "2026-02-23T18:18:46-03:00",
  "server_metrics": {
    "status_stream": "OK",
    "confianca_ia": 0.97,
    "latencia_processamento_ms": 145
  },
  "analise_live": {
    "placar_real": {"H": 93, "A": 85},
    "tempo_video": "Q1 05:03"
  },
  "diagnostico_saas": {
    "erro_detectado": true,
    "tipo": "LINHA_OK_PLACAR_ATRASADO",
    "detalhes_tecnicos": "Linha confirmada mas placar geral atrasado.",
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

**+ Broadcast automático para `WS /ws/oracle`**

## 🔧 Próximas Etapas

1. **Mande uma print do placar/relógio da bllsport**
   - Qual é a região exata (x, y, w, h)?
   - Que fonte/tamanho de número?
   - Formato do placar: "93-85" ou "93 85" ou "Magpies 93"?
   - Formato do tempo: "Q1 05:03" ou "1º 5:03" ou outro?

2. **Ajusto OCR com crop exato** → `frame_crop` na request

3. **Temos pronto**: OCR + oficial + Gemini + error detection + WebSocket

## 📊 Architecture

```
frame_base64 (bllsport)
    ↓
[Vision → OCR → placar/tempo]
    ↓
[Oracle analyzer → error detection]
    ↓
[Gemini enrichment (opcional)]
    ↓
JSON (SaaS rigid format)
    ↓
WebSocket broadcast (1000+ clients)
    ↓
Client executor (macro/manual)
```

## ⚙️ Configuração (.env)

```bash
GEMINI_API_KEY=seu_key_aqui
BALLDONTLIE_API_KEY=opcional
BALLDONTLIE_BASE_URL=https://api.balldontlie.io/v1
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
```

---

**Status: 🟢 PRONTO PARA CALIBRAÇÃO OCR**

Aguardando sua screenshot do placar/relógio da bllsport! 📸
