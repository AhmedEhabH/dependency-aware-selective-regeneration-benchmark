#!/usr/bin/env python3
"""Omission-Risk Development Inference — Sparse-v2 label + feature analysis.

Post-run analysis for the frozen DEVELOPMENT-INFERENCE protocol
(docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md):

1. Compute task-level Sparse-v2 ``has_fn`` labels from run records
   (any-FN-over-reps, task unit; pre-registered aggregation).
2. Report N positive / N negative / prevalence BEFORE fitting anything.
3. Class-balance gate: if either class < 10 independent tasks, do NOT fit a
   multivariable RiskScorer; continue with descriptive/single-feature only.
4. Rerun the frozen omission-risk feature analysis using the REAL Sparse-v2
   labels (N=30 tasks, repetitions nested):
   - single-feature AUROC/AUPRC + bootstrap uncertainty
   - Sparse–BM25 disagreement (real Sparse-v2 write set vs BM25@K)
   - retrieval uncertainty (deterministic family A)
   - adaptive-K (deterministic BM25@K rules; unchanged)
   - graph features (family C) — history capability invalid (no git cache)
   - risk-coverage / escalation budgets
   - cost-sensitivity
5. Compare Sparse-v2-label findings vs the deterministic first-pass findings.

Outputs (research/omission-risk-feature-study-v1/sparse_v2_label_analysis/):
  sparse_v2_labels.json            (per-task labels + prevalence)
  sparse_v2_feature_table.csv      (frozen deterministic features + plan features)
  sparse_v2_single_feature_results.json
  sparse_v2_baselines.json
  sparse_v2_combination.json
  sparse_v2_adaptive_k.json
  sparse_v2_cost_sensitive.json
  sparse_v2_risk_coverage.json
  sparse_v2_comparison.json        (vs deterministic first pass)
  sparse_v2_summary.json
"""

# ruff: noqa: E501  (descriptive strings)
from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from benchmark.harness.djangocms import DjangoCMSRealCommitDataset
from benchmark.omission_risk import adaptive_k, cost, metrics
from benchmark.omission_risk.features import (
    K_GRID,
    compute_scores,
    extract_features,
    feature_names,
    feature_specs,
)
from benchmark.omission_risk.study import (
    BOOTSTRAP_SEED,
    COMBO_FEATURES,
    combo_risk,
    run_adaptive_k_analysis,
)

STUDY_DIR = Path("research/omission-risk-feature-study-v1")
OUTPUT_DIR = STUDY_DIR / "sparse_v2_label_analysis"
DATASET_DIR = Path("benchmark_data/real_commit_impact_v1")
RUN_RECORDS = STUDY_DIR / "sparse_v2_trainval_run_records.jsonl"

# Pre-registered Sparse-LLM plan feature names (family F extension, frozen in the
# protocol before any result): computed from the Sparse-v2 plan outputs.
SPARSE_PLAN_FEATURES: tuple[str, ...] = (
    "fp_regenerate_count",
    "fp_validate_count",
    "fp_human_review_count",
    "fp_preserve_count",
    "fp_action_entropy",
    "fp_mean_confidence",
    "fp_serialized_decision_count",
    "fp_mean_completion_tokens",
)
SPARSE_BM25_FEATURES: tuple[str, ...] = (
    "sparse_bm25_jaccard_k3",
    "sparse_bm25_jaccard_k5",
    "sparse_bm25_jaccard_k10",
    "sparse_bm25_omitted_k3",
    "sparse_bm25_omitted_k5",
    "sparse_bm25_omitted_k10",
)


def _mean(x: Sequence[float]) -> float:
    return float(np.mean(list(x))) if x else 0.0


def _std(x: Sequence[float]) -> float:
    return float(np.std(list(x))) if x else 0.0


def _median(x: Sequence[float]) -> float:
    return float(np.median(list(x))) if x else 0.0


def _quantile(x: Sequence[float], q: float) -> float:
    return float(np.quantile(list(x), q)) if x else 0.0


def _shannon_entropy(probs: Sequence[float], normalize: bool = True) -> float:
    ps = [p for p in probs if p > 0]
    if not ps:
        return 0.0
    h = -sum(p * math.log(p) for p in ps)
    if normalize and len(ps) > 1:
        return h / math.log(len(ps))
    return h


def load_run_records() -> dict[str, dict[str, Any]]:
    recs: dict[str, dict[str, Any]] = {}
    for line in RUN_RECORDS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            recs[rec["run_id"]] = rec
    return recs


def per_cell_summary(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = list(records.values())
    valid = [r for r in rows if r["terminal_status"] == "succeeded"]
    return {
        "cells": len(rows),
        "valid": len(valid),
        "failed": len(rows) - len(valid),
        "schema_valid": sum(1 for r in rows if r.get("schema_valid")),
        "truncations": sum(1 for r in rows if r.get("truncation_status")),
        "prompt_tokens": sum(int(r["prompt_tokens"]) for r in rows),
        "completion_tokens": sum(int(r["completion_tokens"]) for r in rows),
        "total_tokens": sum(int(r["total_tokens"]) for r in rows),
        "model_calls": sum(int(r["model_calls"]) for r in rows),
        "api_cost_usd": round(sum(float(r.get("api_cost", 0.0)) for r in rows), 6),
        "raw_response_sha256_verified": sum(1 for r in rows if r.get("raw_response_sha256")),
        "per_rep_validity": {
            str(rep): {
                "valid": sum(1 for r in rows if r["repetition"] == rep and r["terminal_status"] == "succeeded"),
                "total": sum(1 for r in rows if r["repetition"] == rep),
            }
            for rep in (1, 2, 3)
        },
    }


def compute_task_labels(records: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Task-level Sparse-v2 has_fn labels (any-FN-over-reps, task unit)."""
    by_case: dict[str, list[dict[str, Any]]] = {}
    for r in records.values():
        by_case.setdefault(r["case_id"], []).append(r)

    ds = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    out: dict[str, dict[str, Any]] = {}
    for cid, cells in sorted(by_case.items()):
        proxy = set(ds.load_hidden_proxy_paths(cid))
        rep_fn_counts: list[int] = []
        rep_has_fn: list[int] = []
        valid_used = 0
        for cell in cells:
            if cell["terminal_status"] != "succeeded":
                rep_fn_counts.append(1)
                rep_has_fn.append(1)
                continue
            write_set = set(cell.get("predicted_write_set") or [])
            fn = len(proxy - write_set)
            rep_fn_counts.append(fn)
            rep_has_fn.append(1 if fn >= 1 else 0)
            valid_used += 1
        task = {
            "case_id": cid,
            "split": ds.split_of(cid),
            "proxy_size": len(proxy),
            "n_valid_reps": valid_used,
            "rep_fn_counts": rep_fn_counts,
            "rep_has_fn": rep_has_fn,
            "has_fn": int(any(h == 1 for h in rep_has_fn)),
            "fn_count": max(rep_fn_counts) if rep_fn_counts else 0,
            "fn_rate": (max(rep_fn_counts) / len(proxy)) if proxy else 0.0,
        }
        task["severity"] = (
            "none" if task["fn_rate"] <= 0.0
            else "partial" if task["fn_rate"] < 0.5
            else "complete"
        )
        out[cid] = task
    return out


def per_cell_action_features(records: dict[str, dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Derive action counts / entropy / mean confidence from persisted raw bytes.

    Reads the persisted raw provider response (.txt) for each run and parses the
    serialized decisions. PRESERVE is by omission (sparse contract):
    PRESERVE = candidate_count - serialized_decision_count.
    Zero new API calls; pure re-derivation from persisted evidence.
    """
    raw_dir = STUDY_DIR / "sparse_v2_trainval_runs" / "raw"
    out: dict[str, dict[str, float]] = {}
    for rid, rec in records.items():
        txt = raw_dir / f"{rid}.txt"
        entry = {
            "fp_regenerate_count": 0.0,
            "fp_validate_count": 0.0,
            "fp_human_review_count": 0.0,
            "fp_preserve_count": 0.0,
            "fp_action_entropy": 0.0,
            "fp_mean_confidence": 0.0,
        }
        if txt.is_file():
            try:
                raw = json.loads(txt.read_text(encoding="utf-8"))
                content = (raw.get("choices") or [{}])[0].get("message", {}).get("content", "")
                payload = json.loads(content)
                decisions = payload.get("decisions") or []
                counts: Counter[str] = Counter()
                confs: list[float] = []
                for d in decisions:
                    action = str(d.get("action", "")).upper()
                    counts[action] += 1
                    c = d.get("confidence")
                    if isinstance(c, (int, float)) and not isinstance(c, bool):
                        confs.append(float(c))
                n = int(rec.get("decoded_candidate_count") or 0)
                serialized = sum(counts.values())
                preserve = max(0, n - serialized)
                total_actions = max(1, serialized + preserve)
                probs = [
                    counts["REGENERATE"] / total_actions,
                    counts["VALIDATE"] / total_actions,
                    counts["HUMAN_REVIEW"] / total_actions,
                    preserve / total_actions,
                ]
                entry = {
                    "fp_regenerate_count": float(counts["REGENERATE"]),
                    "fp_validate_count": float(counts["VALIDATE"]),
                    "fp_human_review_count": float(counts["HUMAN_REVIEW"]),
                    "fp_preserve_count": float(preserve),
                    "fp_action_entropy": _shannon_entropy(probs),
                    "fp_mean_confidence": _mean(confs),
                }
            except Exception:
                pass  # fall back to zeros; cell itself records the failure
        out[rid] = entry
    return out


def task_plan_features(task_labels: dict[str, dict[str, Any]], records: dict[str, dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Per-task Sparse-LLM plan features (mean over valid reps; nested)."""
    by_case: dict[str, list[dict[str, Any]]] = {}
    for r in records.values():
        by_case.setdefault(r["case_id"], []).append(r)
    per_cell = per_cell_action_features(records)
    out: dict[str, dict[str, float]] = {}
    for cid in sorted(task_labels):
        cells = [c for c in by_case[cid] if c["terminal_status"] == "succeeded"]
        if not cells:
            out[cid] = {f: 0.0 for f in SPARSE_PLAN_FEATURES}
            continue
        n = int(cells[0]["decoded_candidate_count"] or 0)
        regen: list[float] = []
        validate: list[float] = []
        human_review: list[float] = []
        serialized: list[float] = []
        confs: list[float] = []
        completions: list[float] = []
        entropies: list[float] = []
        for c in cells:
            feats = per_cell.get(c["run_id"], {})
            regen.append(float(feats.get("fp_regenerate_count", 0.0)))
            validate.append(float(feats.get("fp_validate_count", 0.0)))
            human_review.append(float(feats.get("fp_human_review_count", 0.0)))
            serialized.append(float(c.get("serialized_decision_count") or 0))
            completions.append(float(c.get("completion_tokens") or 0))
            confs.append(float(feats.get("fp_mean_confidence", 0.0)))
            entropies.append(float(feats.get("fp_action_entropy", 0.0)))
        preserve = [max(0.0, n - s) for s in serialized]
        out[cid] = {
            "fp_regenerate_count": _mean(regen),
            "fp_validate_count": _mean(validate),
            "fp_human_review_count": _mean(human_review),
            "fp_preserve_count": _mean(preserve),
            "fp_action_entropy": _mean(entropies),
            "fp_mean_confidence": _mean(confs),
            "fp_serialized_decision_count": _mean(serialized),
            "fp_mean_completion_tokens": _mean(completions),
        }
    return out


def sparse_bm25_features(task_labels: dict[str, dict[str, Any]], records: dict[str, dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Sparse–BM25 disagreement per task (real Sparse-v2 write set vs BM25@K)."""
    by_case: dict[str, list[dict[str, Any]]] = {}
    for r in records.values():
        by_case.setdefault(r["case_id"], []).append(r)
    ds = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    out: dict[str, dict[str, float]] = {}
    for cid in sorted(task_labels):
        case = ds.load_public_case(cid)
        index, _ = compute_scores(case)
        cells = [c for c in by_case[cid] if c["terminal_status"] == "succeeded"]
        write_sets = [set(c.get("predicted_write_set") or []) for c in cells] or [set()]
        feats: dict[str, float] = {}
        for k in K_GRID:
            bm25k = set(index.rank(case.intent_text, k=k))
            jacs = []
            omitted = []
            for ws in write_sets:
                union = ws | bm25k
                jacs.append(len(ws & bm25k) / len(union) if union else 1.0)
                omitted.append(float(len(bm25k - ws)))
            feats[f"sparse_bm25_jaccard_k{k}"] = _mean(jacs)
            feats[f"sparse_bm25_omitted_k{k}"] = _mean(omitted)
        out[cid] = feats
    return out


def build_feature_table(
    task_labels: dict[str, dict[str, Any]],
    records: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    ds = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    plan = task_plan_features(task_labels, records)
    dis = sparse_bm25_features(task_labels, records)
    rows: list[dict[str, Any]] = []
    for cid, task in sorted(task_labels.items()):
        case = ds.load_public_case(cid)
        feats = extract_features(case)
        row: dict[str, Any] = {"case_id": cid, "split": task["split"]}
        row.update(feats)
        row.update(plan[cid])
        row.update(dis[cid])
        row["has_fn"] = task["has_fn"]
        row["fn_count"] = task["fn_count"]
        row["fn_rate"] = task["fn_rate"]
        row["severity"] = task["severity"]
        row["proxy_size"] = task["proxy_size"]
        rows.append(row)
    rows.sort(key=lambda r: r["case_id"])
    all_features = feature_names() + list(SPARSE_PLAN_FEATURES) + list(SPARSE_BM25_FEATURES)
    return rows, all_features


# ---------------------------------------------------------------------------
# Single-feature analysis (Sparse-v2 label)
# ---------------------------------------------------------------------------


def evaluate_feature(rows: list[dict[str, Any]], fname: str) -> dict[str, Any]:
    risk = [float(r[fname]) for r in rows]
    y = [int(r["has_fn"]) for r in rows]
    v = [x for x in risk]
    has1 = [v[i] for i in range(len(y)) if y[i] == 1]
    has0 = [v[i] for i in range(len(y)) if y[i] == 0]
    b = metrics.bootstrap_ci(risk, y, metrics.auprc, seed=BOOTSTRAP_SEED)
    return {
        "feature": fname,
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


def random_auroc_band(rows: list[dict[str, Any]], n_seeds: int = 2000, seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    rng = random.Random(seed)
    y = [int(r["has_fn"]) for r in rows]
    vals = []
    for _ in range(n_seeds):
        risk = [rng.random() for _ in rows]
        vals.append(metrics.auroc(risk, y))
    return {
        "mean": _mean(vals),
        "sd": _std(vals),
        "q2_5": _quantile(vals, 0.025),
        "q50": _quantile(vals, 0.5),
        "q97_5": _quantile(vals, 0.975),
        "n_seeds": n_seeds,
    }


def run_single_feature(rows: list[dict[str, Any]], feature_list: list[str]) -> dict[str, Any]:
    out = {}
    for fname in feature_list:
        out[fname] = evaluate_feature(rows, fname)
    return out


def _label_vector(rows: list[dict[str, Any]]) -> list[int]:
    return [int(r["has_fn"]) for r in rows]


def run_sparse_baselines(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(BOOTSTRAP_SEED)
    r0_vecs = []
    for _ in range(50):
        risk = [rng.random() for _ in rows]
        r0_vecs.append(metrics.auroc(risk, _label_vector(rows)))

    def r1(r: dict[str, Any]) -> float:
        return float(r["fp_density_k10"])

    def r3(r: dict[str, Any]) -> float:
        return float(r["bm25_top10_norm_entropy"])

    def r4(r: dict[str, Any]) -> float:
        return 1.0 - float(r["sparse_bm25_jaccard_k10"])

    def r5(r: dict[str, Any]) -> float:
        return float(r["graph_1hop_frontier_size"])

    baselines: dict[str, Callable[[dict[str, Any]], float]] = {
        "R1_first_pass_density": r1,
        "R3_bm25_uncertainty": r3,
        "R4_sparse_bm25_disagreement": r4,
        "R5_graph_frontier": r5,
    }
    y = _label_vector(rows)
    out: dict[str, Any] = {}
    for name, fn in baselines.items():
        risk = [fn(r) for r in rows]
        out[name] = {
            "auroc": metrics.auroc(risk, y),
            "auroc_signed": metrics.auroc_direction(risk, y),
            "auprc": metrics.auprc(risk, y),
            "recall_at_budget": metrics.recall_at_budget(risk, y),
            "prevalence": sum(y) / len(y) if y else 0.0,
        }
    out["R0_random"] = {"auroc_mean": _mean(r0_vecs), "auroc_sd": _std(r0_vecs), "n_seeds": 50}
    return out


def run_sparse_combination(rows: list[dict[str, Any]]) -> dict[str, Any]:
    train = [r for r in rows if r["split"] == "TRAIN"]
    valid = [r for r in rows if r["split"] == "VALIDATION"]
    tr_risks = []
    va_risks = []
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
    y_tr = [int(r["has_fn"]) for r in train]
    y_va = [int(r["has_fn"]) for r in valid]
    return {
        "description": "equal-weight standardized sum (retrieval uncertainty + disagreement + graph frontier); frozen",
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


def run_sparse_calibration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    train = [r for r in rows if r["split"] == "TRAIN"]
    valid = [r for r in rows if r["split"] == "VALIDATION"]
    risk_t = [float(r["bm25_top10_norm_entropy"]) for r in train]
    risk_v = [float(r["bm25_top10_norm_entropy"]) for r in valid]
    y_t = [int(r["has_fn"]) for r in train]
    y_v = [int(r["has_fn"]) for r in valid]
    return {
        "platt": metrics.calibration_report(y_train=y_t, risk_train=risk_t, y_eval=y_v, risk_eval=risk_v, method="platt"),
        "isotonic": metrics.calibration_report(y_train=y_t, risk_train=risk_t, y_eval=y_v, risk_eval=risk_v, method="isotonic"),
    }


def run_sparse_cost_sensitivity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    train = [r for r in rows if r["split"] == "TRAIN"]
    valid = [r for r in rows if r["split"] == "VALIDATION"]
    risk_t = [float(r["bm25_top10_norm_entropy"]) for r in train]
    y_t = [int(r["has_fn"]) for r in train]
    fn_pos = [int(r["fn_count"]) for r in train if r["has_fn"] == 1]
    fn_pos_mean = _mean(fn_pos) if fn_pos else 0.0
    probs_v = metrics._platt_calibration(risk_t, y_t, [float(r["bm25_top10_norm_entropy"]) for r in valid])
    prob_score = {r["case_id"]: float(p) for r, p in zip(valid, probs_v, strict=True)}
    risk_score = {r["case_id"]: r["bm25_top10_norm_entropy"] for r in valid}
    has_fn = {r["case_id"]: int(r["has_fn"]) for r in valid}
    return cost.analyze_cost_sensitivity(
        risk_score=risk_score,
        prob_score=prob_score,
        has_fn=has_fn,
        fn_pos_mean=fn_pos_mean,
    )


def run_sparse_adaptive_k(rows: list[dict[str, Any]], dataset_dir: Path) -> dict[str, Any]:
    """Adaptive-K evaluates the deterministic BM25@K retrieval depth against the
    proxy (evaluation-time only). It is label-independent of the Sparse-v2 label
    and is rerun here for completeness; the deterministic result is unchanged."""
    return run_adaptive_k_analysis(rows, dataset_dir)


def _top_features(single: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    rr = []
    for fname, res in single.items():
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


def signal_vs_random(single: dict[str, Any], band: dict[str, Any]) -> dict[str, Any]:
    radius = max(abs(band["q2_5"] - 0.5), abs(band["q97_5"] - 0.5))
    above = []
    for fname, res in single.items():
        signed = res["auroc_signed"]
        if abs(signed - 0.5) > radius:
            above.append(fname)
    return {
        "band": [band["q2_5"], band["q97_5"]],
        "radius": radius,
        "n_features": len(single),
        "n_above_random_95": len(above),
        "features_above_random_95": sorted(above),
    }


def family_summary(single: dict[str, Any]) -> dict[str, Any]:
    fam_by_name = {s.name: s.family for s in feature_specs()}
    fam_by_name.update({f: "G_sparse_plan" for f in SPARSE_PLAN_FEATURES})
    fam_by_name.update({f: "H_sparse_bm25_disagreement" for f in SPARSE_BM25_FEATURES})
    fam: dict[str, list[float]] = {}
    for fname, res in single.items():
        fam_name = fam_by_name.get(fname)
        if fam_name is None:
            continue
        fam.setdefault(fam_name, []).append(res["auroc_signed"])
    return {
        fam_name: {
            "n_features": len(vals),
            "auroc_signed_mean": _mean(vals),
            "auroc_signed_max_abs": float(max(abs(v) for v in vals)) if vals else 0.0,
        }
        for fam_name, vals in sorted(fam.items())
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = load_run_records()
    cell = per_cell_summary(records)

    labels = compute_task_labels(records)
    n_pos = sum(1 for t in labels.values() if t["has_fn"] == 1)
    n_neg = len(labels) - n_pos
    prevalence = n_pos / len(labels)

    # Phase-B gate A re-run on the new evidence.
    data_avail = json.loads((STUDY_DIR / "data_availability.json").read_text(encoding="utf-8"))
    data_avail["TRAIN"]["sparse_v2_prediction_available"] = True
    data_avail["VALIDATION"]["sparse_v2_prediction_available"] = True
    data_avail["TRAIN"]["repetitions"] = 3
    data_avail["VALIDATION"]["repetitions"] = 3
    data_avail["TRAIN"]["source_artifact"] = "research/omission-risk-feature-study-v1/sparse_v2_trainval_run_records.jsonl"
    data_avail["VALIDATION"]["source_artifact"] = "research/omission-risk-feature-study-v1/sparse_v2_trainval_run_records.jsonl"
    data_avail["TRAIN"]["usable_for_labels"] = True
    data_avail["VALIDATION"]["usable_for_labels"] = True
    data_avail["decision"] = (
        "TRAIN/VALIDATION Sparse-v2 predictions now AVAILABLE (development-inference run "
        "2026-09-16, 90 cells). Registered Sparse-v2-label feature analysis EXECUTED."
    )
    (STUDY_DIR / "data_availability.json").write_text(json.dumps(data_avail, indent=2), encoding="utf-8")

    labels_json = {
        "label_definition": (
            "has_fn(t) = 1 iff the Sparse-v2 prediction omits >=1 proxy-positive file; "
            "pre-registered aggregation = any-FN-over-reps with task-level unit (N=30)."
        ),
        "n_tasks": len(labels),
        "n_positive": n_pos,
        "n_negative": n_neg,
        "prevalence": prevalence,
        "class_balance_gate_ok": min(n_pos, n_neg) >= 10,
        "multivariable_fitted": False,
        "reason": (
            "multivariable RiskScorer NOT fitted: class-balance gate requires >=10 "
            "independent tasks per class; analysis is descriptive/single-feature only."
        ),
        "tasks": labels,
    }
    (OUTPUT_DIR / "sparse_v2_labels.json").write_text(json.dumps(labels_json, indent=2), encoding="utf-8")

    # Feature table + single-feature analysis
    rows, all_features = build_feature_table(labels, records)
    fieldnames = ["case_id", "split"] + all_features + ["has_fn", "fn_count", "fn_rate", "severity", "proxy_size"]
    with (OUTPUT_DIR / "sparse_v2_feature_table.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in fieldnames})

    single = run_single_feature(rows, all_features)
    (OUTPUT_DIR / "sparse_v2_single_feature_results.json").write_text(json.dumps(single, indent=2), encoding="utf-8")

    band = random_auroc_band(rows)
    (OUTPUT_DIR / "sparse_v2_random_band.json").write_text(json.dumps(band, indent=2), encoding="utf-8")

    baselines = run_sparse_baselines(rows)
    (OUTPUT_DIR / "sparse_v2_baselines.json").write_text(json.dumps(baselines, indent=2), encoding="utf-8")

    combo = run_sparse_combination(rows)
    (OUTPUT_DIR / "sparse_v2_combination.json").write_text(json.dumps(combo, indent=2), encoding="utf-8")

    cal = run_sparse_calibration(rows)
    (OUTPUT_DIR / "sparse_v2_calibration.json").write_text(json.dumps(cal, indent=2), encoding="utf-8")

    cost_res = run_sparse_cost_sensitivity(rows)
    (OUTPUT_DIR / "sparse_v2_cost_sensitive.json").write_text(json.dumps(cost_res, indent=2), encoding="utf-8")

    adaptive = run_sparse_adaptive_k(rows, DATASET_DIR)
    (OUTPUT_DIR / "sparse_v2_adaptive_k.json").write_text(json.dumps(adaptive, indent=2), encoding="utf-8")

    fam = family_summary(single)
    vs_random = signal_vs_random(single, band)
    top = _top_features(single)

    comparison = {
        "cell_evidence": cell,
        "n_tasks": len(labels),
        "prevalence": prevalence,
        "class_balance": {"n_pos": n_pos, "n_neg": n_neg, "gate_ok": min(n_pos, n_neg) >= 10},
        "top_features_by_auprc": top,
        "random_band": band,
        "signal_vs_random": vs_random,
        "family_summary": fam,
        "baselines": baselines,
        "combination": combo,
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
    }
    (OUTPUT_DIR / "sparse_v2_summary.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")

    # Comparison vs deterministic first pass
    det_summary = json.loads((STUDY_DIR / "study_results_summary.json").read_text(encoding="utf-8"))
    det_top = det_summary["single_feature_top_by_auprc"]
    det_band = det_summary["random_auroc_band"]["k10"]

    compare = {
        "label_source": {
            "deterministic_first_pass": "metadata-corpus BM25@K has_fn (K_ref=10)",
            "sparse_v2": "Sparse-v2 write-set has_fn (any-FN-over-reps, task unit)",
        },
        "prevalence": {
            "deterministic_k10": det_summary["prevalence_by_k"]["10"],
            "sparse_v2": prevalence,
        },
        "top5_by_auprc": {
            "deterministic_k10": [x["feature"] for x in det_top[:5]],
            "sparse_v2": [x["feature"] for x in top[:5]],
        },
        "signal_vs_random": {
            "deterministic_k10": det_summary["signal_vs_random"]["k10"],
            "sparse_v2": vs_random,
        },
        "random_band": {
            "deterministic_k10": [det_band["q2_5"], det_band["q97_5"]],
            "sparse_v2": [band["q2_5"], band["q97_5"]],
        },
        "baselines_k10": {
            "deterministic": det_summary["baselines"]["k10"],
            "sparse_v2": baselines,
        },
        "family_summary": {
            "deterministic_k10": det_summary["family_summary"]["k10"],
            "sparse_v2": fam,
        },
        "note": (
            "N=30 tasks in both analyses. Sparse-v2 repetitions are nested; task-level "
            "label/features are used, never repetition-level. HELD_OUT_TEST untouched."
        ),
    }
    (OUTPUT_DIR / "sparse_v2_comparison.json").write_text(json.dumps(compare, indent=2), encoding="utf-8")

    print("=== SPARSE-V2 LABEL PREVALENCE (before fitting) ===")
    print(f"N tasks = {len(labels)}")
    print(f"N positive (has_fn=1) = {n_pos}")
    print(f"N negative (has_fn=0) = {n_neg}")
    print(f"prevalence = {prevalence:.4f}")
    print(f"class_balance_gate_ok (>=10 per class) = {min(n_pos, n_neg) >= 10}")
    print("multivariable_fitted = False (descriptive/single-feature only)")
    print(f"90-cell validity: {cell['valid']}/{cell['cells']} valid, tokens={cell['total_tokens']}, cost=${cell['api_cost_usd']}")
    print(f"random_auroc_band = [{band['q2_5']:.3f}, {band['q97_5']:.3f}]")
    print(f"features_above_random_95 = {vs_random['features_above_random_95']}")
    print(f"top_features_by_auprc = {[(x['feature'], round(x['auprc'],3)) for x in top[:5]]}")
    print("outputs:", sorted(p.name for p in OUTPUT_DIR.iterdir()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
