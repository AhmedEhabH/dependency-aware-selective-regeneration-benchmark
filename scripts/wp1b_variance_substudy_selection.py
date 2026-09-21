#!/usr/bin/env python3
"""WP-1b G5 - deterministic variance-substudy subset selection (15 of main-50).

Selection rule (frozen prospectively, BEFORE any WP-1b outcome):
1. Take the canonical task IDs from the frozen main-50 manifest
   (research/wp1a/wp1_main_50_manifest.json).
2. Compute sha256("<fixed-preregistered-salt>" + task_id) for each.
3. Sort ascending by digest.
4. Select the first 15.

Salt: fixed preregistered constant. No task outcome, difficulty, or method
output is used. Deterministic and reproducible.

Outputs:
- artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
MAIN_50 = _PROJECT_DIR / "research" / "wp1a" / "wp1_main_50_manifest.json"
OUT = _PROJECT_DIR / "artifacts" / "wp1b_variance_substudy_preregistration_2026-09-21.json"

SALT = "wp1b-variance-substudy-v1-2026-09-21"
SUBSET_SIZE = 15
RUNS_PER_TASK = 3


def select_subset(task_ids: list[str], salt: str = SALT, size: int = SUBSET_SIZE) -> list[str]:
    entries = []
    for tid in task_ids:
        digest = hashlib.sha256((salt + tid).encode("utf-8")).hexdigest()
        entries.append((digest, tid))
    entries.sort(key=lambda e: e[0])
    return [tid for _, tid in entries[:size]]


def main() -> int:
    main_manifest = json.loads(MAIN_50.read_text(encoding="utf-8"))
    task_ids = main_manifest["task_ids"]
    assert len(task_ids) == 50, f"expected 50 main tasks, got {len(task_ids)}"

    digests = sorted((hashlib.sha256((SALT + tid).encode("utf-8")).hexdigest(), tid) for tid in task_ids)
    selected = [tid for _, tid in digests[:SUBSET_SIZE]]

    manifest = {
        "artifact": "wp1b_variance_substudy_preregistration",
        "date": "2026-09-21",
        "status": "PREREGISTERED_BEFORE_OUTCOMES",
        "salt": SALT,
        "algorithm": "sha256(salt + task_id), sort ascending by digest, first 15",
        "subset_size": SUBSET_SIZE,
        "runs_per_selected_task": RUNS_PER_TASK,
        "temperature": "0.0 (unchanged from main protocol)",
        "scientific_knobs_identical_to_main": True,
        "first_main_execution_may_count_as_replicate_1": False,
        "first_main_execution_note": "NOT pre-registered as replicate 1; all 3 repeats are fresh executions.",
        "source_manifest": str(MAIN_50),
        "source_main_task_ids_sha256": main_manifest["task_ids_sha256"],
        "ordered_digests": [d for d, _ in digests],
        "selected_15_task_ids": selected,
        "selection_manifest_sha256": hashlib.sha256(
            json.dumps({"salt": SALT, "selected": selected}, sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "no_outcome_used": True,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    print(f"[variance-substudy] salt: {SALT}")
    print(f"[variance-substudy] selected 15: {selected}")
    print(f"[variance-substudy] selection manifest sha256: {manifest['selection_manifest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
