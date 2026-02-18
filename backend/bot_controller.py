#!/usr/bin/env python3
"""
Bot controller to manage background execution and logs.
"""

import asyncio
import json
import os
import threading
import time
from collections import deque
from typing import Optional

from core.orquestrador import Orquestrador


class BotController:
    def __init__(self, config_path: str, gemini_api_key: Optional[str]):
        self.config_path = config_path
        self.gemini_api_key = gemini_api_key
        self.thread = None
        self.stop_event = threading.Event()
        self.logs = deque(maxlen=500)
        self.running = False
        self.session_report = {
            "detected": 0,
            "bet": 0,
            "blocked": 0,
            "expired": 0,
            "errors": 0,
            "started_at": None,
        }

    def _load_config(self) -> dict:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_config(self, config: dict) -> None:
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    def _log_handler(self, event_name: str, payload: dict) -> None:
        self.logs.append({"event": event_name, **payload})
        if event_name == "DETECTADO":
            self.session_report["detected"] += 1
        elif event_name == "APOSTOU":
            self.session_report["bet"] += 1
        elif event_name == "BLOQUEADO":
            self.session_report["blocked"] += 1
        elif event_name == "EXPIROU":
            self.session_report["expired"] += 1
        elif event_name in ("GEMINI_ERROR", "ERROR"):
            self.session_report["errors"] += 1

    def start(self) -> None:
        if self.running:
            return

        config = self._load_config()
        config["prompt_auto_bet_on_start"] = False
        self._save_config(config)

        self.session_report = {
            "detected": 0,
            "bet": 0,
            "blocked": 0,
            "expired": 0,
            "errors": 0,
            "started_at": time.time(),
        }

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.running = True

    def stop(self) -> None:
        if not self.running:
            return
        self.stop_event.set()
        self.running = False

    def _run_loop(self) -> None:
        config = self._load_config()
        orchestrator = Orquestrador(
            config,
            self.gemini_api_key,
            stop_event=self.stop_event,
            event_handler=self._log_handler,
            config_path=self.config_path,
        )
        asyncio.run(orchestrator.run())

    def set_auto_bet(self, enabled: bool) -> None:
        config = self._load_config()
        config["auto_bet_enabled"] = bool(enabled)
        self._save_config(config)

    def update_selection(self, updates: dict) -> dict:
        config = self._load_config()
        game_score = updates.pop("game_score", None)
        whitelist_enabled = updates.pop("whitelist_enabled", None)
        min_game_score = updates.pop("min_game_score", None)

        config.update(updates)

        if whitelist_enabled is not None:
            config["whitelist_enabled"] = bool(whitelist_enabled)

        if min_game_score is not None:
            try:
                config["min_game_score"] = float(min_game_score)
            except ValueError:
                pass

        if game_score is not None and config.get("selected_game"):
            scores = config.get("game_scores", {})
            scores[config["selected_game"]] = float(game_score)
            config["game_scores"] = scores

        self._save_config(config)
        return config

    def add_to_whitelist(self, game_name: str) -> dict:
        config = self._load_config()
        whitelist = set(config.get("whitelist_games", []))
        if game_name:
            whitelist.add(game_name)
        config["whitelist_games"] = sorted(whitelist)
        self._save_config(config)
        return config

    def remove_from_whitelist(self, game_name: str) -> dict:
        config = self._load_config()
        whitelist = set(config.get("whitelist_games", []))
        if game_name in whitelist:
            whitelist.remove(game_name)
        config["whitelist_games"] = sorted(whitelist)
        self._save_config(config)
        return config

    def get_status(self) -> dict:
        config = self._load_config()
        return {
            "running": self.running,
            "auto_bet_enabled": bool(config.get("auto_bet_enabled", False)),
            "mode": config.get("mode", "live"),
            "decision_engine": config.get("decision_engine", "gemini"),
            "selected_game": config.get("selected_game"),
            "transmission_provider": config.get("transmission_provider"),
            "bet_provider": config.get("bet_provider"),
            "whitelist_enabled": bool(config.get("whitelist_enabled", False)),
            "whitelist_games": config.get("whitelist_games", []),
            "min_game_score": config.get("min_game_score", 0),
            "game_scores": config.get("game_scores", {}),
            "config": config,
        }

    def get_report(self) -> dict:
        report = dict(self.session_report)
        report["running"] = self.running
        return report

    def get_logs(self, limit: int = 200) -> list:
        items = list(self.logs)[-limit:]
        return items
