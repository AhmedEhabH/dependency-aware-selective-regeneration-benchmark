"""SCIENTIFIC-MICROSTUDY-01 model acceptance gate (D041 / PA-001).

Runs the frozen 3 throwaway non-study operational tasks exactly once per
candidate, resolves provider endpoint metadata WITHOUT any model generation
call, applies the frozen provider policy (first-party DeepSeek for candidate A,
single-provider for candidate B), computes eligibility from the preregistered
thresholds, applies the preregistered selection rule, and writes:

  reports/model_acceptance_gate_2026-09-05.json
  reports/model_acceptance_gate_2026-09-05.md
  reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json

This gate is NON-STUDY operational selection. No Todo scientific scenario,
evaluator, ground truth, or study requirement may enter any prompt here.
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

CANDIDATES: list[dict[str, str]] = [
    {
        "id": "A",
        "model": "deepseek/deepseek-v4-flash-0731",
        "policy": "first_party_deepseek",
        "first_party_provider": "DeepSeek",
    },
    {
        "id": "B",
        "model": "qwen/qwen-2.5-coder-32b-instruct",
        "policy": "single_provider",
    },
]

MODELS_ENDPOINT = "https://openrouter.ai/api/v1/models"

# Deterministic thowaway tasks. NONE is a scientific scenario.
T1_CURRENT = "counter = 0\n\ndef increment():\n    return counter + 1\n"
T1_REQUIRED = "rename_me"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Provider endpoint resolution (metadata only, no model generation call)
# ---------------------------------------------------------------------------

def fetch_models_metadata(endpoint: str = MODELS_ENDPOINT) -> list[dict[str, Any]]:
    """GET /models metadata. Raises on transport/HTTP errors; no generation call."""
    req = urllib.request.Request(endpoint, method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("data", [])


def resolve_provider_for_candidate(
    model: str,
    models_metadata: list[dict[str, Any]],
    *,
    policy: str,
    first_party_provider: str = "",
) -> str:
    """Resolve the single pinned provider slug for a candidate model.

    - first_party_deepseek: pin the provider named ``first_party_provider``;
      if it is not available for the exact model, STOP (raise) and require a
      preregistration amendment.
    - single_provider: the model must advertise exactly one provider; pin it.
      If it is no longer single-provider, STOP and document the change.
    """
    matches = [m for m in models_metadata if m.get("id") == model]
    if not matches:
        raise RuntimeError(
            f"model '{model}' not found in OpenRouter /models metadata; "
            "cannot resolve providers before the gate"
        )
    endpoints = matches[0].get("endpoints") or []
    providers = sorted({e.get("provider_name") for e in endpoints if e.get("provider_name")})
    providers = [p for p in providers if p]

    if policy == "first_party_deepseek":
        if first_party_provider not in providers:
            raise RuntimeError(
                f"first-party provider '{first_party_provider}' not available for "
                f"{model}; available={providers}. STOP acceptance gate; a "
                "preregistration amendment is required before choosing a third party."
            )
        return first_party_provider

    if policy == "single_provider":
        if len(providers) != 1:
            raise RuntimeError(
                f"model '{model}' must be single-provider for the gate; "
                f"found providers={providers}. STOP and document the change."
            )
        return providers[0]

    raise ValueError(f"unknown provider policy: {policy}")


def build_backend(model: str, provider: str, timeout: float = 120.0) -> OpenRouterBackend:
    return OpenRouterBackend(
        model=model,
        provider=provider,
        timeout_seconds=timeout,
        max_transient_retries=1,
    )


# ---------------------------------------------------------------------------
# The three throwaway tasks
# ---------------------------------------------------------------------------

# T1 -- exact-patch operational task
_T1_PROMPT = """You are editing one small deterministic Python file.

Current content:
```python
{T1_CURRENT}
```

Required edit: rename the variable {T1_REQUIRED} to counter_new everywhere in this
file. Change ONLY that identifier. Preserve all other bytes exactly.

Output EXACT PATCH mode: return one or more SEARCH/REPLACE blocks with the exact
structure:
<<<<<<< SEARCH
<exact lines to find>
=======
<replacement lines>
>>>>>>> REPLACE
Do not return the complete file, prose, or markdown fences.
"""


def run_task_t1(backend) -> dict[str, Any]:
    """Exact-patch task: valid SEARCH/REPLACE that applies exactly."""
    prompt = _T1_PROMPT.format(T1_CURRENT=T1_CURRENT, T1_REQUIRED=T1_REQUIRED)
    start = time.monotonic()
    result = _call_backend(backend, prompt, max_tokens=1024)
    duration = time.monotonic() - start

    success = False
    parse_ok = False
    truncation = result["finish_reason"] == "length"
    try:
        blocks = parse_exact_patch(result["text"])
        parse_ok = True
        applied = apply_exact_patches(T1_CURRENT, blocks)
        success = (
            "counter_new" in applied
            and T1_REQUIRED not in applied
            and applied.count("print") == T1_CURRENT.count("print")
        )
    except Exception:
        parse_ok = False
        success = False

    return _task_outcome(
        result, duration=duration, success=success,
        parse_ok=parse_ok, truncation=truncation,
    )


# T2 -- agent-control operational task
_T2_INVENTORY = {
    "todo/models.py": "model",
    "todo/serializers.py": "serializer",
    "todo/views.py": "view",
    "todo/permissions.py": "permission",
    "todo/urls.py": "config",
}

_T2_PROMPT = """You are an impact-scope selector for a small synthetic repository.

Requirement change: the Task model must gain a priority field; serializers and
views must expose and filter it; permissions and urls are unaffected.

Repository inventory:
- todo/models.py (model)
- todo/serializers.py (serializer)
- todo/views.py (view)
- todo/permissions.py (permission)
- todo/urls.py (config)

Output ONLY one JSON object with this exact machine-readable schema (no prose,
no markdown fences):
{{"decisions": [{{"path": "<inventory path>", "action": "regenerate"|"preserve"}}], "rationale": "<one sentence>"}}

Rules:
- 'decisions' must cover every inventory path exactly once.
- paths named in 'decisions' must come only from the inventory above.
- 'regenerate' must include todo/models.py, todo/serializers.py, todo/views.py.
- 'preserve' must include todo/permissions.py and todo/urls.py.
"""


def run_task_t2(backend) -> dict[str, Any]:
    prompt = _T2_PROMPT
    start = time.monotonic()
    result = _call_backend(backend, prompt, max_tokens=1024)
    duration = time.monotonic() - start

    parse_ok = False
    success = False
    truncation = result["finish_reason"] == "length"
    decisions: list[dict[str, str]] = []
    try:
        parsed = _extract_json(result["text"])
        decisions = parsed.get("decisions", [])
        parse_ok = True
        paths = {d.get("path") for d in decisions}
        actions = {d.get("path"): d.get("action") for d in decisions}
        regen = {p for p, a in actions.items() if a == "regenerate"}
        preserve = {p for p, a in actions.items() if a == "preserve"}
        success = (
            set(paths) == set(_T2_INVENTORY)
            and regen == {"todo/models.py", "todo/serializers.py", "todo/views.py"}
            and preserve == {"todo/permissions.py", "todo/urls.py"}
        )
    except Exception:
        parse_ok = False
        success = False

    return _task_outcome(
        result, duration=duration, success=success,
        parse_ok=parse_ok, truncation=truncation,
        decisions=decisions,
    )


# T3 -- repair operational task
T3_FAULTY_PATCH = "counter = 0\n\ndef increment():\n    return counter + 1\n    print('after')\n"
T3_VALIDATION_ERROR = (
    "ValidationError: unreachable code after return in increment() "
    "(assert_unreachable_rejected)"
)

_T3_PROMPT = """A previous patch failed the tiny deterministic validation.

Validation error:
{T3_VALIDATION_ERROR}

Current faulty content:
```python
{T3_FAULTY_PATCH}
```

Required fix: remove the unreachable statement after the return so the file is
clean. Preserve everything else byte-for-byte.

Output EXACT PATCH mode: return one or more SEARCH/REPLACE blocks.
Do not return the complete file, prose, or markdown fences.
"""


def run_task_t3(backend) -> dict[str, Any]:
    prompt = _T3_PROMPT.format(
        T3_VALIDATION_ERROR=T3_VALIDATION_ERROR,
        T3_FAULTY_PATCH=T3_FAULTY_PATCH,
    )
    start = time.monotonic()
    result = _call_backend(backend, prompt, max_tokens=1024)
    duration = time.monotonic() - start

    parse_ok = False
    success = False
    truncation = result["finish_reason"] == "length"
    repaired = T3_FAULTY_PATCH
    try:
        blocks = parse_exact_patch(result["text"])
        parse_ok = True
        repaired = apply_exact_patches(T3_FAULTY_PATCH, blocks)
        success = (
            "print('after')" not in repaired
            and "return counter + 1" in repaired
            and repaired.count("counter") == 2
        )
    except Exception:
        parse_ok = False
        success = False

    return _task_outcome(
        result, duration=duration, success=success,
        parse_ok=parse_ok, truncation=truncation,
        repaired=repaired,
    )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _call_backend(backend, prompt: str, *, max_tokens: int) -> dict[str, Any]:
    import asyncio

    async def _gen():
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


def _extract_json(text: str) -> dict[str, Any]:
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
    *,
    duration: float,
    success: bool,
    parse_ok: bool,
    truncation: bool,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "call_number": 0,
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
        **extra,
    }


# ---------------------------------------------------------------------------
# Eligibility and selection
# ---------------------------------------------------------------------------

@dataclass
class CandidateGateResult:
    id: str
    model: str
    provider: str
    tasks: list[dict[str, Any]] = field(default_factory=list)
    eligible: bool = False
    eligibility: dict[str, Any] = field(default_factory=dict)
    resolved_at: str = field(default_factory=_now_iso)


def compute_eligibility(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Preregistered eligibility thresholds (PREREGISTRATION section 1)."""
    n = len(tasks)
    task_success = sum(1 for t in tasks if t["deterministic_success"])
    parse_ok = sum(1 for t in tasks if t["parser_pass"])
    truncation = sum(1 for t in tasks if t["truncation"])
    usage_ok = sum(
        1 for t in tasks
        if t["prompt_tokens"] > 0 or t["completion_tokens"] > 0 or t["total_tokens"] > 0
    )
    latencies = sorted(t["latency_seconds"] for t in tasks)
    latency_ok = all(t["latency_seconds"] <= 120 for t in tasks)
    median_latency = latencies[len(latencies) // 2] if latencies else float("inf")
    transient_events = sum(1 for t in tasks if t["transient_retry_count"] > 0)

    passed = (
        task_success == n
        and parse_ok == n
        and truncation == 0
        and transient_events <= 1
        and usage_ok == n
        and latency_ok
        and median_latency <= 60
    )
    return {
        "task_success": task_success,
        "all_tasks_reach_success": task_success == n,
        "format_compliance": parse_ok,
        "all_responses_parse": parse_ok == n,
        "truncation_count": truncation,
        "no_truncation": truncation == 0,
        "transient_events": transient_events,
        "transient_reliability": transient_events <= 1,
        "usage_accounting": usage_ok,
        "usage_all_present": usage_ok == n,
        "latency_all_under_120": latency_ok,
        "median_latency": round(median_latency, 3),
        "median_latency_under_60": median_latency <= 60,
        "eligible": passed,
    }


def select_winner(results: list[CandidateGateResult]) -> CandidateGateResult | None:
    """Preregistered selection rule among eligible candidates (D041).

    1. higher first-response format compliance (all 3 of a candidate's first
       responses parsing, i.e. parser_pass on every task);
    2. lower truncation count;
    3. lower median latency;
    4. tie -> document (reproducibility contract is identical for both).
    """
    eligible = [r for r in results if r.eligible]
    if not eligible:
        return None
    if len(eligible) == 1:
        return eligible[0]

    def _med(r: CandidateGateResult) -> float:
        lats = sorted(t["latency_seconds"] for t in r.tasks)
        return lats[len(lats) // 2]

    def _first_response_parse(r: CandidateGateResult) -> int:
        return sum(1 for t in r.tasks if t["parser_pass"])

    ranked = sorted(
        eligible,
        key=lambda r: (
            -_first_response_parse(r),
            sum(1 for t in r.tasks if t["truncation"]),
            _med(r),
        ),
    )
    return ranked[0]


def write_freeze(
    winner: CandidateGateResult,
    *,
    acceptance_report: dict[str, Any],
    prereg_amendment_commit: str,
    source_commit: str,
    pricing_timestamp: str,
    config_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    freeze: dict[str, Any] = {
        "frozen_at": _now_iso(),
        "model": winner.model,
        "provider": winner.provider,
        "backend": "openrouter",
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
        "pricing_timestamp": pricing_timestamp,
        "acceptance_report_hash": hashlib.sha256(
            json.dumps(acceptance_report, sort_keys=True, default=str).encode()
        ).hexdigest(),
        "preregistration_amendment_commit": prereg_amendment_commit,
        "source_commit": source_commit,
        "identity": f"openrouter:{winner.model}@{winner.provider}",
    }
    if config_extra:
        freeze.update(config_extra)
    return freeze


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_gate(
    *,
    models_metadata: list[dict[str, Any]],
    provider_timeout: float = 120.0,
) -> dict[str, Any]:
    candidate_results: list[CandidateGateResult] = []
    for candidate in CANDIDATES:
        provider = resolve_provider_for_candidate(
            candidate["model"],
            models_metadata,
            policy=candidate["policy"],
            first_party_provider=candidate.get("first_party_provider", ""),
        )
        backend = build_backend(candidate["model"], provider, timeout=provider_timeout)

        task_runners = [
            ("T1_exact_patch", run_task_t1),
            ("T2_agent_control", run_task_t2),
            ("T3_repair", run_task_t3),
        ]
        tasks: list[dict[str, Any]] = []
        for call_idx, (_name, fn) in enumerate(task_runners, start=1):
            outcome = fn(backend)
            outcome["call_number"] = call_idx
            outcome["model"] = candidate["model"]
            outcome["provider"] = provider
            tasks.append(outcome)
        eligibility = compute_eligibility(tasks)
        candidate_results.append(
            CandidateGateResult(
                id=candidate["id"],
                model=candidate["model"],
                provider=provider,
                tasks=tasks,
                eligible=eligibility["eligible"],
                eligibility=eligibility,
            )
        )

    winner = select_winner(list(candidate_results))

    report = {
        "date": GATE_DATE,
        "candidates": [
            {
                "id": r.id,
                "model": r.model,
                "provider": r.provider,
                "resolved_at": r.resolved_at,
                "eligible": r.eligible,
                "eligibility": r.eligibility,
                "tasks": r.tasks,
            }
            for r in candidate_results
        ],
        "selection": {
            "winner": winner.model if winner else None,
            "provider": winner.provider if winner else None,
            "rule": "preregistered selection rule (D041); if neither eligible STOP",
        },
    }
    return {"report": report, "winner": winner}


def main() -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("OPENROUTER_API_KEY is required")
        return 1

    models_metadata = fetch_models_metadata()

    prereg_commit = _git("rev-parse", "HEAD")
    source_commit = prereg_commit
    pricing_timestamp = _now_iso()

    result = run_gate(
        models_metadata=models_metadata,
    )
    report = result["report"]
    winner = result["winner"]

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / f"model_acceptance_gate_{GATE_DATE}.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    md_path = REPORTS_DIR / f"model_acceptance_gate_{GATE_DATE}.md"
    md_path.write_text(_render_md(report), encoding="utf-8")

    if winner is None:
        print("NEITHER CANDIDATE ELIGIBLE — STOP; no scientific calls.")
        print(f"Wrote {json_path}")
        return 1

    freeze = write_freeze(
        winner,
        acceptance_report=report,
        prereg_amendment_commit=prereg_commit,
        source_commit=source_commit,
        pricing_timestamp=pricing_timestamp,
    )
    freeze_path = REPORTS_DIR / "SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json"
    freeze_path.write_text(json.dumps(freeze, indent=2, default=str), encoding="utf-8")

    print(f"WINNER model={winner.model} provider={winner.provider}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {freeze_path}")
    return 0


def _render_md(report: dict[str, Any]) -> str:
    lines = [
        f"# Model acceptance gate — {report['date']}",
        "",
        "## Eligibility",
        "",
    ]
    for c in report["candidates"]:
        lines.append(f"- **{c['id']}** `{c['model']}` @ `{c['provider']}`: "
                     f"eligible={c['eligible']} ({c['eligibility']})")
    lines.append("")
    lines.append(f"## Selection\n\nWinner: **{report['selection']['winner']}** "
                 f"@ `{report['selection']['provider']}`")
    return "\n".join(lines)


def _git(*args: str) -> str:
    import subprocess

    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    return proc.stdout.strip() or ""


if __name__ == "__main__":
    raise SystemExit(main())
