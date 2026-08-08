from pathlib import Path
import shutil

from crawler.page_fetcher import PageFetcher


class PageStub:
    url = "https://example.com/final"

    def __init__(self):
        self.closed = False

    def goto(self, *args, **kwargs):
        return None

    def set_extra_http_headers(self, *args, **kwargs):
        return None

    def route(self, *args, **kwargs):
        return None

    def wait_for_load_state(self, *args, **kwargs):
        return None

    def content(self):
        return "<html><title>Example</title></html>"

    def title(self):
        return "Example"

    def close(self):
        self.closed = True


class ContextStub:
    def __init__(self):
        self.page = PageStub()
        self.closed = False

    def new_page(self):
        return self.page

    def close(self):
        self.closed = True


class BrowserPoolStub:
    def __init__(self):
        self.context = ContextStub()
        self.released = []

    def acquire(self):
        return self.context

    def release(self, context):
        self.released.append(context)


def test_page_fetcher_uses_active_context():

    debug_file = Path("page_fetcher_test_debug.html")

    fetcher = PageFetcher(debug_file=debug_file)
    fetcher.context = ContextStub()

    try:
        page = fetcher.fetch("https://example.com")

        assert page.url == "https://example.com/final"
        assert page.title == "Example"
        assert fetcher.context.page.closed is True
    finally:
        if debug_file.exists():
            debug_file.unlink()


def test_page_fetcher_disables_debug_html_by_default():

    debug_dir = Path("page_fetcher_debug_dir_test")

    try:
        if debug_dir.exists():
            shutil.rmtree(debug_dir)

        fetcher = PageFetcher(debug_dir=debug_dir)
        fetcher.context = ContextStub()

        page = fetcher.fetch("https://example.com")

        assert page.title == "Example"
        assert not debug_dir.exists()
    finally:
        if debug_dir.exists():
            shutil.rmtree(debug_dir)


def test_page_fetcher_releases_borrowed_context_to_pool():

    pool = BrowserPoolStub()

    with PageFetcher(browser_pool=pool) as fetcher:
        page = fetcher.fetch("https://example.com")

    assert page.url == "https://example.com/final"
    assert pool.released == [pool.context]
    assert pool.context.closed is False
