"""Frozen Agentless-style execution: single-call API invocation + accounting.

Model/route/decoding/retry/timeout/pricing are the frozen MAIN_297 values
recorded in the protocol freeze. One call per task; raw output persisted;
provider-reported usage is the token/cost source of truth.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

# Frozen values (from execute_saleor_inference.py / OpenRouterBackend policy).
MODEL: str = "qwen/qwen3-coder"
PROVIDER_TAG: str = "deepinfra/turbo"
TEMPERATURE: float = 0.0
MAX_COMPLETION_TOKENS: int = 1024
MAX_TRANSIENT_RETRIES: int = 4
RETRY_BACKOFF_SECONDS: float = 20.0
TIMEOUT_SECONDS: float = 300.0

# Frozen pricing: deepinfra/turbo through OpenRouter ($0.30 / $1.00 per 1M).
PROMPT_PER_TOKEN_USD: float = 0.30 / 1_000_000.0
COMPLETION_PER_TOKEN_USD: float = 1.00 / 1_000_000.0
PRICING_SOURCE: str = "frozen DeepInfra-through-OpenRouter pricing ($0.30/$1.00 per 1M)"

URL: str = "https://openrouter.ai/api/v1/chat/completions"


@dataclass(frozen=True)
class CallEvidence:
    ok: bool
    dispatched: bool
    attempt_count: int
    error: str | None = None
    raw_text: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    api_cost_usd: float = 0.0


def _redact_error(msg: str) -> str:
    return msg[:200]


def call_agentless(
    prompt: str,
    api_key: str,
    *,
    max_retries: int = MAX_TRANSIENT_RETRIES,
    backoff: float = RETRY_BACKOFF_SECONDS,
    timeout: float = TIMEOUT_SECONDS,
) -> CallEvidence:
    """One file-level localization call with the frozen retry policy.

    Transient failures (429/5xx/connect/timeout) are retried up to
    ``max_retries`` with ``backoff`` seconds; 4xx content/auth errors are never
    retried. Returns raw provider text plus provider-reported usage.
    """
    body: dict[str, Any] = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_COMPLETION_TOKENS,
        "stream": False,
        "provider": {"order": [PROVIDER_TAG], "allow_fallbacks": False, "require_parameters": True},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        URL,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    return _call_with_retries(
        _urllib_transport(req, timeout),
        max_retries=max_retries,
        backoff=backoff,
    )


def _urllib_transport(req: urllib.request.Request, timeout: float) -> Any:
    """Return a transport callable mirroring the frozen urllib.OpenRouter call.

    The transport returns the raw response bytes (str) or raises one of the
    standard urllib exceptions so the retry policy classifies them.
    """

    def transport() -> str:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")

    return transport


def _call_with_retries(
    transport,
    *,
    max_retries: int,
    backoff: float,
    sleep_fn=time.sleep,
) -> CallEvidence:
    """Frozen retry loop over an injectable transport (testability)."""
    last_error: BaseException | None = None
    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            sleep_fn(backoff)
        try:
            raw_text = transport()
            return _evidence_from_raw(raw_text, attempt)
        except urllib.error.HTTPError as exc:
            dangerous = exc.code in (429,) or 500 <= exc.code < 600
            last_error = exc
            if not dangerous or attempt == max_retries:
                return CallEvidence(
                    ok=False,
                    dispatched=True,
                    attempt_count=attempt,
                    error=f"OpenRouter HTTP {exc.code}: {_redact_error(str(exc))}",
                )
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == max_retries:
                return CallEvidence(
                    ok=False,
                    dispatched=True,
                    attempt_count=attempt,
                    error=f"OpenRouter transport failed: {_redact_error(str(exc))}",
                )
        except Exception as exc:
            return CallEvidence(
                ok=False,
                dispatched=True,
                attempt_count=attempt,
                error=f"OpenRouter request failed: {_redact_error(str(exc))}",
            )
    assert last_error is not None  # unreachable; all exit paths return
    return CallEvidence(
        ok=False,
        dispatched=True,
        attempt_count=max_retries,
        error=f"OpenRouter failed after {max_retries} attempts: {_redact_error(str(last_error))}",
    )


def _evidence_from_raw(raw_text: str, attempt: int) -> CallEvidence:
    parsed = json.loads(raw_text)
    choice = (parsed.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content") or ""
    usage = parsed.get("usage") or {}
    pt = int(usage.get("prompt_tokens") or 0)
    ct = int(usage.get("completion_tokens") or 0)
    cost = round(pt * PROMPT_PER_TOKEN_USD + ct * COMPLETION_PER_TOKEN_USD, 6)
    return CallEvidence(
        ok=True,
        dispatched=True,
        attempt_count=attempt,
        raw_text=content,
        prompt_tokens=pt,
        completion_tokens=ct,
        api_cost_usd=cost,
    )


def compute_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    return round(
        prompt_tokens * PROMPT_PER_TOKEN_USD
        + completion_tokens * COMPLETION_PER_TOKEN_USD,
        6,
    )


def budget_exceeded(cumulative_cost_usd: float, ceiling_usd: float) -> bool:
    """Frozen budget-stop predicate: STOP before any further call when exceeded."""
    return cumulative_cost_usd > ceiling_usd
