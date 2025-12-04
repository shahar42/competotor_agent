#!/usr/bin/env python3
"""
Test the integrated AliExpress scraper (using Google site search)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.aliexpress import AliExpressScraper
from dotenv import load_dotenv

load_dotenv()

def test_integrated_scraper():
    """Test AliExpress scraper with Google site search approach"""
    scraper = AliExpressScraper()

    print("=" * 60)
    print("Testing Integrated AliExpress Scraper (Google Site Search)")
    print("=" * 60)

    keywords = "smart watch"
    print(f"\nSearching for: '{keywords}'")
    print("-" * 60)

    results = scraper.search(keywords)

    print(f"\n{'='*60}")
    print(f"Results: {len(results)} products found")
    print("=" * 60)

    if results:
        print("\n✅ SUCCESS - AliExpress scraper working:")
        for i, product in enumerate(results, 1):
            print(f"\n{i}. {product['name'][:80]}")
            print(f"   URL: {product['url'][:100]}")
            print(f"   Price: ${product['price']}" if product['price'] else "   Price: N/A")
        return True
    else:
        print("\n❌ FAILED - No products found")
        return False

if __name__ == "__main__":
    success = test_integrated_scraper()
    sys.exit(0 if success else 1)
