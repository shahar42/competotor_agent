from scrapers.aliexpress import AliExpressScraper
from scrapers.kickstarter import KickstarterScraper
from scrapers.serper import SerperScraper
from scrapers.patents import PatentSearchScraper

class ScraperRegistry:
    """Factory pattern - no tight coupling"""

    @staticmethod
    def get_all_scrapers():
        return [
            ("aliexpress", AliExpressScraper()),
            ("kickstarter", KickstarterScraper()),
            ("google", SerperScraper()),
            ("patents", PatentSearchScraper())
        ]
