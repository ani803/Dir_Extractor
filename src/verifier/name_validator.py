import re


class NameValidator:

    INVALID_WORDS = {

        "contact",
        "privacy",
        "policy",
        "career",
        "services",
        "products",
        "board",
        "director",
        "directors",
        "leadership",
        "management",
        "company",
        "investor",
        "relations",
        "download",
        "email",
        "phone",
        "office",
        "support",
        "about",
        "home",
        "news"
    }

    def is_valid(self, name: str) -> bool:

        if not name:
            return False

        name = name.strip()

        if len(name) < 5:
            return False

        lower = name.lower()

        for word in self.INVALID_WORDS:
            if word in lower:
                return False

        if re.search(r"\d", name):
            return False

        words = name.split()

        if len(words) < 2:
            return False

        if len(words) > 5:
            return False

        pattern = r"^[A-Z][A-Za-z.'-]+$"

        for word in words:

            if not re.fullmatch(pattern, word):
                return False

        return True
