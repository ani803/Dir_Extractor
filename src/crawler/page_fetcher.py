from pathlib import Path
from threading import get_ident
import time
from uuid import uuid4

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from models import Page
from config.config import Config
from logger.logger import get_logger


logger = get_logger(__name__)


class PageFetcher:
    """
    Extractor v2.0

    Handles browser automation.

    Features
    --------
    ✓ Retry on failures
    ✓ Resource blocking
    ✓ Faster crawling
    ✓ Better logging
    """

    MAX_RETRIES = 3

    TIMEOUT = Config.PAGE_TIMEOUT_MS

    def __init__(
        self,
        headless=True,
        debug_file=None,
        debug_enabled=None,
        debug_dir=None,
        browser_pool=None,
        context=None,
    ):

        project_root = Path(__file__).resolve().parents[2]

        self.headless = headless

        self.debug_enabled = (
            Config.DEBUG_HTML_ENABLED
            if debug_enabled is None
            else debug_enabled
        )
        self.debug_dir = debug_dir or project_root / "debug"
        self.debug_file = debug_file
        if debug_file is not None:
            self.debug_enabled = True

        self.browser_pool = browser_pool
        self.context = context
        self.playwright = None
        self.browser = None
        self._owns_browser = False
        self._borrowed_context = False

    def _timeout_for_attempt(self, attempt: int) -> int:

        return min(
            self.TIMEOUT,
            Config.PAGE_INITIAL_TIMEOUT_MS * attempt,
        )

    def __enter__(self):

        if self.context is not None:
            return self

        if self.browser_pool is not None:
            self.context = self.browser_pool.acquire()
            self._borrowed_context = True
            return self

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
        )
        self._owns_browser = True

        self.context = self.browser.new_context(

            viewport={
                "width": 1920,
                "height": 1080,
            },

            locale="en-US",

            timezone_id="Asia/Kolkata",

            ignore_https_errors=True,

            java_script_enabled=True,

            user_agent=(
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/138.0 Safari/537.36"
            ),
        )

        return self

    def _configure_page(self, page):

        page.set_extra_http_headers({

            "Accept-Language": "en-US,en;q=0.9",

            "DNT": "1",

            "Upgrade-Insecure-Requests": "1",
        })

        # Block resources that are useless
        page.route(
            "**/*",
            lambda route:

            route.abort()

            if route.request.resource_type
            in (
                "image",
                "media",
                "font",
            )

            else route.continue_()
        )

    def fetch(self, url: str) -> Page:

        for attempt in range(1, self.MAX_RETRIES + 1):

            page = self.context.new_page()
            
            try:

                self._configure_page(page)

                timeout = self._timeout_for_attempt(attempt)

                logger.info(
                    "Fetching [%s/%s] %s timeout=%sms",
                    attempt,
                    self.MAX_RETRIES,
                    url,
                    timeout,
                )

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=timeout,
                )

                page.wait_for_load_state(
                    "networkidle",
                    timeout=timeout,
                )

                html = page.content()

                title = page.title()

                final_url = page.url

                self._write_debug_file(html)

                return Page(
                    url=final_url,
                    html=html,
                    title=title,
                )

            except PlaywrightTimeoutError:

                logger.warning("Timeout fetching %s on attempt %s", url, attempt)

                if attempt == self.MAX_RETRIES:
                    raise

                time.sleep(2 ** attempt)

            except Exception as e:

                logger.warning("Fetch error for %s on attempt %s: %s", url, attempt, e)

                if attempt == self.MAX_RETRIES:
                    raise

                time.sleep(2 ** attempt)

            finally:

                page.close()

    def _write_debug_file(self, html: str):

        if not self.debug_enabled:
            return

        if self.debug_file is not None:
            debug_file = Path(self.debug_file)
        else:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = self.debug_dir / (
                f"page-{get_ident()}-{int(time.time() * 1000)}-{uuid4().hex}.html"
            )

        debug_file.write_text(
            html,
            encoding="utf-8",
        )

    def __exit__(self, exc_type, exc_val, exc_tb):

        if self._borrowed_context:
            self.browser_pool.release(self.context)
            self.context = None
            self._borrowed_context = False
            return

        if self.context is not None and self._owns_browser:
            self.context.close()
            self.context = None

        if self.browser is not None:
            self.browser.close()
            self.browser = None

        if self.playwright is not None:
            self.playwright.stop()
            self.playwright = None
