import requests

from config.config import Config
from models import Company
from search.search_result import SearchResult
from .base_provider import BaseProvider


class BingProvider(BaseProvider):

    SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search"

    def search(self, company: Company) -> SearchResult:

        if not Config.BING_API_KEY:
            return SearchResult(
                company_name=company.company_name,
                success=False,
                error="Bing API key is not configured.",
            )

        headers = {
            "Ocp-Apim-Subscription-Key": Config.BING_API_KEY
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

            pages = data.get("webPages", {}).get("value", [])

            for page in pages:

                url = page.get("url")

                if url:

                    return SearchResult(
                        company_name=company.company_name,
                        official_website=url,
                        source="Bing",
                        confidence=0.90,
                        success=True,
                    )

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error="No Bing results",
            )

        except Exception as e:

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error=str(e),
            )
