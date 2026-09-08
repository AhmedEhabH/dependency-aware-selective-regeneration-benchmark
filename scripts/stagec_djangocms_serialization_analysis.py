#!/usr/bin/env python3
"""ZERO-API deterministic serialization-size analysis for the ImpactPlan
structured representation over the frozen 144-path universe.

- Builds the MINIMAL schema-valid ImpactPlan JSON over the real 144 paths.
- Measures bytes / characters (exact).
- If a Qwen-family tokenizer is available LOCALLY (no network), reports a
  clearly-labeled PROXY token estimate (NOT the exact qwen3-coder tokenizer).
- Compares against the raw truncated ImpactPlan responses (completion tokens,
  finish_reason) and the successful ImpactPlan plan sizes.

No scientific calls.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from benchmark.external_validity import study_runtime as wiring

PROJECT_DIR = wiring.PROJECT_DIR
STUDY_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-study-01"


def load_records() -> list[dict]:
    out = []
    for line in (STUDY_DIR / "run_records.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def minimal_plan_json() -> str:
    paths = wiring.runtime_universe_paths()
    decisions = [
        {
            "path": p,
            "action": "PRESERVE",
            "rationale": "",
            "confidence": 0.6,
            "reason_codes": [],
            "evidence": [],
        }
        for p in paths
    ]
    plan = {
        "decisions": decisions,
        "context_set": [],
        "validation_obligations": [],
        "architecture_checks": [],
        "escalation_reason": "",
    }
    return json.dumps(plan, separators=(",", ":"))


def proxy_tokens(text: str):
    """Use a locally-cached Qwen-family tokenizer as a PROXY (estimate only)."""
    try:
        from transformers import AutoTokenizer
    except Exception as exc:  # pragma: no cover
        return None, f"transformers unavailable: {exc}"
    name = "Qwen/Qwen2.5-Coder-7B-Instruct"
    try:
        tok = AutoTokenizer.from_pretrained(name, local_files_only=True)
    except Exception as exc:
        return None, f"local tokenizer {name} not loadable: {exc}"
    ids = tok.encode(text)
    return len(ids), name


def main() -> int:
    records = load_records()
    minimal = minimal_plan_json()
    n_bytes = len(minimal.encode("utf-8"))
    n_chars = len(minimal)
    tok_result, tok_note = proxy_tokens(minimal)
    # Rough token estimate using the project's own deterministic heuristic
    # (OpenRouterBackend.count_prompt_tokens == max(1, len(prompt)//4)).
    # Clearly an ESTIMATE, not a tokenizer measurement.
    rough_estimate = max(1, n_chars // 4)

    # Successful ImpactPlan cells: completion-token distribution (measured).
    success_completions = sorted(
        int(r["completion_tokens"])
        for r in records
        if r["arm"] == "impact_plan" and r["terminal_status"] == "succeeded"
    )
    success_plans = [
        {
            "run_id": r["run_id"],
            "completion_tokens": int(r["completion_tokens"]),
            "prompt_tokens": int(r["prompt_tokens"]),
        }
        for r in records
        if r["arm"] == "impact_plan" and r["terminal_status"] == "succeeded"
    ]

    # Truncated ImpactPlan responses: completion tokens + finish reason.
    truncations = [
        {
            "run_id": r["run_id"],
            "finish_reason": r.get("finish_reason", ""),
            "truncation_status": r.get("truncation_status", False),
            "completion_tokens": r.get("completion_tokens", 0),
            "prompt_tokens": r.get("prompt_tokens", 0),
        }
        for r in records
        if r["arm"] == "impact_plan"
        and r["terminal_status"] == "failed"
        and "finish_reason=length" in str(r.get("failure_category", ""))
    ]

    def _stats(vals):
        if not vals:
            return {}
        return {
            "min": vals[0],
            "median": vals[len(vals) // 2],
            "max": vals[-1],
            "count": len(vals),
        }

    result = {
        "analysis": "ZERO_API_SERIALIZATION_SIZE_ANALYSIS",
        "minimal_plan": {
            "universe_paths": len(wiring.runtime_universe_paths()),
            "action_label_used": "PRESERVE",
            "rationale": '"" (empty, schema-valid)',
            "evidence": "[] (empty, schema-valid)",
            "json_bytes_utf8": n_bytes,
            "json_characters": n_chars,
            "rough_token_estimate": rough_estimate,
            "rough_token_estimate_method": (
                "project heuristic max(1, n_chars // 4) — ESTIMATE ONLY, not a "
                "tokenizer measurement"
            ),
            "exact_tokenizer_available": False,
            "proxy_tokenizer_result": tok_result,
            "proxy_tokenizer_note": tok_note,
            "note": (
                "Byte/char counts are exact measurements. No Qwen tokenizer is "
                "available locally (only a tokenizer_config.json stub is cached) and "
                "none was downloaded; no API call was made. The token figure is a "
                "rough heuristic estimate and MUST NOT be reported as a measured fact."
            ),
        },
        "successful_impactplan_completion_tokens": {
            "stats": _stats(success_completions),
            "records": success_plans,
        },
        "truncated_responses": {
            "count": len(truncations),
            "all_finish_reason": sorted({t["finish_reason"] for t in truncations}),
            "all_completion_tokens": sorted({t["completion_tokens"] for t in truncations}),
            "records": truncations,
        },
        "successful_plans_size_comparison": success_plans,
    }
    out = STUDY_DIR / "serialization_size_analysis.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"persisted={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())