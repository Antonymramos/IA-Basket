#!/usr/bin/env python3
"""
Bet Scraper - Playwright scraper for betting site scores and odds
"""

from playwright.async_api import async_playwright

class BetScraper:
    def __init__(self, bet_url):
        self.bet_url = bet_url
    
    async def get_score(self):
        """
        Scrape current score and odds from betting site
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(self.bet_url)
            
            # Assuming the score is in elements with specific selectors
            # This needs to be adjusted based on actual site structure
            team_a_score = await page.locator("#team-a-score").text_content()
            team_b_score = await page.locator("#team-b-score").text_content()
            
            await browser.close()
            
            return {
                "team_a": int(team_a_score) if team_a_score.isdigit() else 0,
                "team_b": int(team_b_score) if team_b_score.isdigit() else 0
            }