import json
from pathlib import Path


class ResumeState:
    def __init__(self, path: Path):
        self.path = path
        self.completed_rows = set()
        self._load()

    def _load(self):
        if not self.path.exists():
            return

        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.completed_rows = set(data.get("completed_rows", []))

    def should_skip(self, company) -> bool:
        return company.row_number in self.completed_rows

    def mark_completed(self, company):
        self.completed_rows.add(company.row_number)
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "completed_rows": sorted(self.completed_rows),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
