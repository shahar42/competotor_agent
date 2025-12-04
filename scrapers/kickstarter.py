import requests
import re
from scrapers.base_scraper import BaseScraper
from config.settings import settings

class KickstarterScraper(BaseScraper):
    """
    Kickstarter scraper using Google site search via Serper API.

    Same brilliant approach as AliExpress: Instead of fighting anti-bot protection,
    we use Google's index with 'site:kickstarter.com' queries.

    Benefits:
    - No CAPTCHA or anti-bot issues
    - Reuses existing Serper infrastructure
    - More reliable than direct scraping
    - Fast response times
    """

    def search(self, keywords: str) -> list:
        """
        Search Kickstarter projects via Google site search.
        Returns list of projects matching the base scraper format.
        """
        if not settings.SERPER_API_KEY:
            print("Kickstarter: Serper API key not configured")
            return []

        # Use Google site search to find Kickstarter projects
        search_query = f"site:kickstarter.com {keywords}"

        url = "https://google.serper.dev/search"
        payload = {"q": search_query, "num": 15}
        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)

            if response.status_code != 200:
                print(f"Kickstarter: Serper returned status {response.status_code}")
                return []

            data = response.json()
            results = []

            for item in data.get("organic", []):
                item_url = item.get("link", "")

                # Only include actual project pages (contain /projects/ in URL)
                if "/projects/" not in item_url.lower():
                    continue

                title = item.get("title", "")
                snippet = item.get("snippet", "")

                # Try to extract funding goal/pledged from snippet
                price = None
                price_patterns = [
                    r'\$\s*([\d,]+)',              # $12,345
                    r'([\d,]+)\s*pledged',         # 12,345 pledged
                    r'goal\s*\$\s*([\d,]+)',       # goal $50,000
                ]

                for pattern in price_patterns:
                    match = re.search(pattern, snippet)
                    if match:
                        try:
                            # Remove commas and convert to float
                            price_str = match.group(1).replace(',', '')
                            price = float(price_str)
                            break
                        except:
                            pass

                results.append({
                    "name": title,
                    "url": item_url,
                    "price": price,
                    "description": snippet
                })

                # Stop at 10 projects
                if len(results) >= 10:
                    break

            if results:
                print(f"Kickstarter: Found {len(results)} projects via Google site search")
            else:
                print("Kickstarter: No project pages found in Google results")

            return results

        except Exception as e:
            print(f"Kickstarter scrape error: {e}")
            return []
