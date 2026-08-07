class ConfidenceScorer:

    def score(self, candidate):

        score = getattr(candidate, "confidence", 0) * 0.3

        if candidate.name:
            score += 30

        if candidate.designation:
            score += 30

        if len(candidate.name.split()) >= 2:
            score += 10

        if "director" in candidate.designation.lower():
            score += 15

        if len(candidate.context) > 30:
            score += 15

        return min(score, 100)
