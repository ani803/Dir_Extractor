from crawler.crawler import Crawler
from crawler.page_fetcher import PageFetcher
from models import Link
from models import Page


class FetcherStub:
    seen_batches = []
    active_urls = []

    def __enter__(self):
        self.urls = []
        FetcherStub.seen_batches.append(self.urls)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def fetch(self, url):
        self.urls.append(url)
        FetcherStub.active_urls.append(url)
        return Page(
            url=url,
            html="<html></html>",
            title=url.rsplit("/", 1)[-1],
        )


class BrowserPoolStub:
    def __init__(self, size=1):
        self.size = size
        self.acquired = 0
        self.released = 0
        self.contexts = [ContextStub(index) for index in range(size)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def acquire(self):
        context = self.contexts[self.acquired % len(self.contexts)]
        self.acquired += 1
        return context

    def release(self, context):
        self.released += 1


class ContextStub:
    def __init__(self, index):
        self.index = index

    def new_page(self):
        return PageStub(self.index)


class PageStub:
    url = "https://example.com/final"

    def __init__(self, index):
        self.index = index

    def goto(self, *args, **kwargs):
        return None

    def wait_for_load_state(self, *args, **kwargs):
        return None

    def set_extra_http_headers(self, *args, **kwargs):
        return None

    def route(self, *args, **kwargs):
        return None

    def content(self):
        return f"<html>context {self.index}</html>"

    def title(self):
        return f"context-{self.index}"

    def close(self):
        return None


def test_crawler_fetches_selected_links_in_parallel_batches():

    FetcherStub.seen_batches = []
    FetcherStub.active_urls = []

    crawler = Crawler(
        fetcher_factory=FetcherStub,
        max_workers=2,
    )

    links = [
        Link(url=f"https://example.com/page-{index}", text="", score=100)
        for index in range(5)
    ]

    pages = crawler._fetch_links_parallel(links)

    assert len(pages) == 5
    assert len(FetcherStub.seen_batches) == 2
    assert sorted(FetcherStub.active_urls) == [
        "https://example.com/page-0",
        "https://example.com/page-1",
        "https://example.com/page-2",
        "https://example.com/page-3",
        "https://example.com/page-4",
    ]


def test_crawler_skips_non_positive_links_before_fetching():

    crawler = Crawler(max_workers=2)

    selected = crawler._select_links_to_fetch(
        [
            Link(url="https://example.com/useful", text="", score=10),
            Link(url="https://example.com/ignored", text="", score=0),
        ]
    )

    assert [link.url for link in selected] == ["https://example.com/useful"]


def test_crawler_workers_borrow_contexts_from_browser_pool():

    pool = BrowserPoolStub(size=3)
    crawler = Crawler(
        fetcher_factory=PageFetcher,
        browser_pool=pool,
        max_workers=2,
    )

    links = [
        Link(url=f"https://example.com/page-{index}", text="", score=100)
        for index in range(4)
    ]

    pages = crawler._fetch_links_parallel(links)

    assert len(pages) == 4
    assert pool.acquired == 2
    assert pool.released == 2
