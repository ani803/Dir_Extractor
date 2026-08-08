from ddgs import DDGS

from models import Company
from search.search_result import SearchResult
from .base_provider import BaseProvider
from logger.logger import get_logger


logger = get_logger(__name__)


class DuckDuckGoProvider(BaseProvider):

    # No API key required, so results are noisier than the paid providers --
    # trusted less by default, with the domain-match score doing most of the
    # work to pick the right result out of the top 5.
    BASE_TRUST = 0.85

    def search(self, company: Company) -> SearchResult:

        query = f"{company.search_name} official website"

        logger.info("DuckDuckGo query: %s", query)

        try:
            results = list(DDGS().text(query, max_results=5))

            if not results:
                return SearchResult(
                    company_name=company.company_name,
                    success=False,
                    error="No DuckDuckGo results.",
                )

            logger.info("DuckDuckGo results found: %s", len(results))

            urls = [result.get("href") for result in results]

            return self._best_match(company, urls, source="DuckDuckGo")

        except Exception as e:

            logger.warning("DuckDuckGo error: %s", e)

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error=str(e),
            )
