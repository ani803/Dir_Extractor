import re

from models import Candidate
from .ner_validator import NamedEntityValidator
from .title_matcher import TitleMatcher
from verifier.name_validator import NameValidator


class CandidateFinder:

    BLACKLIST = {
        "annual",
        "board",
        "boardroom",
        "branch",
        "business",
        "report",
        "reports",
        "result",
        "results",
        "meeting",
        "closure",
        "window",
        "trading",
        "stock",
        "exchange",
        "press",
        "release",
        "postal",
        "ballot",
        "notice",
        "book",
        "investor",
        "update",
        "updates",
        "policy",
        "disclosure",
        "requirements",
        "obligations",
        "fund",
        "funds",
        "shares",
        "equity",
        "price",
        "movement",
        "award",
        "appointment",
        "letter",
        "code",
        "vision",
        "mission",
        "culture",
        "brand",
        "profile",
        "group",
        "company",
        "companies",
        "corporate",
        "industry",
        "industries",
        "audit",
        "committee",
        "financial",
        "announcement",
        "communication",
        "governance",
        "director",
        "directors",
        "details",
        "din",
        "email",
        "experience",
        "phone",
        "qualification",
        "registered",
        "office",
        "secretary",
        "tenure",
    }

    PREFIXES = {
        "Mr",
        "Mister",
        "Mrs",
        "Ms",
        "Miss",
        "Dr",
        "Prof",
        "Shri",
        "Smt",
    }

    NAME_JOINERS = {
        "and",
        "or",
        "with",
        "of",
        "the",
        "as",
        "is",
        "are",
        "was",
        "were",
    }

    NAME_PATTERN = re.compile(
        r"(?:Mr\.?|Mrs\.?|Ms\.?|Miss|Dr\.?|Prof\.?|Shri|Smt\.?)?\s*"
        r"[A-Z][a-zA-Z'-]+"
        r"(?:\s+[A-Z][a-zA-Z'-]+){1,4}"
    )

    TITLE_BOUNDARY_PATTERN = r"(?<![A-Za-z]){}(?![A-Za-z])"

    def __init__(self):
        self.name_validator = NameValidator()
        self.ner_validator = NamedEntityValidator()
        self.title_matcher = TitleMatcher()

    def _find_names(self, text: str) -> list[str]:

        names = []

        for match in re.finditer(rf"(?=({self.NAME_PATTERN.pattern}))", text):
            name = " ".join(match.group(1).split())

            if name and name not in names:
                names.append(name)

        return names

    def _find_name_matches(self, text: str):

        matches = []

        for match in re.finditer(rf"(?=({self.NAME_PATTERN.pattern}))", text):
            raw_name = match.group(1)
            clean_name = self._clean_name(raw_name)

            if not clean_name:
                continue

            start = match.start(1)
            end = start + len(raw_name)

            if any(
                existing["name"] == clean_name
                and existing["start"] == start
                and existing["end"] == end
                for existing in matches
            ):
                continue

            matches.append(
                {
                    "name": clean_name,
                    "start": start,
                    "end": end,
                }
            )

        return matches

    def _clean_name(self, name: str) -> str:

        name = " ".join(name.split())
        name = re.sub(r"^(Mr|Mister|Mrs|Ms|Miss|Dr|Prof|Shri|Smt)\.?\s+", "", name)
        name = re.sub(r"\s+", " ", name).strip(" ,:-|")

        return name

    def _is_part_of_longer_title(self, text: str, match, title: str) -> bool:
        return False

    def _title_matches(self, text: str, title: str):

        return self.title_matcher.find(text)

    def _relation_score(self, name_match, title_match, text: str) -> int | None:

        if (
            name_match["start"] < title_match.end()
            and title_match.start() < name_match["end"]
        ):
            return None

        if name_match["end"] <= title_match.start():
            between = text[name_match["end"]:title_match.start()]

            if len(between) > 70:
                return None

            if re.search(r"[.;!?]", between):
                return None

            if re.search(r"\b(?:and|or|with)\b", between, re.IGNORECASE):
                return None

            if re.fullmatch(r"[\s,;:()|/\\-]*(?:is(?:\s+the)?|as(?:\s+the)?|serves\s+as(?:\s+the)?|appointed\s+as(?:\s+the)?|acts\s+as(?:\s+the)?|-\s*)?[\s,;:()|/\\-]*", between, re.IGNORECASE):
                return 100 - len(between)

            if len(between.strip()) <= 4:
                return 80 - len(between)

            return None

        between = text[title_match.end():name_match["start"]]

        if len(between) > 50:
            return None

        if re.search(r"[.;!?]", between):
            return None

        if re.fullmatch(r"[\s,;:()|/\\-]*(?:name)?[\s,;:()|/\\-]*", between, re.IGNORECASE):
            return 90 - len(between)

        return None

    def _find_related_names(self, text: str, title_match) -> list[str]:

        start = max(0, title_match.start - 120)
        end = min(len(text), title_match.end + 120)
        context = text[start:end]
        relative_title_match = re.search(
            self.TITLE_BOUNDARY_PATTERN.format(
                re.escape(title_match.match_text)
            ),
            context,
            re.IGNORECASE,
        )

        if relative_title_match is None:
            return []

        scored_names = []

        for name_match in self._find_name_matches(context):
            score = self._relation_score(
                name_match,
                relative_title_match,
                context,
            )

            if score is None:
                continue

            scored_names.append(
                (
                    score,
                    name_match["name"],
                )
            )

        scored_names.sort(reverse=True)

        return [
            name
            for _, name in scored_names
        ]

    def _looks_like_person(self, name: str) -> bool:

        if not name:
            return False

        name = " ".join(name.split())

        if any(ch.isdigit() for ch in name):
            return False

        words = name.replace(".", "").split()

        if words and words[0] in self.PREFIXES:
            words = words[1:]

        if len(words) < 2 or len(words) > 5:
            return False

        for word in words:
            if word.lower() in self.BLACKLIST:
                return False

        if len(set(words)) == 1:
            return False

        return True

    def find(self, cards):

        candidates = []
        seen = set()

        for card in cards:

            text = " ".join(card.text.split())

            for match in self.title_matcher.find(text):

                    start = max(0, match.start - 120)
                    end = min(len(text), match.end + 120)
                    context = text[start:end]
                    names = self._find_related_names(text, match)

                    # _find_related_names returns every capitalized phrase in
                    # the window around this title, ranked by how closely it
                    # relates to the title match -- not just the one name
                    # that actually goes with it. The old code turned EVERY
                    # one of them into a separate candidate for this same
                    # title, so a title next to two or three unrelated names
                    # (e.g. two board members' names sitting close together
                    # in flattened table text) produced multiple false
                    # "director" rows sharing one title. Only the single
                    # best-ranked name that survives every check is kept per
                    # title occurrence.

                    for name in names:

                        name = self._clean_name(name)

                        if not self._looks_like_person(name):
                            continue

                        if not self.name_validator.is_valid(name):
                            continue

                        nlp_confidence = self.ner_validator.score(
                            name,
                            context,
                        )

                        if nlp_confidence < 60:
                            continue

                        key = name.lower()

                        if key in seen:
                            break

                        seen.add(key)

                        candidates.append(
                            Candidate(
                                name=name,
                                designation=match.title,
                                context=context,
                                source=card.source_url,
                                confidence=min(
                                    100,
                                    (nlp_confidence * 0.7) + (match.score * 0.3),
                                ),
                            )
                        )

                        break

        return candidates
