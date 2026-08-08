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

        "non-executive director",

        "nominee director",

        "additional director",

        "board member"
    }

    FUNCTIONAL_DIRECTOR_TITLES = {

        "sales director",

        "marketing director",

        "creative director",

        "art director",

        "technical director",

        "project director",

        "assistant director",

        "film director"
    }

    OFFICER_ONLY_TITLES = {

        "ceo",

        "chief executive officer",

        "cfo",

        "chief financial officer",

        "coo",

        "chief operating officer",

        "company secretary",

        "secretary",

        "founder",

        "advisor",

        "adviser",

        "president",
    }

    def is_valid(self, designation: str) -> bool:

        if not designation:
            return False

        designation = designation.lower().strip()

        for title in self.FUNCTIONAL_DIRECTOR_TITLES:

            if title in designation:
                return False

        has_board_title = any(
            title in designation
            for title in self.VALID_TITLES
        )

        if not has_board_title:

            for title in self.OFFICER_ONLY_TITLES:

                if title in designation:
                    return False

        for title in self.VALID_TITLES:

            if title in designation:
                return True

        return False
