#!/usr/bin/env python3
"""V2 omission-risk analysis — merged V1+V2 development labels, single-feature.

Deterministic, zero additional API. Uses persisted V2 run records + v1 labels +
frozen feature extractor + Sparse-plan features. Checks the C4 gates:
1. >=10 pos, >=10 neg independent tasks
2. a predeclared feature/family above chance (random band)
3. directionally stable between DEV_TRAIN and DEV_VALIDATION

Output: research/transparency/v2_omission_risk_analysis.json
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.harness.djangocms import DjangoCMSRealCommitDataset  # noqa: E402
from benchmark.harness.interfaces import PublicCase  # noqa: E402
from benchmark.omission_risk import metrics  # noqa: E402
from benchmark.omission_risk.features import extract_features, feature_names  # noqa: E402
from benchmark.omission_risk.study import BOOTSTRAP_SEED  # noqa: E402

V1_LABELS = (
    _PROJECT_DIR
    / "research"
    / "omission-risk-feature-study-v1"
    / "sparse_v2_label_analysis"
    / "sparse_v2_labels.json"
)
V2_RECORDS = (
    _PROJECT_DIR
    / "research"
    / "omission-risk-feature-study-v1"
    / "v2_trainval"
    / "v2_trainval_run_records.jsonl"
)
V2_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
OUT = _PROJECT_DIR / "research" / "transparency" / "v2_omission_risk_analysis.json"

SEED = 20260916
SPARSE_PLAN_FEATURES = (
    "fp_regenerate_count",
    "fp_validate_count",
    "fp_human_review_count",
    "fp_action_entropy",
    "fp_mean_confidence",
    "fp_serialized_decision_count",
)
PEAKINESS = (
    "bm25_zero_count",
    "bm25_nonzero_frac",
    "bm25_relthresh_count",
    "bm25_top1_top2_margin",
)


def _mean(x) -> float:
    return float(np.mean(list(x))) if x else 0.0


def _shannon(probs) -> float:
    ps = [p for p in probs if p > 0]
    if not ps:
        return 0.0
    h = -sum(p * np.log(p) for p in ps)
    return h / np.log(len(ps)) if len(ps) > 1 else 0.0


def per_cell_action_features(raw_dir: Path) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for rid_file in raw_dir.glob("*.txt"):
        rid = rid_file.stem
        entry = {k: 0.0 for k in SPARSE_PLAN_FEATURES}
        try:
            raw = json.loads(rid_file.read_text(encoding="utf-8"))
            content = (raw.get("choices") or [{}])[0].get("message", {}).get("content", "")
            payload = json.loads(content)
            decisions = payload.get("decisions") or []
            counts: Counter[str] = Counter()
            confs: list[float] = []
            for d in decisions:
                counts[str(d.get("action", "")).upper()] += 1
                c = d.get("confidence")
                if isinstance(c, (int, float)) and not isinstance(c, bool):
                    confs.append(float(c))
            n_serialized = sum(counts.values())
            probs = [
                counts["REGENERATE"] / max(1, n_serialized),
                counts["VALIDATE"] / max(1, n_serialized),
                counts["HUMAN_REVIEW"] / max(1, n_serialized),
            ]
            entry = {
                "fp_regenerate_count": float(counts["REGENERATE"]),
                "fp_validate_count": float(counts["VALIDATE"]),
                "fp_human_review_count": float(counts["HUMAN_REVIEW"]),
                "fp_action_entropy": _shannon(probs),
                "fp_mean_confidence": _mean(confs),
                "fp_serialized_decision_count": float(n_serialized),
            }
        except Exception:
            pass
        out[rid] = entry
    return out


def load_v2_case(cid: str) -> PublicCase:
    case_dir = V2_DATASET / "scientific" / cid
    manifest = json.loads((case_dir / "case_manifest.json").read_text(encoding="utf-8"))
    intent = json.loads((case_dir / "public" / "intent.json").read_text(encoding="utf-8"))
    universe = json.loads((case_dir / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
    graph = json.loads((case_dir / "public" / "dependency_graph.json").read_text(encoding="utf-8"))
    record = manifest["record"]
    return PublicCase(
        case_id=cid,
        repository="djangocms",
        repository_url="",
        parent_commit=record["parent_commit"],
        target_commit=record["target_commit"],
        intent_text=intent["intent_text"],
        candidate_paths=tuple(str(r["path"]) for r in universe["records"]),
        candidate_records=tuple(universe["records"]),
        graph_edges=tuple((str(s), str(d)) for s, d in graph.get("edges", [])),
        public_bundle_sha256="",
    )


def main() -> int:
    v1 = json.loads(V1_LABELS.read_text(encoding="utf-8"))
    v1_tasks = v1["tasks"]

    recs = [
        json.loads(line)
        for line in V2_RECORDS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in recs:
        by_case[r["case_id"]].append(r)
    raw_dir = V2_RECORDS.parent / "v2_trainval_runs" / "raw"
    cell_actions = per_cell_action_features(raw_dir)

    ds_v1 = DjangoCMSRealCommitDataset(
        dataset_dir=_PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
    )
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assign = split["assignment"]

    rows: list[dict[str, Any]] = []
    for cid, task in sorted(v1_tasks.items()):
        case = ds_v1.load_public_case(cid)
        feats = extract_features(case)
        row = {"case_id": cid, "split_group": "V1_DEV", "has_fn": task["has_fn"]}
        row.update(feats)
        rows.append(row)

    for cid, cells in by_case.items():
        valid = [c for c in cells if c["terminal_status"] == "succeeded"]
        if not valid:
            continue
        case = load_v2_case(cid)
        feats = extract_features(case)
        proxy = set(valid[0]["hidden_proxy_used_after_inference"])
        rep_fn = [len(proxy - set(c.get("predicted_write_set") or [])) for c in valid]
        has_fn = int(any(fn >= 1 for fn in rep_fn))
        plan: dict[str, list[float]] = {k: [] for k in SPARSE_PLAN_FEATURES}
        for c in valid:
            ca = cell_actions.get(c["run_id"], {})
            for k in plan:
                plan[k].append(ca.get(k, 0.0))
        row = {"case_id": cid, "split_group": assign.get(cid, "V2_DEV"), "has_fn": has_fn}
        row.update(feats)
        row.update({k: _mean(v) for k, v in plan.items()})
        rows.append(row)

    all_features = list(feature_names()) + list(SPARSE_PLAN_FEATURES)
    y = [int(r["has_fn"]) for r in rows]
    n_pos = sum(y)
    n_neg = len(rows) - n_pos

    rng = random.Random(SEED)
    band_vals = []
    for _ in range(2000):
        risk = [rng.random() for _ in rows]
        band_vals.append(metrics.auroc(risk, y))
    bnd = {
        "q2_5": float(np.percentile(band_vals, 2.5)),
        "q97_5": float(np.percentile(band_vals, 97.5)),
    }

    single: dict[str, dict[str, Any]] = {}
    above = []
    for f in all_features:
        risk = [float(r.get(f, 0.0)) for r in rows]
        a = metrics.auroc(risk, y)
        prc = metrics.auprc(risk, y)
        b = metrics.bootstrap_ci(risk, y, metrics.auprc, seed=BOOTSTRAP_SEED)
        single[f] = {
            "auroc": a,
            "auroc_signed": metrics.auroc_direction(risk, y),
            "auprc": prc,
            "ci95": [b["ci95_low"], b["ci95_high"]],
        }
        radius = max(abs(bnd["q2_5"] - 0.5), abs(bnd["q97_5"] - 0.5))
        if abs(a - 0.5) > radius:
            above.append(f)

    def signed(rows_sub, f):
        risk = [float(r[f]) for r in rows_sub]
        yy = [int(r["has_fn"]) for r in rows_sub]
        if len(set(yy)) < 2 or np.std(risk) == 0:
            return None
        return metrics.auroc_direction(risk, yy)

    train_rows = [r for r in rows if r["split_group"] in ("V1_DEV", "DEV_TRAIN")]
    val_rows = [r for r in rows if r["split_group"] == "DEV_VALIDATION"]
    stability = {}
    for f in PEAKINESS:
        stability[f] = {
            "train_signed": signed(train_rows, f),
            "val_signed": signed(val_rows, f),
        }

    result = {
        "merged": {
            "n": len(rows),
            "pos": n_pos,
            "neg": n_neg,
            "prevalence": round(n_pos / len(rows), 4),
            "class_balance_gate": n_pos >= 10 and n_neg >= 10,
        },
        "random_band": bnd,
        "features_above_random_95": sorted(above),
        "n_features_above": len(above),
        "expected_by_chance": round(len(all_features) * 0.05, 2),
        "top_features_by_auprc": sorted(
            [(f, round(single[f]["auprc"], 3)) for f in single], key=lambda x: -x[1]
        )[:10],
        "peakiness_direction_stability": stability,
        "c4_gate_2_signal_above_chance": len(above) > len(all_features) * 0.05,
        "c4_gate_3_direction_stable": all(
            stability[f]["train_signed"] is not None
            and stability[f]["val_signed"] is not None
            and (stability[f]["train_signed"] > 0.5) == (stability[f]["val_signed"] > 0.5)
            for f in PEAKINESS
            if stability[f]["train_signed"] is not None
            and stability[f]["val_signed"] is not None
        ),
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
