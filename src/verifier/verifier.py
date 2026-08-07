from models import Director

from .name_validator import NameValidator
from .designation_validator import DesignationValidator
from .confidence import ConfidenceScorer


class DirectorVerifier:

    def __init__(self):

        self.name_validator = NameValidator()

        self.designation_validator = DesignationValidator()

        self.confidence = ConfidenceScorer()

    def verify(self, candidates):

        verified = []

        seen = set()

        for candidate in candidates:

            if not self.name_validator.is_valid(candidate.name):
                continue

            if not self.designation_validator.is_valid(
                candidate.designation
            ):
                continue

            key = (

                candidate.name.lower(),

                candidate.designation.lower()

            )

            if key in seen:
                continue

            seen.add(key)

            verified.append(

                Director(

                    name=candidate.name,

                    designation=candidate.designation,

                    confidence=self.confidence.score(candidate),

                    source=getattr(candidate, "source", "")

                )

            )

        return verified