from models import Company
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import os

from search.cache_manager import CacheManager
from search.validators import WebsiteValidator
from search.search_result import SearchResult
from config.config import Config
from logger.logger import get_logger


logger = get_logger(__name__)


class WebsiteFinder:

    def __init__(self, providers, max_workers=None):

        self.providers = providers
        self.max_workers = max_workers or Config.SEARCH_WORKERS or min(
            len(providers) or 1,
            max(2, (os.cpu_count() or 2)),
        )

        self.cache = CacheManager()

        self.validator = WebsiteValidator()

    def _search_provider(self, provider, company: Company):

        try:
            result = provider.search(company)
            return provider, result

        except Exception as exc:
            logger.exception(
                "Search provider failed: %s",
                provider.__class__.__name__,
            )

            return provider, SearchResult(
                company_name=company.company_name,
                success=False,
                error=str(exc),
            )

    def find(self, company: Company):

        cached = self.cache.get(company.search_name)

        if cached:

            return SearchResult(
                company_name=company.company_name,
                official_website=cached,
                source="Cache",
                confidence=1.0,
                success=True,
            )

        best_result = None

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:

            futures = [
                executor.submit(
                    self._search_provider,
                    provider,
                    company,
                )
                for provider in self.providers
            ]

            for future in as_completed(futures):

                provider, result = future.result()

                if not result.success:
                    logger.debug(
                        "%s did not return a website: %s",
                        provider.__class__.__name__,
                        result.error,
                    )
                    continue

                if not self.validator.validate(result.official_website):
                    logger.debug(
                        "%s returned invalid website: %s",
                        provider.__class__.__name__,
                        result.official_website,
                    )
                    continue

                if (
                    best_result is None
                    or result.confidence > best_result.confidence
                ):
                    best_result = result

                if result.confidence >= Config.SEARCH_HIGH_CONFIDENCE:
                    logger.info(
                        "Selected %s from %s with confidence %.2f",
                        result.official_website,
                        result.source,
                        result.confidence,
                    )
                    break

        if best_result is not None:

            self.cache.put(
                company.search_name,
                best_result.official_website,
            )

            return best_result

        return SearchResult(
            company_name=company.company_name,
            success=False,
            error="No provider returned a valid website.",
        )
