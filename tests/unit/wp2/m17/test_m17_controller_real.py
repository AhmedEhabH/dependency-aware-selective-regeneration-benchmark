"""M17 K06 - real zero-Docker controller integration (wp2_ctl_v224.py, 8 scenarios).

Runs the REAL repository controller against the REAL qualification plan in a
throwaway git repo with a fake-world/fake-executor boundary. Zero Docker, zero
WSL, zero model/API. See sim/controller_sim.py for the implementation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[4]
SIM = P / "tests/unit/wp2/m17/sim/controller_sim.py"

# The full sim builds 8 throwaway git repos and runs the real controller
# multiple times (~8 builds + controller runs). Run it as one test; each build
# is a few seconds.
def test_m17_real_controller_eight_scenarios():
    import subprocess

    r = subprocess.run([sys.executable, str(SIM)], cwd=str(P), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=1800)
    if r.returncode != 0:
        raise AssertionError(f"sim failed rc={r.returncode}\n{r.stdout[-4000:]}\n{r.stderr[-4000:]}")
    assert "M17_K06_REAL_CONTROLLER_PASS" in r.stdout
    report_line = [ln for ln in r.stdout.splitlines() if "M17_K06_REAL_CONTROLLER_PASS" in ln][0]
    payload = report_line.split("M17_K06_REAL_CONTROLLER_PASS ", 1)[1]
    report = json.loads(payload)
    scenarios = report["scenarios"]
    assert scenarios["happy_path"]["exit"] == 0
    assert scenarios["adapter_violation"]["exit"] == 10
    assert any("M17_ADAPTER_FAIL" in x for x in scenarios["adapter_violation"]["stop"])
    assert scenarios["resource_hold"]["exit"] == 10
    assert any("HOLD_ACTIVE" in x for x in scenarios["resource_hold"]["stop"])
    assert scenarios["resume_first"]["exit"] == 10
    assert any("EVAL_ERROR" in x for x in scenarios["resume_first"]["stop"])
    assert scenarios["resume_second"]["exit"] == 0
    assert scenarios["duplicate_resume"]["exit1"] == 0
    assert scenarios["duplicate_resume"]["exit2"] == 0
    assert scenarios["duplicate_resume"]["n_evidence2"] <= 12
    assert scenarios["unknown_command"]["exit"] == 10
    assert scenarios["manifest_drift"]["exit"] == 2
    assert scenarios["selector_firewall"]["exit"] == 10
    assert any("M17_FIREWALL" in x for x in scenarios["selector_firewall"]["stop"])
