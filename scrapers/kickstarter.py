import requests
from scrapers.base_scraper import BaseScraper
from config.settings import settings

class KickstarterScraper(BaseScraper):
    def search(self, keywords: str) -> list:
        """Search Kickstarter via their discover API"""
        url = "https://www.kickstarter.com/discover/advanced"
        params = {"term": keywords}
        headers = {"User-Agent": settings.USER_AGENT}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=settings.REQUEST_TIMEOUT)
            # TODO: Parse Kickstarter results
            return []
        except Exception as e:
            print(f"Kickstarter scrape error: {e}")
            return []
