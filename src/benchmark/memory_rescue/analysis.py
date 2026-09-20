"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — nested 5x5 CV analysis (T3, ZERO API).

EXACTLY V1 model / folds / threshold procedure (frozen, mission §20):
  - deterministic 5-fold OUTER task-grouped, repository-stratified CV reusing
    the EXACT V1 outer fold assignments;
  - per outer fold: scaler + L2-LR fit on outer-training tasks ONLY;
    INNER 5-fold task-grouped OOF within outer-train; threshold = argmax
    pooled micro-F1 over 0.01..0.99 (tie-break HIGHER); frozen threshold
    applied to outer held-out probabilities; final set = {prob >= threshold}.

Reuses benchmark.calibrated.policy (fit_policy/predict_proba/select_threshold/
confusion/per_task_confusion/paired_bootstrap_deltas) and
benchmark.calibrated.analysis.calibration_diagnostics / evaluate_gate, so the
model, metrics, bootstrap and success gate are byte-for-byte the V1 logic.

Adds (descriptive): error decomposition with memory-channel attribution
(mission §25), intent-length stratification (mission §26), sparse-empty
per-repo results.
"""
# ruff: noqa: N806, N812

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from benchmark.calibrated import analysis as V1A  # type: ignore[no-untyped-call]
from benchmark.calibrated import policy as P  # type: ignore[no-untyped-call]
from benchmark.calibrated.folds import grouped_stratified_folds, split_by_fold  # type: ignore[no-untyped-call]

from .candidates import (  # type: ignore[no-untyped-call]
    BOOLEAN_FEATURES,
    CONTINUOUS_FEATURES,
    FEATURE_NAMES,
    feature_matrix,
    label_vector,
)

FOLD_SEED = 20260920
INNER_SEED = 20260920
N_FOLDS = 5


def run_nested_cv_v2(
    frame: pd.DataFrame,
    tasks_by_id: dict,
    fold_map: dict[str, int],
    provenance: dict | None = None,
    n_folds: int = N_FOLDS,
    inner_seed: int = INNER_SEED,
) -> dict:
    """Run the frozen V2 nested CV (exact V1 procedure, V2 features).

    frame: V2 candidate rows DataFrame (11 feature columns + label).
    tasks_by_id: case_id -> RecallTask.
    fold_map: case_id -> outer fold (reuse EXACT V1 assignments).
    provenance: optional case_id -> {file_path: frozenset(channels)} for the
                descriptive error decomposition (mission §25).
    """
    repo_of = {cid: str(frame.loc[frame["case_id"] == cid, "repository"].iloc[0])
               for cid in sorted(set(frame["case_id"]))}
    case_ids = sorted(set(frame["case_id"]))
    if len(case_ids) != len(tasks_by_id):
        raise ValueError("frame case set must equal the DEV task set")

    oof: list[dict] = []
    final_sets: dict[str, set[str]] = {}
    policy_contribs: dict[str, tuple[int, int, int]] = {}
    sparse_contribs: dict[str, tuple[int, int, int]] = {}
    per_fold: dict[str, dict] = {}

    for fold in range(n_folds):
        train_ids, held_ids = split_by_fold(fold_map, fold)
        train_frame = frame[frame["case_id"].isin(train_ids)]
        test_frame = frame[frame["case_id"].isin(held_ids)].copy()

        X_train = feature_matrix(train_frame)
        y_train = label_vector(train_frame)

        # ---- inner task-grouped OOF threshold selection (outer-train only) ----
        inner_fold_map = grouped_stratified_folds(
            train_ids, lambda c: repo_of[c], k=n_folds, seed=inner_seed)
        inner_probs: list[np.ndarray] = []
        inner_labels: list[np.ndarray] = []
        for j in range(n_folds):
            it_ids, iv_ids = split_by_fold(inner_fold_map, j)
            it = train_frame[train_frame["case_id"].isin(it_ids)]
            iv = train_frame[train_frame["case_id"].isin(iv_ids)]
            if it.empty or iv.empty:
                continue
            scaler_j, model_j = P.fit_policy(
                feature_matrix(it), label_vector(it),
                continuous_cols=CONTINUOUS_FEATURES,
                boolean_cols=BOOLEAN_FEATURES,
                feature_names=FEATURE_NAMES)
            inner_probs.append(P.predict_proba(
                scaler_j, model_j, feature_matrix(iv),
                continuous_cols=CONTINUOUS_FEATURES,
                boolean_cols=BOOLEAN_FEATURES,
                feature_names=FEATURE_NAMES))
            inner_labels.append(label_vector(iv))
        if not inner_probs:
            raise RuntimeError("no inner OOF rows produced; degenerate fold partition")
        inner_probs_all = np.concatenate(inner_probs)
        inner_labels_all = np.concatenate(inner_labels)
        threshold = P.select_threshold(inner_probs_all, inner_labels_all)
        inner_f1_star = P.max_f1_on_grid(inner_probs_all, inner_labels_all)

        # ---- final outer model on ALL outer-training tasks ----
        scaler, model = P.fit_policy(
            X_train, y_train,
            continuous_cols=CONTINUOUS_FEATURES,
            boolean_cols=BOOLEAN_FEATURES,
            feature_names=FEATURE_NAMES)
        test_probs = P.predict_proba(
            scaler, model, feature_matrix(test_frame),
            continuous_cols=CONTINUOUS_FEATURES,
            boolean_cols=BOOLEAN_FEATURES,
            feature_names=FEATURE_NAMES)
        test_frame["prob"] = test_probs
        test_frame["selected"] = (test_probs >= threshold).astype(int)

        for cid in sorted(held_ids):
            sub = test_frame[test_frame["case_id"] == cid]
            selected = set(sub.loc[sub["selected"] == 1, "file_path"])
            task = tasks_by_id[cid]
            final_sets[cid] = selected
            policy_contribs[cid] = P.per_task_confusion(selected, task.proxy)
            sparse_contribs[cid] = P.per_task_confusion(set(task.write_set), task.proxy)

        sel = inner_probs_all >= threshold
        inner_f1 = (
            2.0 * int((sel & (inner_labels_all == 1)).sum())
            / (2 * int((sel & (inner_labels_all == 1)).sum())
               + int((sel & (inner_labels_all == 0)).sum())
               + int(((~sel) & (inner_labels_all == 1)).sum()))
            if (sel & (inner_labels_all == 1)).any() else 0.0
        )
        per_fold[str(fold)] = {
            "n_train_tasks": len(train_ids),
            "n_held_tasks": len(held_ids),
            "inner_threshold": float(threshold),
            "inner_oof_n_rows": int(len(inner_probs_all)),
            "inner_oof_f1_at_threshold": float(inner_f1),
            "lipton_descriptive_f1star": float(inner_f1_star),
            "lipton_descriptive_f1star_over_2": float(inner_f1_star / 2.0),
            "scaler_mean": [float(x) for x in scaler.mean_.tolist()],
            "scaler_scale": [float(x) for x in scaler.scale_.tolist()],
            "lr_coef": [float(x) for x in model.coef_.ravel().tolist()],
            "lr_intercept": float(model.intercept_[0]),
        }

        for row in test_frame.itertuples(index=False):
            oof.append({
                "case_id": row.case_id,
                "repository": row.repository,
                "file_path": row.file_path,
                "prob": float(row.prob),
                "label": int(row.label),
                "selected": int(row.selected),
            })

    repo_metrics: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        cids = [c for c in case_ids if repo_of[c] == repo]
        tp = sum(policy_contribs[c][0] for c in cids)
        fp = sum(policy_contribs[c][1] for c in cids)
        fn = sum(policy_contribs[c][2] for c in cids)
        stp = sum(sparse_contribs[c][0] for c in cids)
        sfp = sum(sparse_contribs[c][1] for c in cids)
        sfn = sum(sparse_contribs[c][2] for c in cids)
        repo_metrics[repo] = {
            "n_tasks": len(cids),
            "policy": P.confusion(tp, fp, fn),
            "sparse": P.confusion(stp, sfp, sfn),
        }

    fold_deltas: dict[str, list[float]] = {r: [] for r in ("djangocms", "saleor")}
    for fold in range(n_folds):
        _, held = split_by_fold(fold_map, fold)
        for repo in ("djangocms", "saleor"):
            cids = [c for c in held if repo_of[c] == repo]
            if not cids:
                fold_deltas[repo].append(0.0)
                continue
            tp = sum(policy_contribs[c][0] for c in cids)
            fp = sum(policy_contribs[c][1] for c in cids)
            fn = sum(policy_contribs[c][2] for c in cids)
            stp = sum(sparse_contribs[c][0] for c in cids)
            sfp = sum(sparse_contribs[c][1] for c in cids)
            sfn = sum(sparse_contribs[c][2] for c in cids)
            f1p = P.confusion(tp, fp, fn)["f1"]
            f1s = P.confusion(stp, sfp, sfn)["f1"]
            fold_deltas[repo].append(round(f1p - f1s, 6))

    bootstrap: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        cids = [c for c in case_ids if repo_of[c] == repo]
        bootstrap[repo] = P.paired_bootstrap_deltas(
            [policy_contribs[c] for c in cids],
            [sparse_contribs[c] for c in cids],
        )

    calibration = V1A.calibration_diagnostics(
        np.array([r["prob"] for r in oof], dtype=np.float64),
        np.array([r["label"] for r in oof], dtype=np.int64),
    )

    err_dec, set_size = decompose_and_set_sizes(final_sets, tasks_by_id, repo_of,
                                                 case_ids, provenance)

    return {
        "n_tasks": len(case_ids),
        "fold_map": fold_map,
        "per_fold": per_fold,
        "oof": oof,
        "final_sets": {k: sorted(v) for k, v in final_sets.items()},
        "repo_metrics": repo_metrics,
        "fold_deltas": fold_deltas,
        "bootstrap": bootstrap,
        "calibration": calibration,
        "error_decomposition": err_dec,
        "set_size": set_size,
    }


def decompose_and_set_sizes(
    final_sets: dict[str, set],
    tasks_by_id: dict,
    repo_of: dict,
    case_ids: list[str],
    provenance: dict | None = None,
) -> tuple[dict, dict]:
    """Error decomposition (A-F + channel attribution) + set-size analysis.

    Mission §25: Sparse TP retained / Sparse TP dropped / Sparse FP dropped /
    Sparse FP retained; omitted positives added by channel; new FP added by
    channel; remaining FN classified as (A) not generated by dense or memory
    candidates, (B) candidate generated but policy rejected, (C) Sparse TP
    dropped.
    """
    decomp: dict[str, dict] = {}
    sizes: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        cids = [c for c in case_ids if repo_of[c] == repo]
        a = b = c = d = 0
        added_by_channel: dict[str, int] = {k: 0 for k in
                                            ("dense_only", "structural", "episodic",
                                             "multiple_memory", "sparse_universe")}
        newfp_by_channel: dict[str, int] = {k: 0 for k in
                                            ("dense_only", "structural", "episodic",
                                             "multiple_memory", "sparse_universe")}
        fn_class: dict[str, int] = {"not_generated": 0, "rejected": 0, "sparse_tp_dropped": 0}
        sparse_sizes: list[int] = []
        policy_sizes: list[int] = []
        proxy_sizes: list[int] = []
        empty_sparse = empty_policy = 0
        additions: list[int] = []
        for cid in cids:
            task = tasks_by_id[cid]
            sparse = set(task.write_set)
            proxy = set(task.proxy)
            policy = set(final_sets[cid])
            a += len((sparse & proxy) & policy)
            b += len((sparse & proxy) - policy)
            c += len((sparse - proxy) - policy)
            d += len((sparse - proxy) & policy)

            prov = (provenance or {}).get(cid, {})
            for f in (policy - sparse) & proxy:  # omitted positives added
                ch = _channel_label(prov, f)
                added_by_channel[ch] += 1
            for f in (policy - sparse) - proxy:  # new FP added
                ch = _channel_label(prov, f)
                newfp_by_channel[ch] += 1
            for f in proxy - policy:  # remaining FN classification
                if f in sparse:
                    fn_class["sparse_tp_dropped"] += 1
                elif f in prov:
                    fn_class["rejected"] += 1
                else:
                    fn_class["not_generated"] += 1

            sparse_sizes.append(len(sparse))
            policy_sizes.append(len(policy))
            proxy_sizes.append(len(proxy))
            empty_sparse += 1 if not sparse else 0
            empty_policy += 1 if not policy else 0
            additions.append(len(policy - sparse))
        decomp[repo] = {
            "A_sparse_tp_retained": a,
            "B_sparse_tp_incorrectly_dropped": b,
            "C_sparse_fp_correctly_dropped": c,
            "D_sparse_fp_retained": d,
            "E_sparse_fn_added_by_channel": added_by_channel,
            "F_new_fp_added_by_channel": newfp_by_channel,
            "remaining_fn_class": fn_class,
        }
        sizes[repo] = {
            "sparse_mean": round(float(np.mean(sparse_sizes)), 4) if sparse_sizes else 0.0,
            "sparse_median": float(np.median(sparse_sizes)) if sparse_sizes else 0.0,
            "policy_mean": round(float(np.mean(policy_sizes)), 4) if policy_sizes else 0.0,
            "policy_median": float(np.median(policy_sizes)) if policy_sizes else 0.0,
            "proxy_mean": round(float(np.mean(proxy_sizes)), 4) if proxy_sizes else 0.0,
            "proxy_median": float(np.median(proxy_sizes)) if proxy_sizes else 0.0,
            "empty_sparse": empty_sparse,
            "empty_policy": empty_policy,
            "n_tasks": len(cids),
            "additions_per_task": [int(x) for x in additions],
            "additions_mean": round(float(np.mean(additions)), 4) if additions else 0.0,
            "additions_median": float(np.median(additions)) if additions else 0.0,
        }
    return decomp, sizes


def _channel_label(prov: dict, f: str) -> str:
    """Descriptive channel label for a non-Sparse candidate file."""
    ch = set(prov.get(f, ()))
    if "sparse" in ch:
        return "sparse_universe"
    mem = ({"structural"} & ch) | ({"episodic"} & ch)
    if len(mem) >= 2:
        return "multiple_memory"
    if "structural" in mem:
        return "structural"
    if "episodic" in mem:
        return "episodic"
    if "dense" in ch:
        return "dense_only"
    return "sparse_universe"


def intent_bucket(intent_text: str) -> str:
    """Pre-registered intent-length bucket (mission §26).

    Buckets: "<=6", "7-15", ">15" whitespace-separated words. DESCRIPTIVE
    ONLY — never a feature, never a gate, never used to choose thresholds or
    memory settings or candidate generation.
    """
    n = len([w for w in intent_text.split() if w.strip()])
    if n <= 6:
        return "<=6"
    if n <= 15:
        return "7-15"
    return ">15"


def intent_stratification(tasks_by_id: dict, policy_contribs: dict,
                          sparse_contribs: dict) -> dict:
    """Descriptive per-repo, per-intent-bucket P/R/F1/FNR for Sparse and policy.

    policy_contribs / sparse_contribs: case_id -> (tp, fp, fn) from the V2 run.
    """
    out: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        buckets: dict[str, dict] = {}
        for cid, task in tasks_by_id.items():
            if task.repository != repo:
                continue
            bucket = intent_bucket(task.intent_text)
            b = buckets.setdefault(bucket, {"n": 0, "sparse": (0, 0, 0), "policy": (0, 0, 0)})
            b["n"] += 1
            sp = b["sparse"]
            b["sparse"] = (sp[0] + sparse_contribs[cid][0],
                           sp[1] + sparse_contribs[cid][1],
                           sp[2] + sparse_contribs[cid][2])
            pc = b["policy"]
            b["policy"] = (pc[0] + policy_contribs[cid][0],
                           pc[1] + policy_contribs[cid][1],
                           pc[2] + policy_contribs[cid][2])
        rows: dict[str, dict] = {}
        for bucket in ("<=6", "7-15", ">15"):
            if bucket not in buckets:
                continue
            b = buckets[bucket]
            rows[bucket] = {
                "n_tasks": b["n"],
                "sparse": P.confusion(*b["sparse"]),
                "policy": P.confusion(*b["policy"]),
            }
        out[repo] = rows
    return out


def sparse_empty_metrics(tasks_by_id: dict, policy_contribs: dict) -> dict:
    """Descriptive metrics restricted to tasks where Sparse is empty."""
    out: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        cids = [cid for cid, t in tasks_by_id.items()
                if t.repository == repo and not t.write_set]
        if not cids:
            out[repo] = {"n_tasks": 0}
            continue
        tp = sum(policy_contribs[c][0] for c in cids)
        fp = sum(policy_contribs[c][1] for c in cids)
        fn = sum(policy_contribs[c][2] for c in cids)
        out[repo] = {"n_tasks": len(cids), **P.confusion(tp, fp, fn)}
    return out


def evaluate_gate(results: dict) -> dict:
    """Frozen primary success gate (mission §24) — EXACT V1 logic."""
    return V1A.evaluate_gate(results)


def _log1p_hist(history_change_count: int) -> float:
    return float(math.log1p(history_change_count))
