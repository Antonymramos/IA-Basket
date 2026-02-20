#!/usr/bin/env python3
"""
Orquestrador - Main loop for monitoring and decision making
"""

import asyncio
import time
from pathlib import Path
from datetime import datetime
from core.gemini_brain import GeminiBrain
from core.analytics_context import build_gemini_context
from core.decision_engine import analyze_discrepancy
from core.delay_risk import evaluate_delay_risk
from core.delay_learning import DelayLearningModel
from core.feedback_loop import FeedbackLoop
from core.nba_knowledge import NBAKnowledge
from core.tools_registry import registrar_discrepancia, executar_aposta_live
from data_ingestion.live_feed_client import LiveFeedClient, HttpLiveFeedClient, BllsportNetworkFeedClient
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
        self.pending_signals = {}
        self.delay_model = DelayLearningModel(config)
        self.blocked_streak = 0
        self.bets_in_session = 0
        self.feed_warning_count = 0
        self.stop_event = stop_event
        self.event_handler = event_handler
        self.config_path = config_path
        if config_path:
            root = Path(config_path).resolve().parents[0]
            self.analytics_db_path = str(root / "data" / "analytics.db")
            self.feedback_db_path = str(root / "data" / "feedback_loop.db")
            self.nba_db_path = str(root / "data" / "nba_knowledge.db")
        else:
            self.analytics_db_path = str(Path("data") / "analytics.db")
            self.feedback_db_path = str(Path("data") / "feedback_loop.db")
            self.nba_db_path = str(Path("data") / "nba_knowledge.db")
        self.feedback_loop = FeedbackLoop(self.feedback_db_path)
        self.nba_knowledge = NBAKnowledge(self.nba_db_path)
        self.automation_cfg = config.get("automation", {})
        self.stop_on_auth_required = bool(self.automation_cfg.get("stop_on_auth_required", True))
        self.max_feed_warnings = int(self.automation_cfg.get("max_feed_warnings", 30))
        self.max_bets_per_session = int(self.automation_cfg.get("max_bets_per_session", 50))
        self.max_blocked_streak = int(self.automation_cfg.get("max_blocked_streak", 40))        
        # Safe mode watchdog: tracks consecutive high-delay alerts
        self.consecutive_high_delays = 0
        self.safe_mode_enabled = False
        self.safe_mode_triggered_at = None
        self.safe_mode_recovery_minutes = 10  # Recover after 10 minutes without high delays
        if self.decision_engine in ("gemini", "compare"):
            if not gemini_api_key:
                raise RuntimeError("decision_engine gemini/compare exige GEMINI_API_KEY no .env")
            # Ativar ensemble voting para máxima precisão com Few-Shot learning + NBA context
            self.gemini = GeminiBrain(
                gemini_api_key, 
                config.get("gemini_model"),
                ensemble_mode=True,  # Múltiplos modelos votando
                confidence_threshold=0.70,  # Mínimo 70% consenso
                feedback_loop=self.feedback_loop,  # Injetar exemplos de sucesso no prompt
                nba_knowledge=self.nba_knowledge  # Injetar contexto NBA no prompt
            )
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
            transmission_provider = str(config.get("transmission_provider", "live_ws"))
            feed_url = str(config.get("live_feed_ws_url", ""))

            if transmission_provider == "bllsport_net":
                if not (feed_url.startswith("http://") or feed_url.startswith("https://")):
                    raise RuntimeError(
                        "Fonte bllsport_net deve ser URL HTTP(S)."
                    )
                user_data_dir = self.config.get("live_feed_user_data_dir")
                headless = bool(self.config.get("live_feed_headless", True))
                self.live_feed = BllsportNetworkFeedClient(
                    feed_url,
                    user_data_dir=user_data_dir,
                    headless=headless,
                )
            elif transmission_provider == "live_http":
                if not (feed_url.startswith("http://") or feed_url.startswith("https://")):
                    raise RuntimeError(
                        "Fonte live_http deve ser URL HTTP(S)."
                    )
                user_data_dir = self.config.get("live_feed_user_data_dir")
                headless = bool(self.config.get("live_feed_headless", True))
                self.live_feed = HttpLiveFeedClient(
                    feed_url,
                    user_data_dir=user_data_dir,
                    headless=headless,
                )
            else:
                if not (feed_url.startswith("ws://") or feed_url.startswith("wss://")):
                    raise RuntimeError(
                        "Fonte de transmissão em modo live_ws deve ser WebSocket rápido (ws:// ou wss://)."
                    )
                self.live_feed = LiveFeedClient(feed_url)

            bet_provider = str(config.get("bet_provider", "bet365_playwright"))
            if bet_provider == "bet_mock":
                simulation = config.get("simulation", {})
                bet_scores = simulation.get(
                    "bet_scores",
                    [
                        {"team_a": 100, "team_b": 98},
                        {"team_a": 100, "team_b": 98},
                        {"team_a": 102, "team_b": 98},
                        {"team_a": 102, "team_b": 101},
                    ],
                )
                self.bet_scraper = SimulatedFeedClient(bet_scores)
            else:
                bet_user_data_dir = self.config.get("bet_user_data_dir")
                bet_headless = bool(self.config.get("bet_headless", True))
                self.bet_scraper = BetScraper(
                    config['bet_url'],
                    user_data_dir=bet_user_data_dir,
                    headless=bet_headless,
                )

    def _build_gemini_memory_context(self):
        try:
            return build_gemini_context(self.analytics_db_path, minutes=120, limit=12)
        except Exception as exc:
            return f"Falha ao carregar contexto histórico: {exc}"

    def _refresh_config(self):
        if not self.config_path:
            return
        try:
            import json
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception:
            return

    def _log_ensemble_decision(self, result, game=None):
        """Registra decisão de ensemble voting com detalhes de consenso."""
        if not result.get("ensemble_mode"):
            return
        
        consensus_strength = result.get("consensus_strength", 0.0)
        votes_count = result.get("votes_count", 0)
        votes_for_action = result.get("votes_for_action", 0)
        action = result.get("action", "none")
        
        event_name = "ENSEMBLE_CONSENSUS" if consensus_strength >= 0.70 else "ENSEMBLE_WEAK"
        
        self._log_event(
            event_name,
            action=action,
            consensus_strength=round(consensus_strength, 3),
            votes_count=votes_count,
            votes_for_action=votes_for_action,
            threshold=0.70,
            game=game,
        )
        self.auto_bet_enabled = bool(self.config.get("auto_bet_enabled", False))
        self.signal_ttl_seconds = float(self.config.get("signal_ttl_seconds", 8.0))
        self.cooldown_seconds = float(self.config.get("cooldown_seconds", 6.0))
        self.automation_cfg = self.config.get("automation", {})
        self.stop_on_auth_required = bool(self.automation_cfg.get("stop_on_auth_required", True))
        self.max_feed_warnings = int(self.automation_cfg.get("max_feed_warnings", 30))
        self.max_bets_per_session = int(self.automation_cfg.get("max_bets_per_session", 50))
        self.max_blocked_streak = int(self.automation_cfg.get("max_blocked_streak", 40))

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
        diff_a = t_a - b_a
        diff_b = t_b - b_b
        signal_id = (
            f"{enriched.get('time_alvo')}_{enriched.get('tipo_pontuacao')}_"
            f"T{t_a}-{t_b}_B{b_a}-{b_b}"
        )
        enriched["signal_id"] = signal_id
        enriched["detected_at"] = now
        enriched["expires_at"] = now + self.signal_ttl_seconds
        enriched["source"] = transmission_data.get("source", "unknown")

        self._log_event(
            "DESYNC",
            signal_id=signal_id,
            time_alvo=enriched.get("time_alvo"),
            tipo_pontuacao=enriched.get("tipo_pontuacao"),
            diff_a=diff_a,
            diff_b=diff_b,
            t_a=t_a,
            t_b=t_b,
            b_a=b_a,
            b_b=b_b,
            source=enriched.get("source"),
        )

        self._log_event(
            "DETECTADO",
            signal_id=signal_id,
            time_alvo=enriched.get("time_alvo"),
            tipo_pontuacao=enriched.get("tipo_pontuacao"),
            ttl_seconds=self.signal_ttl_seconds,
        )

        self.pending_signals[signal_id] = {
            "detected_at": now,
            "time_alvo": enriched.get("time_alvo"),
            "tipo_pontuacao": int(enriched.get("tipo_pontuacao", 2)),
            "target_score": {
                "team_a": int(transmission_data.get("team_a", 0)),
                "team_b": int(transmission_data.get("team_b", 0)),
            },
            "source": str(transmission_data.get("source", "unknown")),
            "pending_logged": False,
        }
        return enriched

    def _update_delay_learning(self, bet_data):
        if not self.pending_signals:
            return

        now = time.time()
        delay_alert = float(self.config.get("risk_filters", {}).get("bet_delay_seconds", 5.0))
        safe_mode_threshold = delay_alert + 3.0  # Safe mode triggers if delay > threshold + 3s
        consecutive_threshold = 5  # If 5+ consecutive DELAY_PENDING, enable safe mode
        resolved = []
        bet_a = int(bet_data.get("team_a", 0))
        bet_b = int(bet_data.get("team_b", 0))

        high_delay_detected = False

        for signal_id, data in self.pending_signals.items():
            target_a = int(data["target_score"].get("team_a", 0))
            target_b = int(data["target_score"].get("team_b", 0))
            time_alvo = data.get("time_alvo", "Team A")

            resolved_now = bet_a >= target_a if time_alvo == "Team A" else bet_b >= target_b
            if not resolved_now:
                pending_age = now - float(data.get("detected_at", now))
                if pending_age >= delay_alert and not data.get("pending_logged"):
                    data["pending_logged"] = True
                    self._log_event(
                        "DELAY_PENDING",
                        signal_id=signal_id,
                        age_seconds=round(pending_age, 3),
                        delay_threshold=delay_alert,
                        time_alvo=time_alvo,
                        tipo_pontuacao=data.get("tipo_pontuacao"),
                        target_a=target_a,
                        target_b=target_b,
                        bet_a=bet_a,
                        bet_b=bet_b,
                        source=str(data.get("source", "unknown")),
                    )
                    
                    # Check if delay is critically high
                    if pending_age >= safe_mode_threshold:
                        high_delay_detected = True
                
                continue

            lag_seconds = max(0.01, now - float(data.get("detected_at", now)))
            point_gap = int(data.get("tipo_pontuacao", 2))
            source = str(data.get("source", "unknown"))
            self.delay_model.add_sample(lag_seconds, point_gap, source)
            stats = self.delay_model.stats()
            self._log_event(
                "DELAY_RESOLVED",
                signal_id=signal_id,
                lag_seconds=round(lag_seconds, 3),
                point_gap=point_gap,
                source=source,
                bet_a=bet_a,
                bet_b=bet_b,
                target_a=target_a,
                target_b=target_b,
            )
            self._log_event(
                "DELAY_LEARN",
                signal_id=signal_id,
                lag_seconds=round(lag_seconds, 3),
                point_gap=point_gap,
                source=source,
                samples=stats.get("samples", 0),
                avg_delay=stats.get("avg_delay"),
            )
            resolved.append(signal_id)
            
            # Reset consecutive_high_delays on successful resolution
            if lag_seconds <= delay_alert:
                self.consecutive_high_delays = 0

        for signal_id in resolved:
            self.pending_signals.pop(signal_id, None)
        
        # Safe mode watchdog logic
        if high_delay_detected:
            self.consecutive_high_delays += 1
            print(f"[SAFETY] High delay detected. Consecutive: {self.consecutive_high_delays}/{consecutive_threshold}")
            
            if self.consecutive_high_delays >= consecutive_threshold and not self.safe_mode_enabled:
                self.safe_mode_enabled = True
                self.safe_mode_triggered_at = now
                self._log_event(
                    "SAFE_MODE_ENABLED",
                    reason="Consecutive high delays detected",
                    consecutive_count=self.consecutive_high_delays,
                    threshold=consecutive_threshold,
                    previous_auto_bet=self.auto_bet_enabled,
                )
                print("[SAFETY] SAFE MODE ENABLED: Auto-bet disabled due to high delays")
                self.auto_bet_enabled = False
        else:
            self.consecutive_high_delays = 0
        
        # Safe mode recovery: disable safe mode after 10 minutes without high delays
        if self.safe_mode_enabled and self.safe_mode_triggered_at:
            recovery_seconds = self.safe_mode_recovery_minutes * 60
            if now - self.safe_mode_triggered_at >= recovery_seconds:
                self.safe_mode_enabled = False
                self._log_event(
                    "SAFE_MODE_RECOVERED",
                    reason=f"No high delays for {self.safe_mode_recovery_minutes} minutes",
                    recovery_time_seconds=round(now - self.safe_mode_triggered_at, 1),
                    auto_bet_re_enabled=True,
                )
                print("[SAFETY] SAFE MODE RECOVERED: Auto-bet can be re-enabled")
                # Note: Not automatically re-enabling; user should confirm

    def _check_auth_required(self, transmission_data, bet_data):
        transmission_auth = bool(transmission_data.get("auth_required", False))
        bet_auth = bool(bet_data.get("auth_required", False))
        if not (transmission_auth or bet_auth):
            return

        self._log_event(
            "AUTH_REQUIRED",
            transmission_auth=transmission_auth,
            bet_auth=bet_auth,
            transmission_source=transmission_data.get("source"),
            bet_source=bet_data.get("source"),
        )

        if self.stop_on_auth_required and self.stop_event:
            self.stop_event.set()

    def _should_force_stop(self):
        if self.max_feed_warnings > 0 and self.feed_warning_count >= self.max_feed_warnings:
            return "max_feed_warnings"
        if self.max_bets_per_session > 0 and self.bets_in_session >= self.max_bets_per_session:
            return "max_bets_per_session"
        if self.max_blocked_streak > 0 and self.blocked_streak >= self.max_blocked_streak:
            return "max_blocked_streak"
        return None

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
                self.blocked_streak += 1
                self._log_event(
                    "BLOQUEADO",
                    signal_id=signal_id,
                    motivo=block_reason["reason"],
                    **block_reason.get("meta", {})
                )
                return

            if not self.auto_bet_enabled:
                self.blocked_streak += 1
                reason = "safe_mode_active" if self.safe_mode_enabled else "auto_bet_off"
                self._log_event(
                    "BLOQUEADO",
                    signal_id=signal_id,
                    motivo=reason,
                    safe_mode_active=self.safe_mode_enabled,
                    time_alvo=result.get("time_alvo"),
                    tipo_pontuacao=result.get("tipo_pontuacao"),
                )
                return

            original_stake = float(result.get("valor_stake", self.config.get("stake", 10.0)))
            base_delay = float(self.config.get("risk_filters", {}).get("bet_delay_seconds", 5.0))
            est_delay, model_used = self.delay_model.estimate_delay(
                point_gap=int(result.get("tipo_pontuacao", 2)),
                source=result.get("source", "unknown"),
                fallback=base_delay,
            )
            risk_result = evaluate_delay_risk(
                tipo_pontuacao=int(result.get("tipo_pontuacao", 0)),
                original_stake=original_stake,
                config=self.config,
                delay_seconds_override=est_delay,
            )

            if not risk_result["should_execute"]:
                self.blocked_streak += 1
                self._log_event(
                    "BLOQUEADO",
                    signal_id=signal_id,
                    motivo=risk_result.get("reason"),
                    ev_after_delay=risk_result.get("ev_after_delay"),
                    delay_seconds_used=risk_result.get("delay_seconds_used"),
                    delay_model_used=model_used,
                    time_alvo=result.get("time_alvo"),
                    tipo_pontuacao=result.get("tipo_pontuacao"),
                )
                return

            self.blocked_streak = 0
            self.bets_in_session += 1
            adjusted_stake = float(risk_result["adjusted_stake"])
            self._log_event(
                "APOSTOU",
                signal_id=signal_id,
                time_alvo=result.get("time_alvo"),
                tipo_pontuacao=result.get("tipo_pontuacao"),
                ev_after_delay=risk_result.get("ev_after_delay"),
                delay_seconds_used=risk_result.get("delay_seconds_used"),
                delay_model_used=model_used,
                stake=adjusted_stake,
            )

            # Record bet execution in feedback loop for learning
            try:
                self.feedback_loop.record_bet_execution(
                    signal_id=signal_id,
                    time_alvo=result.get("time_alvo"),
                    tipo_pontuacao=int(result.get("tipo_pontuacao", 2)),
                    stake=adjusted_stake,
                    ev_score=float(risk_result.get("ev_after_delay", 0.0)),
                    consensus_strength=float(result.get("consensus_strength", 0.5)),
                    point_gap=int(result.get("tipo_pontuacao", 2)),
                    delay_seconds=float(risk_result.get("delay_seconds_used", 0.0)),
                )
            except Exception as e:
                self._log_event("FEEDBACK_ERROR", error=f"Failed to record bet execution: {str(e)}")

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
        memory_context = self._build_gemini_memory_context()
        result = self.gemini.suggest_action(
            transmission_data,
            bet_data,
            float(self.config.get("stake", 10.0)),
            memory_context=memory_context,
        )
        # Log ensemble voting if used
        selected_game = str(self.config.get("selected_game", "")).strip()
        self._log_ensemble_decision(result, game=selected_game)
        
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
        memory_context = self._build_gemini_memory_context()
        gemini_result = self.gemini.suggest_action(
            transmission_data,
            bet_data,
            float(self.config.get("stake", 10.0)),
            memory_context=memory_context,
        )
        
        # Log ensemble voting if used
        selected_game = str(self.config.get("selected_game", "")).strip()
        self._log_ensemble_decision(gemini_result, game=selected_game)

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
        try:
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

                if self.mode == "live" and int(transmission_data.get("team_a", 0)) == 0 and int(transmission_data.get("team_b", 0)) == 0:
                    self.feed_warning_count += 1
                    self._log_event(
                        "FEED_WARNING",
                        motivo="placar_transmissao_nao_extraido",
                        fonte=str(self.config.get("live_feed_ws_url", "")),
                        detalhe=transmission_data.get("source", "unknown"),
                    )

                self._check_auth_required(transmission_data, bet_data)
                self._update_delay_learning(bet_data)

                stop_reason = self._should_force_stop()
                if stop_reason:
                    self._log_event("AUTO_STOP", motivo=stop_reason)
                    if self.stop_event:
                        self.stop_event.set()
                    break

                if self.decision_engine == "gemini":
                    self._process_gemini(transmission_data, bet_data)
                elif self.decision_engine == "compare":
                    self._process_compare(transmission_data, bet_data)
                else:
                    self._process_local_rules(transmission_data, bet_data)

                iteration += 1
                # Wait before next check
                await asyncio.sleep(self.loop_interval)
        finally:
            for resource in (self.live_feed, self.bet_scraper):
                close_method = getattr(resource, "close", None)
                if close_method:
                    result = close_method()
                    if asyncio.iscoroutine(result):
                        await result