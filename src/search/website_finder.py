from models import Company

from search.cache_manager import CacheManager
from search.validators import WebsiteValidator
from search.search_result import SearchResult


class WebsiteFinder:

    def __init__(self, providers):

        self.providers = providers

        self.cache = CacheManager()

        self.validator = WebsiteValidator()

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

        for provider in self.providers:

            result = provider.search(company)

            if not result.success:
                continue

            if not self.validator.validate(result.official_website):
                continue

            self.cache.put(
                company.search_name,
                result.official_website,
            )

            return result

        return SearchResult(
            company_name=company.company_name,
            success=False,
            error="No provider returned a valid website.",
        )