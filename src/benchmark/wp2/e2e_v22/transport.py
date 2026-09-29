"""WP-2 E2E v2.2 transport: observable, HOLD-safe, never produces a scientific outcome.

Contract (enforced in code, covered by tests/unit/wp2/e2e_v22/test_transport_v22.py):

1. One logical request = at most MAX_ATTEMPTS HTTP attempts with a byte-identical body.
2. Wait before attempt k = max(BASELINE_BACKOFFS_S[k-1], Retry-After of the previous
   response), Retry-After capped at RETRY_AFTER_CAP_S.
3. The HOLD files are checked immediately before EVERY network I/O (after any sleep),
   and every few seconds during a sleep.
4. Every attempt (success or failure) is appended to an fsync'ed JSONL log BEFORE the
   next attempt starts: status, safe rate-limit headers, Retry-After, OpenRouter
   error metadata, served provider, timing. No Authorization header, no API key.
5. Retryable exhaustion raises ``ProviderUnavailable``; any other non-2xx raises
   ``RequestRejected``; a HOLD raises ``HoldActiveV22``. None of these subclasses the
   v2.1 exceptions, so ``run_episode_v21`` does NOT catch them and never writes a
   terminal GENERATION_FAIL record. The episode stays pending and is resumed later
   with the same frozen request (the initial response, if any, is already cached).
"""
from __future__ import annotations

import datetime as _dt
import email.utils
import hashlib
import http.client
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmark.wp2.e2e.llm_client import CallResult
from benchmark.wp2.e2e.spec import MAX_TOKENS, MODEL, TEMPERATURE

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
PROVIDER = "deepinfra/turbo"
ROUTE = f"openrouter:{MODEL}@{PROVIDER}"
FROZEN_PROMPT_USD_PER_1M = 0.30
FROZEN_COMPLETION_USD_PER_1M = 1.00

MAX_ATTEMPTS = 4
BASELINE_BACKOFFS_S = (0.0, 5.0, 20.0, 60.0)
RETRY_AFTER_CAP_S = 300.0
MIN_PACING_S = 5.0
HOLD_POLL_S = 5.0
HTTP_TIMEOUT_S = 180

RETRYABLE_STATUS = frozenset({408, 409, 425, 429})
SAFE_HEADERS = ("retry-after", "x-ratelimit-limit", "x-ratelimit-remaining",
                "x-ratelimit-reset", "x-ratelimit-limit-requests",
                "x-ratelimit-remaining-requests", "x-ratelimit-reset-requests")
_SECRET_RE = re.compile(r"(sk-or-[A-Za-z0-9_\-]{6,}|Bearer\s+[A-Za-z0-9_\-\.]{6,})")


class HoldActiveV22(RuntimeError):  # noqa: N818
    """A HOLD file exists: no network I/O is allowed."""


class ProviderUnavailable(RuntimeError):  # noqa: N818
    """All attempts of one logical request failed on retryable conditions."""

    def __init__(self, message: str, attempts: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.attempts = attempts


class RequestRejected(RuntimeError):  # noqa: N818
    """Deterministic rejection (auth, credit, bad request, missing key): needs a human."""

    def __init__(self, message: str, attempts: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.attempts = attempts or []


@dataclass
class RawResponse:
    status: int
    text: str
    headers: dict[str, str]


def scrub(text: str, limit: int = 300) -> str:
    return _SECRET_RE.sub("<redacted>", (text or ""))[:limit]


def parse_retry_after(value: str | None, now: float | None = None) -> float | None:
    """Seconds from a Retry-After header (delta-seconds or HTTP-date)."""
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    try:
        return max(0.0, float(v))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(v)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=_dt.UTC)
    ref = now if now is not None else time.time()
    return max(0.0, when.timestamp() - ref)


def parse_error_meta(text: str) -> dict[str, Any]:
    """Safe subset of an OpenRouter error body."""
    out: dict[str, Any] = {}
    try:
        payload = json.loads(text)
    except (ValueError, TypeError):
        return {"unparsed_body": scrub(text, 200)} if text else {}
    if not isinstance(payload, dict):
        return {}
    err = payload.get("error")
    if isinstance(err, dict):
        out["error_code"] = err.get("code")
        out["error_message"] = scrub(str(err.get("message", "")))
        meta = err.get("metadata")
        if isinstance(meta, dict):
            for key in ("provider_name", "provider_code", "error_type", "reason"):
                if key in meta:
                    out[f"meta_{key}"] = scrub(str(meta[key]), 120)
            if "raw" in meta:
                out["meta_raw"] = scrub(str(meta["raw"]), 300)
    return out


def safe_headers(headers: dict[str, str]) -> dict[str, str]:
    low = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    return {k: low[k] for k in SAFE_HEADERS if k in low}


class AttemptLog:
    """Append-only JSONL, fsync'ed per record."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if "Bearer " in line or "sk-or-" in line:
            raise RuntimeError("refusing to persist a secret-looking attempt record")
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _is_transport_exception(exc: BaseException) -> bool:
    return isinstance(exc, (urllib.error.URLError, TimeoutError, ConnectionError,
                            http.client.HTTPException, OSError))


class V22HttpClient:
    """Drop-in client for ``run_episode_v21`` (``generate_messages``)."""

    def __init__(self, hold_files: Iterable[Path | str], attempt_log: AttemptLog,
                 raw_post: Callable[[bytes, dict[str, str]], RawResponse] | None = None,
                 clock: Callable[[], float] = time.monotonic,
                 wall: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep,
                 model: str = MODEL, provider: str = PROVIDER,
                 max_tokens: int = MAX_TOKENS, temperature: float = TEMPERATURE,
                 api_key_env: str = "OPENROUTER_API_KEY") -> None:
        self._holds = [Path(p) for p in hold_files]
        self._log = attempt_log
        self._raw_post = raw_post or self._default_raw_post
        self._clock = clock
        self._wall = wall
        self._sleep = sleep
        self._model = model
        self._provider = provider
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._api_key_env = api_key_env
        self._last_end: float | None = None
        self.context: dict[str, str] = {}
        self.network_attempts = 0

    # ------------------------------------------------------------------ context
    def set_context(self, **ctx: str) -> None:
        self.context = dict(ctx)

    # ------------------------------------------------------------------ HOLD
    def check_hold(self) -> None:
        for h in self._holds:
            if h.exists():
                raise HoldActiveV22(f"HOLD present: {h}")

    def _sleep_with_hold(self, seconds: float) -> float:
        slept = 0.0
        while slept < seconds:
            self.check_hold()
            step = min(HOLD_POLL_S, seconds - slept)
            self._sleep(step)
            slept += step
        return slept

    # ------------------------------------------------------------------ HTTP
    def _api_key(self) -> str:
        key = os.environ.get(self._api_key_env, "").strip().strip('"').strip("'").strip()
        if not key:
            raise RequestRejected(f"NO_API_KEY: {self._api_key_env} is empty")
        return key

    def _default_raw_post(self, body: bytes, headers: dict[str, str]) -> RawResponse:
        req = urllib.request.Request(BASE_URL, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
                return RawResponse(int(resp.status), resp.read().decode("utf-8", "replace"),
                                   dict(resp.headers.items()))
        except urllib.error.HTTPError as exc:
            text = ""
            try:
                text = exc.read().decode("utf-8", "replace")
            except Exception:
                text = ""
            hdrs = dict(exc.headers.items()) if exc.headers is not None else {}
            return RawResponse(int(exc.code), text, hdrs)

    def build_body(self, messages: list[dict[str, Any]]) -> bytes:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "stream": False,
            "provider": {"order": [self._provider], "allow_fallbacks": False,
                         "require_parameters": True},
        }
        return json.dumps(body, sort_keys=True).encode("utf-8")

    def _pace(self) -> None:
        if self._last_end is None:
            return
        gap = self._clock() - self._last_end
        if gap < MIN_PACING_S:
            self._sleep_with_hold(MIN_PACING_S - gap)

    # ------------------------------------------------------------------ main
    def generate_messages(self, messages: list[dict[str, Any]]) -> CallResult:
        self.check_hold()
        self._pace()
        key = self._api_key()
        body = self.build_body(messages)
        body_sha = hashlib.sha256(body).hexdigest()
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
        kind = "repair" if len(messages) >= 4 else "initial"
        attempts: list[dict[str, Any]] = []
        prev_retry_after: float | None = None
        t_request = self._clock()

        for attempt in range(1, MAX_ATTEMPTS + 1):
            wait = 0.0
            if attempt > 1:
                wait = BASELINE_BACKOFFS_S[attempt - 1]
                if prev_retry_after is not None:
                    wait = max(wait, min(prev_retry_after, RETRY_AFTER_CAP_S))
                self._sleep_with_hold(wait)
            self.check_hold()  # immediately before network I/O
            rec: dict[str, Any] = {
                "utc": _utc(), "attempt": attempt, "kind": kind,
                "request_body_sha256": body_sha, "slept_before_s": round(wait, 3),
                "model": self._model, "provider_pinned": self._provider, **self.context,
            }
            t0 = self._clock()
            self.network_attempts += 1
            try:
                resp = self._raw_post(body, headers)
            except Exception as exc:
                if not _is_transport_exception(exc):
                    raise
                rec.update({"latency_s": round(self._clock() - t0, 3), "http_status": None,
                            "class": "RETRYABLE", "reason": scrub(f"{type(exc).__name__}: {exc}")})
                self._log.append(rec)
                attempts.append(rec)
                prev_retry_after = None
                continue
            rec["latency_s"] = round(self._clock() - t0, 3)
            rec["http_status"] = resp.status
            rec["headers"] = safe_headers(resp.headers)
            prev_retry_after = parse_retry_after(rec["headers"].get("retry-after"), self._wall())
            rec["retry_after_s"] = prev_retry_after

            if 200 <= resp.status < 300:
                result, why = self._parse_success(resp.text, t_request)
                if result is not None:
                    rec.update({"class": "SUCCESS", "served_provider": why})
                    self._log.append(rec)
                    self._last_end = self._clock()
                    return result
                rec.update({"class": "RETRYABLE", "reason": why})
                self._log.append(rec)
                attempts.append(rec)
                continue

            rec.update(parse_error_meta(resp.text))
            if resp.status in RETRYABLE_STATUS or 500 <= resp.status <= 599:
                rec["class"] = "RETRYABLE"
                self._log.append(rec)
                attempts.append(rec)
                continue
            rec["class"] = "REJECTED"
            self._log.append(rec)
            attempts.append(rec)
            self._last_end = self._clock()
            raise RequestRejected(f"HTTP {resp.status}: {rec.get('error_message', '')}", attempts)

        self._last_end = self._clock()
        statuses = [a.get("http_status") for a in attempts]
        raise ProviderUnavailable(
            f"{MAX_ATTEMPTS} attempts exhausted; statuses={statuses}", attempts)

    def _parse_success(self, text: str, t_request: float) -> tuple[CallResult | None, str]:
        try:
            payload = json.loads(text)
        except ValueError:
            return None, "SUCCESS_STATUS_UNPARSEABLE_BODY"
        if not isinstance(payload, dict) or payload.get("error"):
            return None, "PROVIDER_ERROR_IN_BODY"
        choices = payload.get("choices") or []
        if not choices:
            return None, "PROVIDER_EMPTY_CHOICES"
        choice = choices[0]
        message = choice.get("message") or {}
        finish = choice.get("finish_reason") or "stop"
        content = message.get("content") or ""
        if finish == "error" or (not content and finish not in ("stop", "length")):
            return None, f"PROVIDER_FINISH_{finish}"
        usage = payload.get("usage") or {}
        pt = int(usage.get("prompt_tokens", 0) or 0)
        ct = int(usage.get("completion_tokens", 0) or 0)
        cost = usage.get("cost")
        if cost is None:
            cost = pt / 1e6 * FROZEN_PROMPT_USD_PER_1M + ct / 1e6 * FROZEN_COMPLETION_USD_PER_1M
        served = str(payload.get("provider", ""))
        return CallResult(text=content, finish_reason=finish, prompt_tokens=pt,
                          completion_tokens=ct, cost_usd=float(cost),
                          route=f"openrouter:{self._model}@{self._provider}",
                          provider=self._provider,
                          latency_s=round(self._clock() - t_request, 3),
                          request_id=str(payload.get("id", ""))), served

    def generate(self, system: str, user: str) -> CallResult:
        return self.generate_messages([{"role": "system", "content": system},
                                       {"role": "user", "content": user}])
