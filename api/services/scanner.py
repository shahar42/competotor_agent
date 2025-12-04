import json
import logging
from sqlalchemy.orm import Session
from database.models import Idea, Competitor, User
from llm.matcher import ConceptMatcher
from scrapers.registry import ScraperRegistry
from config.settings import settings
from notifications.email import EmailService

logger = logging.getLogger(__name__)

def run_scan_for_idea(idea_id: int, db: Session, image_base64: str = None):
    """
    Orchestrates the full scanning process for a single idea:
    1. Extract concepts (if not already done)
    2. Scrape sources
    3. Filter noise
    4. Calculate similarity
    5. Save results
    6. Send email if new competitors found
    """
    try:
        idea = db.query(Idea).get(idea_id)
        if not idea:
            logger.error(f"Idea {idea_id} not found")
            return

        matcher = ConceptMatcher()
        scraper_registry = ScraperRegistry()
        
        # 1. Concept Extraction (only if not already extracted)
        # Note: In MVP, we might re-extract if it's empty.
        if not idea.extracted_concepts:
            print(f"Extracting concepts for Idea #{idea.id} (Image provided: {bool(image_base64)})")
            concepts = matcher.extract_concepts(idea.user_description, image_base64)
            idea.extracted_concepts = json.dumps(concepts)
            # Save negative keywords if available
            if 'negative_keywords' in concepts:
                idea.negative_keywords = json.dumps(concepts['negative_keywords'])
            db.commit()
        else:
            concepts = json.loads(idea.extracted_concepts)

        search_keywords = concepts.get('search_keywords', [])
        negative_keywords = concepts.get('negative_keywords', [])
        
        if not search_keywords:
            logger.warning(f"No search keywords for idea {idea_id}")
            return

        # 2. Scrape Sources
        # Combine keywords into a single string for scrapers that expect it
        query = " ".join(search_keywords[:3]) # Use top 3 for broader search
        
        logger.info(f"Scanning for idea {idea_id} with query: {query}")
        
        all_scrapers = scraper_registry.get_all_scrapers()
        raw_results = []

        for scraper_name, scraper in all_scrapers:
            try:
                print(f"Starting {scraper_name} scraper...")
                results = scraper.search(query)
                print(f"{scraper_name}: Found {len(results)} results")
                # Tag results with source
                for r in results:
                    r['source'] = scraper_name
                raw_results.extend(results)
            except Exception as e:
                logger.error(f"Scraper {scraper_name} failed: {e}")
                print(f"ERROR in {scraper_name}: {e}")

        # 3. Filter Noise
        clean_results = matcher.filter_noise(raw_results, negative_keywords)
        logger.info(f"Filtered {len(raw_results)} results down to {len(clean_results)}")

        # Limit to top 15 products to prevent long processing times
        MAX_PRODUCTS = 15
        if len(clean_results) > MAX_PRODUCTS:
            logger.info(f"Limiting to {MAX_PRODUCTS} products (had {len(clean_results)})")
            clean_results = clean_results[:MAX_PRODUCTS]

        # 4. Calculate Similarity & Save
        new_competitors = []
        print(f"Starting similarity matching for {len(clean_results)} products...")

        for i, product in enumerate(clean_results, 1):
            # Skip if URL already exists for this idea (deduplication)
            existing = db.query(Competitor).filter(
                Competitor.idea_id == idea.id,
                Competitor.url == product.get('url')
            ).first()
            
            if existing:
                continue

            print(f"Matching product {i}/{len(clean_results)}: {product.get('name', 'Unknown')[:50]}...")
            similarity = matcher.calculate_similarity(idea.user_description, product)
            
            if similarity.get('score', 0) >= settings.SIMILARITY_THRESHOLD:
                competitor = Competitor(
                    idea_id=idea.id,
                    product_name=product.get('name'),
                    source=product.get('source'),
                    url=product.get('url'),
                    price=product.get('price'),
                    similarity_score=similarity.get('score'),
                    reasoning=similarity.get('reasoning'),
                    is_relevant=None # Pending user feedback
                )
                db.add(competitor)
                new_competitors.append(competitor)
        
        print(f"Saving {len(new_competitors)} new competitors to database...")
        db.commit()
        print("Database commit complete")

        # 5. Notify User
        if new_competitors:
            # Limit email to top 6 best matches (sorted by similarity score)
            MAX_EMAIL_COMPETITORS = 6
            top_competitors = sorted(new_competitors, key=lambda x: x.similarity_score, reverse=True)[:MAX_EMAIL_COMPETITORS]

            print(f"Preparing to send email with top {len(top_competitors)} of {len(new_competitors)} competitors...")
            # Fetch user email
            user = db.query(User).get(idea.user_id)
            if user:
                email_service = EmailService()
                print(f"Sending email to {user.email} with {len(top_competitors)} competitors...")
                email_service.send_alert(
                    to_email=user.email,
                    idea_title=concepts.get('core_function', 'Your Idea'),
                    competitors=top_competitors
                )
                print("Email sent successfully")
        else:
            print("No new competitors found above threshold - no email sent")

        logger.info(f"Scan complete for idea {idea_id}. Found {len(new_competitors)} new competitors.")
        print(f"✅ Scan complete! Found {len(new_competitors)} competitors.")

    except Exception as e:
        logger.error(f"Scan failed for idea {idea_id}: {e}")
        # In production, we would retry or flag error
