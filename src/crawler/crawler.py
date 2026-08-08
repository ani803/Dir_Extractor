from .page_fetcher import PageFetcher
from .browserpool import BrowserPool
from .link_extractor import LinkExtractor
from .link_filter import LinkFilter
from .link_scorer import LinkScorer
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import os

from config.config import Config
from logger.logger import get_logger


logger = get_logger(__name__)


class Crawler:

    MAX_PAGES = Config.CRAWLER_MAX_PAGES
    MAX_WORKERS = Config.CRAWLER_WORKERS or min(4, max(1, os.cpu_count() or 1))

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

    def __init__(
        self,
        fetcher_factory=PageFetcher,
        max_workers=None,
        browser_pool_factory=BrowserPool,
        browser_pool=None,
    ):

        self.link_extractor = LinkExtractor()
        self.link_filter = LinkFilter()
        self.link_scorer = LinkScorer()
        self.fetcher_factory = fetcher_factory
        self.max_workers = max_workers or self.MAX_WORKERS
        self.browser_pool_factory = browser_pool_factory
        self.browser_pool = browser_pool
        self._owns_browser_pool = False
        self._homepage_fetcher = None
        self._executor = None

    def __enter__(self):

        if self.browser_pool is None and self.fetcher_factory is PageFetcher:
            self.browser_pool = self.browser_pool_factory(
                size=max(1, self.max_workers + 1),
            )
            self.browser_pool.__enter__()
            self._owns_browser_pool = True

        # One executor for the whole crawl session (i.e. the whole run, not
        # per company). Worker threads persist across companies, which lets
        # BrowserPool hand each thread back its own already-running browser
        # instead of relaunching Chromium every time a company is crawled.
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

        self._homepage_fetcher = self._make_fetcher()
        self._homepage_fetcher.__enter__()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        if self._homepage_fetcher is not None:
            self._homepage_fetcher.__exit__(exc_type, exc_val, exc_tb)
            self._homepage_fetcher = None

        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None

        if self._owns_browser_pool and self.browser_pool is not None:
            self.browser_pool.__exit__(exc_type, exc_val, exc_tb)
            self.browser_pool = None
            self._owns_browser_pool = False

    def _make_fetcher(self):

        if self.browser_pool is not None and self.fetcher_factory is PageFetcher:
            return self.fetcher_factory(browser_pool=self.browser_pool)

        return self.fetcher_factory()

    def _select_links_to_fetch(self, links):

        selected = []
        cumulative_score = 0

        for link in links:
            if len(selected) >= self.MAX_PAGES:
                break

            if link.score < Config.CRAWLER_MIN_LINK_SCORE:
                continue

            selected.append(link)
            cumulative_score += link.score

            if cumulative_score >= Config.CRAWLER_TARGET_SCORE:
                break

        return selected

    def _get_homepage_fetcher(self):

        if self._homepage_fetcher is not None:
            return self._homepage_fetcher

        return self._make_fetcher()

    def _chunk_links(self, links, chunk_count):

        chunks = [[] for _ in range(chunk_count)]

        for index, link in enumerate(links):
            chunks[index % chunk_count].append(link)

        return [chunk for chunk in chunks if chunk]

    def _fetch_link_batch(self, links):

        pages = []

        with self._make_fetcher() as fetcher:

            for link in links:

                try:

                    page = fetcher.fetch(link.url)

                    pages.append(page)

                    logger.info("Downloaded: %s", page.title)

                except Exception as e:

                    logger.warning("Failed: %s | %s", link.url, e)

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

        logger.info("Parallel fetch workers: %s", worker_count)

        # Reuse the crawl session's persistent executor when available (see
        # __enter__) so worker threads -- and therefore their pooled
        # browsers -- carry over between companies. Falls back to a
        # throwaway executor for direct/unit-test use outside `with
        # Crawler():`.
        executor = self._executor
        owns_executor = executor is None

        if owns_executor:
            executor = ThreadPoolExecutor(max_workers=worker_count)

        try:

            futures = [
                executor.submit(
                    self._fetch_link_batch,
                    batch,
                )
                for batch in batches
            ]

            for future in as_completed(futures):

                pages.extend(future.result())

        finally:

            if owns_executor:
                executor.shutdown(wait=True)

        return pages

    def crawl(self, website: str):

        pages = []

        fetcher = self._get_homepage_fetcher()
        owns_fetcher = self._homepage_fetcher is None

        if owns_fetcher:
            fetcher.__enter__()

        try:

            logger.info("Crawler started: %s", website)

            try:

                homepage = fetcher.fetch(website)

                pages.append(homepage)

                logger.info("Homepage: %s", homepage.title)

                links = self.link_extractor.extract(homepage)

                logger.info("Raw links: %s", len(links))

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

                logger.info("Useful links: %s", len(filtered))

                selected_links = self._select_links_to_fetch(filtered)

                for link in selected_links:

                    logger.info("Selected link [%s]: %s", link.score, link.url)

                pages.extend(
                    self._fetch_links_parallel(selected_links)
                )

            except Exception as e:

                logger.exception("Crawler failed: %s", website)

        finally:

            if owns_fetcher:
                fetcher.__exit__(None, None, None)

        logger.info("Pages downloaded: %s", len(pages))

        return pages
