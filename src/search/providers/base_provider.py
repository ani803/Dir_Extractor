from abc import ABC, abstractmethod

from models import Company
from search.search_result import SearchResult
from search.domain_matcher import DomainMatcher
from search.validators import WebsiteValidator


class BaseProvider(ABC):

    result_class = SearchResult

    # How much a provider's own search ranking is trusted before factoring
    # in whether the URL's domain actually resembles the company name. Kept
    # per-subclass so e.g. a paid Google CSE result can outweigh a generic
    # DuckDuckGo scrape when both look equally domain-plausible.
    BASE_TRUST = 0.85

    # A result whose domain doesn't resemble the company name at all is
    # still returned (better than nothing, and the pipeline's own crawler
    # will fail cleanly on a wrong site) but never allowed to look
    # confident enough to short-circuit WebsiteFinder's search across
    # providers.
    MIN_PLAUSIBLE_CONFIDENCE = 0.55

    _validator = WebsiteValidator()

    @abstractmethod
    def search(self, company: Company) -> SearchResult:
        pass

    def _best_match(self, company: Company, urls, source: str) -> SearchResult:
        """
        Given a list of candidate URLs (in the search API's own ranked
        order), pick the one whose domain best matches the company name and
        turn it into a confidence-scored SearchResult.

        Previously every provider just grabbed the very first URL it saw and
        stamped a fixed confidence on it (0.88-0.95) -- so a directory
        listing or an unrelated same-named company ranked #1 would be
        accepted as instantly as a perfect match. Scanning the whole result
        set and scoring each by how well its domain matches the company name
        catches the far more common case where the *right* site is #2 or #3
        while something like a news article or LinkedIn page (missed by a
        provider's own blacklist, if it even has one) is #1.
        """

        best_url = None
        best_score = -1.0

        for url in urls:

            if not url or not self._validator.validate(url):
                continue

            score = DomainMatcher.score(company.search_name or company.company_name, url)

            if score > best_score:
                best_score = score
                best_url = url

        if best_url is None:
            return SearchResult(
                company_name=company.company_name,
                success=False,
                error=f"No plausible official website in {source} results.",
            )

        # Blend the provider's own trust in its ranking with how well the
        # winning domain actually matches the company name, so a
        # weak-but-only-option match never masquerades as a sure thing.
        confidence = self.BASE_TRUST * (0.5 + 0.5 * best_score)
        confidence = max(confidence, self.MIN_PLAUSIBLE_CONFIDENCE * best_score)

        return SearchResult(
            company_name=company.company_name,
            official_website=best_url,
            source=source,
            confidence=round(min(confidence, 0.99), 4),
            success=True,
        )
