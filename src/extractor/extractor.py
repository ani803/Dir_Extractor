from models import Page

from models import Director

from .dom_parser import DOMParser
from .candidate_finder import CandidateFinder
from logger.logger import get_logger


logger = get_logger(__name__)



class DirectorExtractor:
    """
    Coordinates the complete director extraction pipeline.

    Pipeline:
        Pages
            ↓
        DOMParser
            ↓
        PersonCards
            ↓
        CandidateFinder
            ↓
        TitleMatcher
            ↓
        Director Objects
    """

    def __init__(self):

        self.dom_parser = DOMParser()

        self.candidate_finder = CandidateFinder()


    def extract_candidates(self, pages: list[Page]):

        candidates = []

        for page in pages:

            cards = self.dom_parser.parse(page)

            candidates.extend(self.candidate_finder.find(cards))

        return candidates


    def extract(self, pages: list[Page]) -> list[Director]:

        logger.info("Director extraction started")

        candidates = self.extract_candidates(pages)

        logger.info("Candidates found: %s", len(candidates))

        return self.build_directors(candidates)

    def build_directors(self, candidates: list) -> list[Director]:
        """
        Dedupe a list of already-found candidates into final Director
        objects. Kept separate from extract_candidates()/extract() so the
        pipeline can DOM-parse pages exactly once, then choose either this
        (no verifier) or the AI verifier's own dedupe path -- instead of
        re-parsing the same pages twice.
        """

        directors = []
        seen_names = set()

        for candidate in candidates:

            logger.debug(
                "Candidate: %s | %s | %s",
                candidate.name,
                candidate.designation,
                candidate.source,
            )

            key = candidate.name.lower()

            if key in seen_names:
                continue

            seen_names.add(key)

            directors.append(
                Director(
                    name=candidate.name,
                    designation=candidate.designation,
                    source=candidate.source,
                    confidence=candidate.confidence or 85.0,
                )
            )

        logger.info("Directors extracted: %s", len(directors))

        return directors
