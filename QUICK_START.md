# 🎯 ONDE COLOCAR CADA COISA - SUPER SIMPLES

## 🔴 #1 - BLLSport Scraper (PRIMEIRA)

```
📁 integrations/scrapers/bllsport_scraper.py
```

**Já tem template!** Você só precisa implementar 2 métodos:

```python
async def fetch_frame(self) -> str:
    """Retorna: "data:image/png;base64,XXXXX" """
    # TODO: Usar Playwright/Selenium/FFmpeg

async def get_placar(self) -> Dict:
    """Retorna: {"home": 93, "away": 85, "tempo": "Q1 05:03"} """
    # TODO: Usar OCR (já vem pronto em core/)
```

**Depois:** POST para `http://127.0.0.1:8000/api/oracle/ingest`

---

## 🟠 #2 - Bet365 Scraper (SEGUNDA)

```
📁 integrations/scrapers/bet365_scraper.py
```

**Já tem template!** Você só precisa implementar:

```python
async def fetch_odds(self) -> Dict:
    """Retorna: {
        "placar_geral": {"home": 91, "away": 85},
        "linhas": [{"time": "Q1 05:03", "line": 2.5, "odds": 1.40}]
    }"""
    # TODO: Selenium + CDP

async def get_linhas_ativas(self) -> List[Dict]:
    """Retorna linhas que foram REGISTRADAS na Bet365"""
```

---

## 🟡 #3 - Dolphin Executor (TERCEIRA)

```
📁 integrations/executors/dolphin_macro.py
```

**Já tem template!** Você só precisa implementar:

```python
async def execute_macro(self, macro_steps: List[Dict]) -> bool:
    """Executa: [
        {"action": "click", "x": 500, "y": 300},
        {"action": "type", "text": "100"},
        {"action": "click", "x": 600, "y": 350}
    ]"""
    # TODO: Conectar ao Dolphin bot (TCP/WebSocket)
```

---

## 🟢 #4 - Manual Executor (QUARTA)

```
📁 integrations/executors/manual_executor.py
```

**Já tem template!** Você só precisa implementar:

```python
async def notify_recommendation(self, oracle_data: Dict) -> bool:
    """Envia notificação (Telegram/Discord/Email)"""
    # TODO: send_telegram(webhook_url, message)

async def get_approval(self, oracle_data: Dict) -> bool:
    """Aguarda resposta do usuário"""
    # TODO: Endpoint POST /api/approve
```

---

## ✅ JÁ TEM PRONTO (Não precisa mexer)

```
✅ backend/oracle_api.py           (40+ endpoints)
✅ core/oracle_nba.py              (Detector de erros)
✅ core/vision_bllsport.py         (OCR placar/tempo)
✅ core/nba_official.py            (BallDontLie API)
✅ integrations/apis/balldontlie.py (JÁ EXISTE)
```

---

## 🔗 FLUXO COMPLETO

```
1. BLLSport Scraper
   ↓
   Captura frame + aplica OCR
   ↓
2. POST /api/oracle/ingest
   ↓
   (Retorna JSON com análise)
   ↓
3. WebSocket Broadcast
   ↓
4. Dolphin Executor OU Manual Executor
   ↓
   (Executa a aposta recomendada)
```

---

## 📝 TEMPLATE: Como começar?

### Passo 1: Abrir o arquivo
```
c:\Users\anton\OneDrive\Desktop\IA Basket\IA-Basket\
integrations\scrapers\bllsport_scraper.py
```

### Passo 2: Encontrar o TODO
```python
async def fetch_frame(self) -> Optional[str]:
    """Captura frame atual de BLLSport."""
    
    # 👇 AQUI É O SEU CÓDIGO 👇
    # TODO: Usar Playwright/Selenium pra capturar screenshot
```

### Passo 3: Implementar
```python
async def fetch_frame(self) -> Optional[str]:
    """Captura frame atual de BLLSport."""
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(self.channel_url)
        screenshot = await page.screenshot()
        
        import base64
        base64_frame = base64.b64encode(screenshot).decode()
        
        await browser.close()
        
        return f"data:image/png;base64,{base64_frame}"
```

### Passo 4: Testar
```bash
python -m integrations.scrapers.bllsport_scraper
```

---

## 🚀 COMECE AGORA

### Instalar dependências
```bash
pip install playwright selenium
playwright install chromium
```

### Abrir arquivo
```bash
code integrations\scrapers\bllsport_scraper.py
```

### Implementar `fetch_frame()`
- Escolher: Playwright vs Selenium vs FFmpeg
- Capturar screenshot
- Converter pra base64
- Retornar "data:image/png;base64,..."

### Testar
```bash
python test_oracle_api.py
```

---

## 📍 LOCALIZAÇÃO EXATA

| Componente | Arquivo |
|------------|---------|
| BLLSport | `integrations/scrapers/bllsport_scraper.py` |
| Bet365 | `integrations/scrapers/bet365_scraper.py` |
| Flashscore | `integrations/scrapers/flashscore_scraper.py` |
| Dolphin | `integrations/executors/dolphin_macro.py` |
| Manual | `integrations/executors/manual_executor.py` |
| Tests | `tests/test_*.py` |

---

**Tudo pronto! Pode começar! 🚀**
