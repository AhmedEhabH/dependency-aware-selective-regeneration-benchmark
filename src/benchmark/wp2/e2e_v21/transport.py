"""Mission-12B v2.1 - TRANSPORT_V21 gate (T1).

Frozen policy (Mission-12B section 2.3), outcome-blind, decided BEFORE any paid
generation:

- A logical provider request may make TOTAL_HTTP_ATTEMPTS = 4:
  attempt 1 immediately, retry 1 after 5 s, retry 2 after 20 s, retry 3 after 60 s.
- Every retry must use byte-identical HTTP request content/body and identical
  model parameters.
- Retryable: HTTP 429, HTTP 408, HTTP 5xx, timeout, connection/reset/temporary
  transport errors.
- Not retryable: authentication/account/credit/configuration errors and
  HTTP 400/401/403/404 or other deterministic bad-request/config errors.
- Logical-call pacing: minimum 5 seconds between completed provider logical calls.
- After all 4 HTTP attempts fail: return logical call failure (no extra attempts,
  no mutation of prompt/scope/model).
- The v21 HOLD file is checked immediately before EVERY HTTP attempt. If present:
  raise HOLD_ACTIVE before any network I/O.

This module forks/wraps the frozen client semantics for the v2.1 namespace; it
does not modify any historical v2 evidence or the frozen v2 client code.
"""
from __future__ import annotations

import contextlib
import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from benchmark.wp2.e2e.spec import MAX_TOKENS, MODEL, TEMPERATURE

FROZEN_PROMPT_USD_PER_1M = 0.30
FROZEN_COMPLETION_USD_PER_1M = 1.00
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
PROVIDER = "deepinfra/turbo"

TOTAL_HTTP_ATTEMPTS = 4
BACKOFFS_S = (0, 5, 20, 60)
MIN_PACING_S = 5.0

RETRYABLE_STATUS = {429, 408}
NON_RETRYABLE_STATUS = {400, 401, 403, 404}


class HOLD_ACTIVE(RuntimeError):  # noqa: N801, N818
    """Raised before network I/O when the v21 HOLD file is present."""


class GenerationFail(RuntimeError):  # noqa: N818
    """Raised after all TOTAL_HTTP_ATTEMPTS attempts fail on retryable errors."""


class NonRetryableError(RuntimeError):
    """Raised immediately on auth/config/bad-request class errors."""


@dataclass
class AttemptRecord:
    attempt: int
    backoff_s: float
    outcome: str  # SUCCESS | RETRYABLE | NON_RETRYABLE
    reason: str
    http_status: int | None = None


@dataclass
class TransportResult:
    ok: bool
    call: CallResult | None
    attempts: list[AttemptRecord] = field(default_factory=list)
    terminal_reason: str = ""


@dataclass
class CallResult:
    text: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    route: str
    provider: str
    latency_s: float
    request_id: str


def _classify_status(status: int) -> str:
    if status in RETRYABLE_STATUS or 500 <= status <= 599:
        return "RETRYABLE"
    if status in NON_RETRYABLE_STATUS:
        return "NON_RETRYABLE"
    return "UNKNOWN"


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    return bool(isinstance(exc, urllib.error.URLError))


def _is_non_retryable_exception(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    for token in ("auth", "account", "credit", "config", "401", "403",
                  "permission", "forbidden", "unauthorized"):
        if token in text:
            return True
    return False


class V21HttpClient:
    """Minimal byte-identical HTTP POST with the frozen TRANSPORT_V21 policy.

    ``raw_post`` is injectable for tests: ``raw_post(body_bytes, headers) ->
    (status, text)``; default uses urllib over the frozen OpenRouter route.
    """

    def __init__(self, hold_file: Path | str,
                 raw_post: Callable[[bytes, dict[str, str]], tuple[int, str]] | None = None,
                 clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep,
                 model: str = MODEL, max_tokens: int = MAX_TOKENS,
                 temperature: float = TEMPERATURE,
                 api_key_env: str = "OPENROUTER_API_KEY") -> None:
        self._hold_file = Path(hold_file)
        self._raw_post = raw_post or self._default_raw_post
        self._clock = clock
        self._sleep = sleep
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._api_key_env = api_key_env
        self._last_call_end: float | None = None

    # -- HOLD ---------------------------------------------------------------
    def check_hold(self) -> None:
        """Must be called immediately before every HTTP attempt."""
        if self._hold_file.exists():
            raise HOLD_ACTIVE(f"v21 HOLD present: {self._hold_file}")

    # -- pacing -------------------------------------------------------------
    def _pace(self) -> None:
        """Minimum MIN_PACING_S between completed provider logical calls."""
        if self._last_call_end is None:
            return
        elapsed = self._clock() - self._last_call_end
        if elapsed < MIN_PACING_S:
            self._sleep(MIN_PACING_S - elapsed)

    # -- default transport --------------------------------------------------
    def _api_key(self) -> str:
        key = os.environ.get(self._api_key_env, "")
        if not key or not key.strip():
            raise NonRetryableError(f"API key not found in {self._api_key_env}")
        return key.strip().strip('"').strip("'").strip()

    def _default_raw_post(self, body: bytes, headers: dict[str, str]) -> tuple[int, str]:
        req = urllib.request.Request(
            BASE_URL, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return int(resp.status), resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            text = ""
            with contextlib.suppress(Exception):
                text = exc.read().decode("utf-8", errors="replace")
            return int(exc.code), text
        except Exception as exc:
            if _is_non_retryable_exception(exc):
                raise NonRetryableError(f"{type(exc).__name__}: {exc}") from exc
            raise

    # -- core logical call ----------------------------------------------------
    def generate_messages(self, messages: list[dict[str, Any]]) -> CallResult:
        self.check_hold()
        self._pace()
        api_key = self._api_key()
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "stream": False,
            "provider": {"order": [PROVIDER], "allow_fallbacks": False,
                         "require_parameters": True},
        }
        body_bytes = json.dumps(body, sort_keys=True).encode("utf-8")
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {api_key}"}
        t0 = self._clock()
        attempts: list[AttemptRecord] = []
        last_status: int | None = None

        for attempt in range(1, TOTAL_HTTP_ATTEMPTS + 1):
            self.check_hold()
            backoff = BACKOFFS_S[attempt - 1]
            if attempt > 1 and backoff:
                self._sleep(backoff)
            try:
                status, text = self._raw_post(body_bytes, headers)
            except NonRetryableError as exc:
                attempts.append(AttemptRecord(attempt, backoff, "NON_RETRYABLE", str(exc)))
                raise NonRetryableError(
                    f"{exc}; attempts={len(attempts)}; terminal_reason=NON_RETRYABLE") from exc
            except Exception as exc:
                retryable = _is_retryable_exception(exc)
                outcome = "RETRYABLE" if retryable else "NON_RETRYABLE"
                reason = f"{type(exc).__name__}: {exc}"
                attempts.append(AttemptRecord(attempt, backoff, outcome, reason))
                if not retryable:
                    raise NonRetryableError(
                        f"{reason}; attempts={len(attempts)}; terminal_reason=NON_RETRYABLE") from exc
                if attempt == TOTAL_HTTP_ATTEMPTS:
                    self._last_call_end = self._clock()
                    raise GenerationFail(
                        f"after {TOTAL_HTTP_ATTEMPTS} attempts: {reason}; "
                        f"terminal_reason=EXHAUSTED_RETRYABLE") from exc
                continue

            last_status = status
            cls = _classify_status(status)
            if cls == "NON_RETRYABLE":
                attempts.append(AttemptRecord(attempt, backoff, "NON_RETRYABLE",
                                              f"HTTP {status}", status))
                self._last_call_end = self._clock()
                raise NonRetryableError(
                    f"HTTP {status}: {text[:200]!r}; attempts={len(attempts)}; "
                    f"terminal_reason=NON_RETRYABLE")
            if cls == "RETRYABLE":
                attempts.append(AttemptRecord(attempt, backoff, "RETRYABLE",
                                              f"HTTP {status}", status))
                if attempt == TOTAL_HTTP_ATTEMPTS:
                    self._last_call_end = self._clock()
                    raise GenerationFail(
                        f"after {TOTAL_HTTP_ATTEMPTS} attempts (last HTTP {status}); "
                        f"terminal_reason=EXHAUSTED_RETRYABLE")
                continue

            # success (2xx)
            try:
                payload = json.loads(text)
                choice = payload["choices"][0]
                message = choice["message"]
                content = message.get("content") or ""
                finish_reason = choice.get("finish_reason", "stop")
                usage = payload.get("usage", {})
                pt = int(usage.get("prompt_tokens", 0) or 0)
                ct = int(usage.get("completion_tokens", 0) or 0)
                cost = usage.get("cost")
                if cost is None:
                    cost = (pt / 1e6 * FROZEN_PROMPT_USD_PER_1M
                            + ct / 1e6 * FROZEN_COMPLETION_USD_PER_1M)
                result = CallResult(
                    text=content, finish_reason=finish_reason,
                    prompt_tokens=pt, completion_tokens=ct, cost_usd=float(cost),
                    route=f"openrouter:{self._model}@{PROVIDER}",
                    provider=PROVIDER, latency_s=round(self._clock() - t0, 3),
                    request_id=payload.get("id", ""))
            except Exception as exc:
                attempts.append(AttemptRecord(attempt, backoff, "NON_RETRYABLE",
                                              f"PARSE_ERROR: {type(exc).__name__}", status))
                self._last_call_end = self._clock()
                raise NonRetryableError(
                    f"response parse failure: {type(exc).__name__}: {exc}; "
                    f"attempts={len(attempts)}; terminal_reason=NON_RETRYABLE") from exc
            attempts.append(AttemptRecord(attempt, backoff, "SUCCESS", f"HTTP {status}", status))
            self._last_call_end = self._clock()
            return result

        raise GenerationFail(f"unreachable; last_status={last_status}; "
                             f"terminal_reason=EXHAUSTED_RETRYABLE")

    def generate(self, system: str, user: str) -> CallResult:
        return self.generate_messages([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])


class ReplayClientV21:
    """Deterministic zero-cost client for tests / zero-API controls.

    Mirrors the frozen ReplayClient keyed by sha256 of the whole messages list.
    """

    def __init__(self, responses: dict[str, str]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, str]] = []

    def generate_messages(self, messages: list[dict[str, Any]]) -> CallResult:
        import hashlib
        canonical = json.dumps(messages, sort_keys=True, ensure_ascii=False)
        sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.calls.append((sha, canonical))
        text = self._responses.get(sha, self._responses.get(canonical, ""))
        return CallResult(text=text, finish_reason="stop",
                          prompt_tokens=len(canonical) // 4,
                          completion_tokens=len(text) // 4,
                          cost_usd=0.0, route="replay", provider="replay",
                          latency_s=0.0, request_id=f"replay-{sha[:8]}")

    def generate(self, system: str, user: str) -> CallResult:
        return self.generate_messages([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
