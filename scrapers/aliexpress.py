import requests
from bs4 import BeautifulSoup
import re
from scrapers.base_scraper import BaseScraper
from config.settings import settings

class AliExpressScraper(BaseScraper):
    def search(self, keywords: str) -> list:
        """
        AliExpress scraper - attempts to extract product data.
        Note: AliExpress has anti-bot protection, so this may return empty results.
        For production, consider using AliExpress API or a scraping service.
        """
        # Use a more realistic browser user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        # Try mobile site - often less protected
        url = f"https://m.aliexpress.com/wholesale/{keywords.replace(' ', '-')}.html"

        try:
            response = requests.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)

            if response.status_code != 200:
                print(f"AliExpress returned status {response.status_code}")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            results = []

            # Try multiple selector patterns (AliExpress structure varies)
            product_cards = (
                soup.find_all('div', class_=re.compile(r'product.*item', re.I)) or
                soup.find_all('a', class_=re.compile(r'product.*link', re.I)) or
                soup.find_all('div', attrs={'data-product-id': True})
            )

            for card in product_cards[:10]:  # Limit to 10
                try:
                    # Extract product name
                    name_elem = (
                        card.find('h1') or
                        card.find('h2') or
                        card.find('h3') or
                        card.find('div', class_=re.compile(r'title', re.I)) or
                        card.find('a', class_=re.compile(r'title', re.I))
                    )
                    name = name_elem.get_text(strip=True) if name_elem else None

                    # Extract URL
                    link_elem = card.find('a', href=True) if card.name != 'a' else card
                    url = link_elem['href'] if link_elem else None
                    if url and not url.startswith('http'):
                        url = f"https://www.aliexpress.com{url}"

                    # Extract price
                    price_elem = card.find(class_=re.compile(r'price', re.I))
                    price = None
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        # Extract numeric value
                        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                        if price_match:
                            try:
                                price = float(price_match.group())
                            except:
                                pass

                    # Extract description (if available)
                    desc_elem = card.find(class_=re.compile(r'description|detail', re.I))
                    description = desc_elem.get_text(strip=True) if desc_elem else name

                    if name and url:
                        results.append({
                            "name": name,
                            "url": url,
                            "price": price,
                            "description": description or name
                        })

                except Exception as item_error:
                    # Skip malformed items
                    continue

            if not results:
                print(f"AliExpress: No products extracted from {len(product_cards)} cards found")

            return results

        except Exception as e:
            print(f"AliExpress scrape error: {e}")
            return []
