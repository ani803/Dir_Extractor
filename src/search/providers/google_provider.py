import requests

from config.config import Config
from models import Company
from search.search_result import SearchResult
from .base_provider import BaseProvider
from logger.logger import get_logger


logger = get_logger(__name__)


class GoogleProvider(BaseProvider):

    SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

    BASE_TRUST = 0.93

    def search(self, company: Company) -> SearchResult:

        if not Config.GOOGLE_API_KEY:
            return SearchResult(
                company_name=company.company_name,
                success=False,
                error="GOOGLE_API_KEY is missing.",
            )

        if not Config.GOOGLE_CSE_ID:
            return SearchResult(
                company_name=company.company_name,
                success=False,
                error="GOOGLE_CSE_ID is missing.",
            )

        params = {
            "key": Config.GOOGLE_API_KEY,
            "cx": Config.GOOGLE_CSE_ID,
            "q": f"{company.search_name} official website",
            "num": 5,
        }

        logger.info("Google query: %s", params["q"])
        logger.debug("Google CSE ID: %s", Config.GOOGLE_CSE_ID)

        try:
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                timeout=20,
            )

            logger.debug("Google HTTP status: %s", response.status_code)

            data = response.json()

            logger.debug("Google response: %s", data)

            response.raise_for_status()

            if "error" in data:
                return SearchResult(
                    company_name=company.company_name,
                    success=False,
                    error=f"Google API Error: {data['error']}",
                )

            items = data.get("items", [])

            if not items:
                return SearchResult(
                    company_name=company.company_name,
                    success=False,
                    error="Google returned no search results.",
                )

            urls = [item.get("link") for item in items]

            result = self._best_match(company, urls, source="Google")

            if result.success:
                logger.info(
                    "Google selected URL: %s (confidence=%.2f)",
                    result.official_website,
                    result.confidence,
                )

            return result

        except requests.exceptions.RequestException as e:

            logger.warning("Google request exception: %s", e)

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error=str(e),
            )

        except Exception as e:

            logger.warning("Google unexpected exception: %s", e)

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error=str(e),
            )
