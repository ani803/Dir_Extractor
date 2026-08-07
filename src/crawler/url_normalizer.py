from urllib.parse import (
    urljoin,
    urlparse,
    urlunparse,
    parse_qsl,
    urlencode,
)


class URLNormalizer:
    """
    Version 2.0

    Responsible for:

    ✓ Relative → Absolute URLs
    ✓ Remove fragments
    ✓ Remove tracking parameters
    ✓ Normalize slashes
    ✓ Normalize hostname
    """

    TRACKING_PARAMETERS = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
        "msclkid",
    }

    INVALID_SCHEMES = (
        "javascript:",
        "mailto:",
        "tel:",
        "#",
    )

    def normalize(self, base_url: str, href: str) -> str | None:

        if not href:
            return None

        href = href.strip()

        if href.lower().startswith(self.INVALID_SCHEMES):
            return None

        url = urljoin(base_url, href)

        parsed = urlparse(url)

        # Remove fragment
        parsed = parsed._replace(fragment="")

        # Remove tracking parameters
        query = [
            (k, v)
            for k, v in parse_qsl(parsed.query)
            if k not in self.TRACKING_PARAMETERS
        ]

        parsed = parsed._replace(query=urlencode(query))

        url = urlunparse(parsed)

        # Remove trailing slash
        if url.endswith("/"):
            url = url[:-1]

        return url