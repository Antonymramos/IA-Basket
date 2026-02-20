#!/usr/bin/env python3
"""
FastAPI backend for the Jarvis panel.
"""

import json
import os
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.bot_controller import BotController
from backend.connectors import TRANSMISSION_CONNECTORS, BET_CONNECTORS
from backend.gemini_knowledge import ask_gemini
from backend.voice_commands import interpret_voice_command
from core.analytics_context import build_gemini_context
from core.feedback_loop import FeedbackLoop
from core.nba_knowledge import NBAKnowledge
from core.jarvis_knowledge_engine import build_jarvis_knowledge_endpoint
from core.communication_engine import CommunicationEngine

ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT_DIR / "backend" / "static"
CONFIG_PATH = ROOT_DIR / "config.json"
ANALYTICS_DB_PATH = ROOT_DIR / "data" / "analytics.db"
FEEDBACK_DB_PATH = ROOT_DIR / "data" / "feedback_loop.db"
NBA_DB_PATH = ROOT_DIR / "data" / "nba_knowledge.db"
CONFIG_BACKUP_DIR = ROOT_DIR / "data" / "config_backups"

load_dotenv()

DEFAULT_OBJECTIVE = "Reduzir erros de basket e melhorar precisão de execução"

app = FastAPI(title="Hoops Jarvis API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

controller = BotController(str(CONFIG_PATH), os.getenv("GEMINI_API_KEY"))


class AutoBetRequest(BaseModel):
    enabled: bool


class SelectionRequest(BaseModel):
    selected_game: str | None = None
    transmission_provider: str | None = None
    bet_provider: str | None = None
    live_feed_ws_url: str | None = None
    live_feed_headless: bool | None = None
    live_feed_user_data_dir: str | None = None
    bet_url: str | None = None
    bet_headless: bool | None = None
    bet_user_data_dir: str | None = None
    game_score: float | None = None
    min_game_score: float | None = None
    whitelist_enabled: bool | None = None


class VoiceRequest(BaseModel):
    text: str


class KnowledgeRequest(BaseModel):
    prompt: str


class RecommendationsRequest(BaseModel):
    objective: str = "Reduzir erros de basket e melhorar precisão de execução"
    minutes: int = 120
    limit: int = 20


class ApplyRecommendationsRequest(BaseModel):
    objective: str = "Reduzir erros de basket e melhorar precisão de execução"
    minutes: int = 120
    limit: int = 20
    dry_run: bool = True
    recommendations: dict | None = None


class RollbackRequest(BaseModel):
    backup_file: str


class UpdateUrlsRequest(BaseModel):
    bet_url: str | None = None
    live_feed_ws_url: str | None = None
    bet_headless: bool | None = None
    live_feed_headless: bool | None = None
    transmission_provider: str | None = None


def _parse_json_maybe_markdown(text: str) -> dict | None:
    try:
        return json.loads(text)
    except Exception:
        pass

    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        return json.loads(cleaned)
    except Exception:
        return None


def _deep_merge(base: dict, patch: dict) -> dict:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _changed_paths(before: Any, after: Any, prefix: str = "") -> list[str]:
    changed: list[str] = []
    if isinstance(before, dict) and isinstance(after, dict):
        keys = set(before.keys()) | set(after.keys())
        for key in sorted(keys):
            next_prefix = f"{prefix}.{key}" if prefix else key
            if key not in before or key not in after:
                changed.append(next_prefix)
                continue
            changed.extend(_changed_paths(before[key], after[key], next_prefix))
        return changed

    if before != after:
        changed.append(prefix or "root")
    return changed


def _build_delay_calibration_action(txn_bet_status: dict, cfg: dict) -> dict | None:
    """
    Analisa dados de delay e sugere novo bet_delay_seconds se houver suficientes amostras.
    """
    if not txn_bet_status:
        return None
    
    delay_info = txn_bet_status.get("delay", {})
    samples_count = delay_info.get("samples_count", 0)
    avg_lag = delay_info.get("avg_lag_seconds", 0)
    
    # Precisa de pelo menos 50 amostras para auto-calibrar
    if samples_count < 50:
        return None
    
    current_delay = float(((cfg.get("risk_filters") or {}).get("bet_delay_seconds", 5.0)) or 5.0)
    
    # Se o lag médio é significativamente diferente do threshold, sugere ajuste
    diff = avg_lag - current_delay
    
    # Apenas recomenda se a diferença for > 0.5 segundos
    if abs(diff) <= 0.5:
        return None
    
    if diff > 0:
        # Lag médio é maior que o threshold: aumentar para ser mais conservador
        new_delay = round(avg_lag + 0.5, 2)
        action = "aumentar tempo de espera por delay"
        why = f"Lag médio ({avg_lag:.2f}s) excede threshold ({current_delay}s); aumentar para {new_delay}s."
    else:
        # Lag médio é menor: podemos ser mais agressivo
        new_delay = max(1.0, round(avg_lag + 0.3, 2))
        action = "reduzir tempo de espera conservador"
        why = f"Lag médio ({avg_lag:.2f}s) abaixo do threshold ({current_delay}s); reduzir para {new_delay}s."
    
    return {
        "action": action,
        "why": why,
        "config_patch": {
            "risk_filters": {"bet_delay_seconds": new_delay}
        },
        "metadata": {
            "samples_count": samples_count,
            "avg_lag_seconds": round(avg_lag, 3),
            "current_delay_seconds": current_delay,
            "recommended_delay_seconds": new_delay,
        }
    }


def _heuristic_recommendations_from_diagnostics(diag: dict, cfg: dict) -> dict:
    counts = (diag or {}).get("counts_by_event", {}) or {}
    risk = (diag or {}).get("risk_metrics", {}) or {}

    blocked_rate = float(risk.get("blocked_rate_vs_detected", 0) or 0)
    expired_rate = float(risk.get("expired_rate_vs_detected", 0) or 0)
    error_rate = float(risk.get("error_rate_vs_detected", 0) or 0)

    cooldown = float(cfg.get("cooldown_seconds", 6.0) or 6.0)
    ttl = float(cfg.get("signal_ttl_seconds", 6.0) or 6.0)
    delay_cfg = float(((cfg.get("risk_filters") or {}).get("bet_delay_seconds", 5.0)) or 5.0)
    max_feed_warnings = int(((cfg.get("automation") or {}).get("max_feed_warnings", 30)) or 30)

    actions = []

    if blocked_rate >= 0.4:
        actions.append(
            {
                "action": "reduzir bloqueios por repetição",
                "why": "Taxa de bloqueio alta no histórico recente.",
                "config_patch": {"cooldown_seconds": round(cooldown + 1.5, 2)},
            }
        )

    if expired_rate >= 0.25:
        actions.append(
            {
                "action": "aumentar vida útil do sinal",
                "why": "Muitos sinais expirando antes da execução.",
                "config_patch": {
                    "signal_ttl_seconds": round(ttl + 2.0, 2),
                    "risk_filters": {"bet_delay_seconds": max(1.0, round(delay_cfg - 1.0, 2))},
                },
            }
        )

    if counts.get("FEED_WARNING", 0) >= 5 or error_rate >= 0.2:
        actions.append(
            {
                "action": "endurecer proteção de feed",
                "why": "Feed com alertas frequentes ou taxa de erro elevada.",
                "config_patch": {"automation": {"max_feed_warnings": max(10, max_feed_warnings - 5)}},
            }
        )

    if not actions:
        actions.append(
            {
                "action": "ajuste conservador padrão",
                "why": "Sem falhas críticas detectadas; aplicar ajuste leve para estabilidade.",
                "config_patch": {"cooldown_seconds": round(cooldown + 0.5, 2)},
            }
        )

    return {
        "summary": "Recomendações geradas por fallback heurístico local.",
        "priority_actions": actions,
        "risk_notes": [
            "Gerado sem JSON estruturado do Gemini; revisão manual recomendada.",
        ],
        "next_validation": [
            "Executar 10-15 minutos e revisar /api/diagnostics para comparar taxas.",
        ],
    }


def _ensure_backup_dir() -> None:
    CONFIG_BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _create_config_backup(reason: str = "manual") -> str:
    _ensure_backup_dir()
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")
    backup_name = f"config-{timestamp}-{reason}.json"
    backup_path = CONFIG_BACKUP_DIR / backup_name
    content = CONFIG_PATH.read_text(encoding="utf-8")
    backup_path.write_text(content, encoding="utf-8")
    return backup_name


def _list_backups(limit: int = 30) -> list[dict[str, Any]]:
    _ensure_backup_dir()
    files = sorted(CONFIG_BACKUP_DIR.glob("config-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    result = []
    for path in files[:limit]:
        stat = path.stat()
        result.append(
            {
                "file": path.name,
                "size": stat.st_size,
                "mtime": stat.st_mtime,
            }
        )
    return result


def _safe_backup_path(filename: str) -> Path:
    _ensure_backup_dir()
    candidate = (CONFIG_BACKUP_DIR / filename).resolve()
    base = CONFIG_BACKUP_DIR.resolve()
    if base not in candidate.parents and candidate != base:
        raise HTTPException(status_code=400, detail="backup_file inválido")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="backup_file não encontrado")
    return candidate


def _rollback_to_backup_file(backup_file: str) -> dict[str, Any]:
    backup_path = _safe_backup_path(backup_file)
    before_backup = _create_config_backup(reason="before-rollback")

    content = backup_path.read_text(encoding="utf-8")
    try:
        json.loads(content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"backup inválido: {exc}")

    CONFIG_PATH.write_text(content, encoding="utf-8")
    controller._log_handler(
        "CONFIG_ROLLBACK",
        {
            "backup_file": backup_file,
            "before_backup": before_backup,
        },
    )
    return {
        "status": "ok",
        "rolled_back_to": backup_file,
        "before_backup": before_backup,
    }


def _build_knowledge_prompt(user_prompt: str, analytics_context: str, objective: str = DEFAULT_OBJECTIVE) -> str:
    return (
        "Você é Jarvis, especialista em arbitragem e gestão de risco em basket.\n"
        f"Objetivo prioritário: {objective}.\n\n"
        "Regras:\n"
        "- Não invente dados nem afirme acesso à internet em tempo real.\n"
        "- Se a pergunta pedir busca na web, responda com um plano de pesquisa e peça fontes/links.\n"
        "- Responda direto, com passos práticos e métricas.\n\n"
        "Formato de saída (obrigatório):\n"
        "Resumo: <1 frase>\n"
        "Ações: \n"
        "- <acao 1>\n"
        "- <acao 2>\n"
        "Riscos: \n"
        "- <risco 1>\n"
        "Validacao: \n"
        "- <como validar>\n\n"
        f"Contexto histórico:\n{analytics_context}\n\n"
        f"Pergunta: {user_prompt}\n"
    )


@app.get("/")
def index():
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/modern")
def modern_index():
    """Serve o novo front-end moderno com visualizações avançadas"""
    index_path = STATIC_DIR / "index-modern.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/bet-panel")
def bet_panel_index():
    """Serve o painel de apostas e transmissão"""
    index_path = STATIC_DIR / "bet-panel.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/painel-simples")
def simple_panel_index():
    """Serve o painel simples com apenas erros essenciais"""
    index_path = STATIC_DIR / "painel-simples.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/painel-jogo-atual")
def current_game_panel():
    """Serve o painel focado no jogo atual"""
    index_path = STATIC_DIR / "painel-jogo-atual.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/api/status")
def status():
    return controller.get_status()


@app.get("/api/connectors")
def connectors():
    return {
        "transmission": TRANSMISSION_CONNECTORS,
        "bet": BET_CONNECTORS,
    }


@app.post("/api/control/start")
def start_bot():
    controller.start()
    return {"status": "started"}


@app.post("/api/control/stop")
def stop_bot():
    controller.stop()
    return {"status": "stopped"}


@app.post("/api/control/auto-bet")
def auto_bet(request: AutoBetRequest):
    controller.set_auto_bet(request.enabled)
    return {"status": "ok", "auto_bet_enabled": request.enabled}


@app.post("/api/select")
def select_game(request: SelectionRequest):
    updates = {k: v for k, v in request.dict().items() if v is not None}

    if request.transmission_provider == "live_ws":
        if request.live_feed_ws_url and not (
            request.live_feed_ws_url.startswith("ws://")
            or request.live_feed_ws_url.startswith("wss://")
        ):
            raise HTTPException(
                status_code=400,
                detail="Fonte live precisa ser WebSocket rapido (ws:// ou wss://).",
            )
        elif request.transmission_provider in ("live_http", "bllsport_net"):
        if request.live_feed_ws_url and not (
            request.live_feed_ws_url.startswith("http://")
            or request.live_feed_ws_url.startswith("https://")
        ):
            raise HTTPException(
                status_code=400,
                detail="Fonte live_http precisa ser URL HTTP(S).",
            )

    transmission = request.transmission_provider or updates.get("transmission_provider")
    bet_provider = request.bet_provider or updates.get("bet_provider")

    if transmission == "simulated_feed" and bet_provider == "bet_mock":
        updates["mode"] = "simulation"
    else:
        updates["mode"] = "live"

    updated = controller.update_selection(updates)
    return {"status": "ok", "config": updated}


@app.get("/api/logs")
def logs(limit: int = 200):
    return {"items": controller.get_logs(limit=limit)}


@app.get("/api/report")
def report():
    return controller.get_report()


@app.get("/api/diagnostics")
def diagnostics(minutes: int = 120, limit: int = 20):
    return controller.get_diagnostics(minutes=minutes, limit=limit)


@app.get("/api/config/backups")
def config_backups(limit: int = 30):
    safe_limit = min(200, max(1, int(limit)))
    return {"status": "ok", "items": _list_backups(limit=safe_limit)}


@app.post("/api/config/rollback")
def config_rollback(request: RollbackRequest):
    return _rollback_to_backup_file(request.backup_file)


@app.post("/api/config/rollback/latest")
def config_rollback_latest():
    backups = _list_backups(limit=1)
    if not backups:
        raise HTTPException(status_code=404, detail="Nenhum backup disponível para rollback")
    latest_file = backups[0].get("file")
    return _rollback_to_backup_file(latest_file)


@app.post("/api/config/update-urls")
def update_urls(request: UpdateUrlsRequest):
    """
    Atualiza URLs de transmissão e bet365 de forma segura.
    Valida URLs e faz backup automático da config.
    """
    # Criar backup automático antes de modificar
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_file = CONFIG_BACKUP_DIR / f"config-{timestamp}-before-url-update.json"
    CONFIG_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        current_config = json.load(f)
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(current_config, f, indent=2, ensure_ascii=False)
    
    # Validar URLs baseado no provider
    updates = {}
    
    if request.transmission_provider:
        if request.transmission_provider == "live_ws":
            if request.live_feed_ws_url and not (
                request.live_feed_ws_url.startswith("ws://") or 
                request.live_feed_ws_url.startswith("wss://")
            ):
                raise HTTPException(
                    status_code=400,
                    detail="URL de transmissão WebSocket deve começar com ws:// ou wss://"
                )
        elif request.transmission_provider == "live_http":
            if request.live_feed_ws_url and not (
                request.live_feed_ws_url.startswith("http://") or 
                request.live_feed_ws_url.startswith("https://")
            ):
                raise HTTPException(
                    status_code=400,
                    detail="URL de transmissão HTTP deve começar com http:// ou https://"
                )
        updates["transmission_provider"] = request.transmission_provider
    
    if request.bet_url is not None:
        if request.bet_url and not (
            request.bet_url.startswith("http://") or 
            request.bet_url.startswith("https://")
        ):
            raise HTTPException(
                status_code=400,
                detail="URL da Bet365 deve começar com http:// ou https://"
            )
        updates["bet_url"] = request.bet_url
    
    if request.live_feed_ws_url is not None:
        updates["live_feed_ws_url"] = request.live_feed_ws_url
    
    if request.bet_headless is not None:
        updates["bet_headless"] = request.bet_headless
    
    if request.live_feed_headless is not None:
        updates["live_feed_headless"] = request.live_feed_headless
    
    # Aplicar updates
    current_config.update(updates)
    
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(current_config, f, indent=2, ensure_ascii=False)
    
    # Recarregar config no controller (se o método existir)
    try:
        controller._load_config()
    except AttributeError:
        pass  # Controller pode não ter _load_config público
    
    return {
        "status": "ok",
        "message": "URLs atualizadas com sucesso",
        "backup_file": backup_file.name,
        "updated_fields": list(updates.keys()),
        "config": current_config
    }


@app.post("/api/test/simulate-betting")
def simulate_betting_data():
    """
    Endpoints para teste: simula dados realísticos de apostas, transmissão e placar.
    Insere eventos no banco de dados para validar o painel de apostas.
    """
    import sqlite3
    
    try:
        connection = sqlite3.connect(str(ANALYTICS_DB_PATH), timeout=10)
        now = time.time()
        
        # Simular sequência de evento: DETECTADO -> APOSTOU -> BLOQUEADO/EXPIROU
        games = ["Lakers vs Celtics", "Warriors vs Mavericks", "Heat vs 76ers"]
        types = ["2pt", "3pt", "free_throw"]
        
        for i in range(5):
            game = games[i % len(games)]
            bet_type = types[i % len(types)]
            signal_id = f"test_{i}_{int(now)}"
            confidence = 0.75 + (i * 0.05)  # 0.75 to 0.99
            
            # Placar simulado
            team_a_transmission = 45 + i * 2
            team_b_transmission = 42 + i * 2
            team_a_bet = 45 + i * 2
            team_b_bet = 42 + i * 2
            
            # DETECTADO
            connection.execute(
                """
                INSERT INTO events (ts, event_name, game, message, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    now - (300 - i * 60),
                    "DETECTADO",
                    game,
                    f"Sinal detectado no {game}",
                    json.dumps({
                        "signal_id": signal_id,
                        "tipo_pontuacao": bet_type,
                        "confidence": confidence,
                        "transmission_team_a": team_a_transmission,
                        "transmission_team_b": team_b_transmission,
                        "source": "live_http"
                    }, ensure_ascii=False)
                )
            )
            
            # APOSTOU ou BLOQUEADO
            status = "APOSTOU" if i % 3 != 0 else "BLOQUEADO"
            connection.execute(
                """
                INSERT INTO events (ts, event_name, game, message, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    now - (240 - i * 60),
                    status,
                    game,
                    f"Aposta {'executada' if status == 'APOSTOU' else 'bloqueada'} - {bet_type}",
                    json.dumps({
                        "signal_id": signal_id,
                        "tipo_pontuacao": bet_type,
                        "confidence": confidence,
                        "stake": 10.0 + i,
                        "bet_a": team_a_bet,
                        "bet_b": team_b_bet
                    }, ensure_ascii=False)
                )
            )
            
            # DESYNC (transmissão vs bet divergem)
            if i % 2 == 0:
                connection.execute(
                    """
                    INSERT INTO events (ts, event_name, game, message, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        now - (180 - i * 60),
                        "DESYNC",
                        game,
                        f"Desync detectado em {game}",
                        json.dumps({
                            "signal_id": signal_id,
                            "t_a": team_a_transmission + 1,
                            "t_b": team_b_transmission,
                            "b_a": team_a_bet,
                            "b_b": team_b_bet,
                            "diff_a": 1,
                            "diff_b": 0,
                            "tipo_pontuacao": bet_type,
                            "source": "live_http"
                        }, ensure_ascii=False)
                    )
                )
            
            # DELAY_PENDING
            if i % 2 == 1:
                connection.execute(
                    """
                    INSERT INTO events (ts, event_name, game, message, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        now - (120 - i * 60),
                        "DELAY_PENDING",
                        game,
                        f"Delay detectado - idade: {5 + i}s",
                        json.dumps({
                            "signal_id": signal_id,
                            "age_seconds": 5 + i,
                            "delay_threshold": 5.0,
                            "target_a": team_a_transmission,
                            "target_b": team_b_transmission,
                            "bet_a": team_a_bet,
                            "bet_b": team_b_bet,
                            "source": "live_http"
                        }, ensure_ascii=False)
                    )
                )
            
            # EXPIROU (alguns expiram)
            if i % 4 == 3:
                connection.execute(
                    """
                    INSERT INTO events (ts, event_name, game, message, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        now - (60 - i * 30),
                        "EXPIROU",
                        game,
                        f"Janela de aposta expirou",
                        json.dumps({
                            "signal_id": signal_id,
                            "tipo_pontuacao": bet_type,
                            "ttl_seconds": 6.0
                        }, ensure_ascii=False)
                    )
                )
        
        connection.commit()
        connection.close()
        
        return {
            "status": "ok",
            "message": "✅ Dados de teste simulados com sucesso!",
            "events_created": 5 * 3,  # ~15 eventos criados
            "test_games": games,
            "note": "Atualize o painel de apostas (F5) para ver os dados em tempo real"
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao simular dados: {str(exc)}")


@app.post("/api/diagnostics/recommendations")
def diagnostics_recommendations(request: RecommendationsRequest):
    config = controller.get_status().get("config", {})
    model_name = config.get("gemini_model", "gemini-2.5-pro")
    api_key = os.getenv("GEMINI_API_KEY")

    diagnostics_data = controller.get_diagnostics(minutes=request.minutes, limit=request.limit)
    analytics_context = build_gemini_context(
        str(ANALYTICS_DB_PATH),
        minutes=request.minutes,
        limit=min(30, max(5, request.limit)),
    )
    
    # Buscar status transmissão vs bet para calibração de delay
    try:
        import sqlite3
        connection = sqlite3.connect(str(ANALYTICS_DB_PATH), timeout=10)
        connection.row_factory = sqlite3.Row
        
        now = time.time()
        window_start = now - max(1, request.minutes) * 60
        
        delay_rows = connection.execute(
            "SELECT payload_json FROM events WHERE ts >= ? AND event_name = 'DELAY_RESOLVED'",
            (window_start,),
        ).fetchall()
        
        delay_samples = []
        for row in delay_rows:
            try:
                payload = json.loads(row["payload_json"])
                delay_samples.append(payload.get("lag_seconds", 0))
            except Exception:
                pass
        
        txn_bet_status = {
            "delay": {
                "samples_count": len(delay_samples),
                "avg_lag_seconds": sum(delay_samples) / len(delay_samples) if delay_samples else 0,
                "max_lag_seconds": max(delay_samples) if delay_samples else 0,
            }
        }
        connection.close()
    except Exception:
        txn_bet_status = None

    prompt = (
        "Você é um especialista em arbitragem esportiva de basket e engenharia de risco.\n"
        "Objetivo do usuário: " + request.objective + "\n\n"
        "Contexto histórico resumido:\n"
        + analytics_context
        + "\n\n"
        "Diagnóstico completo em JSON:\n"
        + json.dumps(diagnostics_data, ensure_ascii=False)
    )
    
    # Adicionar delay calibration info se disponível
    if txn_bet_status and txn_bet_status.get("delay", {}).get("samples_count", 0) >= 50:
        delay_info = txn_bet_status["delay"]
        prompt += (
            "\n\nDados de Delay (para auto-calibração):\n"
            f"- Amostras coletadas: {delay_info['samples_count']}\n"
            f"- Lag médio: {delay_info['avg_lag_seconds']:.2f}s\n"
            f"- Lag máximo: {delay_info['max_lag_seconds']:.2f}s\n"
            f"- Considere ajustar bet_delay_seconds se houver significativa divergência."
        )
    
    prompt += (
        "\n\nRetorne APENAS um JSON válido com este formato:\n"
        "{\n"
        "  \"summary\": \"texto curto\",\n"
        "  \"priority_actions\": [\n"
        "    {\"action\": \"...\", \"why\": \"...\", \"config_patch\": {\"campo\": valor}}\n"
        "  ],\n"
        "  \"risk_notes\": [\"...\"],\n"
        "  \"next_validation\": [\"...\"]\n"
        "}\n"
        "Use patches de config objetivos (cooldown_seconds, signal_ttl_seconds, risk_filters, automation, watchdog)."
    )

    try:
        response = ask_gemini(api_key, model_name, prompt)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    parsed = _parse_json_maybe_markdown(response)

    return {
        "status": "ok",
        "model": model_name,
        "objective": request.objective,
        "recommendations": parsed,
        "raw": response if parsed is None else None,
    }


@app.post("/api/diagnostics/recommendations/apply")
def diagnostics_recommendations_apply(request: ApplyRecommendationsRequest):
    recommendations = request.recommendations
    source = "provided"

    if recommendations is None:
        source = "generated"
        generated = diagnostics_recommendations(
            RecommendationsRequest(
                objective=request.objective,
                minutes=request.minutes,
                limit=request.limit,
            )
        )
        recommendations = generated.get("recommendations")
        if recommendations is None:
            diagnostics_data = controller.get_diagnostics(minutes=request.minutes, limit=request.limit)
            cfg = controller.get_status().get("config", {})
            recommendations = _heuristic_recommendations_from_diagnostics(diagnostics_data, cfg)
            source = "heuristic_fallback"

    if not isinstance(recommendations, dict):
        raise HTTPException(status_code=400, detail="recommendations ausentes ou inválidas para apply")

    priority_actions = recommendations.get("priority_actions", [])
    if not isinstance(priority_actions, list):
        raise HTTPException(status_code=400, detail="priority_actions inválido")

    patches: list[dict] = []
    for item in priority_actions:
        if not isinstance(item, dict):
            continue
        patch = item.get("config_patch")
        if isinstance(patch, dict) and patch:
            patches.append(patch)

    if not patches:
        raise HTTPException(status_code=400, detail="Nenhum config_patch encontrado nas recomendações")

    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        before_config = json.load(config_file)

    after_config = deepcopy(before_config)
    for patch in patches:
        _deep_merge(after_config, patch)

    changed = _changed_paths(before_config, after_config)
    backup_file = None

    if not request.dry_run:
        backup_file = _create_config_backup(reason="before-apply")
        with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
            json.dump(after_config, config_file, ensure_ascii=False, indent=2)
        controller._log_handler(
            "CONFIG_APPLY",
            {
                "source": source,
                "patches": len(patches),
                "changed_fields": len(changed),
                "dry_run": False,
                "backup_file": backup_file,
            },
        )

    return {
        "status": "ok",
        "source": source,
        "dry_run": request.dry_run,
        "patch_count": len(patches),
        "changed_fields": changed,
        "recommendations": recommendations,
        "applied": not request.dry_run,
        "backup_file": backup_file,
    }


@app.post("/api/voice/command")
def voice_command(request: VoiceRequest):
    action = interpret_voice_command(request.text)

    if action["action"] == "set_auto_bet":
        controller.set_auto_bet(action["enabled"])
        return {"status": "ok", "action": action}

    if action["action"] == "start":
        controller.start()
        return {"status": "ok", "action": action}

    if action["action"] == "stop":
        controller.stop()
        return {"status": "ok", "action": action}

    if action["action"] == "select_game":
        updated = controller.update_selection({"selected_game": action["game"]})
        return {"status": "ok", "action": action, "config": updated}

    if action["action"] == "open_errors_panel":
        return {"status": "ok", "action": action, "ui_target": "errors"}

    if action["action"] == "knowledge_query":
        config = controller.get_status().get("config", {})
        model_name = config.get("gemini_model", "gemini-2.5-pro")
        api_key = os.getenv("GEMINI_API_KEY")
        analytics_context = build_gemini_context(str(ANALYTICS_DB_PATH), minutes=120, limit=10)
        prompt = _build_knowledge_prompt(action.get("prompt", request.text), analytics_context)
        try:
            response = ask_gemini(api_key, model_name, prompt)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {
            "status": "ok",
            "action": action,
            "knowledge_response": response,
        }

    if action["action"] == "rollback_latest":
        rollback_result = config_rollback_latest()
        return {"status": "ok", "action": action, "rollback": rollback_result}

    return {"status": "noop", "action": action}


@app.post("/api/voice/premium")
def voice_premium(request: VoiceRequest):
    """
    Gera áudio premium usando ElevenLabs
    Retorna áudio MP3 em base64 para reprodução no frontend
    """
    try:
        from backend.jarvis_voice_api import generate_jarvis_audio
        import base64
        
        # Gera áudio
        audio_bytes = generate_jarvis_audio(request.text)
        
        # Converte para base64
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {
            "status": "ok",
            "audio": audio_b64,
            "format": "mp3"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/api/transmission-bet-status")
def transmission_bet_status(minutes: int = 60, limit: int = 50):
    """
    Retorna status em tempo real de transmissão vs bet:
    - DESYNC events (transmissão subiu, bet atrasado)
    - DELAY_PENDING e DELAY_RESOLVED (tempo de espera)
    - Estatísticas de atraso (lag)
    """
    import sqlite3
    
    now = time.time()
    window_start = now - max(1, minutes) * 60
    
    try:
        connection = sqlite3.connect(str(ANALYTICS_DB_PATH), timeout=10)
        connection.row_factory = sqlite3.Row
        
        # Buscar DESYNC events recentes
        desync_rows = connection.execute(
            """
            SELECT ts, event_name, payload_json
            FROM events
            WHERE ts >= ? AND event_name = 'DESYNC'
            ORDER BY ts DESC
            LIMIT ?
            """,
            (window_start, limit),
        ).fetchall()
        
        desync_events = []
        for row in desync_rows:
            try:
                payload = json.loads(row["payload_json"])
                desync_events.append({
                    "ts": row["ts"],
                    "signal_id": payload.get("signal_id"),
                    "diff_a": payload.get("diff_a"),
                    "diff_b": payload.get("diff_b"),
                    "t_a": payload.get("t_a"),
                    "t_b": payload.get("t_b"),
                    "b_a": payload.get("b_a"),
                    "b_b": payload.get("b_b"),
                    "type": payload.get("tipo_pontuacao"),
                    "source": payload.get("source"),
                })
            except Exception:
                pass
        
        # Buscar DELAY_RESOLVED events para calcular lag médio
        delay_rows = connection.execute(
            """
            SELECT payload_json
            FROM events
            WHERE ts >= ? AND event_name = 'DELAY_RESOLVED'
            """,
            (window_start,),
        ).fetchall()
        
        delay_samples = []
        for row in delay_rows:
            try:
                payload = json.loads(row["payload_json"])
                delay_samples.append({
                    "lag_seconds": payload.get("lag_seconds", 0),
                    "point_gap": payload.get("point_gap", 2),
                    "source": payload.get("source"),
                })
            except Exception:
                pass
        
        # Buscar DELAY_PENDING events (alertas de atraso)
        pending_rows = connection.execute(
            """
            SELECT ts, payload_json
            FROM events
            WHERE ts >= ? AND event_name = 'DELAY_PENDING'
            ORDER BY ts DESC
            LIMIT ?
            """,
            (window_start, limit),
        ).fetchall()
        
        pending_events = []
        for row in pending_rows:
            try:
                payload = json.loads(row["payload_json"])
                pending_events.append({
                    "ts": row["ts"],
                    "signal_id": payload.get("signal_id"),
                    "age_seconds": payload.get("age_seconds"),
                    "threshold": payload.get("delay_threshold"),
                    "target_a": payload.get("target_a"),
                    "target_b": payload.get("target_b"),
                    "bet_a": payload.get("bet_a"),
                    "bet_b": payload.get("bet_b"),
                    "source": payload.get("source"),
                })
            except Exception:
                pass
        
        # Calcular estatísticas
        avg_lag = 0.0
        max_lag = 0.0
        if delay_samples:
            avg_lag = sum(s["lag_seconds"] for s in delay_samples) / len(delay_samples)
            max_lag = max(s["lag_seconds"] for s in delay_samples)
        
        # Contar eventos tipo
        event_counts = connection.execute(
            """
            SELECT event_name, COUNT(*) AS c
            FROM events
            WHERE ts >= ? AND event_name IN ('DESYNC', 'DELAY_PENDING', 'DELAY_RESOLVED', 'DETECTADO', 'EXPIROU', 'BLOQUEADO', 'APOSTOU')
            GROUP BY event_name
            """,
            (window_start,),
        ).fetchall()
        
        counts_by_event = {row["event_name"]: row["c"] for row in event_counts}
        
        connection.close()
        
        response = {
            "status": "ok",
            "window": {
                "minutes": minutes,
                "start_ts": window_start,
                "now_ts": now,
            },
            "desync": {
                "recent_events": desync_events[:10],  # Últimos 10
                "count": counts_by_event.get("DESYNC", 0),
            },
            "delay": {
                "pending_events": pending_events[:10],  # Últimos 10 alertas
                "avg_lag_seconds": round(avg_lag, 3),
                "max_lag_seconds": round(max_lag, 3),
                "samples_count": len(delay_samples),
                "count_pending": counts_by_event.get("DELAY_PENDING", 0),
                "count_resolved": counts_by_event.get("DELAY_RESOLVED", 0),
            },
            "summary": {
                "detections": counts_by_event.get("DETECTADO", 0),
                "blocked": counts_by_event.get("BLOQUEADO", 0),
                "expired": counts_by_event.get("EXPIROU", 0),
                "executed": counts_by_event.get("APOSTOU", 0),
            },
            "immediate_feedback": []  # Enhanced with narratives
        }

        # Add immediate feedback for recent events using CommunicationEngine
        comm = CommunicationEngine()
        
        # Process DETECTADO events for feedback
        detected_rows = connection.execute(
            """
            SELECT ts, payload_json
            FROM events
            WHERE ts >= ? AND event_name = 'DETECTADO'
            ORDER BY ts DESC
            LIMIT 5
            """,
            (window_start,),
        ).fetchall()

        for row in detected_rows:
            try:
                payload = json.loads(row["payload_json"])
                feedback = comm.format_detection_feedback(
                    payload.get("team_a", "N/A"),
                    payload.get("team_b", "N/A"),
                    str(payload.get("tipo_pontuacao", "2")),
                    payload.get("ev_score", 0),
                    payload.get("consensus_strength", 0.5),
                )
                feedback["timestamp"] = row["ts"]
                response["immediate_feedback"].append(feedback)
            except Exception:
                pass

        # Process APOSTOU events for feedback
        executed_rows = connection.execute(
            """
            SELECT ts, payload_json
            FROM events
            WHERE ts >= ? AND event_name = 'APOSTOU'
            ORDER BY ts DESC
            LIMIT 5
            """,
            (window_start,),
        ).fetchall()

        for row in executed_rows:
            try:
                payload = json.loads(row["payload_json"])
                feedback = comm.format_execution_feedback(
                    payload.get("team_a", "N/A"),
                    payload.get("team_b", "N/A"),
                    payload.get("delay_seconds", 0),
                )
                feedback["timestamp"] = row["ts"]
                response["immediate_feedback"].append(feedback)
            except Exception:
                pass

        # Process BLOQUEADO events for feedback
        blocked_rows = connection.execute(
            """
            SELECT ts, payload_json
            FROM events
            WHERE ts >= ? AND event_name = 'BLOQUEADO'
            ORDER BY ts DESC
            LIMIT 5
            """,
            (window_start,),
        ).fetchall()

        for row in blocked_rows:
            try:
                payload = json.loads(row["payload_json"])
                feedback = comm.format_block_feedback(
                    payload.get("team_a", "N/A"),
                    payload.get("team_b", "N/A"),
                    payload.get("reason", "unknown"),
                    payload.get("current_errors", 0),
                )
                feedback["timestamp"] = row["ts"]
                response["immediate_feedback"].append(feedback)
            except Exception:
                pass

        # Sort feedback by timestamp descending
        response["immediate_feedback"] = sorted(
            response["immediate_feedback"], 
            key=lambda x: x.get("timestamp", 0), 
            reverse=True
        )[:10]
        
        connection.close()
        
        return response
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar status: {str(exc)}")


@app.get("/api/ensemble-stats")
def ensemble_stats(minutes: int = 60, limit: int = 50):
    """
    Retorna estatísticas de ensemble voting (múltiplos modelos votando).
    - ENSEMBLE_CONSENSUS: decisões com consenso forte (>= 70%)
    - ENSEMBLE_WEAK: decisões com consenso fraco (< 70%)
    """
    import sqlite3
    
    now = time.time()
    window_start = now - max(1, minutes) * 60
    
    try:
        connection = sqlite3.connect(str(ANALYTICS_DB_PATH), timeout=10)
        connection.row_factory = sqlite3.Row
        
        # Buscar ensemble events recentes
        ensemble_rows = connection.execute(
            """
            SELECT ts, event_name, payload_json
            FROM events
            WHERE ts >= ? AND event_name IN ('ENSEMBLE_CONSENSUS', 'ENSEMBLE_WEAK')
            ORDER BY ts DESC
            LIMIT ?
            """,
            (window_start, limit),
        ).fetchall()
        
        ensemble_events = []
        consensus_count = 0
        weak_count = 0
        avg_consensus_strength = 0.0
        
        for row in ensemble_rows:
            try:
                payload = json.loads(row["payload_json"])
                event_data = {
                    "ts": row["ts"],
                    "type": row["event_name"],
                    "action": payload.get("action"),
                    "consensus_strength": payload.get("consensus_strength", 0),
                    "votes_count": payload.get("votes_count", 0),
                    "votes_for_action": payload.get("votes_for_action", 0),
                }
                ensemble_events.append(event_data)
                
                if row["event_name"] == "ENSEMBLE_CONSENSUS":
                    consensus_count += 1
                    avg_consensus_strength += payload.get("consensus_strength", 0)
                else:
                    weak_count += 1
            except Exception:
                pass
        
        if consensus_count > 0:
            avg_consensus_strength /= consensus_count
        
        # Contar ações por tipo de consenso
        action_counts = {
            "consensus_execute": 0,
            "consensus_register": 0,
            "weak_execute": 0,
            "weak_register": 0,
        }
        
        for event in ensemble_events:
            key = f"{'consensus' if event['type'] == 'ENSEMBLE_CONSENSUS' else 'weak'}_{'execute' if 'executar' in event['action'] else 'register'}"
            if key in action_counts:
                action_counts[key] += 1
        
        connection.close()
        
        response = {
            "status": "ok",
            "window": {
                "minutes": minutes,
                "start_ts": window_start,
                "now_ts": now,
            },
            "summary": {
                "consensus_decisions": consensus_count,
                "weak_decisions": weak_count,
                "total_ensemble_decisions": consensus_count + weak_count,
                "avg_consensus_strength": round(avg_consensus_strength, 3),
            },
            "action_breakdown": action_counts,
            "recent_decisions": ensemble_events[:15],  # Últimas 15 decisões
        }
        
        return response
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar ensemble stats: {str(exc)}")


@app.get("/api/feedback-stats")
def feedback_stats(minutes: int = 120, limit: int = 50):
    """
    Retorna estatísticas de feedback loop (accuracy tracking, Few-Shot examples).
    - Win rate e accuracy por tipo de pontuação (2pt/3pt)
    - Win rate por força de consenso (strong >= 70% vs weak < 70%)
    - Lucro esperado (EV-weighted)
    - Exemplos de sucesso para Few-Shot Learning
    """
    try:
        feedback = FeedbackLoop(str(FEEDBACK_DB_PATH))
        
        accuracy_stats = feedback.get_accuracy_stats(minutes=minutes, limit=limit)
        success_examples = feedback.get_success_examples(limit=5)
        
        response = {
            "status": "ok",
            "window": {
                "minutes": minutes,
                "timestamp": time.time(),
            },
            "summary": accuracy_stats.get("summary", {}),
            "accuracy_by_points": accuracy_stats.get("accuracy_by_points", {}),
            "accuracy_by_consensus": accuracy_stats.get("accuracy_by_consensus", {}),
            "success_examples": success_examples,
        }
        
        return response
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar feedback stats: {str(exc)}")


@app.get("/api/nba-knowledge")
def nba_knowledge_status():
    """
    Retorna status da base de conhecimento NBA.
    Mostra quantos times, jogadores e padrões estão armazenados.
    """
    try:
        nba = NBAKnowledge(str(NBA_DB_PATH))
        
        with sqlite3.connect(str(NBA_DB_PATH), timeout=10) as connection:
            connection.row_factory = sqlite3.Row
            
            # Contar dados armazenados
            teams_count = connection.execute("SELECT COUNT(*) as c FROM nba_teams").fetchone()["c"]
            players_count = connection.execute("SELECT COUNT(*) as c FROM nba_players").fetchone()["c"]
            patterns_count = connection.execute("SELECT COUNT(*) as c FROM nba_patterns").fetchone()["c"]
            news_count = connection.execute("SELECT COUNT(*) as c FROM nba_news").fetchone()["c"]
        
        # Pegar exemplos
        top_patterns = nba.get_relevant_patterns(3)
        recent_injuries = nba.get_injury_updates()
        recent_news = nba.get_betting_relevant_news()
        
        response = {
            "status": "ok",
            "database": str(NBA_DB_PATH),
            "stats": {
                "teams_stored": teams_count,
                "players_stored": players_count,
                "patterns_discovered": patterns_count,
                "news_items": news_count,
            },
            "relevant_patterns": top_patterns,
            "injury_updates": recent_injuries[:3],
            "betting_news": recent_news[:3],
        }
        
        return response
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar NBA knowledge: {str(exc)}")


@app.post("/api/nba-knowledge/populate")
def populate_nba_knowledge(request: KnowledgeRequest):
    """
    Alimenta a base de conhecimento NBA usando Gemini.
    Busca informações sobre times, jogadores, padrões e notícias.
    """
    try:
        from core.nba_knowledge import fetch_nba_data_from_gemini, build_nba_population_prompt
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=400, detail="GEMINI_API_KEY não configurada")
        
        # Determinar qual categoria popular
        category = request.prompt.lower().strip() if request.prompt else "teams"
        
        valid_categories = ["teams", "stats", "patterns", "players", "news"]
        if category not in valid_categories:
            category = "teams"
        
        # Construir prompt
        prompt = build_nba_population_prompt(category)
        
        # Buscar dados via Gemini
        response_text = fetch_nba_data_from_gemini(api_key, prompt, timeout=20)
        
        if not response_text:
            raise HTTPException(status_code=400, detail=f"Falha ao buscar dados NBA de {category}")
        
        # Tentar parsear JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Tentar extrair JSON do texto
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise HTTPException(status_code=400, detail="Resposta do Gemini não é JSON válido")
        
        # Armazenar dados no banco
        nba = NBAKnowledge(str(NBA_DB_PATH))
        stored_count = 0
        
        if category == "teams" and isinstance(data, list):
            for team_data in data:
                try:
                    nba.store_team_info(
                        team_name=team_data.get("team_name", "Unknown"),
                        city=team_data.get("city", ""),
                        conference=team_data.get("conference", ""),
                        division=team_data.get("division", ""),
                        last_season_record=team_data.get("last_season_record", ""),
                        home_court=team_data.get("home_court", ""),
                        key_players=team_data.get("key_players", ""),
                        historical_notes=team_data.get("historical_notes", ""),
                    )
                    stored_count += 1
                except Exception as e:
                    print(f"Erro ao armazenar team: {e}")
        
        elif category == "players" and isinstance(data, list):
            for player_data in data:
                try:
                    nba.store_player_info(
                        player_name=player_data.get("player_name", "Unknown"),
                        team=player_data.get("team", ""),
                        position=player_data.get("position", ""),
                        jersey_number=int(player_data.get("jersey_number", 0)),
                        height=player_data.get("height", ""),
                        weight=int(player_data.get("weight", 0)),
                        ppg=float(player_data.get("ppg", 0)),
                        rpg=float(player_data.get("rpg", 0)),
                        apg=float(player_data.get("apg", 0)),
                        injury_status=player_data.get("injury_status", "Saudável"),
                    )
                    stored_count += 1
                except Exception as e:
                    print(f"Erro ao armazenar player: {e}")
        
        elif category == "patterns" and isinstance(data, list):
            for pattern_data in data:
                try:
                    nba.store_pattern(
                        pattern_name=pattern_data.get("pattern_name", "Unknown"),
                        description=pattern_data.get("description", ""),
                        relevant_teams=pattern_data.get("relevant_teams", ""),
                        impact_on_scoring=int(pattern_data.get("impact_on_scoring", 0)),
                        betting_edge=pattern_data.get("betting_edge", ""),
                        reliability_score=float(pattern_data.get("reliability_score", 0.5)),
                    )
                    stored_count += 1
                except Exception as e:
                    print(f"Erro ao armazenar pattern: {e}")
        
        elif category == "news" and isinstance(data, list):
            for news_data in data:
                try:
                    nba.store_news(
                        date=news_data.get("date", ""),
                        team=news_data.get("team", ""),
                        headline=news_data.get("headline", ""),
                        impact=news_data.get("impact", ""),
                        relevant_to_betting=bool(news_data.get("relevant_to_betting", False)),
                        injury_update=bool(news_data.get("injury_update", False)),
                    )
                    stored_count += 1
                except Exception as e:
                    print(f"Erro ao armazenar news: {e}")
        
        return {
            "status": "ok",
            "category": category,
            "stored_count": stored_count,
            "message": f"✅ {stored_count} registros de '{category}' armazenados no BD NBA!",
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao popular NBA knowledge: {str(exc)}")


# ============================================
# JARVIS KNOWLEDGE ENGINE ENDPOINTS
# ============================================

@app.get("/api/jarvis/briefing")
def jarvis_briefing(minutes: int = 120):
    """
    Retorna um briefing formatado de toda inteligência acumulada no sistema.
    Inclui: análise de mercado, performance pessoal, contexto NBA, risco, padrões e recomendações.
    """
    try:
        jarvis_engine = build_jarvis_knowledge_endpoint(
            str(ANALYTICS_DB_PATH),
            str(FEEDBACK_DB_PATH),
            str(NBA_DB_PATH)
        )
        briefing = jarvis_engine.get_jarvis_briefing()
        return {
            "status": "ok",
            "brief_type": "formatted_text",
            "briefing": briefing,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar briefing Jarvis: {str(exc)}")


@app.get("/api/jarvis/intelligence")
def jarvis_intelligence(minutes: int = 120):
    """
    Retorna toda inteligência acumulada em formato JSON estruturado.
    Contém: market_analysis, personal_performance, nba_context, risk_assessment, pattern_recognition, recommendations.
    """
    try:
        jarvis_engine = build_jarvis_knowledge_endpoint(
            str(ANALYTICS_DB_PATH),
            str(FEEDBACK_DB_PATH),
            str(NBA_DB_PATH)
        )
        intelligence = jarvis_engine.get_current_betting_intelligence(minutes=minutes)
        return {
            "status": "ok",
            "intelligence": intelligence,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar inteligência Jarvis: {str(exc)}")


class JarvisGetBettingSuggestion(BaseModel):
    team_a: str
    team_b: str


@app.post("/api/jarvis/suggest-bet")
def jarvis_suggest_bet(request: JarvisGetBettingSuggestion):
    """
    Fornece uma sugestão completa de aposta baseada em toda inteligência do sistema.
    Inclui: análise contextual, histórico de performance pessoal, dados NBA e avaliação de risco + confiança.
    """
    try:
        jarvis_engine = build_jarvis_knowledge_endpoint(
            str(ANALYTICS_DB_PATH),
            str(FEEDBACK_DB_PATH),
            str(NBA_DB_PATH)
        )
        suggestion = jarvis_engine.get_betting_suggestion(request.team_a, request.team_b)
        return {
            "status": "ok",
            "suggestion": suggestion,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar sugestão de aposta: {str(exc)}")


@app.get("/api/jarvis/decision-breakdown")
def jarvis_decision_breakdown(team_a: str = "Lakers", team_b: str = "Celtics"):
    """
    Quebra a decisão em componentes com impacto individual explicado.
    Mostra EXATAMENTE por que cada fator importa na recomendação.
    """
    try:
        jarvis_engine = build_jarvis_knowledge_endpoint(
            str(ANALYTICS_DB_PATH),
            str(FEEDBACK_DB_PATH),
            str(NBA_DB_PATH)
        )
        breakdown = jarvis_engine.get_decision_breakdown(team_a, team_b, confidence=0.70)
        return {
            "status": "ok",
            "breakdown": breakdown,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar breakdown: {str(exc)}")


@app.get("/api/jarvis/pattern-insights")
def jarvis_pattern_insights():
    """
    Retorna insights sobre padrões descobertos com narrativa explicativa.
    Mostra: melhor hora para apostar, melhor tipo de jogo, taxas de sucesso.
    """
    try:
        jarvis_engine = build_jarvis_knowledge_endpoint(
            str(ANALYTICS_DB_PATH),
            str(FEEDBACK_DB_PATH),
            str(NBA_DB_PATH)
        )
        insights = jarvis_engine.get_pattern_insights()
        return {
            "status": "ok",
            "insights": insights,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar insights de padrões: {str(exc)}")


@app.get("/api/jarvis/weekly-summary")
def jarvis_weekly_summary():
    """
    Retorna resumo semanal que comunica aprendizado e progresso.
    Inclui: wins/losses, mudança de acurácia, padrões descobertos, sequências.
    """
    try:
        jarvis_engine = build_jarvis_knowledge_endpoint(
            str(ANALYTICS_DB_PATH),
            str(FEEDBACK_DB_PATH),
            str(NBA_DB_PATH)
        )
        summary = jarvis_engine.get_weekly_performance()
        return {
            "status": "ok",
            "summary_text": summary.get("summary"),
            "performance": summary.get("performance"),
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resumo semanal: {str(exc)}")


class JarvisAskRequest(BaseModel):
    question: str


@app.post("/api/jarvis/ask")
def jarvis_ask(request: JarvisAskRequest):
    """
    Chat interativo: responde perguntas do usuário sobre o sistema.
    Ex: "Por que bloqueou aquela aposta?", "Qual é meu melhor horário?", etc.
    """
    try:
        jarvis_engine = build_jarvis_knowledge_endpoint(
            str(ANALYTICS_DB_PATH),
            str(FEEDBACK_DB_PATH),
            str(NBA_DB_PATH)
        )
        answer = jarvis_engine.answer_question(request.question)
        return {
            "status": "ok",
            "question": request.question,
            "answer": answer,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao responder pergunta: {str(exc)}")


@app.post("/api/knowledge")
def knowledge(request: KnowledgeRequest):
    config = controller.get_status().get("config", {})
    model_name = config.get("gemini_model", "gemini-2.5-pro")
    api_key = os.getenv("GEMINI_API_KEY")
    analytics_context = build_gemini_context(str(ANALYTICS_DB_PATH), minutes=120, limit=10)
    enriched_prompt = _build_knowledge_prompt(request.prompt, analytics_context)
    try:
        response = ask_gemini(api_key, model_name, enriched_prompt)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"status": "ok", "response": response}


@app.get("/api/dashboard/modern")
def modern_dashboard():
    """
    Endpoint agregado otimizado para o front-end moderno.
    Retorna todos os dados necessários em uma única chamada.
    """
    try:
        jarvis_engine = build_jarvis_knowledge_endpoint(
            str(ANALYTICS_DB_PATH),
            str(FEEDBACK_DB_PATH),
            str(NBA_DB_PATH)
        )
        
        # Coletar todos os dados
        intelligence = jarvis_engine.get_current_betting_intelligence(minutes=120)
        briefing = jarvis_engine.get_jarvis_briefing()
        patterns = jarvis_engine.get_pattern_insights()
        weekly = jarvis_engine.get_weekly_performance()
        
        # Buscar feedback stats
        from core.feedback_loop import FeedbackLoop
        feedback_loop = FeedbackLoop(str(FEEDBACK_DB_PATH))
        feedback_stats = feedback_loop.get_accuracy_stats(minutes=120, limit=50)
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "intelligence": intelligence,
            "briefing": briefing,
            "patterns": patterns,
            "weekly_summary": weekly,
            "feedback_stats": feedback_stats,
            "system_health": {
                "api_status": "online",
                "auto_bet": controller.get_status().get("auto_bet", False),
                "last_update": datetime.now().isoformat()
            }
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar dashboard: {str(exc)}")


@app.get("/api/gemini/auto-insight")
def gemini_auto_insight(topic: str = "strategy"):
    """
    Gera insights automáticos do Gemini baseados no estado atual do sistema.
    Topics: strategy, patterns, teams, risk
    """
    try:
        config = controller.get_status().get("config", {})
        model_name = config.get("gemini_model", "gemini-2.5-pro")
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="GEMINI_API_KEY não configurada")
        
        analytics_context = build_gemini_context(str(ANALYTICS_DB_PATH), minutes=120, limit=10)
        
        prompts = {
            "strategy": "Baseado nos dados recentes, qual é a melhor estratégia de aposta para hoje? Seja específico e prático.",
            "patterns": "Identifique e explique the 3 principais padrões de vitória descobertos nos dados. Seja conciso.",
            "teams": "Quais times da NBA estão performando melhor nas últimas semanas? Liste top 5 e explique por quê.",
            "risk": "Analise o nível de risco atual e sugira quando seria o melhor momento para apostar hoje."
        }
        
        prompt = prompts.get(topic, prompts["strategy"])
        enriched_prompt = _build_knowledge_prompt(prompt, analytics_context)
        
        response = ask_gemini(api_key, model_name, enriched_prompt)
        
        return {
            "status": "ok",
            "topic": topic,
            "insight": response,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar insight: {str(exc)}")


@app.get("/api/bet-panel")
def bet_panel(minutes: int = 60):
    """
    Endpoint especializado para o painel de apostas e transmissão.
    Retorna dados consolidados de apostas, transmissão e desyncs.
    """
    import sqlite3
    
    now = time.time()
    window_start = now - max(1, minutes) * 60
    
    try:
        connection = sqlite3.connect(str(ANALYTICS_DB_PATH), timeout=10)
        connection.row_factory = sqlite3.Row
        
        # 1. ESTATÍSTICAS DE APOSTAS
        bet_events = connection.execute(
            """
            SELECT ts, event_name, game, payload_json
            FROM events
            WHERE ts >= ? AND event_name IN ('DETECTADO', 'APOSTOU', 'BLOQUEADO', 'EXPIROU')
            ORDER BY ts DESC
            LIMIT 50
            """,
            (window_start,),
        ).fetchall()
        
        recent_bets = []
        bets_counts = {"detectadas": 0, "apostou": 0, "bloqueadas": 0, "expiradas": 0}
        
        for row in bet_events:
            try:
                payload = json.loads(row["payload_json"]) if row["payload_json"] else {}
                
                # Contagem
                event_lower = row["event_name"].lower()
                if event_lower == "detectado":
                    bets_counts["detectadas"] += 1
                elif event_lower == "apostou":
                    bets_counts["apostou"] += 1
                elif event_lower == "bloqueado":
                    bets_counts["bloqueadas"] += 1
                elif event_lower == "expirou":
                    bets_counts["expiradas"] += 1
                
                # Lista de bets recentes
                if len(recent_bets) < 20:
                    recent_bets.append({
                        "timestamp": row["ts"],
                        "status": row["event_name"],
                        "game": row["game"],
                        "type": payload.get("tipo_pontuacao", "?"),
                        "confidence": payload.get("confidence"),
                        "signal_id": payload.get("signal_id")
                    })
            except Exception:
                pass
        
        # 2. DESYNCS
        desync_rows = connection.execute(
            """
            SELECT ts, payload_json
            FROM events
            WHERE ts >= ? AND event_name = 'DESYNC'
            ORDER BY ts DESC
            LIMIT 50
            """,
            (window_start,),
        ).fetchall()
        
        desync_events = []
        for row in desync_rows:
            try:
                payload = json.loads(row["payload_json"])
                desync_events.append({
                    "ts": row["ts"],
                    "transmission": f"{payload.get('t_a')}-{payload.get('t_b')}",
                    "bet": f"{payload.get('b_a')}-{payload.get('b_b')}",
                    "diff": f"+{payload.get('diff_a')}/+{payload.get('diff_b')}",
                    "point_type": payload.get("tipo_pontuacao"),
                    "source": payload.get("source")
                })
            except Exception:
                pass
        
        # 3. DELAYS
        delay_rows = connection.execute(
            """
            SELECT ts, payload_json
            FROM events
            WHERE ts >= ? AND event_name = 'DELAY_PENDING'
            ORDER BY ts DESC
            LIMIT 50
            """,
            (window_start,),
        ).fetchall()
        
        delay_events = []
        total_lag = 0
        lag_samples = 0
        
        for row in delay_rows:
            try:
                payload = json.loads(row["payload_json"])
                delay_events.append({
                    "ts": row["ts"],
                    "target_a": payload.get("target_a"),
                    "target_b": payload.get("target_b"),
                    "bet_a": payload.get("bet_a"),
                    "bet_b": payload.get("bet_b"),
                    "age_seconds": payload.get("age_seconds"),
                    "threshold": payload.get("delay_threshold"),
                    "source": payload.get("source")
                })
                
                if payload.get("age_seconds"):
                    total_lag += payload.get("age_seconds", 0)
                    lag_samples += 1
            except Exception:
                pass
        
        # 4. LAG MÉDIO
        avg_lag = int(total_lag / lag_samples * 1000) if lag_samples > 0 else 0
        
        # 5. CONTAR EVENTOS
        event_counts = connection.execute(
            """
            SELECT event_name, COUNT(*) AS c
            FROM events
            WHERE ts >= ?
            GROUP BY event_name
            """,
            (window_start,),
        ).fetchall()
        
        counts = {row["event_name"]: row["c"] for row in event_counts}
        
        # 6. ANÁLISE OTT - Extrai informações sobre a transmissão
        ott_analysis = {
            "status": "active" if len(desync_events) + len(delay_events) < 5 else "warning",
            "health_score": 100 - (len(desync_events) * 10) - (len(delay_events) * 5),
            "sources": set(),
            "placar_tracking": {},
            "sync_quality": 100 - len(desync_events) * 10
        }
        
        # Extrair fontes e placares da transmissão
        for desync in desync_events:
            if desync.get("source"):
                ott_analysis["sources"].add(desync.get("source"))
            ott_analysis["placar_tracking"][desync.get("transmission", "?")] = {
                "transmission": desync.get("transmission"),
                "bet": desync.get("bet"),
                "diff": desync.get("diff"),
                "type": desync.get("point_type")
            }
        
        # Extração de placar do DETECTADO
        for bet in recent_bets[:10]:
            if bet.get("status") == "DETECTADO":
                signal_id = bet.get("signal_id", "")
                game = bet.get("game", "")
                ott_analysis["placar_tracking"][f"{game} - {signal_id[:8]}"] = {
                    "game": game,
                    "type": bet.get("type"),
                    "confidence": bet.get("confidence"),
                    "timestamp": bet.get("timestamp")
                }
        
        ott_analysis["sources"] = list(ott_analysis["sources"])
        ott_analysis["health_score"] = max(0, ott_analysis["health_score"])
        
        # 7. ANÁLISE DE DECISÃO - Transmissão vs Aposta
        decision_analysis = {
            "total_signals": bets_counts["detectadas"],
            "executed": bets_counts["apostou"],
            "blocked": bets_counts["bloqueadas"],
            "expired": bets_counts["expiradas"],
            "accuracy_rate": 0,
            "decision_breakdown": {},
            "conflicts": []
        }
        
        # Calcular taxa de acerto
        if bets_counts["detectadas"] > 0:
            total_outcome = (bets_counts["apostou"] + bets_counts["bloqueadas"] + bets_counts["expiradas"])
            decision_analysis["accuracy_rate"] = (bets_counts["apostou"] / total_outcome * 100) if total_outcome > 0 else 0
        
        # Breakdown de decisões
        decision_analysis["decision_breakdown"] = {
            "executed_pct": (bets_counts["apostou"] / (bets_counts["detectadas"] + 0.01) * 100) if bets_counts["detectadas"] > 0 else 0,
            "blocked_pct": (bets_counts["bloqueadas"] / (bets_counts["detectadas"] + 0.01) * 100) if bets_counts["detectadas"] > 0 else 0,
            "expired_pct": (bets_counts["expiradas"] / (bets_counts["detectadas"] + 0.01) * 100) if bets_counts["detectadas"] > 0 else 0
        }
        
        # Conflitos: detectar desyncs vs decisões
        if len(desync_events) > 0:
            for desync in desync_events[:5]:
                conflict = {
                    "ts": desync.get("ts"),
                    "type": "desync_conflict",
                    "transmission_score": desync.get("transmission"),
                    "bet_score": desync.get("bet"),
                    "difference": desync.get("diff"),
                    "impact": "high" if desync.get("diff_a", 0) > 2 else "medium"
                }
                decision_analysis["conflicts"].append(conflict)
        
        # Conflitos: delays vs decisões
        if len(delay_events) > 0:
            for delay in delay_events[:3]:
                conflict = {
                    "ts": delay.get("ts"),
                    "type": "delay_conflict",
                    "age_seconds": delay.get("age_seconds"),
                    "threshold": delay.get("threshold"),
                    "impact": "high" if delay.get("age_seconds", 0) > 10 else "medium"
                }
                decision_analysis["conflicts"].append(conflict)
        
        connection.close()
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "window_minutes": minutes,
            "bets": bets_counts,
            "recent_bets": recent_bets,
            "transmission": {
                "desync_count": len(desync_events),
                "delay_count": len(delay_events),
                "avg_lag": avg_lag,
                "desync_events": desync_events,
                "delay_events": delay_events
            },
            "ott_analysis": {
                "status": ott_analysis["status"],
                "health_score": ott_analysis["health_score"],
                "sync_quality": ott_analysis["sync_quality"],
                "sources": ott_analysis["sources"],
                "placars_monitored": len(ott_analysis["placar_tracking"]),
                "placar_samples": list(ott_analysis["placar_tracking"].values())[:5]
            },
            "decision_analysis": decision_analysis
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar bet panel: {str(exc)}")


@app.get("/api/system-health")
def system_health(minutes: int = 60):
    """
    Endpoint agregado para monitoramento de saúde do sistema.
    Retorna: erros, transmissão vs bet, apostas, alertas críticos.
    """
    import sqlite3
    
    now = time.time()
    window_start = now - max(1, minutes) * 60
    
    try:
        connection = sqlite3.connect(str(ANALYTICS_DB_PATH), timeout=10)
        connection.row_factory = sqlite3.Row
        
        # 1. ERROS RECENTES (críticos)
        error_events = connection.execute(
            """
            SELECT ts, event_name, message, game
            FROM events
            WHERE ts >= ? AND event_name IN ('ERROR', 'GEMINI_ERROR', 'FEED_WARNING')
            ORDER BY ts DESC
            LIMIT 20
            """,
            (window_start,),
        ).fetchall()
        
        errors_list = []
        for row in error_events:
            errors_list.append({
                "timestamp": row["ts"],
                "type": row["event_name"],
                "message": row["message"] or "Sem detalhes",
                "game": row["game"],
                "severity": "critical" if row["event_name"] in ("ERROR", "GEMINI_ERROR") else "warning"
            })
        
        # 2. APOSTAS EM ANDAMENTO/RECENTES
        bet_events = connection.execute(
            """
            SELECT ts, event_name, payload_json, game
            FROM events
            WHERE ts >= ? AND event_name IN ('DETECTADO', 'APOSTOU', 'BLOQUEADO', 'EXPIROU')
            ORDER BY ts DESC
            LIMIT 30
            """,
            (window_start,),
        ).fetchall()
        
        active_bets = []
        for row in bet_events:
            try:
                payload = json.loads(row["payload_json"]) if row["payload_json"] else {}
                active_bets.append({
                    "timestamp": row["ts"],
                    "status": row["event_name"],
                    "game": row["game"],
                    "type": payload.get("tipo_pontuacao", "?"),
                    "confidence": payload.get("confidence"),
                    "signal_id": payload.get("signal_id"),
                    "details": payload
                })
            except Exception:
                pass
        
        # 3. DESYNC (transmissão vs bet)
        desync_events = connection.execute(
            """
            SELECT ts, payload_json
            FROM events
            WHERE ts >= ? AND event_name = 'DESYNC'
            ORDER BY ts DESC
            LIMIT 10
            """,
            (window_start,),
        ).fetchall()
        
        desyncs = []
        for row in desync_events:
            try:
                payload = json.loads(row["payload_json"])
                desyncs.append({
                    "timestamp": row["ts"],
                    "transmission": f"{payload.get('t_a')}-{payload.get('t_b')}",
                    "bet": f"{payload.get('b_a')}-{payload.get('b_b')}",
                    "diff": f"+{payload.get('diff_a')}/+{payload.get('diff_b')}",
                    "point_type": payload.get("tipo_pontuacao")
                })
            except Exception:
                pass
        
        # 4. DELAY/LAG (atrasos)
        delay_pending = connection.execute(
            """
            SELECT ts, payload_json
            FROM events
            WHERE ts >= ? AND event_name = 'DELAY_PENDING'
            ORDER BY ts DESC
            LIMIT 5
            """,
            (window_start,),
        ).fetchall()
        
        delays = []
        for row in delay_pending:
            try:
                payload = json.loads(row["payload_json"])
                delays.append({
                    "timestamp": row["ts"],
                    "age_seconds": payload.get("age_seconds"),
                    "threshold": payload.get("delay_threshold"),
                    "signal_id": payload.get("signal_id")
                })
            except Exception:
                pass
        
        # 5. CONTADORES DE EVENTOS
        event_counts = connection.execute(
            """
            SELECT event_name, COUNT(*) AS c
            FROM events
            WHERE ts >= ?
            GROUP BY event_name
            """,
            (window_start,),
        ).fetchall()
        
        counts = {row["event_name"]: row["c"] for row in event_counts}
        
        connection.close()
        
        # HEALTH SCORE (0-100)
        detected = counts.get("DETECTADO", 0)
        blocked = counts.get("BLOQUEADO", 0)
        errors = counts.get("ERROR", 0) + counts.get("GEMINI_ERROR", 0)
        feed_warnings = counts.get("FEED_WARNING", 0)
        
        health_score = 100
        if detected > 0:
            health_score -= min(30, (blocked / detected) * 100)  # -30 max por bloqueios
        health_score -= min(25, errors * 5)  # -5 por erro, -25 max
        health_score -= min(20, feed_warnings * 4)  # -4 por warning, -20 max
        health_score -= min(15, len(desyncs) * 3)  # -3 por desync, -15 max
        health_score -= min(10, len(delays) * 5)  # -5 por delay, -10 max
        health_score = max(0, int(health_score))
        
        # STATUS GERAL
        if health_score >= 80:
            overall_status = "healthy"
        elif health_score >= 50:
            overall_status = "degraded"
        else:
            overall_status = "critical"
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "window_minutes": minutes,
            "overall_status": overall_status,
            "health_score": health_score,
            "errors": {
                "recent": errors_list[:10],
                "total_errors": errors,
                "total_warnings": feed_warnings
            },
            "bets": {
                "recent": active_bets[:15],
                "detected": counts.get("DETECTADO", 0),
                "executed": counts.get("APOSTOU", 0),
                "blocked": counts.get("BLOQUEADO", 0),
                "expired": counts.get("EXPIROU", 0)
            },
            "transmission": {
                "desyncs": desyncs,
                "delays_pending": delays,
                "total_desyncs": counts.get("DESYNC", 0),
                "total_delays": counts.get("DELAY_PENDING", 0)
            },
            "event_counts": counts
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar system health: {str(exc)}")


@app.get("/api/simple-errors")
def simple_errors(minutes: int = 60):
    """
    Endpoint simplificado - apenas as informações essenciais:
    1. Probabilidade de acerto
    2. Localização do erro
    3. Tipo (2 pontos, 3 pontos, free throw)
    4. Qual time
    """
    import sqlite3
    
    now = time.time()
    window_start = now - max(1, minutes) * 60
    
    try:
        connection = sqlite3.connect(str(ANALYTICS_DB_PATH), timeout=10)
        connection.row_factory = sqlite3.Row
        
        # Recuperar eventos DETECTADO (erros/desyncs)
        errors_rows = connection.execute(
            """
            SELECT ts, game, payload_json, event_name
            FROM events
            WHERE ts >= ? AND event_name IN ('DETECTADO', 'DESYNC', 'DELAY_PENDING')
            ORDER BY ts DESC
            LIMIT 100
            """,
            (window_start,),
        ).fetchall()
        
        errors = []
        
        for row in errors_rows:
            try:
                payload = json.loads(row["payload_json"]) if row["payload_json"] else {}
                
                # Extrair dados essenciais
                game = row["game"] or "Jogo Desconhecido"
                event_name = row["event_name"]
                confidence = payload.get("confidence", 0.5)
                probability = int(confidence * 100) if confidence else 50
                
                # Determinar tipo de erro
                tipo_pontuacao = payload.get("tipo_pontuacao", "unknown")
                
                if "2" in str(tipo_pontuacao).lower():
                    tipo = "2 Pontos"
                elif "3" in str(tipo_pontuacao).lower():
                    tipo = "3 Pontos"
                elif "free" in str(tipo_pontuacao).lower() or "free-throw" in str(tipo_pontuacao).lower():
                    tipo = "Free Throw"
                else:
                    tipo = tipo_pontuacao.upper() if tipo_pontuacao else "Desconhecido"
                
                # Localização do erro
                # Para DESYNC: diferença de placar
                # Para normal: tipo de pontuação
                if event_name == "DESYNC":
                    t_a = payload.get("t_a", "?")
                    t_b = payload.get("t_b", "?")
                    b_a = payload.get("b_a", "?")
                    b_b = payload.get("b_b", "?")
                    location = f"Transmissão: {t_a}-{t_b} | Aposta: {b_a}-{b_b}"
                    tipo = tipo_pontuacao.upper() if tipo_pontuacao else "DESYNC"
                elif event_name == "DELAY_PENDING":
                    age = payload.get("age_seconds", "?")
                    location = f"Atraso de {age}s"
                    probability = max(50, probability)  # Delays sempre elevados
                else:
                    # DETECTADO
                    location = f"Linha: {tipo_pontuacao}" if tipo_pontuacao else "N/A"
                
                # Qual é o time?
                # Tenta extrair do game ou usar nome genérico
                teams = game.split(" vs ")
                team = teams[0].strip() if teams else "Time A"
                
                error_obj = {
                    "timestamp": row["ts"],
                    "game": game,
                    "team": team,
                    "probability": probability,
                    "type": tipo,
                    "location": location,
                    "event": event_name,
                    "confidence": round(confidence, 2)
                }
                
                errors.append(error_obj)
                
            except Exception as e:
                print(f"Erro ao processar evento: {str(e)}")
                pass
        
        connection.close()
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "window_minutes": minutes,
            "total_errors": len(errors),
            "errors": errors[:30]  # Retornar apenas os 30 mais recentes
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar lista simples: {str(exc)}")


@app.get("/api/current-game")
def current_game(minutes: int = 5):
    """
    Endpoint focado no jogo ATUAL com informações essenciais:
    1. Nome do jogo
    2. Placar atual
    3. Status de transmissão (delay, desyncs)
    4. Erros/desyncs atuais
    5. Recomendação: pode apostar?
    """
    import sqlite3
    
    now = time.time()
    window_start = now - max(1, minutes) * 60
    
    try:
        connection = sqlite3.connect(str(ANALYTICS_DB_PATH), timeout=10)
        connection.row_factory = sqlite3.Row
        
        # Recuperar jogo mais recente
        game_rows = connection.execute(
            """
            SELECT DISTINCT game
            FROM events
            WHERE ts >= ?
            ORDER BY ts DESC
            LIMIT 1
            """,
            (window_start,),
        ).fetchall()
        
        if not game_rows:
            connection.close()
            return {
                "status": "no_game",
                "message": "Nenhum jogo em andamento",
                "game": None
            }
        
        current_game_name = game_rows[0]["game"]
        
        # Recuperar dados do jogo atual
        events = connection.execute(
            """
            SELECT ts, event_name, payload_json
            FROM events
            WHERE game = ? AND ts >= ?
            ORDER BY ts DESC
            LIMIT 200
            """,
            (current_game_name, window_start),
        ).fetchall()
        
        # Processar dados
        latest_placar = "-- : --"
        desyncs = []
        delays = []
        all_errors = []
        last_sync_check = now
        
        for event in events:
            try:
                payload = json.loads(event["payload_json"]) if event["payload_json"] else {}
                event_name = event["event_name"]
                
                # Extrair placar mais recente
                if event_name == "DETECTADO" and not latest_placar.startswith("ERROR"):
                    t_a = payload.get("t_a")
                    t_b = payload.get("t_b")
                    if t_a is not None and t_b is not None:
                        latest_placar = f"{t_a} : {t_b}"
                
                # Extrair desyncs
                if event_name == "DESYNC":
                    desync = {
                        "ts": event["ts"],
                        "type": "DESYNC",
                        "description": "Diferença de placar detectada",
                        "transmission": f"{payload.get('t_a', '?')}-{payload.get('t_b', '?')}",
                        "bet": f"{payload.get('b_a', '?')}-{payload.get('b_b', '?')}",
                        "probability": 75,
                        "location": f"Transmissão vs Aposta"
                    }
                    desyncs.append(desync)
                    all_errors.append(desync)
                
                # Extrair delays
                if event_name == "DELAY_PENDING":
                    delay = {
                        "ts": event["ts"],
                        "type": "DELAY",
                        "description": f"Atraso de {payload.get('age_seconds', '?')}s",
                        "age_seconds": payload.get("age_seconds", 0),
                        "probability": 60,
                        "location": f"Lag: {payload.get('age_seconds', '?')}s / Threshold: {payload.get('delay_threshold', '?')}s"
                    }
                    delays.append(delay)
                    all_errors.append(delay)
                
            except Exception:
                pass
        
        # Calcular métricas
        desync_count = len(desyncs)
        delay_count = len(delays)
        
        # Health score: 100 - (10 per desync) - (5 per delay)
        health_score = 100 - (desync_count * 10) - (delay_count * 5)
        health_score = max(0, min(100, health_score))
        
        # Avg delay
        avg_delay = 0
        if delays:
            avg_delay = sum(d.get("age_seconds", 0) for d in delays) / len(delays)
            avg_delay = int(avg_delay)
        
        # Quality: sync quality = 100 - (desyncs * 10)
        quality = 100 - (desync_count * 10)
        quality = max(0, min(100, quality))
        
        # Decision: can bet?
        can_bet = True
        condition = "Ótima"
        risk_level = "Baixo"
        confidence = 95
        
        if health_score < 50:
            can_bet = False
            condition = "Ruim"
            risk_level = "Alto"
            confidence = 40
        elif health_score < 70:
            can_bet = True  # Pode mas com cuidado
            condition = "Aceitável"
            risk_level = "Médio"
            confidence = 70
        elif avg_delay > 5:
            can_bet = False
            condition = "Ruim (Delay)"
            risk_level = "Muito Alto"
            confidence = 30
        elif avg_delay > 3:
            can_bet = True
            condition = "Cuidado (Delay)"
            risk_level = "Médio-Alto"
            confidence = 65
        
        connection.close()
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "game": {
                "name": current_game_name,
                "status": "Em andamento",
                "placar": latest_placar,
                "quarter": "Q3"  # Seria extraído do payload em sistema real
            },
            "transmission": {
                "delay": avg_delay,
                "desyncs": desync_count,
                "health_score": health_score,
                "quality": quality,
                "status": "good" if health_score >= 70 else "warning" if health_score >= 50 else "critical"
            },
            "errors": all_errors[:10],  # Top 10 erros mais recentes
            "recommendation": {
                "can_bet": can_bet,
                "condition": condition,
                "risk": risk_level,
                "confidence": confidence
            }
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar dados do jogo atual: {str(exc)}")


@app.get("/api/performance-analysis")
def performance_analysis(minutes: int = 1440):
    """
    Análise completa de desempenho com 5 dimensões:
    1. Quarter Analysis (Q1-Q4) - Períodos do jogo
    2. Confidence Quartiles (Q1-Q4) - Distribuição por confiança
    3. Stage Analysis - Pré-jogo, início, meio, final
    4. Key Metrics - Win rate, ROI, odds médio, expected value
    5. Bankroll Management - 4 lotes com diferentes perfis de risco
    """
    import sqlite3
    
    now = time.time()
    window_start = now - max(1, minutes) * 60
    
    try:
        connection = sqlite3.connect(str(ANALYTICS_DB_PATH), timeout=10)
        connection.row_factory = sqlite3.Row
        
        # Recuperar todos os eventos no período
        all_bets = connection.execute(
            """
            SELECT ts, event_name, game, payload_json
            FROM events
            WHERE ts >= ? AND event_name IN ('DETECTADO', 'APOSTOU', 'BLOQUEADO', 'EXPIROU')
            ORDER BY ts ASC
            """,
            (window_start,),
        ).fetchall()
        
        # ============ 1. QUARTER ANALYSIS ============
        quarter_analysis = {
            "Q1": {"success": 0, "total": 0, "win_rate": 0, "bets": []},
            "Q2": {"success": 0, "total": 0, "win_rate": 0, "bets": []},
            "Q3": {"success": 0, "total": 0, "win_rate": 0, "bets": []},
            "Q4": {"success": 0, "total": 0, "win_rate": 0, "bets": []}
        }
        
        # ============ 2. CONFIDENCE QUARTILES ============
        confidence_quartiles = {
            "Q1_low": {"range": "0-25%", "success": 0, "total": 0, "rate": 0, "bets": []},
            "Q2_medium": {"range": "25-50%", "success": 0, "total": 0, "rate": 0, "bets": []},
            "Q3_high": {"range": "50-75%", "success": 0, "total": 0, "rate": 0, "bets": []},
            "Q4_very_high": {"range": "75-100%", "success": 0, "total": 0, "rate": 0, "bets": []}
        }
        
        # ============ 3. STAGE ANALYSIS ============
        # Pré-jogo: até 10min antes (timestamp negativo)
        # Início: até 15min do jogo
        # Meio: 15-30min
        # Final: 30min+
        stage_analysis = {
            "pre_game": {"label": "Pré-Jogo", "success": 0, "total": 0, "rate": 0, "bets": []},
            "inicio": {"label": "Início (0-15min)", "success": 0, "total": 0, "rate": 0, "bets": []},
            "meio": {"label": "Meio (15-30min)", "success": 0, "total": 0, "rate": 0, "bets": []},
            "final": {"label": "Final (30min+)", "success": 0, "total": 0, "rate": 0, "bets": []}
        }
        
        # ============ 4. KEY METRICS ============
        key_metrics = {
            "win_rate": 0,
            "roi": 0,  # Return on Investment (lucro/investimento)
            "avg_odds": 0,
            "expected_value": 0,
            "total_bets": 0,
            "total_wins": 0,
            "total_losses": 0,
            "total_staked": 0,
            "total_winnings": 0
        }
        
        # Processar cada aposta
        bet_data = []
        odds_list = []
        
        for row in all_bets:
            try:
                payload = json.loads(row["payload_json"]) if row["payload_json"] else {}
                
                is_win = row["event_name"].lower() == "apostou"
                confidence = payload.get("confidence", 0.5)  # Default 50% se não tiver
                
                # Estimar quarter baseado em posição da aposta (heurística)
                # Usar hash do game + timestamp para distribuir
                game_hash = hash(row["game"]) % 4 + 1
                quarter_key = f"Q{game_hash}"
                
                # Estimar stage baseado em timing (heurística simples)
                # Considerar eventos mais recentes como "início" do jogo
                relative_time = (row["ts"] - window_start) / (now - window_start) if (now - window_start) > 0 else 0.5
                
                if relative_time < 0.2:
                    stage_key = "pre_game"
                elif relative_time < 0.4:
                    stage_key = "inicio"
                elif relative_time < 0.7:
                    stage_key = "meio"
                else:
                    stage_key = "final"
                
                # Classificar por confiança
                if confidence < 0.25:
                    conf_key = "Q1_low"
                elif confidence < 0.5:
                    conf_key = "Q2_medium"
                elif confidence < 0.75:
                    conf_key = "Q3_high"
                else:
                    conf_key = "Q4_very_high"
                
                # Registrar aposta
                bet_record = {
                    "game": row["game"],
                    "status": row["event_name"],
                    "confidence": round(confidence * 100, 1),
                    "timestamp": row["ts"],
                    "signal_id": payload.get("signal_id", "N/A")[:12]
                }
                
                # ===== QUARTER =====
                quarter_analysis[quarter_key]["total"] += 1
                quarter_analysis[quarter_key]["bets"].append(bet_record)
                if is_win:
                    quarter_analysis[quarter_key]["success"] += 1
                
                # ===== CONFIDENCE =====
                confidence_quartiles[conf_key]["total"] += 1
                confidence_quartiles[conf_key]["bets"].append(bet_record)
                if is_win:
                    confidence_quartiles[conf_key]["success"] += 1
                
                # ===== STAGE =====
                stage_analysis[stage_key]["total"] += 1
                stage_analysis[stage_key]["bets"].append(bet_record)
                if is_win:
                    stage_analysis[stage_key]["success"] += 1
                
                # ===== KEY METRICS =====
                key_metrics["total_bets"] += 1
                if is_win:
                    key_metrics["total_wins"] += 1
                else:
                    key_metrics["total_losses"] += 1
                
                # Assumir stake fixo de 100 por aposta e odds médio de 1.5
                stake = 100
                assumed_odds = 1.5
                key_metrics["total_staked"] += stake
                odds_list.append(assumed_odds)
                
                if is_win:
                    key_metrics["total_winnings"] += stake * assumed_odds
                
                bet_data.append(bet_record)
                
            except Exception:
                pass
        
        # Calcular taxa de acerto para cada quartile
        for key in quarter_analysis:
            if quarter_analysis[key]["total"] > 0:
                quarter_analysis[key]["win_rate"] = round(
                    quarter_analysis[key]["success"] / quarter_analysis[key]["total"] * 100, 1
                )
        
        for key in confidence_quartiles:
            if confidence_quartiles[key]["total"] > 0:
                confidence_quartiles[key]["rate"] = round(
                    confidence_quartiles[key]["success"] / confidence_quartiles[key]["total"] * 100, 1
                )
        
        for key in stage_analysis:
            if stage_analysis[key]["total"] > 0:
                stage_analysis[key]["rate"] = round(
                    stage_analysis[key]["success"] / stage_analysis[key]["total"] * 100, 1
                )
        
        # Calcular key metrics
        if key_metrics["total_bets"] > 0:
            key_metrics["win_rate"] = round(key_metrics["total_wins"] / key_metrics["total_bets"] * 100, 1)
        
        if key_metrics["total_staked"] > 0:
            net_profit = key_metrics["total_winnings"] - key_metrics["total_staked"]
            key_metrics["roi"] = round(net_profit / key_metrics["total_staked"] * 100, 1)
        
        if len(odds_list) > 0:
            key_metrics["avg_odds"] = round(sum(odds_list) / len(odds_list), 2)
        
        # Expected Value = Win Rate * Odds - (1 - Win Rate)
        if key_metrics["total_bets"] > 0:
            win_rate_decimal = key_metrics["total_wins"] / key_metrics["total_bets"]
            if key_metrics["avg_odds"] > 0:
                key_metrics["expected_value"] = round(
                    (win_rate_decimal * key_metrics["avg_odds"]) - (1 - win_rate_decimal), 3
                )
        
        # ============ 5. BANKROLL MANAGEMENT ============
        # Simular 4 lotes com diferentes estratégias de risco
        total_bankroll = 10000  # Bankroll hipotético
        
        bankroll_management = {
            "total_bankroll": total_bankroll,
            "recommendations": [],
            "lotes": {
                "conservative": {
                    "name": "Conservador",
                    "allocation_pct": 30,
                    "allocation": int(total_bankroll * 0.30),
                    "risk_per_bet": 1,  # 1% max
                    "expected_roi": max(0.5, key_metrics["roi"] * 0.7),
                    "status": "safe"
                },
                "moderate": {
                    "name": "Moderado",
                    "allocation_pct": 40,
                    "allocation": int(total_bankroll * 0.40),
                    "risk_per_bet": 2,  # 2% max
                    "expected_roi": key_metrics["roi"],
                    "status": "balanced"
                },
                "aggressive": {
                    "name": "Agressivo",
                    "allocation_pct": 20,
                    "allocation": int(total_bankroll * 0.20),
                    "risk_per_bet": 5,  # 5% max
                    "expected_roi": max(-10, key_metrics["roi"] * 1.3),
                    "status": "high-risk"
                },
                "recovery": {
                    "name": "Recuperação",
                    "allocation_pct": 10,
                    "allocation": int(total_bankroll * 0.10),
                    "risk_per_bet": 3,  # 3% max
                    "expected_roi": key_metrics["roi"] * 0.9,
                    "status": "recovery"
                }
            }
        }
        
        # Gerar recomendações baseado em desempenho
        recommendations = []
        
        if key_metrics["win_rate"] > 55:
            recommendations.append({
                "type": "success",
                "text": f"🎯 Excelente desempenho! Taxa de acerto em {key_metrics['win_rate']}%",
                "action": "Manter estratégia e considerar aumentar stakes"
            })
        elif key_metrics["win_rate"] > 50:
            recommendations.append({
                "type": "info",
                "text": f"✅ Positivo com {key_metrics['win_rate']}% de acertos",
                "action": "Estratégia viável, continue monitorando"
            })
        else:
            recommendations.append({
                "type": "warning",
                "text": f"⚠️ Taxa de acerto baixa ({key_metrics['win_rate']}%)",
                "action": "Revisar critérios de seleção de apostas"
            })
        
        # Recomendação por quartis de confiança
        best_confidence = max(confidence_quartiles.items(), key=lambda x: x[1]["rate"])
        if best_confidence[1]["rate"] > 0:
            recommendations.append({
                "type": "success",
                "text": f"🔝 Melhor desempenho em {best_confidence[1]['range']} de confiança",
                "action": "Focar em apostas com essa faixa de confiança"
            })
        
        # Recomendação por estágios
        best_stage = max(stage_analysis.items(), key=lambda x: x[1]["rate"])
        if best_stage[1]["rate"] > 0:
            recommendations.append({
                "type": "info",
                "text": f"⏰ Melhor fase: {best_stage[1]['label']} ({best_stage[1]['rate']}%)",
                "action": f"Aumentar volume de apostas nessa fase"
            })
        
        if key_metrics["roi"] > 10:
            recommendations.append({
                "type": "success",
                "text": f"💰 ROI positivo em {key_metrics['roi']}%",
                "action": "Estratégia é lucrativa, escalar com cautela"
            })
        
        bankroll_management["recommendations"] = recommendations
        
        connection.close()
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "window_minutes": minutes,
            "total_bets_analyzed": len(bet_data),
            "quarter_analysis": quarter_analysis,
            "confidence_quartiles": confidence_quartiles,
            "stage_analysis": stage_analysis,
            "key_metrics": key_metrics,
            "bankroll_management": bankroll_management
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar análise de desempenho: {str(exc)}")
