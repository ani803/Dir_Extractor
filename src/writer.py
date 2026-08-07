from pathlib import Path

import pandas as pd


class ExcelWriter:
    """
    Writes processed company/director results to an Excel workbook.
    """

    def __init__(self, file_path: Path):

        self.file_path = file_path

    def save(self, companies):

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        rows = []

        for company in companies:

            if company.directors:

                for director in company.directors:

                    rows.append(
                        {
                            "Row Number": company.row_number,
                            "Company Name": company.company_name,
                            "Search Name": company.search_name,
                            "Website": company.website,
                            "Director Name": director.name,
                            "Designation": director.designation,
                            "Source": director.source,
                            "Confidence": director.confidence,
                            "Status": company.status,
                            "Error": company.error,
                        }
                    )

            else:

                rows.append(
                    {
                        "Row Number": company.row_number,
                        "Company Name": company.company_name,
                        "Search Name": company.search_name,
                        "Website": company.website,
                        "Director Name": "",
                        "Designation": "",
                        "Source": "",
                        "Confidence": "",
                        "Status": company.status,
                        "Error": company.error,
                    }
                )

        pd.DataFrame(rows).to_excel(self.file_path, index=False)
