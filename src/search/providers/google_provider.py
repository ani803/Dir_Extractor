import requests

from config.config import Config
from models import Company
from search.search_result import SearchResult
from .base_provider import BaseProvider


class GoogleProvider(BaseProvider):

    SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

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

        print("\n" + "=" * 80)
        print("Google Search")
        print("=" * 80)
        print("Query :", params["q"])
        print("Key   :", Config.GOOGLE_API_KEY[:8] + "...")
        print("CX    :", Config.GOOGLE_CSE_ID)

        try:
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                timeout=20,
            )

            print("\nHTTP Status:", response.status_code)

            data = response.json()

            print("\nGoogle Response:")
            print(data)

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

            for item in items:

                url = item.get("link")

                if url:
                    print("\nSelected URL:", url)

                    return SearchResult(
                        company_name=company.company_name,
                        official_website=url,
                        source="Google",
                        confidence=0.95,
                        success=True,
                    )

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error="No valid URLs found in Google results.",
            )

        except requests.exceptions.RequestException as e:

            print("\nRequest Exception:", e)

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error=str(e),
            )

        except Exception as e:

            print("\nUnexpected Exception:", e)

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error=str(e),
            )