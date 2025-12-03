import schedule
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from database.connection import SessionLocal
from database.models import Idea, Competitor
from scrapers.registry import ScraperRegistry
from llm.matcher import ConceptMatcher
from notifications.email import EmailNotifier
from config.settings import settings

class DailyRunner:
    def __init__(self):
        self.matcher = ConceptMatcher()
        self.notifier = EmailNotifier()

    def check_all_ideas(self):
        """Main job - runs daily"""
        print(f"[{datetime.now()}] Starting daily check...")

        db = SessionLocal()
        ideas = db.query(Idea).all()

        for idea in ideas:
            print(f"Checking idea #{idea.id}...")
            new_competitors = self._scan_for_idea(idea, db)

            if new_competitors:
                self.notifier.send_report(idea.user_description, new_competitors)

            idea.last_checked = datetime.utcnow()
            db.commit()

        db.close()
        print("✓ Daily check complete")

    def _is_already_tracked(self, idea_id: int, url: str, db) -> bool:
        """Check if product is already tracked"""
        return db.query(Competitor).filter_by(
            idea_id=idea_id,
            url=url
        ).first() is not None

    def _save_competitor(self, idea_id: int, product: dict, source_name: str, similarity: dict, db) -> dict:
        """Save competitor to database and return dict for notification"""
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

        return {
            "name": product["name"],
            "source": source_name,
            "url": product["url"],
            "price": product.get("price"),
            "similarity_score": similarity["score"],
            "reasoning": similarity["reasoning"]
        }

    def _run_single_scraper(self, source_name: str, scraper, search_query: str) -> tuple:
        """Run a single scraper and return results with source name"""
        try:
            results = scraper.search(search_query)
            return (source_name, results)
        except Exception as e:
            print(f"Error scraping {source_name}: {e}")
            return (source_name, [])

    def _scan_for_idea(self, idea: Idea, db) -> list:
        """Scan all sources for one idea (scrapers run in parallel)"""
        import json
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

            # Process results as they complete
            for future in as_completed(futures):
                source_name, results = future.result()

                for product in results:
                    if self._is_already_tracked(idea.id, product["url"], db):
                        continue

                    similarity = self.matcher.calculate_similarity(
                        idea.user_description,
                        product
                    )

                    if similarity["score"] >= settings.SIMILARITY_THRESHOLD:
                        competitor_data = self._save_competitor(
                            idea.id, product, source_name, similarity, db
                        )
                        new_competitors.append(competitor_data)

        db.commit()
        return new_competitors

    def start(self):
        """Run scheduler in background"""
        schedule.every().day.at("09:00").do(self.check_all_ideas)

        print("📅 Scheduler started - checking daily at 9 AM")
        while True:
            schedule.run_pending()
            time.sleep(60)
