#!/usr/bin/env python3
"""
Hoops_Gemini - Live Betting Arbitrage Bot
Main application entry point
"""

import json
import asyncio
import os
from dotenv import load_dotenv
from core.orquestrador import Orquestrador

def main():
    load_dotenv()

    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY não encontrada. Defina no arquivo .env')
    
    # Initialize orchestrator
    orchestrator = Orquestrador(config, api_key)
    
    # Run the bot
    asyncio.run(orchestrator.run())

if __name__ == "__main__":
    main()