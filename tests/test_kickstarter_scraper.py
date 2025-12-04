#!/usr/bin/env python3
"""
Standalone test for Kickstarter scraper using Google site search
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.kickstarter import KickstarterScraper
from dotenv import load_dotenv

load_dotenv()

def test_kickstarter_search():
    """Test Kickstarter scraper with Google site search approach"""
    scraper = KickstarterScraper()

    print("=" * 60)
    print("Testing Kickstarter Scraper (Google Site Search)")
    print("=" * 60)

    keywords = "smart water bottle"
    print(f"\nSearching for: '{keywords}'")
    print("-" * 60)

    results = scraper.search(keywords)

    print(f"\n{'='*60}")
    print(f"Results: {len(results)} projects found")
    print("=" * 60)

    if results:
        print("\n✅ SUCCESS - Kickstarter projects found:")
        for i, project in enumerate(results, 1):
            print(f"\n{i}. {project['name'][:80]}")
            print(f"   URL: {project['url'][:100]}")
            print(f"   Funding: ${project['price']:,.0f}" if project['price'] else "   Funding: N/A")
            print(f"   Description: {project['description'][:100]}...")
        return True
    else:
        print("\n❌ FAILED - No projects found")
        print("This could mean:")
        print("1. No Kickstarter projects match this search")
        print("2. Serper API issue")
        print("3. Google returned no results for site:kickstarter.com")
        return False

if __name__ == "__main__":
    success = test_kickstarter_search()
    sys.exit(0 if success else 1)
