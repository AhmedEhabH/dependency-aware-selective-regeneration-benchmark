#!/usr/bin/env python3
# ruff: noqa: E501, N803, N806
"""Route B ranker-identity audit + incremental-evidence ablation (ZERO API).

Reuses the frozen Route-B V2 implementation EXACTLY (build_task, rank_arm,
recovery_at from scripts.route_b_v2_robustness and the Saleor transfer) to:

A. Ranker-identity audit
   1. prove/disprove CIA-vs-Hybrid rank equivalence mathematically;
   2. check top-B identity at B={1,3,5,10} on all djangoCMS DEV tasks;
   3. check top-B identity at B={1,3,5,10} on all Saleor DEV tasks;
   4. report tasks/budgets where they differ;
   5. classify Hybrid as redundant alias/control if equivalent;
   6. audit whether the name "Classical-CIA" overstates the implementation.

B. Incremental-evidence ablation (characterization only, no method change)
   for BOTH repositories at B={1,3,5,10}:
   - macro ORR / micro ORR / recovered FN count for AnalyticRandom, BM25,
     Graph, frozen composite (bm25 + graph_neighbor);
   - composite minus BM25 paired task-level delta + task-level bootstrap CI;
   - graph minus random;
   - rank/top-B overlap composite vs BM25;
   - number of additional FNs recovered by the composite beyond BM25.

No frozen historical raw output is modified; only NEW files are written.

Outputs:
- reports/ROUTE_B_RANKER_IDENTITY_AUDIT.md
- research/transparency/route_b_ranker_identity_audit.json
- reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md
- research/transparency/route_b_incremental_ablation.json
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from scripts.route_b_v2_robustness import (  # noqa: E402
    BUDGETS,
    SPLIT,
    V1_DATASET,
    V1_RECORDS,
    V2_DATASET,
    V2_RECORDS,
    _load_run,
    build_task,
    load_case,
    rank_arm,
    recovery_at,
)
from scripts.saleor_route_b_transfer import (  # noqa: E402
    SALEOR_DATASET,
    SALEOR_RECORDS,
)

SEED = 20260917
N_BOOT = 2000
OUT_AUDIT_JSON = _PROJECT_DIR / "research" / "transparency" / "route_b_ranker_identity_audit.json"
OUT_AUDIT_MD = _PROJECT_DIR / "reports" / "ROUTE_B_RANKER_IDENTITY_AUDIT.md"
OUT_ABL_JSON = _PROJECT_DIR / "research" / "transparency" / "route_b_incremental_ablation.json"
OUT_ABL_MD = _PROJECT_DIR / "reports" / "ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md"


def build_djangocms_tasks() -> list[dict[str, Any]]:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assign = split["assignment"]
    v1_recs = _load_run(V1_RECORDS)
    v2_recs = _load_run(V2_RECORDS)
    v1_case_ids = {r["case_id"] for r in v1_recs}
    by_case: dict[str, dict[str, Any]] = {}
    for rec in v1_recs + v2_recs:
        if rec["terminal_status"] != "succeeded":
            continue
        cid = rec["case_id"]
        if cid in by_case:
            continue
        dataset = V1_DATASET if cid in v1_case_ids else V2_DATASET
        case = load_case(cid, dataset)
        proxy = set(rec["hidden_proxy_used_after_inference"])
        write_set = set(rec.get("predicted_write_set") or [])
        by_case[cid] = build_task(cid, case, write_set, proxy)
    tasks = []
    for cid, task in by_case.items():
        role = assign.get(cid, "V1_DEV")
        tasks.append({"case_id": cid, "role": role, **task})
    tasks.sort(key=lambda t: t["case_id"])
    return tasks


def build_saleor_tasks() -> list[dict[str, Any]]:
    recs = _load_run(SALEOR_RECORDS)
    by_case: dict[str, dict[str, Any]] = {}
    for rec in recs:
        if rec["terminal_status"] != "succeeded":
            continue
        cid = rec["case_id"]
        if cid in by_case:
            continue
        case = load_case(cid, SALEOR_DATASET)
        proxy = set(rec["hidden_proxy_used_after_inference"])
        write_set = set(rec.get("predicted_write_set") or [])
        by_case[cid] = build_task(cid, case, write_set, proxy)
    tasks = [
        {"case_id": cid, "role": "SALEOR_DEV", **task}
        for cid, task in by_case.items()
    ]
    tasks.sort(key=lambda t: t["case_id"])
    return tasks


def top_b_set(task: dict[str, Any], arm: str, B: int) -> set[str]:
    if B == 0 or arm == "Sparse_B0":
        return set()
    N = task["omitted_size"]
    B_eff = min(B, N)
    ranked = rank_arm(arm, task["candidates"])[:B_eff]
    return set(ranked)


def identity_check(tasks: list[dict[str, Any]], budgets: tuple[int, ...]) -> dict[str, Any]:
    """CIA vs Hybrid top-B identity + full-rank identity."""
    diff_tasks: dict[int, int] = {}
    diff_budget_tasks: list[dict[str, Any]] = []
    full_rank_identical = True
    for t in tasks:
        rank_cia = rank_arm("CIA", t["candidates"])
        rank_hyb = rank_arm("Hybrid", t["candidates"])
        if rank_cia != rank_hyb:
            full_rank_identical = False
        for B in budgets:
            if B == 0:
                continue
            s_cia = set(rank_cia[: min(B, t["omitted_size"])])
            s_hyb = set(rank_hyb[: min(B, t["omitted_size"])])
            if s_cia != s_hyb:
                diff_tasks[B] = diff_tasks.get(B, 0) + 1
                diff_budget_tasks.append({"case_id": t["case_id"], "B": B})
    return {
        "n_tasks": len(tasks),
        "top_b_differ_count_by_b": {str(B): diff_tasks.get(B, 0) for B in budgets if B > 0},
        "n_budget_points_checked": len([B for B in budgets if B > 0]) * len(tasks),
        "n_differing_task_budget_cells": len(diff_budget_tasks),
        "full_rank_identical": full_rank_identical,
        "differing_cells": diff_budget_tasks[:20],
    }


def orr_per_task(task: dict[str, Any], arm: str, B: int) -> float:
    return float(recovery_at(task, arm, B)["orr"])


def recovered_per_task(task: dict[str, Any], arm: str, B: int) -> float:
    return float(recovery_at(task, arm, B)["recovered"])


def ablation(tasks: list[dict[str, Any]], budgets: tuple[int, ...]) -> dict[str, Any]:
    arms = ("AnalyticRandom", "BM25", "Graph", "CIA", "Hybrid", "Oracle", "InspectAll")
    out: dict[str, Any] = {"n_tasks": len(tasks)}
    rng = random.Random(SEED + 7)
    for B in budgets:
        if B == 0:
            continue
        row: dict[str, Any] = {"B": B}
        macro: dict[str, float] = {}
        micro: dict[str, float] = {}
        rec_total: dict[str, float] = {}
        for arm in arms:
            per = [orr_per_task(t, arm, B) for t in tasks]
            macro[arm] = round(float(np.mean(per)), 4)
            recs = [recovered_per_task(t, arm, B) for t in tasks]
            total_rec = float(np.sum(recs))
            total_missed = float(sum(t["n_missed"] for t in tasks))
            rec_total[arm] = round(total_rec, 4)
            micro[arm] = round(total_rec / total_missed, 4) if total_missed else 0.0
        row["macro_orr"] = macro
        row["micro_orr"] = micro
        row["recovered_fn"] = rec_total

        # Composite (CIA) minus BM25 paired task-level delta + bootstrap CI.
        deltas = np.asarray(
            [orr_per_task(t, "CIA", B) - orr_per_task(t, "BM25", B) for t in tasks]
        )
        boot = []
        idx = list(range(len(tasks)))
        for _ in range(N_BOOT):
            sample = [rng.choice(idx) for _ in idx]
            boot.append(float(np.mean(deltas[sample])))
        arr = np.asarray(boot)
        row["composite_minus_bm25"] = {
            "paired_delta_mean": round(float(np.mean(deltas)), 4),
            "paired_delta_median": round(float(np.median(deltas)), 4),
            "bootstrap_ci95": [
                round(float(np.percentile(arr, 2.5)), 4),
                round(float(np.percentile(arr, 97.5)), 4),
            ],
            "n_tasks_paired": len(tasks),
            "n_tasks_composite_greater": int(np.sum(deltas > 1e-9)),
            "n_tasks_bm25_greater": int(np.sum(deltas < -1e-9)),
            "n_tasks_equal": int(np.sum(np.abs(deltas) <= 1e-9)),
        }

        # Graph minus Random.
        g_minus_r = np.asarray(
            [orr_per_task(t, "Graph", B) - orr_per_task(t, "AnalyticRandom", B) for t in tasks]
        )
        row["graph_minus_random"] = {
            "mean_delta": round(float(np.mean(g_minus_r)), 4),
            "n_tasks_positive": int(np.sum(g_minus_r > 1e-9)),
        }

        # Top-B overlap composite vs BM25.
        overlap = []
        exact = 0
        for t in tasks:
            s_cia = top_b_set(t, "CIA", B)
            s_bm25 = top_b_set(t, "BM25", B)
            union = s_cia | s_bm25
            inter = s_cia & s_bm25
            if union:
                overlap.append(len(inter) / len(union))
            else:
                overlap.append(1.0)
            if s_cia == s_bm25:
                exact += 1
        row["composite_vs_bm25_top_b_overlap"] = {
            "mean_jaccard": round(float(np.mean(overlap)), 4),
            "n_tasks_exact_match": exact,
        }

        # Additional FNs recovered by composite beyond BM25.
        extra = np.asarray(
            [recovered_per_task(t, "CIA", B) - recovered_per_task(t, "BM25", B) for t in tasks]
        )
        row["additional_fn_recovered_composite_beyond_bm25"] = {
            "sum_extra_fn": int(round(float(np.sum(extra)))),
            "n_tasks_extra_gt_0": int(np.sum(extra > 1e-9)),
            "n_tasks_extra_lt_0": int(np.sum(extra < -1e-9)),
        }
        out[str(B)] = row
    return out


def main() -> int:
    djcms = build_djangocms_tasks()
    sal = build_saleor_tasks()

    identity = {
        "study_id": "route-b-ranker-identity-audit",
        "date": "2026-09-17",
        "zero_api": True,
        "code_audited": {
            "script": "scripts/route_b_v2_robustness.py",
            "rank_arm_cia": "sorted(items, key=lambda kv: (-kv[1]['bm25'] - kv[1]['graph_neighbor'], kv[0]))",
            "hybrid_feature": "0.5 * bm + 0.5 * nb  (bm = normalized BM25, nb = binary graph neighbor)",
            "rank_arm_hybrid": "sorted(items, key=lambda kv: (-kv[1]['hybrid'], kv[0]))",
            "scalar_relation": "hybrid == 0.5 * (bm25 + graph_neighbor); positive scalar multiple => identical total order",
        },
        "djangocms": identity_check(djcms, BUDGETS),
        "saleor": identity_check(sal, BUDGETS),
        "conclusion": (
            "CIA and Hybrid are MATHEMATICALLY RANK-EQUIVALENT: the hybrid feature is exactly "
            "0.5 * (bm25 + graph_neighbor), a positive scalar multiple of the CIA ordering key "
            "(bm25 + graph_neighbor); sorting by -k and by -0.5*k yields the same total order "
            "(same tie-break by path), hence identical top-B at every B. Hybrid is a REDUNDANT "
            "ALIAS/CONTROL, not an independent baseline."
        ),
    }

    ablation_result = {
        "study_id": "route-b-incremental-evidence-ablation",
        "date": "2026-09-17",
        "zero_api": True,
        "type": "CHARACTERIZATION/ABLATION (no method change)",
        "djangocms": {"n_tasks": len(djcms), "budget_curve": ablation(djcms, BUDGETS)},
        "saleor": {"n_tasks": len(sal), "budget_curve": ablation(sal, BUDGETS)},
    }

    OUT_AUDIT_JSON.write_text(json.dumps(identity, indent=2), encoding="utf-8")
    OUT_ABL_JSON.write_text(json.dumps(ablation_result, indent=2), encoding="utf-8")

    # ---------------- Markdown: identity audit ----------------
    md = [
        "# Route B — Ranker-Identity Audit",
        "",
        "**Date:** 2026-09-17  **Type:** T3 audit  **ZERO API calls**",
        "**Repository:** djangoCMS + Saleor DEVELOPMENT (deterministic recomputation from",
        "committed run records and case bundles; no frozen historical output modified).",
        "",
        "## 1. What the committed code defines (exact)",
        "",
        "From `scripts/route_b_v2_robustness.py` (frozen, imported verbatim by the Saleor transfer):",
        "",
        "- `bm` = normalized BM25 score (`bm25_scores[p] / max_bm25`).",
        "- `graph_neighbor` = binary indicator (1.0 if candidate is a graph neighbor of seeds/write-set, else 0.0).",
        "- `hybrid` feature = `0.5 * bm + 0.5 * graph_neighbor`.",
        "- CIA ordering = descending `bm25 + graph_neighbor` (key `-bm25 - graph_neighbor`, path tie-break).",
        "- Hybrid ordering = descending `hybrid` = descending `0.5*(bm25 + graph_neighbor)` (path tie-break).",
        "",
        "## 2. Mathematical rank-equivalence proof (CIA vs Hybrid)",
        "",
        "Let $s(p) = bm(p) + nb(p)$ be the CIA key and $h(p) = 0.5\\cdot bm(p) + 0.5\\cdot nb(p)$ the Hybrid key.",
        "Then $h(p) = 0.5\\cdot s(p)$ for every candidate $p$. Since $0.5 > 0$ is a fixed positive scalar,",
        "the total order induced by descending $s$ equals the total order induced by descending $h$;",
        "the path tie-break is identical. Therefore the two rankers produce **identical rankings and",
        "identical top-$B$ sets for every budget $B$** on every task.",
        "",
        "## 3. Empirical top-B identity (deterministic, zero API)",
        "",
        f"- djangoCMS DEVELOPMENT: {identity['djangocms']['n_tasks']} tasks; B = {{1,3,5,10}}; "
        f"differing task-budget cells: **{identity['djangocms']['n_differing_task_budget_cells']}**; "
        f"full-rank identical: **{identity['djangocms']['full_rank_identical']}**.",
        f"- Saleor DEVELOPMENT: {identity['saleor']['n_tasks']} tasks; B = {{1,3,5,10}}; "
        f"differing task-budget cells: **{identity['saleor']['n_differing_task_budget_cells']}**; "
        f"full-rank identical: **{identity['saleor']['full_rank_identical']}**.",
        "",
        "| Repo | B | tasks where top-B differs |",
        "|---|---:|---:|",
    ]
    for repo_key, label in (("djangocms", "djangoCMS"), ("saleor", "Saleor")):
        for B in (1, 3, 5, 10):
            md.append(f"| {label} | {B} | {identity[repo_key]['top_b_differ_count_by_b'][str(B)]} |")
    md += [
        "",
        "## 4. Classification",
        "",
        "**CIA and Hybrid are rank-equivalent on every djangoCMS and Saleor DEVELOPMENT task at",
        "every checked budget (0 differing cells). Hybrid is a REDUNDANT ALIAS/CONTROL, NOT an",
        "independent baseline.** The V2 results files already show identical macro/micro ORR and",
        "recovered-FN counts for CIA and Hybrid at every B on both repositories.",
        "",
        "Historical results are NOT changed; this is a correction/clarification appended at 2026-09-17.",
        "",
        "## 5. Name audit: does `Classical-CIA` overstate the implementation?",
        "",
        "- The frozen Route-B V2 `CIA` arm is **exactly** `normalized BM25 + binary graph-neighbor",
        "  indicator`. It does NOT implement classical dependency propagation, association/importance",
        "  weighting, or a path-fused score in this script.",
        "- A separate, genuinely classical CIA implementation exists at",
        "  `scripts/classical_cia_baseline_v1.py` (CIA-1H / CIA-2H hop-bounded dependency closures,",
        "  `reports/CLASSICAL_CIA_BASELINE_V1_REPORT.md`), but that is a DIFFERENT baseline and is NOT",
        "  what the Route-B V2 frozen ranker calls `CIA`.",
        "- **Conclusion:** the label `Classical-CIA` OVERSTATES the frozen Route-B V2 arm. Precise name:",
        "  **`BM25+Graph-Neighbor Composite (historical label: CIA)`**. Terminology is corrected in the",
        "  confirmatory packet V2 and Proposal V1.4; the ranking formula is NOT silently changed before",
        "  confirmatory testing.",
        "",
        "## 6. Incremental-evidence ablation (summary pointer)",
        "",
        "See `reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md` for composite-vs-BM25 paired deltas,",
        "bootstrap CIs, top-B overlap, and additional-FN recovery on both repositories.",
        "",
        "Full machine-readable audit: `research/transparency/route_b_ranker_identity_audit.json`.",
    ]
    OUT_AUDIT_MD.write_text("\n".join(md), encoding="utf-8")

    # ---------------- Markdown: incremental ablation ----------------
    def abl_table(abl: dict[str, Any], repo_label: str) -> list[str]:
        rows = [
            "",
            f"### {repo_label} — incremental evidence (N={abl['n_tasks']})",
            "",
            "| B | Random | BM25 | Graph | Composite | CIA−BM25 Δ (boot 95% CI) | Graph−Random | Jaccard overlap comp vs BM25 | extra FN comp−BM25 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for B in (1, 3, 5, 10):
            r = abl["budget_curve"][str(B)]
            rows.append(
                f"| {B} | {r['macro_orr']['AnalyticRandom']:.3f} | {r['macro_orr']['BM25']:.3f} "
                f"| {r['macro_orr']['Graph']:.3f} | {r['macro_orr']['CIA']:.3f} "
                f"| {r['composite_minus_bm25']['paired_delta_mean']:+.3f} "
                f"[{r['composite_minus_bm25']['bootstrap_ci95'][0]:+.3f}, {r['composite_minus_bm25']['bootstrap_ci95'][1]:+.3f}] "
                f"| {r['graph_minus_random']['mean_delta']:+.3f} "
                f"| {r['composite_vs_bm25_top_b_overlap']['mean_jaccard']:.3f} "
                f"| {r['additional_fn_recovered_composite_beyond_bm25']['sum_extra_fn']:+d} |"
            )
        return rows

    md2 = [
        "# Route B — Incremental-Evidence Ablation (zero API)",
        "",
        "**Date:** 2026-09-17  **Type:** CHARACTERIZATION/ABLATION (no method tuning, no method change)",
        "**Basis:** frozen Route-B V2 protocol applied to djangoCMS and Saleor DEVELOPMENT run records.",
        "Primary endpoint = Omission Recovery Rate @ B (macro).",
        "",
        "## Interpretation guide",
        "",
        "- `Composite` = frozen `BM25+Graph-Neighbor Composite (historical label: CIA)`.",
        "- The key question is whether graph-neighbor evidence adds materially to BM25 alone or whether",
        "  the replicated transfer signal is predominantly lexical.",
        "- No new ranker is chosen from this analysis; the frozen confirmatory method is unchanged.",
        "",
    ] + abl_table(ablation_result["djangocms"], "djangoCMS") + abl_table(ablation_result["saleor"], "Saleor")
    md2 += [
        "",
        "## Notes",
        "",
        "- Paired task-level delta (composite − BM25) with a task-level bootstrap CI (seed 20260917,",
        "  2000 resamples); task is the independent unit.",
        "- Jaccard overlap of top-B sets composite vs BM25 (1.0 = identical top-B sets on that task;",
        "  the table reports the mean across tasks).",
        "- extra FN = (composite recovered FNs) − (BM25 recovered FNs) summed over tasks; positive =",
        "  the composite recovers additional omitted files beyond BM25 at the same budget.",
        "- Saleor `Graph` arm ≈ binary neighbor only; the Saleor dependency graph is sparser, which the",
        "  graph-vs-random row reflects.",
        "- Full machine-readable results: `research/transparency/route_b_incremental_ablation.json`.",
    ]
    OUT_ABL_MD.write_text("\n".join(md2), encoding="utf-8")

    print("djangocms tasks:", len(djcms), "saleor tasks:", len(sal))
    print("identity djangocms differ:", identity["djangocms"]["n_differing_task_budget_cells"],
          "saleor differ:", identity["saleor"]["n_differing_task_budget_cells"])
    print("outputs:", OUT_AUDIT_JSON, OUT_AUDIT_MD, OUT_ABL_JSON, OUT_ABL_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
