#!/usr/bin/env python3
"""
Bet Scraper - Playwright scraper for betting site scores and odds
"""

import re
from playwright.async_api import async_playwright

class BetScraper:
    def __init__(self, bet_url, user_data_dir: str | None = None, headless: bool = True):
        self.bet_url = bet_url
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
                a = int(match.group(1))
                b = int(match.group(2))
                if 0 <= a <= 250 and 0 <= b <= 250:
                    candidates.append((a + b, a, b))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        _, a, b = candidates[0]
        return {"team_a": a, "team_b": b}
    
    async def get_score(self):
        """
        Scrape current score and odds from betting site
        """
        try:
            await self._ensure_page()
            await self._page.goto(self.bet_url, wait_until="domcontentloaded", timeout=25000)
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

            auth_markers = ["entrar", "login", "senha", "sign in"]
            joined = f"{page_title} {page_body}".lower()
            if any(marker in joined for marker in auth_markers):
                return {
                    "team_a": 0,
                    "team_b": 0,
                    "source": "bet_auth_required",
                    "auth_required": True,
                }

            parsed = self._extract_score(page_body)
            if parsed:
                parsed["source"] = "bet_dom"
                return parsed

            return {"team_a": 0, "team_b": 0, "source": "bet_not_found"}
        except Exception as e:
            print(f"Erro ao obter placar da bet: {e}")
            return {"team_a": 0, "team_b": 0, "source": "bet_error"}