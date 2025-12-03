import requests
from scrapers.base_scraper import BaseScraper
from config.settings import settings

class SerperScraper(BaseScraper):
    """Google search via Serper.dev API - filtered for product pages only"""

    def _is_product_url(self, url: str) -> bool:
        """Check if URL is likely a product page"""
        if not url:
            return False

        url_lower = url.lower()

        # Product indicators
        product_keywords = [
            'product', 'buy', 'shop', 'store',
            'item', 'purchase', 'cart', '/p/',
            '/products/', 'amazon.com', 'ebay.com',
            'etsy.com', 'walmart.com', 'target.com',
            'aliexpress.com', 'shopify'
        ]

        # Filter out non-product pages
        exclude_keywords = [
            'blog', 'article', 'news', 'trends',
            'review', 'about', 'contact', 'forum',
            'reddit.com', 'youtube.com', 'pinterest.com',
            'trendhunter.com', 'instructables.com'
        ]

        # Exclude if matches exclusion list
        if any(keyword in url_lower for keyword in exclude_keywords):
            return False

        # Include if matches product indicators
        return any(keyword in url_lower for keyword in product_keywords)

    def search(self, keywords: str) -> list:
        if not settings.SERPER_API_KEY:
            return []

        url = "https://google.serper.dev/search"
        payload = {"q": keywords + " buy product"}
        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)
            data = response.json()

            results = []
            for item in data.get("organic", [])[:20]:  # Fetch more to account for filtering
                item_url = item.get("link")

                # Only include if it's a product URL
                if self._is_product_url(item_url):
                    results.append({
                        "name": item.get("title"),
                        "url": item_url,
                        "description": item.get("snippet"),
                        "price": None
                    })

                # Stop once we have 10 valid products
                if len(results) >= 10:
                    break

            if not results:
                print("Google: No product pages found (all results were articles/blogs)")

            return results
        except Exception as e:
            print(f"Serper scrape error: {e}")
            return []
