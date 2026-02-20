#!/usr/bin/env python3
"""
Basic voice command interpreter for Jarvis panel.
"""

import re
import unicodedata


WAKE_WORDS = {
    "jarvis",
    "jarve",
    "jarves",
    "jarviz",
    "jarvi",
    "jarbis",
    "gervis",
    "jarvins",
    "jardim",
    "jazz",
}

NOISE_TOKENS = {
    "ja",
    "jardim",
    "jazz",
    "jar",
    "jarv",
    "vos",
    "voce",
    "vo",
}

VERB_TOKENS = {
    "abrir",
    "abre",
    "abra",
    "abri",
    "iniciar",
    "inicia",
    "ligar",
    "liga",
    "parar",
    "pausar",
    "pause",
    "stop",
    "status",
    "situacao",
    "lucro",
    "resultado",
    "relatorio",
    "buscar",
    "busca",
    "pesquisa",
    "analisar",
}


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def _strip_wake_words(text: str) -> str:
    tokens = [t for t in text.split() if t not in WAKE_WORDS]

    max_strip = 2
    while tokens and max_strip > 0:
        ahead = tokens[1:3]
        if tokens[0] in NOISE_TOKENS and any(tok in VERB_TOKENS for tok in ahead):
            tokens.pop(0)
            max_strip -= 1
            continue
        if tokens[0] in WAKE_WORDS:
            tokens.pop(0)
            max_strip -= 1
            continue
        break

    return " ".join(tokens).strip()


def interpret_voice_command(text: str) -> dict:
    if not text:
        return {"action": "none"}

    normalized = _strip_wake_words(_normalize(text))

    # Painel de erros / diagnóstico
    if re.search(r"\b(abrir|abre|mostrar|exibir)\b.*\b(painel|dashboard)\b.*\b(erro|erros|diagnostico)\b", normalized):
        return {"action": "open_errors_panel"}

    # Pesquisa/estratégia com Gemini
    if re.search(
        r"\b(busca|buscar|pesquisa|pesquisar|estrategia|analisa|analisar|internet|net|nba|padrao|margem|jogos|ultimos|ultimo|vitoria|vitorias|derrota|derrotas|basquete|basket)\b",
        normalized,
    ):
        return {"action": "knowledge_query", "prompt": text.strip()}

    if re.search(r"\b(ativar|liga|ligar|inicia|iniciar)\b.*\b(auto\s*bet|autobet|auto\s*aposta|aposta|apostas|bet)\b", normalized):
        return {"action": "set_auto_bet", "enabled": True}

    if re.search(r"\b(desativar|desliga|desligar|pausa|parar)\b.*\b(auto\s*bet|autobet|auto\s*aposta|aposta|apostas|bet)\b", normalized):
        return {"action": "set_auto_bet", "enabled": False}

    if re.search(r"\b(pausar|pause|stop|parar)\b", normalized):
        return {"action": "stop"}

    if re.search(r"\b(iniciar|start|rodar|executar)\b", normalized):
        return {"action": "start"}

    if re.search(r"\b(desfazer|rollback|reverter|voltar)\b.*\b(ajuste|config|configuracao|configuração)\b", normalized):
        return {"action": "rollback_latest"}

    if re.search(r"\b(rollback|reverter)\b", normalized):
        return {"action": "rollback_latest"}

    match = re.search(r"trocar jogo\s+(.+)$", normalized)
    if match:
        return {"action": "select_game", "game": match.group(1).strip()}

    return {"action": "none"}
