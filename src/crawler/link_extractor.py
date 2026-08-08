from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse

from models import Link
from models import Page
from logger.logger import get_logger


logger = get_logger(__name__)


class LinkExtractor:
    """
    Version 2.0

    Responsibilities
    ----------------
    ✓ Extract hyperlinks
    ✓ Convert relative URLs
    ✓ Normalize URLs
    ✓ Remove duplicates
    ✓ Ignore invalid links

    NO filtering.
    NO scoring.
    """

    INVALID_SCHEMES = (
        "javascript:",
        "mailto:",
        "tel:",
        "#",
    )

    def normalize_url(self, url: str) -> str:

        parsed = urlparse(url)

        # Remove fragments (#section)
        parsed = parsed._replace(fragment="")

        # Remove query parameters (optional)
        parsed = parsed._replace(query="")

        url = urlunparse(parsed)

        return url.rstrip("/")

    def extract(self, page: Page) -> list[Link]:

        soup = BeautifulSoup(page.html, "html.parser")

        links = []
        seen = set()

        for tag in soup.find_all("a", href=True):

            href = tag["href"].strip()

            if not href:
                continue

            if href.lower().startswith(self.INVALID_SCHEMES):
                continue

            absolute = urljoin(page.url, href)

            absolute = self.normalize_url(absolute)

            if absolute in seen:
                continue

            seen.add(absolute)

            text = tag.get_text(" ", strip=True)

            links.append(
                Link(
                    url=absolute,
                    text=text,
                )
            )

        logger.info("Extracted %s unique links", len(links))

        return links
