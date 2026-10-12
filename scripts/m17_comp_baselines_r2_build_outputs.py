#!/usr/bin/env python3
# ruff: noqa: E501
"""M17_COMP_BASELINES_R2 — build final deliverables.

Reads the execution metrics + bootstrap + agentless prompt sizes and writes:
  BASELINE_EXECUTION_R2.json
  BASELINE_COMPARISON_R2.csv
  BASELINE_COMPARISON_R2.md
  PER_TASK_PAIRED_R2.csv
  REPRODUCIBILITY_RECEIPT_R2.json
(AGENTLESS_STYLE_EXECUTION_ESTIMATE.md is written separately.)
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "research" / "competitor-baselines-r2"

METRICS = json.loads((OUT / "per_task_metrics_r2.json").read_text(encoding="utf-8"))
BOOT = json.loads((OUT / "paired_bootstrap_r2.json").read_text(encoding="utf-8"))
SIZES = json.loads((OUT / "agentless_prompt_sizes_r2.json").read_text(encoding="utf-8"))

FREEZE_SHA256 = "881237ddef31efd66d1f437e861b6d8de9af296dc5ede0eef742b8df9ec1cef9"

ARM_LABELS = {
    "BM25@1": "DIRECT_SAME_PROTOCOL",
    "BM25@3": "DIRECT_SAME_PROTOCOL",
    "BM25@5": "DIRECT_SAME_PROTOCOL",
    "BM25@10": "DIRECT_SAME_PROTOCOL",
    "DENSE@1": "DIRECT_SAME_PROTOCOL",
    "DENSE@3": "DIRECT_SAME_PROTOCOL",
    "DENSE@5": "DIRECT_SAME_PROTOCOL",
    "DENSE@10": "DIRECT_SAME_PROTOCOL",
    "BM25_SIZE_MATCHED": "SIZE_MATCHED_CONTROL",
    "DENSE_SIZE_MATCHED": "SIZE_MATCHED_CONTROL",
    "BM25_TO_CIA_1HOP": "DIRECT_SAME_PROTOCOL",
    "BM25_TO_CIA_2HOP": "DIRECT_SAME_PROTOCOL",
    "C_ORACLE_1HOP": "UPPER_BOUND_ONLY",
    "C_ORACLE_2HOP": "UPPER_BOUND_ONLY",
    "SIP": "FROZEN_MAIN297_ARM",
    "RM-CSS": "FROZEN_MAIN297_ARM",
    "AGENT": "FROZEN_MAIN297_ARM",
}
ARM_NOTES = {
    "DENSE@1": "DENSE_ONLY_ABLATION (frozen qwen/qwen3-embedding-8b realization-A scores reused; RM-CSS classifier consumes this same dense representation)",
    "DENSE@3": "DENSE_ONLY_ABLATION",
    "DENSE@5": "DENSE_ONLY_ABLATION",
    "DENSE@10": "DENSE_ONLY_ABLATION",
    "DENSE_SIZE_MATCHED": "DENSE_ONLY_ABLATION; SIZE_MATCHED_CONTROL",
    "BM25_SIZE_MATCHED": "SIZE_MATCHED_CONTROL; k_t = |RM-CSS output| per task",
    "BM25_TO_CIA_1HOP": "seed = BM25 top-1 (same-protocol); static reverse-dependency closure",
    "BM25_TO_CIA_2HOP": "seed = BM25 top-1; 2-hop closure",
    "C_ORACLE_1HOP": "GOLD_SEEDED; diagnostic bridge to seeded methods (RIPPLE / From Seed to Scope)",
    "C_ORACLE_2HOP": "GOLD_SEEDED",
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()


def main() -> int:
    agg = METRICS["aggregates"]
    eff = METRICS["efficiency"]
    arms = METRICS["arms"]

    # ---------------- BASELINE_EXECUTION_R2.json ----------------
    execution = {
        "protocol_id": "M17_COMP_BASELINES_R2_PROTOCOL_FREEZE",
        "freeze_sha256": FREEZE_SHA256,
        "mission": "M17_COMP_BASELINES_R2_FINAL_CHEAP_SAME_PROTOCOL",
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "population": METRICS["population"],
        "arms": arms,
        "arm_labels": {a: ARM_LABELS[a] for a in arms},
        "arm_notes": {a: ARM_NOTES.get(a, "") for a in arms},
        "aggregates": agg,
        "efficiency": eff,
        "dense_reuse": {
            "artifact": "research/saleor-reserve-300-rmcss/full_file_scores_saleor300.parquet",
            "model": "qwen/qwen3-embedding-8b", "provider": "DeepInfra", "realization": "A",
            "new_api_calls": 0,
            "historical_materialization_cost_usd_300_tasks_INFORMATIONAL": 0.026035,
        },
        "invalid_prediction_count": 0,
        "duplicate_prediction_count": 0,
        "outside_universe_checked": "all 297 tasks x 14 baseline arms; 0 selections outside the frozen candidate universe",
        "swerank_embed_small": {
            "status": "BLOCKED_DOWNLOAD",
            "reason": "model Salesforce/SweRankEmbed-Small (273 MiB) not present in any local cache; new download >100 MiB is prohibited by the mission; the frozen qwen dense artifact path (above) required no download and no new API call",
        },
        "zero_api_statement": "all arms executed in this mission made 0 new LLM/API calls and incurred $0.00 new API cost; computational cost is not zero (wall times above)",
        "paired_bootstrap": BOOT,
    }
    (OUT / "BASELINE_EXECUTION_R2.json").write_text(
        json.dumps(execution, indent=1, sort_keys=True), encoding="utf-8")

    # ---------------- BASELINE_COMPARISON_R2.csv ----------------
    csv_path = OUT / "BASELINE_COMPARISON_R2.csv"
    fields = ["arm", "evaluation_label", "notes", "micro_precision", "micro_recall", "micro_f1",
              "micro_fnr", "macro_precision", "macro_recall", "macro_f1", "mean_size", "median_size",
              "min_size", "max_size", "empty_set_count", "n_tasks",
              "delta_f1_point", "delta_f1_ci025", "delta_f1_ci975", "delta_f1_ci_crosses_zero",
              "delta_recall_point", "delta_recall_ci025", "delta_recall_ci975", "delta_recall_ci_crosses_zero",
              "llm_calls_new", "api_cost_usd_new", "wall_seconds"]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        for a in arms:
            g = agg[a]
            b = BOOT["rows"].get(a, {})
            d1 = b.get("delta_f1_micro", {})
            dr = b.get("delta_recall", {})
            e = eff.get(a, {})
            w.writerow([
                a, ARM_LABELS[a], ARM_NOTES.get(a, "read-only reuse of frozen MAIN_297 evidence" if a in ("SIP", "RM-CSS", "AGENT") else ""),
                f"{g['micro']['precision']:.6f}", f"{g['micro']['recall']:.6f}", f"{g['micro']['f1']:.6f}",
                f"{g['micro']['fnr']:.6f}", f"{g['macro']['precision']:.6f}", f"{g['macro']['recall']:.6f}", f"{g['macro']['f1']:.6f}",
                f"{g['size']['mean']:.4f}", f"{g['size']['median']}", g["size"]["min"], g["size"]["max"],
                g["empty_set_count"], g["n_tasks"],
                "" if not d1 else f"{d1['point']:.6f}", "" if not d1 else f"{d1['q025']:.6f}",
                "" if not d1 else f"{d1['q975']:.6f}", "" if not d1 else str(d1["ci_crosses_zero"]),
                "" if not dr else f"{dr['point']:.6f}", "" if not dr else f"{dr['q025']:.6f}",
                "" if not dr else f"{dr['q975']:.6f}", "" if not dr else str(dr["ci_crosses_zero"]),
                e.get("llm_calls_new", 0), e.get("api_cost_usd_new", 0.0),
                f"{e.get('wall_seconds', 0.0):.3f}",
            ])
    print("wrote", csv_path)

    # ---------------- PER_TASK_PAIRED_R2.csv ----------------
    per_path = OUT / "PER_TASK_PAIRED_R2.csv"
    pf = ["task_id", "gold_size", "universe_size", "rmcss_size"] + \
         [f"{a}_size" for a in arms if a not in ("SIP", "RM-CSS", "AGENT")] + \
         [f"{a}_tp" for a in arms] + [f"{a}_fp" for a in arms] + [f"{a}_fn" for a in arms]
    with per_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(pf)
        baseline_arms = [a for a in arms if a not in ("SIP", "RM-CSS", "AGENT")]
        for tid, row in METRICS["per_task"].items():
            line = [tid, len(row["gold"]), row["universe_size"], row["rmcss_size"]]
            line += [len(row.get(f"{a}_selected", [])) for a in baseline_arms]
            line += [row[f"{a}_confusion"]["tp"] for a in arms]
            line += [row[f"{a}_confusion"]["fp"] for a in arms]
            line += [row[f"{a}_confusion"]["fn"] for a in arms]
            w.writerow(line)
    print("wrote", per_path)

    # ---------------- BASELINE_COMPARISON_R2.md ----------------
    md = build_markdown(agg, arms)
    (OUT / "BASELINE_COMPARISON_R2.md").write_text(md, encoding="utf-8")
    print("wrote", OUT / "BASELINE_COMPARISON_R2.md")

    # ---------------- REPRODUCIBILITY_RECEIPT_R2.json ----------------
    scripts = {
        "scripts/m17_comp_baselines_r2_execute.py": PROJECT / "scripts" / "m17_comp_baselines_r2_execute.py",
        "scripts/m17_comp_baselines_r2_bootstrap.py": PROJECT / "scripts" / "m17_comp_baselines_r2_bootstrap.py",
        "scripts/m17_comp_baselines_r2_agentless_estimate.py": PROJECT / "scripts" / "m17_comp_baselines_r2_agentless_estimate.py",
        "scripts/m17_comp_baselines_r2_build_outputs.py": PROJECT / "scripts" / "m17_comp_baselines_r2_build_outputs.py",
    }
    receipt = {
        "protocol_id": "M17_COMP_BASELINES_R2_PROTOCOL_FREEZE",
        "freeze_sha256": FREEZE_SHA256,
        "branch": execution["branch"],
        "head": execution["head"],
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": __import__("numpy").__version__,
            "pandas": __import__("pandas").__version__,
        },
        "script_sha256": {rel: sha256_file(p) for rel, p in scripts.items()},
        "output_artifact_sha256": {
            rel: sha256_file(OUT / rel)
            for rel in ["BASELINE_PROTOCOL_FREEZE_R2.json", "BASELINE_EXECUTION_R2.json",
                        "BASELINE_COMPARISON_R2.csv", "BASELINE_COMPARISON_R2.md",
                        "PER_TASK_PAIRED_R2.csv", "REPRODUCIBILITY_RECEIPT_R2.json",
                        "per_task_predictions_r2.json", "per_task_metrics_r2.json",
                        "paired_bootstrap_r2.json", "agentless_prompt_sizes_r2.json",
                        "AGENTLESS_STYLE_EXECUTION_ESTIMATE.md"]
            if (OUT / rel).exists()
        },
        "random_seeds": {"bootstrap": 20261012, "sampling_seed_original": 20260920},
        "evaluator_identity": "benchmark.wp1a.scorer.per_task_confusion/ArmConfusion + benchmark.wp1b.main_scoring pooled() (micro P/R/F1/FNR; macro = mean of per-task values with 0 for empty denominators, recorded convention)",
        "main297_manifest_identity": {"artifact": "research/wp1b/wp1b_main_297_manifest.json",
                                       "manifest_sha256": METRICS["population"]["manifest_sha256"]},
        "gold_identity": {"artifact": "research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json",
                          "opened_once": True, "n_tasks": 300, "used_tasks": METRICS["population"]["n_tasks"]},
        "candidate_universe_identity": "per-task benchmark_data/real_commit_impact_saleor/scientific/<id>/public/candidate_universe.json",
        "parent_content_source": "frozen upstream cache repo dist/pilot-repo-cache/saleor (22,615 commits) via git ls-tree -r -z + git cat-file --batch",
        "dense_artifact": "research/saleor-reserve-300-rmcss/full_file_scores_saleor300.parquet (realization A; verified query_sha256 == intent_sha256)",
        "frozen_predictions_reused": {
            "sip_rmcss": "research/wp1a/sip_rmcss_per_task_predictions.json (+ .sha256)",
            "agent": "research/wp1b/main-297-2026-09-22/wp1b_agent_predictions.json (+ .sha256)",
        },
        "verifications": {
            "population_identity": "300 RESERVE - 3 Calibration-3 == MAIN_297 (297)",
            "sip_rmcss_agent_reproduction": "per-task confusion re-derived from frozen predictions exactly matches authoritative wp1b_main297_result.json (SIP 192/341/723; RM-CSS 281/379/634; Agent 291/397/624)",
            "blob_identity": "extracted parent content LF-normalized sha256 matches frozen candidate-universe records (validated before full run; 0/506 on the git-archive-blocked parent; 0 mismatches across the mission)",
            "outside_universe": "0 selections outside the frozen candidate universe across 297 tasks x 14 baseline arms",
            "missing_at_parent": "0 universe files missing at any parent commit",
        },
        "no_paid_api": "0 new LLM/API calls; $0.00 new API cost",
    }
    (OUT / "REPRODUCIBILITY_RECEIPT_R2.json").write_text(
        json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8")
    print("wrote", OUT / "REPRODUCIBILITY_RECEIPT_R2.json")
    return 0


def build_markdown(agg: dict, arms: list[str]) -> str:
    b = BOOT["rows"]
    rows = []
    for a in ["RM-CSS", "SIP", "AGENT"] + [x for x in arms if x not in ("RM-CSS", "SIP", "AGENT")]:
        g = agg[a]
        m = g["micro"]
        rows.append(
            f"| {a} | {ARM_LABELS[a]} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} "
            f"| {m['fnr']:.4f} | {g['macro']['f1']:.4f} | {g['size']['mean']:.2f} "
            f"({g['size']['min']}..{g['size']['max']}) |")
    table = "\n".join(rows)

    boot_rows = []
    for a in ["BM25@1", "BM25@3", "BM25@5", "BM25@10", "DENSE@1", "DENSE@3", "DENSE@5", "DENSE@10",
              "BM25_SIZE_MATCHED", "DENSE_SIZE_MATCHED"]:
        r = b[a]
        d1, dr = r["delta_f1_micro"], r["delta_recall"]
        boot_rows.append(
            f"| RM-CSS − {a} | {r['label']} | {d1['point']:+.4f} | [{d1['q025']:+.4f}, {d1['q975']:+.4f}] "
            f"| {dr['point']:+.4f} | [{dr['q025']:+.4f}, {dr['q975']:+.4f}] |")
    boot_table = "\n".join(boot_rows)

    return f"""# M17 — Cheap Zero-Paid-API Same-Protocol Baselines on MAIN_297 (R2)

**Mission:** `M17_COMP_BASELINES_R2_FINAL_CHEAP_SAME_PROTOCOL`
**Branch:** `{_git('branch','--show-current')}` · **HEAD:** `{_git('rev-parse','HEAD')}`
**Freeze:** `research/competitor-baselines-r2/BASELINE_PROTOCOL_FREEZE_R2.json` SHA256 `{FREEZE_SHA256}`
**Population:** MAIN_297 (297 tasks = RESERVE-300 minus 3 Calibration-3)
**Evaluator:** the exact evaluator used for RM-CSS / SIP / Agent MAIN_297 results
(`benchmark.wp1a.scorer` micro pooling + per-task confusion).

## 1. Frozen protocol and population identity

- Manifest: `research/wp1b/wp1b_main_297_manifest.json` (`manifest_sha256 6bc5980f…fccde`; `task_ids_sha256 1678dbaa…ccbceb`).
- Gold: `research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json` (opened-once observed change-set proxy; all proxy paths inside the frozen candidate universe).
- Candidate universe: per-task `public/candidate_universe.json` (no added exclusions; 0 predictions outside universe).
- Input to methods: exact developer change description (`intent_text`) + repository snapshot at the parent commit; no gold-derived information.
- All parameter decisions (BM25 k1=1.2/b=0.75, DENSE frozen artifact, K ∈ {{1,3,5,10}}, SIZE_MATCHED rule, oracle seed rule, bootstrap seed 20261012) frozen BEFORE any baseline outcome.

## 2. Direct same-protocol results (micro, pooled over 297 tasks)

| Arm | Evaluation label | P | R | F1 | FNR | macro F1 | size mean (min..max) |
|---|---:|---:|---:|---:|---:|---:|---:|
{table}

> DENSE rows additionally carry **DENSE_ONLY_ABLATION** (the frozen RM-CSS classifier consumes exactly this dense representation; ranking quality isolated from the calibrated head).

## 3. Size-matched controls

- `BM25_SIZE_MATCHED`, `DENSE_SIZE_MATCHED`: k_t = number of files selected by the frozen RM-CSS prediction for task t (RM-CSS **output size only**; never reads gold).
- Purpose: separate ranking quality from selection-budget differences. Not presented as independent published competitor implementations.

## 4. Parameter-grid results (pre-specified; no K selected after outcomes)

- BM25@1/3/5/10: F1 0.172 / 0.234 / 0.241 / 0.213 (FNR 0.886 / 0.769 / 0.684 / 0.548).
- DENSE@1/3/5/10: F1 0.195 / 0.275 / 0.268 / 0.225 (FNR 0.871 / 0.729 / 0.648 / 0.522).
- Best direct baseline F1 (0.275 @ DENSE@3) < RM-CSS F1 (0.357).

## 5. Gold-seeded upper bounds (diagnostic)

- `C_ORACLE_1HOP` F1 0.127, `C_ORACLE_2HOP` F1 0.015 (UPPER_BOUND_ONLY / GOLD_SEEDED).
- Reverse-dependency closure is recall-hungry and precision-poor on Saleor (mean set 27 / 373 files); these are **diagnostic** and never enter the headline comparison. They form the bridge to seeded methods such as RIPPLE / From Seed to Scope (also GOLD_SEEDED by definition).

## 6. Paired bootstrap CIs (RM-CSS − baseline; 10,000 resamples over tasks, seed 20261012)

| Comparison | Label | ΔF1 point | ΔF1 95% CI | ΔRecall point | ΔRecall 95% CI |
|---|---:|---:|---:|---:|---:|
{boot_table}

RM-CSS micro-F1 is above **every** direct variant and both size-matched controls with 95% CIs entirely above zero. ΔRecall is positive vs small-K baselines and negative vs K=10 (large set sizes), i.e. the RM-CSS advantage is precision-and-set-size driven.

## 7. Efficiency

- Zero-API arms: **0 new LLM calls, $0.00 new API cost** (all arms). Computational cost is not zero: BM25 full run wall ≈ 250 s (index 42.6 s + query 207.6 s over 297 tasks, local CPU); Phase 2 total wall ≈ 277 s.
- DENSE: frozen-artifact reuse (no new calls; historical materialization $0.026035 for 300 tasks recorded as informational, not this mission's spend).
- Reused frozen arms: SIP (1 call/task, ~5.00M prompt tokens, $1.593 total), RM-CSS, bounded Agent (protocol v3) — evidence frozen, not rerun.

## 8. Agentless-style estimate

See `AGENTLESS_STYLE_EXECUTION_ESTIMATE.md` (official repo `https://github.com/OpenAutoCoder/Agentless` @ `5ce5888b`; prompt source `agentless/fl/FL.py`; offline prompt-size stats; ~$0.7–$1.7 localization-only cost band with the frozen qwen3-coder@deepinfra/turbo price; planned run class = **AGENTLESS_STYLE_ADAPTATION**).

## 9. Blocked / ambiguous arms

- `SweRankEmbed-Small` dense path: **BLOCKED_DOWNLOAD** (model not cached locally; 273 MiB download > 100 MiB prohibited). Mission continued with the frozen qwen dense artifact (zero new download, zero new API call) — see execution JSON.
- No other arm blocked; no BASELINE_PROTOCOL_AMBIGUITY / MISSING_ARTIFACT / EVALUATOR_MISMATCH / NOT_REPRODUCIBLE_WITHOUT_NEW_PROTOCOL.

## 10. Interpretation (no scientific claim change)

- On the frozen MAIN_297 population and the frozen file-level evaluator, the pre-specified cheap zero-API baselines (BM25, dense retrieval, static CIA closure, gold-seeded CIA) do not match RM-CSS micro-F1; the RM-CSS advantage is statistically supported at the 95% level against every direct variant.
- Static reverse-dependency closure (even gold-seeded) performs poorly as a set-selection method here — recall is easy, precision collapses.
- Published Acc@K / Hit@K / MRR / MAP / function-level accuracy / resolve rates from competitor papers are **PUBLISHED_CONTEXT_ONLY** and must never be numerically compared with these micro-F1 numbers (see `research/competitors/COMPETITOR_MATRIX_R1.md` §4).
- RIPPLE / From Seed to Scope is **not run**; any future comparison to it requires a separately frozen seed-generation protocol (e.g., BM25 top-1) and would otherwise be GOLD_SEEDED / UPPER_BOUND_ONLY.
"""


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
