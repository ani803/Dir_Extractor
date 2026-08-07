class ConfidenceScorer:

    STRONG_TITLES = {
        "managing director",
        "whole time director",
        "whole-time director",
        "executive director",
        "independent director",
        "non executive director",
        "non-executive director",
        "additional director",
        "nominee director",
    }

    SOURCE_KEYWORDS = {
        "board",
        "director",
        "directors",
        "governance",
        "leadership",
        "management",
        "team",
    }

    def score(self, candidate):

        score = getattr(candidate, "confidence", 0) * 0.35

        if candidate.name:
            score += 20

        if candidate.designation:
            score += 15

        if len(candidate.name.split()) >= 2:
            score += 10

        designation = candidate.designation.lower()

        if designation in self.STRONG_TITLES:
            score += 15

        elif "director" in designation:
            score += 15

        context = candidate.context.lower()

        if candidate.name.lower() in context:
            score += 5

        if candidate.designation.lower() in context:
            score += 5

        source = (getattr(candidate, "source", "") or "").lower()

        if any(keyword in source for keyword in self.SOURCE_KEYWORDS):
            score += 10

        return min(score, 100)
