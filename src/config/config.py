import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

class Config:

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

    BING_API_KEY = os.getenv("BING_API_KEY")

    SERPAPI_KEY = os.getenv("SERPAPI_KEY")

    BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

    CRAWLER_MAX_PAGES = int(os.getenv("CRAWLER_MAX_PAGES", "10"))
    CRAWLER_WORKERS = int(os.getenv("CRAWLER_WORKERS", "0"))
    CRAWLER_MIN_LINK_SCORE = int(os.getenv("CRAWLER_MIN_LINK_SCORE", "1"))
    CRAWLER_TARGET_SCORE = int(os.getenv("CRAWLER_TARGET_SCORE", "500"))

    SEARCH_WORKERS = int(os.getenv("SEARCH_WORKERS", "0"))
    SEARCH_HIGH_CONFIDENCE = float(os.getenv("SEARCH_HIGH_CONFIDENCE", "0.90"))

    PAGE_TIMEOUT_MS = int(os.getenv("PAGE_TIMEOUT_MS", "30000"))
    PAGE_INITIAL_TIMEOUT_MS = int(os.getenv("PAGE_INITIAL_TIMEOUT_MS", "8000"))
    DEBUG_HTML_ENABLED = (
        os.getenv("DEBUG_HTML_ENABLED", "false").lower()
        in {"1", "true", "yes", "on"}
    )

    DIRECTOR_REJECT_THRESHOLD = float(os.getenv("DIRECTOR_REJECT_THRESHOLD", "50"))
    DIRECTOR_REVIEW_THRESHOLD = float(os.getenv("DIRECTOR_REVIEW_THRESHOLD", "70"))
    DIRECTOR_ACCEPT_THRESHOLD = float(os.getenv("DIRECTOR_ACCEPT_THRESHOLD", "85"))
    DIRECTOR_HIGH_CONFIDENCE_THRESHOLD = float(
        os.getenv("DIRECTOR_HIGH_CONFIDENCE_THRESHOLD", "95")
    )

    AI_VERIFICATION_ENABLED = (
        os.getenv("AI_VERIFICATION_ENABLED", "false").lower()
        in {"1", "true", "yes", "on"}
    )
    # ANTHROPIC_API_KEY is the primary name; AI_VERIFICATION_API_KEY is kept
    # as a fallback for anyone who set that name under the old webhook setup.
    AI_VERIFICATION_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv(
        "AI_VERIFICATION_API_KEY"
    )
    AI_VERIFICATION_MODEL = os.getenv("AI_VERIFICATION_MODEL", "claude-sonnet-5")
    AI_VERIFICATION_THRESHOLD = float(
        os.getenv("AI_VERIFICATION_THRESHOLD", "75")
    )
    AI_VERIFICATION_TIMEOUT = int(os.getenv("AI_VERIFICATION_TIMEOUT", "30"))
    # Candidates below the threshold are grouped into batches of this size and
    # sent to the model in a single request, instead of one request each.
    AI_VERIFICATION_BATCH_SIZE = int(os.getenv("AI_VERIFICATION_BATCH_SIZE", "20"))
    AI_VERIFICATION_MAX_RETRIES = int(os.getenv("AI_VERIFICATION_MAX_RETRIES", "3"))
