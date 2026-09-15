"""P5 — Append-only per-call usage ledger around litellm.completion.

INSTRUMENTATION ONLY. This does NOT alter LocAgent prompts, BM25, graph
traversal, ranking, temperature, iteration logic, or stopping behavior. It
only observes each ``litellm.completion()`` call and appends one metadata
record to a JSONL ledger.

Persisted per call (immediately after the call):
- case_id            (from the upstream current-issue global when available)
- call_index         (per-case sequence number)
- resolved model     (the model string passed to litellm)
- resolved provider  (custom_llm_provider from response hidden params, if any)
- success/failure    ("success" or a short error category)
- prompt_tokens / completion_tokens (from response usage when available)
- call latency (s)
- estimated cost (USD) from the frozen OpenRouter/DeepInfra pricing snapshot

NEVER persisted: prompts, responses, API keys, hidden change-set proxies,
candidate-universe content, or any scientific target material.

Ledger path is read from ``LOCAGENT_USAGE_LEDGER`` (set by the launcher). The
ledger is the AUTHORITATIVE source for model-call count and token/cost
accounting in the shared comparison; ``len(raw_output_loc)`` is NOT used as the
model-call metric.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any

# Frozen P1 endpoint pricing snapshot (OpenRouter -> DeepInfra, Qwen3-Coder
# 480B A35B). Same constants as src/benchmark/locagent/evaluator.py; duplicated
# here so the ledger works inside the isolated WSL venv without importing the
# benchmark package.
PROMPT_PER_TOKEN_USD = 0.30 / 1_000_000
COMPLETION_PER_TOKEN_USD = 1.00 / 1_000_000

_LOCK = threading.Lock()
_call_counters: dict[str, int] = {}
_last_case: str | None = None
_last_index: int = 0
_installed = False


def _ledger_path() -> str:
    return os.environ.get("LOCAGENT_USAGE_LEDGER", "")


def _current_case_id() -> str:
    try:
        from plugins.location_tools.repo_ops.repo_ops import get_current_issue_id

        cid = get_current_issue_id()
        return str(cid) if cid else ""
    except Exception:
        return ""


def _estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return round(
        int(prompt_tokens) * PROMPT_PER_TOKEN_USD
        + int(completion_tokens) * COMPLETION_PER_TOKEN_USD,
        8,
    )


def _provider_from_response(resp: Any) -> str:
    try:
        hidden = getattr(resp, "_hidden_params", None) or {}
        return str(hidden.get("custom_llm_provider", ""))
    except Exception:
        return ""


def _next_call_index(case_id: str) -> int:
    global _last_case, _last_index
    if case_id != _last_case:
        _last_case = case_id
        _last_index = 0
    _last_index += 1
    return _last_index


def install() -> None:
    """Wrap litellm.completion once (idempotent across spawn re-imports)."""
    global _installed
    if _installed:
        return

    import litellm

    original = litellm.completion

    def _instrumented(*args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()
        case_id = _current_case_id()
        model = str(kwargs.get("model") or (args[0] if args else ""))
        try:
            resp = original(*args, **kwargs)
            latency = time.monotonic() - start
            usage = getattr(resp, "usage", None)
            pt = int(getattr(usage, "prompt_tokens", 0) or 0)
            ct = int(getattr(usage, "completion_tokens", 0) or 0)
            _append(
                case_id=case_id,
                model=model,
                provider=_provider_from_response(resp),
                status="success",
                prompt_tokens=pt,
                completion_tokens=ct,
                latency_s=round(latency, 4),
                cost_usd=_estimate_cost(pt, ct),
            )
            return resp
        except Exception as exc:  # record failure, re-raise unchanged
            latency = time.monotonic() - start
            category = f"{type(exc).__name__}"
            _append(
                case_id=case_id,
                model=model,
                provider="",
                status=category,
                prompt_tokens=0,
                completion_tokens=0,
                latency_s=round(latency, 4),
                cost_usd=0.0,
            )
            raise

    litellm.completion = _instrumented
    _installed = True


def _append(
    *,
    case_id: str,
    model: str,
    provider: str,
    status: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_s: float,
    cost_usd: float,
) -> None:
    path = _ledger_path()
    if not path:
        return
    call_index = _next_call_index(case_id)
    row = {
        "case_id": case_id,
        "call_index": call_index,
        "model": model,
        "provider": provider,
        "status": status,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "latency_s": latency_s,
        "estimated_cost_usd": cost_usd,
        "pricing_snapshot": {
            "prompt_per_token_usd": PROMPT_PER_TOKEN_USD,
            "completion_per_token_usd": COMPLETION_PER_TOKEN_USD,
        },
    }
    with _LOCK, open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def load_ledger(path: str) -> list[dict[str, Any]]:
    """Read all ledger rows (for scoring/audit)."""
    if not os.path.exists(path):
        return []
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows
