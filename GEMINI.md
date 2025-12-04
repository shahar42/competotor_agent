# Project Context: Idea Validator Agent

**Last Updated:** December 3, 2025
**Repository:** https://github.com/shahar42/competotor_agent
**Current Phase:** Phase 1 MVP (Email-First Architecture)

## 1. Project Overview
An AI-powered system that validates user invention ideas by scanning the web (AliExpress, Google, Patents) for competitors.
*   **Core Value:** "Know if your idea exists before you build it."
*   **MVP Strategy:** No dashboard, email-only interaction, immediate background scans.
*   **Monetization:** Free tier (1 idea) -> Paid tiers (monitoring + reports).

## 2. Architecture & Stack

### Backend
*   **Framework:** FastAPI (`api/main.py`)
*   **Database:** SQLite (Local) / PostgreSQL (Production). SQLAlchemy ORM.
*   **Async:** Background tasks used for scanning to prevent request blocking.

### Core Components
*   **LLM:** Gemini 2.5 Flash (`llm/client.py`).
*   **Scrapers:** Hybrid approach (`scrapers/`).
    *   *AliExpress:* Selenium (Headless Chrome).
    *   *Google/Patents:* Serper/SerpAPI (HTTP).
*   **Matcher:** `llm/matcher.py` - Custom logic for concept extraction and similarity scoring.

### Infrastructure
*   **Docker:** Custom `Dockerfile` based on `python:3.11-slim`.
    *   *Crucial:* Includes `google-chrome-stable` to allow Selenium to run on Render/Serverless.
*   **Deployment:** Ready for Render (Web Service via Docker).

## 3. Key Features Implemented

### A. The "Negative Keyword" Strategy (False Positive Reduction)
To prevent the LLM from finding irrelevant "sort-of-similar" products:
1.  **Extraction:** We ask Gemini for `negative_keywords` (e.g., Idea: "Cat Sleep Collar" -> Negative: "Dog", "Shock").
2.  **Filtering:** `matcher.filter_noise()` strictly removes scraped results containing these words *before* the expensive LLM comparison.

### B. The Feedback Loop ("Shadow Logger")
*   **Mechanism:** Emails contain "Is this relevant? [Yes] [No]" links.
*   **Endpoint:** `GET /webhooks/feedback` updates `Competitor.is_relevant` and `feedback_at`.
*   **Goal:** Collect a dataset of (Idea, Product, Label) to fine-tune a Llama model in Phase 2.

### C. Database Schema (`database/models.py`)
*   **User:** `email`, `is_premium`.
*   **Idea:** `user_id`, `negative_keywords` (stored JSON), `extracted_concepts`.
*   **Competitor:** `is_relevant` (User feedback flag).

## 4. Current Workflows

### 1. Signup & Submit
*   `POST /auth/signup` -> Creates User.
*   `POST /ideas/submit` -> Creates Idea -> Triggers `background_scan_wrapper`.

### 2. The Scan Pipeline (`api/services/scanner.py`)
1.  Fetch Idea.
2.  **Extract:** Get search terms + negative keywords.
3.  **Search:** Run all scrapers.
4.  **Filter:** Apply Negative Keywords (Quick Kill).
5.  **Match:** Gemini calculates similarity score (0-100).
6.  **Notify:** Send email via `EmailService` if > threshold.

## 5. Environment Variables Required
```bash
GEMINI_API_KEY=...
SERPER_API_KEY=...
SMTP_USER=...
SMTP_PASSWORD=...
API_BASE_URL=... (e.g., https://idea-validator.onrender.com)
```

## 6. Next Steps / Todo
1.  **Deployment:** Push to Render and verify Docker build works.
2.  **Feedback UI:** Create a simple HTML "Thank You" page for the feedback endpoint (currently returns raw JSON).
3.  **Recurring Scans:** The `scheduler/runner.py` exists but isn't connected to the API yet. Needs to be run as a separate worker or integrated into FastAPI lifespan.
4.  **Auth:** Implement magic links or simple token auth (currently just email).
