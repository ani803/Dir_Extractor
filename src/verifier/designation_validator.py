class DesignationValidator:

    VALID_TITLES = {

        "director",

        "managing director",

        "whole time director",

        "executive director",

        "independent director",

        "chairman",

        "chairperson",

        "non executive director",

        "nominee director",

        "additional director",

        "ceo",

        "chief executive officer",

        "board member"
    }

    INVALID_TITLES = {

        "sales director",

        "marketing director",

        "creative director",

        "art director",

        "technical director",

        "project director",

        "assistant director",

        "film director"
    }

    def is_valid(self, designation: str) -> bool:

        if not designation:
            return False

        designation = designation.lower().strip()

        for title in self.INVALID_TITLES:

            if title in designation:
                return False

        for title in self.VALID_TITLES:

            if title in designation:
                return True

        return False