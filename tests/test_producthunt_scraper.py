#!/usr/bin/env python3
"""
Standalone test for ProductHunt scraper using Google site search
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.producthunt import ProductHuntScraper
from dotenv import load_dotenv

load_dotenv()

def test_producthunt_search():
    """Test ProductHunt scraper with Google site search approach"""
    scraper = ProductHuntScraper()

    print("=" * 60)
    print("Testing ProductHunt Scraper (Google Site Search)")
    print("=" * 60)

    keywords = "AI writing assistant"
    print(f"\nSearching for: '{keywords}'")
    print("-" * 60)

    results = scraper.search(keywords)

    print(f"\n{'='*60}")
    print(f"Results: {len(results)} products found")
    print("=" * 60)

    if results:
        print("\n✅ SUCCESS - ProductHunt products found:")
        for i, product in enumerate(results, 1):
            print(f"\n{i}. {product['name'][:80]}")
            print(f"   URL: {product['url'][:100]}")
            print(f"   Description: {product['description'][:100]}...")
        return True
    else:
        print("\n❌ FAILED - No products found")
        return False

if __name__ == "__main__":
    success = test_producthunt_search()
    sys.exit(0 if success else 1)
