#!/usr/bin/env python3
"""
Local test for idea submission flow with mocked LLM to avoid quota limits.
Tests the full pipeline: concept extraction → scraping → matching → email
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from database.connection import SessionLocal, init_db
from database.models import User, Idea, Competitor, ScanHistory
from api.services.scanner import run_scan_for_idea
import json

def setup_test_user():
    """Create test user in database"""
    db = SessionLocal()

    # Clean up existing test data (cascade delete: competitors → scan_history → ideas → user)
    existing_user = db.query(User).filter(User.email == "test@example.com").first()
    if existing_user:
        for idea in db.query(Idea).filter(Idea.user_id == existing_user.id).all():
            db.query(Competitor).filter(Competitor.idea_id == idea.id).delete()
            db.query(ScanHistory).filter(ScanHistory.idea_id == idea.id).delete()
        db.query(Idea).filter(Idea.user_id == existing_user.id).delete()
        db.query(User).filter(User.email == "test@example.com").delete()
        db.commit()

    user = User(
        email="test@example.com",
        is_active=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    print(f"✓ Created test user: {user.email} (ID: {user.id})")
    return user.id, db

def create_test_idea(user_id, db):
    """Create test idea"""
    idea = Idea(
        user_id=user_id,
        user_description="A smart lamp that monitors ocean conditions for surfers"
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)

    print(f"✓ Created test idea (ID: {idea.id})")
    return idea.id

def mock_gemini_response(prompt: str, **kwargs):
    """Mock Gemini responses based on prompt content"""

    # Concept extraction
    if "Extract key concepts" in prompt:
        return json.dumps({
            "core_function": "Smart surfing conditions monitor lamp",
            "key_features": ["ocean monitoring", "LED indicators", "surf alerts"],
            "search_keywords": ["surf lamp", "ocean monitor", "surf conditions", "smart lamp", "wave alert"],
            "negative_keywords": ["surfboard", "wax", "leash", "wetsuit"],
            "category": "Smart Home & Sports"
        })

    # Similarity calculation
    elif "Compare this invention" in prompt:
        # Simulate finding a moderate match
        return json.dumps({
            "score": 65,
            "reasoning": "Both are lamps with monitoring features, but competitor focuses on general home automation while user's idea is surf-specific",
            "user_advantage": "Specialized for surfers with ocean condition monitoring"
        })

    # Verdict
    elif "brutal startup advisor" in prompt:
        return "Verdict: PROCEED CAUTIOUSLY - moderate competition exists but your surf-specific angle could carve a niche market."

    # Gap analysis
    elif "Market Gap Analysis" in prompt:
        return "Competitors suffer from generic alerts not tailored to surfers. Your idea solves this by providing surf-specific ocean monitoring. Opportunity: Market as 'The only lamp that knows when to surf'."

    return "{}"

def test_with_mocked_llm():
    """Test full flow with mocked LLM (no quota usage)"""
    print("\n=== Testing with MOCKED LLM (no quota) ===\n")

    init_db()
    user_id, db = setup_test_user()
    idea_id = create_test_idea(user_id, db)

    # Mock the Gemini client
    with patch('llm.client.GeminiClient.generate', side_effect=mock_gemini_response):
        with patch('notifications.email.EmailService.send_alert') as mock_email:
            with patch('notifications.email.EmailService.send_no_matches_email') as mock_no_match:

                print("\n🔍 Running scan with mocked LLM...")

                try:
                    run_scan_for_idea(idea_id, db)

                    # Check what happened
                    if mock_email.called:
                        print(f"\n✓ Email would be sent with competitors")
                        call_args = mock_email.call_args
                        competitors = call_args[1]['competitors']
                        print(f"  Found {len(competitors)} competitors")
                        for comp in competitors:
                            print(f"    - {comp.product_name} ({comp.similarity_score}%)")

                    if mock_no_match.called:
                        print(f"\n✓ 'No matches' email would be sent")

                    if not mock_email.called and not mock_no_match.called:
                        print("\n⚠️  No email attempted - check scraper results")

                except Exception as e:
                    print(f"\n❌ Scan failed: {e}")
                    import traceback
                    traceback.print_exc()

    db.close()
    print("\n=== Test Complete ===\n")

def test_real_llm_single_product():
    """Test with REAL LLM but limit to 1 product (uses ~3 API calls)"""
    print("\n=== Testing with REAL LLM (limited quota usage) ===\n")
    print("⚠️  This will use ~3 Gemini API calls")

    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted")
        return

    init_db()
    user_id, db = setup_test_user()
    idea_id = create_test_idea(user_id, db)

    # Patch scrapers to return only 1 product
    def mock_search(query):
        return [{
            'name': 'Smart Ocean Monitor Display',
            'url': 'https://example.com/product',
            'price': '49.99',
            'description': 'LED display showing ocean conditions'
        }]

    with patch('scrapers.serper.SerperScraper.search', side_effect=mock_search):
        with patch('scrapers.aliexpress.AliExpressScraper.search', return_value=[]):
            with patch('scrapers.kickstarter.KickstarterScraper.search', return_value=[]):
                with patch('notifications.email.EmailService.send_alert') as mock_email:

                    print("\n🔍 Running scan with REAL LLM (1 product only)...")

                    try:
                        run_scan_for_idea(idea_id, db)

                        if mock_email.called:
                            print(f"\n✓ Email would be sent!")
                            call_args = mock_email.call_args
                            print(f"  To: {call_args[1]['to_email']}")
                            competitors = call_args[1]['competitors']
                            print(f"  Competitors: {len(competitors)}")
                        else:
                            print(f"\n⚠️  No email sent")

                    except Exception as e:
                        print(f"\n❌ Failed: {e}")
                        import traceback
                        traceback.print_exc()

    db.close()
    print("\n=== Test Complete ===\n")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Mocked LLM (no quota usage)")
    print("2. Real LLM with 1 product (~3 API calls)")

    choice = input("Choice (1 or 2): ")

    if choice == "1":
        test_with_mocked_llm()
    elif choice == "2":
        test_real_llm_single_product()
    else:
        print("Invalid choice")
