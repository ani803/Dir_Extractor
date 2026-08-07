from .page_fetcher import PageFetcher
from .link_extractor import LinkExtractor
from .link_filter import LinkFilter
from .link_scorer import LinkScorer
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed


class Crawler:

    MAX_PAGES = 10
    MAX_WORKERS = 4

    PRIORITY_KEYWORDS = {
        "board",
        "board-of-directors",
        "leadership",
        "management",
        "our-team",
        "team",
        "governance",
        "about",
        "people",
        "executive",
        "officers",
    }

    SKIP_KEYWORDS = {
        ".pdf",
        "pdf",
        "investor_updates",
        "annual-report",
        "annual_report",
        "financial-results",
        "results",
        "press-release",
        "press_release",
        "downloads",
        "download",
        "notice",
        "notices",
        "shareholder",
        "stock-exchange",
        "privacy",
        "cookie",
        "terms",
        "policy",
        "careers",
        "jobs",
        "login",
        "signup",
    }

    def __init__(self, fetcher_factory=PageFetcher, max_workers=None):

        self.link_extractor = LinkExtractor()
        self.link_filter = LinkFilter()
        self.link_scorer = LinkScorer()
        self.fetcher_factory = fetcher_factory
        self.max_workers = max_workers or self.MAX_WORKERS

    def _select_links_to_fetch(self, links):

        return [
            link
            for link in links[: self.MAX_PAGES]
            if link.score > 0
        ]

    def _chunk_links(self, links, chunk_count):

        chunks = [[] for _ in range(chunk_count)]

        for index, link in enumerate(links):
            chunks[index % chunk_count].append(link)

        return [chunk for chunk in chunks if chunk]

    def _fetch_link_batch(self, links):

        pages = []

        with self.fetcher_factory() as fetcher:

            for link in links:

                try:

                    page = fetcher.fetch(link.url)

                    pages.append(page)

                    print(f"Downloaded : {page.title}")

                except Exception as e:

                    print(f"Failed : {link.url}")
                    print(e)

        return pages

    def _fetch_links_parallel(self, links):

        if not links:
            return []

        worker_count = min(
            self.max_workers,
            len(links),
        )

        batches = self._chunk_links(
            links,
            worker_count,
        )

        pages = []

        print(f"Parallel fetch workers : {worker_count}")

        with ThreadPoolExecutor(max_workers=worker_count) as executor:

            futures = [
                executor.submit(
                    self._fetch_link_batch,
                    batch,
                )
                for batch in batches
            ]

            for future in as_completed(futures):

                pages.extend(future.result())

        return pages

    def crawl(self, website: str):

        pages = []

        with PageFetcher() as fetcher:

            print("=" * 80)
            print("CRAWLER")
            print("=" * 80)

            try:

                homepage = fetcher.fetch(website)

                pages.append(homepage)

                print(f"Homepage : {homepage.title}")

                links = self.link_extractor.extract(homepage)

                print(f"Raw Links : {len(links)}")

                links = self.link_filter.filter(
                homepage.url,
                links,
                )

                links = self.link_scorer.score(links)

                filtered = []
                visited = set()

                for link in links:

                    url = link.url.lower()

                    if url in visited:
                        continue

                    visited.add(url)

                    if any(word in url for word in self.SKIP_KEYWORDS):
                        continue

                    if any(word in url for word in self.PRIORITY_KEYWORDS):
                        link.score += 100

                    filtered.append(link)

                filtered.sort(
                    key=lambda x: x.score,
                    reverse=True,
                )

                print(f"Useful Links : {len(filtered)}")

                selected_links = self._select_links_to_fetch(filtered)

                for link in selected_links:

                    print(f"[{link.score:3}] {link.url}")

                pages.extend(
                    self._fetch_links_parallel(selected_links)
                )

            except Exception as e:

                print("\nCrawler Failed")
                print(e)

        print(f"\nPages downloaded : {len(pages)}")

        return pages
