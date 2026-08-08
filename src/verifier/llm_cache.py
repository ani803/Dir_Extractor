import hashlib
import json
from pathlib import Path


class VerificationCache:
    """
    Disk-backed cache of AI verification results.

    Keyed by a hash of (name, designation, context) so the same candidate
    text is never sent to the LLM twice -- across a single run's retries,
    across --resume runs, and across re-runs after a crash. This matters
    because AI verification is the most expensive step in the pipeline
    (network latency + token cost), and the same website is often re-crawled
    (e.g. after a resume) with identical candidates.
    """

    def __init__(self, cache_file: Path | None = None):

        project_root = Path(__file__).resolve().parents[2]

        self.cache_file = cache_file or project_root / "cache" / "ai_verifications.json"

        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        self._cache = self._load()
        self._dirty = False

    def _load(self) -> dict:

        try:

            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        except (json.JSONDecodeError, FileNotFoundError, OSError):

            return {}

    @staticmethod
    def key_for(name: str, designation: str, context: str) -> str:

        raw = "|".join(
            [
                (name or "").strip().lower(),
                (designation or "").strip().lower(),
                (context or "")[:300].strip().lower(),
            ]
        )

        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str):

        return self._cache.get(key)

    def put(self, key: str, result: dict):

        self._cache[key] = result
        self._dirty = True

    def flush(self):
        """Write to disk only if something changed since the last flush."""

        if not self._dirty:
            return

        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2)

        self._dirty = False
