from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchResult:
    """
    Represents the outcome of searching for a company's
    official website.
    """

    company_name: str

    official_website: Optional[str] = None

    source: Optional[str] = None

    confidence: float = 0.0

    success: bool = False

    error: Optional[str] = None