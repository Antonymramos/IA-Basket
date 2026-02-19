#!/usr/bin/env python3
"""
Orquestrador - Main loop for monitoring and decision making
"""

import asyncio
import time
from datetime import datetime
from core.gemini_brain import GeminiBrain
from core.decision_engine import analyze_discrepancy
from core.delay_risk import evaluate_delay_risk
from core.tools_registry import registrar_discrepancia, executar_aposta_live
from data_ingestion.live_feed_client import LiveFeedClient
from data_ingestion.bet_scraper import BetScraper
from data_ingestion.simulated_feeds import SimulatedFeedClient

class Orquestrador:
    def __init__(self, config, gemini_api_key=None, stop_event=None, event_handler=None, config_path=None):
        self.config = config
        self.mode = config.get("mode", "live")
        self.decision_engine = config.get("decision_engine", "gemini")
        self.auto_bet_enabled = bool(config.get("auto_bet_enabled", False))
        self.loop_interval = float(config.get("loop_interval_seconds", 0.5))
        self.max_iterations = config.get("max_iterations")
        self.signal_ttl_seconds = float(config.get("signal_ttl_seconds", 8.0))
        self.cooldown_seconds = float(config.get("cooldown_seconds", 6.0))
        self.last_state_signature = None
        self.last_action_by_key = {}
        self.stop_event = stop_event
        self.event_handler = event_handler
        self.config_path = config_path

        if self.decision_engine in ("gemini", "compare"):
            if not gemini_api_key:
                raise RuntimeError("decision_engine gemini/compare exige GEMINI_API_KEY no .env")
            self.gemini = GeminiBrain(gemini_api_key, config.get("gemini_model"))
        else:
            self.gemini = None

        if self.mode == "simulation":
            simulation = config.get("simulation", {})
            transmission_scores = simulation.get(
                "transmission_scores",
                [
                    {"team_a": 100, "team_b": 98},
                    {"team_a": 102, "team_b": 98},
                    {"team_a": 102, "team_b": 101},
                    {"team_a": 105, "team_b": 101}
                ]
            )
            bet_scores = simulation.get(
                "bet_scores",
                [
                    {"team_a": 100, "team_b": 98},
                    {"team_a": 100, "team_b": 98},
                    {"team_a": 102, "team_b": 98},
                    {"team_a": 102, "team_b": 101}
                ]
            )
            self.live_feed = SimulatedFeedClient(transmission_scores)
            self.bet_scraper = SimulatedFeedClient(bet_scores)
        else:
            ws_url = str(config.get("live_feed_ws_url", ""))
            if not (ws_url.startswith("ws://") or ws_url.startswith("wss://")):
                raise RuntimeError(
                    "Fonte de transmissão em modo live deve ser WebSocket rápido (ws:// ou wss://)."
                )
            self.live_feed = LiveFeedClient(config['live_feed_ws_url'])
            self.bet_scraper = BetScraper(config['bet_url'])

    def _refresh_config(self):
        if not self.config_path:
            return
        try:
            import json
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception:
            return

        self.auto_bet_enabled = bool(self.config.get("auto_bet_enabled", False))
        self.signal_ttl_seconds = float(self.config.get("signal_ttl_seconds", 8.0))
        self.cooldown_seconds = float(self.config.get("cooldown_seconds", 6.0))

    def _log_event(self, event_name, **fields):
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        payload = " ".join([f"{key}={value}" for key, value in fields.items()])
        print(f"[{timestamp}] [{event_name}] {payload}".strip())
        if self.event_handler:
            self.event_handler(event_name, {"timestamp": timestamp, **fields})

    def _with_signal_metadata(self, result, transmission_data, bet_data):
        if result.get("action") != "executar_aposta_live":
            return result

        enriched = dict(result)
        now = time.time()
        t_a = int(transmission_data.get("team_a", 0))
        t_b = int(transmission_data.get("team_b", 0))
        b_a = int(bet_data.get("team_a", 0))
        b_b = int(bet_data.get("team_b", 0))
        signal_id = (
            f"{enriched.get('time_alvo')}_{enriched.get('tipo_pontuacao')}_"
            f"T{t_a}-{t_b}_B{b_a}-{b_b}"
        )
        enriched["signal_id"] = signal_id
        enriched["detected_at"] = now
        enriched["expires_at"] = now + self.signal_ttl_seconds

        self._log_event(
            "DETECTADO",
            signal_id=signal_id,
            time_alvo=enriched.get("time_alvo"),
            tipo_pontuacao=enriched.get("tipo_pontuacao"),
            ttl_seconds=self.signal_ttl_seconds,
        )
        return enriched

    def _process_local_rules(self, transmission_data, bet_data):
        state_signature = (
            transmission_data.get("team_a", 0),
            transmission_data.get("team_b", 0),
            bet_data.get("team_a", 0),
            bet_data.get("team_b", 0),
        )

        if state_signature == self.last_state_signature:
            print("Estado repetido, sem nova ação.")
            return

        self.last_state_signature = state_signature
        result = analyze_discrepancy(transmission_data, bet_data)
        result = self._with_signal_metadata(result, transmission_data, bet_data)
        self._dispatch_action(result, transmission_data, bet_data)

    def _dispatch_action(self, result, transmission_data, bet_data):
        action = result.get("action")

        if action == "gemini_error":
            self._log_event("GEMINI_ERROR", error=result.get("error"))
        elif action == "executar_aposta_live":
            signal_id = result.get("signal_id", "unknown")
            detected_at = float(result.get("detected_at", time.time()))
            expires_at = float(result.get("expires_at", detected_at + self.signal_ttl_seconds))
            acceptance_delay = float(self.config.get("risk_filters", {}).get("bet_delay_seconds", 0.0))
            now = time.time()

            if now > expires_at or (now + acceptance_delay) > expires_at:
                self._log_event(
                    "EXPIROU",
                    signal_id=signal_id,
                    age_seconds=round(now - detected_at, 3),
                    acceptance_delay=acceptance_delay,
                    ttl_seconds=self.signal_ttl_seconds,
                )
                return

            block_reason = self._check_policy_blocks(result, now)
            if block_reason:
                self._log_event(
                    "BLOQUEADO",
                    signal_id=signal_id,
                    motivo=block_reason["reason"],
                    **block_reason.get("meta", {})
                )
                return

            if not self.auto_bet_enabled:
                self._log_event(
                    "BLOQUEADO",
                    signal_id=signal_id,
                    motivo="auto_bet_off",
                    time_alvo=result.get("time_alvo"),
                    tipo_pontuacao=result.get("tipo_pontuacao"),
                )
                return

            original_stake = float(result.get("valor_stake", self.config.get("stake", 10.0)))
            risk_result = evaluate_delay_risk(
                tipo_pontuacao=int(result.get("tipo_pontuacao", 0)),
                original_stake=original_stake,
                config=self.config,
            )

            if not risk_result["should_execute"]:
                self._log_event(
                    "BLOQUEADO",
                    signal_id=signal_id,
                    motivo=risk_result.get("reason"),
                    ev_after_delay=risk_result.get("ev_after_delay"),
                    time_alvo=result.get("time_alvo"),
                    tipo_pontuacao=result.get("tipo_pontuacao"),
                )
                return

            adjusted_stake = float(risk_result["adjusted_stake"])
            self._log_event(
                "APOSTOU",
                signal_id=signal_id,
                time_alvo=result.get("time_alvo"),
                tipo_pontuacao=result.get("tipo_pontuacao"),
                ev_after_delay=risk_result.get("ev_after_delay"),
                stake=adjusted_stake,
            )

            action_key = self._cooldown_key(result)
            self.last_action_by_key[action_key] = now

            executar_aposta_live(
                time_alvo=result["time_alvo"],
                tipo_pontuacao=result["tipo_pontuacao"],
                valor_stake=adjusted_stake
            )
        elif action == "registrar_discrepancia":
            registrar_discrepancia(
                time_alvo=result["time_alvo"],
                tipo_pontuacao=result["tipo_pontuacao"],
                transmissao_score=transmission_data,
                bet_score=bet_data,
            )
        else:
            print(f"Sem discrepância | transmissão={transmission_data} | bet={bet_data}")

    def _cooldown_key(self, result):
        selected_game = str(self.config.get("selected_game", "")).strip()
        time_alvo = result.get("time_alvo", "Team A")
        tipo = result.get("tipo_pontuacao", 0)
        return f"{selected_game}:{time_alvo}:{tipo}"

    def _check_policy_blocks(self, result, now):
        selected_game = str(self.config.get("selected_game", "")).strip()
        whitelist_enabled = bool(self.config.get("whitelist_enabled", False))
        whitelist_games = set(self.config.get("whitelist_games", []))

        if whitelist_enabled:
            if not selected_game:
                return {"reason": "whitelist_empty", "meta": {"detalhe": "sem_jogo"}}
            if selected_game not in whitelist_games:
                return {"reason": "whitelist_block", "meta": {"jogo": selected_game}}

        min_game_score = float(self.config.get("min_game_score", 0) or 0)
        if selected_game and min_game_score > 0:
            game_scores = self.config.get("game_scores", {})
            score = game_scores.get(selected_game)
            if score is not None and float(score) < min_game_score:
                return {
                    "reason": "score_below_threshold",
                    "meta": {"score": score, "min_score": min_game_score},
                }

        if self.cooldown_seconds > 0:
            key = self._cooldown_key(result)
            last_at = self.last_action_by_key.get(key)
            if last_at and (now - last_at) < self.cooldown_seconds:
                return {
                    "reason": "cooldown_active",
                    "meta": {
                        "cooldown_seconds": self.cooldown_seconds,
                        "elapsed": round(now - last_at, 2),
                    },
                }

        return None

    def _process_gemini(self, transmission_data, bet_data):
        state_signature = (
            transmission_data.get("team_a", 0),
            transmission_data.get("team_b", 0),
            bet_data.get("team_a", 0),
            bet_data.get("team_b", 0),
        )

        if state_signature == self.last_state_signature:
            print("Estado repetido, sem nova ação.")
            return

        self.last_state_signature = state_signature
        result = self.gemini.suggest_action(
            transmission_data,
            bet_data,
            float(self.config.get("stake", 10.0))
        )
        result = self._with_signal_metadata(result, transmission_data, bet_data)
        self._dispatch_action(result, transmission_data, bet_data)

    def _process_compare(self, transmission_data, bet_data):
        state_signature = (
            transmission_data.get("team_a", 0),
            transmission_data.get("team_b", 0),
            bet_data.get("team_a", 0),
            bet_data.get("team_b", 0),
        )

        if state_signature == self.last_state_signature:
            print("Estado repetido, sem nova ação.")
            return

        self.last_state_signature = state_signature
        local_result = analyze_discrepancy(transmission_data, bet_data)
        gemini_result = self.gemini.suggest_action(
            transmission_data,
            bet_data,
            float(self.config.get("stake", 10.0))
        )

        local_result = self._with_signal_metadata(local_result, transmission_data, bet_data)
        gemini_result = self._with_signal_metadata(gemini_result, transmission_data, bet_data)

        local_signature = (
            local_result.get("action"),
            local_result.get("time_alvo"),
            local_result.get("tipo_pontuacao"),
        )
        gemini_signature = (
            gemini_result.get("action"),
            gemini_result.get("time_alvo"),
            gemini_result.get("tipo_pontuacao"),
        )
        is_match = local_signature == gemini_signature
        gemini_available = gemini_result.get("action") != "gemini_error"

        self._log_event(
            "COMPARE",
            local_action=local_result.get("action"),
            gemini_action=gemini_result.get("action"),
            gemini_available=gemini_available,
            match=is_match,
        )

        compare_execute = self.config.get("compare_execute", "local_rules")
        if compare_execute == "gemini":
            self._dispatch_action(gemini_result, transmission_data, bet_data)
        elif compare_execute == "none":
            print("[COMPARE] Modo avaliação: nenhuma ação executada.")
        else:
            self._dispatch_action(local_result, transmission_data, bet_data)
    
    async def run(self):
        """
        Main monitoring loop
        """
        auto_bet_mode = "ON" if self.auto_bet_enabled else "OFF"
        print(
            f"Iniciando monitoramento | mode={self.mode} "
            f"| decision_engine={self.decision_engine} "
            f"| auto_bet={auto_bet_mode}"
        )

        iteration = 0
        while True:
            if self.stop_event and self.stop_event.is_set():
                self._log_event("STOP", motivo="stop_event")
                break
            if self.max_iterations is not None and iteration >= int(self.max_iterations):
                print("Monitoramento finalizado (max_iterations atingido).")
                break

            self._refresh_config()

            # Get data from both sources
            transmission_data = await self.live_feed.get_score()
            bet_data = await self.bet_scraper.get_score()
            self._log_event(
                "TICK",
                idx=iteration + 1,
                transmissao=transmission_data,
                bet=bet_data,
            )

            if self.decision_engine == "gemini":
                self._process_gemini(transmission_data, bet_data)
            elif self.decision_engine == "compare":
                self._process_compare(transmission_data, bet_data)
            else:
                self._process_local_rules(transmission_data, bet_data)

            iteration += 1
            # Wait before next check
            await asyncio.sleep(self.loop_interval)