import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///idea_validator.db")

    # LLM
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-09-2025")

    # Email
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "shaharisn1@gmail.com"
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
        
    RECIPIENT_EMAIL = "shaharisn1@gmail.com"

    # Scraping
    USER_AGENT = "IdeaValidator/1.0"
    REQUEST_TIMEOUT = 30

    # Serper API (add to .env: SERPER_API_KEY)
    SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

    # SerpAPI (for Google Patents - add to .env: SERPAPI_API_KEY)
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

    # Similarity matching
    SIMILARITY_THRESHOLD = 60  # 0-100, products above this are considered competitors

    # App
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    ENABLE_MONITORING = os.getenv("ENABLE_MONITORING", "false").lower() == "true"

settings = Settings()
