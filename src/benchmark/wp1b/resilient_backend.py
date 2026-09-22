"""WP-1b MAIN run - resilient, accounting transport wrapper (harness only).

This module is HARNESS code for the paid WP-1b MAIN_297 / variance runs. It
does NOT change the frozen agent (protocol v3): the wrapped backend receives
exactly the prompt, schema, temperature and completion cap the frozen
``IterativeRepositoryAgentStrategy`` sends, and returns the provider response
unchanged.

What it adds (all operational, preregistered in
``docs/WP1B_MAIN297_EXECUTION_ADDENDUM_2026-09-22.md``):

1. The frozen retry rule, implemented exactly: TRANSPORT failures only
   (HTTP 429 / 5xx / connection / timeout), a byte-identical request, at most
   ``MAX_TRANSPORT_RETRIES = 3`` retries
   (``research/wp1a/wp1a_failure_semantics.json``). The inner
   ``OpenRouterBackend`` must be built with ``max_transient_retries=0`` so that
   this wrapper owns the whole retry budget (the inner default of ONE
   immediate retry does NOT match the frozen rule). A fixed backoff
   (10 s, 60 s, 180 s) separates attempts; the request bytes are unchanged.
2. A durable spend ledger (append + flush + fsync per call) so spend is never
   lost when a task crashes midway.
3. A per-request USD guard: before every call, the worst-case cost of that
   call (prompt estimate at the frozen prompt price + the full completion cap
   at the frozen completion price) is added to the ledger total; if that would
   exceed the ceiling the call is NOT sent (``BudgetGuardError``).
4. HTTP-attempt accounting (logical calls vs HTTP attempts).

Nothing here reads labels, proxies, target diffs or outcomes.
"""
from __future__ import annotations

import datetime
import http.client
import json
import math
import os
import re
import socket
import ssl
import time
import urllib.error
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import LLMResponse

FROZEN_PROMPT_USD_PER_1M: float = 0.30
FROZEN_COMPLETION_USD_PER_1M: float = 1.00
MAX_TRANSPORT_RETRIES: int = 3
# Backoff between the byte-identical retries (not a scientific knob; the request
# bytes never change). Long enough to ride out short provider incidents.
BACKOFF_SECONDS: tuple[float, ...] = (10.0, 60.0, 180.0)

# Error classes (addendum section 3.8)
TRANSPORT = "TRANSPORT"                    # retried (max 3); then item-level handling
ACCOUNT_OR_CONFIG = "ACCOUNT_OR_CONFIG"    # 401/402/403/404/missing key -> halt, item not recorded
BAD_REQUEST = "BAD_REQUEST"                # 400/413/422 -> instrument halt, item not recorded
PROVIDER_GLITCH = "PROVIDER_GLITCH"        # malformed/missing-usage response -> item-level handling
# Conservative upper bound used ONLY by the per-request USD guard (never for
# accounting): real Qwen tokenization on Saleor prompts is ~0.31 tokens/char.
GUARD_TOKENS_PER_CHAR: float = 0.5


class BudgetGuardError(Exception):
    """Raised BEFORE a request is sent when it could breach the USD ceiling."""


class BackendCallFailedError(ModelBackendError):
    """A model call failed for good (after the frozen retry budget where applicable)."""

    def __init__(self, message: str, *, classification: str, attempts: int) -> None:
        super().__init__(message)
        self.classification = classification
        self.attempts = attempts


class InnerBackend(Protocol):
    def count_prompt_tokens(self, prompt: str) -> int: ...

    async def generate_structured(
        self,
        prompt: str,
        *,
        schema_name: str,
        schema: dict[str, Any],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...


def frozen_usd(prompt_tokens: int, completion_tokens: int) -> float:
    """Frozen DeepInfra-through-OpenRouter list-price accounting."""
    return (
        prompt_tokens / 1e6 * FROZEN_PROMPT_USD_PER_1M
        + completion_tokens / 1e6 * FROZEN_COMPLETION_USD_PER_1M
    )


_HTTP_CODE = re.compile(r"OpenRouter HTTP (\d{3})")


def _cause_chain(exc: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    cur: BaseException | None = exc
    while cur is not None and cur not in chain and len(chain) < 8:
        chain.append(cur)
        cur = cur.__cause__ or cur.__context__
    return chain


def _classify_http(code: int) -> str:
    if code in (408, 429) or 500 <= code < 600:
        return TRANSPORT
    if code in (401, 402, 403, 404):  # key / credits / permission / model-route missing
        return ACCOUNT_OR_CONFIG
    return BAD_REQUEST


def classify_backend_error(exc: BaseException) -> str:
    """Classify a backend failure (message + cause chain).

    TRANSPORT: HTTP 408 / 429 / 5xx, connection failures, resets, remote disconnects,
    incomplete reads, SSL errors, timeouts - including the generic
    ``OpenRouter request failed: ...`` wrapper when its cause is a transport
    exception (``http.client.RemoteDisconnected``, ``ConnectionResetError`` ...).
    """
    msg = str(exc)
    m = _HTTP_CODE.search(msg)
    if m:
        return _classify_http(int(m.group(1)))
    if "API key not found" in msg:
        return ACCOUNT_OR_CONFIG
    if "OpenRouter connection failed" in msg or "timed out" in msg:
        return TRANSPORT
    for c in _cause_chain(exc)[1:]:
        if isinstance(c, urllib.error.HTTPError):
            return _classify_http(int(getattr(c, "code", 0) or 0))
        if isinstance(c, ConnectionError | http.client.HTTPException | ssl.SSLError
                      | urllib.error.URLError | TimeoutError | socket.timeout):
            return TRANSPORT
    return PROVIDER_GLITCH


def is_transient_transport_error(exc: BaseException) -> bool:
    return classify_backend_error(exc) == TRANSPORT


def utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def fsync_append(path: Path, line: str) -> None:
    """Append one line durably (flush + fsync)."""
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())


@dataclass
class SpendLedger:
    """Append-only, fsync'ed per-call spend ledger (JSONL).

    ``kind=call`` entries carry frozen list-price USD; ``kind=failure`` entries
    record a call that failed after the retry budget (no tokens billed by the
    provider are known for those; their USD is 0 in the frozen accounting).
    """

    path: Path
    total_usd: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    logical_calls: int = 0
    http_attempts: int = 0
    failed_calls: int = 0

    @classmethod
    def open(cls, path: Path) -> SpendLedger:
        ledger = cls(path=path)
        if path.exists():
            for raw in path.read_text(encoding="utf-8").splitlines():
                if not raw.strip():
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue  # torn last line after a crash; quarantined by the runner
                if isinstance(entry, dict):
                    ledger._absorb(entry)
        return ledger

    def _absorb(self, entry: dict[str, Any]) -> None:
        self.http_attempts += int(entry.get("http_attempts", 0))
        if entry.get("kind") == "call":
            self.logical_calls += 1
            self.total_prompt_tokens += int(entry.get("prompt_tokens", 0))
            self.total_completion_tokens += int(entry.get("completion_tokens", 0))
            self.total_usd += float(entry.get("usd", 0.0))
        elif entry.get("kind") == "failure":
            self.failed_calls += 1

    def append(self, entry: dict[str, Any]) -> None:
        fsync_append(self.path, json.dumps(entry, sort_keys=True))
        self._absorb(entry)


@dataclass
class _CallContext:
    work_key: str = ""
    task_id: str = ""
    attempt_id: str = ""
    call_index: int = 0
    attempts_this_item: int = 0
    retries_this_item: int = 0


class ResilientAccountingBackend:
    """Wrap an inner backend with the frozen transport-retry rule + ledger.

    The agent calls ``count_prompt_tokens`` and ``generate_structured``; both
    delegate to the inner backend with byte-identical arguments.
    """

    def __init__(
        self,
        inner: InnerBackend,
        *,
        ledger: SpendLedger,
        ceiling_usd: float,
        max_retries: int = MAX_TRANSPORT_RETRIES,
        backoff_seconds: tuple[float, ...] = BACKOFF_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_retries != MAX_TRANSPORT_RETRIES:
            raise ValueError(
                f"frozen retry rule is max {MAX_TRANSPORT_RETRIES} transport retries; got {max_retries}"
            )
        if ceiling_usd <= 0:
            raise ValueError("ceiling_usd must be positive")
        if not backoff_seconds:
            raise ValueError("backoff_seconds must be non-empty")
        self._inner = inner
        self._ledger = ledger
        self._ceiling = ceiling_usd
        self._max_retries = max_retries
        self._backoff = backoff_seconds
        self._sleep = sleep
        self._clock = clock
        self._ctx = _CallContext()

    @property
    def inner(self) -> InnerBackend:
        return self._inner

    @property
    def ledger(self) -> SpendLedger:
        return self._ledger

    @property
    def ceiling_usd(self) -> float:
        return self._ceiling

    def begin_item(self, *, work_key: str, task_id: str, attempt_id: str = "") -> None:
        self._ctx = _CallContext(work_key=work_key, task_id=task_id, attempt_id=attempt_id or work_key)

    @property
    def item_http_attempts(self) -> int:
        return self._ctx.attempts_this_item

    @property
    def item_transport_retries(self) -> int:
        return self._ctx.retries_this_item

    def count_prompt_tokens(self, prompt: str) -> int:
        return self._inner.count_prompt_tokens(prompt)

    async def generate_structured(
        self,
        prompt: str,
        *,
        schema_name: str,
        schema: dict[str, Any],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        async def _send() -> LLMResponse:
            return await self._inner.generate_structured(
                prompt,
                schema_name=schema_name,
                schema=schema,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        return await self._with_retries(_send, prompt=prompt, max_tokens=max_tokens)

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Protocol conformance only: the frozen agent always uses structured output."""
        inner_generate = getattr(self._inner, "generate", None)
        if not callable(inner_generate):
            raise ModelBackendError("inner backend has no generate(); structured output required")

        async def _send() -> LLMResponse:
            result = await inner_generate(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
            if not isinstance(result, LLMResponse):
                raise ModelBackendError("inner backend returned a non-LLMResponse value")
            return result

        return await self._with_retries(_send, prompt=prompt, max_tokens=max_tokens)

    async def _with_retries(
        self,
        send: Callable[[], Awaitable[LLMResponse]],
        *,
        prompt: str,
        max_tokens: int,
    ) -> LLMResponse:
        self._ctx.call_index += 1
        est_prompt = max(
            self._inner.count_prompt_tokens(prompt),
            math.ceil(len(prompt) * GUARD_TOKENS_PER_CHAR),
        )
        worst = frozen_usd(est_prompt, max(max_tokens, 0))
        if self._ledger.total_usd + worst > self._ceiling:
            raise BudgetGuardError(
                f"per-request guard: ledger {self._ledger.total_usd:.6f} + worst-case "
                f"{worst:.6f} > ceiling {self._ceiling:.2f}"
            )
        attempts = 0
        t0 = self._clock()
        while True:
            attempts += 1
            self._ctx.attempts_this_item += 1
            try:
                response = await send()
            except ModelBackendError as exc:
                cls = classify_backend_error(exc)
                if cls == TRANSPORT and attempts <= self._max_retries:
                    self._ctx.retries_this_item += 1
                    self._sleep(self._backoff[min(attempts - 1, len(self._backoff) - 1)])
                    continue
                self._ledger.append({
                    "kind": "failure",
                    "work_key": self._ctx.work_key,
                    "task_id": self._ctx.task_id,
                    "attempt_id": self._ctx.attempt_id,
                    "call_index": self._ctx.call_index,
                    "http_attempts": attempts,
                    "classification": cls,
                    "transient": cls == TRANSPORT,
                    "error": str(exc)[:500],
                    "utc": utc_now(),
                })
                raise BackendCallFailedError(str(exc), classification=cls, attempts=attempts) from exc
            tok = response.token_usage
            self._ledger.append({
                "kind": "call",
                "work_key": self._ctx.work_key,
                "task_id": self._ctx.task_id,
                "attempt_id": self._ctx.attempt_id,
                "call_index": self._ctx.call_index,
                "http_attempts": attempts,
                "prompt_tokens": tok.prompt_tokens,
                "completion_tokens": tok.completion_tokens,
                "usd": frozen_usd(tok.prompt_tokens, tok.completion_tokens),
                "finish_reason": response.finish_reason,
                "latency_s": round(self._clock() - t0, 4),
                "utc": utc_now(),
            })
            return response
