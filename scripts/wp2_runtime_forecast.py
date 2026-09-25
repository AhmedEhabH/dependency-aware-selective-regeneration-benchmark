#!/usr/bin/env python3
"""WP-2 C2 runtime forecast (monitoring/planning only - ZERO API).

Calibrates FAST/MEDIUM/SLOW/VERY_SLOW buckets from the observed wall_s of the
220 completed MAIN Linux V2 tasks, using pre-outcome structural metadata
(changed production count, changed test count, added vs modified tests,
migration/config-heavy flag, environment era, candidate test file count).

Forecast only: never alters task inclusion, order, worker count, or oracle
semantics. Produces the per-bucket counts/medians and a C4 projection.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

PER_TASK = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "per_task_v2.jsonl"
CENSUS = PROJECT / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json"
DEV_CENSUS = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "dev_census_2026-09-23.json"
OUT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "c2_runtime_forecast_2026-09-23.json"

BUCKETS = ("FAST", "MEDIUM", "SLOW", "VERY_SLOW")


def bucket_of(wall_s: float, qs: list[float]) -> str:
    q1, q2, q3 = qs
    if wall_s <= q1:
        return "FAST"
    if wall_s <= q2:
        return "MEDIUM"
    if wall_s <= q3:
        return "SLOW"
    return "VERY_SLOW"


def main() -> int:
    rows = [
        json.loads(line)
        for line in PER_TASK.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    census = {t["task_id"]: t for t in json.loads(CENSUS.read_text(encoding="utf-8"))["tasks"]}
    dev = json.loads(DEV_CENSUS.read_text(encoding="utf-8"))

    walls = [r["wall_s"] for r in rows if r.get("wall_s")]
    walls_sorted = sorted(walls)
    n = len(walls_sorted)
    q1 = walls_sorted[n // 4 - 1]
    q2 = walls_sorted[n // 2 - 1]
    q3 = walls_sorted[(3 * n) // 4 - 1]
    qs = [q1, q2, q3]

    per_bucket: dict[str, list[float]] = {b: [] for b in BUCKETS}
    task_meta = {}
    for r in rows:
        b = bucket_of(r["wall_s"], qs)
        per_bucket[b].append(r["wall_s"])
        c = census.get(r["task_id"], {})
        task_meta[r["task_id"]] = {
            "bucket": b,
            "wall_s": r["wall_s"],
            "era": r.get("era_key"),
            "n_production": c.get("n_production", 0),
            "n_test": c.get("n_test", 0),
            "n_test_added": c.get("n_test_added", 0),
            "n_test_modified": c.get("n_test_modified", 0),
            "migration_or_config_heavy": (c.get("n_migration", 0) or 0) + (c.get("n_config_or_infra", 0) or 0) > 0,
        }

    buckets = {}
    for b in BUCKETS:
        ws = per_bucket[b]
        buckets[b] = {
            "count": len(ws),
            "completed": len(ws),
            "remaining": 0,
            "median_wall_s": round(statistics.median(ws), 1) if ws else None,
            "estimated_remaining_wall_s": 0.0,
        }

    # C4 projection using the calibrated bucket medians and the DEV census
    # structural metadata (111 changed-test candidates).
    c4_buckets = {b: 0 for b in BUCKETS}
    dev_tasks = dev["tasks"]
    changed = [t for t in dev_tasks if not t["no_changed_test_evidence"]]
    for t in changed:
        score = (t["n_test_added"] + t["n_test_modified"]) + t["n_migration"] * 2
        c4_buckets["FAST"] if score <= 1 else None
        # deterministic simple proxy: use test-file count and migration flag
        if t["n_changed_test"] <= 1 and not t["migration_or_config_heavy"]:
            c4_buckets["FAST"] += 1
        elif t["n_changed_test"] <= 3 and not t["migration_or_config_heavy"]:
            c4_buckets["MEDIUM"] += 1
        elif t["n_changed_test"] <= 5 or t["migration_or_config_heavy"]:
            c4_buckets["SLOW"] += 1
        else:
            c4_buckets["VERY_SLOW"] += 1
    c4_eta_s = sum(
        c4_buckets[b] * (buckets[b]["median_wall_s"] or 0) for b in BUCKETS
    )

    artifact = {
        "artifact": "wp2_c2_runtime_forecast",
        "date": "2026-09-23",
        "note": (
            "monitoring/planning only; calibrated from 220 completed C2 tasks; "
            "never alters inclusion/order/workers/oracle semantics"
        ),
        "calibration_thresholds_s": {"Q1": q1, "Q2": q2, "Q3": q3},
        "bucket_definition": "FAST<=Q1, MEDIUM=(Q1,Q2], SLOW=(Q2,Q3], VERY_SLOW>Q3",
        "buckets": buckets,
        "top_20_slowest_remaining": [],  # C2 complete: no remaining
        "expected_c2_completion": "COMPLETE (2026-09-24T17:47:14Z)",
        "c4_projection": {
            "n_changed_test_candidates": len(changed),
            "bucket_counts": c4_buckets,
            "estimated_remaining_wall_s": round(c4_eta_s, 0),
            "note": (
                "uses calibrated C2 bucket medians applied to DEV "
                "structural features"
            ),
        },
        "tasks": task_meta,
    }
    OUT.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")
    print("thresholds:", {"Q1": round(q1, 1), "Q2": round(q2, 1), "Q3": round(q3, 1)})
    for b in BUCKETS:
        print(f"  {b}: count={buckets[b]['count']} median={buckets[b]['median_wall_s']}s")
    print("C4 projection buckets:", c4_buckets, "eta_s=", round(c4_eta_s, 0))
    print("wrote", OUT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
