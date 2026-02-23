# 🚀 COMECE AGORA: Próximos Passos (Acionáveis)

## 📊 Status Atual

```
Backend FastAPI:     ✅✅✅✅✅✅✅✅✅✅✅✅ 100%
OCR Pipeline:        ✅✅✅✅✅✅✅✅✅✅✅✅ 100%
WebSocket Broadcast: ✅✅✅✅✅✅✅✅✅✅✅✅ 100%
Error Detection:     ✅✅✅✅✅✅✅✅✅✅✅✅ 100%
─────────────────────────────────────────────────
BLLSport Scraper:    ❌ 0% (COMEÇAR AGORA!)
Bet365 Scraper:      ❌ 0%
Dolphin Macro:       ❌ 0%
Fallbacks:           ❌ 0%
Métricas:            ❌ 0%
─────────────────────────────────────────────────
TOTAL:               ██████░░░░░░ 67% (38h para 100%)
```

---

## 🎯 OPÇÃO 1: BLLSport Scraper (RECOMENDADO - Comece aqui!)

### Por que?
- ✅ Mais rápido (4-6 horas)
- ✅ Não precisa de dependências externas funcionando
- ✅ Testa o pipeline OCR em produção (com seus dados reais)
- ✅ Você pode avaliar a acurácia antes de arriscar $$$

### O que você precisa:
```
1. Um screenshot do placar bllsport.com
   Deve mostrar:
   - Placar (ex: 93-85)
   - Tempo (ex: Q1 05:03)
   - Jogador (ex: R$L Mag)
   
2. Os comentários (x, y, w, h) de onde fica cada um
   Exemplo: "Placar está no canto superior: x=100, y=50, w=400, h=100"
```

### Passo 1: Tirar screenshot

```bash
# Abra bllsport.com em seu navegador
# Vá para um jogo ao-vivo
# Selecione a área que tem APENAS o placar/tempo/jogador
# Faça print (Shift+Print ou Snip)
# Salve em: integrations/scrapers/bllsport_sample.png
```

### Passo 2: Implementar básico

**Arquivo:** `integrations/scrapers/bllsport_scraper.py`

```python
import asyncio
import base64
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import async_playwright


class BLLSportScraper:
    """Scraper para bllsport.com live stream."""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.url = "https://bllsport.com"
    
    async def connect(self) -> bool:
        """Conectar ao bllsport com Playwright."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=False)
            self.page = await self.browser.new_page()
            
            # Navegar
            await self.page.goto(self.url, wait_until="networkidle")
            print("✅ Conectado ao bllsport")
            return True
        except Exception as e:
            print(f"❌ Falha ao conectar: {e}")
            return False
    
    async def get_live_frame(self) -> Optional[str]:
        """
        Capturar screenshot ao-vivo no formato base64.
        
        Retorna: "data:image/png;base64,..." ou None se falhou
        """
        try:
            # Aguardar elemento do vídeo
            await self.page.wait_for_selector(".video-player, [role='main']", timeout=5000)
            
            # Screenshot
            screenshot_bytes = await self.page.screenshot(type="png")
            
            # Converter para base64
            b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            
            return f"data:image/png;base64,{b64}"
        
        except Exception as e:
            print(f"❌ Falha ao capturar frame: {e}")
            return None
    
    async def get_placar(self, frame_base64: str, crop: Dict = None) -> Dict:
        """
        Extrair placar/tempo do frame via OCR.
        
        Args:
            frame_base64: Frame em base64
            crop: {"x": 100, "y": 50, "w": 400, "h": 100} (opcional)
        
        Returns:
            {
                "home": 93,
                "away": 85,
                "tempo": "Q1 05:03",
                "jogador": "R$L Mag",
                "erro": None
            }
        """
        
        # Usar core.vision_bllsport
        from core.vision_bllsport import analyze_bllsport_frame
        
        try:
            # Se crop não foi fornecido, tentar padrão
            if not crop:
                crop = {
                    "x": 0,      # Você vai ajustar com base em seu screenshot
                    "y": 0,
                    "w": 1280,   # Full width (ajustar conforme necessário)
                    "h": 720     # Altura do vídeo
                }
            
            # Chamar OCR
            vision_result = analyze_bllsport_frame(frame_base64, crop)
            
            if not vision_result.ok:
                return {
                    "home": None,
                    "away": None,
                    "tempo": None,
                    "jogador": None,
                    "erro": vision_result.error
                }
            
            return {
                "home": vision_result.placar["home"],
                "away": vision_result.placar["away"],
                "tempo": vision_result.tempo_video,
                "jogador": "R$L Mag",  # TODO: extrair do frame
                "erro": None
            }
        
        except Exception as e:
            return {
                "home": None,
                "away": None,
                "tempo": None,
                "jogador": None,
                "erro": str(e)
            }
    
    async def loop_forever(self, interval_ms: int = 300):
        """
        Loop contínuo capturando frames (3 FPS ~= 300ms).
        """
        if not await self.connect():
            return
        
        try:
            while True:
                # Capturar frame
                frame = await self.get_live_frame()
                
                if frame:
                    # Extrair placar
                    placar = await self.get_placar(frame)
                    print(f"✅ {placar['home']}-{placar['away']} Q{placar['tempo']}")
                    
                    # Enviar para backend
                    # POST /api/oracle/ingest
                    # ... (implementar depois)
                
                await asyncio.sleep(interval_ms / 1000)
        
        except KeyboardInterrupt:
            print("\n⏸️  Parando...")
        
        finally:
            await self.close()
    
    async def close(self):
        """Fechar browser."""
        if self.browser:
            await self.browser.close()
            print("✅ Browser fechado")


# ==== TESTE ====

async def main():
    scraper = BLLSportScraper()
    
    # Opção 1: Uma vez
    if await scraper.connect():
        frame = await scraper.get_live_frame()
        if frame:
            # TODO: Você fornece crop aqui
            crop = {"x": 0, "y": 0, "w": 1280, "h": 720}
            placar = await scraper.get_placar(frame, crop)
            print(f"Placar: {placar}")
        
        await scraper.close()
    
    # Opção 2: Loop contínuo (comentado por enquanto)
    # await scraper.loop_forever(interval_ms=300)


if __name__ == "__main__":
    asyncio.run(main())
```

### Passo 3: Testar

```bash
# Instale Playwright
pip install playwright
python -m playwright install chromium

# Rode o teste
cd c:\Users\anton\OneDrive\Desktop\IA\ Basket\IA-Basket
python -m pytest tests/test_scrapers.py::test_bllsport_connect -v -s
```

### Passo 4: Calibrar OCR com seu screenshot

**AQUI VOCÊ PARTICIPA!**

```bash
# 1. Tire um screenshot REAL de bllsport mostrando:
#    - Placar (ex: 93-85)
#    - Tempo (ex: Q1 05:03)
#
# 2. Me envie o arquivo + as coordenadas:
#    Placar fica em: x=50, y=100, w=200, h=50
#    Tempo fica em:  x=280, y=100, w=150, h=50
#
# 3. Eu ajusto o regex no core/vision_bllsport.py
#
# 4. Testamos juntos
```

---

## 🎯 OPÇÃO 2: Entender Dolphin Macro Agora

Se quer pular direto para o "coração" do sistema:

### Passo 1: Verificar Dolphin

```powershell
# Está instalado?
Get-ChildItem 'C:\Program Files\Dolphin Anty\'

# Se não:
choco install dolphin-anty
# ou baixar de https://dolphin.dev
```

### Passo 2: Criar profiles

```bash
# Abrir Dolphin
C:\Program Files\Dolphin Anty\dolphin.exe

# Criar Profile 1 "BET365_MAIN"
├─ Name: BET365_MAIN
├─ Fingerprint: Random
├─ Make: Browser vai ser invisível

# Criar Profile 2 "BET365_FALLBACK"
├─ Name: BET365_FALLBACK
├─ Fingerprint: Diferente
```

### Passo 3: Testar comunicação TCP

```python
# test_dolphin_connection.py
import asyncio
import httpx

async def test_dolphin():
    """Testar se Dolphin está respondendo."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://127.0.0.1:7778/browser/status",
                timeout=5.0
            )
            print(f"✅ Dolphin respondendo: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"❌ Dolphin não respondendo: {e}")
        print("   → Verifique se Dolphin.exe está aberto")

asyncio.run(test_dolphin())
```

---

## 🎯 OPÇÃO 3: Começar Fallbacks

Se quer setup os fallbacks para robuustez:

### YouTube Stream Parsing

```python
# integrations/apis/youtube.py

import re
from playwright.async_api import async_playwright

async def get_youtube_frame(video_id: str) -> str:
    """
    Capturar frame de YouTube livestream.
    
    Args:
        video_id: ex "9bZkp7q19f0"
    """
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    page = await browser.new_page()
    
    await page.goto(f"https://youtube.com/watch?v={video_id}")
    await page.wait_for_selector("video")
    
    # Screenshot do vídeo
    screenshot = await page.screenshot()
    
    await browser.close()
    
    import base64
    return f"data:image/png;base64,{base64.b64encode(screenshot).decode()}"


async def main():
    # Testar com NBA 2025 livestream (procure um video_id ativo)
    frame = await get_youtube_frame("AQUI_VAI_VIDEO_ID")
    
    # Enviar pro OCR
    from core.vision_bllsport import analyze_bllsport_frame
    result = analyze_bllsport_frame(frame)
    print(result)

asyncio.run(main())
```

---

## ⚡ RESUMO: Comece Aqui AGORA

### Timeline recomendada:

**Hoje (2-3 horas):**
- [ ] BLLSport scraper básico
- [ ] Tire screenshot do placar
- [ ] Me envie para calibrar OCR

**Amanhã (4-6 horas):**
- [ ] OCR totalmente calibrado
- [ ] Scraper rodando em loop contínuo

**Próximo dia (8-10 horas):**
- [ ] Bet365 scraper (login + oddss)
- [ ] Testar com aposta de R$1

**Semana 2 (20-30 horas):**
- [ ] Dolphin Macro completo
- [ ] Testar macro em produção

**Semana 3 (10-15 horas):**
- [ ] Fallbacks + dashboard
- [ ] Métricas

---

## 🔥 COMANDO PARA COMEÇAR AGORA

### C1: Clone do repo + setup

```bash
cd c:\Users\anton\OneDrive\Desktop\IA\ Basket\IA-Basket

# Ativar venv
.venv\Scripts\Activate.ps1

# Instalar Playwright
pip install playwright
python -m playwright install chromium

# Criar arquivo de teste
code integrations/scrapers/bllsport_scraper.py
```

### C2: Rode backend primeiro

```bash
# Em outro terminal:
python -m uvicorn backend.main:app --reload --port 8000

# Verificar: http://127.0.0.1:8000/docs
```

### C3: Teste inicial

```bash
python integrations/scrapers/bllsport_scraper.py

# Deve conectar ao bllsport e capturar frame
# Se falhar: verá erro claro
```

---

## 📱 Precisarei de você:

1. **Screenshot do bllsport** (mostrando placar/tempo)
2. **Coordenadas** (onde fica cada informação)
3. **Se usar Dolphin:** Qual versão + profiles já criados?
4. **Bet365 account** (para testar macro com R$1)

---

## 🎯 RÁPIDO CHECK-IN

**Você prefere começar por:**

- [ ] A) BLLSport Scraper (recomendado - rápido feedback)
- [ ] B) Entender Dolphin (mais complexo mas core)
- [ ] C) Fallbacks/YouTube (mais fácil)
- [ ] D) Métricas/Dashboard (mais simples, sem scrapers)

**Indique qual e eu gero código 100% pronto para você usar!**

---

**Status: 🟢 Backend Pronto | Aguardando sua input (screenshot ou preferência) para começar fase 2 🚀**
