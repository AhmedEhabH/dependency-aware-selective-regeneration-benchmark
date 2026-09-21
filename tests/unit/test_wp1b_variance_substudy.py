"""WP-1b G5 - variance-substudy subset determinism tests.

Protects the Impact Correctness validity dimension: the 15-task subset must be
deterministic, reproducible, and free of outcome influence.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

ARTIFACTS = PROJECT_DIR / "artifacts"
SALT = "wp1b-variance-substudy-v1-2026-09-21"
EXPECTED = [
    "saleor-rc-1a8b592913a0",
    "saleor-rc-1f6fbe2ebf9b",
    "saleor-rc-032b98afff20",
    "saleor-rc-0ad61b3f0096",
    "saleor-rc-070f4bd7c042",
    "saleor-rc-11756ee6b65a",
    "saleor-rc-22a30bf2e4cc",
    "saleor-rc-0f16ed78b02b",
    "saleor-rc-19bb9b070965",
    "saleor-rc-14f2176b5d8c",
    "saleor-rc-0713acb0f004",
    "saleor-rc-07c8859c0ac3",
    "saleor-rc-1f9b5c53a63a",
    "saleor-rc-1b4da5a88d08",
    "saleor-rc-0df62b3144b0",
]


def test_selection_is_deterministic() -> None:
    result = subprocess.run(
        [sys.executable, str(PROJECT_DIR / "scripts" / "wp1b_variance_substudy_selection.py")],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads(
        (ARTIFACTS / "wp1b_variance_substudy_preregistration_2026-09-21.json").read_text(encoding="utf-8")
    )
    assert manifest["salt"] == SALT
    assert manifest["selected_15_task_ids"] == EXPECTED
    assert len(set(manifest["selected_15_task_ids"])) == 15
    assert manifest["first_main_execution_may_count_as_replicate_1"] is False


def test_selected_subset_is_outcome_free() -> None:
    manifest = json.loads(
        (ARTIFACTS / "wp1b_variance_substudy_preregistration_2026-09-21.json").read_text(encoding="utf-8")
    )
    assert manifest["no_outcome_used"] is True
    assert manifest["status"] == "PREREGISTERED_BEFORE_OUTCOMES"
    assert manifest["subset_size"] == 15
    assert manifest["runs_per_selected_task"] == 3
    assert manifest["scientific_knobs_identical_to_main"] is True


def test_digest_order_matches_selection() -> None:
    manifest = json.loads(
        (ARTIFACTS / "wp1b_variance_substudy_preregistration_2026-09-21.json").read_text(encoding="utf-8")
    )
    ordered_digests = manifest["ordered_digests"]
    assert len(ordered_digests) == 50
    assert ordered_digests == sorted(ordered_digests)
    selected = manifest["selected_15_task_ids"]
    main = json.loads((PROJECT_DIR / "research" / "wp1a" / "wp1_main_50_manifest.json").read_text(encoding="utf-8"))
    for tid in selected:
        assert tid in main["task_ids"]
