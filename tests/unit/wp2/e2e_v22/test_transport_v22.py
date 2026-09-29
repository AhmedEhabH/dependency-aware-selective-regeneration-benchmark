"""v2.2 transport: observable retries, Retry-After, HOLD before I/O, no scientific outcome."""
from __future__ import annotations

import json
import urllib.error
from pathlib import Path

import pytest

from benchmark.wp2.e2e_v21 import transport as t21
from benchmark.wp2.e2e_v22.transport import (
    MAX_ATTEMPTS,
    RETRY_AFTER_CAP_S,
    AttemptLog,
    HoldActiveV22,
    ProviderUnavailable,
    RawResponse,
    RequestRejected,
    V22HttpClient,
    parse_retry_after,
)

KEY = "sk-or-TESTKEY1234567890"
MSGS = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]


def ok_body(provider: str = "DeepInfra") -> str:
    return json.dumps({"id": "gen-1", "provider": provider,
                       "choices": [{"message": {"content": "FILE: a.py"}, "finish_reason": "stop"}],
                       "usage": {"prompt_tokens": 10, "completion_tokens": 3, "cost": 0.0001}})


def err_body(code: int, provider_code: str = "rate_limited") -> str:
    return json.dumps({"error": {"code": code, "message": f"err {code} {KEY}",
                                 "metadata": {"provider_name": "DeepInfra",
                                              "provider_code": provider_code,
                                              "error_type": "rate_limit"}}})


class Harness:
    def __init__(self, tmp: Path, responses: list, hold: Path | None = None,
                 hold_after_sleep: bool = False) -> None:
        self.responses = list(responses)
        self.bodies: list[bytes] = []
        self.sleeps: list[float] = []
        self.hold = hold or tmp / "HOLD"
        self.hold_after_sleep = hold_after_sleep
        self.log_path = tmp / "attempts.jsonl"
        self.t = 0.0
        self.client = V22HttpClient([self.hold], AttemptLog(self.log_path), raw_post=self.post,
                                    clock=self.clock, wall=lambda: 1_000_000.0,
                                    sleep=self.sleep)

    def clock(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.sleeps.append(s)
        self.t += s
        if self.hold_after_sleep:
            self.hold.write_text("x")

    def post(self, body: bytes, headers: dict) -> RawResponse:
        assert headers["Authorization"] == f"Bearer {KEY}"
        self.bodies.append(body)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def log(self) -> list[dict]:
        return [json.loads(x) for x in self.log_path.read_text().splitlines()] if self.log_path.exists() else []


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)


def test_success_logs_served_provider(tmp_path):
    h = Harness(tmp_path, [RawResponse(200, ok_body(), {"X-RateLimit-Remaining": "9"})])
    res = h.client.generate_messages(MSGS)
    assert res.text == "FILE: a.py" and res.cost_usd == 0.0001
    rec = h.log()[0]
    assert rec["class"] == "SUCCESS" and rec["served_provider"] == "DeepInfra"
    assert rec["headers"]["x-ratelimit-remaining"] == "9"


def test_retry_after_honoured_and_headers_preserved(tmp_path):
    h = Harness(tmp_path, [
        RawResponse(429, err_body(429), {"Retry-After": "180", "X-RateLimit-Limit": "20",
                                         "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "123"}),
        RawResponse(200, ok_body(), {})])
    h.client.generate_messages(MSGS)
    assert sum(h.sleeps) == pytest.approx(180.0)
    first = h.log()[0]
    assert first["http_status"] == 429 and first["retry_after_s"] == 180.0
    assert first["headers"]["x-ratelimit-limit"] == "20"
    assert first["meta_provider_code"] == "rate_limited"
    assert first["meta_error_type"] == "rate_limit"


def test_retry_after_is_capped(tmp_path):
    h = Harness(tmp_path, [RawResponse(429, err_body(429), {"Retry-After": "99999"}),
                           RawResponse(200, ok_body(), {})])
    h.client.generate_messages(MSGS)
    assert sum(h.sleeps) == pytest.approx(RETRY_AFTER_CAP_S)


def test_exhaustion_raises_provider_unavailable_after_exactly_four(tmp_path):
    h = Harness(tmp_path, [RawResponse(503, err_body(503), {})] * 6)
    with pytest.raises(ProviderUnavailable) as ei:
        h.client.generate_messages(MSGS)
    assert len(h.bodies) == MAX_ATTEMPTS == 4
    assert len(set(h.bodies)) == 1  # byte-identical body
    assert len(ei.value.attempts) == 4
    assert sum(h.sleeps) == pytest.approx(5 + 20 + 60)


def test_hold_created_during_backoff_blocks_next_network_io(tmp_path):
    h = Harness(tmp_path, [RawResponse(429, err_body(429), {}), RawResponse(200, ok_body(), {})],
                hold_after_sleep=True)
    with pytest.raises(HoldActiveV22):
        h.client.generate_messages(MSGS)
    assert len(h.bodies) == 1


def test_hold_before_first_attempt_means_zero_network(tmp_path):
    (tmp_path / "HOLD").write_text("x")
    h = Harness(tmp_path, [RawResponse(200, ok_body(), {})])
    with pytest.raises(HoldActiveV22):
        h.client.generate_messages(MSGS)
    assert h.bodies == []


@pytest.mark.parametrize("status", [400, 401, 402, 403, 404, 413, 422])
def test_non_retryable_is_rejected_after_one_attempt(tmp_path, status):
    h = Harness(tmp_path, [RawResponse(status, err_body(status), {})] * 2)
    with pytest.raises(RequestRejected):
        h.client.generate_messages(MSGS)
    assert len(h.bodies) == 1


def test_empty_choices_is_retryable(tmp_path):
    empty = json.dumps({"choices": []})
    h = Harness(tmp_path, [RawResponse(200, empty, {}), RawResponse(200, ok_body(), {})])
    assert h.client.generate_messages(MSGS).text == "FILE: a.py"
    assert [r["class"] for r in h.log()] == ["RETRYABLE", "SUCCESS"]


def test_transport_exception_retryable_but_programming_error_raises(tmp_path):
    h = Harness(tmp_path, [urllib.error.URLError("reset"), RawResponse(200, ok_body(), {})])
    assert h.client.generate_messages(MSGS).text == "FILE: a.py"
    h2 = Harness(tmp_path / "b", [TypeError("bug")])
    with pytest.raises(TypeError):
        h2.client.generate_messages(MSGS)


def test_missing_key_rejected_with_zero_network(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    h = Harness(tmp_path, [RawResponse(200, ok_body(), {})])
    with pytest.raises(RequestRejected):
        h.client.generate_messages(MSGS)
    assert h.bodies == []


def test_secret_never_persisted(tmp_path):
    h = Harness(tmp_path, [RawResponse(429, err_body(429), {})] * 4)
    with pytest.raises(ProviderUnavailable):
        h.client.generate_messages(MSGS)
    text = h.log_path.read_text()
    assert KEY not in text and "Bearer" not in text


def test_attempt_log_written_before_next_attempt(tmp_path):
    seen: list[int] = []
    h = Harness(tmp_path, [RawResponse(429, err_body(429), {}), RawResponse(200, ok_body(), {})])
    orig = h.post

    def post(body, headers):
        seen.append(len(h.log()))
        return orig(body, headers)
    h.client._raw_post = post
    h.client.generate_messages(MSGS)
    assert seen == [0, 1]


def test_exceptions_are_not_caught_by_v21_episode_handler():
    v21 = (t21.HOLD_ACTIVE, t21.GenerationFail, t21.NonRetryableError)
    for exc in (HoldActiveV22("x"), ProviderUnavailable("x", []), RequestRejected("x")):
        assert not isinstance(exc, v21)


def test_parse_retry_after_http_date():
    assert parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT", now=1445412480.0 - 60) == pytest.approx(60)
    assert parse_retry_after("7") == 7.0
    assert parse_retry_after("garbage") is None
