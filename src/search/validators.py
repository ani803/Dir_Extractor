from urllib.parse import urlparse


class WebsiteValidator:

    """
    Validates search results.
    """

    BAD_DOMAINS = {

        "linkedin.com",

        "facebook.com",

        "instagram.com",

        "twitter.com",

        "youtube.com",

        "wikipedia.org",

        "moneycontrol.com",

        "crunchbase.com"
    }

    def validate(self, website):

        if website is None:

            return False

        domain = urlparse(
            website
        ).netloc.lower()

        for bad in self.BAD_DOMAINS:

            if bad in domain:

                return False

        return True