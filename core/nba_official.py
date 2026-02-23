from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class OfficialResult:
    ok: bool
    provider: str
    placar: dict[str, int] | None
    tempo: str | None
    raw: dict[str, Any] | None = None
    error: str | None = None


def _try_import_httpx():
    try:
        import httpx  # type: ignore

        return httpx
    except Exception:
        return None


async def fetch_balldontlie_game(*, base_url: str, api_key: str | None, game_id: int) -> OfficialResult:
    """Busca um jogo por ID no balldontlie.

    OBS: A API do balldontlie pode variar por versão. Mantemos isso opcional e configurável.
    """

    httpx = _try_import_httpx()
    if httpx is None:
        return OfficialResult(
            ok=False,
            provider="balldontlie",
            placar=None,
            tempo=None,
            raw=None,
            error="Dependência ausente: httpx. Instale: pip install httpx",
        )

    headers = {}
    if api_key:
        headers["Authorization"] = api_key

    url = f"{base_url.rstrip('/')}/games/{game_id}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        return OfficialResult(ok=False, provider="balldontlie", placar=None, tempo=None, raw=None, error=str(exc))

    # Tentativa de extrair score
    home = data.get("home_team_score")
    away = data.get("visitor_team_score")
    placar = None
    try:
        if home is not None and away is not None:
            placar = {"Home": int(home), "Away": int(away)}
    except Exception:
        placar = None

    return OfficialResult(ok=True, provider="balldontlie", placar=placar, tempo=None, raw=data)
