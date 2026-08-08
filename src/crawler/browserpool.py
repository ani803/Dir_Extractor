import threading
from threading import BoundedSemaphore
from threading import Lock

from playwright.sync_api import sync_playwright


class BrowserPool:
    """
    Bounds concurrency across worker threads AND reuses one Chromium process
    per thread for the pool's lifetime, instead of launching (and killing) a
    fresh browser on every acquire()/release() cycle.

    Why per-thread: Playwright's sync API ties a browser to the OS thread
    that launched it -- using it from another thread raises errors. Crawler
    submits work to a persistent ThreadPoolExecutor, so each worker thread
    is stable across companies, which makes "one browser per thread, reused
    for the life of the thread" both safe and effective: a company-heavy run
    that used to launch a new Chromium process on every acquire (hundreds to
    thousands of times) now launches at most `size` of them, total.

    acquire() only ever creates a new, lightweight BrowserContext (cheap --
    tens of milliseconds) against the thread's already-running browser.
    release() closes that context, not the browser.
    """

    def __init__(self, size=5, headless=True):

        self.size = size
        self.headless = headless

        self.lock = Lock()
        self.slots = BoundedSemaphore(size)

        self._local = threading.local()
        self._thread_resources = []  # [(playwright, browser), ...] for cleanup

    def __enter__(self):

        return self

    def _get_thread_browser(self):

        browser = getattr(self._local, "browser", None)

        if browser is not None:
            return browser

        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=self.headless)

        self._local.playwright = playwright
        self._local.browser = browser

        with self.lock:
            self._thread_resources.append((playwright, browser))

        return browser

    def acquire(self):

        self.slots.acquire()

        try:
            browser = self._get_thread_browser()

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

            return context

        except Exception:
            self.slots.release()
            raise

    def release(self, context):

        if context is None:
            return

        try:
            context.close()
        except Exception:
            pass
        finally:
            self.slots.release()

    def __exit__(self, exc_type, exc_val, exc_tb):

        with self.lock:
            resources = list(self._thread_resources)
            self._thread_resources.clear()

        for playwright, browser in resources:

            try:
                browser.close()
            finally:
                playwright.stop()
