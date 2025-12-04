#!/usr/bin/env python3
"""
Standalone test for AliExpress scraper using Selenium
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.aliexpress import AliExpressScraper
from dotenv import load_dotenv

load_dotenv()

def test_aliexpress_search():
    """Test AliExpress scraper with a sample search"""
    scraper = AliExpressScraper()

    print("=" * 60)
    print("Testing AliExpress Scraper (Selenium)")
    print("=" * 60)

    # Test with a simple search term
    keywords = "bluetooth speaker"
    print(f"\nSearching for: '{keywords}'")
    print("-" * 60)

    results = scraper.search(keywords)

    print(f"\n{'='*60}")
    print(f"Results: {len(results)} products found")
    print("=" * 60)

    if results:
        print("\n✅ SUCCESS - Products extracted:")
        for i, product in enumerate(results, 1):
            print(f"\n{i}. {product['name']}")
            print(f"   URL: {product['url']}")
            print(f"   Price: ${product['price']}" if product['price'] else "   Price: N/A")
            print(f"   Description: {product['description'][:100]}...")
    else:
        print("\n❌ FAILED - No products extracted")
        print("This could mean:")
        print("1. AliExpress blocked the request")
        print("2. Page structure changed")
        print("3. Selenium/Chrome not properly configured")
        return False

    return True

if __name__ == "__main__":
    success = test_aliexpress_search()
    sys.exit(0 if success else 1)
