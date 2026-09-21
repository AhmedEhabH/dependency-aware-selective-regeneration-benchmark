#!/usr/bin/env python3
"""WP-1b B1 - budget model v2 (new blocker G8).

Defect being fixed: src/benchmark/wp1a/budget.py uses PROMPT_BASE_CHARS_EST =
6000 while the agent prompt (INITIAL_SYSTEM_PROMPT) lists every editable path.
For Saleor that is ~810 paths/task (range 438-1140), ~11,200 prompt tokens,
re-sent on each of up to 8 calls. The frozen v1 model underestimates prompt
tokens by ~3.4x and would likely end in BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON.

This script builds, for every task in Calibration-3 and in the D4 manifest
(B2), the real ArtifactUniverse with the production path
(allow_ground_truth_universe=False) from the public candidate universe
(public/candidate_universe.json) and the stored SIP intent (intent parity), and
renders the EXACT initial prompt with _build_initial_prompt(...). Label-free.

Worst case per task = sum over r=1..8 of (base_prompt_chars + (r-1)*(2000
chars + result-tag overhead)) * TOKENS_PER_CHAR, plus 8 * cap completion tokens.
Priced at the frozen $0.30/$1.00 per 1M.

Frozen ceilings (D5): Calibration-3 0.25, Main 21.50, Variance 3.50, Total 25.25.
If any computed worst case * 1.5 exceeds its D5 ceiling this script exits
CEILING_BELOW_WORST_CASE (fail-closed; does not raise D5).

Outputs: research/wp1b/wp1b_budget_model_v2.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.core.enums import ArtifactType  # noqa: E402
from benchmark.core.models import ArtifactRef, ArtifactUniverse, RequirementChange  # noqa: E402
from benchmark.strategies.iterative_agent import _build_initial_prompt  # noqa: E402

RESEARCH = _PROJECT_DIR / "research"
SALEOR_SCIENTIFIC = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
OUT = RESEARCH / "wp1b"

TOKENS_PER_CHAR = 0.3137
TOOL_OUTPUT_CHARS_PER_ROUND = 2000.0
RESULT_TAG_OVERHEAD_CHARS = 60.0
MAX_AGENT_CALLS = 8
AGENT_CAP = 1024
PROMPT_PRICE_PER_1M = 0.30
COMPLETION_PRICE_PER_1M = 1.00
SAFETY = 1.5

# D5 hard ceilings (USD).
CEILINGS = {
    "calibration_3": 0.25,
    "main": 21.50,
    "variance_substudy": 3.50,
    "total": 25.25,
}


def _load_manifest(name: str) -> list[str]:
    p = OUT / name
    data = json.loads(p.read_text(encoding="utf-8"))
    return [str(x) for x in data["task_ids"]]


def _build_universe(task_id: str) -> ArtifactUniverse:
    """Build the real ArtifactUniverse via the production path
    (allow_ground_truth_universe=False): public candidate universe only."""
    cu = json.loads(
        (SALEOR_SCIENTIFIC / task_id / "public" / "candidate_universe.json").read_text(encoding="utf-8")
    )
    records = cu.get("records", [])
    artifacts = tuple(
        ArtifactRef(path=str(r["path"]), artifact_type=ArtifactType.source)
        for r in records
    )
    return ArtifactUniverse(artifacts=artifacts)


def _build_requirement_change(task_id: str) -> RequirementChange:
    """Deterministic WP-1b agent input construction.

    The stored SIP intent (public/intent.json intent_text) is the byte-identical
    stored SIP intent (intent parity). The INITIAL_SYSTEM_PROMPT template has
    Before/After/Acceptance criteria fields; the requirement change carries the
    commit message as the `after` (the change being requested) and the parent
    commit (public, deterministic) as the `before` context. This keeps the
    stored SIP intent byte-identical in the rendered prompt.
    """
    intent = json.loads(
        (SALEOR_SCIENTIFIC / task_id / "public" / "intent.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (SALEOR_SCIENTIFIC / task_id / "case_manifest.json").read_text(encoding="utf-8")
    )
    parent_commit = manifest.get("record", {}).get("parent_commit", "")
    intent_text = str(intent.get("intent_text", ""))
    return RequirementChange(
        before=f"Repository state at parent commit {parent_commit}",
        after=intent_text,
        acceptance_criteria=(),
    )


def _render_base_prompt_chars(task_id: str) -> int:
    universe = _build_universe(task_id)
    req = _build_requirement_change(task_id)
    editable_paths = tuple(a.path for a in universe.artifacts)
    prompt = _build_initial_prompt(req, editable_paths)
    return len(prompt)


def _worst_case(task_id: str) -> dict[str, float]:
    """Worst-case tokens: base prompt on every call, prompt grows by
    (2000 + result-tag overhead) chars per extra call; plus cap completion
    tokens on every call."""
    base_chars = _render_base_prompt_chars(task_id)
    prompt_tokens = 0.0
    for r in range(1, MAX_AGENT_CALLS + 1):
        call_chars = base_chars + (TOOL_OUTPUT_CHARS_PER_ROUND + RESULT_TAG_OVERHEAD_CHARS) * (r - 1)
        prompt_tokens += call_chars * TOKENS_PER_CHAR
    completion_tokens = AGENT_CAP * MAX_AGENT_CALLS
    return {
        "base_prompt_chars": float(base_chars),
        "base_prompt_tokens": float(base_chars) * TOKENS_PER_CHAR,
        "worst_case_prompt_tokens": prompt_tokens,
        "worst_case_completion_tokens": float(completion_tokens),
        "worst_case_total_tokens": prompt_tokens + completion_tokens,
        "worst_case_usd": prompt_tokens / 1e6 * PROMPT_PRICE_PER_1M + completion_tokens / 1e6 * COMPLETION_PRICE_PER_1M,
    }


def _total(records: list[dict]) -> dict[str, float]:
    return {
        "prompt_tokens": sum(r["worst_case_prompt_tokens"] for r in records),
        "completion_tokens": sum(r["worst_case_completion_tokens"] for r in records),
        "total_tokens": sum(r["worst_case_total_tokens"] for r in records),
        "usd_base": sum(r["worst_case_usd"] for r in records),
    }


def main() -> int:
    cal3_ids = json.loads(
        (RESEARCH / "wp1a" / "wp1_calibration_3_manifest.json").read_text(encoding="utf-8")
    )["task_ids"]
    main297 = _load_manifest("wp1b_main_297_manifest.json")
    main150 = _load_manifest("wp1b_main_150_manifest.json")
    main50 = _load_manifest("wp1b_main_50_manifest.json")

    salt = "wp1b-variance-substudy-v1-2026-09-21"
    var15 = sorted(main50, key=lambda t: hashlib.sha256((salt + t).encode("utf-8")).hexdigest())[:15]

    per_task: dict[str, dict] = {}
    all_ids = sorted(set(cal3_ids + main297))
    for tid in all_ids:
        per_task[tid] = _worst_case(tid)

    cal_records = [per_task[t] for t in cal3_ids]
    main297_records = [per_task[t] for t in main297]
    main150_records = [per_task[t] for t in main150]
    main50_records = [per_task[t] for t in main50]
    var_records = [per_task[t] for t in var15]

    cal_total = _total(cal_records)
    main297_total = _total(main297_records)
    main150_total = _total(main150_records)
    main50_total = _total(main50_records)
    var_total_usd = 3 * _total(var_records)["usd_base"]

    # v1 frozen model (for underestimate factor).
    v1 = {"projected_prompt_tokens": 1729114, "ceiling_usd": 1.103733, "prompt_base_chars_est": 6000}
    v1_prompt_53 = 1729114
    # underestimate factor vs the 53-task v1 prompt projection:
    # v1 projected 1.729M prompt tokens for 53 tasks; new worst-case (8-call) prompt for those 53.
    _53 = cal3_ids + [t for t in main50]
    v1_factor = sum(per_task[t]["worst_case_prompt_tokens"] for t in _53) / v1_prompt_53

    out = {
        "artifact": "wp1b_budget_model_v2",
        "mission": "WP1B_PREFLIGHT_FREEZE_2026-09-21",
        "date": "2026-09-21",
        "api_calls": 0,
        "labels_used": "opened RESERVE-300 proxies only; 786 untouched",
        "model": "qwen/qwen3-coder",
        "provider": "deepinfra/turbo (through OpenRouter)",
        "pricing": {
            "prompt_per_1m_usd": PROMPT_PRICE_PER_1M,
            "completion_per_1m_usd": COMPLETION_PRICE_PER_1M,
        },
        "agent": {
            "MAX_AGENT_CALLS": MAX_AGENT_CALLS,
            "agent_control_max_completion_tokens": AGENT_CAP,
            "tool_output_chars_per_round": TOOL_OUTPUT_CHARS_PER_ROUND,
            "result_tag_overhead_chars": RESULT_TAG_OVERHEAD_CHARS,
            "tokens_per_char": TOKENS_PER_CHAR,
            "safety_factor": SAFETY,
        },
        "universe": {
            "mean_size": round(
                sum(len(_build_universe(t).artifacts) for t in cal3_ids + main50)
                / (len(cal3_ids) + len(main50)),
                3,
            ),
            "note": "universe from each task's real public candidate_universe.json "
                    "(production path, allow_ground_truth_universe=False)",
        },
        "v1_frozen_model": v1,
        "worst_case_per_task": {
            tid: {k: round(v, 6) for k, v in rec.items()} for tid, rec in per_task.items()
        },
        "totals": {
            "calibration_3": {k: round(v, 6) for k, v in cal_total.items()},
            "main_50": {k: round(v, 6) for k, v in main50_total.items()},
            "main_150": {k: round(v, 6) for k, v in main150_total.items()},
            "main_297": {k: round(v, 6) for k, v in main297_total.items()},
            "variance_substudy_15x3": {"usd_base": round(var_total_usd, 6)},
        },
        "with_safety_x1_5": {
            "calibration_3": round(cal_total["usd_base"] * SAFETY, 6),
            "main_50": round(main50_total["usd_base"] * SAFETY, 6),
            "main_150": round(main150_total["usd_base"] * SAFETY, 6),
            "main_297": round(main297_total["usd_base"] * SAFETY, 6),
            "variance_substudy_15x3": round(var_total_usd * SAFETY, 6),
        },
        "frozen_ceilings": CEILINGS,
        "ceiling_checks": {
            "calibration_3_with_safety_below_d5": round(cal_total["usd_base"] * SAFETY, 6) <= CEILINGS["calibration_3"],
            "main_297_with_safety_below_d5": round(main297_total["usd_base"] * SAFETY, 6) <= CEILINGS["main"],
            "variance_with_safety_below_d5": round(var_total_usd * SAFETY, 6) <= CEILINGS["variance_substudy"],
        },
        "underestimate_factor_vs_v1_prompt_53": round(v1_factor, 4),
        "abort_rule_v2": (
            "If the main-run ceiling is hit before all N tasks finish, the primary "
            "result is BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON. Exception, "
            "preregistered now: if the first 50 tasks in frozen order (the nested "
            "MAIN_50) finished, MAIN_50 may be analysed as UNDERPOWERED_FALLBACK - "
            "never as the primary claim."
        ),
    }

    # Fail-closed ceiling check.
    fails = [k for k, v in out["ceiling_checks"].items() if not v]
    if fails:
        print("[wp1b-b1] CEILING_BELOW_WORST_CASE", fails)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "wp1b_budget_model_v2.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("[wp1b-b1] written research/wp1b/wp1b_budget_model_v2.json")
    print("[wp1b-b1] calibration3 worst-case usd:", round(cal_total["usd_base"], 6),
          "x1.5:", round(cal_total["usd_base"] * SAFETY, 6), "ceiling:", CEILINGS["calibration_3"])
    print("[wp1b-b1] main297 worst-case usd:", round(main297_total["usd_base"], 6),
          "x1.5:", round(main297_total["usd_base"] * SAFETY, 6), "ceiling:", CEILINGS["main"])
    print("[wp1b-b1] variance 15x3 usd:", round(var_total_usd, 6),
          "x1.5:", round(var_total_usd * SAFETY, 6), "ceiling:", CEILINGS["variance_substudy"])
    print("[wp1b-b1] underestimate factor (v1 prompt 1.729M -> 53-task worst prompt):", round(v1_factor, 4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
