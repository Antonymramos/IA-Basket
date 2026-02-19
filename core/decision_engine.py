#!/usr/bin/env python3
"""
Local rule engine for discrepancy detection.
"""

def analyze_discrepancy(transmission_data, bet_data):
    t_a = int(transmission_data.get("team_a", 0))
    t_b = int(transmission_data.get("team_b", 0))
    b_a = int(bet_data.get("team_a", 0))
    b_b = int(bet_data.get("team_b", 0))

    diff_a = t_a - b_a
    diff_b = t_b - b_b

    if diff_a in (2, 3) and diff_b == 0:
        return {
            "action": "executar_aposta_live",
            "time_alvo": "Team A",
            "tipo_pontuacao": diff_a,
        }

    if diff_b in (2, 3) and diff_a == 0:
        return {
            "action": "executar_aposta_live",
            "time_alvo": "Team B",
            "tipo_pontuacao": diff_b,
        }

    return {
        "action": "none"
    }
