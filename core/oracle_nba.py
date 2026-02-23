from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


ERROR_PRIORITY = [
    "LINHA_OK_PLACAR_ATRASADO",
    "3PTS_REGISTRADO_2PTS",
    "LANCE_LIVRE_DELAY",
    "DELAY_GERAL",
    "BUG_CADERNETA",
    "TEMPO_DESYNC",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def parse_score(value: Any) -> dict[str, int] | None:
    """Aceita {Home/Away}, {H/A}, "91-85", "91 : 85"."""
    if value is None:
        return None

    if isinstance(value, dict):
        # aceita Home/Away, H/A
        for left_key, right_key in (("Home", "Away"), ("H", "A"), ("home", "away")):
            if left_key in value and right_key in value:
                try:
                    return {"H": int(value[left_key]), "A": int(value[right_key])}
                except Exception:
                    return None
        # aceita team_a/team_b
        if "team_a" in value and "team_b" in value:
            try:
                return {"H": int(value["team_a"]), "A": int(value["team_b"])}
            except Exception:
                return None

    if isinstance(value, str):
        m = re.search(r"(\d{1,3})\s*[-:]\s*(\d{1,3})", value)
        if m:
            return {"H": int(m.group(1)), "A": int(m.group(2))}

    return None


def parse_clock(value: Any) -> tuple[int | None, int | None]:
    """Retorna (quarter, seconds_remaining). Aceita 'Q1 05:03', 'Q05:03', 'Q3 1:28'."""
    if not value:
        return (None, None)

    if isinstance(value, str):
        s = value.strip().upper()
        m = re.search(r"Q\s*(\d)\s*(\d{1,2}):(\d{2})", s)
        if not m:
            m = re.search(r"Q(\d)\s*(\d{1,2}):(\d{2})", s)
        if m:
            q = int(m.group(1))
            mm = int(m.group(2))
            ss = int(m.group(3))
            return (q, mm * 60 + ss)

    return (None, None)


def _line_indicates_scoring(line: str) -> dict[str, Any] | None:
    """Heurística para identificar linha de pontuação confirmada na Bet365."""
    if not line:
        return None

    raw = line.strip()
    lowered = raw.lower()
    confirmed = any(tok in lowered for tok in ["✓", "registrou", "ok", "green"])
    if not confirmed:
        return None

    # Tipo de ponto
    if "3" in lowered and "pt" in lowered:
        points = 3
        kind = "3 pontos"
    elif "2" in lowered and "pt" in lowered:
        points = 2
        kind = "2 pontos"
    elif "lance livre" in lowered or "free throw" in lowered or "ft" in lowered:
        points = 1
        kind = "1 ponto (lance livre)"
    else:
        points = None
        kind = "pontuação"

    # Tempo na própria linha
    q, sec = parse_clock(raw)

    return {
        "confirmed": True,
        "points": points,
        "kind": kind,
        "clock": raw,
        "quarter": q,
        "seconds": sec,
        "raw": raw,
    }


@dataclass
class OracleInput:
    video_score: dict[str, int] | None
    video_clock: str | None
    bet_score: dict[str, int] | None
    bet_clock: str | None
    bet_lines: list[str]
    official_score: dict[str, int] | None
    official_clock: str | None
    system_latency_ms: float | None = None


def detect_oracle_error(data: OracleInput) -> dict[str, Any]:
    """Retorna diagnóstico (tipo/severidade) baseado em regras técnicas + heurísticas."""

    # Defaults
    erro_detectado = False
    tipo = None
    severidade = "BAIXA"
    detalhes = ""

    v = data.video_score
    b = data.bet_score
    o = data.official_score

    # 0) Falta de dados
    if not v or not b:
        return {
            "erro_detectado": True,
            "tipo": "FALTA_DADOS",
            "severidade": "MEDIA",
            "detalhes_tecnicos": "Não foi possível obter placar/tempo de uma das fontes.",
        }

    vH, vA = v.get("H", 0), v.get("A", 0)
    bH, bA = b.get("H", 0), b.get("A", 0)

    # Base: verdade absoluta preferida (video; se existir oficial, valida)
    truth = v
    if o and abs(o.get("H", 0) - vH) <= 3 and abs(o.get("A", 0) - vA) <= 3:
        truth = o

    tH, tA = truth.get("H", 0), truth.get("A", 0)

    gapH = tH - bH
    gapA = tA - bA

    # 1) LINHA_OK_PLACAR_ATRASADO (prioridade máxima)
    scored_lines = [x for x in ( _line_indicates_scoring(line) for line in data.bet_lines ) if x]
    if scored_lines and (gapH >= 2 or gapA >= 2):
        erro_detectado = True
        tipo = "LINHA_OK_PLACAR_ATRASADO"
        severidade = "CRITICA"
        best_line = scored_lines[0]
        detalhes = (
            f"Linha confirmada na Bet365 mas placar geral atrasado. "
            f"Bet={bH}-{bA} vs Verdade={tH}-{tA}. Linha='{best_line['raw']}'."
        )

    # 2) DELAY_GERAL (>3s) / TEMPO_DESYNC
    if not erro_detectado:
        vq, vsec = parse_clock(data.video_clock)
        bq, bsec = parse_clock(data.bet_clock)
        if vq and bq and vq == bq and vsec is not None and bsec is not None:
            # bet "parado" => segundos não mudam e ficam muito atrás
            delta = bsec - vsec
            if delta >= 4:
                erro_detectado = True
                tipo = "DELAY_GERAL"
                severidade = "ALTA" if delta >= 6 else "MEDIA"
                detalhes = f"Delay de relógio estimado ~{delta}s (Bet atrás do vídeo)."
            elif abs(delta) >= 10:
                erro_detectado = True
                tipo = "TEMPO_DESYNC"
                severidade = "MEDIA"
                detalhes = f"Desync de tempo entre fontes (delta ~{delta}s)."

    # 3) Placar atrasado sem linha confirmada
    if not erro_detectado and (gapH >= 2 or gapA >= 2):
        erro_detectado = True
        tipo = "PLACAR_ATRASADO"
        severidade = "ALTA" if (gapH >= 4 or gapA >= 4) else "MEDIA"
        detalhes = f"Placar Bet365 atrás: Bet={bH}-{bA} vs Verdade={tH}-{tA}."

    return {
        "erro_detectado": bool(erro_detectado),
        "tipo": tipo or "OK",
        "severidade": severidade,
        "detalhes_tecnicos": detalhes or "Sem divergência relevante detectada.",
    }


def build_oracle_output(
    *,
    video_score: Any,
    video_clock: Any,
    bet_score: Any,
    bet_clock: Any,
    bet_lines: Any,
    official_score: Any = None,
    official_clock: Any = None,
    system_status_stream: str = "OK",
    latency_ms: float | None = None,
) -> dict[str, Any]:
    """Monta o JSON rígido para broadcast (sem executar macro automaticamente)."""

    v = parse_score(video_score)
    b = parse_score(bet_score)
    o = parse_score(official_score) if official_score is not None else None

    lines = []
    if isinstance(bet_lines, list):
        lines = [str(x) for x in bet_lines if str(x).strip()]
    elif isinstance(bet_lines, str):
        lines = [bet_lines]

    diagnosis = detect_oracle_error(
        OracleInput(
            video_score=v,
            video_clock=str(video_clock) if video_clock is not None else None,
            bet_score=b,
            bet_clock=str(bet_clock) if bet_clock is not None else None,
            bet_lines=lines,
            official_score=o,
            official_clock=str(official_clock) if official_clock is not None else None,
            system_latency_ms=latency_ms,
        )
    )

    # Confiança simples (heurística)
    confianca = 0.97 if diagnosis["tipo"] == "LINHA_OK_PLACAR_ATRASADO" else 0.85
    if not v or not b:
        confianca = 0.55

    return {
        "timestamp": _now_iso(),
        "server_metrics": {
            "status_stream": system_status_stream,
            "confianca_ia": round(confianca, 2),
            "latencia_processamento_ms": int(latency_ms or 0),
        },
        "analise_live": {
            "placar_real": {"H": (v or {}).get("H", 0), "A": (v or {}).get("A", 0)},
            "tempo_video": str(video_clock or ""),
            "evento": "",
        },
        "diagnostico_saas": {
            "erro_detectado": diagnosis["erro_detectado"],
            "tipo": diagnosis["tipo"],
            "detalhes_tecnicos": diagnosis["detalhes_tecnicos"],
            "severidade": diagnosis["severidade"],
        },
        "comando_cliente": {
            "executar": False,
            "urgencia": "IMEDIATA" if diagnosis["severidade"] in ("CRITICA", "ALTA") else "CAUTELOSA",
            "macro_steps": [],
        },
        "notificacao_dashboard": (
            "ALERTA: DIVERGENCIA DETECTADA" if diagnosis["erro_detectado"] else "OK: SEM ERRO CRITICO"
        ),
    }
