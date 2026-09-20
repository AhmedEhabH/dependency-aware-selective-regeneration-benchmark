"""CALIBRATED_SET_SELECTION_V1 — nested 5x5 task-grouped CV analysis (T3, ZERO API).

Frozen procedure (docs/CALIBRATED_SET_SELECTION_V1_IMPACT_DECLARATION_2026-09-20.md):

- OUTER 5-fold task-grouped, repository-stratified CV (fold seed 20260920).
- For every outer fold:
  1. held-out tasks designated;
  2. scaler + L2-LR fit on the remaining outer-training tasks ONLY;
  3. INNER 5-fold task-grouped OOF within the outer-training tasks;
  4. threshold = argmax pooled micro-F1 on inner-OOF over grid 0.01..0.99
     (tie-break: HIGHER threshold);
  5. the threshold is frozen;
  6. probabilities predicted for the outer held-out tasks;
  7. final set = {candidate : prob >= threshold}; scored vs the proxy.
- Held-out labels NEVER influence scaling, coefficients, threshold, feature
  construction, or candidate-universe definition.

Outputs: per-repo pooled metrics, fold-by-fold results, paired task bootstrap
CIs, calibration diagnostics, error decomposition, set-size analysis,
realization A/B robustness (run the driver twice with different realizations).

All functions are pure and deterministic (fixed seeds; liblinear solver).
"""
# ruff: noqa: N806

from __future__ import annotations

import numpy as np
import pandas as pd

from .features import (
    feature_matrix,
    label_vector,
)
from .folds import grouped_stratified_folds, split_by_fold
from .policy import (
    confusion,
    fit_policy,
    max_f1_on_grid,
    paired_bootstrap_deltas,
    per_task_confusion,
    predict_proba,
    select_threshold,
)

FOLD_SEED = 20260920
INNER_SEED = 20260920
N_FOLDS = 5


def run_nested_cv(
    frame: pd.DataFrame,
    tasks_by_id: dict,
    fold_map: dict[str, int],
    n_folds: int = N_FOLDS,
    inner_seed: int = INNER_SEED,
) -> dict:
    """Run the frozen nested CV and return a full result dict.

    frame: candidate rows DataFrame from features.rows_to_frame.
    tasks_by_id: case_id -> RecallTask (write_set + proxy for scoring only).
    fold_map: case_id -> outer fold (deterministic; from folds.grouped_stratified_folds).
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
            train_ids, lambda c: repo_of[c], k=n_folds, seed=inner_seed
        )
        inner_probs: list[np.ndarray] = []
        inner_labels: list[np.ndarray] = []
        for j in range(n_folds):
            it_ids, iv_ids = split_by_fold(inner_fold_map, j)
            it = train_frame[train_frame["case_id"].isin(it_ids)]
            iv = train_frame[train_frame["case_id"].isin(iv_ids)]
            if it.empty or iv.empty:
                continue
            scaler_j, model_j = fit_policy(feature_matrix(it), label_vector(it))
            inner_probs.append(predict_proba(scaler_j, model_j, feature_matrix(iv)))
            inner_labels.append(label_vector(iv))
        if not inner_probs:
            raise RuntimeError("no inner OOF rows produced; degenerate fold partition")
        inner_probs_all = np.concatenate(inner_probs)
        inner_labels_all = np.concatenate(inner_labels)
        threshold = select_threshold(inner_probs_all, inner_labels_all)
        inner_f1_star = max_f1_on_grid(inner_probs_all, inner_labels_all)

        # ---- final outer model on ALL outer-training tasks ----
        scaler, model = fit_policy(X_train, y_train)
        test_probs = predict_proba(scaler, model, feature_matrix(test_frame))
        test_frame["prob"] = test_probs
        test_frame["selected"] = (test_probs >= threshold).astype(int)

        # ---- build final sets + per-task confusion for held-out tasks ----
        for cid in sorted(held_ids):
            sub = test_frame[test_frame["case_id"] == cid]
            selected = set(sub.loc[sub["selected"] == 1, "file_path"])
            task = tasks_by_id[cid]
            final_sets[cid] = selected
            policy_contribs[cid] = per_task_confusion(selected, task.proxy)
            sparse_contribs[cid] = per_task_confusion(set(task.write_set), task.proxy)

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

    # ---- pooled repo metrics ----
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
            "policy": confusion(tp, fp, fn),
            "sparse": confusion(stp, sfp, sfn),
        }

    # ---- fold-by-fold repo F1 deltas (gate E) ----
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
            f1p = confusion(tp, fp, fn)["f1"]
            f1s = confusion(stp, sfp, sfn)["f1"]
            fold_deltas[repo].append(round(f1p - f1s, 6))

    # ---- paired task bootstrap CIs (policy - sparse) ----
    bootstrap: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        cids = [c for c in case_ids if repo_of[c] == repo]
        bootstrap[repo] = paired_bootstrap_deltas(
            [policy_contribs[c] for c in cids],
            [sparse_contribs[c] for c in cids],
        )

    # ---- calibration diagnostics (outer OOF probabilities) ----
    calibration = calibration_diagnostics(
        np.array([r["prob"] for r in oof], dtype=np.float64),
        np.array([r["label"] for r in oof], dtype=np.int64),
    )

    # ---- error decomposition + set-size analysis ----
    err_dec, set_size = decompose_and_set_sizes(final_sets, tasks_by_id, repo_of, case_ids)

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


def calibration_diagnostics(probs: np.ndarray, labels: np.ndarray,
                            n_bins: int = 10) -> dict:
    """Frozen 10 equal-width probability-bin calibration diagnostics.

    Brier score; Expected Calibration Error (ECE); reliability table.
    No second calibration algorithm. Deterministic.
    """
    if len(probs) == 0:
        return {"brier": None, "ece": None, "bins": [], "n_rows": 0}
    brier = float(np.mean((probs - labels) ** 2))
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_rows = []
    ece = 0.0
    n = len(probs)
    for b in range(n_bins):
        lo, hi = edges[b], edges[b + 1]
        mask = (probs >= lo) & (probs < hi)
        if b == n_bins - 1:
            mask |= probs == 1.0
        nb = int(mask.sum())
        if nb == 0:
            bin_rows.append({"bin": b, "lo": float(lo), "hi": float(hi),
                             "n": 0, "mean_pred": None, "empirical_rate": None})
            continue
        mean_pred = float(probs[mask].mean())
        emp = float(labels[mask].mean())
        bin_rows.append({"bin": b, "lo": float(lo), "hi": float(hi),
                         "n": nb, "mean_pred": round(mean_pred, 4),
                         "empirical_rate": round(emp, 4)})
        ece += (nb / n) * abs(emp - mean_pred)
    return {"brier": round(brier, 6), "ece": round(float(ece), 6),
            "bins": bin_rows, "n_rows": n, "n_bins": n_bins,
            "bin_type": "equal_width"}


def decompose_and_set_sizes(
    final_sets: dict[str, set],
    tasks_by_id: dict,
    repo_of: dict,
    case_ids: list[str],
) -> tuple[dict, dict]:
    """Error decomposition (A-F) + set-size analysis per repository."""
    decomp: dict[str, dict] = {}
    sizes: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        cids = [c for c in case_ids if repo_of[c] == repo]
        a = b = c = d = e = f = 0
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
            e += len((proxy - sparse) & (policy - sparse))
            f += len((policy - sparse) - proxy)
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
            "E_sparse_fn_correctly_added": e,
            "F_new_fp_added": f,
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
            "additions_distribution": {
                str(k): int(sum(1 for x in additions if x == k))
                for k in sorted(set(additions))
            },
        }
    return decomp, sizes


def evaluate_gate(results: dict, n_folds: int = N_FOLDS) -> dict:
    """Primary success gate (mission 23) + PARETO_SUCCESS (mission 24)."""
    gate: dict = {}
    pareto: dict = {}
    for repo in ("djangocms", "saleor"):
        m = results["repo_metrics"][repo]
        f1p = m["policy"]["f1"]
        f1s = m["sparse"]["f1"]
        rp = m["policy"]["recall"]
        rs = m["sparse"]["recall"]
        pp = m["policy"]["precision"]
        ps = m["sparse"]["precision"]
        fnrp = m["policy"]["fnr"]
        fnrs = m["sparse"]["fnr"]
        ci_f1 = results["bootstrap"][repo]["f1"]
        folds_ge = sum(1 for x in results["fold_deltas"][repo] if x >= 0.0)
        gate[repo] = {
            "A_f1_policy_gt_sparse": bool(f1p > f1s),
            "A_f1_policy": f1p,
            "A_f1_sparse": f1s,
            "B_ci_lower_delta_f1_gt0": bool(ci_f1["ci95_lower"] > 0),
            "B_delta_f1": ci_f1["point_delta"],
            "B_ci95_lower": ci_f1["ci95_lower"],
            "B_ci95_upper": ci_f1["ci95_upper"],
            "C_recall_policy_ge_sparse": bool(rp >= rs),
            "D_fnr_policy_le_sparse": bool(fnrp <= fnrs),
            "E_folds_delta_f1_ge0": bool(folds_ge >= 3),
            "E_n_folds_ge0": folds_ge,
            "E_n_folds": n_folds,
            "fold_deltas": results["fold_deltas"][repo],
            "pass": bool(
                f1p > f1s
                and ci_f1["ci95_lower"] > 0
                and rp >= rs
                and fnrp <= fnrs
                and folds_ge >= 3
            ),
        }
        pareto[repo] = bool(
            pp > ps and rp > rs and f1p > f1s and fnrp < fnrs
        )
    return {
        "gate": gate,
        "pareto_success": bool(all(pareto.values())),
        "pareto_per_repo": pareto,
        "both_repos_pass": bool(all(gate[r]["pass"] for r in gate)),
    }
