"""WP-1a Correction C - deterministic zero-API per-task SIP/RM-CSS re-derivation.

Reconstructs per-task predicted sets from the FROZEN Saleor-300 artifacts only:

- SIP predicted set: stored per-task ``predicted_write_set`` in
  ``sip_300_run_records.jsonl`` (the stored SIP predictions; NO LLM re-call).
- RM-CSS predicted set: deterministic re-derivation from the frozen candidate
  rows (label-free prediction view) + the frozen primary deployment artifact
  + the frozen threshold (0.20). No tuning, no label-dependent features.

Pipeline:
1. load SIP predicted sets from the frozen run records (fail-closed EMPTY for
   succeeded-empty and transport-failed records).
2. load the label-free prediction view (schema.load_prediction_view) and apply
   the frozen L2-LR model / StandardScaler from the deployment artifact to get
   per-candidate probabilities; RM-CSS predicted set = {file: prob >= thr}.
3. persist per-task predicted sets + prediction hashes + source/config/model
   hashes into a NEW frozen per-task artifact (does NOT replace the historical
   Saleor-300 result artifact).
4. verification (separate function): re-score the full 300 against the stored
   proxies (labels loaded ONLY after the prediction hashes are frozen) and
   require EXACT reproduction of the authoritative frozen headline values.
   Any mismatch -> WP1A_RMCSS_REDERIVATION_DRIFT (raise / fail closed).

Authoritative frozen headline values (reports/saleor_reserve_300_rmcss_result.json):
  SIP:     TP 193 FP 344 FN 728 P 0.35940409683426444 R 0.20955483170466885
           F1 0.26474622770919065
  RM-CSS:  TP 283 FP 382 FN 638 P 0.4255639097744361 R 0.30727470141150925
           F1 0.35687263556116017
  Delta F1 = 0.09212640785196952
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from benchmark.wp1a.schema import FEATURE_NAMES, load_prediction_view

FLOAT_TOLERANCE: float = 1e-9
THRESHOLD: float = 0.20

# Authoritative frozen headline values (must reproduce EXACTLY).
AUTHORITATIVE: dict[str, Any] = {
    "sip": {
        "tp": 193, "fp": 344, "fn": 728,
        "precision": 0.35940409683426444,
        "recall": 0.20955483170466885,
        "f1": 0.26474622770919065,
    },
    "rmcss": {
        "tp": 283, "fp": 382, "fn": 638,
        "precision": 0.4255639097744361,
        "recall": 0.30727470141150925,
        "f1": 0.35687263556116017,
    },
    "delta_f1": 0.09212640785196952,
}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return _sha256_text(canonical)


def load_sip_sets(records_path: Path) -> dict[str, set[str]]:
    """Load stored SIP predicted sets (fail-closed EMPTY on non-succeeded)."""
    sets: dict[str, set[str]] = {}
    for line in records_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        cid = rec["case_id"]
        if rec.get("terminal_status") == "succeeded":
            sets[cid] = set(rec.get("predicted_write_set") or [])
        else:
            sets[cid] = set()
    return sets


def apply_frozen_model(
    artifact: dict[str, Any], frame: pd.DataFrame
) -> NDArray[np.float64]:
    """Apply the frozen L2-LR + StandardScaler from the deployment artifact."""
    scaler = StandardScaler()
    scaler.mean_ = np.asarray(artifact["scaler_mean"], dtype=np.float64)
    scaler.scale_ = np.asarray(artifact["scaler_scale"], dtype=np.float64)
    scaler.var_ = scaler.scale_ ** 2
    scaler.n_features_in_ = len(artifact["scaler_mean"])
    model = LogisticRegression(penalty="l2", C=1.0, solver="liblinear",
                               max_iter=1000, random_state=0)
    idx_cont = [FEATURE_NAMES.index(c) for c in artifact["continuous_features"]]
    idx_bool = [FEATURE_NAMES.index(c) for c in artifact["boolean_features"]]
    x = frame[list(FEATURE_NAMES)].to_numpy(dtype=np.float64)
    x_cont = scaler.transform(x[:, idx_cont])
    x_bool = x[:, idx_bool].astype(np.float64)
    model.coef_ = np.asarray(artifact["lr_coef"], dtype=np.float64).reshape(1, -1)
    model.intercept_ = np.asarray([artifact["lr_intercept"]], dtype=np.float64)
    model.classes_ = np.asarray([0, 1])
    model.n_features_in_ = x_cont.shape[1] + x_bool.shape[1]
    prob = model.predict_proba(np.concatenate([x_cont, x_bool], axis=1))[:, 1]
    return np.asarray(prob, dtype=np.float64)


def derive_rmcss_sets(
    candidate_rows_path: Path,
    deployment_artifact: dict[str, Any],
    threshold: float = THRESHOLD,
) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Deterministic RM-CSS per-task predicted sets (label-free).

    Returns (predicted_sets, per_task_prediction_hash).
    """
    frame = load_prediction_view(candidate_rows_path)
    prob = apply_frozen_model(deployment_artifact, frame)
    frame = frame.copy()
    frame["prob"] = prob
    predicted: dict[str, set[str]] = {}
    hashes: dict[str, str] = {}
    for cid, g in frame.groupby("case_id", sort=True):
        selected = set(g.loc[g["prob"] >= threshold, "file_path"])
        predicted[cid] = selected
        hashes[cid] = _sha256_text("\n".join(sorted(selected)))
    return predicted, hashes


def rederive_per_task(
    *,
    records_path: Path,
    candidate_rows_path: Path,
    deployment_artifact_path: Path,
) -> dict[str, Any]:
    """Build the frozen per-task prediction artifact (label-free)."""
    deployment = json.loads(deployment_artifact_path.read_text(encoding="utf-8"))
    sip_sets = load_sip_sets(records_path)
    rmcss_sets, rmcss_hashes = derive_rmcss_sets(candidate_rows_path, deployment)

    task_ids = sorted(set(sip_sets) | set(rmcss_sets))
    assert len(task_ids) == 300, f"expected 300 tasks, got {len(task_ids)}"

    sip_hashes = {
        cid: _sha256_text("\n".join(sorted(sip_sets[cid]))) for cid in task_ids
    }

    per_task: dict[str, object] = {}
    for cid in task_ids:
        per_task[cid] = {
            "task_id": cid,
            "sip_predicted_set": sorted(sip_sets[cid]),
            "sip_prediction_hash": sip_hashes[cid],
            "rmcss_predicted_set": sorted(rmcss_sets[cid]),
            "rmcss_prediction_hash": rmcss_hashes[cid],
        }

    artifact = {
        "wp1a": "sip_rmcss_per_task_predictions",
        "generated_utc": None,
        "source_artifacts": {
            "sip_run_records": str(records_path),
            "candidate_rows": str(candidate_rows_path),
            "deployment_artifact": str(deployment_artifact_path),
            "deployment_config_sha256": deployment.get("config_sha256"),
            "threshold": THRESHOLD,
            "realization": deployment.get("realization"),
        },
        "model_identity": {
            "scientific_model": "qwen/qwen3-coder",
            "provider_tag": "deepinfra/turbo",
            "note": "SIP stored predictions reused verbatim; no LLM re-call. "
                    "RM-CSS is a frozen deterministic classifier (L2-LR), not a "
                    "generative model.",
        },
        "n_tasks": len(task_ids),
        "manifest_sha256": _sha256_json(per_task),
        "per_task": per_task,
    }
    return artifact


def _confusion(selected: set[str], proxy: set[str]) -> tuple[int, int, int]:
    tp = len(selected & proxy)
    fp = len(selected - proxy)
    fn = len(proxy - selected)
    return tp, fp, fn


def _metrics(tp: int, fp: int, fn: int) -> dict[str, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def verify_exact_reproduction(
    *,
    per_task_artifact: dict[str, Any],
    proxies_path: Path,
    tolerance: float = FLOAT_TOLERANCE,
) -> dict[str, Any]:
    """Re-score the full 300 and require EXACT reproduction of authoritative
    headline values. Labels (proxies) are loaded HERE, only AFTER the per-task
    prediction hashes were persisted.

    Raises WP1A_RMCSS_REDERIVATION_DRIFT on any mismatch.
    """
    proxies = json.loads(proxies_path.read_text(encoding="utf-8"))["proxies"]
    per_task = per_task_artifact["per_task"]
    task_ids = sorted(per_task)
    assert len(task_ids) == 300

    sip_tot = [0, 0, 0]
    rmcss_tot = [0, 0, 0]
    for cid in task_ids:
        proxy = set(proxies[cid])
        sip_t = _confusion(set(per_task[cid]["sip_predicted_set"]), proxy)
        rm_t = _confusion(set(per_task[cid]["rmcss_predicted_set"]), proxy)
        sip_tot = [s + a for s, a in zip(sip_tot, sip_t, strict=True)]
        rmcss_tot = [s + a for s, a in zip(rmcss_tot, rm_t, strict=True)]

    sip_m = _metrics(*sip_tot)
    rmcss_m = _metrics(*rmcss_tot)
    delta_f1 = rmcss_m["f1"] - sip_m["f1"]

    def _close(a: float, b: float, tol: float) -> bool:
        return abs(a - b) <= tol * max(1.0, abs(b))

    diffs: list[str] = []
    for name, got, exp in (
        ("sip.tp", sip_m["tp"], AUTHORITATIVE["sip"]["tp"]),
        ("sip.fp", sip_m["fp"], AUTHORITATIVE["sip"]["fp"]),
        ("sip.fn", sip_m["fn"], AUTHORITATIVE["sip"]["fn"]),
        ("sip.precision", sip_m["precision"], AUTHORITATIVE["sip"]["precision"]),
        ("sip.recall", sip_m["recall"], AUTHORITATIVE["sip"]["recall"]),
        ("sip.f1", sip_m["f1"], AUTHORITATIVE["sip"]["f1"]),
        ("rmcss.tp", rmcss_m["tp"], AUTHORITATIVE["rmcss"]["tp"]),
        ("rmcss.fp", rmcss_m["fp"], AUTHORITATIVE["rmcss"]["fp"]),
        ("rmcss.fn", rmcss_m["fn"], AUTHORITATIVE["rmcss"]["fn"]),
        ("rmcss.precision", rmcss_m["precision"], AUTHORITATIVE["rmcss"]["precision"]),
        ("rmcss.recall", rmcss_m["recall"], AUTHORITATIVE["rmcss"]["recall"]),
        ("rmcss.f1", rmcss_m["f1"], AUTHORITATIVE["rmcss"]["f1"]),
        ("delta_f1", delta_f1, AUTHORITATIVE["delta_f1"]),
    ):
        ok = (int(got) == int(exp) if isinstance(exp, int)
                  else _close(float(got), float(exp), tolerance))
        if not ok:
            diffs.append(f"{name}: got {got!r} expected {exp!r}")

    result = {
        "verification": "EXACT_REPRODUCTION" if not diffs else "WP1A_RMCSS_REDERIVATION_DRIFT",
        "sip": sip_m,
        "rmcss": rmcss_m,
        "delta_f1": delta_f1,
        "expected_delta_f1": AUTHORITATIVE["delta_f1"],
        "n_tasks": len(task_ids),
        "tolerance": tolerance,
        "diffs": diffs,
    }
    if diffs:
        raise ValueError(
            f"WP1A_RMCSS_REDERIVATION_DRIFT: {diffs}"
        )
    return result
