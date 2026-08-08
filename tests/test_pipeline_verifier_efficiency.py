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


class CountingExtractor:
    """Records how many times each extraction method is called, so we can
    assert pages are only ever DOM-parsed once per company."""

    def __init__(self):
        self.extract_candidates_calls = 0
        self.extract_calls = 0

    def extract_candidates(self, pages):
        self.extract_candidates_calls += 1
        return ["candidate1", "candidate2"]

    def extract(self, pages):
        self.extract_calls += 1
        return []


class VerifierStub:
    def verify(self, candidates):
        return [
            Director(name="Jane Sharma", designation="Director", source="https://example.com")
        ]


def test_pipeline_parses_pages_only_once_when_verifier_present():

    extractor = CountingExtractor()

    pipeline = CompanyPipeline(
        cleaner=CleanerStub(),
        website_finder=WebsiteFinderStub(),
        crawler=CrawlerStub(),
        extractor=extractor,
        verifier=VerifierStub(),
    )

    company = pipeline.process(Company(row_number=1, company_name="Test Co"))

    assert extractor.extract_candidates_calls == 1
    assert extractor.extract_calls == 0
    assert company.status == "Completed"


def test_pipeline_uses_extract_when_no_verifier():

    extractor = CountingExtractor()

    pipeline = CompanyPipeline(
        cleaner=CleanerStub(),
        website_finder=WebsiteFinderStub(),
        crawler=CrawlerStub(),
        extractor=extractor,
        verifier=None,
    )

    pipeline.process(Company(row_number=1, company_name="Test Co"))

    assert extractor.extract_candidates_calls == 0
    assert extractor.extract_calls == 1
