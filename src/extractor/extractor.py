from models import Page

from models import Director

from .dom_parser import DOMParser
from .candidate_finder import CandidateFinder



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

        print("\n" + "=" * 80)
        print("DIRECTOR EXTRACTION")
        print("=" * 80)

        directors = []
        seen_names = set()

        candidates = self.extract_candidates(pages)

        print(f"Candidates Found: {len(candidates)}")

        for candidate in candidates:

            print("----------------------------------------")
            print("Name:", candidate.name)
            print("Designation:", candidate.designation)
            print("Source:", candidate.source)

            key = candidate.name.lower()

            if key in seen_names:
                continue

            seen_names.add(key)

            directors.append(
                Director(
                    name=candidate.name,
                    designation=candidate.designation,
                    source=candidate.source,
                    confidence=85.0,
                )
            )

        print(f"\nDirectors Extracted: {len(directors)}")

        return directors