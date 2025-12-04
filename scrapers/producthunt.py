import requests
import re
from scrapers.base_scraper import BaseScraper
from config.settings import settings

class ProductHuntScraper(BaseScraper):
    """
    ProductHunt scraper using Google site search via Serper API.

    Finds tech products and startups launched on ProductHunt.
    """

    def search(self, keywords: str) -> list:
        """
        Search ProductHunt launches via Google site search.
        Returns list of products matching the base scraper format.
        """
        if not settings.SERPER_API_KEY:
            print("ProductHunt: Serper API key not configured")
            return []

        # Use Google site search to find ProductHunt products
        search_query = f"site:producthunt.com {keywords}"

        url = "https://google.serper.dev/search"
        payload = {"q": search_query, "num": 15}
        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)

            if response.status_code != 200:
                print(f"ProductHunt: Serper returned status {response.status_code}")
                return []

            data = response.json()
            results = []

            for item in data.get("organic", []):
                item_url = item.get("link", "")

                # Only include actual product pages (contain /products/ in URL)
                if "/products/" not in item_url.lower():
                    continue

                title = item.get("title", "")
                snippet = item.get("snippet", "")

                # ProductHunt doesn't have prices, products are typically free/freemium
                # Could extract upvote count if needed
                price = None

                results.append({
                    "name": title,
                    "url": item_url,
                    "price": price,
                    "description": snippet
                })

                # Stop at 10 products
                if len(results) >= 10:
                    break

            if results:
                print(f"ProductHunt: Found {len(results)} products via Google site search")
            else:
                print("ProductHunt: No product pages found in Google results")

            return results

        except Exception as e:
            print(f"ProductHunt scrape error: {e}")
            return []
