import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        if not idea.extracted_concepts:
            print(f"Extracting concepts for Idea #{idea.id} (Image provided: {bool(image_base64)})")
            concepts = matcher.extract_concepts(idea.user_description, image_base64)
            idea.extracted_concepts = json.dumps(concepts)
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
        query = " ".join(search_keywords[:3]) 
        logger.info(f"Scanning for idea {idea_id} with query: {query}")
        
        all_scrapers = scraper_registry.get_all_scrapers()
        raw_results = []

        # Run scrapers in parallel (Optional optimization, but good practice)
        with ThreadPoolExecutor(max_workers=len(all_scrapers)) as executor:
            futures = {executor.submit(scraper.search, query): name for name, scraper in all_scrapers}
            
            for future in as_completed(futures):
                scraper_name = futures[future]
                try:
                    print(f"Starting {scraper_name} scraper...")
                    results = future.result()
                    print(f"{scraper_name}: Found {len(results)} results")
                    for r in results:
                        r['source'] = scraper_name
                    raw_results.extend(results)
                except Exception as e:
                    logger.error(f"Scraper {scraper_name} failed: {e}")
                    print(f"ERROR in {scraper_name}: {e}")

        # 3. Filter Noise
        clean_results = matcher.filter_noise(raw_results, negative_keywords)
        logger.info(f"Filtered {len(raw_results)} results down to {len(clean_results)}")

        # Limit to top 15 products
        MAX_PRODUCTS = 15
        if len(clean_results) > MAX_PRODUCTS:
            logger.info(f"Limiting to {MAX_PRODUCTS} products (had {len(clean_results)})")
            clean_results = clean_results[:MAX_PRODUCTS]

        # 4. Calculate Similarity & Save (Parallelized)
        new_competitors = []
        print(f"Starting parallel similarity matching for {len(clean_results)} products...")

        def process_product(product):
            # Skip if URL already exists for this idea (deduplication)
            # Note: DB check inside thread is tricky with shared session.
            # Ideally check before, but for MVP valid to just proceed or create new session.
            # We will trust the outer loop filtered duplicates or just re-check later.
            # Actually, let's just run the LLM check.

            print(f"Matching: {product.get('name', 'Unknown')[:30]}...")
            similarity = matcher.calculate_similarity(idea.user_description, product)
            return product, similarity

        # Use ThreadPool for LLM calls
        with ThreadPoolExecutor(max_workers=1) as executor:
            future_to_product = {
                executor.submit(process_product, p): p 
                for p in clean_results 
                # Pre-check DB to avoid unnecessary threads
                if not db.query(Competitor).filter(Competitor.idea_id == idea.id, Competitor.url == p.get('url')).first()
            }

            for future in as_completed(future_to_product):
                try:
                    product, similarity = future.result()
                    
                    if similarity.get('score', 0) >= settings.SIMILARITY_THRESHOLD:
                        competitor = Competitor(
                            idea_id=idea.id,
                            product_name=product.get('name'),
                            source=product.get('source'),
                            url=product.get('url'),
                            price=product.get('price'),
                            similarity_score=similarity.get('score'),
                            reasoning=similarity.get('reasoning'),
                            is_relevant=None
                        )
                        new_competitors.append(competitor)
                except Exception as e:
                    print(f"Error matching product: {e}")

        # Save all at once
        if new_competitors:
            print(f"Saving {len(new_competitors)} new competitors to database...")
            db.add_all(new_competitors)
            db.commit()
            print("Database commit complete")

        # 5. Notify User
        if new_competitors:
            MAX_EMAIL_COMPETITORS = 4
            top_competitors = sorted(new_competitors, key=lambda x: x.similarity_score, reverse=True)[:MAX_EMAIL_COMPETITORS]
            
            # Generate Verdict (If Enabled)
            verdict = None
            if settings.ENABLE_VERDICT:
                try:
                    print("Generating AI Verdict...")
                    competitor_dicts = [
                        {"product_name": c.product_name, "similarity_score": c.similarity_score} 
                        for c in top_competitors
                    ]
                    verdict = matcher.generate_verdict(concepts.get('core_function', idea.user_description), competitor_dicts)
                    print(f"Verdict: {verdict}")
                except Exception as e:
                    logger.error(f"Verdict generation failed: {e}")
                    print(f"Verdict generation ERROR: {e}")
            
            # Gap Hunter (If Enabled)
            gap_analysis = None
            if settings.ENABLE_GAP_HUNT and top_competitors:
                try:
                    # Target the #1 competitor
                    top_comp = top_competitors[0]
                    print(f"Gap Hunter: Hunting complaints for {top_comp.product_name}...")
                    
                    # The "Hate Search" - Search Google for negative sentiment
                    # We reuse the Google Scraper logic but with a specific query
                    hate_query = f"{top_comp.product_name} review problem OR broken OR bad OR disappointed OR hate"
                    
                    # We need a quick way to search. We can instantiate SerperScraper directly or use registry.
                    # For simplicity/robustness, let's use the SerperScraper directly if available.
                    from scrapers.serper import SerperScraper
                    serper = SerperScraper()
                    
                    # Search (limit to 5 results for speed)
                    complaint_results = serper.search(hate_query)
                    
                    if complaint_results:
                        # Extract snippets
                        snippets = [r.get('description', '') or r.get('name', '') for r in complaint_results]
                        # Filter empty snippets
                        snippets = [s for s in snippets if s]
                        
                        if snippets:
                            gap_analysis = matcher.analyze_gaps(
                                user_idea=idea.user_description,
                                competitor_name=top_comp.product_name,
                                complaints=snippets
                            )
                            print(f"Gap Analysis: {gap_analysis}")
                        else:
                            print("Gap Hunter: No complaint snippets found.")
                    else:
                        print("Gap Hunter: No negative results found.")

                except Exception as e:
                    logger.error(f"Gap Hunter failed: {e}")
                    print(f"Gap Hunter Error: {e}")

            print(f"Preparing email with top {len(top_competitors)} competitors...")
            user = db.query(User).get(idea.user_id)
            if user:
                email_service = EmailService()
                print(f"Sending email to {user.email}...")
                email_service.send_alert(
                    to_email=user.email,
                    idea_title=concepts.get('core_function', 'Your Idea'),
                    competitors=top_competitors,
                    verdict=verdict,
                    gap_analysis=gap_analysis
                )
                print("Email sent successfully")
        else:
            print("No competitors found - sending 'no matches' email")
            user = db.query(User).get(idea.user_id)
            if user:
                email_service = EmailService()
                email_service.send_no_matches_email(
                    to_email=user.email,
                    idea_title=concepts.get('core_function', 'Your Idea')
                )
                print("No-matches email sent successfully")

        logger.info(f"Scan complete for idea {idea_id}. Found {len(new_competitors)} new competitors.")
        print(f"✅ Scan complete! Found {len(new_competitors)} competitors.")

    except Exception as e:
        logger.error(f"Scan failed for idea {idea_id}: {e}")
