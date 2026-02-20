#!/usr/bin/env python3
"""
Persistência e consultas de diagnósticos para eventos do bot.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


class AnalyticsStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ts REAL NOT NULL,
                        event_name TEXT NOT NULL,
                        game TEXT,
                        message TEXT,
                        payload_json TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_events_event_name ON events(event_name)"
                )
                connection.commit()

    def record_event(self, event_name: str, payload: dict[str, Any], game: str | None = None) -> None:
        timestamp = time.time()
        safe_payload = payload or {}
        message = str(safe_payload.get("message") or safe_payload.get("reason") or "")

        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO events (ts, event_name, game, message, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        event_name,
                        game,
                        message,
                        json.dumps(safe_payload, ensure_ascii=False),
                    ),
                )
                connection.commit()

    def get_diagnostics(self, minutes: int = 120, limit: int = 20) -> dict[str, Any]:
        now = time.time()
        window_start = now - max(1, minutes) * 60

        with self._connect() as connection:
            total_events = connection.execute(
                "SELECT COUNT(*) AS c FROM events"
            ).fetchone()["c"]
            window_events = connection.execute(
                "SELECT COUNT(*) AS c FROM events WHERE ts >= ?",
                (window_start,),
            ).fetchone()["c"]

            rows = connection.execute(
                """
                SELECT event_name, COUNT(*) AS c
                FROM events
                WHERE ts >= ?
                GROUP BY event_name
                ORDER BY c DESC
                """,
                (window_start,),
            ).fetchall()
            counts_by_event = {row["event_name"]: row["c"] for row in rows}

            error_rows = connection.execute(
                """
                SELECT event_name, message, COUNT(*) AS c
                FROM events
                WHERE ts >= ?
                  AND event_name IN ('ERROR', 'GEMINI_ERROR', 'BLOQUEADO', 'EXPIROU')
                GROUP BY event_name, message
                ORDER BY c DESC
                LIMIT ?
                """,
                (window_start, limit),
            ).fetchall()

            recent_errors = connection.execute(
                """
                SELECT ts, event_name, game, message
                FROM events
                WHERE ts >= ?
                  AND event_name IN ('ERROR', 'GEMINI_ERROR', 'BLOQUEADO', 'EXPIROU')
                ORDER BY ts DESC
                LIMIT ?
                """,
                (window_start, limit),
            ).fetchall()

        detected = counts_by_event.get("DETECTADO", 0)
        blocked = counts_by_event.get("BLOQUEADO", 0)
        expired = counts_by_event.get("EXPIROU", 0)
        generic_errors = counts_by_event.get("ERROR", 0) + counts_by_event.get("GEMINI_ERROR", 0)
        risk_denominator = max(1, detected)

        return {
            "window_minutes": minutes,
            "window_start_ts": window_start,
            "now_ts": now,
            "total_events": total_events,
            "window_events": window_events,
            "counts_by_event": counts_by_event,
            "risk_metrics": {
                "blocked_rate_vs_detected": round(blocked / risk_denominator, 4),
                "expired_rate_vs_detected": round(expired / risk_denominator, 4),
                "error_rate_vs_detected": round(generic_errors / risk_denominator, 4),
            },
            "top_error_patterns": [
                {
                    "event": row["event_name"],
                    "message": row["message"],
                    "count": row["c"],
                }
                for row in error_rows
            ],
            "recent_errors": [
                {
                    "ts": row["ts"],
                    "event": row["event_name"],
                    "game": row["game"],
                    "message": row["message"],
                }
                for row in recent_errors
            ],
        }
