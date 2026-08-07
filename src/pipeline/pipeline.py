from models import Company
import traceback


class CompanyPipeline:
    """
    Complete processing pipeline.

    Company
        ↓
    Cleaner
        ↓
    WebsiteFinder
        ↓
    Crawler
        ↓
    DirectorExtractor
        ↓
    Company
    """

    def __init__(
        self,
        cleaner,
        website_finder,
        crawler,
        extractor,
        verifier=None,
    ):

        self.cleaner = cleaner
        self.website_finder = website_finder
        self.crawler = crawler
        self.extractor = extractor
        self.verifier = verifier

    def process(self, company: Company) -> Company:

        try:

            print("=" * 70)
            print(f"Processing : {company.company_name}")

            # -----------------------------------------
            # Step 1 : Clean company name
            # -----------------------------------------

            company = self.cleaner.clean(company)

            # -----------------------------------------
            # Step 2 : Find Website
            # -----------------------------------------

            if not company.website:

                search_result = self.website_finder.find(company)

                if not search_result.success:

                    company.status = "Website Not Found"

                    print("Website not found.")

                    return company

                company.website = search_result.official_website

            print(f"Website : {company.website}")

            # -----------------------------------------
            # Step 3 : Crawl Website
            # -----------------------------------------

            pages = self.crawler.crawl(company.website)

            print(f"Pages downloaded : {len(pages)}")

            # -----------------------------------------
            # Step 4 : Extract Directors
            # -----------------------------------------

            print(type(self.extractor))
            print(self.extractor.__class__.__module__)
            print(dir(self.extractor))

            directors = self.extractor.extract(pages)

            # -----------------------------------------
            # Step 5 : Verify (optional)
            # -----------------------------------------

            if self.verifier is not None:


                candidates = self.extractor.extract_candidates(pages)

                directors = self.verifier.verify(candidates)

            company.directors.extend(directors)

            # -----------------------------------------
            # Step 6 : Status
            # -----------------------------------------

            if len(company.directors):

                company.status = "Completed"

            else:

                company.status = "No Directors Found"

            return company

        except Exception as e:

            print("\n" + "=" * 80)
            print("PIPELINE EXCEPTION")
            print("=" * 80)

            traceback.print_exc()

            company.status = "Failed"
            company.error = str(e)

            print("\nError:", e)

            return company