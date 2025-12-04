import requests
import re
from scrapers.base_scraper import BaseScraper
from config.settings import settings

class AmazonScraper(BaseScraper):
    """
    Amazon scraper using Google site search via Serper API.

    Finds products listed on Amazon.
    """

    def search(self, keywords: str) -> list:
        """
        Search Amazon products via Google site search.
        Returns list of products matching the base scraper format.
        """
        if not settings.SERPER_API_KEY:
            print("Amazon: Serper API key not configured")
            return []

        # Use Google site search to find Amazon products
        search_query = f"site:amazon.com {keywords}"

        url = "https://google.serper.dev/search"
        payload = {"q": search_query, "num": 15}
        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)

            if response.status_code != 200:
                print(f"Amazon: Serper returned status {response.status_code}")
                return []

            data = response.json()
            results = []

            for item in data.get("organic", []):
                item_url = item.get("link", "")

                # Only include actual product pages (contain /dp/ or /gp/product/ in URL)
                if not ("/dp/" in item_url.lower() or "/gp/product/" in item_url.lower()):
                    continue

                title = item.get("title", "")
                snippet = item.get("snippet", "")

                # Try to extract price from snippet
                price = None
                price_patterns = [
                    r'\$\s*(\d+\.?\d*)',           # $12.99
                    r'(\d+\.?\d*)\s*\$',           # 12.99 $
                    r'Price:\s*\$\s*(\d+\.?\d*)',  # Price: $12.99
                ]

                for pattern in price_patterns:
                    match = re.search(pattern, snippet)
                    if match:
                        try:
                            price = float(match.group(1))
                            break
                        except:
                            pass

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
                print(f"Amazon: Found {len(results)} products via Google site search")
            else:
                print("Amazon: No product pages found in Google results")

            return results

        except Exception as e:
            print(f"Amazon scrape error: {e}")
            return []
