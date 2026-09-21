#!/usr/bin/env python3
"""WP-1b B2 - sample-size amendment manifests (MAIN_297 / MAIN_150 / MAIN_50).

Builds research/wp1b/wp1b_main_<N>_manifest.json from the frozen order in
research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.json:

  - MAIN_297: all 300 in frozen order, minus the 3 Calibration-3 tasks.
  - MAIN_150: the first 150 in frozen order, minus any Calibration-3 task among
    them (report the count).
  - MAIN_50:  the existing WP-1a manifest, unchanged (copied reference only).

Assertions:
  - first 50 IDs of the new MAIN_297 manifest == the WP-1a MAIN_50 task_ids
    exactly;
  - none of the 3 calibration IDs are in MAIN_297;
  - task_ids_sha256 and manifest_sha256 recorded as in the WP-1a manifests.

Execution order for Phase D = manifest order (MAIN_50 first).
The variance substudy stays exactly as preregistered (15 of MAIN_50, 3 fresh
runs each, salt unchanged).

Outputs:
- research/wp1b/wp1b_main_297_manifest.json
- research/wp1b/wp1b_main_150_manifest.json
- research/wp1b/wp1b_main_50_manifest.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
RESEARCH = _PROJECT_DIR / "research"
SAMPLE = RESEARCH / "saleor-reserve-300-rmcss" / "saleor_reserve_300_sample.json"
WP1A_MAIN50 = RESEARCH / "wp1a" / "wp1_main_50_manifest.json"
WP1A_CAL3 = RESEARCH / "wp1a" / "wp1_calibration_3_manifest.json"
OUT = RESEARCH / "wp1b"


def _sha256_lines(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(ids) + "\n").encode("utf-8")).hexdigest()


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def main() -> int:
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    ids = sample["selected_ids"]
    assert len(ids) == 300 and ids == sorted(ids), "frozen ordering must be sorted 300"

    main50 = json.loads(WP1A_MAIN50.read_text(encoding="utf-8"))
    cal3 = json.loads(WP1A_CAL3.read_text(encoding="utf-8"))
    main50_ids = main50["task_ids"]
    cal3_ids = cal3["task_ids"]

    cal_set = set(cal3_ids)
    main297 = [t for t in ids if t not in cal_set]
    main150 = [t for t in ids[:150] if t not in cal_set]
    cal_in_150 = [t for t in ids[:150] if t in cal_set]

    # Assert the first 50 IDs of the new manifest == WP-1a MAIN_50 exactly.
    assert main297[:50] == main50_ids, "first 50 of MAIN_297 must equal WP-1a MAIN_50"
    assert main50_ids[0] == ids[0], "ordering source mismatch"

    OUT.mkdir(parents=True, exist_ok=True)

    manifests = {}
    for name, task_ids, note in (
        ("wp1b_main_297_manifest.json", main297, "all 300 in frozen order minus the 3 Calibration-3 tasks"),
        ("wp1b_main_150_manifest.json", main150, "first 150 in frozen order minus any Calibration-3 task among them"),
        ("wp1b_main_50_manifest.json", main50_ids, "existing WP-1a manifest, unchanged (reference copy)"),
    ):
        manifest = {
            "wp1b": name[:-5],
            "n": len(task_ids),
            "selection_rule": note,
            "sample_source": "research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.json",
            "sample_sha256": sample["selected_ids_sha256"],
            "main_50_first_50_exact": task_ids[:50] == main50_ids,
            "calibration_ids_absent": not (set(task_ids) & cal_set),
            "calibration_ids_among_first_150": cal_in_150,
            "task_ids": task_ids,
            "task_ids_sha256": _sha256_lines(task_ids),
            "manifest_sha256": _sha256_json({"task_ids": task_ids}),
            "labels_not_used": True,
            "786_reserve_outcomes_not_accessed": True,
        }
        manifests[name] = manifest
        (OUT / name).write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    assert manifests["wp1b_main_297_manifest.json"]["task_ids_sha256"] == _sha256_lines(main297)
    assert manifests["wp1b_main_150_manifest.json"]["calibration_ids_absent"] is True

    print("[wp1b-b2] MAIN_297 n:", len(main297))
    print("[wp1b-b2] MAIN_150 n:", len(main150), "calibration_among_first_150:",
          cal_in_150, "count:", len(cal_in_150))
    print("[wp1b-b2] MAIN_50 n:", len(main50_ids), "first50_exact:",
          manifests["wp1b_main_297_manifest.json"]["main_50_first_50_exact"])
    print("[wp1b-b2] MAIN_297 task_ids_sha256:", manifests["wp1b_main_297_manifest.json"]["task_ids_sha256"])
    print("[wp1b-b2] MAIN_297 manifest_sha256:", manifests["wp1b_main_297_manifest.json"]["manifest_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
