import os
import re


class NamedEntityValidator:
    """
    Validates that an extracted phrase looks like a person's name.

    If spaCy and a model are installed, PERSON entities are used as a stronger
    signal. The fallback keeps the project usable without extra model downloads.
    """

    ORGANIZATION_WORDS = {
        "bank",
        "capital",
        "company",
        "corporation",
        "finance",
        "financial",
        "finserv",
        "foundation",
        "fund",
        "group",
        "holdings",
        "india",
        "industries",
        "limited",
        "llp",
        "nbfc",
        "private",
        "services",
        "trust",
    }

    NON_PERSON_WORDS = {
        "about",
        "audit",
        "board",
        "committee",
        "compliance",
        "contact",
        "details",
        "din",
        "director",
        "directors",
        "email",
        "governance",
        "investor",
        "leadership",
        "management",
        "office",
        "profile",
        "registered",
        "secretary",
        "team",
    }

    CONNECTOR_WORDS = {
        "and",
        "as",
        "by",
        "for",
        "from",
        "in",
        "is",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }

    NAME_TOKEN_PATTERN = re.compile(r"^[A-Z][A-Za-z.'-]+$")

    def __init__(self, model_name: str | None = None):

        self.nlp = self._load_spacy_model(
            model_name
            or os.getenv("DIRECTOR_EXTRACTOR_SPACY_MODEL")
            or "en_core_web_sm"
        )

    def _load_spacy_model(self, model_name: str):

        try:
            import spacy

            return spacy.load(model_name)

        except Exception:
            return None

    def _normalize(self, value: str) -> str:

        return re.sub(r"\s+", " ", value or "").strip().lower()

    def _person_entities(self, context: str) -> set[str]:

        if self.nlp is None:
            return set()

        doc = self.nlp(context)

        return {
            self._normalize(entity.text)
            for entity in doc.ents
            if entity.label_ == "PERSON"
        }

    def _looks_like_non_person_phrase(self, name: str) -> bool:

        words = name.split()
        lower_words = {word.lower().strip(".") for word in words}

        if lower_words & self.NON_PERSON_WORDS:
            return True

        if lower_words & self.ORGANIZATION_WORDS:
            return True

        if lower_words & self.CONNECTOR_WORDS:
            return True

        if any(len(word) == 1 for word in words):
            return True

        return False

    def score(self, name: str, context: str = "") -> int:

        name = re.sub(r"\s+", " ", name or "").strip()

        if not name:
            return 0

        words = name.split()

        if len(words) < 2 or len(words) > 5:
            return 0

        if self._looks_like_non_person_phrase(name):
            return 0

        if not all(self.NAME_TOKEN_PATTERN.fullmatch(word) for word in words):
            return 0

        score = 50

        if 2 <= len(words) <= 3:
            score += 20

        if all(word[0].isupper() and not word.isupper() for word in words):
            score += 10

        person_entities = self._person_entities(context)

        if person_entities:
            normalized_name = self._normalize(name)

            if any(
                normalized_name == entity
                or normalized_name in entity
                or entity in normalized_name
                for entity in person_entities
            ):
                score += 20
            else:
                score -= 30

        return max(0, min(score, 100))

    def is_person_name(self, name: str, context: str = "") -> bool:

        return self.score(name, context) >= 60
