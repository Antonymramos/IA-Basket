#!/usr/bin/env python3
"""
Live Feed Client - WebSocket client for real-time game scores
"""

import asyncio
import json
import re
import time
import websockets
from playwright.async_api import async_playwright

class LiveFeedClient:
    def __init__(self, ws_url):
        self.ws_url = ws_url
    
    async def get_score(self):
        """
        Connect to WebSocket and get current score
        """
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Send request for score
                await websocket.send(json.dumps({"action": "get_score"}))
                response = await websocket.recv()
                data = json.loads(response)
                return data
        except Exception as e:
            print(f"Erro ao obter placar da transmissão: {e}")
            return {"team_a": 0, "team_b": 0}


class HttpLiveFeedClient:
    def __init__(self, page_url: str, user_data_dir: str | None = None, headless: bool = True):
        self.page_url = page_url
        self.user_data_dir = user_data_dir
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def _ensure_page(self):
        if self._page is not None:
            return
        self._playwright = await async_playwright().start()
        if self.user_data_dir:
            self._context = await self._playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=self.headless,
            )
            if self._context.pages:
                self._page = self._context.pages[0]
            else:
                self._page = await self._context.new_page()
        else:
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._page = await self._browser.new_page()

    async def close(self):
        try:
            if self._page is not None:
                await self._page.close()
            if self._context is not None:
                await self._context.close()
            if self._browser is not None:
                await self._browser.close()
            if self._playwright is not None:
                await self._playwright.stop()
        except Exception:
            pass
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

    def _extract_score(self, text: str):
        if not text:
            return None

        normalized = " ".join(text.split())
        patterns = [
            r"\b(\d{1,3})\s*[-:]\s*(\d{1,3})\b",
            r"\b(\d{1,3})\s+x\s*(\d{1,3})\b",
        ]

        candidates = []
        for pattern in patterns:
            for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
                team_a = int(match.group(1))
                team_b = int(match.group(2))
                if 0 <= team_a <= 250 and 0 <= team_b <= 250:
                    candidates.append((team_a + team_b, team_a, team_b))

        if not candidates:
            return None

        candidates.sort(reverse=True)
        _, team_a, team_b = candidates[0]
        return {"team_a": team_a, "team_b": team_b}

    async def _extract_score_from_page(self):
        selectors = [
            "[class*='score']",
            "[id*='score']",
            "[class*='Score']",
            "[id*='Score']",
            "[class*='result']",
            "[id*='result']",
            "[class*='points']",
            "[id*='points']",
            "header",
            "main",
        ]

        snippets = []
        for selector in selectors:
            try:
                nodes = self._page.locator(selector)
                count = await nodes.count()
                limit = min(count, 8)
                for idx in range(limit):
                    raw = await nodes.nth(idx).inner_text(timeout=1000)
                    text = " ".join(raw.split())
                    if text:
                        snippets.append(text[:300])
            except Exception:
                continue

        try:
            body_text = await self._page.inner_text("body")
            if body_text:
                snippets.append(" ".join(body_text.split())[:2000])
        except Exception:
            pass

        for snippet in snippets:
            parsed = self._extract_score(snippet)
            if parsed:
                parsed["source"] = "http_dom"
                return parsed

        parsed = self._extract_score(" | ".join(snippets))
        if parsed:
            parsed["source"] = "http_combined"
            return parsed

        return None

    async def get_score(self):
        try:
            await self._ensure_page()
            await self._page.goto(self.page_url, wait_until="domcontentloaded", timeout=20000)
            await self._page.wait_for_timeout(1800)

            page_title = ""
            page_body = ""
            try:
                page_title = await self._page.title()
            except Exception:
                pass
            try:
                page_body = await self._page.inner_text("body")
            except Exception:
                pass

            auth_markers = ["login", "senha", "entrar", "sign in"]
            joined = f"{page_title} {page_body}".lower()
            if any(marker in joined for marker in auth_markers):
                print("Erro ao obter placar HTTP: autenticação necessária na fonte de transmissão.")
                return {"team_a": 0, "team_b": 0, "source": "http_auth_required", "auth_required": True}

            parsed = await self._extract_score_from_page()
            if parsed:
                return parsed

            for frame in self._page.frames:
                if frame == self._page.main_frame:
                    continue
                try:
                    frame_text = await frame.inner_text("body")
                    frame_parsed = self._extract_score(frame_text)
                    if frame_parsed:
                        frame_parsed["source"] = "http_iframe"
                        return frame_parsed
                except Exception:
                    continue

            print("Erro ao obter placar HTTP: não foi possível extrair placar da página.")
            return {"team_a": 0, "team_b": 0, "source": "http_not_found"}
        except Exception as e:
            print(f"Erro ao obter placar HTTP: {e}")
            return {"team_a": 0, "team_b": 0, "source": "http_error"}


class BllsportNetworkFeedClient:
    def __init__(self, page_url: str, user_data_dir: str | None = None, headless: bool = True, wait_seconds: float = 2.0):
        self.page_url = page_url
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.wait_seconds = wait_seconds
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._score_event = None
        self._last_score = None
        self._last_update_ts = 0.0
        self._page_loaded = False

    async def _ensure_page(self):
        if self._page is not None:
            return

        self._score_event = asyncio.Event()
        self._playwright = await async_playwright().start()
        if self.user_data_dir:
            self._context = await self._playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=self.headless,
            )
            if self._context.pages:
                self._page = self._context.pages[0]
            else:
                self._page = await self._context.new_page()
        else:
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._page = await self._browser.new_page()

        self._page.on("response", lambda response: asyncio.create_task(self._handle_response(response)))
        self._page.on("websocket", self._handle_websocket)

    async def close(self):
        try:
            if self._page is not None:
                await self._page.close()
            if self._context is not None:
                await self._context.close()
            if self._browser is not None:
                await self._browser.close()
            if self._playwright is not None:
                await self._playwright.stop()
        except Exception:
            pass
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            self._score_event = None
            self._page_loaded = False

    def _set_score(self, score: dict):
        if not score:
            return
        self._last_score = score
        self._last_update_ts = time.time()
        if self._score_event and not self._score_event.is_set():
            self._score_event.set()

    def _extract_score_from_text(self, text: str) -> dict | None:
        if not text:
            return None
        match = re.search(r"\b(\d{1,3})\s*[-:]\s*(\d{1,3})\b", text)
        if match:
            team_a = int(match.group(1))
            team_b = int(match.group(2))
            if 0 <= team_a <= 250 and 0 <= team_b <= 250:
                return {"team_a": team_a, "team_b": team_b}
        return None

    def _score_from_mapping(self, payload: dict) -> dict | None:
        if not isinstance(payload, dict):
            return None

        lowered = {str(k).lower(): k for k in payload.keys()}
        pairs = [
            ("home_score", "away_score"),
            ("home", "away"),
            ("homeScore", "awayScore"),
            ("score_home", "score_away"),
            ("scorea", "scoreb"),
            ("team_a", "team_b"),
            ("homeTeamScore", "awayTeamScore"),
        ]

        for left_key, right_key in pairs:
            lk = left_key.lower()
            rk = right_key.lower()
            if lk in lowered and rk in lowered:
                try:
                    team_a = int(payload[lowered[lk]])
                    team_b = int(payload[lowered[rk]])
                    if 0 <= team_a <= 250 and 0 <= team_b <= 250:
                        return {"team_a": team_a, "team_b": team_b}
                except Exception:
                    pass

        if "score" in lowered:
            raw = payload.get(lowered["score"])
            if isinstance(raw, str):
                return self._extract_score_from_text(raw)
            if isinstance(raw, dict):
                nested = self._score_from_mapping(raw)
                if nested:
                    return nested

        for key in ("home", "away"):
            if key in lowered:
                node = payload.get(lowered[key])
                if isinstance(node, dict):
                    for score_key in ("score", "points", "goals"):
                        if score_key in node:
                            try:
                                value = int(node[score_key])
                            except Exception:
                                value = None
                            if value is not None:
                                if key == "home":
                                    other = payload.get(lowered.get("away", ""), {})
                                    other_val = None
                                    if isinstance(other, dict):
                                        for score_key2 in ("score", "points", "goals"):
                                            if score_key2 in other:
                                                try:
                                                    other_val = int(other[score_key2])
                                                except Exception:
                                                    other_val = None
                                                break
                                    if other_val is not None:
                                        return {"team_a": value, "team_b": other_val}

        return None

    def _search_score_in_payload(self, payload) -> dict | None:
        if isinstance(payload, dict):
            direct = self._score_from_mapping(payload)
            if direct:
                return direct
            for value in payload.values():
                nested = self._search_score_in_payload(value)
                if nested:
                    return nested
        elif isinstance(payload, list):
            for item in payload:
                nested = self._search_score_in_payload(item)
                if nested:
                    return nested
        elif isinstance(payload, str):
            parsed = self._extract_score_from_text(payload)
            if parsed:
                return parsed
        return None

    async def _handle_response(self, response):
        try:
            content_type = response.headers.get("content-type", "")
            if "json" not in content_type:
                return
            data = await response.json()
            score = self._search_score_in_payload(data)
            if score:
                score["source"] = "bllsport_net"
                self._set_score(score)
        except Exception:
            return

    def _handle_websocket(self, websocket):
        try:
            websocket.on("framereceived", lambda frame: asyncio.create_task(self._handle_ws_frame(frame)))
        except Exception:
            return

    async def _handle_ws_frame(self, frame):
        try:
            payload = frame.payload
            if not payload:
                return
            try:
                parsed = json.loads(payload)
            except Exception:
                parsed = payload
            score = self._search_score_in_payload(parsed)
            if score:
                score["source"] = "bllsport_ws"
                self._set_score(score)
        except Exception:
            return

    async def get_score(self):
        try:
            await self._ensure_page()
            if not self._page_loaded:
                await self._page.goto(self.page_url, wait_until="domcontentloaded", timeout=25000)
                self._page_loaded = True

            if self._last_score and (time.time() - self._last_update_ts) < 5:
                return self._last_score

            if self._score_event:
                self._score_event.clear()

            try:
                await asyncio.wait_for(self._score_event.wait(), timeout=self.wait_seconds)
            except Exception:
                pass

            if self._last_score:
                return self._last_score

            return {"team_a": 0, "team_b": 0, "source": "bllsport_no_score"}
        except Exception as exc:
            return {"team_a": 0, "team_b": 0, "source": "bllsport_error", "error": str(exc)}