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


def resolve_auto_bet_setting(config):
    auto_bet_enabled = bool(config.get('auto_bet_enabled', False))
    prompt_on_start = bool(config.get('prompt_auto_bet_on_start', False))

    if prompt_on_start:
        default_label = 'S' if auto_bet_enabled else 'N'
        choice = input(f"Aposta automática ligada? (S/N) [padrão {default_label}]: ").strip().lower()
        if choice in ('s', 'sim', 'y', 'yes'):
            auto_bet_enabled = True
        elif choice in ('n', 'nao', 'não', 'no'):
            auto_bet_enabled = False

    config['auto_bet_enabled'] = auto_bet_enabled
    mode = 'ON' if auto_bet_enabled else 'OFF'
    print(f"[USER_CONTROL] auto_bet_enabled={mode}")

def main():
    load_dotenv()

    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)

    decision_engine = config.get('decision_engine', 'gemini')
    api_key = os.getenv('GEMINI_API_KEY')
    if decision_engine in ('gemini', 'compare') and not api_key:
        raise RuntimeError('GEMINI_API_KEY não encontrada. Defina no arquivo .env')

    resolve_auto_bet_setting(config)
    
    # Initialize orchestrator
    orchestrator = Orquestrador(config, api_key)
    
    # Run the bot
    asyncio.run(orchestrator.run())

if __name__ == "__main__":
    main()