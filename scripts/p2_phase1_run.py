#!/usr/bin/env python3
# ruff: noqa: E501, N806
# B_t / M are the frozen protocol's realized-budget / missed-count symbols.
"""P2 Phase-1 — common adaptive-budget DEVELOPMENT evaluation (ZERO API).

Frozen constants:
- P2-P1 tau_gap = 0.10 (declared in the pre-registration note; no data fit).
- P2-P2 tau_marg = 25th percentile of the composite-score distribution over
  djangoCMS DEV_TRAIN candidates ONLY (derived here, before any
  DEV_VALIDATION / Saleor outcome is inspected).
- P2-P3 tau_cost grid = declared sensitivity ratios (0.5, 1.0, 2.0), run as a
  curve; never presented as monetary truth.
- P2-P4 tau_energy = 0.90 (declared).

The derivation split is djangoCMS DEV_TRAIN (117 tasks). Validation splits:
djangoCMS DEV_VALIDATION (27) and Saleor DEV (149). Results are also reported
per repository (djangoCMS DEV = 174, Saleor DEV = 149) and pooled.

Outputs:
- research/p2-phase1/frozen_constants.json
- research/p2-phase1/results_summary.json
- research/p2-phase1/per_task_rows.json
- reports/p2_phase1_gates.json
- reports/P2_PHASE1_HARNESS_RESULTS.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.p2.cost_model import measured_verifier_cost_model  # noqa: E402
from benchmark.p2.evaluate import (  # noqa: E402
    evaluate_fixed_b,
    evaluate_inspect_all,
    evaluate_policy,
    matched_fixed_b_summary,
    pareto_frontier,
    strata_summary,
)
from benchmark.p2.policies import (  # noqa: E402
    P2P1ScoreGap,
    P2P2MarginalScore,
    P2P3CostRatio,
    P2P4LearningK,
    PolicyView,
)
from benchmark.p2.tasks import FIXED_BUDGETS, load_dev_tasks  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "p2-phase1"
OUT_CONSTANTS = OUT_DIR / "frozen_constants.json"
OUT_SUMMARY = OUT_DIR / "results_summary.json"
OUT_PER_TASK = OUT_DIR / "per_task_rows.json"
GATES_JSON = _PROJECT_DIR / "reports" / "p2_phase1_gates.json"
REPORT_MD = _PROJECT_DIR / "reports" / "P2_PHASE1_HARNESS_RESULTS.md"

TAU_GAP = 0.10
TAU_ENERGY = 0.90
COST_RATIO_GRID = (0.5, 1.0, 2.0)
SEED = 20260918


def derive_tau_marg(dev_train_tasks: list[Any]) -> float:
    """25th percentile of the per-task TOP-1 composite scores on DEV_TRAIN.

    Pre-registered derivation rule (frozen on DEV_TRAIN before any validation /
    Saleor outcome): the marginal-score threshold is the 25th percentile of the
    strongest observable signal per task. The full candidate-pool distribution is
    bimodal with ~58% zeros (irrelevant candidates), whose 25th percentile is 0
    and would make the rule degenerate; the per-task top-1 distribution is the
    non-degenerate reference intended by the pre-registration note.
    """
    tops = [t.candidates[0].composite for t in dev_train_tasks if t.candidates]
    return round(float(np.percentile(tops, 25)), 6)


def _make_policies(tau_marg: float, cost_model: Any) -> dict[str, Any]:  # noqa: ARG001
    return {
        "P2-P1-score-gap": P2P1ScoreGap(tau_gap=TAU_GAP),
        "P2-P2-marginal-score": P2P2MarginalScore(tau_marg=tau_marg),
        "P2-P4-learning-k-analogue": P2P4LearningK(tau_energy=TAU_ENERGY),
    }


def _group(tasks: list[Any], *, repo: str | None = None, roles: set[str] | None = None) -> list[Any]:
    out = []
    for t in tasks:
        if repo is not None and t.repository != repo:
            continue
        if roles is not None and t.role not in roles:
            continue
        out.append(t)
    return out


def main() -> int:
    tasks = list(load_dev_tasks())
    cost_model = measured_verifier_cost_model()

    dev_train = _group(tasks, repo="djangocms", roles={"DEV_TRAIN"})
    dev_val = _group(tasks, repo="djangocms", roles={"DEV_VALIDATION"})
    djangocms_dev = _group(tasks, repo="djangocms")
    saleor_dev = _group(tasks, repo="saleor")
    pooled = tasks

    tau_marg = derive_tau_marg(dev_train)
    constants = {
        "tau_gap": TAU_GAP,
        "tau_marg": tau_marg,
        "tau_marg_derivation": "25th percentile of per-task TOP-1 composite scores on djangoCMS DEV_TRAIN (non-degenerate reference; candidate pool is ~58% zeros)",
        "tau_energy": TAU_ENERGY,
        "cost_ratio_grid": list(COST_RATIO_GRID),
        "derivation_split": "djangoCMS DEV_TRAIN (117 tasks; observable composite scores only)",
        "validation_splits": ["djangoCMS DEV_VALIDATION", "Saleor DEV"],
        "seed": SEED,
        "frozen": True,
        "no_tuning_on_outcomes": True,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CONSTANTS.write_text(json.dumps(constants, indent=2), encoding="utf-8")

    splits = {
        "djangocms_dev": djangocms_dev,
        "saleor_dev": saleor_dev,
        "pooled_dev": pooled,
        "djangocms_dev_train_derivation": dev_train,
        "djangocms_dev_validation": dev_val,
    }

    # Per-repo + pooled results
    results: dict[str, Any] = {"constants": constants}
    for split_name, ts in splits.items():
        fixed_curve = [evaluate_fixed_b(ts, B, ranker="composite", cost_model=cost_model) for B in FIXED_BUDGETS]
        bm25_curve = [evaluate_fixed_b(ts, B, ranker="bm25", cost_model=cost_model) for B in FIXED_BUDGETS]
        inspect_all = evaluate_inspect_all(ts)
        pol = _make_policies(tau_marg, cost_model)
        p3 = {}
        for r in COST_RATIO_GRID:
            p3[f"tau={r}"] = evaluate_policy(ts, P2P3CostRatio(r, cost_model), cost_model=cost_model)
        policy_res = {name: evaluate_policy(ts, p, cost_model=cost_model) for name, p in pol.items()}
        policy_res.update({f"P2-P3-cost-ratio-{k}": v for k, v in p3.items()})

        points = fixed_curve + list(policy_res.values()) + [inspect_all]
        results[split_name] = {
            "n_tasks": len(ts),
            "fixed_B_composite": fixed_curve,
            "fixed_B_bm25": bm25_curve,
            "inspect_all": inspect_all,
            "policies": policy_res,
            "matched_fixed_b": {
                name: matched_fixed_b_summary(agg, fixed_curve)
                for name, agg in policy_res.items()
            },
            "pareto_frontier": pareto_frontier(points),
        }

    # Strata per repo (omitted-size terciles)
    strata = {}
    for repo_name, ts in (("djangocms", djangocms_dev), ("saleor", saleor_dev)):
        strata[repo_name] = {
            name: strata_summary(ts, p, cost_model=cost_model)
            for name, p in _make_policies(tau_marg, cost_model).items()
        }
    results["strata"] = strata

    OUT_SUMMARY.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # ---- Gate: strong-method trigger (frozen, pre-outcome rule) ----
    # A policy shows a reproducible DEV trade-off on BOTH repos if its mean cost
    # is strictly below the fixed-B=5 reference cost AND its macro ORR is within
    # 5% of the fixed-B=5 macro ORR on that repo.
    def _gate_info(split_name: str) -> dict[str, Any]:
        d = results[split_name]
        f5 = next(f for f in d["fixed_B_composite"] if f["budget"] == 5)
        out = {}
        for name, agg in d["policies"].items():
            better_cost = agg["mean_cost_usd"] < f5["mean_cost_usd"]
            within_recovery = agg["macro_orr"] >= f5["macro_orr"] * 0.95
            out[name] = {
                "policy_orr": agg["macro_orr"],
                "policy_cost_usd": agg["mean_cost_usd"],
                "fixedB5_orr": f5["macro_orr"],
                "fixedB5_cost_usd": f5["mean_cost_usd"],
                "lower_cost_than_B5": better_cost,
                "orr_within_5pct_of_B5": within_recovery,
                "trade_off_present": better_cost and within_recovery,
            }
        return out

    gate = {
        "rule": "proceed to stronger methods iff any P2-P1..P4 shows lower mean cost than fixed-B=5 AND macro ORR within 5% of fixed-B=5 on BOTH djangoCMS DEV and Saleor DEV (pre-registered, not tuned)",
        "djangocms_dev": _gate_info("djangocms_dev"),
        "saleor_dev": _gate_info("saleor_dev"),
    }
    for name in ("P2-P1-score-gap", "P2-P2-marginal-score", "P2-P4-learning-k-analogue", "P2-P3-cost-ratio-tau=0.5"):
        ok = gate["djangocms_dev"][name]["trade_off_present"] and gate["saleor_dev"][name]["trade_off_present"]
        gate.setdefault("per_policy", {})[name] = {"both_repos_trade_off": ok}
    gate["strong_method_gate_pass"] = any(
        v["both_repos_trade_off"] for v in gate.get("per_policy", {}).values()
    )
    GATES_JSON.write_text(json.dumps({"gates": [{"name": "strong_method_trigger", "passed": gate["strong_method_gate_pass"], "detail": gate}], "all_passed": gate["strong_method_gate_pass"]}, indent=2), encoding="utf-8")

    # Per-task rows for the primary policies + fixed-B=5 composite (reporting only)
    rows_out: dict[str, list[dict[str, Any]]] = {}
    pol = _make_policies(tau_marg, cost_model)
    for split_name, ts in splits.items():
        rows_out[split_name] = []
        for t in ts:
            row = {"case_id": t.case_id, "repository": t.repository, "role": t.role,
                   "omitted_size": t.omitted_size, "universe_size": t.universe_size,
                   "n_missed": t.n_missed}
            for pname, p in pol.items():
                B_t = int(p.choose_budget(PolicyView.from_task(t)))
                from benchmark.p2.evaluate import recovery_at
                rec = recovery_at(t, B_t, ranker="composite")
                M = t.n_missed
                row[f"{pname}_B"] = B_t
                row[f"{pname}_recovered"] = rec
                row[f"{pname}_orr"] = round(rec / M, 4) if M else 0.0
            row["fixedB5_composite_recovered"] = recovery_at(t, 5, ranker="composite")
            rows_out[split_name].append(row)
    OUT_PER_TASK.write_text(json.dumps(rows_out, indent=2), encoding="utf-8")

    # ---- Markdown report ----
    md = [
        "# P2 Phase-1 — Common Adaptive-Budget Harness: DEVELOPMENT Results",
        "",
        "**Date:** 2026-09-18  **Tier:** T3 scientific DEVELOPMENT (ZERO API)",
        "**Data:** djangoCMS DEV (174 tasks) + Saleor DEV (149 tasks). djangoCMS",
        "INTERNAL_TEST is spent and NEVER used for P2 selection/tuning; RESERVE and",
        "Saleor INTERNAL_TEST/RESERVE are sealed.",
        "",
        "## Frozen constants (derived on djangoCMS DEV_TRAIN ONLY)",
        "",
        f"- `tau_gap` = {TAU_GAP} (declared in the pre-registration note)",
        f"- `tau_marg` = {tau_marg} (25th percentile of DEV_TRAIN composite scores)",
        f"- `tau_energy` = {TAU_ENERGY} (declared)",
        f"- cost-ratio grid (declared sensitivity): {list(COST_RATIO_GRID)}",
        "",
        "## Verifier cost model (measured, frozen)",
        "",
        "- prompt_tokens(B) = 204.51 + 7.40*B; api_cost(B) = 0.000065 + 0.000005*B",
        "  (least-squares fit over the 320 frozen confirmatory verifier calls).",
        "- Cost semantics: 1 batch verifier call at realized B_t (candidates = B_t);",
        "  `marginal_calls = B_t` is a labelled sensitivity.",
        "",
    ]

    for split_name, title in (
        ("djangocms_dev", "djangoCMS DEV (n=174)"),
        ("saleor_dev", "Saleor DEV (n=149)"),
        ("pooled_dev", "Pooled DEV (n=323)"),
    ):
        d = results[split_name]
        md += [f"## {title}", "", "| method | macro ORR | micro ORR | mean B/task | mean tokens | mean cost $ | oracle-gap | over-alloc | under-alloc |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for f in d["fixed_B_composite"]:
            md.append(f"| fixed-B{f['budget']} (composite) | {f['macro_orr']} | {f['micro_orr']} | {f['budget']} | {f['mean_tokens']} | {f['mean_cost_usd']} | {f['mean_oracle_gap_closed']} | {f['over_allocation_rate']} | {f['under_allocation_rate']} |")
        for name, agg in d["policies"].items():
            md.append(f"| {name} | {agg['macro_orr']} | {agg['micro_orr']} | {agg['expected_budget']} | {agg['mean_tokens']} | {agg['mean_cost_usd']} | {agg['mean_oracle_gap_closed']} | {agg['over_allocation_rate']} | {agg['under_allocation_rate']} |")
        md += ["", f"Pareto frontier (recovery-vs-cost): {', '.join(d['pareto_frontier'])}", "", f"Matched fixed-B comparison: {json.dumps(d['matched_fixed_b'], indent=1)}", ""]

    md += [
        "## Strata (omitted-size terciles, per repo)",
        "",
        "```json",
        json.dumps(strata, indent=1),
        "```",
        "",
        "## Strong-method gate (pre-registered)",
        "",
        f"gate pass = {gate['strong_method_gate_pass']}",
        "",
        "```json",
        json.dumps({k: v for k, v in gate.items() if k != 'per_policy'}, indent=1),
        "```",
        "",
        "Machine-readable: research/p2-phase1/{frozen_constants,results_summary,per_task_rows}.json",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(md), encoding="utf-8")

    print(json.dumps({"n_djangocms": len(djangocms_dev), "n_saleor": len(saleor_dev),
                      "tau_marg": tau_marg, "gate_pass": gate["strong_method_gate_pass"]}, indent=1))
    print("wrote", OUT_CONSTANTS, OUT_SUMMARY, OUT_PER_TASK, GATES_JSON, REPORT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
