#!/usr/bin/env python3
"""
Test Google site search approach for AliExpress products
"""
import sys
import os
import requests
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_google_site_search():
    """Test searching AliExpress via Google site search"""
    SERPER_API_KEY = os.getenv('SERPER_API_KEY')

    if not SERPER_API_KEY:
        print("❌ SERPER_API_KEY not found in .env")
        return False

    keywords = "bluetooth speaker"
    search_query = f"site:aliexpress.com {keywords}"

    print("=" * 60)
    print("Testing Google Site Search for AliExpress")
    print("=" * 60)
    print(f"\nSearch query: '{search_query}'")
    print("-" * 60)

    url = "https://google.serper.dev/search"
    payload = {"q": search_query, "num": 15}
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"❌ Serper returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False

        data = response.json()
        results = []

        for item in data.get("organic", []):
            item_url = item.get("link", "")

            # Only include actual product pages
            if "/item/" not in item_url.lower():
                continue

            title = item.get("title", "")
            snippet = item.get("snippet", "")

            # Try to extract price from snippet
            price = None
            price_patterns = [
                r'\$\s*(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*USD',
                r'US\s*\$\s*(\d+\.?\d*)',
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

            if len(results) >= 10:
                break

        print(f"\n{'='*60}")
        print(f"Results: {len(results)} products found")
        print("=" * 60)

        if results:
            print("\n✅ SUCCESS - Products found via Google:")
            for i, product in enumerate(results, 1):
                print(f"\n{i}. {product['name'][:80]}")
                print(f"   URL: {product['url'][:100]}")
                print(f"   Price: ${product['price']}" if product['price'] else "   Price: N/A")
                print(f"   Description: {product['description'][:100]}...")
            return True
        else:
            print("\n❌ FAILED - No products found")
            print("Raw response organic results:")
            print(data.get("organic", []))
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_google_site_search()
    sys.exit(0 if success else 1)
