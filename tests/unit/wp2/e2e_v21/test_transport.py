"""Mission-12B v2.1 - TRANSPORT_V21 unit tests (T1): zero API.

Frozen policy assertions:
- exactly 4 total HTTP attempts (attempt 1 immediate; 5/20/60 backoffs)
- retryable: 429/408/5xx/timeout/connection
- non-retryable: 400/401/403/404/auth/config -> fail immediately
- HOLD check immediately before every HTTP attempt -> 0 network on HOLD
- byte-identical request body across retries
- no fifth attempt
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark.wp2.e2e_v21.transport import (
    HOLD_ACTIVE,
    GenerationFail,
    NonRetryableError,
    V21HttpClient,
)


def _ok(status: int = 200) -> tuple[int, str]:
    payload = {"choices": [{"message": {"content": "hi"},
                            "finish_reason": "stop"}],
               "usage": {"prompt_tokens": 5, "completion_tokens": 2, "cost": 0.001},
               "id": "req-1"}
    return status, json.dumps(payload)


def _make_client(tmp_path: Path, sequence: list[tuple[int, str]]) -> tuple[V21HttpClient, list[bytes]]:
    hold = tmp_path / "HOLD"
    seen: list[bytes] = []

    def fake_post(body: bytes, headers: dict[str, str]) -> tuple[int, str]:
        seen.append(bytes(body))
        idx = len(seen) - 1
        return sequence[min(idx, len(sequence) - 1)]

    client = V21HttpClient(hold_file=hold, raw_post=fake_post,
                           sleep=lambda _s: None)
    return client, seen


def test_429_429_success_exactly_three_attempts(tmp_path: Path) -> None:
    client, seen = _make_client(tmp_path, [(429, ""), (429, ""), _ok()])
    msgs = [{"role": "user", "content": "x"}]
    result = client.generate_messages(msgs)
    assert result.text == "hi"
    assert len(seen) == 3


def test_four_retryable_failures_exactly_four_then_fail(tmp_path: Path) -> None:
    client, seen = _make_client(tmp_path, [(429, ""), (408, ""), (500, ""), (503, "")])
    with pytest.raises(GenerationFail) as exc:
        client.generate_messages([{"role": "user", "content": "x"}])
    assert "EXHAUSTED_RETRYABLE" in str(exc.value)
    assert len(seen) == 4


def test_hold_before_attempt1_zero_http_calls(tmp_path: Path) -> None:
    hold = tmp_path / "HOLD"
    hold.write_text("", encoding="utf-8")
    seen: list[bytes] = []

    def fake_post(body: bytes, headers: dict[str, str]) -> tuple[int, str]:
        seen.append(bytes(body))
        return _ok()

    client = V21HttpClient(hold_file=hold, raw_post=fake_post, sleep=lambda _s: None)
    with pytest.raises(HOLD_ACTIVE):
        client.generate_messages([{"role": "user", "content": "x"}])
    assert len(seen) == 0


def test_hold_appears_before_retry_blocks_retry_network(tmp_path: Path) -> None:
    hold = tmp_path / "HOLD"
    seen: list[bytes] = []

    def fake_post(body: bytes, headers: dict[str, str]) -> tuple[int, str]:
        seen.append(bytes(body))
        if len(seen) == 1:
            hold.write_text("", encoding="utf-8")
            return 429, ""
        return _ok()

    client = V21HttpClient(hold_file=hold, raw_post=fake_post, sleep=lambda _s: None)
    with pytest.raises(HOLD_ACTIVE):
        client.generate_messages([{"role": "user", "content": "x"}])
    assert len(seen) == 1


def test_http400_exactly_one_attempt(tmp_path: Path) -> None:
    client, seen = _make_client(tmp_path, [(400, '{"error":"bad request"}')])
    with pytest.raises(NonRetryableError) as exc:
        client.generate_messages([{"role": "user", "content": "x"}])
    assert "HTTP 400" in str(exc.value)
    assert len(seen) == 1


def test_http401_403_404_non_retryable(tmp_path: Path) -> None:
    for code in (401, 403, 404):
        client, seen = _make_client(tmp_path, [(code, "")])
        with pytest.raises(NonRetryableError):
            client.generate_messages([{"role": "user", "content": "x"}])
        assert len(seen) == 1, f"code {code} should fail after exactly 1 attempt"


def test_http408_retryable(tmp_path: Path) -> None:
    client, seen = _make_client(tmp_path, [(408, ""), _ok()])
    result = client.generate_messages([{"role": "user", "content": "x"}])
    assert result.text == "hi"
    assert len(seen) == 2


def test_http5xx_retryable(tmp_path: Path) -> None:
    client, seen = _make_client(tmp_path, [(502, ""), (504, ""), _ok()])
    result = client.generate_messages([{"role": "user", "content": "x"}])
    assert result.text == "hi"
    assert len(seen) == 3


def test_request_body_bytes_identical_across_retries(tmp_path: Path) -> None:
    client, seen = _make_client(tmp_path, [(429, ""), (429, ""), _ok()])
    client.generate_messages([{"role": "user", "content": "hello world"}])
    assert len(seen) == 3
    assert seen[0] == seen[1] == seen[2]


def test_no_fifth_attempt_on_four_retryable(tmp_path: Path) -> None:
    client, seen = _make_client(tmp_path, [(429, ""), (429, ""), (429, ""), (429, "")])
    with pytest.raises(GenerationFail):
        client.generate_messages([{"role": "user", "content": "x"}])
    assert len(seen) == 4


def test_timeout_exception_retryable(tmp_path: Path) -> None:
    hold = tmp_path / "HOLD"
    seen: list[bytes] = []

    def fake_post(body: bytes, headers: dict[str, str]) -> tuple[int, str]:
        seen.append(bytes(body))
        if len(seen) < 2:
            raise TimeoutError("timed out")
        return _ok()

    client = V21HttpClient(hold_file=hold, raw_post=fake_post, sleep=lambda _s: None)
    result = client.generate_messages([{"role": "user", "content": "x"}])
    assert result.text == "hi"
    assert len(seen) == 2


def test_pacing_between_logical_calls(tmp_path: Path) -> None:
    hold = tmp_path / "HOLD"
    sleeps: list[float] = []
    client = V21HttpClient(hold_file=hold, raw_post=lambda b, h: _ok(),
                           sleep=lambda s: sleeps.append(s))
    client.generate_messages([{"role": "user", "content": "a"}])
    client.generate_messages([{"role": "user", "content": "b"}])
    assert len(sleeps) == 1
    assert 4.0 <= sleeps[0] <= 5.0
