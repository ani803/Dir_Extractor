import requests

from config.config import Config
from models import Company
from search.search_result import SearchResult
from .base_provider import BaseProvider


class BraveProvider(BaseProvider):

    SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

    BASE_TRUST = 0.90

    def search(self, company: Company) -> SearchResult:

        if not Config.BRAVE_API_KEY:

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error="Brave API key not configured.",
            )

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": Config.BRAVE_API_KEY,
        }

        params = {
            "q": f"{company.search_name} official website",
            "count": 5,
        }

        try:

            response = requests.get(
                self.SEARCH_URL,
                headers=headers,
                params=params,
                timeout=20,
            )

            response.raise_for_status()

            data = response.json()

            results = (
                data.get("web", {})
                .get("results", [])
            )

            if not results:

                return SearchResult(
                    company_name=company.company_name,
                    success=False,
                    error="No Brave results.",
                )

            urls = [result.get("url") for result in results]

            return self._best_match(company, urls, source="Brave")

        except Exception as e:

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error=str(e),
            )
