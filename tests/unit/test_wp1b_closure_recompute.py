"""WP-1b closure recomputation tests (mission PHASE 2).

Protects the Impact Correctness validity dimension (frozen metric/evidence
values are recomputed from raw artifacts without importing the audited WP-1a
helpers).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def _run_recompute(out_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_DIR / "scripts" / "wp1b_closure_recompute.py"),
         "--out", str(out_dir)],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=300,
    )


def _read_recomputation(out_dir: Path) -> dict:
    return json.loads((out_dir / "wp1a_wp1b_closure_recomputation.json").read_text(encoding="utf-8"))


def test_recompute_overall_pass(tmp_path: Path) -> None:
    result = _run_recompute(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OVERALL: PASS" in result.stdout


def test_recomputed_hashes_and_splits(tmp_path: Path) -> None:
    _run_recompute(tmp_path)
    data = _read_recomputation(tmp_path)
    splits = data["sample_and_splits"]
    assert splits["sample_hash_match"] is True
    assert splits["main_50"]["task_ids_sha256"] == "9b26ad5965f6f6a134c7defe50e20c5811df46f7d703ce7fdf954e572db8ee32"
    cal_sha = "23f520d8164721885583a926c40dc71cb100b14bb47758dc3bb480279e0847e0"
    assert splits["calibration_3"]["task_ids_sha256"] == cal_sha
    assert splits["intersection"]["empty"] is True
    assert splits["intersection"]["size"] == 0
    assert splits["all_from_opened_300"] is True


def test_recomputed_pooled_metrics(tmp_path: Path) -> None:
    _run_recompute(tmp_path)
    data = _read_recomputation(tmp_path)
    m = data["pooled_metrics"]
    assert m["n_tasks"] == 300
    assert m["sip_f1_match"] is True
    assert m["rmcss_f1_match"] is True
    assert m["delta_f1_match"] is True
    assert m["all_sip_prediction_hashes_ok"] is True
    assert m["all_rmcss_prediction_hashes_ok"] is True
    assert m["sip"]["f1"] == 0.26474622770919065
    assert m["rmcss"]["f1"] == 0.35687263556116017
    assert abs(m["delta_f1"] - 0.09212640785196952) < 1e-9


def test_v11_truncation_evidence_recorded(tmp_path: Path) -> None:
    _run_recompute(tmp_path)
    data = _read_recomputation(tmp_path)
    v11 = data["v11_truncation_evidence"]
    assert v11["n_records"] == 30
    assert v11["agent_control_cap_distribution"] == {"1024": 30}
    assert v11["message_scan_counts"]["cap_hit_control_truncation"] == 0
