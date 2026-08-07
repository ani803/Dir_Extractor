from pathlib import Path
import time

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from models import Page


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

    TIMEOUT = 30000

    def __init__(
        self,
        headless=True,
        debug_file=None,
    ):

        project_root = Path(__file__).resolve().parents[2]

        self.headless = headless

        self.debug_file = (
            debug_file
            or project_root / "src" / "debug.html"
        )

    def __enter__(self):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
        )

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

                print(f"[{attempt}/{self.MAX_RETRIES}] {url}")

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.TIMEOUT,
                )

                page.wait_for_load_state(
                    "networkidle",
                    timeout=self.TIMEOUT,
                )

                html = page.content()

                title = page.title()

                final_url = page.url

                self.debug_file.write_text(
                    html,
                    encoding="utf-8",
                )

                return Page(
                    url=final_url,
                    html=html,
                    title=title,
                )

            except PlaywrightTimeoutError:

                print(f"Timeout ({attempt})")

                if attempt == self.MAX_RETRIES:
                    raise

                time.sleep(2 ** attempt)

            except Exception as e:

                print(f"Fetch Error ({attempt})")

                print(e)

                if attempt == self.MAX_RETRIES:
                    raise

                time.sleep(2 ** attempt)

            finally:

                page.close()

    def __exit__(self, exc_type, exc_val, exc_tb):

        self.context.close()

        self.browser.close()

        self.playwright.stop()
