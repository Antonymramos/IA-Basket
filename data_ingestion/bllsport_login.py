#!/usr/bin/env python3
"""
Open a persistent Playwright profile so the user can log into BLLSport once.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

DEFAULT_PROFILE_DIR = Path("data") / "bllsport_profile"
LOGIN_URL = "https://bllsport.com/"


async def main() -> None:
    profile_dir = DEFAULT_PROFILE_DIR
    profile_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        print("Faça login no BLLSport. Depois, volte aqui e pressione ENTER para sair.")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, input)
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
