from models import Company, Director
from pipeline.pipeline import CompanyPipeline
from search.search_result import SearchResult


class CleanerStub:
    def clean(self, company):
        company.search_name = company.company_name.upper()
        return company


class WebsiteFinderStub:
    def find(self, company):
        return SearchResult(
            company_name=company.company_name,
            official_website="https://example.com",
            source="test",
            confidence=1.0,
            success=True,
        )


class CrawlerStub:
    def crawl(self, website):
        return ["page"]


class ExtractorStub:
    def extract(self, pages):
        return [Director(name="Jane Sharma", designation="Director", source="https://example.com")]


def test_pipeline_marks_completed_when_directors_are_found():

    pipeline = CompanyPipeline(
        cleaner=CleanerStub(),
        website_finder=WebsiteFinderStub(),
        crawler=CrawlerStub(),
        extractor=ExtractorStub(),
    )

    company = pipeline.process(Company(row_number=2, company_name="Example Finance"))

    assert company.status == "Completed"
    assert company.website == "https://example.com"
    assert len(company.directors) == 1
