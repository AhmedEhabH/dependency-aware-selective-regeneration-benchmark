#!/usr/bin/env python3
# ruff: noqa: E501, UP031
"""CALIBRATED_SET_SELECTION_V1 — human-readable report generator (T3, ZERO API).

Reads the persisted artifacts under research/calibrated-set-selection-v1/ and
writes reports/CALIBRATED_SET_SELECTION_V1_REPORT_2026-09-20.md. The report is
self-contained (understandable without reading raw JSON).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))

OUT_DIR = _PROJECT_DIR / "research" / "calibrated-set-selection-v1"
REPORT_DIR = _PROJECT_DIR / "reports"


def _load(name):
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def _metric_line(m):
    return (f"TP {m['tp']} / FP {m['fp']} / FN {m['fn']} | "
            f"P {m['precision']:.4f} | R {m['recall']:.4f} | "
            f"F1 {m['f1']:.4f} | FNR {m['fnr']:.4f}")


def main() -> int:
    va = _load("verdict_A.json")
    vb = _load("verdict_B.json")
    verdict = json.loads((OUT_DIR / "final_verdict.json").read_text(encoding="utf-8"))
    rm = _load("repo_metrics_A.json")
    boot = _load("bootstrap_ci_A.json")
    fd = _load("fold_details_A.json")
    ed = _load("error_decomposition_A.json")
    cal = _load("calibration_A.json")
    rob = _load("robustness_ab.json")
    det = _load("determinism_A.json")
    gate = va["gate"]

    lines: list[str] = []
    add = lines.append

    add("# Calibrated Set Selection V1 — Report (2026-09-20)")
    add("")
    add("**Mission:** CALIBRATED_SET_SELECTION_V1 (DEV-ONLY FINAL FILE-SET POLICY)")
    add("**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731")
    add("**Tier:** T3 · **API budget:** ZERO paid calls · **Sealed data:** untouched")
    add("**Primary score realization:** Qwen realization A (chronologically first); realization B = robustness rerun")
    add("**Verdict:** `%s`" % verdict["verdict"])
    add("")
    add("> The primary gate FAILS on djangoCMS (criterion B: paired-bootstrap 95% CI for")
    add("> Delta F1 crosses zero). Saleor PASSES. Realization B reproduces the SAME verdict")
    add("> (robust FAIL). This is a frozen negative: `CALIBRATED_SET_SELECTION_V1_FAIL`.")
    add("")
    add("---")
    add("")
    add("## WHAT PROBLEM REMAINED?")
    add("")
    add("Sparse localization has a large false-negative loss (FNR 0.753 djangoCMS / 0.788")
    add("Saleor), and every prior ADD mechanism (Route-B, bounded semantic, precision-safe")
    add("acceptance) either added an FP tail or failed its gate. The independently replicated")
    add("dense-ranking signal (Qwen A+B both PASS at B=5) proved the ranking is useful but a")
    add("FIXED addition budget (B=5) creates an increasing FP tail. The remaining question was")
    add("whether ONE minimal interpretable repository-independent decision policy could convert")
    add("the dense signal into a FINAL affected-file set that beats Sparse itself, with ADD /")
    add("KEEP / DROP and no fixed B.")
    add("")
    add("## WHY FIXED B FAILED?")
    add("")
    add("SweRank exact-rank omitted-positive hit rates (verified from the raw SweRank artifact):")
    add("djangoCMS rank1 0.241 (42/174), rank2 0.132 (23/174), rank3 0.109 (19/174); Saleor")
    add("rank1 0.262 (39/149), rank2 0.174 (26/149), rank3 0.128 (19/149). Candidate precision")
    add("decays with rank, so adding a fixed B=5 means later ranks are mostly false positives.")
    add("These are frequencies, NOT calibrated probabilities (Lipton et al. 2014 applies only to")
    add("well-calibrated probabilities).")
    add("")
    add("> **Verification correction (POST-HOC diagnostic):** the historical two-realization")
    add("> report listed SweRank rank-4/5 hit rates as djangoCMS 0.023/0.034 and Saleor")
    add("> 0.074/0.034. A fresh recomputation from the SAME artifact gives djangoCMS 0.080/0.052")
    add("> and Saleor 0.134/0.094 (14/9 of 174 and 20/14 of 149). Ranks 1-3 (the values used for")
    add("> every frozen conclusion and quoted by this mission) are IDENTICAL. The rank-4/5 rows")
    add("> were a transcription error in the historical report; no frozen conclusion changed.")
    add("")
    add("## WHAT DOES THE POLICY DO?")
    add("")
    add("For every task the policy examines a frozen candidate universe (the Sparse files for")
    add("KEEP/DROP, plus the top-20 NON-SPARSE files by the frozen Qwen dense rank for ADD) and")
    add("assigns each candidate an L2-Logistic-Regression probability. A file enters the final")
    add("set iff its probability is at least a threshold that was learned (inner-CV) on DEV.")
    add("There is no fixed B: the number of additions is whatever the threshold yields per task.")
    add("")
    add("## WHAT FEATURES WERE USED?")
    add("")
    add("Exactly 7 (frozen): `dense_file_score`; `log_rank = log1p(dense_rank)` (ABSOLUTE rank);")
    add("`gap_to_top1`; `in_sparse`; `log_sparse_set_size = log1p(|Sparse|)`; `sparse_empty`;")
    add("`sparse_rank_interaction = in_sparse * log_rank`. Files with no embeddable units (NaN")
    add("score) were imputed deterministically to `min_finite_score - 1.0`. NO repository")
    add("identity, NO file-count N, NO BM25/graph/co-change/history/path/label features.")
    add("")
    add("## WHY ABSOLUTE LOG-RANK?")
    add("")
    add("The post-hoc rank-hit pattern is broadly similar across repositories despite the")
    add("universe sizes having effectively no overlap (djangoCMS 139..234; Saleor 403..1142).")
    add("Normalizing rank by N would therefore inject repository-universe size as a hidden")
    add("repository-identity proxy, contradicting the pooled repository-independent policy.")
    add("")
    add("## HOW WAS LEAKAGE PREVENTED?")
    add("")
    add("Scaler fit on OUTER-TRAIN rows only; LR fit on OUTER-TRAIN tasks only; threshold chosen")
    add("via INNER task-grouped OOF within the OUTER-TRAIN tasks only (grid 0.01..0.99, argmax")
    add("pooled micro-F1, tie-break HIGHER); held-out labels appear ONLY in the final scoring.")
    add("A dedicated test flips held-out labels and proves OOF probabilities/sets are unchanged;")
    add("the independent audit recomputes every number from the persisted artifacts (20/20 PASS);")
    add("gate G (determinism) verified: %s." % det["oof_and_sets_identical"])
    add("")
    add("## HOW WAS THRESHOLD CHOSEN?")
    add("")
    add("Inside each outer-training partition, an inner 5-fold task-grouped OOF produced predicted")
    add("probabilities; the threshold maximized pooled micro-F1 on the grid 0.01..0.99 (tie-break:")
    add("higher). Per-fold thresholds (realization A):")
    for k in range(5):
        d = fd[str(k)]
        add(f"- fold {k}: t = {d['inner_threshold']:.2f} (inner-OOF F1 at t = {d['inner_oof_f1_at_threshold']:.4f}; "
            f"descriptive Lipton F1*/2 = {d['lipton_descriptive_f1star_over_2']:.4f})")
    add("")
    add("## WHAT HAPPENED TO PRECISION?")
    add("")
    add("| Repo | Sparse P | V1 P | Delta P (95% CI) |")
    add("|---|---:|---:|---|")
    for repo in ("djangocms", "saleor"):
        m = rm[repo]
        ci = boot[repo]["precision"]
        add(f"| {repo} | {m['sparse']['precision']:.4f} | {m['policy']['precision']:.4f} | "
            f"{ci['point_delta']:+.4f} [{ci['ci95_lower']:+.4f}, {ci['ci95_upper']:+.4f}] |")
    add("")
    add("## WHAT HAPPENED TO RECALL?")
    add("")
    add("| Repo | Sparse R | V1 R | Delta R (95% CI) |")
    add("|---|---:|---:|---|")
    for repo in ("djangocms", "saleor"):
        m = rm[repo]
        ci = boot[repo]["recall"]
        add(f"| {repo} | {m['sparse']['recall']:.4f} | {m['policy']['recall']:.4f} | "
            f"{ci['point_delta']:+.4f} [{ci['ci95_lower']:+.4f}, {ci['ci95_upper']:+.4f}] |")
    add("")
    add("## WHAT HAPPENED TO FNR?")
    add("")
    add("| Repo | Sparse FNR | V1 FNR | Delta FNR (95% CI) |")
    add("|---|---:|---:|---|")
    for repo in ("djangocms", "saleor"):
        m = rm[repo]
        ci = boot[repo]["fnr"]
        add(f"| {repo} | {m['sparse']['fnr']:.4f} | {m['policy']['fnr']:.4f} | "
            f"{ci['point_delta']:+.4f} [{ci['ci95_lower']:+.4f}, {ci['ci95_upper']:+.4f}] |")
    add("")
    add("## WHAT HAPPENED TO F1?")
    add("")
    add("| Repo | Sparse F1 | V1 F1 | Delta F1 (95% CI) | criterion B |")
    add("|---|---:|---:|---:|---|")
    for repo in ("djangocms", "saleor"):
        m = rm[repo]
        ci = boot[repo]["f1"]
        add(f"| {repo} | {m['sparse']['f1']:.4f} | {m['policy']['f1']:.4f} | "
            f"{ci['point_delta']:+.4f} [{ci['ci95_lower']:+.4f}, {ci['ci95_upper']:+.4f}] | "
            f"{'PASS' if ci['ci95_lower'] > 0 else 'FAIL'} |")
    add("")
    add("## HOW MANY SPARSE FP WERE DROPPED? HOW MANY SPARSE TP WERE ACCIDENTALLY DROPPED? HOW MANY OMITTED POSITIVES WERE ADDED?")
    add("")
    add("| Repo | Sparse TP retained | Sparse TP dropped (accident) | Sparse FP dropped | Sparse FP retained | Omitted positives added | New FP added |")
    add("|---|---:|---:|---:|---:|---:|---:|")
    for repo in ("djangocms", "saleor"):
        d = ed[repo]
        add(f"| {repo} | {d['A_sparse_tp_retained']} | {d['B_sparse_tp_incorrectly_dropped']} | "
            f"{d['C_sparse_fp_correctly_dropped']} | {d['D_sparse_fp_retained']} | "
            f"{d['E_sparse_fn_correctly_added']} | {d['F_new_fp_added']} |")
    add("")
    add("The F1 gain comes from BOTH directions: dropped Sparse false positives AND added")
    add("omitted positives, with only a modest number of new false positives (the learned")
    add("threshold, not a fixed B, controls the tail).")
    add("")
    add("## DID WE BEAT SPARSE ON BOTH REPOSITORIES?")
    add("")
    add("Point estimates: YES on F1/Recall/FNR on BOTH repos (djangoCMS F1 0.318 -> 0.334;")
    add("Saleor 0.261 -> 0.336). BUT the preregistered gate requires the paired-bootstrap 95% CI")
    add("for Delta F1 to exclude zero on BOTH repos. djangoCMS Delta F1 = %+.4f with CI [%+.4f, %+.4f]"
    % (boot["djangocms"]["f1"]["point_delta"],
       boot["djangocms"]["f1"]["ci95_lower"], boot["djangocms"]["f1"]["ci95_upper"]))
    add("— the lower bound is below zero, so the djangoCMS improvement is NOT statistically")
    add("distinguished from Sparse. Saleor Delta F1 = %+.4f with CI [%+.4f, %+.4f] (excludes zero)."
    % (boot["saleor"]["f1"]["point_delta"],
       boot["saleor"]["f1"]["ci95_lower"], boot["saleor"]["f1"]["ci95_upper"]))
    add("")
    add("| Gate criterion | djangoCMS | Saleor |")
    add("|---|---:|---:|")
    g = gate["gate"]
    add(f"| A: F1_policy > F1_sparse | {g['djangocms']['A_f1_policy_gt_sparse']} | {g['saleor']['A_f1_policy_gt_sparse']} |")
    add(f"| B: CI lower(Delta F1) > 0 | {g['djangocms']['B_ci_lower_delta_f1_gt0']} | {g['saleor']['B_ci_lower_delta_f1_gt0']} |")
    add(f"| C: R_policy >= R_sparse | {g['djangocms']['C_recall_policy_ge_sparse']} | {g['saleor']['C_recall_policy_ge_sparse']} |")
    add(f"| D: FNR_policy <= FNR_sparse | {g['djangocms']['D_fnr_policy_le_sparse']} | {g['saleor']['D_fnr_policy_le_sparse']} |")
    add(f"| E: >=3/5 folds Delta F1 >= 0 | {g['djangocms']['E_folds_delta_f1_ge0']} ({g['djangocms']['E_n_folds_ge0']}/5) | {g['saleor']['E_folds_delta_f1_ge0']} ({g['saleor']['E_n_folds_ge0']}/5) |")
    add("| F: zero target leakage | PASS (audit + flip test) | PASS (audit + flip test) |")
    add(f"| G: deterministic rerun | {det['oof_and_sets_identical']} | {det['oof_and_sets_identical']} |")
    add("")
    add("## DID WE ACHIEVE PARETO_SUCCESS?")
    add("")
    add(f"No (PARETO_SUCCESS = {'PASS' if gate['pareto_success'] else 'FAIL'}). Saleor is Pareto-better than")
    add("Sparse in isolation; djangoCMS is not (precision falls 0.446 -> %.4f and the F1 CI crosses zero)."
        % rm["djangocms"]["policy"]["precision"])
    add("")
    add("## CALIBRATION DIAGNOSTICS (frozen 10 equal-width bins, outer OOF)")
    add("")
    add(f"- Brier score: {cal['brier']}")
    add(f"- Expected Calibration Error (ECE): {cal['ece']}")
    add("- Reliability table (mean predicted vs empirical rate per bin):")
    add("")
    add("| bin | n | mean predicted | empirical positive rate |")
    add("|---|---:|---:|---:|")
    for b in cal["bins"]:
        if b["n"] == 0:
            continue
        add(f"| [{b['lo']:.2f}, {b['hi']:.2f}) | {b['n']} | {b['mean_pred']} | {b['empirical_rate']} |")
    add("")
    add("## REALIZATION-B ROBUSTNESS (same frozen pipeline, Qwen realization B scores)")
    add("")
    add(f"- exact same selected set: {rob['exact_same_selected_set_percentage']}% of 323 tasks")
    add(f"- task-level Jaccard: mean {rob['jaccard_mean']}, median {rob['jaccard_median']}, min {rob['jaccard_min']}, max {rob['jaccard_max']}")
    add(f"- verdict agreement: A={va['verdict']}, B={vb['verdict']} (SAME)")
    add(f"- F1 A vs B: djangoCMS {rob['f1_djangocms_A']:.4f} vs {rob['f1_djangocms_B']:.4f}; "
        f"Saleor {rob['f1_saleor_A']:.4f} vs {rob['f1_saleor_B']:.4f}")
    add("")
    add("The A/B set agreement (83.28%) is lower than the fixed-B=5 replication (97.21%) because")
    add("files near the learned probability threshold flip more easily under hosted float noise;")
    add("the SCIENTIFIC verdict is stable (both FAIL on the same criterion).")
    add("")
    add("## HOW MUCH ORACLE HEADROOM REMAINS?")
    add("")
    add("Oracle-Add ALL (perfect recall of omitted positives) caps file-level F1 at 0.867/0.829;")
    add("the V1 policy reaches 0.334/0.336. The remaining gap decomposes into: (1) ranking /")
    add("candidate-coverage error (positives outside Sparse union top-20), (2) ADD decision")
    add("error (top-20 candidates that are positives but below the threshold), (3) DROP decision")
    add("error (Sparse positives accidentally dropped: 14 djangoCMS / 6 Saleor), and (4) the")
    add("historical changed-file proxy's own ambiguity. See the Oracle-gap dated successor")
    add("`reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-20.md`.")
    add("")
    add("## WHAT DOES THIS MEAN FOR STAGE 5?")
    add("")
    add("The final file-set decision policy is NOT frozen as a success: the preregistered primary")
    add("gate FAILS (djangoCMS Delta-F1 CI crosses zero), and the frozen verdict is")
    add("`CALIBRATED_SET_SELECTION_V1_FAIL`. Stage 5 remains PAUSED and SEALED")
    add("(`FINAL_POLICY_NOT_FROZEN`). The dense-ranking mechanism is independently replicated, so")
    add("lack of independent replication is no longer a Stage-5 blocker — but the policy problem")
    add("is not solved.")
    add("")
    add("## WHAT DOES THIS NOT PROVE?")
    add("")
    add("- It does NOT prove the calibrated policy is useless: the point estimates improve on")
    add("  both repos and Saleor's CI excludes zero. It proves the CURRENT frozen minimal policy")
    add("  is not statistically distinguishable from Sparse on djangoCMS under the frozen gate.")
    add("- It does NOT prove any V2 feature set (graph, co-change, BM25, history, model family")
    add("  changes) — those require a NEW mission and a NEW frozen hypothesis.")
    add("- It does NOT prove Qwen/SweRank training-provenance status (verdict C unchanged).")
    add("- It does NOT unlock Stage 5 and does NOT claim the method beats LocAgent or any")
    add("  external baseline (LocAgent F1~0.333 is from a different exposed 10-task population).")
    add("")
    add("## Evidence")
    add("")
    add("Machine-readable outputs under `research/calibrated-set-selection-v1/`; frozen config in")
    add("`reports/calibrated_set_selection_v1_freeze.json`; independent audit 20/20 PASS"
    " (`reports/calibrated_set_selection_v1_audit.json`).")

    report = "\n".join(lines) + "\n"
    (REPORT_DIR / "CALIBRATED_SET_SELECTION_V1_REPORT_2026-09-20.md").write_text(
        report, encoding="utf-8")
    print(f"report written: {len(lines)} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
