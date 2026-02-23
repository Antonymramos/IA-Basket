from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.gemini_knowledge import ask_gemini
from core.oracle_nba import build_oracle_output
from core.vision_bllsport import analyze_bllsport_frame
from core.nba_official import fetch_balldontlie_game

ROOT_DIR = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT_DIR / "prompts" / "ORACLE_PROMPT_PRINCIPAL.txt"


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise RuntimeError(f"Prompt principal não encontrado: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def _prompt_meta(prompt: str) -> dict[str, Any]:
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    stat = PROMPT_PATH.stat() if PROMPT_PATH.exists() else None
    return {
        "sha256": digest,
        "chars": len(prompt),
        "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).astimezone().isoformat(timespec="seconds") if stat else None,
    }


app = FastAPI(title="Oracle NBA API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/debug/routes")
def debug_routes() -> dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": _now_iso(),
        "oracle_api_file": __file__,
        "routes": [
            {
                "path": getattr(r, "path", None),
                "name": getattr(r, "name", None),
                "methods": sorted(list(getattr(r, "methods", []) or [])),
            }
            for r in app.routes
        ],
    }


class _WSManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast_json(self, payload: dict[str, Any]) -> None:
        if not self._connections:
            return
        message = json.dumps(payload, ensure_ascii=False)
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


ws_manager = _WSManager()
latest_oracle: dict[str, Any] | None = None


@app.get("/api/status")
def status() -> dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": _now_iso(),
        "service": "oracle-nba",
        "prompt": _prompt_meta(_load_prompt()),
    }


@app.get("/api/oracle/prompt")
def oracle_prompt(include_text: bool = False) -> dict[str, Any]:
    prompt = _load_prompt()
    data: dict[str, Any] = {
        "status": "ok",
        "timestamp": _now_iso(),
        "prompt_meta": _prompt_meta(prompt),
    }
    if include_text:
        data["prompt_text"] = prompt
    return data


class OracleAnalyzeRequest(BaseModel):
    video_live: dict | None = None
    frame_base64: str | None = None
    frame_crop: dict | None = None
    bet365: dict | None = None
    nba_oficial: dict | None = None
    system: dict | None = None


@app.post("/api/oracle/analyze")
def oracle_analyze(request: OracleAnalyzeRequest) -> dict[str, Any]:
    video = request.video_live or {}
    bet = request.bet365 or {}
    official = request.nba_oficial or {}
    system = request.system or {}

    video_score = video.get("placar") or video.get("placar_video") or video.get("score")
    video_clock = video.get("tempo") or video.get("tempo_video")

    bet_score = bet.get("placar_geral") or bet.get("placar") or bet.get("score")
    bet_clock = bet.get("tempo_bet") or bet.get("tempo")
    bet_lines = bet.get("linhas") or bet.get("lines") or []

    official_score = official.get("placar") or official.get("score")
    official_clock = official.get("tempo")

    latency_ms = system.get("latencia_ms") or system.get("latency_ms")
    status_stream = system.get("status_stream") or system.get("stream") or "OK"

    return build_oracle_output(
        video_score=video_score,
        video_clock=video_clock,
        bet_score=bet_score,
        bet_clock=bet_clock,
        bet_lines=bet_lines,
        official_score=official_score,
        official_clock=official_clock,
        system_status_stream=status_stream,
        latency_ms=float(latency_ms) if latency_ms is not None else None,
    )


@app.post("/api/oracle/ingest")
async def oracle_ingest(request: OracleAnalyzeRequest) -> dict[str, Any]:
    """Ingestão em tempo real: calcula o JSON do Oráculo e faz broadcast via WebSocket."""
    global latest_oracle
    started = datetime.now(timezone.utc)
    # Se vier frame_base64 e não veio video_live, tenta OCR (bllsport)
    if request.frame_base64 and not request.video_live:
        vision = analyze_bllsport_frame(request.frame_base64, crop=request.frame_crop)
        if vision.ok:
            request.video_live = {
                "placar": vision.placar,
                "tempo": vision.tempo_video,
                "ocr": {"raw_text": vision.raw_text[:2000]},
            }
        else:
            # Marca stream como fallback (mantém pipeline vivo)
            system = request.system or {}
            system.setdefault("status_stream", "FALLBACK")
            system.setdefault("stream_error", vision.error)
            request.system = system

    # Se latência não foi informada pelo client, usa tempo de processamento do servidor
    system = request.system or {}
    if system.get("latencia_ms") is None and system.get("latency_ms") is None:
        elapsed_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        system["latencia_ms"] = elapsed_ms
        request.system = system

    result = oracle_analyze(request)
    latest_oracle = result
    await ws_manager.broadcast_json(result)
    return result


class VisionParseRequest(BaseModel):
    frame_base64: str
    crop: dict | None = None


@app.post("/api/oracle/vision/parse-frame")
def oracle_parse_frame(request: VisionParseRequest) -> dict[str, Any]:
    """OCR do frame da bllsport (placar/tempo)."""
    vision = analyze_bllsport_frame(request.frame_base64, crop=request.crop)
    return {
        "status": "ok" if vision.ok else "error",
        "timestamp": _now_iso(),
        "placar": vision.placar,
        "tempo_video": vision.tempo_video,
        "raw_text": vision.raw_text[:2000],
        "error": vision.error,
    }


@app.get("/api/oracle/nba/balldontlie/game")
async def oracle_balldontlie_game(game_id: int) -> dict[str, Any]:
    """Busca score oficial por game_id (opcional/configurável)."""
    import os

    base_url = os.getenv("BALLDONTLIE_BASE_URL", "https://api.balldontlie.io/v1")
    api_key = os.getenv("BALLDONTLIE_API_KEY")
    result = await fetch_balldontlie_game(base_url=base_url, api_key=api_key, game_id=game_id)
    return {
        "status": "ok" if result.ok else "error",
        "timestamp": _now_iso(),
        "provider": result.provider,
        "placar": result.placar,
        "tempo": result.tempo,
        "raw": result.raw,
        "error": result.error,
    }


@app.get("/api/oracle/latest")
def oracle_latest() -> dict[str, Any]:
    """Último JSON gerado (útil para clientes que conectam depois)."""
    return {
        "status": "ok",
        "timestamp": _now_iso(),
        "latest": latest_oracle,
    }


@app.websocket("/ws/oracle")
async def ws_oracle(websocket: WebSocket):
    """WebSocket de broadcast do Oráculo (JSON puro em texto)."""
    await ws_manager.connect(websocket)
    try:
        if latest_oracle:
            await websocket.send_text(json.dumps(latest_oracle, ensure_ascii=False))
        while True:
            # Mantém a conexão viva; aceita mensagens do cliente (ignoradas).
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


class OracleGeminiRequest(BaseModel):
    # Entrada bruta para o Gemini
    frame_base64: str | None = None
    bet365_json: dict | None = None
    nba_oficial_json: dict | None = None
    system_info: dict | None = None


@app.post("/api/oracle/gemini-json")
def oracle_gemini_json(request: OracleGeminiRequest) -> dict[str, Any]:
    """Chama Gemini para produzir JSON rígido (sem executar macro).

    Observação: isso só gera diagnóstico/comando. A execução (macro/click) deve ser feita por um executor externo.
    """

    api_key = (request.system_info or {}).get("gemini_api_key")
    if not api_key:
        # fallback: env var
        import os

        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY não configurada")

    prompt = _load_prompt()

    payload = {
        "FRAME_BASE64": request.frame_base64,
        "BET365_JSON": request.bet365_json,
        "NBA_OFICIAL": request.nba_oficial_json,
        "SISTEMA_INFO": request.system_info,
    }

    enriched = (
        prompt
        + "\n\n"
        + "RETORNE APENAS JSON VÁLIDO (SEM TEXTO EXTRA).\n"
        + "INPUT_JSON:\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    # Model preferido (mantém compatibilidade)
    model_name = "gemini-1.5-flash"
    text = ask_gemini(api_key, model_name, enriched)

    # Extrair JSON
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        raise HTTPException(status_code=502, detail="Gemini não retornou JSON")

    try:
        parsed = json.loads(text[start:end])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"JSON inválido do Gemini: {exc}")

    return parsed
