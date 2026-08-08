import time

from config.config import Config
from logger.logger import get_logger

from .llm_cache import VerificationCache


logger = get_logger(__name__)


SYSTEM_PROMPT = (
    "You are verifying candidate director names that were scraped from company "
    "websites for regulatory/compliance research. For each candidate, decide "
    "whether the given context genuinely identifies them as a current director, "
    "board member, or board chair of the company. Do not count CEOs, CFOs, COOs, "
    "company secretaries, founders, presidents, partners, advisors, auditors, or "
    "other senior officers unless the same context explicitly says they are also "
    "a director or board member. Also reject footer links, unrelated employees, "
    "journalists quoted in news snippets, and misparsed phrases. Use only the "
    "text you are given; never invent or assume facts that are not in the "
    "context. Be conservative: if the context is ambiguous or doesn't clearly "
    "support the claim, say so and lower the confidence rather than guessing."
)

VERIFY_TOOL = {
    "name": "record_verification",
    "description": (
        "Record a verification decision for every candidate given in the prompt. "
        "Return exactly one result per candidate, matched back to the input by index."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {
                            "type": "integer",
                            "description": "The candidate's index from the input list, 0-based.",
                        },
                        "is_director": {
                            "type": "boolean",
                            "description": (
                                "True only if the context clearly supports this person being "
                                "a current director, board member, or board chair of the company."
                            ),
                        },
                        "name": {
                            "type": "string",
                            "description": "The person's full name, corrected for typos/casing if needed.",
                        },
                        "designation": {
                            "type": "string",
                            "description": "The person's board designation/title, corrected if needed.",
                        },
                        "confidence": {
                            "type": "integer",
                            "description": "0-100 confidence that this is a real, current director.",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "One short sentence citing the specific evidence in the context.",
                        },
                    },
                    "required": ["index", "is_director", "confidence", "reasoning"],
                },
            }
        },
        "required": ["results"],
    },
}


class AIAssistedVerifier:
    """
    Batched, LLM-backed verification of low-confidence director candidates.

    Design goals vs. the previous implementation:

    - Real model, not a placeholder webhook. Talks to Anthropic's Messages API
      using a tool-call (structured output), so responses are always
      well-formed JSON instead of free text that has to be hopefully parsed.
    - Batched. All of a company's low-confidence candidates are sent in ONE
      request (chunked at AI_VERIFICATION_BATCH_SIZE) instead of one HTTP
      round trip per candidate -- this is both faster and cheaper.
    - Cached to disk. The same (name, designation, context) is never
      re-verified twice, so --resume runs and re-runs after a crash don't
      re-spend tokens on candidates already judged in a previous run.
    - Never blocks the pipeline. Candidates already at/above the confidence
      threshold skip the LLM entirely (no spend on the easy cases), and any
      API failure (missing key, network error, rate limit, malformed
      response) degrades gracefully back to the heuristic-only score instead
      of raising.
    """

    def __init__(self, client=None, cache=None):

        self.enabled = Config.AI_VERIFICATION_ENABLED
        self.api_key = Config.AI_VERIFICATION_API_KEY
        self.model = Config.AI_VERIFICATION_MODEL
        self.threshold = Config.AI_VERIFICATION_THRESHOLD
        self.batch_size = max(1, Config.AI_VERIFICATION_BATCH_SIZE)
        self.max_retries = max(0, Config.AI_VERIFICATION_MAX_RETRIES)
        self.timeout = Config.AI_VERIFICATION_TIMEOUT

        self.cache = cache or VerificationCache()
        self._client = client
        self._warned_missing_sdk = False

    def _get_client(self):

        if self._client is not None:
            return self._client

        if not self.api_key:
            logger.warning(
                "AI verification is enabled but no ANTHROPIC_API_KEY is set. "
                "Falling back to heuristic confidence scores only."
            )
            return None

        try:
            from anthropic import Anthropic
        except ImportError:

            if not self._warned_missing_sdk:
                logger.warning(
                    "AI verification is enabled but the 'anthropic' package is "
                    "not installed. Run: pip install anthropic. Falling back to "
                    "heuristic confidence scores only."
                )
                self._warned_missing_sdk = True

            return None

        self._client = Anthropic(api_key=self.api_key)

        return self._client

    def verify(self, candidates: list) -> list:
        """
        Verify a company's full candidate list in place, batching API calls
        and skipping candidates that are already confident or already cached.
        Returns the same list, mutated with corrected fields/confidence.
        """

        if not self.enabled or not candidates:
            return candidates

        client = self._get_client()

        if client is None:
            return candidates

        to_verify = []
        cache_keys = {}

        for candidate in candidates:

            if candidate.confidence >= self.threshold:
                continue

            key = VerificationCache.key_for(
                candidate.name, candidate.designation, candidate.context
            )
            cache_keys[id(candidate)] = key

            cached = self.cache.get(key)

            if cached is not None:
                self._apply_result(candidate, cached)
            else:
                to_verify.append(candidate)

        for start in range(0, len(to_verify), self.batch_size):

            batch = to_verify[start:start + self.batch_size]
            results = self._verify_batch(client, batch)

            for offset, candidate in enumerate(batch):

                result = results.get(offset)

                if result is None:
                    continue

                self._apply_result(candidate, result)
                self.cache.put(cache_keys[id(candidate)], result)

        self.cache.flush()

        return candidates

    def _verify_batch(self, client, batch: list) -> dict:

        if not batch:
            return {}

        prompt = self._build_prompt(batch)

        for attempt in range(self.max_retries + 1):

            try:
                response = client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    system=SYSTEM_PROMPT,
                    tools=[VERIFY_TOOL],
                    tool_choice={"type": "tool", "name": "record_verification"},
                    messages=[{"role": "user", "content": prompt}],
                    timeout=self.timeout,
                )

                return self._parse_response(response, len(batch))

            except Exception as exc:

                logger.warning(
                    "AI verification request failed (attempt %s/%s, batch size %s): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    len(batch),
                    exc,
                )

                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)

        logger.warning(
            "AI verification exhausted retries for a batch of %s candidates; "
            "keeping heuristic scores for this batch.",
            len(batch),
        )

        return {}

    def _build_prompt(self, batch: list) -> str:

        lines = [
            "Verify each of the following director candidates. Return false for "
            "CEO/CFO/COO/company secretary/founder/advisor/officer titles unless "
            "the context explicitly also identifies the person as a director or "
            "board member.\n"
        ]

        for index, candidate in enumerate(batch):
            lines.append(
                f"[{index}] Name: {candidate.name}\n"
                f"    Claimed designation: {candidate.designation}\n"
                f"    Source page: {candidate.source}\n"
                f"    Context: \"{(candidate.context or '').strip()[:600]}\"\n"
            )

        return "\n".join(lines)

    def _parse_response(self, response, expected_count: int) -> dict:

        results = {}

        for block in getattr(response, "content", []):

            if getattr(block, "type", None) != "tool_use":
                continue

            items = (block.input or {}).get("results", [])

            for item in items:

                index = item.get("index")

                if not isinstance(index, int) or not (0 <= index < expected_count):
                    continue

                results[index] = {
                    "is_director": bool(item.get("is_director", False)),
                    "name": item.get("name"),
                    "designation": item.get("designation"),
                    "confidence": self._safe_confidence(item.get("confidence")),
                    "reasoning": item.get("reasoning", ""),
                }

        return results

    @staticmethod
    def _safe_confidence(value) -> float:

        try:
            return max(0.0, min(100.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    def _apply_result(self, candidate, result: dict):

        candidate.ai_reasoning = result.get("reasoning", "")

        if not result.get("is_director", False):
            candidate.confidence = min(candidate.confidence, 40)
            candidate.ai_verified = False
            return

        candidate.name = result.get("name") or candidate.name
        candidate.designation = result.get("designation") or candidate.designation
        candidate.confidence = max(
            candidate.confidence,
            result.get("confidence", candidate.confidence),
        )
        candidate.ai_verified = True
