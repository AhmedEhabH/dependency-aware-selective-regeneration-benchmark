"""SCIENTIFIC-WIP-IMPACTPLAN-V1 model acceptance gate (D047, supersedes D041).

Single primary scientific model: ``qwen/qwen3-coder``.
Provider policy: FIXED COMPATIBLE PROVIDER, no fallback. Provider order:
1) DeepInfra (Turbo), 2) NovitaAI only if DeepInfra fails the frozen
operational contract. First-party hosting is NOT a scientific requirement (D7).

Three non-study operational tasks:
- A1 structured ImpactPlan task (synthetic, JSON-schema, R/P/V/H);
- A2 exact-patch task;
- A3 agent-control/tool task.

Thresholds (04_MODEL_PROVIDER_DECISION.md):
- 3/3 deterministic task success;
- 3/3 first responses parse;
- 0 truncations;
- no provider fallback;
- usage recorded;
- every successful call <= 120 s; median <= 60 s;
- <= 1 transient retry total (retry must succeed).

Writes:
  reports/model_acceptance_gate_2026-09-05.json
  reports/model_acceptance_gate_2026-09-05.md
  reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark.execution.exact_patch import apply_exact_patches, parse_exact_patch
from benchmark.llm.openrouter_backend import OpenRouterBackend

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
GATE_DATE = "2026-09-05"

PRIMARY_MODEL = "qwen/qwen3-coder"
PROVIDER_SEQUENCE: tuple[str, ...] = ("DeepInfra", "Novita")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# -------------------------------------------------------------------------
# Provider endpoint resolution (metadata only, no generation call)
# -------------------------------------------------------------------------


def fetch_model_endpoints(model: str, base_url: str = "https://openrouter.ai/api/v1") -> list[dict[str, Any]]:
    """GET /models/{model}/endpoints (no generation call)."""
    url = f"{base_url}/models/{model}/endpoints"
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data")
    if isinstance(data, dict):
        return data.get("endpoints") or []
    if isinstance(data, list):
        return data
    return []


def resolve_provider_from_endpoints(
    model: str,
    endpoints: list[dict[str, Any]],
    provider_order: tuple[str, ...],
) -> str:
    """Resolve the single pinned provider slug for the primary model."""
    available = {
        e.get("provider_name") for e in endpoints if e.get("provider_name")
    }
    for provider in provider_order:
        if provider in available:
            return provider
    raise RuntimeError(
        f"no provider from preregistered order {provider_order} is available for "
        f"{model}; available={sorted(available)}. STOP; do not model-shop."
    )


def pricing_snapshot(
    model: str,
    endpoints: list[dict[str, Any]],
    provider: str,
) -> dict[str, Any]:
    for e in endpoints:
        if e.get("provider_name") == provider:
            price = e.get("pricing") or {}
            return {
                "model": model,
                "provider": provider,
                "tag": e.get("tag"),
                "quantization": e.get("quantization"),
                "prompt_per_token_usd": price.get("prompt"),
                "completion_per_token_usd": price.get("completion"),
                "input_cache_read_per_token_usd": price.get("input_cache_read"),
                "fetched_at": _now_iso(),
            }
    return {}


def build_backend(model: str, provider: str, timeout: float = 120.0) -> OpenRouterBackend:
    return OpenRouterBackend(
        model=model,
        provider=provider,
        timeout_seconds=timeout,
        max_transient_retries=1,
    )


# -------------------------------------------------------------------------
# The three throwaway tasks
# -------------------------------------------------------------------------

_A1_CANDIDATES = ("pkg/alpha.py", "pkg/beta.py", "pkg/gamma.py")

_A1_PROMPT = """You are an impact planner for a tiny synthetic repository.

Requirement change: add a ``count`` attribute to the ``Alpha`` configuration and
expose it in the consumer module.

Candidate artifacts:
- pkg/alpha.py (config definition)
- pkg/beta.py (consumer that reads Alpha.count)
- pkg/gamma.py (unrelated utility)

Output ONLY one JSON object (no prose, no markdown fences):
{{
  "decisions": [
    {{"path": "<candidate>", "action": "REGENERATE"|"PRESERVE"|"VALIDATE_ONLY"|"HUMAN_REVIEW",
      "rationale": "<sentence>", "confidence": <0..1>}}
  ],
  "context_set": ["<paths to read as context>"],
  "validation_obligations": [],
  "architecture_checks": []
}}

Rules:
- classify exactly the three candidate paths; no other paths.
- REGENERATE only paths that absolutely need an edit (alpha.py and beta.py).
- PRESERVE gamma.py.
- context_set must be a subset of the three candidates.
"""


def run_task_a1(backend) -> dict[str, Any]:
    start = time.monotonic()
    result = _call_backend(backend, _A1_PROMPT, max_tokens=1024)
    dur = time.monotonic() - start
    parse_ok = False
    success = False
    try:
        parsed = _extract_json_object(result["text"])
        decisions = parsed.get("decisions", [])
        parse_ok = True
        paths = {d.get("path") for d in decisions}
        actions = {d.get("path"): (d.get("action") or "").upper() for d in decisions}
        success = (
            paths == set(_A1_CANDIDATES)
            and actions.get("pkg/alpha.py") == "REGENERATE"
            and actions.get("pkg/beta.py") == "REGENERATE"
            and actions.get("pkg/gamma.py") == "PRESERVE"
        )
    except Exception:
        parse_ok = False
        success = False
    return _task_outcome(result, dur, success=success, parse_ok=parse_ok,
                         truncation=result["finish_reason"] == "length")


_T2_CURRENT = "rename_me = 0\n\ndef increment():\n    return rename_me + 1\n"
_T2_REQUIRED = "rename_me"

_T2_PROMPT = """You are editing one small deterministic Python file.

Current content:
```python
{T2_CURRENT}
```

Required edit: rename the variable {T2_REQUIRED} to counter_new everywhere in
this file. Change ONLY that identifier. Preserve all other bytes exactly.

Output EXACT PATCH mode: return one or more SEARCH/REPLACE blocks:
<<<<<<< SEARCH
<exact lines to find>
=======
<replacement lines>
>>>>>>> REPLACE
Do not return the complete file, prose, or markdown fences.
"""


def run_task_a2(backend) -> dict[str, Any]:
    prompt = _T2_PROMPT.format(T2_CURRENT=_T2_CURRENT, T2_REQUIRED=_T2_REQUIRED)
    start = time.monotonic()
    result = _call_backend(backend, prompt, max_tokens=1024)
    dur = time.monotonic() - start
    success = False
    parse_ok = False
    try:
        blocks = parse_exact_patch(result["text"])
        parse_ok = True
        applied = apply_exact_patches(_T2_CURRENT, blocks)
        success = (
            _T2_REQUIRED not in applied
            and "counter_new" in applied
        )
    except Exception:
        parse_ok = False
        success = False
    return _task_outcome(result, dur, success=success, parse_ok=parse_ok,
                         truncation=result["finish_reason"] == "length")


_T3_INVENTORY = ("pkg/alpha.py", "pkg/beta.py", "pkg/gamma.py")

_T3_PROMPT = """You are an impact-scope selector for a tiny synthetic repository.

Requirement: add ``count`` to the Alpha configuration and expose it to beta.

Inventory:
- pkg/alpha.py (config)
- pkg/beta.py (consumer)
- pkg/gamma.py (unrelated)

Output ONLY one JSON object:
{{"selected_paths": ["..."], "rationale": "..."}}

Rules:
- selected_paths must be a subset of the inventory.
- The exact set of paths that need edits is ["pkg/alpha.py", "pkg/beta.py"].
- No prose, no markdown fences.
"""


def run_task_a3(backend) -> dict[str, Any]:
    start = time.monotonic()
    result = _call_backend(backend, _T3_PROMPT, max_tokens=1024)
    dur = time.monotonic() - start
    parse_ok = False
    success = False
    try:
        parsed = _extract_json_object(result["text"])
        paths = set(parsed.get("selected_paths") or [])
        parse_ok = True
        success = (
            paths == {"pkg/alpha.py", "pkg/beta.py"}
            and paths <= set(_T3_INVENTORY)
        )
    except Exception:
        parse_ok = False
        success = False
    return _task_outcome(result, dur, success=success, parse_ok=parse_ok,
                         truncation=result["finish_reason"] == "length")


# -------------------------------------------------------------------------
# Shared helpers
# -------------------------------------------------------------------------


def _call_backend(backend, prompt: str, *, max_tokens: int) -> dict[str, Any]:
    import asyncio

    async def _gen() -> Any:
        return await backend.generate(prompt=prompt, temperature=0.0, max_tokens=max_tokens)

    resp = asyncio.run(_gen())
    return {
        "text": resp.text,
        "prompt_tokens": resp.token_usage.prompt_tokens,
        "completion_tokens": resp.token_usage.completion_tokens,
        "total_tokens": resp.token_usage.total_tokens,
        "finish_reason": resp.finish_reason,
        "transient_retry_count": getattr(backend, "transient_retry_count", 0),
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    import re

    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    candidate = fence.group(1).strip() if fence else text.strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start < 0 or end < 0 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(candidate[start : end + 1])


def _task_outcome(
    result: dict[str, Any],
    duration: float,
    *,
    success: bool,
    parse_ok: bool,
    truncation: bool,
) -> dict[str, Any]:
    return {
        "prompt_tokens": result["prompt_tokens"],
        "completion_tokens": result["completion_tokens"],
        "total_tokens": result["total_tokens"],
        "finish_reason": result["finish_reason"],
        "transient_retry_count": result["transient_retry_count"],
        "latency_seconds": round(duration, 3),
        "parser_pass": parse_ok,
        "truncation": truncation,
        "deterministic_success": success,
        "response_sha256": hashlib.sha256(result["text"].encode("utf-8")).hexdigest(),
    }


# -------------------------------------------------------------------------
# Eligibility / freeze
# -------------------------------------------------------------------------


@dataclass
class GateOutcome:
    model: str
    provider: str
    tasks: list[dict[str, Any]] = field(default_factory=list)
    eligible: bool = False
    eligibility: dict[str, Any] = field(default_factory=dict)
    resolved_at: str = field(default_factory=_now_iso)


def compute_eligibility(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(tasks)
    success = sum(1 for t in tasks if t["deterministic_success"])
    parse_ok = sum(1 for t in tasks if t["parser_pass"])
    truncations = sum(1 for t in tasks if t["truncation"])
    usage_ok = sum(
        1 for t in tasks
        if t["prompt_tokens"] > 0 and t["completion_tokens"] and t["total_tokens"]
    )
    latencies = sorted(t["latency_seconds"] for t in tasks)
    median = latencies[len(latencies) // 2] if latencies else float("inf")
    transient = sum(1 for t in tasks if t["transient_retry_count"] > 0)
    eligible = (
        success == n
        and parse_ok == n
        and truncations == 0
        and all(t["latency_seconds"] <= 120 for t in tasks)
        and median <= 60
        and transient <= 1
        and usage_ok == n
    )
    return {
        "task_success": success,
        "all_tasks_reach_success": success == n,
        "format_compliance": parse_ok,
        "all_responses_parse": parse_ok == n,
        "truncation_count": truncations,
        "no_truncation": truncations == 0,
        "transient_events": transient,
        "transient_reliability": transient <= 1,
        "usage_accounting": usage_ok,
        "usage_all_present": usage_ok == n,
        "latency_all_under_120": all(t["latency_seconds"] <= 120 for t in tasks),
        "median_latency": round(median, 3),
        "median_latency_under_60": median <= 60,
        "eligible": eligible,
    }


def write_freeze(
    outcome: GateOutcome,
    *,
    acceptance_report: dict[str, Any],
    prereg_amendment_commit: str,
    source_commit: str,
    pricing_timestamp: str,
    pricing: dict[str, Any],
) -> dict[str, Any]:
    return {
        "frozen_at": _now_iso(),
        "model": outcome.model,
        "provider": outcome.provider,
        "backend": "openrouter",
        "identity": f"openrouter:{outcome.model}@{outcome.provider}",
        "protocol": "scientific-wip-impactplan-v1",
        "temperature": 0.0,
        "mode": "direct/non-thinking",
        "provider_fallbacks": False,
        "require_parameters": True,
        "call_timeout_seconds": 120,
        "workflow_timeout_seconds": 900,
        "source_edit_cap": 4096,
        "agent_control_cap": 512,
        "max_attempts": 3,
        "retry_policy": "transient 429/5xx/transport retry max=1; 4xx never retried",
        "pricing": pricing,
        "pricing_timestamp": pricing_timestamp,
        "acceptance_report_hash": hashlib.sha256(
            json.dumps(acceptance_report, sort_keys=True, default=str).encode()
        ).hexdigest(),
        "preregistration_amendment_commit": prereg_amendment_commit,
        "source_commit": source_commit,
    }


# -------------------------------------------------------------------------
# Orchestration
# -------------------------------------------------------------------------


def main() -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("OPENROUTER_API_KEY is required")
        return 1

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=list(PROVIDER_SEQUENCE),
        default=None,
        help="Force a specific provider for the operational gate.",
    )
    args = parser.parse_args()

    model = PRIMARY_MODEL
    endpoints = fetch_model_endpoints(model)
    provider = args.provider or resolve_provider_from_endpoints(
        model, endpoints, PROVIDER_SEQUENCE
    )
    backend = build_backend(model, provider)

    tasks: list[dict[str, Any]] = []
    for name, fn in (
        ("A1_impact_plan", run_task_a1),
        ("A2_exact_patch", run_task_a2),
        ("A3_agent_control", run_task_a3),
    ):
        out = fn(backend)
        out["task"] = name
        out["model"] = model
        out["provider"] = provider
        tasks.append(out)

    elig = compute_eligibility(tasks)
    outcome = GateOutcome(
        model=model, provider=provider, tasks=tasks,
        eligible=elig["eligible"], eligibility=elig,
    )

    report = {
        "date": GATE_DATE,
        "model": model,
        "provider": provider,
        "resolved_at": outcome.resolved_at,
        "eligible": outcome.eligible,
        "eligibility": outcome.eligibility,
        "tasks": outcome.tasks,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_p = REPORTS_DIR / f"model_acceptance_gate_{GATE_DATE}.json"
    md_p = REPORTS_DIR / f"model_acceptance_gate_{GATE_DATE}.md"
    json_p.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    md_p.write_text(_render_md(report), encoding="utf-8")

    if not outcome.eligible:
        print("MODEL_NOT_ELIGIBLE — no scientific calls; STOP.")
        print(f"Wrote {json_p}")
        return 1

    pricing = pricing_snapshot(model, endpoints, provider)
    source_commit = _git("rev-parse", "HEAD")
    freeze = write_freeze(
        outcome,
        acceptance_report=report,
        prereg_amendment_commit=source_commit,
        source_commit=source_commit,
        pricing_timestamp=_now_iso(),
        pricing=pricing,
    )
    freeze_path = REPORTS_DIR / "SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json"
    freeze_path.write_text(json.dumps(freeze, indent=2, default=str), encoding="utf-8")

    print(f"FREEZING model={model} provider={provider}")
    print(f"Wrote {json_p}")
    print(f"Wrote {md_p}")
    print(f"Wrote {freeze_path}")
    return 0


def _render_md(report: dict[str, Any]) -> str:
    lines = [
        f"# Model acceptance gate — {report['date']}",
        "",
        f"Model: **{report['model']}** @ `{report['provider']}`",
        "",
        f"Eligible={report['eligible']}",
        "",
        "## Tasks",
    ]
    for t in report["tasks"]:
        lines.append(
            f"- {t['task']}: success={t['deterministic_success']} "
            f"parse={t['parser_pass']} trunc={t['truncation']} "
            f"latency={t['latency_seconds']}s"
        )
    lines.append("")
    return "\n".join(lines)


def _git(*args: str) -> str:
    import subprocess

    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return proc.stdout.strip() or ""


if __name__ == "__main__":
    raise SystemExit(main())
