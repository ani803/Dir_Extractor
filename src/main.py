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

from config.config import Config
import config.config as config

print("Config file:", config.__file__)
print("Google:", Config.GOOGLE_API_KEY)
print("CSE:", Config.GOOGLE_CSE_ID)


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

    return parser


def main():

    args = build_parser().parse_args()

    reader = ExcelReader(args.input)

    companies = reader.load()

    if args.limit is not None:
        companies = companies[:args.limit]

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
        crawler=Crawler(),
        extractor=DirectorExtractor(),
        verifier=None if args.no_verify else DirectorVerifier(),
    )

    processed = []

    for company in companies:

        company = pipeline.process(company)

        processed.append(company)

        print(company.status)
        print("=" * 60)

    ExcelWriter(args.output).save(processed)

    print(f"Pipeline Finished. Results saved to: {args.output}")


if __name__ == "__main__":
    main()
