import requests

from config.config import Config
from models import Company
from search.search_result import SearchResult
from .base_provider import BaseProvider


class SerpApiProvider(BaseProvider):

    SEARCH_URL = "https://serpapi.com/search.json"

    def search(self, company: Company) -> SearchResult:

        if not Config.SERPAPI_KEY:
            return SearchResult(
                company_name=company.company_name,
                success=False,
                error="SerpAPI key is not configured.",
            )

        params = {
            "api_key": Config.SERPAPI_KEY,
            "engine": "google",
            "q": f"{company.search_name} official website",
        }

        try:

            response = requests.get(
                self.SEARCH_URL,
                params=params,
                timeout=20,
            )

            response.raise_for_status()

            data = response.json()

            for result in data.get("organic_results", []):

                url = result.get("link")

                if url:

                    return SearchResult(
                        company_name=company.company_name,
                        official_website=url,
                        source="SerpAPI",
                        confidence=0.88,
                        success=True,
                    )

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error="No SerpAPI results",
            )

        except Exception as e:

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error=str(e),
            )
