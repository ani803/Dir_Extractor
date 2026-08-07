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