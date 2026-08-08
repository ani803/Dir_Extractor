import argparse
from pathlib import Path

from cleaner import CompanyCleaner
from crawler.crawler import Crawler
from excel_reader import ExcelReader
from extractor.extractor import DirectorExtractor
from pipeline.pipeline import CompanyPipeline
from verifier.verifier import DirectorVerifier
from search.website_finder import WebsiteFinder
from search.providers import (
    DuckDuckGoProvider,
    BraveProvider,
    GoogleProvider,
    BingProvider,
    SerpApiProvider,
)
from writer import ExcelWriter
from logger.logger import get_logger
from metrics import RuntimeMetrics
from resume import ResumeState

from config.config import Config
import config.config as config

logger = get_logger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_parser():

    parser = argparse.ArgumentParser(
        description="Extract company directors from official websites listed in an Excel file."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "input" / "List of NBFCs.xlsx",
        help="Input Excel file containing a company name column.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "output" / "directors.xlsx",
        help="Output Excel file for extracted directors.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of companies to process.",
    )

    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip candidate validation and confidence scoring.",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip companies already marked completed in the resume state file.",
    )

    parser.add_argument(
        "--state-file",
        type=Path,
        default=PROJECT_ROOT / "cache" / "resume_state.json",
        help="Path to the resume state file.",
    )

    return parser


def main():

    args = build_parser().parse_args()

    reader = ExcelReader(args.input)

    companies = reader.load()

    if args.limit is not None:
        companies = companies[:args.limit]

    metrics = RuntimeMetrics()
    metrics.start(len(companies))
    resume_state = ResumeState(args.state_file) if args.resume else None
    writer = ExcelWriter(args.output)

    processed = []

    with Crawler() as crawler:

        pipeline = CompanyPipeline(
            cleaner=CompanyCleaner(),
            website_finder=WebsiteFinder(
                providers=[
                    DuckDuckGoProvider(),
                    BraveProvider(),
                    GoogleProvider(),
                    SerpApiProvider(),
                    BingProvider(),
                    ]
                ),
            crawler=crawler,
            extractor=DirectorExtractor(),
            verifier=None if args.no_verify else DirectorVerifier(),
        )

        for index, company in enumerate(companies, start=1):

            logger.info("Progress: %s/%s", index, len(companies))

            if resume_state and resume_state.should_skip(company):
                metrics.record_skip()
                logger.info(
                    "Skipping completed row %s: %s",
                    company.row_number,
                    company.company_name,
                )
                continue

            company = pipeline.process(company)

            processed.append(company)
            metrics.record_company(company)

            if resume_state:
                writer.save(processed)

            if resume_state and company.status != "Failed":
                resume_state.mark_completed(company)

            logger.info("Status: %s | %s", company.status, metrics.progress_text())

    writer.save(processed)

    logger.info("Pipeline finished. Results saved to: %s", args.output)
    logger.info("Final metrics: %s", metrics.progress_text())


if __name__ == "__main__":
    main()
