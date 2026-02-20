#!/usr/bin/env python3
"""
Context builder para enriquecer prompts do Gemini com histórico recente de eventos,
Few-Shot examples, temporal context, e SOTAQUE BRASILEIRO.
"""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from pathlib import Path


def _query(connection: sqlite3.Connection, sql: str, params: tuple = ()):
    cur = connection.execute(sql, params)
    return cur.fetchall()


def _get_temporal_context() -> str:
    """Extrai contexto temporal (hora, dia da semana, etc)."""
    now = datetime.now()
    hour = now.hour
    day_name = now.strftime("%A")
    
    # Períodos do dia
    if 6 <= hour < 12:
        period = "manhã"
    elif 12 <= hour < 18:
        period = "tarde"
    else:
        period = "noite/madrugada"
    
    lines = [
        f"Contexto Temporal: {day_name} ({now.strftime('%H:%M')}), período={period}",
        f"Padrão esperado: Mais apostas na {period} geralmente.",
    ]
    
    return "\n".join(lines)


def _get_few_shot_examples(db_path: str) -> str:
    """Extrai últimas apostas bem-sucedidas como Few-Shot examples."""
    try:
        path = Path(db_path)
        if not path.exists():
            return "Sem exemplos de sucesso ainda (histórico vazio)."
        
        with sqlite3.connect(str(path), timeout=5) as connection:
            connection.row_factory = sqlite3.Row
            
            success_rows = _query(
                connection,
                """
                SELECT 
                    tipo_pontuacao, 
                    ev_score, 
                    consensus_strength,
                    ROUND(consensus_strength * 100) as consensus_pct,
                    delay_seconds
                FROM bet_results 
                WHERE result_status = 'WON'
                ORDER BY ts DESC
                LIMIT 5
                """
            )
        
        if not success_rows:
            return "Sem apostas bem-sucedidas no histórico ainda."
        
        lines = ["EXEMPLOS DE DECISÕES BEM-SUCEDIDAS (Few-Shot Learning):"]
        for i, row in enumerate(success_rows, 1):
            lines.append(
                f"  Exemplo {i}: {row['tipo_pontuacao']}pt, "
                f"EV={row['ev_score']:.2f}, "
                f"Consenso={row['consensus_pct']}%, "
                f"Delay={row['delay_seconds']:.1f}s → ✓ GANHOU"
            )
        
        return "\n".join(lines)
    
    except Exception:
        return "Erro ao carregar exemplos de sucesso."


def build_gemini_context(db_path: str, minutes: int = 120, limit: int = 12) -> str:
    path = Path(db_path)
    if not path.exists():
        return "Sem histórico local ainda."

    window_start = time.time() - max(1, minutes) * 60

    with sqlite3.connect(str(path), timeout=5) as connection:
        connection.row_factory = sqlite3.Row

        event_counts = _query(
            connection,
            """
            SELECT event_name, COUNT(*) AS c
            FROM events
            WHERE ts >= ?
            GROUP BY event_name
            ORDER BY c DESC
            """,
            (window_start,),
        )

        recent_patterns = _query(
            connection,
            """
            SELECT event_name, message, COUNT(*) AS c
            FROM events
            WHERE ts >= ?
              AND event_name IN ('ERROR', 'GEMINI_ERROR', 'BLOQUEADO', 'EXPIROU', 'COMPARE', 'FEED_WARNING')
            GROUP BY event_name, message
            ORDER BY c DESC
            LIMIT ?
            """,
            (window_start, limit),
        )

        recent_events = _query(
            connection,
            """
            SELECT ts, event_name, game, message
            FROM events
            WHERE ts >= ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (window_start, limit),
        )

    counts = {row["event_name"]: row["c"] for row in event_counts}
    detected = counts.get("DETECTADO", 0)
    blocked = counts.get("BLOQUEADO", 0)
    expired = counts.get("EXPIROU", 0)
    errors = counts.get("ERROR", 0) + counts.get("GEMINI_ERROR", 0)

    denominator = max(1, detected)
    blocked_rate = blocked / denominator
    expired_rate = expired / denominator
    error_rate = errors / denominator

    lines: list[str] = []
    lines.append(f"Janela: últimos {minutes} minutos")
    lines.append(
        f"Métricas: detectado={detected}, bloqueado={blocked} ({blocked_rate:.2%}), "
        f"expirado={expired} ({expired_rate:.2%}), erros={errors} ({error_rate:.2%})"
    )
    
    # Adicionar contexto temporal
    lines.append("")
    lines.append(_get_temporal_context())
    
    # Adicionar Few-Shot examples
    lines.append("")
    lines.append(_get_few_shot_examples(db_path))

    if recent_patterns:
        lines.append("")
        lines.append("Padrões recentes de falha:")
        for row in recent_patterns:
            message = (row["message"] or "").strip() or "sem_mensagem"
            lines.append(f"- {row['event_name']} x{row['c']}: {message}")

    if recent_events:
        lines.append("")
        lines.append("Últimos eventos:")
        for row in recent_events[:6]:
            msg = (row["message"] or "").strip() or ""
            game = (row["game"] or "").strip() or "sem_jogo"
            lines.append(f"- {row['event_name']} | jogo={game} | {msg}")

    return "\n".join(lines)

def build_brazilian_enriched_context(db_path: str, minutes: int = 120, limit: int = 12) -> str:
    """
    Constrói contexto enriquecido com SOTAQUE BRASILEIRO, gírias e jeito BR.
    Isso ajuda Gemini a entender melhor o padrão de apostador brasileiro.
    """
    # Base context
    base_context = build_gemini_context(db_path, minutes, limit)
    
    # Adiciona contexto cultural brasileiro
    from core.brazilian_context import get_contexto_temporal_brasileiro, get_explicacao_girias
    
    brazilian_enrichment = f"""
    
    === 🇧🇷 CONTEXTO CULTURAL BRASILEIRO ===
    {get_contexto_temporal_brasileiro()}
    
    {get_explicacao_girias()}
    """
    
    return base_context + brazilian_enrichment