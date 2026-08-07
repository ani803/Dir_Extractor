from urllib.parse import urlparse


class LinkScorer:
    """
    Version 2.0

    Scores links according to how likely they are
    to contain company director / leadership information.
    """

    POSITIVE_KEYWORDS = {

        # Highest priority
        "board": 120,
        "board-of-directors": 150,
        "directors": 120,
        "director": 100,

        "leadership": 100,
        "management": 90,
        "executive": 90,
        "executives": 90,
        "governance": 85,

        "our-team": 80,
        "team": 70,
        "people": 70,
        "leaders": 70,
        "leadership-team": 90,

        "about": 60,
        "about-us": 60,
        "company": 40,
        "corporate": 40,

        "chairman": 90,
        "ceo": 80,
        "cfo": 70,
        "md": 70,
        "officers": 80,
    }

    NEGATIVE_KEYWORDS = {

        ".pdf": -200,

        "pdf": -150,
        "download": -120,
        "downloads": -120,

        "investor": -120,
        "investor_updates": -150,

        "annual-report": -150,
        "annual_report": -150,

        "financial-results": -120,
        "results": -100,

        "press-release": -90,
        "press_release": -90,

        "news": -70,
        "media": -70,

        "shareholder": -70,

        "privacy": -200,
        "cookie": -200,
        "terms": -200,
        "policy": -150,

        "login": -200,
        "signup": -200,
        "register": -200,

        "career": -100,
        "careers": -100,
        "jobs": -100,

        "contact": -30,
    }

    def score(self, links):

        for link in links:

            score = 0

            url = link.url.lower()

            text = (link.text or "").lower()

            ###################################################
            # Positive URL keywords
            ###################################################

            for keyword, value in self.POSITIVE_KEYWORDS.items():

                if keyword in url:
                    score += value

            ###################################################
            # Positive anchor text
            ###################################################

            for keyword, value in self.POSITIVE_KEYWORDS.items():

                if keyword in text:
                    score += value // 2

            ###################################################
            # Negative URL keywords
            ###################################################

            for keyword, value in self.NEGATIVE_KEYWORDS.items():

                if keyword in url:
                    score += value

            ###################################################
            # URL depth
            ###################################################

            parsed = urlparse(url)

            path = parsed.path.strip("/")

            if path == "":
                score += 20

            depth = len([p for p in path.split("/") if p])

            if depth == 1:
                score += 25

            elif depth == 2:
                score += 15

            elif depth == 3:
                score += 5

            else:
                score -= 15

            ###################################################
            # Bonus for clean URLs
            ###################################################

            if "?" not in url:
                score += 10

            ###################################################
            # Penalize very long URLs
            ###################################################

            if len(url) > 120:
                score -= 15

            ###################################################
            # Store final score
            ###################################################

            link.score = score

        return sorted(
            links,
            key=lambda x: x.score,
            reverse=True,
        )