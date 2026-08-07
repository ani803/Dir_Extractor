from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Director:
    """
    Represents a single director or board member.
    """

    name: str

    designation: Optional[str] = None

    source: Optional[str] = None

    confidence: float = 0.0


@dataclass
class SearchResult:
    official_website: Optional[str]
    confidence: float
    source: str


@dataclass
class Link:

    url: str

    text: str

    score: int = 0


@dataclass
class Candidate:
    """
    Represents a possible director candidate found on a webpage.
    """

    name: str

    designation: str

    context: str

    source: Optional[str] = None

    confidence: float = 0.0
    

@dataclass
class Page:
    """
    Represents one downloaded webpage.
    """

    url: str

    html: str

    title: str = ""


@dataclass
class PersonCard:
    """
    Represents one logical person section
    from a webpage.
    """

    text: str

    html: str

    source_url: str


@dataclass
class Company:
    """
    Represents a company throughout the pipeline.
    """

    row_number: int

    company_name: str

    search_name: str = ""

    search_result: Optional[SearchResult] = None

    website: Optional[str] = None

    directors: list[Candidate] = field(default_factory=list)

    status: str = "Pending"

    error: Optional[str] = None

