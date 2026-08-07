from urllib.parse import urlparse


class LinkFilter:
    """
    Version 2.0

    Removes links that are extremely unlikely
    to contain director information.
    """

    SKIP_KEYWORDS = {

        ".pdf",

        "pdf",

        "download",
        "downloads",

        "investor",
        "investor_updates",

        "financial-results",
        "results",

        "annual-report",
        "annual_report",

        "press-release",
        "press_release",

        "privacy",
        "cookie",

        "terms",
        "policy",

        "login",
        "signup",
        "register",

        "careers",
        "career",
        "jobs",

        "news",
        "media",

        "rss",

        "shareholder",

        "mailto:",
        "javascript:",
    }

    SOCIAL_DOMAINS = {

        "facebook.com",
        "linkedin.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "tiktok.com",
        "wa.me",
    }

    def __init__(self, same_domain=True):

        self.same_domain = same_domain

    def filter(self, homepage_url: str, links):

        homepage_domain = urlparse(homepage_url).netloc

        filtered = []

        seen = set()

        for link in links:

            url = link.url.lower()

            if url in seen:
                continue

            seen.add(url)

            if any(keyword in url for keyword in self.SKIP_KEYWORDS):
                continue

            if any(domain in url for domain in self.SOCIAL_DOMAINS):
                continue

            if self.same_domain:

                domain = urlparse(url).netloc

                if domain != homepage_domain:
                    continue

            filtered.append(link)

        return filtered