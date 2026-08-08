from urllib.parse import urlparse


class WebsiteValidator:
    """
    Validates that a URL looks like it could be a company's own official
    website, filtering out the aggregators, directories, social networks,
    news sites, and registry lookups that search engines routinely rank
    above (or alongside) the real site.

    This is the single shared blacklist -- previously each search provider
    had its own inconsistent copy (or none at all: only DuckDuckGo actually
    filtered its own results before this validator ran), so a provider like
    Google or Bing could hand back a directory/news page and it would sail
    through untouched.
    """

    BAD_DOMAINS = {
        # Social / video
        "linkedin.com",
        "facebook.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "pinterest.com",

        # Encyclopedic / reference
        "wikipedia.org",
        "wikidata.org",

        # Company registries, filings & corporate-data aggregators
        "zaubacorp.com",
        "tofler.in",
        "instafinancials.com",
        "probe42.in",
        "thecompanycheck.com",
        "opencorporates.com",
        "mca.gov.in",
        "zoominfo.com",
        "rocketreach.co",
        "signalhire.com",
        "crunchbase.com",
        "owler.com",
        "dnb.com",

        # Business directories / listings / classifieds
        "indiamart.com",
        "justdial.com",
        "sulekha.com",
        "tradeindia.com",
        "yellowpages.in",
        "yellowpages.com",
        "exportersindia.com",

        # Finance / markets data (about the company, not run by it)
        "moneycontrol.com",
        "screener.in",
        "bseindia.com",
        "nseindia.com",
        "tickertape.in",
        "trendlyne.com",
        "wallmine.com",

        # News & media
        "bloomberg.com",
        "reuters.com",
        "economictimes.indiatimes.com",
        "livemint.com",
        "business-standard.com",
        "ndtv.com",
        "financialexpress.com",

        # Job boards / review sites
        "glassdoor.com",
        "indeed.com",
        "ambitionbox.com",

        # Generic search/portal pages that occasionally leak through as a
        # "result" from a misconfigured provider
        "google.com",
        "bing.com",
        "duckduckgo.com",
    }

    def _domain_matches(self, netloc: str, bad_domain: str) -> bool:
        """
        True if netloc IS bad_domain or a subdomain of it (e.g.
        'in.linkedin.com' matches 'linkedin.com'), never a coincidental
        substring (e.g. 'notlinkedin.com' must NOT match 'linkedin.com').
        """

        return netloc == bad_domain or netloc.endswith("." + bad_domain)

    def validate(self, website) -> bool:

        if not website:
            return False

        domain = urlparse(website).netloc.lower()

        # Strip a leading userinfo/port if present.
        domain = domain.split("@")[-1].split(":")[0]

        if not domain:
            return False

        for bad in self.BAD_DOMAINS:

            if self._domain_matches(domain, bad):
                return False

        return True
