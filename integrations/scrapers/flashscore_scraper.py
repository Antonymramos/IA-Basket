"""Flashscore Scraper - Fallback provider for live scores."""

import asyncio
from typing import Optional, Dict


class FlashscoreScraper:
    """Scraper para Flashscore - Fallback se BLLSport cair."""

    def __init__(self):
        """Initialize Flashscore scraper."""
        self.is_running = False
        self.current_score: Dict = {}

    async def start(self):
        """Inicia loop de captura."""
        self.is_running = True
        while self.is_running:
            try:
                await self.fetch_score()
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Flashscore error: {e}")
                await asyncio.sleep(2)

    async def fetch_score(self) -> Optional[Dict]:
        """
        Captura score de Flashscore.
        
        Returns:
            {"home": 93, "away": 85, "tempo": "5:03", "status": "live"}
        
        TODO:
            - Usar Selenium/Playwright
            - Acessar https://www.flashscore.com/
            - Encontrar jogo NBA ativo
            - Extrair placar/tempo
        """
        # Placeholder
        return None

    async def stop(self):
        """Para o loop."""
        self.is_running = False


if __name__ == "__main__":
    print("🟢 Flashscore Scraper (Fallback)")
    print("   Aguardando implementação...")
