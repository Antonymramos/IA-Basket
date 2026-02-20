

import asyncio
import json
import os
import threading
import time
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path
from typing import Optional

from backend.analytics_store import AnalyticsStore
from core.orquestrador import Orquestrador


class BotController:
    def __init__(self, config_path: str, gemini_api_key: Optional[str]):
        self.config_path = config_path
        self.gemini_api_key = gemini_api_key
        project_root = Path(config_path).resolve().parents[0]
        self.analytics_store = AnalyticsStore(str(project_root / "data" / "analytics.db"))
        self.thread = None
        self.stop_event = threading.Event()
        self.logs = deque(maxlen=500)
        self.running = False
        self.last_event_at = None
        self.watchdog_thread = None
        self.watchdog_stop = threading.Event()
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
        self.last_event_at = time.time()
        selected_game = None
        try:
            selected_game = self._load_config().get("selected_game")
        except Exception:
            selected_game = None
        try:
            self.analytics_store.record_event(event_name, payload, selected_game)
        except Exception:
            pass
        self._maybe_notify(event_name, payload)
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
        self.watchdog_stop.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog_thread.start()
        self.running = True
        self.last_event_at = time.time()
        self._log_handler("CONTROL", {"action": "start"})

    def stop(self) -> None:
        if not self.running:
            return
        self.stop_event.set()
        self.watchdog_stop.set()
        self.running = False
        self._log_handler("CONTROL", {"action": "stop"})

    def _run_loop(self) -> None:
        try:
            config = self._load_config()
            orchestrator = Orquestrador(
                config,
                self.gemini_api_key,
                stop_event=self.stop_event,
                event_handler=self._log_handler,
                config_path=self.config_path,
            )
            asyncio.run(orchestrator.run())
        except Exception as exc:
            self._log_handler("ERROR", {"message": str(exc)})
        finally:
            self.running = False

    def _watchdog_loop(self) -> None:
        while not self.watchdog_stop.is_set():
            time.sleep(2.0)
            if not self.running:
                continue

            try:
                config = self._load_config()
            except Exception:
                continue

            watchdog_enabled = bool(config.get("watchdog_enabled", True))
            if not watchdog_enabled:
                continue

            timeout_seconds = float(config.get("watchdog_timeout_seconds", 20.0))
            restart_on_stall = bool(config.get("watchdog_restart_on_stall", True))

            if self.last_event_at is None:
                continue

            stalled = (time.time() - self.last_event_at) > timeout_seconds
            if not stalled:
                continue

            self._log_handler(
                "WATCHDOG",
                {
                    "reason": "no_events",
                    "timeout_seconds": timeout_seconds,
                    "restart": restart_on_stall,
                },
            )

            if not restart_on_stall:
                continue

            self.stop_event.set()
            time.sleep(1.0)
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            self.last_event_at = time.time()

    def _maybe_notify(self, event_name: str, payload: dict) -> None:
        try:
            config = self._load_config()
        except Exception:
            return

        notify_cfg = config.get("notifications", {})
        if not bool(notify_cfg.get("telegram_enabled", False)):
            return

        chat_id = str(notify_cfg.get("telegram_chat_id", "")).strip()
        token = str(notify_cfg.get("telegram_bot_token", "")).strip()
        if not chat_id or not token:
            return

        allowed = set(notify_cfg.get("events", ["DETECTADO", "APOSTOU", "AUTH_REQUIRED", "AUTO_STOP", "WATCHDOG"]))
        if event_name not in allowed:
            return

        msg = f"[{event_name}] {json.dumps(payload, ensure_ascii=False)}"
        encoded = urllib.parse.urlencode({"chat_id": chat_id, "text": msg}).encode("utf-8")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        req = urllib.request.Request(url, data=encoded, method="POST")
        try:
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            return

    def set_auto_bet(self, enabled: bool) -> None:
        config = self._load_config()
        config["auto_bet_enabled"] = bool(enabled)
        self._save_config(config)
        self._log_handler("CONTROL", {"action": "auto_bet", "enabled": bool(enabled)})

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

        automation_cfg = config.get("automation", {})
        auto_fill_backend_fields = bool(automation_cfg.get("auto_fill_backend_fields", True))
        selected_game = str(config.get("selected_game", "")).strip()
        if auto_fill_backend_fields and selected_game:
            scores = config.get("game_scores", {})
            if selected_game not in scores:
                default_score = float(config.get("min_game_score", 0) or 0)
                scores[selected_game] = default_score
            config["game_scores"] = scores

            whitelist = set(config.get("whitelist_games", []))
            whitelist.add(selected_game)
            config["whitelist_games"] = sorted(whitelist)

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

    def get_diagnostics(self, minutes: int = 120, limit: int = 20) -> dict:
        diagnostics = self.analytics_store.get_diagnostics(minutes=minutes, limit=limit)
        diagnostics["runtime"] = self.get_report()
        diagnostics["status"] = self.get_status()
        return diagnostics
