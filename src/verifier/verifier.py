from models import Director

from .name_validator import NameValidator
from .designation_validator import DesignationValidator
from .confidence import ConfidenceScorer
from .ai_verifier import AIAssistedVerifier


class DirectorVerifier:

    def __init__(self):

        self.name_validator = NameValidator()

        self.designation_validator = DesignationValidator()

        self.confidence = ConfidenceScorer()
        self.ai_verifier = AIAssistedVerifier()

    def verify(self, candidates):

        # Batch every candidate for this company through the AI verifier in
        # one pass (chunked internally) instead of one call per candidate.
        candidates = self.ai_verifier.verify(candidates)

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

                    source=getattr(candidate, "source", ""),

                    ai_verified=getattr(candidate, "ai_verified", None),

                    ai_reasoning=getattr(candidate, "ai_reasoning", ""),

                )

            )

        return verified
