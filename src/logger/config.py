from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Log directory
LOG_DIR = PROJECT_ROOT / "logs"

LOG_DIR.mkdir(exist_ok=True)

# Log files
APP_LOG = LOG_DIR / "app.log"

ERROR_LOG = LOG_DIR / "error.log"

CRAWLER_LOG = LOG_DIR / "crawler.log"