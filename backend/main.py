#!/usr/bin/env python3
"""
FastAPI backend for the Jarvis panel.
"""

import json
import os
from pathlib import Path

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

ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT_DIR / "backend" / "static"
CONFIG_PATH = ROOT_DIR / "config.json"

load_dotenv()

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
    bet_url: str | None = None
    game_score: float | None = None
    min_game_score: float | None = None
    whitelist_enabled: bool | None = None


class WhitelistRequest(BaseModel):
    game: str


class VoiceRequest(BaseModel):
    text: str


class KnowledgeRequest(BaseModel):
    prompt: str


@app.get("/")
def index():
    index_path = STATIC_DIR / "index.html"
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

    if request.transmission_provider == "simulated_feed":
        updates["mode"] = "simulation"
    elif request.transmission_provider == "live_ws":
        if request.live_feed_ws_url and not (
            request.live_feed_ws_url.startswith("ws://")
            or request.live_feed_ws_url.startswith("wss://")
        ):
            raise HTTPException(
                status_code=400,
                detail="Fonte live precisa ser WebSocket rapido (ws:// ou wss://).",
            )
        updates["mode"] = "live"

    if request.bet_provider == "bet_mock":
        updates["mode"] = "simulation"

    updated = controller.update_selection(updates)
    return {"status": "ok", "config": updated}


@app.get("/api/logs")
def logs(limit: int = 200):
    return {"items": controller.get_logs(limit=limit)}


@app.get("/api/report")
def report():
    return controller.get_report()


@app.post("/api/whitelist/add")
def whitelist_add(request: WhitelistRequest):
    config = controller.add_to_whitelist(request.game)
    return {"status": "ok", "config": config}


@app.post("/api/whitelist/remove")
def whitelist_remove(request: WhitelistRequest):
    config = controller.remove_from_whitelist(request.game)
    return {"status": "ok", "config": config}


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

    return {"status": "noop", "action": action}


@app.post("/api/knowledge")
def knowledge(request: KnowledgeRequest):
    config = controller.get_status().get("config", {})
    model_name = config.get("gemini_model", "gemini-2.0-flash")
    api_key = os.getenv("GEMINI_API_KEY")
    try:
        response = ask_gemini(api_key, model_name, request.prompt)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"status": "ok", "response": response}
