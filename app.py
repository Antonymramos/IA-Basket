#!/usr/bin/env python3
"""
Hoops_Gemini - Live Betting Arbitrage Bot
Main application entry point
"""

import json
import asyncio
from core.orquestrador import Orquestrador

def main():
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize orchestrator
    orchestrator = Orquestrador(config)
    
    # Run the bot
    asyncio.run(orchestrator.run())

if __name__ == "__main__":
    main()