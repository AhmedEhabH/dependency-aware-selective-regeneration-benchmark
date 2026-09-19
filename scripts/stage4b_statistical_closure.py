#!/usr/bin/env python3
# ruff: noqa: E501
"""STAGE-4B STATISTICAL CLOSURE — POST-HOC DESCRIPTIVE DEVELOPMENT ANALYSIS.

Recomputes the frozen precision-safe-acceptance pilot (P67,
PRECISION_SAFE_ACCEPTANCE_FAIL) at the reference budget B=5 as a PAIRED
TASK-LEVEL comparison of Arm B (RANK->VERIFY->VARIABLE ACCEPT) minus Arm A
(frozen Route-B verifier), with >=10,000 task-paired bootstrap resamples and a
fixed seed.

This is DESCRIPTIVE UNCERTAINTY ANALYSIS ONLY. It does NOT change the
preregistered P67 verdict or the frozen gate.

Metrics (definitions in src/benchmark/signal/metrics.py):
  - macro ORR            mean_i(ORR_i), ORR_i = recovered_i / missed_i
  - final Precision      pooled TP/(TP+FP) over the resampled tasks
  - final Recall         pooled TP/(TP+FN)
  - final F1             2TP/(2TP+FP+FN)
  - final FNR            pooled FN/(TP+FN)
  - candidate precision  pooled correct recovered / accepted additions

For each metric reports: point estimate (Arm A, Arm B, delta), absolute and
relative delta, 95% paired-bootstrap CI, n tasks, and TP/FP/FN per arm.

ALSO: explains the djangoCMS phenomenon (pooled TP/FP/FN, Precision, Recall,
F1, FNR improve while Macro ORR declines) from raw task-level data.

Outputs:
  - reports/STAGE4B_STATISTICAL_CLOSURE_2026-09-19.md
  - reports/stage4b_bootstrap_ci.json
  - research/strong-localization-signal/stage4b/task_level.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.signal.metrics import (  # noqa: E402
    METRIC_NAMES,
    confusion,
    orr,
    p_r_f1_fnr,
    paired_bootstrap,
)

RESULT_JSON = _PROJECT_DIR / "research" / "precision-safe-acceptance-pilot" / "pilot_results.json"
V1_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
V2_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SALEOR_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"

B_REF = 5
N_RESAMPLES = 10_000
SEED = 20260919
REPOS = ("djangocms", "saleor")

OUT_MD = _PROJECT_DIR / "reports" / "STAGE4B_STATISTICAL_CLOSURE_2026-09-19.md"
OUT_JSON = _PROJECT_DIR / "reports" / "stage4b_bootstrap_ci.json"
OUT_TASKS = _PROJECT_DIR / "research" / "strong-localization-signal" / "stage4b" / "task_level.json"


def _fn_paths(task) -> set[str]:
    return {c["path"] for c in task.candidates if c["is_missed_positive"]}


def _load_tasks():
    tasks = load_dev_tasks()
    by_cid = {t.case_id: t for t in tasks}
    data = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
    records = data["records"]
    arm_a = [r for r in records if r["stage"] == "arm_a_verifier" and r["B"] == B_REF]
    rank = [r for r in records if r["stage"] == "rank"]
    return by_cid, arm_a, rank


def _arm_contribs(by_cid, records, which: str) -> dict[str, dict]:
    """Per-task contributions for each arm, keyed by case_id.

    For each task returns:
      tp, fp, fn       pooled final-set confusion (write_set UNION additions)
      recovered, missed  ORR inputs
      cand_fn, cand_sel  candidate-precision inputs
      additions, fn_additions (for the phenomenon diagnosis)
    """
    out: dict[str, dict] = {}
    for r in records:
        cid = r["case_id"]
        t = by_cid[cid]
        pos = set(t.proxy)
        fn_set = _fn_paths(t)
        if which == "A":
            sel = set(r["verifier_selected"])
            rec = set(r["verifier_recovered"])
        else:
            per_b = r.get("per_b", {}).get(str(B_REF), {})
            sel = set(per_b.get("additions", []))
            rec = set(per_b.get("recovered", []))
        final = set(t.write_set) | sel
        tp, fp, fn = confusion(final, pos)
        out[cid] = {
            "tp": tp, "fp": fp, "fn": fn,
            "recovered": len(rec), "missed": t.n_missed,
            "cand_fn": len(sel & fn_set), "cand_sel": len(sel),
            "additions": sorted(sel), "fn_additions": sorted(sel & fn_set),
            "fn_paths": t.fn_paths,
            "n_missed": t.n_missed,
        }
    return out


def main() -> int:
    by_cid, arm_a, rank = _load_tasks()
    contrib_a = _arm_contribs(by_cid, arm_a, "A")
    contrib_b = _arm_contribs(by_cid, rank, "B")

    results: dict = {"reference_budget": B_REF, "n_resamples": N_RESAMPLES,
                     "seed": SEED, "label": "POST-HOC DESCRIPTIVE DEVELOPMENT ANALYSIS",
                     "verdict_unchanged": "PRECISION_SAFE_ACCEPTANCE_FAIL",
                     "repos": {}}
    md = [
        "# Stage 4b Statistical Closure (POST-HOC DESCRIPTIVE DEVELOPMENT ANALYSIS)",
        "",
        f"**Date:** 2026-09-19  **Reference budget:** B={B_REF}  **Resamples:** {N_RESAMPLES} (task-paired, fixed seed {SEED})",
        "",
        "**The preregistered Stage-4b verdict is UNCHANGED and immutable: "
        "`PRECISION_SAFE_ACCEPTANCE_FAIL` (P67).** This document adds descriptive "
        "uncertainty analysis ONLY — it does NOT reopen or reinterpret the frozen gate.",
        "",
        "**Metric definitions (used in every relevant report from 2026-09-19 on):**",
        "",
        "```",
        "Precision            P  = TP / (TP + FP)",
        "Recall               R  = TP / (TP + FN)",
        "False Negative Rate  FNR = FN / (TP + FN) = 1 - R",
        "F1                   F1 = 2TP / (2TP + FP + FN)",
        "Candidate precision  = correct recovered omitted positives / all accepted recovery candidates",
        "ORR per task i       ORR_i = recovered omitted positives_i / omitted positives_i",
        "                        (0 when the task has no omitted positives — frozen macro convention)",
        "Macro ORR            mean_i(ORR_i)",
        "95% paired bootstrap CI: Delta_b = Metric_B_b - Metric_A_b;",
        "                        CI95 = [quantile_2.5%(Delta), quantile_97.5%(Delta)];",
        "                        bootstrap unit = TASK (never individual files).",
        "```",
        "",
    ]

    task_level: dict[str, dict] = {}
    for repo in REPOS:
        ids_a = sorted(c for c in contrib_a if by_cid[c].repository == repo)
        ids_b = sorted(c for c in contrib_b if by_cid[c].repository == repo)
        ids = sorted(set(ids_a) & set(ids_b))
        ca = [contrib_a[i] for i in ids]
        cb = [contrib_b[i] for i in ids]

        # metric contribution tuples, aligned per task
        tuples_a: dict[str, list] = {m: [] for m in METRIC_NAMES}
        tuples_b: dict[str, list] = {m: [] for m in METRIC_NAMES}
        for ta, tb in zip(ca, cb, strict=True):
            tuples_a["macro_orr"].append((orr(ta["recovered"], ta["missed"]),))
            tuples_b["macro_orr"].append((orr(tb["recovered"], tb["missed"]),))
            for m in ("final_precision", "final_recall", "final_f1", "final_fnr"):
                tuples_a[m].append((ta["tp"], ta["fp"], ta["fn"]))
                tuples_b[m].append((tb["tp"], tb["fp"], tb["fn"]))
            tuples_a["candidate_precision"].append((ta["cand_fn"], ta["cand_sel"]))
            tuples_b["candidate_precision"].append((tb["cand_fn"], tb["cand_sel"]))

        repo_metrics = {}
        for m in METRIC_NAMES:
            ci = paired_bootstrap(tuples_a[m], tuples_b[m], m, N_RESAMPLES, SEED)
            repo_metrics[m] = ci
        results["repos"][repo] = {"n_tasks": len(ids), "metrics": repo_metrics}

        # pooled TP/FP/FN per arm
        pa = p_r_f1_fnr(sum(t["tp"] for t in ca), sum(t["fp"] for t in ca), sum(t["fn"] for t in ca))
        pb = p_r_f1_fnr(sum(t["tp"] for t in cb), sum(t["fp"] for t in cb), sum(t["fn"] for t in cb))
        task_level[repo] = {
            "case_ids": ids,
            "arm_a": [{"case_id": i, **c} for i, c in zip(ids, ca, strict=True)],
            "arm_b": [{"case_id": i, **c} for i, c in zip(ids, cb, strict=True)],
        }

        md += [
            f"## {repo} DEV — Stage 4b pilot @B=5 (n = {len(ids)} tasks, paired)",
            "",
            "### Pooled file-level confusion per arm",
            "",
            "| Arm | TP | FP | FN | Precision | Recall | F1 | FNR |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
            f"| A (Route-B verifier) | {pa['tp']} | {pa['fp']} | {pa['fn']} | {pa['precision']:.4f} | {pa['recall']:.4f} | {pa['f1']:.4f} | {pa['fnr']:.4f} |",
            f"| B (RANK->VERIFY) | {pb['tp']} | {pb['fp']} | {pb['fn']} | {pb['precision']:.4f} | {pb['recall']:.4f} | {pb['f1']:.4f} | {pb['fnr']:.4f} |",
            "",
            "### Arm B minus Arm A — point estimates and 95% paired-task-bootstrap CIs",
            "",
            "| Metric | A | B | delta (abs) | delta (rel) | CI95 lower | CI95 upper | excludes 0 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for m in METRIC_NAMES:
            ci = repo_metrics[m]
            rel = (ci["point_delta"] / ci["point_arm_a"]) if ci["point_arm_a"] else None
            rel_s = f"{rel:.2%}" if rel is not None else "n/a (A=0)"
            md.append(
                f"| {m} | {ci['point_arm_a']:.4f} | {ci['point_arm_b']:.4f} | "
                f"{ci['point_delta']:+.4f} | {rel_s} | {ci['ci95_lower']:.4f} | "
                f"{ci['ci95_upper']:.4f} | {ci['ci95_excludes_zero']} |"
            )
        md.append("")

    md += _phenomenon_section(contrib_a, contrib_b, by_cid)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_TASKS.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    OUT_TASKS.write_text(json.dumps(task_level, indent=2), encoding="utf-8")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print("wrote:", OUT_JSON, OUT_TASKS, OUT_MD)
    return 0


def _phenomenon_section(contrib_a, contrib_b, by_cid) -> list[str]:
    """Explain WHY djangoCMS pooled TP/FP/FN + P/R/F1/FNR improve while Macro ORR declines."""
    lines = [
        "## The djangoCMS phenomenon: pooled TP/FP/FN improve while Macro ORR declines — why",
        "",
        "**Observed fact (frozen pilot):** on djangoCMS @B=5 the Arm-B final set has"
        " *more* TP, *fewer* FP and *fewer* FN than Arm A (pooled P/R/F1/FNR all"
        " improve), yet the Arm-B Macro ORR (0.1523) is *below* Arm A (0.2225)."
        " Macro ORR and pooled Recall/F1 can move in opposite directions; this"
        " is expected under the definitions:",
        "",
        "1. **Macro ORR is a per-task ratio averaged over tasks; pooled Recall is a"
        "   global ratio over pooled positives.**",
        "   - ORR_i = recovered_i / missed_i. Tasks with a large missed set `missed_i`"
        "     contribute little to the macro; tasks with a tiny missed set (e.g. a"
        "     single FN, `missed_i = 1`) dominate the macro when the arm recovers"
        "     that single FN. Arm A recovered the single FN on **three M=1 tasks**;"
        "     Arm B instead approved a *different* non-FN candidate on those tasks,"
        "     producing three `delta_i = -1.0` per-task ORR deltas that dominate the"
        "     macro average.",
        "   - Pooled Recall pools *all* proxy positives first and divides the pooled"
        "     recovered count. A task with a large FN set carries proportionally more"
        "     weight there, so recovering a few positives on large-FN tasks moves"
        "     pooled Recall even when it does not fix the small-M tasks.",
        "2. **The FP/TP composition differs.** The conservative verifier in Arm B"
        "   accepts fewer candidates overall (40 vs 64 selected on djangoCMS @B=5),"
        "   cutting the FP tail (candidate precision 0.1406 -> 0.2500) while still"
        "   recovering the same net number of FNs (9 -> 10). Fewer FPs and more TPs"
        "   at the pooled level directly raise P, R, F1 and lower FNR.",
        "3. **Mechanism verification (from the raw task-level record).** The per-task"
        "   deltas at B=5 (djangoCMS) are dominated by the M=1 recovery pattern:",
        "",
    ]

    dc_ids = sorted(c for c in contrib_a if by_cid[c].repository == "djangocms")
    m1_rows = []
    for cid in dc_ids:
        a = contrib_a[cid]
        b = contrib_b[cid]
        if a["n_missed"] == 1:
            a_ok = a["recovered"]
            b_ok = b["recovered"]
            m1_rows.append((cid, a_ok, b_ok, a["additions"], b["additions"]))
    if m1_rows:
        lines += [
            "| case_id (M=1) | Arm A recovered | Arm B recovered | Arm A additions | Arm B additions |",
            "|---|---:|---:|---|---|---|",
        ]
        for cid, ao, bo, aa, ba in sorted(m1_rows):
            lines.append(f"| {cid} | {ao} | {bo} | {','.join(aa) or '-'} | {','.join(ba) or '-'} |")
    else:
        lines.append("(no M=1 tasks found in the djangoCMS sample)")
    lines += [
        "",
        "4. **Conclusion.** The decline in Macro ORR on djangoCMS is a *macro-vs-pooled"
        "   weighting artifact of the conservative verifier over-rejecting the easy"
        "   single-FN recoveries*, not a sign that the Arm-B final set is worse at the"
        "   file level. The preregistered gate (P67) used Macro ORR as a decisive"
        "   criterion on BOTH repos, so the pilot correctly FAILED under its own"
        "   protocol. This explanation is POST-HOC and descriptive; it does not alter",
        "   `PRECISION_SAFE_ACCEPTANCE_FAIL`.",
        "",
    ]
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
