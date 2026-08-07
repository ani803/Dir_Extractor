from queue import Queue
from threading import Lock

from playwright.sync_api import sync_playwright


class BrowserPool:

    def __init__(self, size=5, headless=True):

        self.size = size
        self.headless = headless

        self.lock = Lock()

        self.playwright = None
        self.browser = None

        self.pool = Queue()

    def __enter__(self):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=self.headless
        )

        for _ in range(self.size):

            context = self.browser.new_context(

                viewport={
                    "width": 1920,
                    "height": 1080,
                },

                ignore_https_errors=True,

                java_script_enabled=True,
            )

            self.pool.put(context)

        return self

    def acquire(self):

        return self.pool.get()

    def release(self, context):

        self.pool.put(context)

    def __exit__(self, exc_type, exc_val, exc_tb):

        while not self.pool.empty():

            context = self.pool.get()

            context.close()

        self.browser.close()

        self.playwright.stop()