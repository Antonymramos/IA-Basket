#!/usr/bin/env python3
"""
Orquestrador - Main loop for monitoring and decision making
"""

import asyncio
import json
from core.gemini_brain import GeminiBrain
from data_ingestion.live_feed_client import LiveFeedClient
from data_ingestion.bet_scraper import BetScraper

class Orquestrador:
    def __init__(self, config):
        self.config = config
        self.gemini = GeminiBrain(config['gemini_api_key'])
        self.live_feed = LiveFeedClient(config['live_feed_ws_url'])
        self.bet_scraper = BetScraper(config['bet_url'])
    
    async def run(self):
        """
        Main monitoring loop
        """
        print("Iniciando monitoramento...")
        
        while True:
            # Get data from both sources
            transmission_data = await self.live_feed.get_score()
            bet_data = await self.bet_scraper.get_score()
            
            # Analyze with Gemini
            response = self.gemini.analyze(transmission_data, bet_data)
            
            # Process response (tool calls)
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content.parts:
                        for part in candidate.content.parts:
                            if part.function_call:
                                # Execute the function call
                                function_name = part.function_call.name
                                args = part.function_call.args
                                if function_name == "registrar_discrepancia":
                                    from core.tools_registry import registrar_discrepancia
                                    registrar_discrepancia(**args)
                                elif function_name == "executar_aposta_live":
                                    from core.tools_registry import executar_aposta_live
                                    executar_aposta_live(**args)
            
            # Wait before next check
            await asyncio.sleep(0.5)  # 500ms