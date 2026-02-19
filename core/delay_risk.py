#!/usr/bin/env python3
"""
Risk filter for in-play bet acceptance delay.
"""


def evaluate_delay_risk(tipo_pontuacao: int, original_stake: float, config: dict) -> dict:
    risk_cfg = config.get("risk_filters", {})
    enabled = bool(risk_cfg.get("enabled", True))
    if not enabled:
        return {
            "should_execute": True,
            "adjusted_stake": original_stake,
            "ev_after_delay": None,
            "reason": "risk_filter_disabled",
        }

    delay_seconds = float(risk_cfg.get("bet_delay_seconds", 5.0))
    min_ev_after_delay = float(risk_cfg.get("min_ev_after_delay", 0.01))
    ev_decay_per_second = float(risk_cfg.get("ev_decay_per_second", 0.01))

    edge_map = risk_cfg.get("ev_edge_by_points", {"2": 0.06, "3": 0.09})
    base_edge = float(edge_map.get(str(tipo_pontuacao), 0.03))

    ev_after_delay = base_edge - (delay_seconds * ev_decay_per_second)

    if ev_after_delay < min_ev_after_delay:
        return {
            "should_execute": False,
            "adjusted_stake": 0.0,
            "ev_after_delay": ev_after_delay,
            "reason": "ev_below_threshold_after_delay",
        }

    if not risk_cfg.get("stake_scale_with_ev", True):
        return {
            "should_execute": True,
            "adjusted_stake": original_stake,
            "ev_after_delay": ev_after_delay,
            "reason": "approved_fixed_stake",
        }

    min_stake_factor = float(risk_cfg.get("min_stake_factor", 0.4))
    max_stake_factor = float(risk_cfg.get("max_stake_factor", 1.2))

    stake_factor = ev_after_delay / max(min_ev_after_delay, 1e-6)
    stake_factor = max(min_stake_factor, min(max_stake_factor, stake_factor))
    adjusted_stake = round(original_stake * stake_factor, 2)

    return {
        "should_execute": True,
        "adjusted_stake": adjusted_stake,
        "ev_after_delay": ev_after_delay,
        "reason": "approved_scaled_stake",
    }
