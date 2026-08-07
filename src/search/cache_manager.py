import json
from pathlib import Path


class CacheManager:

    def __init__(self, cache_file: Path | None = None):

        project_root = Path(__file__).resolve().parents[2]

        self.cache_file = cache_file or project_root / "cache" / "websites.json"

        self.cache_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.cache_file.exists():
            self.cache_file.write_text(
                "{}",
                encoding="utf-8",
            )

        self.cache = self._load()

    def _load(self):

        try:

            with open(
                self.cache_file,
                "r",
                encoding="utf-8",
            ) as f:

                return json.load(f)

        except (
            json.JSONDecodeError,
            FileNotFoundError,
            OSError,
        ):

            return {}

    def save(self):

        with open(
            self.cache_file,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                self.cache,
                f,
                indent=4,
            )

    def get(self, company_name):

        return self.cache.get(company_name)

    def put(self, company_name, website):

        self.cache[company_name] = website

        self.save()

    def clear(self):

        self.cache = {}

        self.save()
