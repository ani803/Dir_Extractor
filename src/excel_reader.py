from pathlib import Path

import pandas as pd 
from models import Company


class ExcelReader:

    def __init__(self, file_path: Path):

        self.file_path = file_path

    def load(self) -> list[Company]:

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        df = pd.read_excel(self.file_path)


        if df.empty: 
            raise ValueError("Excel file is empty ")

        #removing completely empty rows and columns 
        df = df.dropna(how='all')

        #automatically locate the company name column 
        company_column = self._find_company_column(df)
        website_column = self._find_website_column(df)

        companies = []

        for index, row in df.iterrows():
            company_name = str(row[company_column]).strip()

            if company_name == "" or company_name.lower() == "nan":
                continue

            companies.append(
                Company(
                    row_number = index + 2, 
                    company_name = company_name,
                    website = self._clean_optional_value(row[website_column]) if website_column else None,
                )
            )

        return companies



    def _find_company_column(self, df: pd.DataFrame) -> str: 

        possible_columns  = [
            "Company", 
            "Company Name",
            "Name",
            "Business Name",
            "Organisation",
            "Organization",
            "Business",
            "Company_Name",
            "Entity", 
            "NBFC Name"
        ]

        for column in df.columns: 

            if str(column).strip() in possible_columns: 
                return column

        raise ValueError(
            f"Couldn't find a comapany name column.\n"
            f"Available columns:\n{list(df.columns)}"
        )

    def _find_website_column(self, df: pd.DataFrame) -> str | None:

        possible_columns = {
            "website",
            "website url",
            "url",
            "official website",
            "company website",
        }

        for column in df.columns:

            if str(column).strip().lower() in possible_columns:
                return column

        return None

    def _clean_optional_value(self, value) -> str | None:

        cleaned = str(value).strip()

        if cleaned == "" or cleaned.lower() == "nan":
            return None

        return cleaned
