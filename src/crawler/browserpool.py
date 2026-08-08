from threading import BoundedSemaphore
from threading import Lock

from playwright.sync_api import sync_playwright


class BrowserPool:

    def __init__(self, size=5, headless=True):

        self.size = size
        self.headless = headless

        self.lock = Lock()
        self.slots = BoundedSemaphore(size)

        self._resources = {}

    def __enter__(self):

        return self

    def acquire(self):

        self.slots.acquire()

        try:
            playwright = sync_playwright().start()

            browser = playwright.chromium.launch(
                headless=self.headless
            )

            context = browser.new_context(

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

            with self.lock:
                self._resources[id(context)] = (
                    playwright,
                    browser,
                    context,
                )

            return context

        except Exception:
            self.slots.release()
            raise

    def release(self, context):

        if context is None:
            return

        with self.lock:
            resources = self._resources.pop(id(context), None)

        if resources is None:
            self.slots.release()
            return

        playwright, browser, context = resources

        try:
            context.close()
        finally:
            try:
                browser.close()
            finally:
                playwright.stop()
                self.slots.release()

    def __exit__(self, exc_type, exc_val, exc_tb):

        with self.lock:
            resources = list(self._resources.values())
            self._resources.clear()

        for playwright, browser, context in resources:
            try:
                context.close()
            finally:
                try:
                    browser.close()
                finally:
                    playwright.stop()
                    self.slots.release()
