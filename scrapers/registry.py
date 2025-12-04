from scrapers.aliexpress import AliExpressScraper
from scrapers.kickstarter import KickstarterScraper
from scrapers.serper import SerperScraper
from scrapers.patents import PatentSearchScraper
from scrapers.producthunt import ProductHuntScraper
from scrapers.amazon import AmazonScraper

class ScraperRegistry:
    """Factory pattern - no tight coupling"""

    @staticmethod
    def get_all_scrapers():
        return [
            ("aliexpress", AliExpressScraper()),
            ("kickstarter", KickstarterScraper()),
            ("amazon", AmazonScraper()),
            ("producthunt", ProductHuntScraper()),
            ("google", SerperScraper()),
            ("patents", PatentSearchScraper())
        ]
