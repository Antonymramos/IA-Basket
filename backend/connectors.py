#!/usr/bin/env python3
"""
Connector registry for Jarvis panel.
"""

TRANSMISSION_CONNECTORS = [
    {
        "id": "simulated_feed",
        "label": "Simulado (feed local)",
        "type": "simulation",
        "description": "Scores simulados para testes rapidos.",
    },
    {
        "id": "live_ws",
        "label": "WebSocket rapido",
        "type": "live",
        "description": "Feed rapido via WS (ws:// ou wss://).",
    },
]

BET_CONNECTORS = [
    {
        "id": "bet_mock",
        "label": "Bet mock (simulado)",
        "type": "simulation",
        "description": "Simulador local de bet para testes.",
    },
    {
        "id": "bet365_playwright",
        "label": "Bet365 (Playwright)",
        "type": "live",
        "description": "Automacao UI via Playwright.",
    },
]
