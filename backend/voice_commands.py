#!/usr/bin/env python3
"""
Basic voice command interpreter for Jarvis panel.
"""

import re


def interpret_voice_command(text: str) -> dict:
    if not text:
        return {"action": "none"}

    normalized = text.strip().lower()

    if re.search(r"\b(ativar|ligar)\b.*\b(aposta|apostas)\b", normalized):
        return {"action": "set_auto_bet", "enabled": True}

    if re.search(r"\b(desativar|desligar)\b.*\b(aposta|apostas)\b", normalized):
        return {"action": "set_auto_bet", "enabled": False}

    if re.search(r"\b(pausar|stop|parar)\b", normalized):
        return {"action": "stop"}

    if re.search(r"\b(iniciar|start|rodar|executar)\b", normalized):
        return {"action": "start"}

    match = re.search(r"trocar jogo\s+(.+)$", normalized)
    if match:
        return {"action": "select_game", "game": match.group(1).strip()}

    return {"action": "none"}
