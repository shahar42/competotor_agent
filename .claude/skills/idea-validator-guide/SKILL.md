---
name: idea-validator-guide
description: Quick guide for the Idea Validator agent system. Invoked when user asks about the validator system, how it works, architecture, components, or wants to understand the codebase in this directory.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
tags: [idea-validator, architecture, documentation, system-guide]
scope: project
---

# Idea Validator Agent System

An AI-powered system that validates if user invention ideas already exist by continuously monitoring multiple product sources.

## System Purpose

**What it does**: Takes user invention ideas, extracts core concepts using LLM, searches multiple platforms (AliExpress, Kickstarter, Google, US Patents), and sends daily email alerts when similar products or patents are found.

**Location**: `/home/shahar42/agent_product_scanner`

## Architecture Overview

```
User Input → Concept Extraction → Multi-Source Search → Similarity Scoring → Daily Monitoring → Email Alerts
```

### Pipeline Flow
1. **Onboarding** (bot.py) - User describes their idea
2. **Concept Extraction** (llm/matcher.py) - Gemini extracts core function, features, keywords
3. **Immediate Scan** - Searches all sources right away
4. **Storage** (SQLite) - Saves idea + found competitors
5. **Daily Monitoring** (scheduler/runner.py) - Runs at 9 AM daily
6. **Email Notifications** - Alerts when new competitors found

## Project Structure

```
agent_product_scanner/
├── bot.py                 # Main CLI - onboarding flow
├── main.py               # Entry point (bot or scheduler)
├── database/
│   ├── connection.py     # SQLAlchemy setup (SQLite)
│   └── models.py         # Idea & Competitor models
├── llm/
│   ├── client.py         # Gemini API wrapper
│   └── matcher.py        # Concept extraction & similarity
├── scrapers/
│   ├── base_scraper.py   # Abstract scraper interface
│   ├── registry.py       # Factory for all scrapers
│   ├── aliexpress.py     # AliExpress search
│   ├── kickstarter.py    # Kickstarter projects
│   ├── serper.py         # Google via Serper API
│   └── patents.py        # US Patents via PatentsView API
├── scheduler/
│   └── runner.py         # Daily job scheduler
├── notifications/
│   └── email.py          # Email alerts
└── config/
    └── settings.py       # Configuration

Database: idea_validator.db (SQLite)
```

## Database Schema

### Table: `ideas`
- id (PK)
- user_description (TEXT) - Full idea description
- extracted_concepts (TEXT) - JSON: {core_function, key_features, search_keywords, category}
- created_at, last_checked (DATETIME)

### Table: `competitors`
- id (PK)
- idea_id (FK → ideas.id)
- product_name, source (aliexpress/kickstarter/google/patents)
- url, price (nullable)
- similarity_score (0-100) - LLM-calculated match percentage
- reasoning (TEXT) - Why LLM thinks it's similar
- discovered_at (DATETIME)

## Key Components Explained

### 1. Concept Extraction (llm/matcher.py)
**ConceptMatcher.extract_concepts(user_description)**
- Uses Gemini to parse user's idea
- Returns structured JSON:
  ```json
  {
    "core_function": "what it does",
    "key_features": ["feature1", "feature2"],
    "search_keywords": ["term1", "term2", "term3", "term4", "term5"],
    "category": "product type"
  }
  ```

### 2. Similarity Scoring (llm/matcher.py)
**ConceptMatcher.calculate_similarity(user_idea, competitor_product)**
- Compares user idea vs found product
- Returns:
  ```json
  {
    "score": 85,  // 0-100 similarity
    "reasoning": "why they match",
    "user_advantage": "what makes user's idea unique"
  }
  ```
- Threshold: 60+ = considered competitor

### 3. Multi-Source Scraping (scrapers/)
**ScraperRegistry.get_all_scrapers()** returns:
- **AliExpress** - Web scraping + Selenium
- **Kickstarter** - Active projects search
- **Serper** - Google search via API with product URL filtering (excludes blogs/articles)
- **Patents** - US Patents via PatentsView API (completely free, no rate limits)

All inherit from `BaseScraper` with standard `.search(query)` method

**Note**: Serper scraper includes smart filtering to return only actual product pages, not blog articles or news sites. Patent scraper searches USPTO database for early-stage innovations. See detailed filtering logic in Scraper Implementation Notes below.

### 4. Daily Scheduler (scheduler/runner.py)
**DailyRunner.start()**
- Runs every day at 9:00 AM
- Checks all stored ideas
- For each idea:
  1. Search all sources with extracted keywords
  2. Calculate similarity for each result
  3. Save new competitors (≥60% match)
  4. Send email if new competitors found
  5. Update `last_checked` timestamp

## Usage & Commands

### Run Interactive Onboarding
```bash
python main.py
# or
python bot.py
```

**Flow**:
1. User describes invention idea
2. AI extracts concepts
3. User confirms extraction
4. Immediate scan across all sources
5. Shows results + similarity scores
6. Saves to database
7. Activates daily monitoring

### Start Scheduler (Background Monitoring)
```bash
python main.py schedule
```

Runs daily at 9 AM, checks all ideas, sends email alerts.

### Manual Database Inspection
```bash
# View all ideas
sqlite3 idea_validator.db "SELECT * FROM ideas;"

# View competitors for idea #1
sqlite3 idea_validator.db "SELECT * FROM competitors WHERE idea_id = 1;"

# Check last scan time
sqlite3 idea_validator.db "SELECT id, last_checked FROM ideas;"
```

## Environment Setup

### .env File (required)
```bash
GEMINI_API_KEY=your_api_key_here
SERPER_API_KEY=your_serper_key  # For Google search
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_TO=recipient@example.com
```

### Dependencies (requirements.txt)
- **requests** 2.31.0 - HTTP requests
- **beautifulsoup4** 4.12.0 - HTML parsing
- **selenium** 4.15.0 - Browser automation
- **google-generativeai** 0.3.0 - Gemini API
- **sqlalchemy** 2.0.0 - ORM
- **python-dotenv** 1.0.0 - Environment variables
- **schedule** 1.2.0 - Job scheduling
- **rich** 13.7.0 - CLI formatting

### Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Common Workflows

### Workflow 1: Add New Idea
```bash
python main.py
# Choose option 1: Add new idea
# Follow prompts
```

System will:
- Extract concepts
- Run immediate scan
- Store in database
- Enable daily monitoring

### Workflow 2: Check Current Ideas
```bash
sqlite3 idea_validator.db
sqlite> SELECT id, user_description, last_checked FROM ideas;
sqlite> SELECT product_name, source, similarity_score FROM competitors WHERE idea_id = 1;
```

### Workflow 3: Modify Scheduler Time
Edit `scheduler/runner.py:88`:
```python
schedule.every().day.at("09:00").do(self.check_all_ideas)
# Change "09:00" to desired time
```

## LLM Integration Details

### Gemini Model Used
- Model: `gemini-2.5-flash-preview-09-2025` (or fallback)
- Temperature: Default (not specified)
- Response Format: JSON (with cleanup for ```json blocks)

### Prompts
1. **Concept Extraction**: Asks for core_function, key_features, search_keywords, category
2. **Similarity**: Compares idea vs product, returns score + reasoning + user_advantage

### JSON Cleanup Logic
Both LLM calls strip markdown code fences:
```python
if clean_response.startswith("```json"):
    clean_response = clean_response[7:]
if clean_response.startswith("```"):
    clean_response = clean_response[3:]
if clean_response.endswith("```"):
    clean_response = clean_response[:-3]
```

## Scraper Implementation Notes

### Base Scraper Interface
```python
class BaseScraper(ABC):
    @abstractmethod
    def search(self, query: str) -> list[dict]:
        """Returns: [{name, url, description?, price?}, ...]"""
        pass
```

### AliExpress Scraper
- Uses Selenium for dynamic content
- Headless browser
- Extracts: name, price, url

### Kickstarter Scraper
- Web scraping with requests + BeautifulSoup
- Searches active projects only
- Extracts: name, description, url

### Serper Scraper (Google Search with Product Filtering)
- Google search via Serper.dev API
- Requires SERPER_API_KEY in .env
- **Smart product filtering** - Only returns actual product pages, not blog/news articles
- Returns up to 10 valid product results

#### Product URL Filtering (`scrapers/serper.py`)

**Problem solved**: Google was returning blog articles, news sites, and trend reports (like Trend Hunter) instead of actual buyable products.

**Solution**: Two-stage filtering system that validates URLs before including them:

**Excluded Sites (automatically filtered out):**
```python
exclude_keywords = [
    'blog', 'article', 'news', 'trends',
    'review', 'about', 'contact', 'forum',
    'reddit.com', 'youtube.com', 'pinterest.com',
    'trendhunter.com', 'instructables.com'
]
```

**Product Page Indicators (must match at least one):**
```python
product_keywords = [
    'product', 'buy', 'shop', 'store',
    'item', 'purchase', 'cart', '/p/',
    '/products/', 'amazon.com', 'ebay.com',
    'etsy.com', 'walmart.com', 'target.com',
    'aliexpress.com', 'shopify'
]
```

**How it works:**
1. Fetches 20 Google results (to account for filtering)
2. Each URL is checked: if it contains ANY exclude keyword → rejected
3. Remaining URLs must contain at least ONE product keyword → accepted
4. Stops once 10 valid product pages are found
5. If no valid products found, displays: "No product pages found (all results were articles/blogs)"

**Example**: A result from `trendhunter.com/trends/surf-lamp` would be automatically filtered out, even if it has a high similarity score, because it's an article about a product concept, not an actual buyable product.

### Patent Scraper (Google Patents via SerpAPI)
- Google Patents search via SerpAPI
- **Free tier**: 100 searches/month with free API key
- Searches global patents (US, EP, CN, etc.)
- Returns up to 10 relevant patents

#### How Patent Search Works (`scrapers/patents.py`)

**Why patents matter**: Detects early-stage innovations before they become products. If someone filed a patent for your idea, they may be planning to manufacture it.

**API Details:**
- Endpoint: `https://serpapi.com/search?engine=google_patents`
- Authentication: API key required (SERPAPI_API_KEY in .env)
- Rate limits: 100 searches/month (free tier)
- Coverage: Global patents

**Query structure:**
```python
params = {
    "engine": "google_patents",
    "q": keywords,
    "api_key": settings.SERPAPI_API_KEY,
    "num": 10
}
```

**Data mapping:**
- Patent title → `name` field (prefixed with "Patent:")
- Patent PDF/link → `url` field
- Snippet → `description` field (truncated to 500 chars)
- Price → always `None` (patents don't have prices)

**Example output:**
```python
{
    "name": "Patent: Smart hydration tracking bottle with LED indicators",
    "url": "https://patentimages.storage.googleapis.com/.../patent.pdf",
    "description": "A water bottle with integrated sensors that monitor fluid intake...",
    "price": None
}
```

**Setup:**
1. Sign up for free SerpAPI account at https://serpapi.com
2. Get API key from dashboard (100 free searches/month)
3. Add to `.env`: `SERPAPI_API_KEY=your_key_here`

**Integration:** Patents are treated identically to products - same similarity scoring, same notification system, stored in same `competitors` table with `source="patents"`.

## Troubleshooting

### Common Issues

**1. Selenium ChromeDriver not found**
```bash
# Install chromedriver
sudo apt install chromium-chromedriver  # Linux
# or download from: https://chromedriver.chromium.org/
```

**2. Gemini API key invalid**
```bash
# Check .env file
cat .env | grep GEMINI_API_KEY
# Verify key at: https://makersuite.google.com/app/apikey
```

**3. Email not sending**
- Use Gmail App Password (not regular password)
- Enable 2FA and generate app password
- Check EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO in .env

**4. Scheduler not running**
```bash
# Check if process is running
ps aux | grep "python main.py schedule"

# Run in foreground to see errors
python main.py schedule
```

### Debug Commands
```bash
# Test Gemini connection
python -c "from llm.client import GeminiClient; c = GeminiClient(); print(c.generate('Hello'))"

# Test database
python -c "from database.connection import SessionLocal; db = SessionLocal(); print('OK')"

# Test scraper
python -c "from scrapers.registry import ScraperRegistry; r = ScraperRegistry(); print(r.get_all_scrapers())"
```

## Development Tips

### Adding New Scraper
1. Create `scrapers/new_source.py`
2. Inherit from `BaseScraper`
3. Implement `search(query)` method
4. Add to `scrapers/registry.py`

### Modifying Similarity Threshold
Edit `scheduler/runner.py:63`:
```python
if similarity["score"] >= 60:  # Lower = more matches, Higher = stricter
```

### Changing Email Format
Edit `notifications/email.py` (file not shown, but exists)

## System Status

**Current State**: Fully operational
- Database: SQLite (idea_validator.db)
- LLM: Gemini 2.5 Flash
- Scrapers: 4 active sources (AliExpress, Kickstarter, Google, US Patents)
- Scheduler: Daily at 9 AM
- Notifications: Email alerts

## Next Steps (If Asked)

Potential improvements:
- Add more scrapers (Amazon, Product Hunt, Etsy)
- Web dashboard (Flask/FastAPI)
- Price tracking over time
- Advanced similarity tuning
- Export reports to PDF
- Multi-user support

---

**You're ready to work on the Idea Validator system!** Use this guide for reference.
