#!/usr/bin/env python3
"""M4A-3 / P1 — recompute serialized decision counts from persisted raw evidence.

PRIORITY-0 CORRECTION ARTIFACT GENERATOR (ZERO API CALLS).

Context: the original P1 metrics (`research/real-commit-p1-01/final_metrics.json`)
computed `serialized_records` and task-level `*_records_mean` from
`len(decoded_write_set_ids)`. That field contains ONLY decoded REGENERATE ids
— the predicted write-set size — NOT the number of decision rows the model
actually serialized. For Full-v2 the model serializes one explicit decision per
candidate; for Sparse-v2 it serializes only non-PRESERVE decisions (which may
include VALIDATE / HUMAN_REVIEW rows that REGENERATE-only counting drops).

This script reconstructs the true serialized decision count for every one of
the 60 frozen P1 cells by parsing the persisted raw provider responses
(`research/real-commit-p1-01/runs/raw/<run_id>.txt`):

    parsed = json.loads(raw)
    payload = json.loads(parsed["choices"][0]["message"]["content"])
    serialized_decision_count = len(payload["decisions"])

and persists:

- per-cell `serialized_decision_count` and `predicted_write_set_size`
  into `research/real-commit-p1-01/serialization_metric_corrected.json`;
- corrected arm/task/bootstrap serialized-record metrics into
  `research/real-commit-p1-01/final_metrics_serialization_corrected.json`;
- the human-readable correction report
  `reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md`.

Independently asserts, for every valid cell:
- Full-v2: `serialized_decision_count == candidate_count`;
- Sparse-v2: no explicit PRESERVE rows AND
  `serialized_decision_count == number of explicit non-PRESERVE decisions`.

Nothing else is recomputed: P/R/F1/FNR, TP/FP/FN, validity, truncation, token
usage, cost, and latency are read unchanged from the persisted run records.
Raw response bytes are NEVER modified.

Usage:
    python scripts/recompute_real_commit_p1_serialization_metric.py
"""

from __future__ import annotations

import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import p1_evaluation as p1  # noqa: E402

STUDY_DIR = _PROJECT_DIR / "research" / "real-commit-p1-01"
REPORTS_DIR = _PROJECT_DIR / "reports"
RAW_DIR = STUDY_DIR / "runs" / "raw"
RECORDS_PATH = STUDY_DIR / "run_records.jsonl"
ORIGINAL_METRICS_PATH = STUDY_DIR / "final_metrics.json"
CORRECTED_METRICS_PATH = STUDY_DIR / "final_metrics_serialization_corrected.json"
PER_CELL_PATH = STUDY_DIR / "serialization_metric_corrected.json"
REPORT_PATH = REPORTS_DIR / "REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md"

ARMS = ("full_v2", "sparse_v2")
BOOTSTRAP_SEED = 20260914
BOOTSTRAP_ITERS = 10000


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "n": 0}
    n = len(values)
    s = sorted(values)
    mean = sum(values) / n
    median = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"mean": round(mean, 6), "median": round(median, 6), "min": round(s[0], 6), "max": round(s[-1], 6), "n": n}


def _load_records() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in RECORDS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["run_id"]] = rec
    return out


def _load_manifest_cells() -> list[dict[str, Any]]:
    manifest = json.loads((STUDY_DIR / "manifest_60.json").read_text(encoding="utf-8"))
    cells = manifest["cells"]
    assert isinstance(cells, list)
    return cells


def recompute_serialized_counts(records: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Parse every persisted raw response and derive per-cell serialized counts.

    Returns (per_cell_payload, audit_entries). Raises on integrity failures.
    """
    per_cell: dict[str, Any] = {}
    audit: list[dict[str, Any]] = []
    for run_id, rec in records.items():
        raw_path = RAW_DIR / f"{run_id}.txt"
        if not raw_path.is_file():
            raise FileNotFoundError(f"missing raw response: {raw_path}")
        raw_text = raw_path.read_text(encoding="utf-8")

        entry: dict[str, Any] = {
            "run_id": run_id,
            "case_id": rec["case_id"],
            "repetition": rec["repetition"],
            "arm": rec["arm"],
            "candidate_count": rec["decoded_candidate_count"],
            "predicted_write_set_size": len(rec.get("decoded_write_set_ids") or []),
            "terminal_status": rec.get("terminal_status"),
            "schema_valid": rec.get("schema_valid"),
            "raw_response_sha256": rec.get("raw_response_sha256", ""),
        }

        serialized_count, errors = p1.serialized_decision_count_from_raw(raw_text)
        entry["serialized_decision_count"] = serialized_count
        entry["parse_errors"] = errors

        if not entry["schema_valid"]:
            entry["assert_ok"] = False
            entry["assert_message"] = "cell is not schema-valid; serialized count not asserted"
            per_cell[run_id] = entry
            audit.append(entry)
            continue

        if entry["arm"] == "full_v2":
            ok = serialized_count == entry["candidate_count"]
            msg = (
                f"full_v2 serialized_decision_count {serialized_count} == candidate_count {entry['candidate_count']}"
                if ok
                else f"MISMATCH: serialized {serialized_count} != candidate_count {entry['candidate_count']}"
            )
        else:
            items = p1.raw_decision_items(raw_text)
            preserve_rows = [d for d in items if str(d.get("action") or "").upper() == "PRESERVE"]
            non_preserve = [d for d in items if str(d.get("action") or "").upper() != "PRESERVE"]
            ok = (not preserve_rows) and (serialized_count == len(non_preserve))
            msg = (
                f"sparse_v2 serialized {serialized_count} == non-PRESERVE "
                f"{len(non_preserve)}, explicit PRESERVE rows {len(preserve_rows)}"
                if ok
                else f"SPARSE MISMATCH: serialized {serialized_count}, "
                f"non-PRESERVE {len(non_preserve)}, PRESERVE rows {len(preserve_rows)}"
            )
        entry["assert_ok"] = ok
        entry["assert_message"] = msg
        per_cell[run_id] = entry
        audit.append(entry)
    return per_cell, audit


def _task_records(records: dict[str, dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    out: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for r in records.values():
        out.setdefault(r["case_id"], {}).setdefault(r["arm"], []).append(r)
    return out


def _bootstrap_paired(task_level: dict[str, dict[str, Any]], case_ids: list[str]) -> dict[str, Any]:
    rng = random.Random(BOOTSTRAP_SEED)
    deltas: list[float] = []
    for _ in range(BOOTSTRAP_ITERS):
        sample = [task_level[rng.choice(case_ids)] for _ in case_ids]
        vals = [t["sparse_v2_records_mean"] - t["full_v2_records_mean"] for t in sample]
        deltas.append(sum(vals) / len(vals))
    s = sorted(deltas)
    return {
        "mean_delta": round(sum(deltas) / len(deltas), 6),
        "ci95_low": round(s[int(0.025 * BOOTSTRAP_ITERS)], 6),
        "ci95_high": round(s[int(0.975 * BOOTSTRAP_ITERS)], 6),
    }


def recompute_corrected_metrics(
    records: dict[str, dict[str, Any]],
    per_cell: dict[str, Any],
) -> dict[str, Any]:
    rows_all = list(records.values())
    case_ids = p1.held_out_case_ids(_PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1")
    by_task = _task_records(records)

    def _serial_count(run_id: str) -> int:
        return int(per_cell[run_id]["serialized_decision_count"])

    def _write_size(run_id: str) -> int:
        return int(per_cell[run_id]["predicted_write_set_size"])

    per_arm: dict[str, Any] = {}
    for arm in ARMS:
        arm_rows = [r for r in rows_all if r["arm"] == arm]
        per_arm[arm] = {
            "arm": arm,
            "recorded": len(arm_rows),
            "valid": len(arm_rows),
            "serialized_records": _stats([float(_serial_count(r["run_id"])) for r in arm_rows]),
            "predicted_write_set_size": _stats([float(_write_size(r["run_id"])) for r in arm_rows]),
            "write_set_size": _stats([float(len(r.get("decoded_write_set_ids") or [])) for r in arm_rows]),
        }

    task_level: dict[str, dict[str, Any]] = {}
    paired: dict[str, dict[str, Any]] = {}
    for cid in case_ids:
        arms = by_task.get(cid, {})
        entry: dict[str, Any] = {"case_id": cid}
        for arm in ARMS:
            rows = arms.get(arm, [])
            entry[f"{arm}_records_mean"] = _stats(
                [float(_serial_count(r["run_id"])) for r in rows]
            )["mean"]
            entry[f"{arm}_write_set_size_mean"] = _stats(
                [float(len(r.get("decoded_write_set_ids") or [])) for r in rows]
            )["mean"]
        task_level[cid] = entry
        paired[cid] = {
            "case_id": cid,
            "delta_records_mean": round(
                entry["sparse_v2_records_mean"] - entry["full_v2_records_mean"], 6
            ),
            "delta_write_set_size_mean": round(
                entry["sparse_v2_write_set_size_mean"] - entry["full_v2_write_set_size_mean"], 6
            ),
        }

    bootstrap = _bootstrap_paired(task_level, case_ids)

    original = {}
    if ORIGINAL_METRICS_PATH.is_file():
        original = json.loads(ORIGINAL_METRICS_PATH.read_text(encoding="utf-8"))

    return {
        "study_id": "real-commit-p1-full-v2-vs-sparse-v2-01",
        "correction_kind": "serialized-record derived metric recomputed from persisted raw responses",
        "independent_tasks": len(case_ids),
        "nested_repetitions": p1.P1_REPETITIONS,
        "arms": per_arm,
        "task_level": task_level,
        "paired_task_level_deltas": paired,
        "bootstrap_over_tasks": {"records": bootstrap},
        "original_metrics_reference": {
            "path": str(ORIGINAL_METRICS_PATH.relative_to(_PROJECT_DIR)),
            "arms_serialized_records": {
                arm: original.get("arms", {}).get(arm, {}).get("serialized_records", {})
                for arm in ARMS
            },
            "bootstrap_records": original.get("bootstrap_over_tasks", {}).get("records", {}),
        },
        "computed_at": _now_iso(),
    }


def _render_report(
    per_cell: dict[str, Any],
    audit: list[dict[str, Any]],
    corrected: dict[str, Any],
) -> str:
    arms = corrected["arms"]
    full = arms["full_v2"]
    sparse = arms["sparse_v2"]
    boot = corrected["bootstrap_over_tasks"]["records"]
    orig_full = corrected["original_metrics_reference"]["arms_serialized_records"]["full_v2"]
    orig_sparse = corrected["original_metrics_reference"]["arms_serialized_records"]["sparse_v2"]
    orig_boot = corrected["original_metrics_reference"]["bootstrap_records"]

    failed_asserts = [a for a in audit if not a.get("assert_ok")]
    lines = [
        "# M4A-3 / P1 — Serialized-Record Metric Correction",
        "",
        "**Date:** 2026-09-14",
        "**Study:** `real-commit-p1-full-v2-vs-sparse-v2-01`",
        "**Type:** derived-metric recomputation from persisted raw responses (ZERO API calls).",
        "",
        "## 1. Defect",
        "",
        "The original metrics (`final_metrics.json`) computed `serialized_records` and",
        "task-level `*_records_mean` from `len(decoded_write_set_ids)`. That field holds",
        "ONLY decoded `REGENERATE` candidate ids — the **predicted write-set size** — and",
        "is NOT the number of decision rows the model serialized. Evidence of the",
        "mislabel: Full-v2 must serialize exactly one decision per candidate (the frozen",
        "manifest candidate counts are 140–152, mean 144), yet the original report showed",
        "`Records mean = 4.03`, which equals the mean REGENERATE write-set size.",
        "",
        "## 2. Method",
        "",
        "For each of the 60 frozen P1 cells, the persisted raw provider response",
        "(`research/real-commit-p1-01/runs/raw/<run_id>.txt`) is parsed:",
        "",
        "    parsed = json.loads(raw)",
        "    payload = json.loads(parsed[\"choices\"][0][\"message\"][\"content\"])",
        "    serialized_decision_count = len(payload[\"decisions\"])",
        "",
        "`serialized_decision_count` is persisted per cell; `predicted_write_set_size`",
        "is retained separately as `len(decoded_write_set_ids)`. Raw response bytes are",
        "never modified. P/R/F1/FNR, TP/FP/FN, validity, truncation, token usage, cost,",
        "and latency are read unchanged from the persisted run records.",
        "",
        "## 3. Independent assertions (every valid cell)",
        "",
        "- Full-v2: `serialized_decision_count == candidate_count` — asserted for",
        "  all valid cells; **failures:",
        f"  {sum(1 for a in audit if a['arm'] == 'full_v2' and not a.get('assert_ok'))}**.",
        "- Sparse-v2: no explicit `PRESERVE` rows AND `serialized_decision_count`",
        "  == explicit non-PRESERVE decision count — **failures:",
        f"  {sum(1 for a in audit if a['arm'] == 'sparse_v2' and not a.get('assert_ok'))}**.",
        f"- Total cells parsed: {len(per_cell)}; total assertion failures: {len(failed_asserts)}.",
        "",
        "## 4. Corrected serialized-record metrics",
        "",
        "| Arm | Serialized records mean | Predicted write-set mean |",
        "|---|---:|---:|",
        f"| Full-v2 | **{full['serialized_records']['mean']:.3f}** | "
        f"{full['write_set_size']['mean']:.3f} |",
        f"| Sparse-v2 | **{sparse['serialized_records']['mean']:.3f}** | "
        f"{sparse['write_set_size']['mean']:.3f} |",
        "",
        "Paired task-level delta (Sparse − Full) in serialized records + bootstrap CI:",
        "",
        f"- mean delta: **{boot['mean_delta']:.3f}**",
        f"- 95% bootstrap CI: **[{boot['ci95_low']:.3f}, {boot['ci95_high']:.3f}]** "
        f"(10,000 resamples over 10 tasks, seed {BOOTSTRAP_SEED})",
        "",
        "## 5. Former (mislabeled) values for comparison",
        "",
        "| Quantity | Former (write-set size) | Corrected (serialized decisions) |",
        "|---|---:|---:|",
        f"| Full-v2 mean | {orig_full.get('mean', 'n/a')} | **{full['serialized_records']['mean']:.3f}** |",
        f"| Sparse-v2 mean | {orig_sparse.get('mean', 'n/a')} | **{sparse['serialized_records']['mean']:.3f}** |",
        f"| Delta mean | {orig_boot.get('mean_delta', 'n/a')} | **{boot['mean_delta']:.3f}** |",
        f"| Delta CI | [{orig_boot.get('ci95_low', 'n/a')}, "
        f"{orig_boot.get('ci95_high', 'n/a')}] | **[{boot['ci95_low']:.3f}, "
        f"{boot['ci95_high']:.3f}]** |",
        "",
        "## 6. Interpretation impact",
        "",
        "- The serialized-record reduction of Sparse-v2 is **larger** than the former",
        "  write-set-only value indicated (Sparse now correctly includes explicit",
        "  VALIDATE / HUMAN_REVIEW rows; Full-v2 is the full candidate serialization).",
        "- Semantic metrics (P/R/F1/FNR), validity, truncation, tokens, cost, and",
        "  latency are **unchanged** — this correction affects only the serialized",
        "  decision-record derived metric.",
        "- The historical diff remains an **OBSERVED CHANGE-SET PROXY**, never semantic",
        "  ground truth.",
        "",
        "## 7. Artifacts",
        "",
        "- `research/real-commit-p1-01/final_metrics_serialization_corrected.json`",
        "- `research/real-commit-p1-01/serialization_metric_corrected.json` (per-cell)",
        "- `research/real-commit-p1-01/final_metrics.json` (original, UNCHANGED)",
        "- This report.",
        "",
        "## 8. Regression coverage",
        "",
        "`tests/unit/test_real_commit_p1_serialization_metric.py` proves Full-v2",
        "record count equals candidate count and Sparse-v2 record count derives from",
        "raw `decisions` (not write-set size). `tests/integration/` re-runs this",
        "recomputation against the persisted evidence.",
        "",
        "## 9. Related findings from the same audit (NOT re-run here)",
        "",
        "The same defect pattern (reporting `len(decoded_write_set_ids)` as",
        "\"serialized records\") exists in the runners for the **M1B controlled 16K",
        "study** (`scripts/controlled_encoding_ablation_execute.py`, sparse arm) and",
        "the **M3 graph ablation** (`scripts/graph_ablation_execute.py`). The frozen",
        "M1B/M3 final-metrics JSONs and result reports are NOT rewritten in this",
        "milestone (historical evidence preserved). Both runners are fixed",
        "prospectively so any future re-execution persists `serialized_decision_count`",
        "alongside `predicted_write_set_size`. Audit-quantified magnitude for M1B",
        "sparse-v2 from the persisted raw responses: serialized decision mean **5.9**",
        "vs the reported write-set mean **4.9**. Registered as technical-debt items",
        "TD-011/TD-012 for a separate decision.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    records = _load_records()
    cells = _load_manifest_cells()
    if len(records) != len(cells):
        print(f"expected {len(cells)} records, found {len(records)}")
        return 2

    per_cell, audit = recompute_serialized_counts(records)
    failures = [a for a in audit if not a.get("assert_ok")]
    if failures:
        print("ASSERTION FAILURES:")
        for f in failures:
            print(f"  {f['run_id']}: {f['assert_message']}")
        return 1

    corrected = recompute_corrected_metrics(records, per_cell)
    per_cell_payload = {
        "study_id": "real-commit-p1-full-v2-vs-sparse-v2-01",
        "correction_kind": "per-cell serialized decision count parsed from persisted raw responses",
        "cells": list(per_cell.values()),
        "computed_at": _now_iso(),
    }

    PER_CELL_PATH.write_text(json.dumps(per_cell_payload, indent=2, default=str), encoding="utf-8")
    CORRECTED_METRICS_PATH.write_text(json.dumps(corrected, indent=2, default=str), encoding="utf-8")
    REPORT_PATH.write_text(_render_report(per_cell, audit, corrected), encoding="utf-8")

    print(json.dumps(corrected["arms"], indent=2))
    print(json.dumps(corrected["bootstrap_over_tasks"], indent=2))
    print(f"per-cell corrected: {PER_CELL_PATH}")
    print(f"corrected metrics: {CORRECTED_METRICS_PATH}")
    print(f"correction report: {REPORT_PATH}")
    print("SERIALIZATION_METRIC_CORRECTION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
