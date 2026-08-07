from dataclasses import dataclass
from time import perf_counter


@dataclass
class RuntimeMetrics:
    started_at: float = 0.0
    companies_total: int = 0
    companies_processed: int = 0
    websites_found: int = 0
    pages_crawled: int = 0
    directors_found: int = 0
    failures: int = 0
    skipped: int = 0

    def start(self, companies_total: int):
        self.started_at = perf_counter()
        self.companies_total = companies_total

    @property
    def elapsed_seconds(self) -> float:
        if not self.started_at:
            return 0.0

        return perf_counter() - self.started_at

    def record_company(self, company):
        self.companies_processed += 1

        if company.website:
            self.websites_found += 1

        if company.directors:
            self.directors_found += len(company.directors)

        if company.status in {"Failed", "Website Not Found"}:
            self.failures += 1

    def record_skip(self):
        self.skipped += 1

    @property
    def average_seconds_per_company(self) -> float:
        processed = self.companies_processed or 1
        return self.elapsed_seconds / processed

    @property
    def estimated_remaining_seconds(self) -> float:
        remaining = max(
            0,
            self.companies_total - self.companies_processed - self.skipped,
        )
        return remaining * self.average_seconds_per_company

    @property
    def success_rate(self) -> float:
        attempted = self.companies_processed or 1
        successes = attempted - self.failures
        return (successes / attempted) * 100

    def progress_text(self) -> str:
        if not self.companies_total:
            return "No companies loaded"

        percent = (self.companies_processed / self.companies_total) * 100

        return (
            f"{self.companies_processed}/{self.companies_total} "
            f"({percent:.1f}%) | "
            f"directors={self.directors_found} | "
            f"failures={self.failures} | "
            f"skipped={self.skipped} | "
            f"success={self.success_rate:.1f}% | "
            f"avg={self.average_seconds_per_company:.1f}s | "
            f"eta={self.estimated_remaining_seconds:.1f}s | "
            f"elapsed={self.elapsed_seconds:.1f}s"
        )
