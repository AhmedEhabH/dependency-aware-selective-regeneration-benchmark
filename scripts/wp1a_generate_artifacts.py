#!/usr/bin/env python3
"""WP-1a generate the remaining frozen artifacts (no API calls):

- research/wp1a/wp1a_failure_semantics.json
- research/wp1a/wp1a_cost_quality_categories.json
- research/wp1a/wp1a_shared_scorer_schema.json
- research/wp1a/wp1a_accounting_schema.json
- research/wp1a/wp1a_budget_model.json
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.wp1a import accounting, budget, scorer, semantics  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "wp1a"


def main() -> int:
    now = datetime.datetime.now(datetime.UTC).isoformat()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    failure = {
        "wp1a": "wp1a_failure_semantics",
        "generated_utc": now,
        "primary_analysis_rule": semantics.PRIMARY_ANALYSIS_RULE,
        "interpretation_rule": semantics.INTERPRETATION_RULE,
        "per_arm_failure_rates": list(semantics.FAILURE_RATE_NAMES),
        "retry": {"transport": "max 3 byte-identical retries; ONLY transport failures may be retried"},
        "timeout": "cooperative workflow deadline; fail-closed EMPTY",
        "malformed": "invalid JSON -> error appended; continue if calls remain; else EMPTY",
        "empty": "no paths selected -> EMPTY prediction (fail-closed)",
        "invalid_paths": "outside editable universe -> error; continue if calls remain; else EMPTY",
        "round_cap_reached": "remaining agent calls exhausted without final -> EMPTY prediction",
        "partial_tool_failure": (
            "tool error result returned to the agent; loop continues; repeated "
            "identical tool request rejected"
        ),
        "no_silent_exclusions": True,
    }
    (OUT_DIR / "wp1a_failure_semantics.json").write_text(json.dumps(failure, indent=1), encoding="utf-8")

    categories = {
        "wp1a": "wp1a_cost_quality_categories",
        "generated_utc": now,
        "hypothesis": semantics.HYPOTHESIS_H_WP1,
        "categories": semantics.COST_QUALITY_CATEGORIES,
        "dominance_gate_latency_rule": semantics.DOMINANCE_GATE_LATENCY_RULE,
        "claim_boundary": semantics.CLAIM_BOUNDARY,
    }
    (OUT_DIR / "wp1a_cost_quality_categories.json").write_text(json.dumps(categories, indent=1), encoding="utf-8")

    scorer_schema = {
        "wp1a": "wp1a_shared_scorer_schema",
        "generated_utc": now,
        "arms": list(scorer.ARMS),
        "inputs": ["frozen predictions (task_id -> set of file paths)",
                   "labels loaded ONLY after prediction freeze",
                   "identical task IDs across arms"],
        "metrics": list(scorer.METRIC_NAMES),
        "bootstrap": {
            "n_resamples": scorer.N_RESAMPLES,
            "seed": scorer.BOOTSTRAP_SEED,
            "ci": "[Q2.5,Q97.5] percentile",
            "unit": "task",
            "delta_f1": "F1(RM-CSS) - F1(repository_agent)",
            "ci_crosses_zero": "NO_DIFFERENCE_DETECTED_AT_THIS_N (not equivalence)",
            "no_silent_margin": "No non-inferiority margin is silently chosen.",
        },
    }
    (OUT_DIR / "wp1a_shared_scorer_schema.json").write_text(json.dumps(scorer_schema, indent=1), encoding="utf-8")

    accounting_schema = {
        "wp1a": "wp1a_accounting_schema",
        "generated_utc": now,
        "per_arm_fields": list(accounting.ARM_EFFICIENCY_FIELDS),
        "rmcss_marginal_view_fields": list(accounting.RMCSS_MARGINAL_VIEW_FIELDS),
        "rmcss_setup_view_fields": list(accounting.RMCSS_SETUP_VIEW_FIELDS),
        "rmcss_two_views_rule": (
            "View A marginal/per-change operational cost (no double counting of "
            "already-built reusable indexes); View B preprocessing/setup cost "
            "(one-time builds). Report amortized examples at N=50 and N=300. "
            "Do not hide one-time preprocessing; do not charge the full one-time "
            "build to every task."
        ),
        "latency_provenance_rule": accounting.LATENCY_PROVENANCE_RULE,
        "frozen_efficiency_reference": "research/saleor-reserve-300-rmcss/saleor_reserve_300_efficiency.json",
    }
    (OUT_DIR / "wp1a_accounting_schema.json").write_text(json.dumps(accounting_schema, indent=1), encoding="utf-8")

    budget_model = budget.project_agent_cost()
    budget_model["generated_utc"] = now
    budget_model["wp1a"] = "wp1a_budget_model"
    (OUT_DIR / "wp1a_budget_model.json").write_text(json.dumps(budget_model, indent=1), encoding="utf-8")

    print("[wp1a-gen] failure semantics + cost-quality + scorer schema + accounting + budget written")
    print("[wp1a-budget] recommended ceiling USD:", budget_model["recommended_ceiling_usd"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
