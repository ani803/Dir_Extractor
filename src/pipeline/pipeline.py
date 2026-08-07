from models import Company
from logger.logger import get_logger


logger = get_logger(__name__)


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

            logger.info("Processing: %s", company.company_name)

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

                    logger.warning("Website not found: %s", company.company_name)

                    return company

                company.website = search_result.official_website

            logger.info("Website: %s", company.website)

            # -----------------------------------------
            # Step 3 : Crawl Website
            # -----------------------------------------

            pages = self.crawler.crawl(company.website)

            logger.info("Pages downloaded: %s", len(pages))

            # -----------------------------------------
            # Step 4 : Extract Directors
            # -----------------------------------------
            #
            # The pages only get DOM-parsed and candidate-matched once here.
            # Previously this called extractor.extract(pages) (which itself
            # parses + finds candidates) and then, if a verifier was present,
            # called extractor.extract_candidates(pages) again -- parsing
            # every page a second time and throwing away the first result.

            if self.verifier is not None:

                candidates = self.extractor.extract_candidates(pages)

                directors = self.verifier.verify(candidates)

            else:

                directors = self.extractor.extract(pages)

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

            logger.exception("Pipeline exception for %s", company.company_name)

            company.status = "Failed"
            company.error = str(e)

            return company
