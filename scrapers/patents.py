import requests
from scrapers.base_scraper import BaseScraper
from config.settings import settings

class PatentSearchScraper(BaseScraper):
    """Search US patents via SerpAPI Google Patents"""

    BASE_URL = "https://serpapi.com/search"

    def search(self, keywords: str) -> list:
        """
        Returns: [{"name": str, "url": str, "price": None, "description": str}]
        """
        if not settings.SERPAPI_API_KEY:
            print("SerpAPI key not configured - skipping patent search")
            return []

        try:
            params = {
                "engine": "google_patents",
                "q": keywords,
                "api_key": settings.SERPAPI_API_KEY,
                "num": 10
            }

            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=settings.REQUEST_TIMEOUT
            )

            if response.status_code != 200:
                print(f"SerpAPI error: {response.status_code}")
                return []

            data = response.json()
            patents = data.get("organic_results", [])

            results = []
            for patent in patents[:10]:
                results.append({
                    "name": f"Patent: {patent.get('title', 'Untitled')}",
                    "url": patent.get("pdf", patent.get("link", "")),
                    "description": patent.get("snippet", "No description available")[:500],
                    "price": None  # Patents don't have prices
                })

            return results

        except Exception as e:
            print(f"Patent search error: {e}")
            return []
