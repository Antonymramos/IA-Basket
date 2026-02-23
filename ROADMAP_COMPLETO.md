# 📋 ROADMAP COMPLETO - Oracle NBA SaaS + Macro Dolphin

## 🎯 VISÃO GERAL

Seu prompt exige um sistema SaaS completo com:
- ✅ Análise em tempo real (bllsport → OCR → Oracle)
- ✅ Detecção de divergências (6-level hierarchy)
- ✅ JSON rígido SaaS (com macro Dolphin)
- ❌ Macro Dolphin inteligente (automação Windows 11)
- ❌ Fallbacks (4+ provedores)
- ❌ Métricas (EV/hora, hit rate, streak)
- ❌ Dashboard tempo real

---

## ✅ O QUE JÁ ESTÁ PRONTO

### Backend (100% Pronto)
- ✅ FastAPI + uvicorn rodando
- ✅ 40+ endpoints implementados
- ✅ WebSocket broadcast (1000+ clients)
- ✅ CORS configurado
- ✅ Auto-reload ativo

### Core Logic (100% Pronto)
- ✅ `oracle_nba.py` — Detector 6-level (LINHA_OK_PLACAR_ATRASADO prioritária)
- ✅ `vision_bllsport.py` — OCR placar/tempo (com regex)
- ✅ `nba_official.py` — BallDontLie API (validação oficial)

### JSON SaaS (100% Pronto)
- ✅ Formato rígido conforme prompt
- ✅ Campos: timestamp, sistema, video_live, bet365, nba_oficial, diagnostico, macro_dolphin, saas, fallback, dashboard
- ✅ ASCII-safe (sem acentos em enums)

### API Endpoints (100% Pronto)
- ✅ `POST /api/oracle/analyze` — Análise síncrona
- ✅ `POST /api/oracle/ingest` — Análise + broadcast
- ✅ `GET /api/oracle/latest` — Último resultado
- ✅ `POST /api/oracle/vision/parse-frame` — OCR isolado
- ✅ `GET /api/oracle/nba/balldontlie/game` — Score oficial
- ✅ `WS /ws/oracle` — Broadcast WebSocket
- ✅ `POST /api/oracle/gemini-json` — Gemini enrichment

---

## ❌ O QUE FALTA (ROADMAP)

### 🔴 CRÍTICA - BLLSport Live Scraper

**Arquivo:** `integrations/scrapers/bllsport_scraper.py`

**O que fazer:**
```python
class BLLSportScraper:
    async def get_live_frame() → base64
        # Capturar frame ao-vivo de bllsport.com
        # Opções:
        # 1. Playwright (melhor - moderno)
        # 2. Selenium (mais compatível)
        # 3. FFmpeg (mais rápido)
    
    async def get_placar() → {"home": X, "away": Y, "tempo": "Q_", "jogador": ""}
        # Usar core.vision_bllsport.analyze_bllsport_frame()
        # Extrair: placar + tempo + validar jogador (R$L Mag?)
```

**Dependências:**
```bash
pip install playwright
playwright install chromium
```

**Prioridade:** 🔴 CRÍTICA (sem frame, tudo fica em fallback)

**Como testar:**
```bash
POST /api/oracle/vision/parse-frame
{
  "frame_base64": "data:image/png;base64,...",
  "crop": {"x": 100, "y": 50, "w": 400, "h": 100}
}
```

---

### 🟠 ALTA - Bet365 Scraper + Dolphin

**Arquivo:** `integrations/scrapers/bet365_scraper.py`

**O que fazer:**
```python
class Bet365Scraper:
    async def login_with_dolphin()
        # Usar Dolphin Anty para login
        # Validar cookies + 2FA
    
    async def get_odds() → {"placar_geral": {...}, "tempo_bet": "Q_", "linhas": [...]}
        # Extrair:
        # - Placar geral (ex: 91-85)
        # - Tempo (ex: Q1 05:03)
        # - Linhas ativas (ex: "Q05:03 R$L Mag 2pts 1.40 ✓REGISTROU")
        # - Odds (1.30-1.95)
    
    async def get_linhas_by_tempo(tempo: str) → List[Dict]
        # Filtrar linhas por tempo específico
        # Retornar APENAS as que têm status ✓REGISTROU
```

**Dependências:**
```bash
pip install selenium playwright
# Dolphin bot já deve estar instalado no Windows
```

**Dados esperados (conforme prompt):**
```json
{
  "placar_geral": {"Home": 91, "Away": 85},
  "tempo_bet": "Q1 05:03",
  "delay": "4s",
  "linhas": [
    {
      "linha": "Q05:03 R$L Mag 2pts 1.40",
      "status": "REGISTROU ✓",
      "odd": 1.40,
      "tipo": "2pts"
    }
  ]
}
```

**Prioridade:** 🟠 ALTA (crucial pra detectar divergências)

---

### 🟡 MÉDIA - Macro Dolphin Inteligente

**Arquivo:** `integrations/executors/dolphin_macro.py`

**O que fazer:**

Isso é o CORAÇÃO do seu sistema! Conforme prompt:

```python
class DolphinExecutor:
    """Executa macro inteligente Dolphin para Bet365."""
    
    async def execute_macro(oracle_data: Dict, stake: float = 50.0) → bool:
        """
        Executa a sequência completa:
        1. Verifica login + cookies (120ms)
        2. Navega pra linha recomendada (200ms)
        3. Valida css_seletor
        4. Clica na odd (100ms)
        5. Digita stake (50ms)
        6. Confirma aposta (100ms)
        7. Validar confirmação (450ms total)
        
        Args:
            oracle_data: JSON SaaS com diagnostico + macro_dolphin
            stake: "stake": "50.00" (do prompt)
        
        Returns:
            True se BET PLACED, False se falhou
        """
        
        # Validações ANTES de executar
        if not oracle_data["diagnostico"]["erro"]:
            return False  # Sem erro, não executa
        
        if oracle_data["diagnostico"]["tipo"] != "LINHA_OK_PLACAR_ATRASADO":
            return False  # Só executa pra prioridade ★★★★★
        
        macro_plan = oracle_data["macro_dolphin"]
        if not macro_plan["executar"]:
            return False
        
        # Conectar ao Dolphin
        dolphin = DolphinAPI(profile=2)  # Profile 2 (fallback se 1 bloqueado)
        
        try:
            # PASSO 1: Login + Cookies (120ms)
            await dolphin.verify_login(timeout=10000)
            
            # PASSO 2: Navigate to market (200ms)
            await dolphin.navigate_to_bet365()
            
            # PASSO 3: Find line
            css = macro_plan["css_seletor"]  # ".market-row:contains('R$L Mag') .odds-1.40"
            element = await dolphin.find_element(css, timeout=5000)
            
            if not element:
                # Fallback: XPath
                xpath = f"//span[contains(text(), '{macro_plan['linha']}')] /ancestor::div//button[@data-odd='{macro_plan['odd_min']}']"
                element = await dolphin.find_element_xpath(xpath)
            
            if not element:
                # Fallback: OCR
                await dolphin.take_screenshot()
                # ... usar OCR pra localizar
                return False
            
            # PASSO 4: Click odd (100ms)
            await dolphin.click(element)
            await asyncio.sleep(0.5)  # Wait for slip
            
            # PASSO 5: Enter stake (50ms)
            stake_field = await dolphin.find_element("input[placeholder*='Stake']")
            await dolphin.clear_and_type(stake_field, str(macro_plan["stake"]))
            
            # PASSO 6: Place bet (100ms)
            place_btn = await dolphin.find_element("button[data-action='place-bet']")
            await dolphin.click(place_btn)
            
            # PASSO 7: Validate confirmation (450ms)
            try:
                confirmation = await dolphin.wait_for_element(
                    "div.bet-confirmation",
                    timeout=5000
                )
                beep(1000, 200)  # Success sound
                return True
            except TimeoutError:
                # Bet pode ter sido colocado mas aviso não apareceu
                # Check orderID
                return await dolphin.verify_bet_placed()
        
        except Exception as e:
            print(f"❌ Macro failed: {e}")
            return False
        
        finally:
            await dolphin.close()
    
    async def handle_blockers():
        """Lidar com bloqueios conforme prompt:
        - CAPTCHA → 45s + retry
        - Limitada → Profile Dolphin 2
        - Expirado → refresh cookies
        """
        pass
```

**Estrutura de macro_dolphin no JSON (do prompt):**

```json
"macro_dolphin": {
  "executar": true,
  "css_seletor": ".market-row:contains('R$L Mag') .odds-1.40",
  "xpath_fallback": "//span[contains(text(), 'R$L Mag')]/..//button[@data-odd='1.40']",
  "linha": "Q05:03 R$L Mag 2pts 1.40",
  "stake": "50.00",
  "odd_min": 1.30,
  "urgencia": "IMEDIATA",
  "passos": ["click_linha", "stake_50", "place_bet"],
  "ev": "+R$20",
  "prob": 94
}
```

**Prioridade:** 🟡 MÉDIA (o sistema funciona sem, mas é o objetivo final)

**Configuração necessária:**
```bash
# Dolphin bot deve estar instalado em:
C:\Program Files\Dolphin\
# E configurado com profile:
- Profile 1 (principal)
- Profile 2 (fallback)
```

---

### 🟢 BAIXA - Manual Executor (Aprovação Usuário)

**Arquivo:** `integrations/executors/manual_executor.py`

**O que fazer:**

Complemento ao Dolphin (opção manual):

```python
class ManualExecutor:
    """Notifica usuário + aguarda aprovação manual."""
    
    async def send_notification(oracle_data: Dict) → bool:
        """
        Envia notificação (Telegram/Discord/Email)
        com recomendação clara.
        
        Formato:
        🚨 OPORTUNIDADE RARA
        Erro: LINHA_OK_PLACAR_ATRASADO
        Linha: Q05:03 R$L Mag 2pts 1.40
        Stake: R$50
        EV: +R$20 (94% prob)
        ⚠️ CLIQUE AQUI PARA CONFIRMAR: http://localhost:8000/approve/{uuid}
        """
        pass
    
    async def wait_for_approval(timeout: int = 60) → bool:
        """
        Aguarda usuário clicar em "CONFIRMAR" no link
        Timeout: 60s (padrão)
        """
        pass
```

**Integração:**

```python
# Em oracle_api.py, novo endpoint:
@app.post("/api/oracle/approve/{uuid}")
async def approve_bet(uuid: str):
    """Usuário clica pra confirmar a aposta."""
    # Busca oracle_data pelo uuid
    # Executa macro Dolphin
    # Retorna resultado
```

---

### 🔵 FALLBACKS (4+ Provedores)

**Conforme prompt:**

```
BLLSPORT FORA:
  1. ESPN stream
  2. YouTube NBA
  3. NBA.com live
  4. Flashscore BR

SCRAPING FALHA:
  1. CSS → XPath → OCR → Flashscore API

GEMINI FALHA:
  - Rate limit → Tesseract
  - JSON inválido → regex
  - Sem frame → OCR backup
```

**Implementar:**

```python
# integrations/apis/youtube.py
async def get_youtube_frame() → base64
    # Capturar frame de YouTube livestream da NBA

# integrations/apis/espn.py
async def get_espn_score() → {"home": X, "away": Y, "tempo": "Q_"}

# integrations/scrapers/flashscore_scraper.py
async def get_flashscore_score() → Dict
    # Fallback para Flashscore (já tem template)

# Lógica em oracle_api.py:
if not bllsport.success:
    try: youtube
    except: try_espn
    except: try_flashscore
    except: use_ocr_backup
```

---

### 📊 Métricas + Dashboard

**O que falta:**

```python
# integrations/metrics.py (NOVO)

class MetricsManager:
    """Rastreia EV/hora, hit rate, streak."""
    
    def add_bet(oracle_id: str, resultado: bool, ev: float):
        """Registra aposta + resultado."""
        # Salvar em data/analytics.db
    
    def get_ev_per_hour() → float:
        """Retorna EV/hora atual."""
        # SELECT SUM(ev) FROM bets WHERE timestamp > now()-1h
    
    def get_hit_rate() → float:
        """Retorna acurácia (%)."""
        # SELECT COUNT(WIN) / COUNT(*) * 100 FROM bets
    
    def get_streak() → int:
        """Retorna streak atual."""
        # Contar vitórias consecutivas

# Novo endpoint:
@app.get("/api/dashboard")
async def dashboard():
    """
    Retorna métricas do dia.
    {
      "ev_hora": "+R$285.40",
      "hit_rate": "94.7%",
      "streak": 92,
      "total_bets": 156,
      "total_won": 147,
      "total_ev": "+R$4431"
    }
    """
```

---

## 📅 PLANO DE IMPLEMENTAÇÃO (Recomendado)

### Fase 1: Scrapers (1-2 semanas)
- [ ] **Semana 1, Dia 1-3:** BLLSport Scraper
  - [ ] Escolher Playwright vs Selenium
  - [ ] Capturar frame ao-vivo
  - [ ] Testar OCR com frames reais
  - [ ] Ajustar crop/regex conforme você enviar screenshot

- [ ] **Semana 1, Dia 4-7:** Bet365 Scraper
  - [ ] Conectar ao Dolphin
  - [ ] Fazer login
  - [ ] Extrair odds/linhas
  - [ ] Mapear CSS/XPath das linhas

### Fase 2: Macro Dolphin (2-3 semanas)
- [ ] **Semana 2-3:** DolphinExecutor
  - [ ] Setup API (TCP/RPC)
  - [ ] Implementar click/type/wait
  - [ ] Testar com aposta de teste (R$1)
  - [ ] Handlers para CAPTCHA/login bloqueado

### Fase 3: Fallbacks + Polish (1 semana)
- [ ] **Semana 4:** YouTube, ESPN, Flashscore APIs
  - [ ] Implementar 4 fallbacks
  - [ ] Testar fallback cascade
  - [ ] Adicionar rate limiting/retry logic

### Fase 4: Métricas + Dashboard (3-5 dias)
- [ ] Analytics DB setup
- [ ] MetricsManager
- [ ] `/api/dashboard` endpoint
- [ ] Webhook notificações

### Fase 5: Testes Completos (1 semana)
- [ ] Integration tests
- [ ] Load tests (1000+ WebSocket clients)
- [ ] Stress test macro Dolphin
- [ ] E2E com dados reais

---

## 🏗️ ESTRUTURA FINAL (Esperada)

```
IA-Basket/
├── backend/
│   ├── oracle_api.py              (294 linhas - add metrics)
│   ├── gemini_knowledge.py
│   └── main.py
│
├── core/
│   ├── oracle_nba.py              (já tem tudo)
│   ├── vision_bllsport.py         (já tem tudo)
│   └── nba_official.py            (já tem tudo)
│
├── integrations/
│   ├── scrapers/
│   │   ├── bllsport_scraper.py    (🔴 FAZER)
│   │   ├── bet365_scraper.py      (🟠 FAZER)
│   │   └── flashscore_scraper.py  (template existe)
│   │
│   ├── apis/
│   │   ├── youtube.py             (🔵 FAZER)
│   │   ├── espn.py                (🔵 FAZER)
│   │   ├── flashscore.py          (🔵 FAZER)
│   │   └── balldontlie.py         (✅ existe)
│   │
│   ├── executors/
│   │   ├── dolphin_macro.py       (🟡 FAZER)
│   │   ├── manual_executor.py     (🟢 FAZER)
│   │   ├── metrics.py             (NEW)
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── data/
│   ├── analytics.db               (NEW - métricas)
│   └── latest_oracle.json
│
└── tests/
    ├── test_scrapers.py           (NEW)
    ├── test_macro.py              (NEW)
    └── test_e2e.py                (NEW)
```

---

## 🎯 RESUMO: O QUE FALTA

| Componente | Status | Prioridade | Esforço |
|-----------|--------|-----------|---------|
| BLLSport Scraper | ❌ | 🔴 Crítica | 4-6h |
| Bet365 Scraper | ❌ | 🟠 Alta | 8-10h |
| Dolphin Macro | ❌ | 🟡 Média | 20-30h |
| Manual Executor | ❌ | 🟢 Baixa | 3-4h |
| YouTube/ESPN/Flashscore | ❌ | 🔵 Fallback | 6-8h |
| Métricas + Dashboard | ❌ | 🔵 Polish | 5-8h |
| **TOTAL** | | | **~50-70h** |

---

## 🚀 PRÓXIMO PASSO

**COMECE PELO:**

1. **BLLSport Scraper** (você manda screenshot do placar/relógio da bllsport para calibração)
2. **Depois:** Bet365 Scraper
3. **Depois:** Dolphin Macro

**Comando para rodar tudo pronto:**

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# Vai pra: http://127.0.0.1:8000/docs
```

---

**Status Final: 🟢 Backend 100% | Scrapers 0% | Macro 0% | Fallbacks 0% | Métricas 0%**

Pronto pra começar? 🚀
