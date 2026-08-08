import re
from difflib import SequenceMatcher
from urllib.parse import urlparse


class DomainMatcher:
    """
    Scores how well a URL's domain matches a company name.

    Every search provider used to trust whatever URL a search API returned
    first, with a fixed hand-picked confidence (0.88-0.95) regardless of
    whether that URL had anything to do with the company. A provider's #1
    organic result is very often a directory listing, a news article, or an
    unrelated company with a similar name -- and once one provider returned
    *anything* with confidence >= SEARCH_HIGH_CONFIDENCE, WebsiteFinder
    locked it in immediately and every later step (crawling, extraction)
    silently ran against the wrong company.

    This gives providers a real, cheap (no extra network calls) signal:
    normalize both the company name and the domain's registrable name down
    to their core tokens (stripping legal suffixes like Private/Limited/
    NBFC/Finance/India/etc.), then score their similarity. Providers combine
    this with their own trust in the search API to produce a confidence that
    actually reflects whether the result looks like the company.
    """

    LEGAL_SUFFIXES = {
        "private", "pvt", "limited", "ltd", "llp", "llc", "inc",
        "incorporated", "corporation", "corp", "company", "co",
        "and", "the", "group", "holdings", "india", "indian",
        "nbfc", "finance", "financial", "financials", "services",
        "service", "capital", "investments", "investment", "trust",
        "fund", "funds",
    }

    @staticmethod
    def _tokens(value: str) -> set[str]:

        value = (value or "").lower()
        value = re.sub(r"[^a-z0-9\s]", " ", value)

        return {
            token
            for token in value.split()
            if token and token not in DomainMatcher.LEGAL_SUFFIXES
        }

    @staticmethod
    def registrable_name(url: str) -> str:
        """Best-effort second-level domain, e.g. 'abc-finance' from
        'https://www.abc-finance.co.in/about'."""

        try:
            netloc = urlparse(url).netloc.lower()
        except ValueError:
            return ""

        netloc = netloc.split("@")[-1].split(":")[0]

        parts = [p for p in netloc.split(".") if p]

        # Drop the common leading "www" and trailing ccTLD/gTLD segments
        # (co.in, com.au, com, in, ...) to isolate the registrable label.
        if parts and parts[0] == "www":
            parts = parts[1:]

        known_tlds = {"com", "in", "co", "net", "org", "biz", "info"}

        while len(parts) > 1 and parts[-1] in known_tlds:
            parts = parts[:-1]

        return parts[-1] if parts else ""

    @classmethod
    def score(cls, company_name: str, url: str) -> float:
        """
        Returns 0.0-1.0: how well the URL's domain matches the company name.
        """

        if not url:
            return 0.0

        domain_label = cls.registrable_name(url)

        if not domain_label:
            return 0.0

        company_tokens = cls._tokens(company_name)
        domain_tokens = cls._tokens(domain_label.replace("-", " "))

        if not company_tokens:
            return 0.0

        # Token overlap: how many of the company's meaningful words show up
        # in the domain (handles "sundaram-finance.in" for "Sundaram Finance
        # Ltd" even though the domain also has a legal-suffix word dropped).
        overlap = len(company_tokens & domain_tokens)
        overlap_score = overlap / len(company_tokens) if company_tokens else 0.0

        # Character-level similarity as a fallback for compound domains with
        # no spaces, e.g. "sundaramfinance.in" vs "Sundaram Finance".
        company_compact = "".join(sorted(company_tokens))
        domain_compact = "".join(sorted(domain_tokens)) or domain_label.replace("-", "")
        char_score = SequenceMatcher(None, company_compact, domain_compact).ratio()

        return max(overlap_score, char_score)
