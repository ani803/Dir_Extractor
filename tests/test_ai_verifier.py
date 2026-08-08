from pathlib import Path
from uuid import uuid4

from models import Candidate
from verifier.ai_verifier import AIAssistedVerifier
from verifier.llm_cache import VerificationCache
from config.config import Config


class FakeToolBlock:
    def __init__(self, input):
        self.type = "tool_use"
        self.input = input


class FakeResponse:
    def __init__(self, results):
        self.content = [FakeToolBlock({"results": results})]


class FakeMessages:
    def __init__(self, responder=None):
        self.calls = 0
        self.batch_sizes = []
        self._responder = responder

    def create(self, **kwargs):
        self.calls += 1
        prompt = kwargs["messages"][0]["content"]
        n = prompt.count("] Name:")
        self.batch_sizes.append(n)

        if self._responder:
            return self._responder(n)

        results = [
            {
                "index": i,
                "is_director": True,
                "name": None,
                "designation": None,
                "confidence": 90,
                "reasoning": "context supports it",
            }
            for i in range(n)
        ]
        return FakeResponse(results)


class FakeClient:
    def __init__(self, responder=None):
        self.messages = FakeMessages(responder)


def _make_verifier(client, batch_size=10, threshold=75, cache_dir=None):
    cache_file = (
        Path(cache_dir) / "cache.json"
        if cache_dir
        else Path(f"ai_cache_{uuid4().hex}.json")
    )
    cache = VerificationCache(cache_file=cache_file)

    Config.AI_VERIFICATION_ENABLED = True
    Config.AI_VERIFICATION_API_KEY = "fake"

    verifier = AIAssistedVerifier(client=client, cache=cache)
    verifier.threshold = threshold
    verifier.batch_size = batch_size
    return verifier


def _low_confidence_candidates(n):
    return [
        Candidate(
            name=f"Person {i}",
            designation="Director",
            context="He serves as Director of the company.",
            confidence=30,
        )
        for i in range(n)
    ]


def test_candidates_are_batched_not_sent_one_at_a_time():
    client = FakeClient()
    verifier = _make_verifier(client, batch_size=10)

    candidates = _low_confidence_candidates(25)
    try:
        verifier.verify(candidates)

        assert client.messages.calls == 3
        assert all(c.ai_verified is True for c in candidates)
    finally:
        verifier.cache.cache_file.unlink(missing_ok=True)


def test_high_confidence_candidates_skip_the_api():
    client = FakeClient()
    verifier = _make_verifier(client)

    candidates = _low_confidence_candidates(2)
    candidates[0].confidence = 95  # already confident, should not be sent

    try:
        verifier.verify(candidates)

        assert client.messages.batch_sizes == [1]
        assert candidates[0].ai_verified is None
    finally:
        verifier.cache.cache_file.unlink(missing_ok=True)


def test_verified_results_are_cached_across_runs():
    client = FakeClient()
    cache_dir = Path(f"ai_cache_dir_{uuid4().hex}")
    verifier = _make_verifier(client, cache_dir=cache_dir)

    try:
        candidates = _low_confidence_candidates(5)
        verifier.verify(candidates)
        assert client.messages.calls == 1

        # A second verifier sharing the same cache file should not re-call the API.
        cache2 = VerificationCache(cache_file=cache_dir / "cache.json")
        verifier2 = AIAssistedVerifier(client=client, cache=cache2)
        verifier2.threshold = 75
        verifier2.verify(_low_confidence_candidates(5))

        assert client.messages.calls == 1
    finally:
        verifier.cache.cache_file.unlink(missing_ok=True)
        cache_dir.rmdir()


def test_failed_requests_fall_back_to_heuristic_score_without_crashing():
    def always_fail(n):
        raise RuntimeError("simulated network failure")

    client = FakeClient(responder=always_fail)
    verifier = _make_verifier(client)
    verifier.max_retries = 1

    candidates = _low_confidence_candidates(3)
    original_confidence = [c.confidence for c in candidates]

    try:
        result = verifier.verify(candidates)

        assert result is candidates
        assert [c.confidence for c in candidates] == original_confidence
        assert all(c.ai_verified is None for c in candidates)
    finally:
        verifier.cache.cache_file.unlink(missing_ok=True)


def test_disabled_verifier_is_a_no_op():
    client = FakeClient()
    verifier = _make_verifier(client)
    verifier.enabled = False

    candidates = _low_confidence_candidates(3)
    try:
        verifier.verify(candidates)

        assert client.messages.calls == 0
    finally:
        verifier.cache.cache_file.unlink(missing_ok=True)
