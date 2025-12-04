import schedule
import time
import hashlib
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from database.connection import SessionLocal
from database.models import Idea, Competitor, ScanHistory
from scrapers.registry import ScraperRegistry
from llm.matcher import ConceptMatcher
from notifications.email import EmailService
from config.settings import settings

class DailyRunner:
    def __init__(self):
        self.matcher = ConceptMatcher()
        self.notifier = EmailService()

    def _get_url_hash(self, url: str) -> str:
        """Generate a consistent 32-char hash for a URL"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def check_all_ideas(self):
        """Main job - runs daily, checks for ideas needing weekly updates"""
        print(f"[{datetime.now()}] Starting daily monitoring check...")

        db = SessionLocal()
        
        # Only fetch ideas that have monitoring enabled and are within the valid window
        now = datetime.utcnow()
        ideas = db.query(Idea).filter(
            Idea.monitoring_enabled == True,
            Idea.monitoring_ends_at > now
        ).all()

        count = 0
        for idea in ideas:
            # Enforce Weekly Frequency: Check if 7 days have passed since last check
            # Handle case where last_checked is None (shouldn't happen due to default, but safe)
            last_checked = idea.last_checked or datetime.min
            days_since_last = (now - last_checked).days
            
            if days_since_last < 7:
                print(f"Skipping Idea #{idea.id} (Checked {days_since_last} days ago)")
                continue

            print(f"Checking monitored Idea #{idea.id}...")
            try:
                new_competitors = self._scan_for_idea(idea, db)
                if new_competitors:
                    print(f"Found {len(new_competitors)} new matches for Idea #{idea.id}")
                    if idea.user and idea.user.email:
                        self.notifier.send_alert(idea.user.email, idea.user_description, new_competitors)
                    else:
                        print(f"WARNING: Idea #{idea.id} has no user email associated.")
                else:
                    print(f"No new matches for Idea #{idea.id}")
                
                idea.last_checked = datetime.utcnow()
                db.commit()
                count += 1
            except Exception as e:
                print(f"Error checking Idea #{idea.id}: {e}")
                import traceback
                traceback.print_exc()

        db.close()
        print(f"✓ Daily check complete. Scanned {count} ideas.")

    def _is_already_seen(self, idea_id: int, url: str, db) -> bool:
        """
        Check scan history. 
        Returns True if we have EVER seen this URL for this Idea (relevant or not).
        """
        url_hash = self._get_url_hash(url)
        
        # Check history (efficient index lookup)
        exists = db.query(ScanHistory).filter_by(
            idea_id=idea_id,
            url_hash=url_hash
        ).first()
        
        if exists:
            # Update last_seen for analytics/maintenance
            exists.last_seen = datetime.utcnow()
            # We don't commit here to avoid spamming DB writes, commit happens at end of scan
            return True
            
        return False

    def _record_scan_result(self, idea_id: int, url: str, is_relevant: bool, db):
        """Log that we have processed this product"""
        url_hash = self._get_url_hash(url)
        history = ScanHistory(
            idea_id=idea_id,
            url_hash=url_hash,
            is_relevant=is_relevant
        )
        db.add(history)

    def _save_competitor(self, idea_id: int, product: dict, source_name: str, similarity: dict, db) -> Competitor:
        """Save competitor to database and return the Object"""
        comp = Competitor(
            idea_id=idea_id,
            product_name=product["name"],
            source=source_name,
            url=product["url"],
            price=product.get("price"),
            similarity_score=similarity["score"],
            reasoning=similarity["reasoning"]
        )
        db.add(comp)
        return comp

    def _run_single_scraper(self, source_name: str, scraper, search_query: str) -> tuple:
        """Run a single scraper and return results with source name"""
        try:
            results = scraper.search(search_query)
            return (source_name, results)
        except Exception as e:
            print(f"Error scraping {source_name}: {e}")
            return (source_name, [])

    def _scan_for_idea(self, idea: Idea, db) -> list:
        """Scan all sources for one idea"""
        if not idea.extracted_concepts:
            print(f"Idea #{idea.id} has no extracted concepts. Skipping.")
            return []

        concepts = json.loads(idea.extracted_concepts)
        search_query = " ".join(concepts.get("search_keywords", []))

        new_competitors = []
        registry = ScraperRegistry()
        all_scrapers = list(registry.get_all_scrapers())

        # Run all scrapers in parallel
        with ThreadPoolExecutor(max_workers=len(all_scrapers)) as executor:
            futures = {
                executor.submit(self._run_single_scraper, source_name, scraper, search_query): source_name
                for source_name, scraper in all_scrapers
            }

            for future in as_completed(futures):
                source_name, results = future.result()

                for product in results:
                    # 1. Smart Diff: Check if seen before (Hash check)
                    if self._is_already_seen(idea.id, product["url"], db):
                        continue

                    # 2. If New: Run LLM Matcher
                    similarity = self.matcher.calculate_similarity(
                        idea.user_description,
                        product
                    )
                    
                    is_match = similarity["score"] >= settings.SIMILARITY_THRESHOLD

                    # 3. Record History (Firewall for next time)
                    self._record_scan_result(idea.id, product["url"], is_match, db)

                    # 4. If Match: Save Competitor & Queue for Alert
                    if is_match:
                        comp = self._save_competitor(
                            idea.id, product, source_name, similarity, db
                        )
                        new_competitors.append(comp)

        db.commit()
        return new_competitors

    def start(self):
        """Run scheduler in background"""
        schedule.every().day.at("09:00").do(self.check_all_ideas)

        print("📅 Monitoring Service Started - Checking daily at 09:00 UTC")
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    # Entry point for standalone worker
    runner = DailyRunner()
    runner.start()
