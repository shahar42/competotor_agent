# Idea Validator - System Status & Documentation

**Live URL**: https://idea-validator-api.onrender.com
**Repository**: https://github.com/shahar42/competotor_agent
**Status**: ✅ Production (Deployed on Render)

---

## What This System Does

**Idea Validator** helps product inventors validate their ideas before building by automatically finding existing competitors in the market.

### User Flow:
1. User submits product idea description via web form
2. System extracts key concepts using Gemini AI
3. Scrapers search multiple sources (Amazon, Kickstarter, AliExpress, Google, Patents)
4. AI calculates similarity scores (0-100%) for each found product
5. Top competitors (>60% match) are emailed to the user
6. User provides feedback (relevant/not relevant) via email links

### Key Features:
- **AI-Powered Concept Extraction**: Gemini identifies core features, search keywords, and negative keywords
- **Multi-Source Scraping**: 6 scrapers covering marketplaces, crowdfunding, patents
- **Smart Noise Filtering**: Negative keywords filter out false positives before expensive LLM calls
- **Persistent Storage**: PostgreSQL database stores all ideas and competitors
- **Email Notifications**: Automated alerts with top 6 best matches
- **Feedback Loop**: Users can mark results as relevant/irrelevant
- **Weekly Smart Monitoring**: Optional 1-3 month tracking with low-storage "smart diff" (only alerts on new items)

---

## Technical Architecture

### Stack:
- **Backend**: FastAPI (Python 3.13)
- **Database**: PostgreSQL (Render managed)
- **LLM**: Google Gemini 2.5 Flash (API-based)
- **Deployment**: Render (Web Service, Oregon region)
- **Storage**: ~150-200 MB (no browser dependencies)

### Key Components:

#### 1. API Routes (`/api/routers/`)
- `/auth/signup` - User registration
- `/ideas/submit` - Idea submission (triggers background scan)
- `/ideas/results/{email}` - View all user results
- `/webhooks/feedback` - Record user feedback on competitors

#### 2. Scrapers (`/scrapers/`)
All scrapers use **API-based requests** (no Selenium/Chrome needed):
- **AliExpress**: Google site search (`site:aliexpress.com`)
- **Amazon**: Google site search (`site:amazon.com`)
- **Kickstarter**: Google site search (`site:kickstarter.com`)
- **ProductHunt**: Google site search (`site:producthunt.com`)
- **Google Shopping**: Serper API
- **Patents**: SerpAPI

#### 3. LLM Pipeline (`/llm/`)
- **Concept Extraction**: Gemini extracts search keywords + negative keywords
- **Noise Filtering**: Title-based keyword filtering (cheap pre-LLM filter)
- **Similarity Matching**: Gemini compares user idea vs competitor (expensive, limited to top 15)

#### 4. Background Processing
- Scans run via FastAPI `BackgroundTasks`
- Each scan takes ~1-3 minutes (depending on LLM response time)
- Results limited to top 15 products to prevent long processing

#### 5. Weekly Monitoring Service
- **Runner**: `scheduler/runner.py` (runs as separate thread if enabled)
- **Frequency**: Weekly checks (every 7 days per idea)
- **Optimization**: Uses `ScanHistory` table to store MD5 hashes of seen URLs. Prevents duplicate alerts and keeps DB usage minimal (critical for Render free tier).

---

## Deployment Information

### Render Service Configuration:

**Service ID**: `srv-d4otmp6mcj7s73842cfg`
**Type**: Web Service
**Plan**: Starter ($7/mo)
**Region**: Oregon (US West)
**Auto-Deploy**: Enabled (main branch)

### Environment Variables Required:

```bash
# LLM
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL=gemini-2.5-flash-preview-09-2025

# Database (auto-set by Render)
DATABASE_URL=postgresql://...

# Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=shaharisn1@gmail.com
SMTP_PASSWORD=<gmail-app-password>

# Scraper APIs
SERPER_API_KEY=<serper-api-key>
SERPAPI_API_KEY=<serpapi-api-key>

# App Config
API_BASE_URL=https://idea-validator-api.onrender.com
ENABLE_MONITORING=true # Optional: Defaults to false
```

### Database Configuration:

**Service ID**: `dpg-d4ou7t6mcj7s7384clh0-a`
**Type**: PostgreSQL 18
**Plan**: Free (expires Jan 3, 2026)
**Region**: Oregon
**Connection**: Internal URL (Render network only)

**⚠️ Important**: Free database expires in 90 days. Upgrade to paid plan or data will be deleted.

### Build Configuration:

**Dockerfile**: `Dockerfile` (Python 3.11-slim base)
**Build Command**: `pip install --no-cache-dir -r requirements.txt`
**Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port 8000`

**Key Optimization**: Chrome/Selenium removed (saves 200-300 MB) - all scrapers use requests API.

---

## Common Issues & Solutions

### 1. Environment Variable Whitespace
**Problem**: Database/API connection fails with "Illegal metadata" or "does not exist"
**Solution**: Ensure NO trailing spaces/newlines when pasting env vars in Render dashboard

### 2. Background Task Termination
**Problem**: Scan starts but never completes
**Solution**: Service restart kills background tasks. User must resubmit after deployments.

### 3. Slow Scans (>5 minutes)
**Problem**: Gemini API rate limiting or timeout
**Solution**: Normal during high traffic. Consider upgrading to Gemini Pro or adding retry logic.

### 4. Email Delivery
**Problem**: Emails not received
**Solution**:
- Check Gmail app password is correct (not regular password)
- Verify SMTP_PASSWORD has no trailing spaces
- Check spam folder

---

## Performance Metrics

### Typical Scan Breakdown:
- Concept extraction: 3-5 seconds
- Scraping (6 sources): 5-10 seconds
- Similarity matching (15 products): 30-60 seconds
- **Total**: 1-3 minutes

### Resource Usage:
- RAM: ~256 MB (Render free tier sufficient)
- CPU: 0.1 vCPU (minimal)
- Storage: 150-200 MB deployed image

### API Costs (per scan):
- Gemini API calls: ~2-4 calls ($0.0001-$0.0003)
- Serper API calls: 1-2 calls ($0.002-$0.004)
- **Total per scan**: ~$0.005

---

## Recent Deployments

**Latest**: `e952812` - Add API endpoint to view user results
**Previous**: `08a6e80` - Update landing page copy
**Previous**: `41fe5a9` - Add PostgreSQL support

### Git Workflow:
```bash
git add .
git commit -m "Your message"
git push origin main  # Auto-deploys to Render
```

---

## Monitoring & Logs

### View Logs:
```bash
# Via Render Dashboard
https://dashboard.render.com/web/srv-d4otmp6mcj7s73842cfg

# Via API (if monitoring tools added)
# Currently: Manual dashboard checks only
```

### Health Check:
```bash
curl https://idea-validator-api.onrender.com/
# Should return: static/index.html
```

---

## Future Improvements

### Priority:
1. Add uptime monitoring (UptimeRobot, etc.)
2. Implement proper job queue (Celery/Redis) instead of BackgroundTasks
3. Add rate limiting per user
4. Database backup automation before Jan 3, 2026 expiry
5. Error tracking (Sentry)

### Nice-to-Have:
- User dashboard (view past scans)
- Webhook integrations (Slack, Discord)
- Export results to PDF/CSV

---

## Contact & Support

**Owner**: shahar42
**Email**: shaharisn1@gmail.com
**Issues**: https://github.com/shahar42/competotor_agent/issues

---

Last Updated: 2025-12-04
