"""Omission-Risk Feature Study V1 — analysis driver (deterministic, ZERO LLM).

Goal: evaluate whether cheap observable signals predict elevated false-negative
risk of the deterministic first pass (metadata-corpus BM25@K) on TRAIN/
VALIDATION, WITHOUT observing hidden reference files during feature extraction,
WITHOUT new LLM calls, and WITHOUT touching HELD_OUT_TEST.

Outputs (research/omission-risk-feature-study-v1/):
- feature_table.csv
- feature_manifest.json
- single_feature_results.json
- adaptive_k_results.json
- cost_sensitive_analysis.json
- raw_task_level_inputs.json
- study_results_summary.json

Statistical unit = task. Development evidence only.
"""

from __future__ import annotations

import csv
import json
import random
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from benchmark.harness.djangocms import DjangoCMSRealCommitDataset
from benchmark.harness.interfaces import BudgetPolicy
from benchmark.harness.spec import ExperimentSpec
from benchmark.omission_risk import adaptive_k, cost, labels, metrics
from benchmark.omission_risk.features import (
    K_GRID,
    compute_scores,
    extract_features,
    feature_names,
    feature_specs,
)

DATASET_DIR_DEFAULT = Path("benchmark_data/real_commit_impact_v1")
OUTPUT_DIR_DEFAULT = Path("research/omission-risk-feature-study-v1")
BOOTSTRAP_SEED = 20260916


def build_spec() -> ExperimentSpec:
    return ExperimentSpec(
        spec_id="omission-risk-feature-study-v1",
        protocol_version="omission-risk-feature-study-v1",
        dataset_name="djangocms-real-commit-v1",
        repository="djangocms",
        method_name="omission-risk-feature-study",
        model_name="",
        provider="none",
        k_values=K_GRID,
        splits_allowed=("TRAIN", "VALIDATION"),
        seed=BOOTSTRAP_SEED,
        budget=BudgetPolicy(zero_llm=True),
        frozen_rules=(
            "TRAIN+VALIDATION ONLY; HELD_OUT_TEST forbidden (fail closed)",
            "zero LLM calls",
            "first pass = metadata-corpus BM25@K (registered stand-in)",
            "primary label K_ref=10; K in {3,5} sensitivity",
            "labels and features fixed before any performance observation",
        ),
        notes="Omission-risk feature study V1 (development evidence only)",
    )


def collect_task_table(
    dataset_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Iterate TRAIN+VALIDATION; return (rows, raw_by_split)."""
    ds = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)
    rows: list[dict[str, Any]] = []
    raw: dict[str, list[dict[str, Any]]] = {"TRAIN": [], "VALIDATION": []}
    for cid in ds.case_ids():
        split = ds.split_of(cid)
        case = ds.load_public_case(cid)
        t_feat = time.perf_counter()
        feats = extract_features(case)
        extract_s = time.perf_counter() - t_feat
        index, scores = compute_scores(case)
        desc_scores = [scores[d] for d in sorted(scores, key=lambda p: (-scores[p], p))]
        first_pass = {
            k: set(index.rank(case.intent_text, k=k)) for k in (1, 3, 5, 10)
        }
        proxy = ds.load_hidden_proxy_paths(cid)  # evaluation-time only
        lbl = labels.task_labels(
            case=case, first_pass_by_k=first_pass, proxy_paths=proxy
        )
        row: dict[str, Any] = {"case_id": cid, "split": split}
        row.update(feats)
        row["_extract_s"] = extract_s
        for k in K_GRID:
            row[f"has_fn_k{k}"] = lbl[f"has_fn_k{k}"]
            row[f"fn_count_k{k}"] = lbl[f"fn_count_k{k}"]
            row[f"fn_rate_k{k}"] = lbl[f"fn_rate_k{k}"]
            row[f"severity_k{k}"] = lbl[f"severity_k{k}"]
        row["proxy_size"] = lbl["proxy_size"]
        rows.append(row)
        raw[split].append(
            {
                "case_id": cid,
                "split": split,
                "intent_text": case.intent_text,
                "parent_commit": case.parent_commit,
                "n_candidates": len(case.candidate_paths),
                "graph_edges": len(case.graph_edges),
                "proxy_paths": list(proxy),
                "first_pass_top10": sorted(first_pass[10]),
                "desc_bm25_scores": desc_scores,
                "labels": {k: lbl[f"has_fn_k{k}"] for k in K_GRID},
                "extraction_seconds": extract_s,
            }
        )
    rows.sort(key=lambda r: r["case_id"])
    for split_rows in raw.values():
        split_rows.sort(key=lambda r: r["case_id"])
    return rows, raw


def _mean(x: Sequence[float]) -> float:
    return float(np.mean(list(x))) if x else 0.0


def _std(x: Sequence[float]) -> float:
    return float(np.std(list(x))) if x else 0.0


def _median(x: Sequence[float]) -> float:
    return float(np.median(list(x))) if x else 0.0


def _quantile(x: Sequence[float], q: float) -> float:
    return float(np.quantile(list(x), q)) if x else 0.0


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _risk_vector(rows: list[dict[str, Any]], fname: str) -> list[float]:
    return [float(r[fname]) for r in rows]


def _label_vector(rows: list[dict[str, Any]], kref: int) -> list[int]:
    return [int(r[f"has_fn_k{kref}"]) for r in rows]


def evaluate_feature(
    rows: list[dict[str, Any]], fname: str, kref: int
) -> dict[str, Any]:
    """Single-feature evaluation with task-level bootstrap + uncertainty."""
    risk = _risk_vector(rows, fname)
    y = _label_vector(rows, kref)
    v = [x for x in risk]
    has1 = [v[i] for i in range(len(y)) if y[i] == 1]
    has0 = [v[i] for i in range(len(y)) if y[i] == 0]
    b = metrics.bootstrap_ci(risk, y, metrics.auprc, seed=BOOTSTRAP_SEED)
    return {
        "feature": fname,
        "k_ref": kref,
        "n": len(rows),
        "n_pos": sum(y),
        "prevalence": sum(y) / len(y) if y else 0.0,
        "auroc": metrics.auroc(risk, y),
        "auroc_signed": metrics.auroc_direction(risk, y),
        "auprc": metrics.auprc(risk, y),
        "auprc_bootstrap": b,
        "recall_at_budget": metrics.recall_at_budget(risk, y),
        "risk_coverage": metrics.risk_coverage(risk, y),
        "dist_mean": _mean(v),
        "dist_median": _median(v),
        "dist_iqr": [_quantile(v, 0.25), _quantile(v, 0.75)],
        "dist_hasfn1_mean": _mean(has1),
        "dist_hasfn0_mean": _mean(has0) if has0 else 0.0,
        "dist_hasfn1_count": len(has1),
    }


def _train_test(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train = [r for r in rows if r["split"] == "TRAIN"]
    valid = [r for r in rows if r["split"] == "VALIDATION"]
    return train, valid


def minmax_bound(
    train: list[dict[str, Any]], fname: str
) -> tuple[float, float]:
    vals = [float(r[fname]) for r in train]
    return (min(vals), max(vals)) if vals else (0.0, 1.0)


def std_score(train: list[dict[str, Any]], fname: str, value: float) -> float:
    lo, hi = minmax_bound(train, fname)
    span = hi - lo or 1.0
    return (value - lo) / span


def run_single_feature_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for kref in K_GRID:
        out[f"k{kref}"] = {}
        for fname in feature_names():
            out[f"k{kref}"][fname] = evaluate_feature(rows, fname, kref)
    return out


def run_baselines(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """R0 random (frozen seeds), R1 density, R2 validate-count (deferred),
    R3 BM25 uncertainty, R4 disagreement, R5 graph frontier."""
    rng = random.Random(BOOTSTRAP_SEED)
    r0_vecs: dict[int, list[float]] = {k: [] for k in K_GRID}
    for _ in range(50):
        risk = [rng.random() for _ in rows]
        for kref in K_GRID:
            y = _label_vector(rows, kref)
            r0_vecs[kref].append(metrics.auroc(risk, y))

    def r1(r: dict[str, Any]) -> float:
        return float(r["fp_density_k10"])

    def r2(_r: dict[str, Any]) -> float:
        return 0.0  # constant: VALIDATE count of a deterministic first pass

    def r3(r: dict[str, Any]) -> float:
        return float(r["bm25_top10_norm_entropy"])

    def r4(r: dict[str, Any]) -> float:
        return 1.0 - float(r["disagree_jaccard_graph_k10"])

    def r5(r: dict[str, Any]) -> float:
        return float(r["graph_1hop_frontier_size"])

    baselines: dict[str, Callable[[dict[str, Any]], float]] = {
        "R1_first_pass_density": r1,
        "R2_validate_count_deferred": r2,
        "R3_bm25_uncertainty": r3,
        "R4_disagreement": r4,
        "R5_graph_frontier": r5,
    }
    out: dict[str, Any] = {}
    for kref in K_GRID:
        y = _label_vector(rows, kref)
        out[f"k{kref}"] = {}
        for name, fn in baselines.items():
            risk = [fn(r) for r in rows]
            out[f"k{kref}"][name] = {
                "auroc": metrics.auroc(risk, y),
                "auroc_signed": metrics.auroc_direction(risk, y),
                "auprc": metrics.auprc(risk, y),
                "recall_at_budget": metrics.recall_at_budget(risk, y),
                "prevalence": sum(y) / len(y) if y else 0.0,
            }
        out[f"k{kref}"]["R0_random"] = {
            "auroc_mean": _mean(r0_vecs[kref]),
            "auroc_sd": _std(r0_vecs[kref]),
            "n_seeds": 50,
        }
    return out


# Pre-declared single interpretable combination (registered BEFORE analysis):
#   retrieval uncertainty (bm25_top10_norm_entropy)
#   + Sparse-BM25 disagreement (1 - Jaccard(BM25@10, Graph@10))
#   + one structural signal (graph 1-hop frontier size)
# Equal-weight min-max standardized sum, bounds from TRAIN only.
COMBO_FEATURES: tuple[str, ...] = (
    "bm25_top10_norm_entropy",
    "disagree_jaccard_graph_k10",
    "graph_1hop_frontier_size",
)


def combo_risk(
    train: list[dict[str, Any]],
    row_or_val: dict[str, Any],
    fname: str,
) -> float:
    base = float(row_or_val[fname])
    score = std_score(train, fname, base)
    if fname == "disagree_jaccard_graph_k10":
        return 1.0 - score  # lower Jaccard -> higher risk
    return score


def run_combination(rows: list[dict[str, Any]]) -> dict[str, Any]:
    train, valid = _train_test(rows)
    out: dict[str, Any] = {"description": "equal-weight standardized sum", "k": {}}
    for kref in K_GRID:
        tr_risks: list[float] = []
        va_risks: list[float] = []
        for r in train:
            tr_risks.append(
                combo_risk(train, r, COMBO_FEATURES[0])
                + combo_risk(train, r, COMBO_FEATURES[1])
                + combo_risk(train, r, COMBO_FEATURES[2])
            )
        for r in valid:
            va_risks.append(
                combo_risk(train, r, COMBO_FEATURES[0])
                + combo_risk(train, r, COMBO_FEATURES[1])
                + combo_risk(train, r, COMBO_FEATURES[2])
            )
        y_tr = _label_vector(train, kref)
        y_va = _label_vector(valid, kref)
        out["k"][f"k{kref}"] = {
            "train": {
                "auroc": metrics.auroc(tr_risks, y_tr),
                "auroc_signed": metrics.auroc_direction(tr_risks, y_tr),
                "auprc": metrics.auprc(tr_risks, y_tr),
                "recall_at_budget": metrics.recall_at_budget(tr_risks, y_tr),
                "n": len(train),
            },
            "validation": {
                "auroc": metrics.auroc(va_risks, y_va),
                "auroc_signed": metrics.auroc_direction(va_risks, y_va),
                "auprc": metrics.auprc(va_risks, y_va),
                "recall_at_budget": metrics.recall_at_budget(va_risks, y_va),
                "n": len(valid),
            },
        }
    return out


def run_calibration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    train, valid = _train_test(rows)
    out: dict[str, Any] = {}
    for kref in K_GRID:
        risk_t = _risk_vector(train, "bm25_top10_norm_entropy")
        risk_v = _risk_vector(valid, "bm25_top10_norm_entropy")
        y_t = _label_vector(train, kref)
        y_v = _label_vector(valid, kref)
        out[f"k{kref}"] = {
            "platt": metrics.calibration_report(
                y_train=y_t, risk_train=risk_t, y_eval=y_v, risk_eval=risk_v,
                method="platt",
            ),
            "isotonic": metrics.calibration_report(
                y_train=y_t, risk_train=risk_t, y_eval=y_v, risk_eval=risk_v,
                method="isotonic",
            ),
        }
    return out


def run_cost_sensitivity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    train, valid = _train_test(rows)
    out: dict[str, Any] = {}
    for kref in K_GRID:
        risk_t = _risk_vector(train, "bm25_top10_norm_entropy")
        y_t = _label_vector(train, kref)
        fn_pos = [
            int(r[f"fn_count_k{kref}"]) for r in train if r[f"has_fn_k{kref}"] == 1
        ]
        fn_pos_mean = _mean(fn_pos) if fn_pos else 0.0
        probs_v = metrics._platt_calibration(
            risk_t, y_t, _risk_vector(valid, "bm25_top10_norm_entropy")
        )
        prob_score = {r["case_id"]: float(p) for r, p in zip(valid, probs_v, strict=True)}
        risk_score = {r["case_id"]: r["bm25_top10_norm_entropy"] for r in valid}
        has_fn = {r["case_id"]: int(r[f"has_fn_k{kref}"]) for r in valid}
        out[f"k{kref}"] = cost.analyze_cost_sensitivity(
            risk_score=risk_score,
            prob_score=prob_score,
            has_fn=has_fn,
            fn_pos_mean=fn_pos_mean,
        )
    return out


def run_adaptive_k_analysis(
    rows: list[dict[str, Any]], dataset_dir: Path
) -> dict[str, Any]:
    train, valid = _train_test(rows)
    # Sorted scores per case (from the raw persisted inputs, deterministic).
    raw_path = OUTPUT_DIR_DEFAULT / "raw_task_level_inputs.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    all_cases = raw["TRAIN"] + raw["VALIDATION"]
    scores_by_case = {c["case_id"]: c["desc_bm25_scores"] for c in all_cases}
    proxy_by_case = {c["case_id"]: set(c["proxy_paths"]) for c in all_cases}
    ds = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)
    ranked_by_case_k: dict[tuple[str, int], list[str]] = {}
    for c in all_cases:
        case = ds.load_public_case(c["case_id"])
        index, _ = compute_scores(case)
        for k in (3, 10):
            ranked_by_case_k[(c["case_id"], k)] = list(
                index.rank(case.intent_text, k=k)
            )
    out: dict[str, Any] = {}
    for rule in adaptive_k.ADAPTIVE_RULES:
        out[rule] = {
            "TRAIN": adaptive_k.evaluate_rule(
                rule,
                sorted_scores_by_case=scores_by_case,
                ranked_by_case_k=ranked_by_case_k,
                case_ids=[r["case_id"] for r in train],
                proxy_by_case=proxy_by_case,
            ),
            "VALIDATION": adaptive_k.evaluate_rule(
                rule,
                sorted_scores_by_case=scores_by_case,
                ranked_by_case_k=ranked_by_case_k,
                case_ids=[r["case_id"] for r in valid],
                proxy_by_case=proxy_by_case,
            ),
        }
    return out


def _jaccard(parent_selected: set[str], frozen_selected: set[str]) -> float:
    return (
        len(parent_selected & frozen_selected)
        / len(parent_selected | frozen_selected)
        if (parent_selected | frozen_selected)
        else 1.0
    )


def frozen_agreement_diagnostic(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Metadata-corpus BM25@K vs frozen parent-corpus BM25@K agreement.

    Diagnostic only: quantifies how much the registered metadata retrieval
    stage diverges from the frozen Protocol-A parent-commit BM25 stage.
    """
    frozen_path = Path("research/cheap-baselines-v1/raw_predictions_v1.json")
    if not frozen_path.exists():
        return {"status": "frozen evidence not present", "agree_jaccard": None}
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    frozen_by_case: dict[str, dict[int, set[str]]] = {}
    for c in frozen["cases"]:
        sel: dict[int, set[str]] = {}
        for r in c["results"]:
            if r["baseline"] == "bm25" and r["k"] in (3, 5, 10):
                sel[int(r["k"])] = set(r["selected_paths"])
        frozen_by_case[c["case_id"]] = sel
    diagnostics: dict[str, Any] = {}
    total_j: dict[int, list[float]] = {k: [] for k in (3, 5, 10)}
    for r in rows:
        cid = r["case_id"]
        if cid not in frozen_by_case:
            continue
        # recompute metadata-corpus top-K for the case
        ds = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR_DEFAULT)
        case = ds.load_public_case(cid)
        index, _ = compute_scores(case)
        for k in (3, 5, 10):
            meta_sel = set(index.rank(case.intent_text, k=k))
            frozen_sel = frozen_by_case[cid].get(k, set())
            j = _jaccard(meta_sel, frozen_sel)
            total_j[k].append(j)
            diagnostics.setdefault(cid, {})[f"jaccard_meta_vs_frozen_k{k}"] = j
    return {
        "status": "ok",
        "mean_jaccard": {str(k): _mean(total_j[k]) for k in (3, 5, 10)},
        "per_case": diagnostics,
    }


def run_study(
    *,
    dataset_dir: Path = DATASET_DIR_DEFAULT,
    output_dir: Path = OUTPUT_DIR_DEFAULT,
    write_raw: bool = True,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    t_start = time.perf_counter()
    rows, raw = collect_task_table(dataset_dir)
    collect_seconds = time.perf_counter() - t_start

    spec = build_spec()
    manifest: dict[str, Any] = {
        "study_id": "OMISSION_RISK_FEATURE_STUDY_V1",
        "spec": spec.to_dict(),
        "spec_sha256": spec.sha256,
        "label_definition": (
            "has_fn(t;K)=1 iff first-pass BM25@K omits >=1 proxy-positive "
            "file; primary K_ref=10; K in {3,5} sensitivity; task-level unit."
        ),
        "first_pass_definition": (
            "metadata-corpus BM25@K (module+classes+functions); zero LLM; "
            "Sparse-LLM action features DEFERRED; historical/evolutionary "
            "features DEFERRED (no repo cache, zero-LLM principle)."
        ),
        "strict_data_rule": (
            "TRAIN 24 + VALIDATION 6 only; HELD_OUT_TEST 10 forbidden; "
            "labels computed at evaluation time from the observed proxy."
        ),
        "zero_llm_calls": True,
        "dataset_dir": str(dataset_dir),
        "output_dir": str(output_dir),
        "n_tasks": len(rows),
        "n_train": sum(1 for r in rows if r["split"] == "TRAIN"),
        "n_validation": sum(1 for r in rows if r["split"] == "VALIDATION"),
        "collect_seconds": collect_seconds,
        "feature_schema": [
            {
                "name": s.name,
                "family": s.family,
                "description": s.description,
                "k_dependent": s.k_dependent,
            }
            for s in feature_specs()
        ],
    }

    # Feature table csv
    fieldnames = ["case_id", "split", "_extract_s"] + feature_names() + [
        f"{p}_k{k}" for k in K_GRID for p in ("has_fn", "fn_count", "fn_rate", "severity")
    ] + ["proxy_size"]
    csv_path = output_dir / "feature_table.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in fieldnames})

    (output_dir / "feature_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if write_raw:
        (output_dir / "raw_task_level_inputs.json").write_text(
            json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    single = run_single_feature_analysis(rows)
    baselines = run_baselines(rows)
    combos = run_combination(rows)
    cal = run_calibration(rows)
    cost_res = run_cost_sensitivity(rows)
    adaptive = run_adaptive_k_analysis(rows, dataset_dir)
    frozen_diag = frozen_agreement_diagnostic(rows)
    rng_band = random_auroc_band(rows)
    fam_summary = family_summary(single)
    vs_random = signal_vs_random(single, rng_band)

    (output_dir / "single_feature_results.json").write_text(
        json.dumps(single, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "adaptive_k_results.json").write_text(
        json.dumps(adaptive, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "cost_sensitive_analysis.json").write_text(
        json.dumps(cost_res, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary = {
        "n_tasks": len(rows),
        "prevalence_by_k": {
            str(k): (sum(r[f"has_fn_k{k}"] for r in rows) / len(rows))
            for k in K_GRID
        },
        "single_feature_top_by_auprc": _top_features(single),
        "random_auroc_band": rng_band,
        "family_summary": fam_summary,
        "signal_vs_random": vs_random,
        "baselines": baselines,
        "combinations": combos,
        "calibration": cal,
        "cost_sensitive": cost_res,
        "adaptive_k_summary": {
            rule: {
                spl: {
                    "avg_k": adaptive[rule][spl]["avg_k"],
                    "f1": adaptive[rule][spl]["f1"],
                    "fnr": adaptive[rule][spl]["fnr"],
                    "recall": adaptive[rule][spl]["recall"],
                }
                for spl in ("TRAIN", "VALIDATION")
            }
            for rule in adaptive_k.ADAPTIVE_RULES
        },
        "frozen_agreement_diagnostic": frozen_diag,
        "zero_llm_calls": True,
    }
    (output_dir / "study_results_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def _top_features(single: dict[str, Any], k: int = 10, limit: int = 8) -> list[dict[str, Any]]:
    feats = single[f"k{k}"]
    rr = []
    for fname, res in feats.items():
        if "__" in fname:
            continue
        rr.append(
            {
                "feature": fname,
                "auprc": res["auprc"],
                "auroc": res["auroc"],
                "auroc_signed": res["auroc_signed"],
                "auprc_ci95": [
                    res["auprc_bootstrap"]["ci95_low"],
                    res["auprc_bootstrap"]["ci95_high"],
                ],
            }
        )
    rr.sort(key=lambda d: -d["auprc"])
    return rr[:limit]


def random_auroc_band(
    rows: list[dict[str, Any]], n_seeds: int = 2000, seed: int = BOOTSTRAP_SEED
) -> dict[str, Any]:
    """Random-risk AUROC distribution per K (noise band for n=30)."""
    rng = random.Random(seed)
    out: dict[str, Any] = {}
    for kref in K_GRID:
        y = _label_vector(rows, kref)
        vals: list[float] = []
        for _ in range(n_seeds):
            risk = [rng.random() for _ in rows]
            vals.append(metrics.auroc(risk, y))
        out[f"k{kref}"] = {
            "mean": _mean(vals),
            "sd": _std(vals),
            "q2_5": _quantile(vals, 0.025),
            "q50": _quantile(vals, 0.5),
            "q97_5": _quantile(vals, 0.975),
            "n_seeds": n_seeds,
        }
    return out


def family_summary(single: dict[str, Any]) -> dict[str, Any]:
    """Aggregate single-feature AUROC/AUPRC by feature family."""
    fam_by_name = {s.name: s.family for s in feature_specs()}
    out: dict[str, Any] = {}
    for kref in K_GRID:
        fam: dict[str, list[float]] = {}
        for fname, res in single[f"k{kref}"].items():
            fam_name = fam_by_name.get(fname)
            if fam_name is None:
                continue
            fam.setdefault(fam_name, []).append(res["auroc_signed"])
        out[f"k{kref}"] = {
            fam_name: {
                "n_features": len(vals),
                "auroc_signed_mean": _mean(vals),
                "auroc_signed_max_abs": float(max(abs(v) for v in vals)) if vals else 0.0,
            }
            for fam_name, vals in sorted(fam.items())
        }
    return out


def signal_vs_random(
    single: dict[str, Any], rng_band: dict[str, Any]
) -> dict[str, Any]:
    """Classify each feature as within/above the random AUROC band (2.5-97.5%).

    Discrimination strength is measured as |AUROC - 0.5|; the random band is
    the same distance for the random-risk AUROC distribution.
    """
    out: dict[str, Any] = {}
    for kref in K_GRID:
        band = rng_band[f"k{kref}"]
        radius = max(abs(band["q2_5"] - 0.5), abs(band["q97_5"] - 0.5))
        above: list[str] = []
        for fname, res in single[f"k{kref}"].items():
            signed = res["auroc_signed"]
            if abs(signed - 0.5) > radius:
                above.append(fname)
        out[f"k{kref}"] = {
            "band": [band["q2_5"], band["q97_5"]],
            "radius": radius,
            "n_features": len(single[f"k{kref}"]),
            "n_above_random_95": len(above),
            "features_above_random_95": sorted(above),
        }
    return out
