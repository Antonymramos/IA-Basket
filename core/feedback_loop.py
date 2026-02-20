#!/usr/bin/env python3
"""
Feedback Loop: Rastreia resultado de apostas e calcula acurácia para aprendizado contínuo.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any


class FeedbackLoop:
    """Rastreia resultados de apostas para feedback e aprendizado."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection
    
    def _init_db(self) -> None:
        """Cria tabela para rastrear resultados de apostas."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bet_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    signal_id TEXT NOT NULL,
                    time_alvo TEXT,
                    tipo_pontuacao INTEGER,
                    stake REAL,
                    result_status TEXT,
                    result_reason TEXT,
                    ev_score REAL,
                    consensus_strength REAL,
                    point_gap INTEGER,
                    delay_seconds REAL,
                    timestamp_executed REAL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_bet_results_ts ON bet_results(ts)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_bet_results_status ON bet_results(result_status)"
            )
            connection.commit()
    
    def record_bet_execution(
        self,
        signal_id: str,
        time_alvo: str,
        tipo_pontuacao: int,
        stake: float,
        ev_score: float = 0.0,
        consensus_strength: float = 0.0,
        point_gap: int = 2,
        delay_seconds: float = 0.0,
    ) -> None:
        """Registra execução de aposta (antes de saber resultado)."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO bet_results 
                (ts, signal_id, time_alvo, tipo_pontuacao, stake, result_status, 
                 ev_score, consensus_strength, point_gap, delay_seconds, timestamp_executed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    signal_id,
                    time_alvo,
                    tipo_pontuacao,
                    stake,
                    "PENDING",
                    ev_score,
                    consensus_strength,
                    point_gap,
                    delay_seconds,
                    time.time(),
                ),
            )
            connection.commit()
    
    def record_bet_result(
        self,
        signal_id: str,
        result_status: str,
        result_reason: str = ""
    ) -> None:
        """
        Atualiza resultado de aposta.
        result_status: WON, LOST, EXPIRED, ERROR
        """
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE bet_results 
                SET result_status = ?, result_reason = ?
                WHERE signal_id = ? AND result_status = 'PENDING'
                """,
                (result_status, result_reason, signal_id),
            )
            connection.commit()
    
    def get_accuracy_stats(self, minutes: int = 120) -> dict[str, Any]:
        """Calcula acurácia e métricas de desempenho."""
        now = time.time()
        window_start = now - max(1, minutes) * 60
        
        with self._connect() as connection:
            # Total de apostas no período
            total = connection.execute(
                "SELECT COUNT(*) AS c FROM bet_results WHERE ts >= ? AND result_status != 'PENDING'",
                (window_start,),
            ).fetchone()["c"]
            
            # Apostas ganhas
            won = connection.execute(
                "SELECT COUNT(*) AS c FROM bet_results WHERE ts >= ? AND result_status = 'WON'",
                (window_start,),
            ).fetchone()["c"]
            
            # Apostas perdidas
            lost = connection.execute(
                "SELECT COUNT(*) AS c FROM bet_results WHERE ts >= ? AND result_status = 'LOST'",
                (window_start,),
            ).fetchone()["c"]
            
            # Apostas expiradas
            expired = connection.execute(
                "SELECT COUNT(*) AS c FROM bet_results WHERE ts >= ? AND result_status = 'EXPIRED'",
                (window_start,),
            ).fetchone()["c"]
            
            # Lucro/perda esperado
            won_ev = connection.execute(
                "SELECT SUM(ev_score * stake) AS total FROM bet_results WHERE ts >= ? AND result_status = 'WON'",
                (window_start,),
            ).fetchone()["total"] or 0.0
            
            lost_ev = connection.execute(
                "SELECT SUM(ev_score * stake) AS total FROM bet_results WHERE ts >= ? AND result_status = 'LOST'",
                (window_start,),
            ).fetchone()["total"] or 0.0
            
            # Acurácia por tipo de pontuação (2pt vs 3pt)
            accuracy_2pt = connection.execute(
                """
                SELECT 
                    SUM(CASE WHEN result_status = 'WON' THEN 1 ELSE 0 END) AS wins,
                    COUNT(*) AS total
                FROM bet_results 
                WHERE ts >= ? AND tipo_pontuacao = 2 AND result_status IN ('WON', 'LOST')
                """,
                (window_start,),
            ).fetchone()
            
            accuracy_3pt = connection.execute(
                """
                SELECT 
                    SUM(CASE WHEN result_status = 'WON' THEN 1 ELSE 0 END) AS wins,
                    COUNT(*) AS total
                FROM bet_results 
                WHERE ts >= ? AND tipo_pontuacao = 3 AND result_status IN ('WON', 'LOST')
                """,
                (window_start,),
            ).fetchone()
            
            # Acurácia por consenso (forte vs fraco)
            high_consensus = connection.execute(
                """
                SELECT 
                    SUM(CASE WHEN result_status = 'WON' THEN 1 ELSE 0 END) AS wins,
                    COUNT(*) AS total
                FROM bet_results 
                WHERE ts >= ? AND consensus_strength >= 0.70 AND result_status IN ('WON', 'LOST')
                """,
                (window_start,),
            ).fetchone()
            
            low_consensus = connection.execute(
                """
                SELECT 
                    SUM(CASE WHEN result_status = 'WON' THEN 1 ELSE 0 END) AS wins,
                    COUNT(*) AS total
                FROM bet_results 
                WHERE ts >= ? AND consensus_strength < 0.70 AND result_status IN ('WON', 'LOST')
                """,
                (window_start,),
            ).fetchone()
        
        # Calcula percentuais
        win_rate = (won / max(1, total)) if total > 0 else 0.0
        
        acc_2pt_rate = 0.0
        if accuracy_2pt["total"] and accuracy_2pt["total"] > 0:
            acc_2pt_rate = (accuracy_2pt["wins"] or 0) / accuracy_2pt["total"]
        
        acc_3pt_rate = 0.0
        if accuracy_3pt["total"] and accuracy_3pt["total"] > 0:
            acc_3pt_rate = (accuracy_3pt["wins"] or 0) / accuracy_3pt["total"]
        
        high_cons_rate = 0.0
        if high_consensus["total"] and high_consensus["total"] > 0:
            high_cons_rate = (high_consensus["wins"] or 0) / high_consensus["total"]
        
        low_cons_rate = 0.0
        if low_consensus["total"] and low_consensus["total"] > 0:
            low_cons_rate = (low_consensus["wins"] or 0) / low_consensus["total"]
        
        return {
            "window_minutes": minutes,
            "window_start_ts": window_start,
            "now_ts": now,
            "summary": {
                "total_bets": total,
                "won": won,
                "lost": lost,
                "expired": expired,
                "win_rate": round(win_rate, 3),
                "expected_profit": round(won_ev - lost_ev, 2),
            },
            "accuracy_by_points": {
                "2pt": {
                    "wins": accuracy_2pt["wins"] or 0,
                    "total": accuracy_2pt["total"] or 0,
                    "accuracy": round(acc_2pt_rate, 3),
                },
                "3pt": {
                    "wins": accuracy_3pt["wins"] or 0,
                    "total": accuracy_3pt["total"] or 0,
                    "accuracy": round(acc_3pt_rate, 3),
                },
            },
            "accuracy_by_consensus": {
                "strong_consensus": {
                    "wins": high_consensus["wins"] or 0,
                    "total": high_consensus["total"] or 0,
                    "accuracy": round(high_cons_rate, 3),
                },
                "weak_consensus": {
                    "wins": low_consensus["wins"] or 0,
                    "total": low_consensus["total"] or 0,
                    "accuracy": round(low_cons_rate, 3),
                },
            },
        }
    
    def get_success_examples(self, limit: int = 5) -> list[dict[str, Any]]:
        """Retorna últimas apostas bem-sucedidas para Few-Shot Learning."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT 
                    ts, signal_id, time_alvo, tipo_pontuacao, stake, 
                    ev_score, consensus_strength, point_gap, delay_seconds
                FROM bet_results 
                WHERE result_status = 'WON'
                ORDER BY ts DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        
        return [
            {
                "time_alvo": row["time_alvo"],
                "tipo_pontuacao": row["tipo_pontuacao"],
                "ev_score": row["ev_score"],
                "consensus_strength": row["consensus_strength"],
                "point_gap": row["point_gap"],
                "delay_seconds": row["delay_seconds"],
                "stake": row["stake"],
            }
            for row in rows
        ]
