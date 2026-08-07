from pathlib import Path

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

    def new_page(self):
        return self.page


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
