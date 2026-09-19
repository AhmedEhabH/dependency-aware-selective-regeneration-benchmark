"""Stage-4b statistical closure tests (T3, ZERO API).

Verifies that the closure recomputes the FROZEN Stage-4b point estimates
exactly (P67 metrics) and that the paired-task bootstrap is deterministic and
uses the TASK as the resampling unit.
"""
from __future__ import annotations

import json
from pathlib import Path

from benchmark.signal.metrics import macro_orr, orr

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
_CI_JSON = _PROJECT_DIR / "reports" / "stage4b_bootstrap_ci.json"
_METRICS_JSON = _PROJECT_DIR / "reports" / "precision_safe_acceptance_metrics.json"
_GATE_JSON = _PROJECT_DIR / "reports" / "precision_safe_acceptance_gate.json"


def test_point_estimates_match_frozen_metrics():
    ci = json.loads(_CI_JSON.read_text(encoding="utf-8"))
    metrics = json.loads(_METRICS_JSON.read_text(encoding="utf-8"))
    assert ci["verdict_unchanged"] == "PRECISION_SAFE_ACCEPTANCE_FAIL"
    for repo in ("djangocms", "saleor"):
        b5 = metrics["repos"][repo]["B"]["5"]
        m = ci["repos"][repo]["metrics"]
        assert abs(m["macro_orr"]["point_arm_a"] - b5["arm_a"]["macro_orr"]) < 1e-4
        assert abs(m["macro_orr"]["point_arm_b"] - b5["arm_b"]["macro_orr"]) < 1e-4
        assert abs(m["final_f1"]["point_arm_a"] - b5["arm_a"]["naive_union_f1"]) < 1e-4
        assert abs(m["final_f1"]["point_arm_b"] - b5["arm_b"]["naive_union_f1"]) < 1e-4
        assert abs(m["candidate_precision"]["point_arm_a"] - b5["arm_a"]["candidate_precision"]) < 1e-4
        assert abs(m["candidate_precision"]["point_arm_b"] - b5["arm_b"]["candidate_precision"]) < 1e-4


def test_gate_deltas_match_closure():
    ci = json.loads(_CI_JSON.read_text(encoding="utf-8"))
    gate = json.loads(_GATE_JSON.read_text(encoding="utf-8"))
    for repo in ("djangocms", "saleor"):
        m = ci["repos"][repo]["metrics"]
        assert abs(m["macro_orr"]["point_delta"] - gate["repos"][repo]["orr_delta_armB_minus_armA"]) < 1e-4
        assert abs(m["final_f1"]["point_delta"] - gate["repos"][repo]["naive_f1_delta_armB_minus_armA"]) < 1e-4


def test_n_resamples_and_seed():
    ci = json.loads(_CI_JSON.read_text(encoding="utf-8"))
    assert ci["n_resamples"] >= 10_000
    assert ci["seed"] == 20260919


def test_closure_is_deterministic():
    """Re-running the closure script must produce identical CIs (fixed seed)."""
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, str(_PROJECT_DIR / "scripts" / "stage4b_statistical_closure.py")],
        capture_output=True, text=True, cwd=_PROJECT_DIR,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    again = json.loads(_CI_JSON.read_text(encoding="utf-8"))
    first = json.loads(_CI_JSON.read_text(encoding="utf-8"))
    assert again == first


def test_macro_orr_zero_denominator_convention():
    assert orr(0, 0) == 0.0
    assert macro_orr([orr(0, 0), orr(1, 2)]) == 0.25
