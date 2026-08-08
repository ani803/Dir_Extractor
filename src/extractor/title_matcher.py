import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TitleMatch:
    title: str
    start: int
    end: int
    score: int
    match_text: str


class TitleMatcher:
    """
    Rule-based title matcher for board and senior management titles.
    """

    TITLE_RULES = [
        ("Whole-Time Director", r"whole[-\s]+time\s+director", 95),
        ("Managing Director", r"managing\s+director", 95),
        ("Independent Director", r"independent\s+director", 90),
        ("Executive Director", r"executive\s+director", 88),
        ("Non-Executive Director", r"non[-\s]+executive\s+director", 88),
        ("Additional Director", r"additional\s+director", 84),
        ("Nominee Director", r"nominee\s+director", 84),
        ("Chief Executive Officer", r"chief\s+executive\s+officer", 78),
        ("CEO", r"ceo", 76),
        ("Chairperson", r"chair(?:person|woman|man)", 82),
        ("Board Member", r"board\s+member", 74),
        ("Managing Partner", r"managing\s+partner", 72),
        ("Director", r"director", 70),
    ]

    def __init__(self):
        self.patterns = [
            (
                title,
                re.compile(rf"(?<![A-Za-z]){pattern}(?![A-Za-z])", re.IGNORECASE),
                score,
            )
            for title, pattern, score in self.TITLE_RULES
        ]

    def find(self, text: str) -> list[TitleMatch]:
        matches = []

        for title, pattern, score in self.patterns:
            for match in pattern.finditer(text):
                matches.append(
                    TitleMatch(
                        title=title,
                        start=match.start(),
                        end=match.end(),
                        score=score,
                        match_text=match.group(0),
                    )
                )

        matches.sort(
            key=lambda item: (
                item.start,
                -(item.end - item.start),
                -item.score,
            )
        )

        filtered = []

        for match in matches:
            if any(
                existing.start <= match.start
                and match.end <= existing.end
                and existing.score >= match.score
                for existing in filtered
            ):
                continue

            filtered.append(match)

        return filtered
