import tempfile
from pathlib import Path

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


def _make_verifier(client, batch_size=10, threshold=75, tmp_path=None):
    cache_file = Path(tmp_path) / "cache.json" if tmp_path else Path(tempfile.mktemp())
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


def test_candidates_are_batched_not_sent_one_at_a_time(tmp_path):
    client = FakeClient()
    verifier = _make_verifier(client, batch_size=10, tmp_path=tmp_path)

    candidates = _low_confidence_candidates(25)
    verifier.verify(candidates)

    assert client.messages.calls == 3
    assert all(c.ai_verified is True for c in candidates)


def test_high_confidence_candidates_skip_the_api(tmp_path):
    client = FakeClient()
    verifier = _make_verifier(client, tmp_path=tmp_path)

    candidates = _low_confidence_candidates(2)
    candidates[0].confidence = 95  # already confident, should not be sent

    verifier.verify(candidates)

    assert client.messages.batch_sizes == [1]
    assert candidates[0].ai_verified is None


def test_verified_results_are_cached_across_runs(tmp_path):
    client = FakeClient()
    verifier = _make_verifier(client, tmp_path=tmp_path)

    candidates = _low_confidence_candidates(5)
    verifier.verify(candidates)
    assert client.messages.calls == 1

    # A second verifier sharing the same cache file should not re-call the API.
    cache2 = VerificationCache(cache_file=Path(tmp_path) / "cache.json")
    verifier2 = AIAssistedVerifier(client=client, cache=cache2)
    verifier2.threshold = 75
    verifier2.verify(_low_confidence_candidates(5))

    assert client.messages.calls == 1


def test_failed_requests_fall_back_to_heuristic_score_without_crashing(tmp_path):
    def always_fail(n):
        raise RuntimeError("simulated network failure")

    client = FakeClient(responder=always_fail)
    verifier = _make_verifier(client, tmp_path=tmp_path)
    verifier.max_retries = 1

    candidates = _low_confidence_candidates(3)
    original_confidence = [c.confidence for c in candidates]

    result = verifier.verify(candidates)

    assert result is candidates
    assert [c.confidence for c in candidates] == original_confidence
    assert all(c.ai_verified is None for c in candidates)


def test_disabled_verifier_is_a_no_op(tmp_path):
    client = FakeClient()
    verifier = _make_verifier(client, tmp_path=tmp_path)
    verifier.enabled = False

    candidates = _low_confidence_candidates(3)
    verifier.verify(candidates)

    assert client.messages.calls == 0
