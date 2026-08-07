import re

from models import Company


class CompanyCleaner:
    """
    Cleans and normalizes company names for searching.
    """

    REPLACEMENTS = {

        "PVT.": "PRIVATE",
        "PVT": "PRIVATE",

        "LTD.": "LIMITED",
        "LTD": "LIMITED",

        "CO.": "COMPANY",
        "CO": "COMPANY",

        "&": "AND"
    }

    def clean(self, company: Company) -> Company:

        search_name = company.company_name.upper()

        # Remove brackets
        search_name = re.sub(r"\(.*?\)", "", search_name)

        # Replace punctuation with spaces
        search_name = re.sub(r"[^\w\s]", " ", search_name)

        # Normalize common abbreviations
        for old, new in self.REPLACEMENTS.items():
            search_name = search_name.replace(old, new)

        # Remove extra whitespace
        search_name = re.sub(r"\s+", " ", search_name).strip()

        company.search_name = search_name

        return company