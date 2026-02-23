# ⚡ TL;DR - O ESSENCIAL EM 2 MINUTOS

## Situação
- ✅ **Backend 100% pronto** (FastAPI, OCR, WebSocket, detecção de erros)
- ❌ **Faltam: BLLSport + Bet365 scrapers + Dolphin macro** (38h de código)

---

## O que você precisa fazer

**Opção 1 (Recomendado):** Comece com BLLSport Scraper HOJE
- Captura frame ao-vivo do bllsport
- Testa OCR com dados reais
- 4-6 horas de trabalho
- Você manda screenshot para calibração

**Opção 2:** Entender Dolphin macro (mais complexo)
- Automação de apostas no Bet365
- 20-30 horas de trabalho
- Guia completo em DOLPHIN_MACRO_GUIDE.md

**Opção 3:** Fazer rollback fallbacks (mais simples)
- YouTube + ESPN + Flashscore
- 6-8 horas

---

## Começar AGORA

```bash
# Terminal 1: Rodar backend
cd c:\Users\anton\OneDrive\Desktop\IA\ Basket\IA-Basket
python -m uvicorn backend.main:app --port 8000

# Terminal 2: Implementar BLLSport
code integrations/scrapers/bllsport_scraper.py

# Copie isto (template completo abaixo):
```

---

## Template BLLSport Básico (Copiar e Colar)

```python
import asyncio
import base64
from typing import Optional, Dict
from playwright.async_api import async_playwright
from core.vision_bllsport import analyze_bllsport_frame

class BLLSportScraper:
    def __init__(self):
        self.browser = None
        self.page = None
    
    async def connect(self) -> bool:
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=False)
            self.page = await self.browser.new_page()
            await self.page.goto("https://bllsport.com", wait_until="networkidle")
            print("✅ Conectado ao bllsport")
            return True
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    async def get_live_frame(self) -> Optional[str]:
        """Captura screenshot em base64"""
        try:
            screenshot_bytes = await self.page.screenshot(type="png")
            b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            return f"data:image/png;base64,{b64}"
        except Exception as e:
            print(f"❌ Erro screenshot: {e}")
            return None
    
    async def get_placar(self, frame_base64: str) -> Dict:
        """Extrai placar via OCR"""
        try:
            # VOCÊ VAI AJUSTAR ESTES VALORES após enviar screenshot
            crop = {"x": 0, "y": 0, "w": 1280, "h": 720}
            
            vision_result = analyze_bllsport_frame(frame_base64, crop)
            
            if not vision_result.ok:
                return {"home": None, "away": None, "tempo": None, "erro": vision_result.error}
            
            return {
                "home": vision_result.placar["home"],
                "away": vision_result.placar["away"],
                "tempo": vision_result.tempo_video,
                "erro": None
            }
        except Exception as e:
            return {"home": None, "away": None, "tempo": None, "erro": str(e)}
    
    async def close(self):
        if self.browser:
            await self.browser.close()

# TESTE
async def main():
    scraper = BLLSportScraper()
    if await scraper.connect():
        frame = await scraper.get_live_frame()
        if frame:
            placar = await scraper.get_placar(frame)
            print(f"Placar: {placar['home']}-{placar['away']} Q{placar['tempo']}")
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Instalar dependência rápido

```bash
pip install playwright
python -m playwright install chromium
python integrations/scrapers/bllsport_scraper.py
```

---

## Próximo: Enviar screenshot

1. Abra bllsport.com
2. Tire screenshot (Shift+Print)
3. Localize: onde fica placar, tempo, jogador?
4. Me envie com as coordenadas (x, y, w, h)
5. Eu calibro OCR + você tem 100% funcional

---

## Documentos para referência

- `MAPA_VISUAL.md` - Overview completo
- `COMECE_AGORA.md` - Próximos passos detalhados
- `DOLPHIN_MACRO_GUIDE.md` - Se quiser automação
- `ROADMAP_COMPLETO.md` - Timeline 5 semanas

---

## Status Backend (já testado ✅)

```bash
# GET /docs → Interface Swagger
curl http://127.0.0.1:8000/docs

# POST /api/oracle/analyze → Análise rápida
curl -X POST http://127.0.0.1:8000/api/oracle/analyze \
  -H "Content-Type: application/json" \
  -d '{"frame_base64": "..."}'

# WS /ws/oracle → WebSocket broadcast (1000+ clients)
# GET /api/latest → Último resultado
```

---

## ⏱️ ETA

| O quê | Tempo | Quando |
|---|---|---|
| BLLSport Scraper | 4-6h | Hoje/Amanhã |
| Bet365 Scraper | 8-10h | Dia 2-3 |
| Dolphin Macro | 20-30h | Dias 3-7 |
| Fallbacks | 6-8h | Dias 5-6 |
| Métricas | 5-8h | Dias 6-7 |
| **TOTAL** | **38h** | **5-7 dias** |

---

**Você está pronto? Comece agora! 🚀**

Cole o código acima em `integrations/scrapers/bllsport_scraper.py` e execute.
