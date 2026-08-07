from crawler.crawler import Crawler
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
