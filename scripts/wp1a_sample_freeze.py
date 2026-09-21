"""WP-1a sample freeze - main n=50 + calibration n=3 (disjoint, label-free).

Rule (documented, deterministic):
- population: ONLY the already-opened Saleor-300 sample (selected_ids from
  research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.json, frozen
  deterministic ordering).
- Main set: the FIRST 50 tasks in the frozen deterministic sample ordering
  (as proposed by docs/WP1_REPOSITORY_AGENT_SELECTION_ONLY_BASELINE_DRAFT.md).
- Calibration set: n=3 drawn deterministically from the same 300 WITHOUT
  labels/difficulty, using numpy.random.default_rng(20260921) (a distinct,
  documented seed) over the sorted COMPLEMENT of the main-50, size 3,
  replace=False, output sorted lexicographically. Always disjoint from main 50.
- The 786 remaining Saleor RESERVE outcomes are NEVER accessed.

Outputs:
- research/wp1a/wp1_main_50_manifest.json
- research/wp1a/wp1_calibration_3_manifest.json
- research/wp1a/wp1_sample_freeze.json (aggregate + disjointness assertion)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = _PROJECT_DIR / "research" / "wp1a"
SAMPLE = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_sample.json"
SAMPLE_SHA = "445b5e9d0aeeab9551e8feeb3e59e6b5bcfee793f029810a6efe0cbc8f126447"

MAIN_N = 50
CAL_N = 3
CAL_SEED = 20260921


def _sha256_lines(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(ids) + "\n").encode("utf-8")).hexdigest()


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def main() -> int:
    import numpy as np

    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    ids = sample["selected_ids"]
    assert len(ids) == 300 and len(set(ids)) == 300
    assert sample["sampling_seed"] == 20260920
    assert _sha256_lines(ids) == SAMPLE_SHA, "frozen sample ordering hash mismatch"

    main_50 = ids[:MAIN_N]
    main_set = set(main_50)
    assert len(main_set) == MAIN_N

    complement = sorted(set(ids) - main_set)
    assert len(complement) == 300 - MAIN_N

    rng = np.random.default_rng(CAL_SEED)
    cal_3 = sorted(str(x) for x in rng.choice(
        np.asarray(complement, dtype=object), size=CAL_N, replace=False
    ))
    cal_set = set(cal_3)
    assert len(cal_set) == CAL_N
    assert cal_set.isdisjoint(main_set), "main/calibration intersection must be empty"

    main_manifest = {
        "wp1a": "wp1_main_50_manifest",
        "n": MAIN_N,
        "selection_rule": (
            "first 50 tasks in the frozen Saleor-300 deterministic sample "
            "ordering (no label/difficulty filtering)"
        ),
        "sample_source": "research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.json",
        "sample_sha256": SAMPLE_SHA,
        "task_ids": main_50,
        "task_ids_sha256": _sha256_lines(main_50),
        "manifest_sha256": _sha256_json({"task_ids": main_50}),
        "labels_not_used": True,
        "786_reserve_outcomes_not_accessed": True,
    }
    cal_manifest = {
        "wp1a": "wp1_calibration_3_manifest",
        "n": CAL_N,
        "selection_rule": (
            f"numpy.random.default_rng({CAL_SEED}).choice over the sorted "
            f"complement of the main-{MAIN_N}, size {CAL_N}, replace=False, "
            "output sorted; no label/difficulty filtering"
        ),
        "sample_source": "research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.json",
        "sample_sha256": SAMPLE_SHA,
        "task_ids": cal_3,
        "task_ids_sha256": _sha256_lines(cal_3),
        "manifest_sha256": _sha256_json({"task_ids": cal_3}),
        "labels_not_used": True,
        "786_reserve_outcomes_not_accessed": True,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "wp1_main_50_manifest.json").write_text(
        json.dumps(main_manifest, indent=1), encoding="utf-8")
    (OUT_DIR / "wp1_calibration_3_manifest.json").write_text(
        json.dumps(cal_manifest, indent=1), encoding="utf-8")

    aggregate = {
        "wp1a": "wp1_sample_freeze",
        "main_n": MAIN_N,
        "calibration_n": CAL_N,
        "main_task_ids_sha256": main_manifest["task_ids_sha256"],
        "calibration_task_ids_sha256": cal_manifest["task_ids_sha256"],
        "intersection_empty": main_set.isdisjoint(cal_set),
        "intersection_size": len(main_set & cal_set),
        "all_from_opened_300": (main_set | cal_set).issubset(set(ids)),
        "786_reserve_outcomes_not_accessed": True,
    }
    (OUT_DIR / "wp1_sample_freeze.json").write_text(
        json.dumps(aggregate, indent=1), encoding="utf-8")

    print("[wp1a-freeze] main 50 sha:", main_manifest["task_ids_sha256"])
    print("[wp1a-freeze] calibration 3 sha:", cal_manifest["task_ids_sha256"])
    print("[wp1a-freeze] calibration ids:", cal_3)
    print("[wp1a-freeze] intersection_empty:", aggregate["intersection_empty"])
    print("[wp1a-freeze] all_from_opened_300:", aggregate["all_from_opened_300"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
