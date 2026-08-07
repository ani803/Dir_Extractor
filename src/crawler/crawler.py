from .page_fetcher import PageFetcher
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

    def __init__(self, fetcher_factory=PageFetcher, max_workers=None):

        self.link_extractor = LinkExtractor()
        self.link_filter = LinkFilter()
        self.link_scorer = LinkScorer()
        self.fetcher_factory = fetcher_factory
        self.max_workers = max_workers or self.MAX_WORKERS
        self._homepage_fetcher = None

    def __enter__(self):

        self._homepage_fetcher = self.fetcher_factory()
        self._homepage_fetcher.__enter__()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        if self._homepage_fetcher is not None:
            self._homepage_fetcher.__exit__(exc_type, exc_val, exc_tb)
            self._homepage_fetcher = None

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

        return self.fetcher_factory()

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
