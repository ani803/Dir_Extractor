from ddgs import DDGS

from models import Company
from search.search_result import SearchResult
from .base_provider import BaseProvider


class DuckDuckGoProvider(BaseProvider):

    def search(self, company: Company) -> SearchResult:

        query = f"{company.search_name} official website"

        print("=" * 80)
        print("DuckDuckGo Search")
        print("=" * 80)
        print("Query:", query)

        try:
            results = list(DDGS().text(query, max_results=5))

            if not results:
                return SearchResult(
                    company_name=company.company_name,
                    success=False,
                    error="No DuckDuckGo results.",
                )

            print("Results Found:", len(results))

            # Websites that are usually NOT the company's official website
            BLACKLIST = [
                "wikipedia.org",
                "linkedin.com",
                "facebook.com",
                "instagram.com",
                "x.com",
                "twitter.com",
                "youtube.com",
                "crunchbase.com",
                "bloomberg.com",
                "moneycontrol.com",
                "zaubacorp.com",
                "tofler.in",
                "indiamart.com",
            ]

            best_url = None

            for result in results:

                url = result.get("href")

                if not url:
                    continue

                print("Candidate:", url)

                url_lower = url.lower()

                # Skip non-official websites
                if any(site in url_lower for site in BLACKLIST):
                    print("Skipped")
                    continue

                best_url = url
                break

            if best_url:
                return SearchResult(
                    company_name=company.company_name,
                    official_website=best_url,
                    source="DuckDuckGo",
                    confidence=0.95,
                    success=True,
                )

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error="No suitable official website found.",
            )

        except Exception as e:

            print("DuckDuckGo Error:", e)

            return SearchResult(
                company_name=company.company_name,
                success=False,
                error=str(e),
            )