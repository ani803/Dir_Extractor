from models import Company
from search.search_result import SearchResult
from search.website_finder import WebsiteFinder


class ProviderStub:
    def search(self, company):
        return SearchResult(
            company_name=company.company_name,
            official_website="https://example.com",
            source="stub",
            confidence=0.9,
            success=True,
        )


def test_website_finder_uses_provider_result():

    company = Company(
        row_number=1,
        company_name="Example Finance",
        search_name="EXAMPLE FINANCE",
    )

    finder = WebsiteFinder(providers=[ProviderStub()])
    finder.cache.cache = {}
    finder.cache.save = lambda: None

    result = finder.find(company)

    assert result.success is True
    assert result.official_website == "https://example.com"
